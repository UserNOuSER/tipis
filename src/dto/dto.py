# core/dto.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict

# ==========================================
# 1. SensorData
# Сырые данные с датчиков (вход в ядро)
# ==========================================
@dataclass
class SensorData:
    Q: float = 0.0                # Расход
    P_in: float = 0.0             # Давление на входе
    P_out: float = 0.0            # Давление на выходе
    T: float = 20.0               # Температура
    timestamp: datetime = field(default_factory=datetime.now)

# ==========================================
# 2. ProcessedData
# Отфильтрованные и нормализованные данные
# ==========================================
@dataclass
class ProcessedData:
    Q_rel: float = 0.0            # Относительный расход
    H_rel: float = 0.0            # Относительный напор
    margin: float = 0.0           # Маржа помпажа
    dQdt: float = 0.0             # Скорость изменения расхода (производная)

# ==========================================
# 3. FuzzySet
# Результат фаззификации (степени принадлежности)
# В Python Map<string, float> -> Dict[str, float]
# ==========================================
@dataclass
class FuzzySet:
    degrees: Dict[str, float] = field(default_factory=dict) 
    # Пример: {"Low": 0.2, "Mid": 0.8, "High": 0.0}

# ==========================================
# 4. RuleOutput
# Результат оценки правил перед дефаззификацией
# ==========================================
@dataclass
class RuleOutput:
    aggregatedArea: float = 0.0
    centroidSum: float = 0.0
    label: str = ""

# ==========================================
# 5. ControlSignal
# Финальный управляющий сигнал
# ==========================================
@dataclass
class ControlSignal:
    valveOpenPercent: float = 0.0 # % открытия байпасного клапана
    timestamp: datetime = field(default_factory=datetime.now)
    status: str = "NORMAL"        # Статус (например, "NORMAL", "WARNING", "SURGE")

# ==========================================
# 6. Point
# Точка на плоскости ГДХ для визуализации
# ==========================================
@dataclass
class Point:
    Q: float = 0.0
    H: float = 0.0
    efficiency: float = 0.0