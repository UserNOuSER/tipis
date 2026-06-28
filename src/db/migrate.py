"""
Миграция БД: добавление таблицы Compressor и поля Name в FuzzyConfigs.
Запускается ОДИН РАЗ при первом старте после обновления моделей.
"""
from sqlalchemy import create_engine, text, inspect  # ty:ignore[unresolved-import]
from db.init_db import Base
from db.models import Compressor, FuzzyConfig
import logging

logger = logging.getLogger(__name__)


def run_migration(db_url: str = "sqlite:///anti_surge_prototype.db"):
    """Выполняет миграцию БД"""
    engine = create_engine(db_url, echo=False)
    inspector = inspect(engine)
    
    existing_tables = inspector.get_table_names()
    
    with engine.connect() as conn:
        # 1. Создаём таблицу Compressors, если её нет
        if 'Compressors' not in existing_tables:
            logger.info("🏗️ Создание таблицы Compressors...")
            Base.metadata.tables['Compressors'].create(engine)
            logger.info("✅ Таблица Compressors создана")
        else:
            logger.info("ℹ️ Таблица Compressors уже существует")
        
        # 2. Добавляем колонку Name в FuzzyConfigs, если её нет
        if 'FuzzyConfigs' in existing_tables:
            columns = [col['name'] for col in inspector.get_columns('FuzzyConfigs')]
            
            if 'Name' not in columns:
                logger.info("🏗️ Добавление колонки Name в FuzzyConfigs...")
                conn.execute(text("ALTER TABLE FuzzyConfigs ADD COLUMN Name VARCHAR(100)"))
                conn.commit()
                logger.info("✅ Колонка Name добавлена")
            
            if 'Description' not in columns:
                logger.info("🏗️ Добавление колонки Description в FuzzyConfigs...")
                conn.execute(text("ALTER TABLE FuzzyConfigs ADD COLUMN Description VARCHAR(500)"))
                conn.commit()
                logger.info("✅ Колонка Description добавлена")
        
        # 3. Заполняем тестовыми данными
        _seed_test_data(conn, inspector)
    
    logger.info("✅ Миграция завершена")


def _seed_test_data(conn, inspector):
    """Заполняет БД тестовыми данными"""
    # Проверяем, есть ли уже компрессоры
    result = conn.execute(text("SELECT COUNT(*) FROM Compressors")).scalar()
    if result > 0:
        logger.info("ℹ️ Тестовые данные уже есть, пропускаем")
        return
    
    logger.info("🌱 Заполнение тестовыми данными...")
    
    # 1. Обновляем существующий конфиг (ID=1) — даём ему имя
    conn.execute(text("""
        UPDATE FuzzyConfigs 
        SET Name = 'Стандартный', 
            Description = 'Базовые правила для большинства компрессоров'
        WHERE ConfigID = 1
    """))
    
    # 2. Создаём дополнительные профили
    conn.execute(text("""
        INSERT INTO FuzzyConfigs (Version, Name, Description, InputVars, OutputVars, MembershipParams)
        VALUES 
        ('1.0.0', 'Агрессивный', 'Раннее срабатывание для критичных установок', 
         '{"margin": ["Low", "Mid", "High"], "dQdt": ["Neg", "Zero", "Pos"]}',
         '{"valve": ["Close", "Open_25", "Open_50", "Open_75", "Open_100"]}',
         '{}'),
        ('1.0.0', 'Экономный', 'Поздняя реакция для стабильных режимов',
         '{"margin": ["Low", "Mid", "High"], "dQdt": ["Neg", "Zero", "Pos"]}',
         '{"valve": ["Close", "Open_25", "Open_50", "Open_75", "Open_100"]}',
         '{}')
    """))
    
    # 3. Создаём компрессоры
    conn.execute(text("""
        INSERT INTO Compressors (Name, Model, ProfileID)
        VALUES 
        ('CC-45X', 'Centac CC-45X', 1),
        ('SK-600B', 'Siemens SK-600B', 1),
        ('K-101A', 'Kobe K-101A', 2),
        ('VHP-72', 'Ariel VHP-72', 1),
        ('CB-200', 'FS-Elliott CB-200', 3),
        ('T-500R', 'Solar T-500R', 1)
    """))
    
    # 4. Добавляем правила для профиля "Агрессивный" (ConfigID=2)
    conn.execute(text("""
        INSERT INTO FuzzyRules (ConfigID, Version, AntecedentKey, Consequent, Weight, Priority)
        VALUES 
        (2, '1.0.0', 'margin=Mid', 'valve=Open_50', 1.0, 1),
        (2, '1.0.0', 'margin=High', 'valve=Open_25', 1.0, 2),
        (2, '1.0.0', 'margin=Low', 'valve=Open_100', 1.0, 3)
    """))
    
    # 5. Добавляем правила для профиля "Экономный" (ConfigID=3)
    conn.execute(text("""
        INSERT INTO FuzzyRules (ConfigID, Version, AntecedentKey, Consequent, Weight, Priority)
        VALUES 
        (3, '1.0.0', 'margin=Low AND dQdt=Neg', 'valve=Open_75', 1.0, 1),
        (3, '1.0.0', 'margin=Low', 'valve=Open_50', 1.0, 2),
        (3, '1.0.0', 'margin=Mid', 'valve=Close', 1.0, 3)
    """))
    
    conn.commit()
    logger.info("✅ Тестовые данные заполнены: 3 профиля, 6 компрессоров")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_migration()