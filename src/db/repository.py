import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import create_engine  # ty:ignore[unresolved-import]
from sqlalchemy.orm import sessionmaker, Session  # ty:ignore[unresolved-import]
from sqlalchemy.exc import SQLAlchemyError  # ty:ignore[unresolved-import]

# Импортируем ORM-модели
from db.models import (
    FuzzyConfig, FuzzyRule, EventLog, 
    GDX_Point, GDX_Header, SurgeBoundary
)

logger = logging.getLogger(__name__)

class Database:
    """
    Репозиторий для CRUD-операций с БД.
    Реализует паттерн Singleton (согласно UML из Лаб 3).
    """
    _instance = None
    _session_factory = None
    _engine = None

    def __new__(cls, db_url: str = "sqlite:///anti_surge_prototype.db"):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._engine = create_engine(db_url, echo=False)
            cls._session_factory = sessionmaker(bind=cls._engine)
            logger.info(f"✅ Database Singleton initialized: {db_url}")
        return cls._instance

    def get_session(self) -> Session:
        """Создает новую сессию для транзакций."""
        return self._session_factory()  # ty:ignore[call-non-callable]

    # ==========================================
    # 1. Загрузка конфигурации нечеткой логики
    # ==========================================
    def load_fuzzy_config(self, config_id: int, version: str) -> Optional[Dict[str, Any]]:
        """
        Загружает конфигурацию FuzzyConfig и связанные с ней правила FuzzyRule.
        Возвращает словарь, готовый для передачи в C++ ядро (или DTO).
        """
        session = self.get_session()
        try:
            # 1. Ищем саму конфигурацию
            config = session.query(FuzzyConfig).filter_by(
                ConfigID=config_id, Version=version
            ).first()
            
            if not config:
                logger.warning(f"Конфигурация {config_id} v{version} не найдена.")
                return None

            # 2. Ищем активные правила для этой конфигурации
            rules = session.query(FuzzyRule).filter_by(
                ConfigID=config_id, Version=version, IsActive=True
            ).order_by(FuzzyRule.Priority).all()

            # 3. Формируем итоговый словарь (DTO-совместимый)
            # SQLAlchemy может возвращать JSON как строку или как dict (в зависимости от драйвера)
            input_vars = config.InputVars if isinstance(config.InputVars, dict) else json.loads(config.InputVars or "{}")
            output_vars = config.OutputVars if isinstance(config.OutputVars, dict) else json.loads(config.OutputVars or "{}")

            result = {
                "config_id": config.ConfigID,
                "version": config.Version,
                "input_vars": input_vars,
                "output_vars": output_vars,
                "membership_params": config.MembershipParams,
                "rules": [
                    {
                        "rule_id": r.RuleID,
                        "antecedent": r.AntecedentKey,
                        "consequent": r.Consequent,
                        "weight": r.Weight,
                        "priority": r.Priority
                    }
                    for r in rules
                ]
            }
            
            logger.info(f"📥 Загружено {len(rules)} правил для конфига {config_id} v{version}")
            return result

        except SQLAlchemyError as e:
            logger.error(f"❌ Ошибка БД при загрузке конфига: {e}")
            session.rollback()
            return None
        finally:
            session.close()

    # ==========================================
    # 2. Сохранение события (Телеметрия + Лог)
    # ==========================================
    def save_event_log(self, event_data: Dict[str, Any]) -> bool:
        """
        Сохраняет запись в таблицу EventLog.
        event_data должен содержать поля: Q, H, P_in, P_out, T_in, Margin, dQdt, 
        ValvePosition, Status, CompressorID, UserID, RuleFired (опционально).
        """
        session = self.get_session()
        try:
            # Создаем объект ORM-модели из словаря
            # Если каких-то полей нет, SQLAlchemy подставит NULL или DEFAULT
            log_entry = EventLog(
                Timestamp=event_data.get("timestamp", datetime.now(timezone.utc)),
                Q=event_data.get("Q"),
                H=event_data.get("H"),
                P_in=event_data.get("P_in"),
                P_out=event_data.get("P_out"),
                T_in=event_data.get("T_in"),
                Margin=event_data.get("margin"),
                dQdt=event_data.get("dQdt"),
                ValvePosition=event_data.get("valve_position"),
                RuleFired=event_data.get("rule_fired"),
                Status=event_data.get("status", False),
                CompressorID=event_data.get("compressor_id", 1), # Дефолтный ID
                UserID=event_data.get("user_id", 1)              # Дефолтный ID
            )
            
            session.add(log_entry)
            session.commit()
            logger.debug(f"💾 Событие сохранено в EventLog (ID: {log_entry.EventID})")
            return True

        except SQLAlchemyError as e:
            logger.error(f"❌ Ошибка записи в EventLog: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    # ==========================================
    # 3. Получение точек ГДХ для компрессора
    # ==========================================
    def get_gdx_points(self, compressor_id: int, composition_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Возвращает список точек ГДХ (Q, H, Efficiency) для отрисовки кривых на графике.
        Группирует точки по RPM (оборотам).
        """
        session = self.get_session()
        try:
            query = session.query(GDX_Header, GDX_Point).join(
                GDX_Point, GDX_Header.CurveID == GDX_Point.CurveID
            ).filter(
                GDX_Header.CompressorID == compressor_id
            )
            
            # Если указан состав газа, фильтруем и по нему
            if composition_id:
                query = query.filter(GDX_Header.CompositionID == composition_id)
                
            results = query.order_by(GDX_Header.RPM, GDX_Point.PointIndex).all()

            # Формируем список точек (DTO Point из Лаб 3)
            points = []
            for header, point in results:
                points.append({
                    "rpm": header.RPM,
                    "curve_id": header.CurveID,
                    "q": point.Q,
                    "h": point.H,
                    "efficiency": point.Efficiency,
                    "power": point.Power
                })
                
            logger.info(f"📈 Загружено {len(points)} точек ГДХ для компрессора {compressor_id}")
            return points

        except SQLAlchemyError as e:
            logger.error(f"❌ Ошибка загрузки ГДХ: {e}")
            return []
        finally:
            session.close()

    # ==========================================
    # 4. Дополнительные полезные методы
    # ==========================================
    def get_surge_boundary(self, compressor_id: int) -> List[Dict[str, float]]:
        """Загружает линию помпажа (SurgeBoundary) для отрисовки на графике Q-H."""
        session = self.get_session()
        try:
            boundaries = session.query(SurgeBoundary).filter_by(
                CompressorID=compressor_id
            ).all()
            
            return [{"q_surge": b.Q_surge, "h_surge": b.H_surge} for b in boundaries]
        except SQLAlchemyError as e:
            logger.error(f"❌ Ошибка загрузки границы помпажа: {e}")
            return []
        finally:
            session.close()

    # ==========================================
    # 5. Получение журнала событий с фильтрацией   
    # ==========================================

    def get_event_log(self, 
                      compressor_id: int = 1, 
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None,
                      limit: int = 100) -> List[Dict[str, Any]]:
        """
        Получает журнал событий с фильтрами.
        """
        session = self.get_session()
        try:
            query = session.query(EventLog).filter(
                EventLog.CompressorID == compressor_id
            )
            
            if start_date:
                query = query.filter(EventLog.Timestamp >= start_date)
            if end_date:
                query = query.filter(EventLog.Timestamp <= end_date)
            
            events = query.order_by(EventLog.Timestamp.desc()).limit(limit).all()
            
            result = []
            for event in events:
                result.append({
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
                    "user_id": event.UserID
                })
            
            logger.info(f" Загружено {len(result)} событий из журнала")
            return result
            
        except SQLAlchemyError as e:
            logger.error(f"❌ Ошибка загрузки журнала: {e}")
            return []
        finally:
            session.close()

    # ==========================================
    # 6. Получение деталей конкретного события
    # ==========================================

    def get_event_details(self, event_id: int) -> Optional[Dict[str, Any]]:
        """Получает детали конкретного события"""
        session = self.get_session()
        try:
            event = session.query(EventLog).filter_by(EventID=event_id).first()
            if event:
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
                    "rule_fired": event.RuleFired
                }
            return None
        except SQLAlchemyError as e:
            logger.error(f"❌ Ошибка загрузки деталей события: {e}")
            return None
        finally:
            session.close()

    def get_all_users(self) -> List[Dict[str, Any]]:
        """Получает список всех пользователей"""
        session = self.get_session()
        try:
            from db.models import User
            users = session.query(User).all()
            
            result = []
            for user in users:
                # Безопасно получаем поля через getattr (если поля нет — подставляем дефолт)
                result.append({
                    "user_id": getattr(user, 'UserID', 0),
                    "username": getattr(user, 'Username', ''),
                    "role": getattr(user, 'Role', 'OPERATOR'),
                    "is_active": getattr(user, 'IsActive', True)
                })
            
            logger.info(f"👥 Загружено {len(result)} пользователей")
            return result
        except SQLAlchemyError as e:
            logger.error(f"❌ Ошибка загрузки пользователей: {e}")
            return []
        finally:
            session.close()

    def create_user(self, username: str, password: str, role: str = "OPERATOR") -> bool:
        """Создаёт нового пользователя"""
        session = self.get_session()
        try:
            from db.models import User
            import hashlib
            
            # Хэшируем пароль (в продакшене используй bcrypt!)
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            new_user = User(
                Username=username,
                PasswordHash=password_hash,
                Role=role,
                IsActive=True
            )
            session.add(new_user)
            session.commit()
            logger.info(f"✅ Создан пользователь: {username} (роль: {role})")
            return True
        except SQLAlchemyError as e:
            logger.error(f"❌ Ошибка создания пользователя: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def update_user(self, user_id: int, username: Optional[str] = None, role: Optional[str] = None, is_active: Optional[bool] = None) -> bool:
        """Обновляет данные пользователя"""
        session = self.get_session()
        try:
            from db.models import User
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
            
            session.commit()
            logger.info(f"✅ Обновлён пользователь: {user_id}")
            return True
        except SQLAlchemyError as e:
            logger.error(f"❌ Ошибка обновления пользователя: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def delete_user(self, user_id: int) -> bool:
        """Удаляет пользователя"""
        session = self.get_session()
        try:
            from db.models import User
            user = session.query(User).filter_by(UserID=user_id).first()
            if not user:
                return False
            
            session.delete(user)
            session.commit()
            logger.info(f"🗑️ Удалён пользователь: {user_id}")
            return True
        except SQLAlchemyError as e:
            logger.error(f"❌ Ошибка удаления пользователя: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def reset_password(self, user_id: int, new_password: str) -> bool:
        """Сбрасывает пароль пользователя"""
        session = self.get_session()
        try:
            from db.models import User
            import hashlib
            
            user = session.query(User).filter_by(UserID=user_id).first()
            if not user:
                return False
            
            password_hash = hashlib.sha256(new_password.encode()).hexdigest()
            user.PasswordHash = password_hash
            session.commit()
            logger.info(f"🔑 Сброшен пароль для пользователя: {user_id}")
            return True
        except SQLAlchemyError as e:
            logger.error(f"❌ Ошибка сброса пароля: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    # ==========================================
    # Обновление конфигурации нечёткой логики
    # ==========================================
    def update_fuzzy_config(self, config_id: int, version: str,
                           input_vars: Dict, output_vars: Dict,
                           membership_params: Dict, rules: List[Dict],
                           updated_by: str) -> bool:
        """
        Обновляет конфигурацию и связанные правила.
        Использует стратегию 'удалить старые правила → создать новые'.
        """
        session = self.get_session()
        try:
            from db.models import FuzzyConfig, FuzzyRule
            
            # 1. Находим конфигурацию
            config = session.query(FuzzyConfig).filter_by(
                ConfigID=config_id, Version=version
            ).first()
            
            if not config:
                logger.warning(f"Конфиг {config_id} v{version} не найден")
                return False
            
            # 2. Обновляем саму конфигурацию
            config.InputVars = json.dumps(input_vars) if not isinstance(input_vars, str) else input_vars
            config.OutputVars = json.dumps(output_vars) if not isinstance(output_vars, str) else output_vars
            config.MembershipParams = json.dumps(membership_params) if not isinstance(membership_params, str) else membership_params
            config.UpdatedBy = updated_by
            
            # 3. Удаляем старые правила
            session.query(FuzzyRule).filter_by(
                ConfigID=config_id, Version=version
            ).delete()
            
            # 4. Создаём новые правила
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
            
            session.commit()
            logger.info(f"✅ Конфиг {config_id} v{version} обновлён ({len(rules)} правил)")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"❌ Ошибка обновления конфига: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    # ==========================================
    # Работа с компрессорами
    # ==========================================
    def get_all_compressors(self) -> List[Dict[str, Any]]:
        """Получает список всех компрессоров с их профилями"""
        session = self.get_session()
        try:
            from db.models import Compressor, FuzzyConfig
            result = session.query(Compressor, FuzzyConfig.Name).join(
                FuzzyConfig, Compressor.ProfileID == FuzzyConfig.ConfigID
            ).all()
            
            compressors = []
            for comp, profile_name in result:
                compressors.append({
                    "compressor_id": comp.CompressorID,
                    "name": comp.Name,
                    "model": comp.Model,
                    "profile_id": comp.ProfileID,
                    "profile_name": profile_name or f"Профиль #{comp.ProfileID}"
                })
            
            logger.info(f"🔧 Загружено {len(compressors)} компрессоров")
            return compressors
        except SQLAlchemyError as e:
            logger.error(f"❌ Ошибка загрузки компрессоров: {e}")
            return []
        finally:
            session.close()

    def get_compressor(self, compressor_id: int) -> Optional[Dict[str, Any]]:
        """Получает данные конкретного компрессора"""
        session = self.get_session()
        try:
            from db.models import Compressor, FuzzyConfig
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
        except SQLAlchemyError as e:
            logger.error(f"❌ Ошибка загрузки компрессора: {e}")
            return None
        finally:
            session.close()

    def assign_profile_to_compressor(self, compressor_id: int, profile_id: int) -> bool:
        """Привязывает профиль к компрессору"""
        session = self.get_session()
        try:
            from db.models import Compressor
            comp = session.query(Compressor).filter_by(CompressorID=compressor_id).first()
            if not comp:
                return False
            
            comp.ProfileID = profile_id
            session.commit()
            logger.info(f"✅ Компрессору {compressor_id} назначен профиль {profile_id}")
            return True
        except SQLAlchemyError as e:
            logger.error(f"❌ Ошибка назначения профиля: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    # ==========================================
    # Работа с профилями правил
    # ==========================================
    def get_all_profiles(self) -> List[Dict[str, Any]]:
        """Получает список всех профилей правил"""
        session = self.get_session()
        try:
            from db.models import FuzzyConfig
            profiles = session.query(FuzzyConfig).all()
            
            result = []
            for p in profiles:
                result.append({
                    "profile_id": p.ConfigID,
                    "name": p.Name or f"Профиль #{p.ConfigID}",
                    "description": p.Description,
                    "version": p.Version,
                    "updated_at": p.UpdatedAt,
                    "updated_by": p.UpdatedBy
                })
            
            logger.info(f"📋 Загружено {len(result)} профилей")
            return result
        except SQLAlchemyError as e:
            logger.error(f"❌ Ошибка загрузки профилей: {e}")
            return []
        finally:
            session.close()

    def load_profile_config(self, profile_id: int) -> Optional[Dict[str, Any]]:
        """Загружает конфигурацию конкретного профиля"""
        session = self.get_session()
        try:
            from db.models import FuzzyConfig, FuzzyRule
            config = session.query(FuzzyConfig).filter_by(ConfigID=profile_id).first()
            
            if not config:
                return None
            
            rules = session.query(FuzzyRule).filter_by(
                ConfigID=profile_id, IsActive=True
            ).order_by(FuzzyRule.Priority).all()
            
            input_vars = config.InputVars if isinstance(config.InputVars, dict) else json.loads(config.InputVars or "{}")
            output_vars = config.OutputVars if isinstance(config.OutputVars, dict) else json.loads(config.OutputVars or "{}")
            membership_params = config.MembershipParams if isinstance(config.MembershipParams, dict) else json.loads(config.MembershipParams or "{}")
            
            return {
                "profile_id": config.ConfigID,
                "name": config.Name,
                "description": config.Description,
                "version": config.Version,
                "input_vars": input_vars,
                "output_vars": output_vars,
                "membership_params": membership_params,
                "rules": [
                    {
                        "rule_id": r.RuleID,
                        "antecedent": r.AntecedentKey,
                        "consequent": r.Consequent,
                        "weight": r.Weight,
                        "priority": r.Priority
                    }
                    for r in rules
                ]
            }
        except SQLAlchemyError as e:
            logger.error(f"❌ Ошибка загрузки профиля: {e}")
            return None
        finally:
            session.close()

    def create_profile(self, name: str, description: str = "", 
                      input_vars: Dict = None, output_vars: Dict = None,  # ty:ignore[invalid-parameter-default]
                      membership_params: Dict = None, rules: List[Dict] = None,  # ty:ignore[invalid-parameter-default]
                      created_by: str = "system") -> Optional[int]:
        """Создаёт новый профиль правил. Возвращает ID нового профиля."""
        session = self.get_session()
        try:
            from db.models import FuzzyConfig, FuzzyRule
            
            new_config = FuzzyConfig(
                Version="1.0.0",
                Name=name,
                Description=description,
                InputVars=json.dumps(input_vars or {}),
                OutputVars=json.dumps(output_vars or {}),
                MembershipParams=json.dumps(membership_params or {}),
                UpdatedBy=created_by
            )
            session.add(new_config)
            session.flush()  # Получаем ConfigID
            
            # Добавляем правила
            if rules:
                for rule_data in rules:
                    new_rule = FuzzyRule(
                        ConfigID=new_config.ConfigID,
                        Version="1.0.0",
                        AntecedentKey=rule_data["antecedent"],
                        Consequent=rule_data["consequent"],
                        Weight=rule_data.get("weight", 1.0),
                        Priority=rule_data.get("priority", 1),
                        IsActive=True
                    )
                    session.add(new_rule)
            
            session.commit()
            logger.info(f"✅ Создан профиль '{name}' (ID={new_config.ConfigID})")
            return new_config.ConfigID
        except SQLAlchemyError as e:
            logger.error(f"❌ Ошибка создания профиля: {e}")
            session.rollback()
            return None
        finally:
            session.close()

    def update_profile(self, profile_id: int, name: str = None,  # ty:ignore[invalid-parameter-default]
                      description: str = None, input_vars: Dict = None,  # ty:ignore[invalid-parameter-default]
                      output_vars: Dict = None, membership_params: Dict = None,  # ty:ignore[invalid-parameter-default]
                      rules: List[Dict] = None, updated_by: str = "system") -> bool:  # ty:ignore[invalid-parameter-default]
        """Обновляет профиль правил"""
        session = self.get_session()
        try:
            from db.models import FuzzyConfig, FuzzyRule
            config = session.query(FuzzyConfig).filter_by(ConfigID=profile_id).first()
            if not config:
                return False
            
            if name is not None:
                config.Name = name
            if description is not None:
                config.Description = description
            if input_vars is not None:
                config.InputVars = json.dumps(input_vars) if not isinstance(input_vars, str) else input_vars
            if output_vars is not None:
                config.OutputVars = json.dumps(output_vars) if not isinstance(output_vars, str) else output_vars
            if membership_params is not None:
                config.MembershipParams = json.dumps(membership_params) if not isinstance(membership_params, str) else membership_params
            config.UpdatedBy = updated_by
            
            # Если переданы правила — заменяем все
            if rules is not None:
                session.query(FuzzyRule).filter_by(ConfigID=profile_id).delete()
                for rule_data in rules:
                    new_rule = FuzzyRule(
                        ConfigID=profile_id,
                        Version="1.0.0",
                        AntecedentKey=rule_data["antecedent"],
                        Consequent=rule_data["consequent"],
                        Weight=rule_data.get("weight", 1.0),
                        Priority=rule_data.get("priority", 1),
                        IsActive=True
                    )
                    session.add(new_rule)
            
            session.commit()
            logger.info(f"✅ Профиль {profile_id} обновлён")
            return True
        except SQLAlchemyError as e:
            logger.error(f"❌ Ошибка обновления профиля: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def delete_profile(self, profile_id: int) -> tuple[bool, str]:
        """
        Удаляет профиль правил.
        Возвращает (успех, сообщение).
        Не позволяет удалить профиль, если он назначен компрессорам.
        """
        session = self.get_session()
        try:
            from db.models import FuzzyConfig, Compressor, FuzzyRule
            
            # 1. Проверяем, есть ли компрессоры с этим профилем
            linked_compressors = session.query(Compressor).filter_by(ProfileID=profile_id).all()
            if linked_compressors:
                names = ", ".join([c.Name for c in linked_compressors])
                msg = f"Профиль назначен компрессорам: {names}. Сначала переназначьте их."
                logger.warning(f"⚠️ {msg}")
                return False, msg
            
            # 2. Проверяем, не последний ли это профиль
            total_profiles = session.query(FuzzyConfig).count()
            if total_profiles <= 1:
                msg = "Нельзя удалить единственный профиль в системе"
                logger.warning(f"⚠️ {msg}")
                return False, msg
            
            # 3. Находим и удаляем профиль
            profile = session.query(FuzzyConfig).filter_by(ConfigID=profile_id).first()
            if not profile:
                return False, "Профиль не найден"
            
            profile_name = profile.Name or f"#{profile_id}"
            
            # Каскадное удаление правил (настроено в модели)
            session.delete(profile)
            session.commit()
            
            logger.info(f"🗑️ Удалён профиль '{profile_name}' (ID={profile_id})")
            return True, f"Профиль '{profile_name}' удалён"
            
        except SQLAlchemyError as e:
            logger.error(f"❌ Ошибка удаления профиля: {e}")
            session.rollback()
            return False, f"Ошибка БД: {e}"
        finally:
            session.close()