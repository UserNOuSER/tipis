import json
import hashlib
import logging
from typing import List, Optional, Dict, Any, Callable, Tuple
from datetime import datetime
from contextlib import contextmanager

from sqlalchemy import create_engine  # ty:ignore[unresolved-import]
from sqlalchemy.orm import sessionmaker, Session  # ty:ignore[unresolved-import]
from sqlalchemy.exc import SQLAlchemyError  # ty:ignore[unresolved-import]

from db.models import (
    FuzzyConfig, FuzzyRule, EventLog,
    GDX_Point, GDX_Header, SurgeBoundary,
    User, Compressor
)

logger = logging.getLogger(__name__)


class Database:
    """
    Репозиторий для CRUD-операций с БД.
    Реализует паттерн Singleton.
    """
    
    _instance: Optional['Database'] = None
    _session_factory = None
    _engine = None

    def __new__(cls, db_url: str = "sqlite:///anti_surge_prototype.db"):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._engine = create_engine(db_url, echo=False)
            cls._session_factory = sessionmaker(bind=cls._engine)
            logger.info(f"✅ Database Singleton initialized: {db_url}")
        return cls._instance

    # ==========================================
    # Вспомогательные методы
    # ==========================================
    @contextmanager
    def _session_scope(self):
        """
        Контекстный менеджер для работы с сессией.
        Автоматически закрывает сессию и делает rollback при ошибке.
        """
        session = self._session_factory()  # ty:ignore[call-non-callable]
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"❌ Ошибка БД: {e}")
            raise
        finally:
            session.close()

    @staticmethod
    def _safe_json_loads(value: Any) -> Any:
        """Безопасно парсит JSON-строку, возвращает dict/list или исходное значение"""
        if value is None:
            return {}
        if isinstance(value, (dict, list)):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                logger.warning(f"⚠️ Не удалось распарсить JSON: {value[:50]}...")
                return {}
        return {}

    @staticmethod
    def _safe_json_dumps(value: Any) -> str:
        """Безопасно сериализует значение в JSON-строку"""
        if isinstance(value, str):
            return value
        try:
            return json.dumps(value, ensure_ascii=False)
        except (TypeError, ValueError):
            return "{}"

    @staticmethod
    def _hash_password(password: str) -> str:
        """Хэширует пароль (SHA-256). В продакшене используй bcrypt!"""
        return hashlib.sha256(password.encode()).hexdigest()

    def _execute_safely(self, operation: Callable, error_msg: str, default: Any = None) -> Any:
        """
        Выполняет операцию с обработкой ошибок.
        Возвращает default при ошибке.
        """
        try:
            return operation()
        except SQLAlchemyError as e:
            logger.error(f"{error_msg}: {e}")
            return default

    # ==========================================
    # Конфигурация нечёткой логики
    # ==========================================
    def load_fuzzy_config(self, config_id: int, version: str) -> Optional[Dict[str, Any]]:
        """Загружает конфигурацию FuzzyConfig и связанные правила."""
        def _load():
            with self._session_scope() as session:
                config = session.query(FuzzyConfig).filter_by(
                    ConfigID=config_id, Version=version
                ).first()
                
                if not config:
                    logger.warning(f"Конфигурация {config_id} v{version} не найдена")
                    return None

                rules = self._load_rules_for_config(session, config_id, version)
                return self._build_config_dto(config, rules)

        result = self._execute_safely(
            _load, 
            f"Ошибка загрузки конфига {config_id} v{version}"
        )
        if result and result.get("rules"):
            logger.info(f"📥 Загружено {len(result['rules'])} правил для конфига {config_id} v{version}")
        return result

    def _load_rules_for_config(self, session: Session, config_id: int, version: str) -> List[Dict]:
        """Загружает активные правила для конфигурации"""
        rules = session.query(FuzzyRule).filter_by(
            ConfigID=config_id, Version=version, IsActive=True
        ).order_by(FuzzyRule.Priority).all()
        
        return [self._rule_to_dict(r) for r in rules]

    @staticmethod
    def _rule_to_dict(rule: FuzzyRule) -> Dict[str, Any]:
        """Преобразует ORM-объект правила в словарь"""
        return {
            "rule_id": rule.RuleID,
            "antecedent": rule.AntecedentKey,
            "consequent": rule.Consequent,
            "weight": rule.Weight,
            "priority": rule.Priority
        }

    @staticmethod
    def _build_config_dto(config: FuzzyConfig, rules: List[Dict]) -> Dict[str, Any]:
        """Формирует DTO-совместимый словарь конфигурации"""
        return {
            "config_id": config.ConfigID,
            "version": config.Version,
            "input_vars": Database._safe_json_loads(config.InputVars),
            "output_vars": Database._safe_json_loads(config.OutputVars),
            "membership_params": Database._safe_json_loads(config.MembershipParams),
            "rules": rules
        }

    # ==========================================
    # Журнал событий
    # ==========================================
    def save_event_log(self, event_data: Dict[str, Any]) -> bool:
        def _save():
            with self._session_scope() as session:
                event = EventLog(
                    Timestamp=event_data.get("timestamp", datetime.utcnow()),
                    Q=event_data.get("Q", 0),
                    H=event_data.get("H", 0),
                    P_in=event_data.get("P_in", 0),
                    P_out=event_data.get("P_out", 0),
                    T_in=event_data.get("T_in", 0),
                    Margin=event_data.get("margin", 0),
                    dQdt=event_data.get("dQdt", 0),
                    ValvePosition=event_data.get("valve_position", 0),
                    RuleFired=event_data.get("rule_fired", ""),
                    Status=event_data.get("status", False),
                    CompressorID=event_data.get("compressor_id", 1),
                    UserID=event_data.get("user_id", 1),
                    ReactionTime=event_data.get("reaction_time", 0.0),
                    GasComposition=event_data.get("gas_composition", "")
                )
                session.add(event)
            return True

        return self._execute_safely(_save, "Ошибка сохранения события", False)

    def get_event_log(
        self,
        compressor_id: int = 1,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Получает журнал событий с фильтрами"""
        def _load():
            with self._session_scope() as session:
                query = session.query(EventLog).filter(
                    EventLog.CompressorID == compressor_id
                )
                
                if start_date:
                    query = query.filter(EventLog.Timestamp >= start_date)
                if end_date:
                    query = query.filter(EventLog.Timestamp <= end_date)
                
                events = query.order_by(EventLog.Timestamp.desc()).limit(limit).all()
                return [self._event_to_dict(e) for e in events]

        result = self._execute_safely(_load, "Ошибка загрузки журнала", [])
        logger.info(f"📋 Загружено {len(result)} событий из журнала")
        return result

    def get_event_details(self, event_id: int) -> Optional[Dict[str, Any]]:
        """Получает детали конкретного события"""
        def _load():
            with self._session_scope() as session:
                event = session.query(EventLog).filter_by(EventID=event_id).first()
                return self._event_to_dict(event) if event else None

        return self._execute_safely(_load, f"Ошибка загрузки события {event_id}")

    @staticmethod
    def _event_to_dict(event: EventLog) -> Dict[str, Any]:
        """Преобразует ORM-объект события в словарь"""
        return {
            "event_id": event.EventID,
            "timestamp": event.Timestamp,
            "q": event.Q,
            "h": event.H,
            "p_in": event.P_in,
            "p_out": event.P_out,
            "t_in": event.T_in,
            "margin": event.Margin,
            "dqdt": event.dQdt,
            "valve_position": event.ValvePosition,
            "status": event.Status,
            "rule_fired": event.RuleFired,
            "compressor_id": event.CompressorID,
            "user_id": event.UserID,
            "reaction_time": getattr(event, 'ReactionTime', 0.0) or 0.0,
            "gas_composition": getattr(event, 'GasComposition', '') or ''
        }

    # ==========================================
    # Точки ГДХ и линия помпажа
    # ==========================================
    def get_gdx_points(
        self, 
        compressor_id: int, 
        composition_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Возвращает список точек ГДХ для отрисовки кривых"""
        def _load():
            with self._session_scope() as session:
                query = session.query(GDX_Header, GDX_Point).join(
                    GDX_Point, GDX_Header.CurveID == GDX_Point.CurveID
                ).filter(GDX_Header.CompressorID == compressor_id)
                
                if composition_id:
                    query = query.filter(GDX_Header.CompositionID == composition_id)
                
                results = query.order_by(GDX_Header.RPM, GDX_Point.PointIndex).all()
                return [
                    {
                        "rpm": header.RPM,
                        "curve_id": header.CurveID,
                        "q": point.Q,
                        "h": point.H,
                        "efficiency": point.Efficiency,
                        "power": point.Power
                    }
                    for header, point in results
                ]

        result = self._execute_safely(_load, "Ошибка загрузки ГДХ", [])
        logger.info(f"📈 Загружено {len(result)} точек ГДХ для компрессора {compressor_id}")
        return result

    def get_surge_boundary(self, compressor_id: int) -> List[Dict[str, float]]:
        """Загружает линию помпажа для отрисовки"""
        def _load():
            with self._session_scope() as session:
                boundaries = session.query(SurgeBoundary).filter_by(
                    CompressorID=compressor_id
                ).all()
                return [{"q_surge": b.Q_surge, "h_surge": b.H_surge} for b in boundaries]

        return self._execute_safely(_load, "Ошибка загрузки границы помпажа", [])

    # ==========================================
    # Пользователи
    # ==========================================
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Получает список всех пользователей"""
        def _load():
            with self._session_scope() as session:
                users = session.query(User).all()
                return [self._user_to_dict(u) for u in users]

        result = self._execute_safely(_load, "Ошибка загрузки пользователей", [])
        logger.info(f"👥 Загружено {len(result)} пользователей")
        return result

    def create_user(self, username: str, password: str, role: str = "OPERATOR") -> bool:
        """Создаёт нового пользователя"""
        def _create():
            with self._session_scope() as session:
                new_user = User(
                    Username=username,
                    PasswordHash=self._hash_password(password),
                    Role=role,
                    IsActive=True
                )
                session.add(new_user)
            logger.info(f"✅ Создан пользователь: {username} (роль: {role})")
            return True

        return self._execute_safely(_create, "Ошибка создания пользователя", False)

    def update_user(
        self, 
        user_id: int, 
        username: Optional[str] = None,
        role: Optional[str] = None, 
        is_active: Optional[bool] = None
    ) -> bool:
        """Обновляет данные пользователя"""
        def _update():
            with self._session_scope() as session:
                user = session.query(User).filter_by(UserID=user_id).first()
                if not user:
                    logger.warning(f"Пользователь {user_id} не найден")
                    return False
                
                if username is not None:
                    user.Username = username
                if role is not None:
                    user.Role = role
                if is_active is not None:
                    user.IsActive = is_active
            logger.info(f"✅ Обновлён пользователь: {user_id}")
            return True

        return self._execute_safely(_update, "Ошибка обновления пользователя", False)

    def delete_user(self, user_id: int) -> bool:
        """Удаляет пользователя"""
        def _delete():
            with self._session_scope() as session:
                user = session.query(User).filter_by(UserID=user_id).first()
                if not user:
                    return False
                session.delete(user)
            logger.info(f"🗑️ Удалён пользователь: {user_id}")
            return True

        return self._execute_safely(_delete, "Ошибка удаления пользователя", False)

    def reset_password(self, user_id: int, new_password: str) -> bool:
        """Сбрасывает пароль пользователя"""
        def _reset():
            with self._session_scope() as session:
                user = session.query(User).filter_by(UserID=user_id).first()
                if not user:
                    return False
                user.PasswordHash = self._hash_password(new_password)
            logger.info(f"🔑 Сброшен пароль для пользователя: {user_id}")
            return True

        return self._execute_safely(_reset, "Ошибка сброса пароля", False)

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Аутентифицирует пользователя по логину и паролю"""
        def _auth():
            with self._session_scope() as session:
                user = session.query(User).filter_by(
                    Username=username,
                    PasswordHash=self._hash_password(password),
                    IsActive=True
                ).first()
                
                if user:
                    user.LastLogin = datetime.now()
                    return self._user_to_dict(user)
                return None

        result = self._execute_safely(_auth, "Ошибка аутентификации")
        if result:
            logger.info(f"✅ Пользователь {username} вошёл в систему")
        else:
            logger.warning(f"⚠️ Неудачная попытка входа: {username}")
        return result

    def get_user_count(self) -> int:
        """Возвращает количество пользователей в БД"""
        def _count():
            with self._session_scope() as session:
                return session.query(User).count()
        return self._execute_safely(_count, "Ошибка подсчёта пользователей", 0)

    @staticmethod
    def _user_to_dict(user: User) -> Dict[str, Any]:
        """Преобразует ORM-объект пользователя в словарь"""
        return {
            "user_id": user.UserID,
            "username": user.Username,
            "role": user.Role,
            "is_active": user.IsActive
        }

    # ==========================================
    # Компрессоры
    # ==========================================
    def get_all_compressors(self) -> List[Dict[str, Any]]:
        """Получает список всех компрессоров с их профилями"""
        def _load():
            with self._session_scope() as session:
                results = session.query(Compressor, FuzzyConfig.Name).join(
                    FuzzyConfig, Compressor.ProfileID == FuzzyConfig.ConfigID
                ).all()
                
                return [
                    {
                        "compressor_id": comp.CompressorID,
                        "name": comp.Name,
                        "model": comp.Model,
                        "profile_id": comp.ProfileID,
                        "profile_name": profile_name or f"Профиль #{comp.ProfileID}"
                    }
                    for comp, profile_name in results
                ]

        result = self._execute_safely(_load, "Ошибка загрузки компрессоров", [])
        logger.info(f"🔧 Загружено {len(result)} компрессоров")
        return result

    def get_compressor(self, compressor_id: int) -> Optional[Dict[str, Any]]:
        """Получает данные конкретного компрессора"""
        def _load():
            with self._session_scope() as session:
                result = session.query(Compressor, FuzzyConfig.Name).join(
                    FuzzyConfig, Compressor.ProfileID == FuzzyConfig.ConfigID
                ).filter(Compressor.CompressorID == compressor_id).first()
                
                if result:
                    comp, profile_name = result
                    return {
                        "compressor_id": comp.CompressorID,
                        "name": comp.Name,
                        "model": comp.Model,
                        "profile_id": comp.ProfileID,
                        "profile_name": profile_name
                    }
                return None

        return self._execute_safely(_load, f"Ошибка загрузки компрессора {compressor_id}")

    def assign_profile_to_compressor(self, compressor_id: int, profile_id: int) -> bool:
        """Привязывает профиль к компрессору"""
        def _assign():
            with self._session_scope() as session:
                comp = session.query(Compressor).filter_by(CompressorID=compressor_id).first()
                if not comp:
                    return False
                comp.ProfileID = profile_id
            logger.info(f"✅ Компрессору {compressor_id} назначен профиль {profile_id}")
            return True

        return self._execute_safely(_assign, "Ошибка назначения профиля", False)

    # ==========================================
    # Профили правил
    # ==========================================
    def get_all_profiles(self) -> List[Dict[str, Any]]:
        """Получает список всех профилей правил"""
        def _load():
            with self._session_scope() as session:
                profiles = session.query(FuzzyConfig).all()
                return [
                    {
                        "profile_id": p.ConfigID,
                        "name": p.Name or f"Профиль #{p.ConfigID}",
                        "description": p.Description,
                        "version": p.Version,
                        "updated_at": p.UpdatedAt,
                        "updated_by": p.UpdatedBy
                    }
                    for p in profiles
                ]

        result = self._execute_safely(_load, "Ошибка загрузки профилей", [])
        logger.info(f"📋 Загружено {len(result)} профилей")
        return result

    def load_profile_config(self, profile_id: int) -> Optional[Dict[str, Any]]:
        """Загружает конфигурацию конкретного профиля"""
        def _load():
            with self._session_scope() as session:
                config = session.query(FuzzyConfig).filter_by(ConfigID=profile_id).first()
                if not config:
                    return None
                
                rules = self._load_rules_for_config(session, profile_id, config.Version)
                return {
                    "profile_id": config.ConfigID,
                    "name": config.Name,
                    "description": config.Description,
                    "version": config.Version,
                    "input_vars": self._safe_json_loads(config.InputVars),
                    "output_vars": self._safe_json_loads(config.OutputVars),
                    "membership_params": self._safe_json_loads(config.MembershipParams),
                    "rules": rules
                }

        return self._execute_safely(_load, f"Ошибка загрузки профиля {profile_id}")

    def create_profile(
        self,
        name: str,
        description: str = "",
        input_vars: Optional[Dict] = None,
        output_vars: Optional[Dict] = None,
        membership_params: Optional[Dict] = None,
        rules: Optional[List[Dict]] = None,
        created_by: str = "system"
    ) -> Optional[int]:
        """Создаёт новый профиль правил. Возвращает ID нового профиля."""
        def _create():
            with self._session_scope() as session:
                new_config = FuzzyConfig(
                    Version="1.0.0",
                    Name=name,
                    Description=description,
                    InputVars=self._safe_json_dumps(input_vars or {}),
                    OutputVars=self._safe_json_dumps(output_vars or {}),
                    MembershipParams=self._safe_json_dumps(membership_params or {}),
                    UpdatedBy=created_by
                )
                session.add(new_config)
                session.flush()
                
                if rules:
                    self._add_rules_to_config(session, new_config.ConfigID, "1.0.0", rules)
                
                return new_config.ConfigID

        result = self._execute_safely(_create, "Ошибка создания профиля")
        if result:
            logger.info(f"✅ Создан профиль '{name}' (ID={result})")
        return result

    def update_profile(
        self,
        profile_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        input_vars: Optional[Dict] = None,
        output_vars: Optional[Dict] = None,
        membership_params: Optional[Dict] = None,
        rules: Optional[List[Dict]] = None,
        updated_by: str = "system"
    ) -> bool:
        """Обновляет профиль правил"""
        def _update():
            with self._session_scope() as session:
                config = session.query(FuzzyConfig).filter_by(ConfigID=profile_id).first()
                if not config:
                    return False
                
                if name is not None:
                    config.Name = name
                if description is not None:
                    config.Description = description
                if input_vars is not None:
                    config.InputVars = self._safe_json_dumps(input_vars)
                if output_vars is not None:
                    config.OutputVars = self._safe_json_dumps(output_vars)
                if membership_params is not None:
                    config.MembershipParams = self._safe_json_dumps(membership_params)
                config.UpdatedBy = updated_by
                
                if rules is not None:
                    session.query(FuzzyRule).filter_by(ConfigID=profile_id).delete()
                    self._add_rules_to_config(session, profile_id, config.Version, rules)
                
                return True

        result = self._execute_safely(_update, f"Ошибка обновления профиля {profile_id}", False)
        if result:
            logger.info(f"✅ Профиль {profile_id} обновлён")
        return result

    def delete_profile(self, profile_id: int) -> Tuple[bool, str]:
        """
        Удаляет профиль правил.
        Возвращает (успех, сообщение).
        Не позволяет удалить профиль, если он назначен компрессорам.
        """
        def _delete():
            with self._session_scope() as session:
                # Проверка: есть ли компрессоры с этим профилем
                linked = session.query(Compressor).filter_by(ProfileID=profile_id).all()
                if linked:
                    names = ", ".join(c.Name for c in linked)
                    return False, f"Профиль назначен компрессорам: {names}. Сначала переназначьте их."
                
                # Проверка: не последний ли это профиль
                if session.query(FuzzyConfig).count() <= 1:
                    return False, "Нельзя удалить единственный профиль в системе"
                
                profile = session.query(FuzzyConfig).filter_by(ConfigID=profile_id).first()
                if not profile:
                    return False, "Профиль не найден"
                
                profile_name = profile.Name or f"#{profile_id}"
                session.delete(profile)
                return True, f"Профиль '{profile_name}' удалён"

        success, message = self._execute_safely(_delete, "Ошибка удаления профиля", (False, "Ошибка БД"))
        if success:
            logger.info(f"🗑️ {message}")
        else:
            logger.warning(f"⚠️ {message}")
        return success, message

    def _add_rules_to_config(
        self, 
        session: Session, 
        config_id: int, 
        version: str, 
        rules: List[Dict]
    ):
        """Добавляет правила к конфигурации"""
        for rule_data in rules:
            new_rule = FuzzyRule(
                ConfigID=config_id,
                Version=version,
                AntecedentKey=rule_data["antecedent"],
                Consequent=rule_data["consequent"],
                Weight=rule_data.get("weight", 1.0),
                Priority=rule_data.get("priority", 1),
                IsActive=True
            )
            session.add(new_rule)

    # ==========================================
    # Устаревший метод (для обратной совместимости)
    # ==========================================
    def update_fuzzy_config(
        self, 
        config_id: int, 
        version: str,
        input_vars: Dict, 
        output_vars: Dict,
        membership_params: Dict, 
        rules: List[Dict],
        updated_by: str
    ) -> bool:
        """
        ⚠️ УСТАРЕВШИЙ МЕТОД — используйте update_profile()
        Оставлен для обратной совместимости.
        """
        return self.update_profile(
            profile_id=config_id,
            input_vars=input_vars,
            output_vars=output_vars,
            membership_params=membership_params,
            rules=rules,
            updated_by=updated_by
        )