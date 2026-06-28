# core/anti_surge_core.py
"""
Заглушка для реального C++ ядра.
После компиляции .pyd этот файл будет заменён на биндинг.
"""
from typing import Dict, Any, Optional
from core.base_engine import IEngine
from dto.dto import ProcessedData, SensorData


class AntiSurgeCore(IEngine):  # ✅ Наследуем от IEngine
    """Реальное C++ ядро (заглушка)"""

    def __init__(self):
        self._initialized = False
        self._last_processed: Optional[ProcessedData] = None
        self._surge_detected = False

    def init_py(self) -> None:
        self._initialized = True

    def update_config(self, config: Dict[str, Any]) -> None:
        pass

    def process_sensor_data(self, Q: float, P_in: float, P_out: float, T: float) -> Any:
        return None

    def get_last_processed(self) -> Optional[ProcessedData]:
        return self._last_processed

    def is_surge_detected(self) -> bool:
        return self._surge_detected

    def get_sensor_data(self) -> Optional[SensorData]:
        return None