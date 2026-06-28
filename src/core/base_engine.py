"""Абстрактный интерфейс для движков обработки данных."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class IEngine(ABC):
    """Интерфейс движка — определяет контракт для CoreBridge и AntiSurgeCore."""

    @abstractmethod
    def init_py(self) -> None: ...

    @abstractmethod
    def update_config(self, config: Dict[str, Any]) -> None: ...

    @abstractmethod
    def process_sensor_data(self, Q: float, P_in: float, P_out: float, T: float) -> Any: ...

    @abstractmethod
    def get_last_processed(self) -> Any: ...

    @abstractmethod
    def is_surge_detected(self) -> bool: ...