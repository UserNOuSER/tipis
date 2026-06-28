# db/init_db.py
import logging
from sqlalchemy import create_engine  # ty:ignore[unresolved-import]
from sqlalchemy.orm import sessionmaker, declarative_base  # ty:ignore[unresolved-import]

logger = logging.getLogger(__name__)

Base = declarative_base()

DATABASE_URL = "sqlite:///anti_surge_prototype.db"

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(DATABASE_URL, echo=False)
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine())
    return _SessionLocal


def initialize_database():
    """Инициализация БД: создание таблиц + миграция"""
    logger.info("🔌 Подключение к базе данных...")
    engine = get_engine()
    
    logger.info("🏗️ Создание таблиц (если их нет)...")
    Base.metadata.create_all(engine)
    
    # ✅ Запускаем миграцию
    from db.migrate import run_migration
    run_migration(DATABASE_URL)
    
    logger.info("✅ База данных готова к работе")