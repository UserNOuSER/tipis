"""
Скрипт генерации тестовых данных для прототипа.
Создаёт пользователей, события и точки ГДХ.
"""
import random
import hashlib
from datetime import datetime, timedelta
from sqlalchemy import create_engine  # ty:ignore[unresolved-import]
from sqlalchemy.orm import sessionmaker  # ty:ignore[unresolved-import]
from db.models import Base, User, EventLog, GDX_Header, GDX_Point, SurgeBoundary
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_password_hash(password: str) -> str:
    """Хэширует пароль (как в repository.py)"""
    return hashlib.sha256(password.encode()).hexdigest()


def seed_users(session):
    """Создаёт тестовых пользователей"""
    logger.info("👥 Генерация пользователей...")
    
    users_data = [
        {"username": "admin", "password": "admin123", "role": "ADMIN"},
        {"username": "engineer1", "password": "eng123", "role": "ENGINEER"},
        {"username": "engineer2", "password": "eng456", "role": "ENGINEER"},
        {"username": "operator1", "password": "op123", "role": "OPERATOR"},
        {"username": "operator2", "password": "op456", "role": "OPERATOR"},
        {"username": "operator3", "password": "op789", "role": "OPERATOR"},
    ]
    
    for user_data in users_data:
        user = User(
            Username=user_data["username"],
            PasswordHash=generate_password_hash(user_data["password"]),
            Role=user_data["role"],
            IsActive=True
        )
        session.add(user)
    
    session.commit()
    logger.info(f"✅ Создано {len(users_data)} пользователей")


def seed_events(session, count=1000):
    """Генерирует реалистичные события с помпажными ситуациями"""
    logger.info(f"📊 Генерация {count} событий...")
    
    base_time = datetime.now() - timedelta(days=7)
    
    for i in range(count):
        # Эмуляция работы компрессора
        # 80% времени - нормальная работа, 15% - предупреждение, 5% - помпаж
        scenario = random.random()
        
        if scenario < 0.80:
            # Нормальная работа
            margin = random.uniform(20, 80)
            q = random.uniform(50, 90)
            h = random.uniform(800, 1500)
            valve_pos = random.uniform(0, 30)
            status = False
        elif scenario < 0.95:
            # Предупреждение (маржа падает)
            margin = random.uniform(5, 20)
            q = random.uniform(30, 60)
            h = random.uniform(600, 1000)
            valve_pos = random.uniform(30, 70)
            status = False
        else:
            # Помпаж (критическая ситуация)
            margin = random.uniform(0, 5)
            q = random.uniform(10, 40)
            h = random.uniform(400, 800)
            valve_pos = random.uniform(70, 100)
            status = True
        
        # Производная расхода
        dqdt = random.uniform(-5, 5)
        
        # Давления
        p_in = random.uniform(1.5, 3.0)
        p_out = p_in + (h / 100.0)  # Связь с напором
        t_in = random.uniform(20, 40)
        
        event = EventLog(
            Timestamp=base_time + timedelta(seconds=i * 10),
            Q=q,
            H=h,
            P_in=p_in,
            P_out=p_out,
            T_in=t_in,
            Margin=margin,
            dQdt=dqdt,
            ValvePosition=valve_pos,
            RuleFired=f"margin={'Low' if margin < 10 else 'Mid' if margin < 30 else 'High'}",
            Status=status,
            CompressorID=1,  # CC-45X
            UserID=1  # admin
        )
        session.add(event)
    
    session.commit()
    logger.info(f"✅ Создано {count} событий")


def seed_gdx_points(session):
    """Генерирует точки ГДХ для графиков"""
    logger.info("📈 Генерация точек ГДХ...")
    
    # Создаём заголовки кривых для разных оборотов
    rpms = [5000, 7500, 10000, 12500]
    
    for rpm in rpms:
        header = GDX_Header(
            CompressorID=1,
            CompositionID=1,
            RPM=rpm
        )
        session.add(header)
        session.flush()  # Получаем CurveID
        
        # Генерируем точки кривой (парабола)
        num_points = 20
        for i in range(num_points):
            q = 20 + i * 4  # От 20 до 96
            # Параболическая зависимость H от Q
            h = 2000 - 0.02 * (q - 50) ** 2 + random.uniform(-50, 50)
            efficiency = 0.75 + random.uniform(-0.05, 0.05)
            power = q * h / 1000 * 0.8
            
            point = GDX_Point(
                CurveID=header.CurveID,
                PointIndex=i,
                Q=q,
                H=h,
                Efficiency=efficiency,
                Power=power
            )
            session.add(point)
    
    session.commit()
    logger.info(f"✅ Создано {len(rpms)} кривых ГДХ")


def seed_surge_boundary(session):
    """Генерирует линию помпажа"""
    logger.info("🚨 Генерация линии помпажа...")
    
    # Линия помпажа (граница устойчивой работы)
    surge_points = [
        (25, 1800),
        (30, 1700),
        (35, 1600),
        (40, 1500),
        (45, 1400),
        (50, 1300),
        (55, 1200),
        (60, 1100),
        (65, 1000),
        (70, 900),
    ]
    
    for q, h in surge_points:
        boundary = SurgeBoundary(
            CompressorID=1,
            Q_surge=q,
            H_surge=h
        )
        session.add(boundary)
    
    session.commit()
    logger.info(f"✅ Создано {len(surge_points)} точек линии помпажа")


def run_seeding(db_url="sqlite:///anti_surge_prototype.db"):
    """Запускает генерацию всех тестовых данных"""
    engine = create_engine(db_url, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # Проверяем, есть ли уже данные
        if session.query(User).count() > 0:
            logger.info("ℹ️ Данные уже есть, пропускаем генерацию")
            return
        
        logger.info("🌱 Начинаем генерацию тестовых данных...")
        
        seed_users(session)
        seed_events(session, count=1000)
        seed_gdx_points(session)
        seed_surge_boundary(session)
        
        logger.info("✅ Все тестовые данные сгенерированы!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка генерации данных: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    run_seeding()