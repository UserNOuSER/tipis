# db/seed_gdx.py
"""
Добавляет точки ГДХ и линию помпажа в БД.
Запускается один раз, если данных нет.
"""
from sqlalchemy import create_engine, text  # ty:ignore[unresolved-import]
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_gdx_data(db_url="sqlite:///anti_surge_prototype.db"):
    """Добавляет тестовые данные ГДХ"""
    engine = create_engine(db_url, echo=False)
    
    with engine.connect() as conn:
        # Проверяем, есть ли уже данные
        result = conn.execute(text("SELECT COUNT(*) FROM GDX_Headers")).scalar()
        if result > 0:
            logger.info(f"ℹ️ В БД уже есть {result} кривых ГДХ, пропускаем")
            return
        
        logger.info("📈 Добавляем точки ГДХ...")
        
        # Создаём заголовки кривых для разных оборотов
        rpms = [5000, 7500, 10000, 12500]
        
        for rpm in rpms:
            # Вставляем заголовок
            conn.execute(text("""
                INSERT INTO GDX_Headers (CompressorID, CompositionID, RPM)
                VALUES (1, 1, :rpm)
            """), {"rpm": rpm})
            
            # Получаем CurveID
            curve_id = conn.execute(text(
                "SELECT CurveID FROM GDX_Headers WHERE RPM = :rpm"
            ), {"rpm": rpm}).scalar()
            
            # Генерируем точки кривой (парабола)
            num_points = 20
            for i in range(num_points):
                q = 20 + i * 4  # От 20 до 96
                # Параболическая зависимость H от Q
                h = 2000 - 0.02 * (q - 50) ** 2
                efficiency = 0.75
                power = q * h / 1000 * 0.8
                
                conn.execute(text("""
                    INSERT INTO GDX_Points (CurveID, PointIndex, Q, H, Efficiency, Power)
                    VALUES (:curve_id, :point_index, :q, :h, :efficiency, :power)
                """), {
                    "curve_id": curve_id,
                    "point_index": i,
                    "q": q,
                    "h": h,
                    "efficiency": efficiency,
                    "power": power
                })
        
        logger.info(f"✅ Создано {len(rpms)} кривых ГДХ")
        
        # Добавляем линию помпажа
        logger.info("🚨 Добавляем линию помпажа...")
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
            conn.execute(text("""
                INSERT INTO SurgeBoundaries (CompressorID, Q_surge, H_surge)
                VALUES (1, :q, :h)
            """), {"q": q, "h": h})
        
        conn.commit()
        logger.info(f"✅ Создано {len(surge_points)} точек линии помпажа")


if __name__ == "__main__":
    seed_gdx_data()