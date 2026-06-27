# db/repository.py
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
        return self._session_factory()

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