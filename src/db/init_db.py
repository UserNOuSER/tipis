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


def create_super_user():
    """Создаёт суперпользователя при первом запуске (через консоль)"""
    from db.models import User
    import hashlib
    
    session = get_session_factory()()
    try:
        user_count = session.query(User).count()
        if user_count > 0:
            logger.info(f"Database already has {user_count} users, skipping admin creation")
            return
        
        print("\n" + "=" * 60)
        print(" ПЕРВЫЙ ЗАПУСК СИСТЕМЫ")
        print("=" * 60)
        print("Необходимо создать суперпользователя (администратора).")
        print("Эти данные будут использоваться для входа в систему.\n")
        
        while True:
            username = input(" Введите логин администратора: ").strip()
            if not username:
                print(" Логин не может быть пустым")
                continue
            if len(username) < 3:
                print(" Логин должен быть не менее 3 символов")
                continue
            break
        
        while True:
            password = input(" Введите пароль (минимум 6 символов): ").strip()
            if len(password) < 6:
                print(" Пароль должен быть не менее 6 символов")
                continue
            
            password_confirm = input(" Повторите пароль: ").strip()
            if password != password_confirm:
                print(" Пароли не совпадают")
                continue
            break
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        super_user = User(
            Username=username,
            PasswordHash=password_hash,
            Role="ADMIN",
            IsActive=True
        )
        session.add(super_user)
        session.commit()
        
        print("\n" + "=" * 60)
        print(f" Суперпользователь '{username}' успешно создан!")
        print("=" * 60 + "\n")
        
    except Exception as e:
        logger.error(f" Ошибка создания суперпользователя: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def initialize_database():
    """Инициализация БД: создание таблиц + миграция + генерация данных + суперпользователь"""
    logger.info(" Подключение к базе данных...")
    engine = get_engine()
    
    # ВАЖНО: Импортируем модели ДО создания таблиц!
    # Это регистрирует все классы (FuzzyConfigs, EventLog и т.д.) в Base.metadata
    import db.models  # noqa: F401
    
    logger.info(" Создание таблиц (если их нет)...")
    Base.metadata.create_all(engine)
    
    # Запускаем миграцию
    from db.migrate import run_migration
    run_migration(DATABASE_URL)
    
    # Создаём суперпользователя при первом запуске
    create_super_user()
    
    # Генерируем тестовые данные
    from db.seed_data import run_seeding
    run_seeding(DATABASE_URL)
    
    logger.info(" База данных готова к работе")