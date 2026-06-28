# dto/dto.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict

# ==========================================
# 1. SensorData
# Сырые данные с датчиков (вход в ядро)
# ==========================================
@dataclass
class SensorData:
    Q: float = 0.0
    P_in: float = 0.0
    P_out: float = 0.0
    T: float = 20.0
    timestamp: datetime = field(default_factory=datetime.now)

# ==========================================
# 2. ProcessedData
# Отфильтрованные и нормализованные данные
# ==========================================
@dataclass
class ProcessedData:
    Q_rel: float = 0.0
    H_rel: float = 0.0
    margin: float = 0.0
    dQdt: float = 0.0

@dataclass
class FuzzySet:
    degrees: Dict[str, float] = field(default_factory=dict)

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
    valveOpenPercent: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    status: str = "NORMAL"
    lastUsedRule: str = ""
    reactionTime: float = 0.0
    compressorName: str = "CC-45X"
    # ✅ НОВЫЕ ПОЛЯ для телеметрии
    gasComposition: str = "Природный газ (CH₄ 92%)"
    surgeStatus: str = "АПЗ: Норма"
    marginPercent: float = 0.0

# ==========================================
# 6. Point
# Точка на плоскости ГДХ для визуализации
# ==========================================
@dataclass
class Point:
    Q: float = 0.0
    H: float = 0.0
    efficiency: float = 0.0