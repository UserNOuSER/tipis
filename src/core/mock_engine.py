import sys
import traceback
import os

# --- ФИКС ПУТЕЙ ИМПОРТА ---
# Получаем абсолютный путь к папке, где лежит main.py (src/ui/)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Поднимаемся на уровень выше, чтобы найти папку src (или корень проекта)
# Если db лежит в src/db, то поднимаемся на 1 уровень. Если в корне, то на 2.
project_root = os.path.dirname(current_dir) 
# Добавляем корень проекта в пути поиска Python
if project_root not in sys.path:
    sys.path.append(project_root)
# ----------------------------
try:
    import math
    import random
    from datetime import datetime
    from dto.dto import SensorData, ProcessedData, FuzzySet, RuleOutput, ControlSignal, Point
except Exception as e:
    print(f"Ошибка импорта: {e}", file=sys.stderr)
    traceback.print_exc()
    sys.exit(1)

# ==========================================
# Слой Controller: Вычислительное ядро
# ==========================================

class DataProcessor:
    """Эмуляция предварительной обработки данных с датчиков."""
    def __init__(self):
        self.filter_window = 5
        self._q_history = []

    def filter(self, data: SensorData) -> ProcessedData:
        """Фильтрация шума, нормализация и расчет производной."""
        # Эмуляция нормализации (приведение к относительным величинам)
        # Допустим, номинальный расход Q_nom = 100, номинальный напор H_nom = 2000
        q_nom = 100.0
        h_nom = 2000.0
        
        q_rel = data.Q / q_nom
        
        # Расчет напора из разницы давлений (упрощенная физическая модель)
        h = (data.P_out - data.P_in) * 100.0 
        h_rel = h / h_nom
        
        # Эмуляция расчета маржи помпажа (расстояние до линии помпажа в %)
        # Линия помпажа условно на Q_rel = 0.4
        surge_line_q = 0.4
        margin = ((q_rel - surge_line_q) / (1.0 - surge_line_q)) * 100.0
        
        # Расчет производной dQ/dt
        self._q_history.append(data.Q)
        if len(self._q_history) > 1:
            # dt = 0.1 сек (эмуляция частоты 10 Гц для мока)
            dqdt = (self._q_history[-1] - self._q_history[-2]) / 0.1 
        else:
            dqdt = 0.0
            
        # Ограничиваем историю
        if len(self._q_history) > self.filter_window:
            self._q_history.pop(0)

        return ProcessedData(Q_rel=q_rel, H_rel=h_rel, margin=margin, dQdt=dqdt)

    # Метод-заглушка для обратной совместимости, если где-то вызывается
    def filter_noise(self, data_list: list) -> list:
        return data_list 


class FuzzyEngine:
    """Эмуляция механизма нечёткого вывода (Мамдани)."""
    
    def fuzzify(self, inputs: ProcessedData) -> FuzzySet:
        """Фаззификация: перевод четких значений в степени принадлежности."""
        # Эмуляция терм-множества для margin: {Low, Mid, High}
        degrees = {"Low": 0.0, "Mid": 0.0, "High": 0.0}
        
        if inputs.margin < 15.0:
            degrees["Low"] = 1.0 - (inputs.margin / 15.0)
            degrees["Mid"] = inputs.margin / 15.0
        else:
            degrees["High"] = min(1.0, (inputs.margin - 15.0) / 20.0)
            degrees["Mid"] = max(0.0, 1.0 - degrees["High"])
            
        return FuzzySet(degrees=degrees)

    def evaluate_rules(self, fuzzied: FuzzySet) -> RuleOutput:
        """Оценка базы правил (IF-THEN)."""
        # Простейшая эмуляция: если Low > 0.5, то срабатывает правило открытия клапана
        if fuzzied.degrees.get("Low", 0) > 0.5:
            return RuleOutput(aggregatedArea=1.0, centroidSum=100.0, label="Open_100")
        elif fuzzied.degrees.get("Mid", 0) > 0.5:
            return RuleOutput(aggregatedArea=1.0, centroidSum=50.0, label="Open_50")
        else:
            return RuleOutput(aggregatedArea=1.0, centroidSum=0.0, label="Close")

    def defuzzify(self, output: RuleOutput) -> float:
        """Дефаззификация (метод центра тяжести)."""
        if output.aggregatedArea > 0:
            return output.centroidSum / output.aggregatedArea
        return 0.0


class AntiSurgeCore:
    """Главный оркестратор цикла защиты (Фасад)."""
    def __init__(self):
        self._is_initialized = False
        self._surge_detected = False
        self.processor = DataProcessor()
        self.engine = FuzzyEngine()
        self._last_processed = None

    def initialize(self, config_path: str):
        """Инициализация ядра (загрузка конфигов, правил)."""
        self._is_initialized = True

    def get_system_status(self) -> str:
        return "ГОТОВ К РАБОТЕ" if self._is_initialized else "ОШИБКА"

    def process_sensor_data(self, data: SensorData) -> ControlSignal:
        """Основной цикл обработки одного среза данных с датчиков."""
        if not self._is_initialized:
            return ControlSignal(valveOpenPercent=0.0, status="ERROR")

        # 1. Предобработка
        processed = self.processor.filter(data)
        self._last_processed = processed

        # 2. Нечеткий вывод
        fuzzied = self.engine.fuzzify(processed)
        rule_out = self.engine.evaluate_rules(fuzzied)
        valve_pos = self.engine.defuzzify(rule_out)

        # 3. Определение статуса (логика тревог)
        status = "NORMAL"
        if processed.margin < 10.0:
            status = "WARNING"
        if processed.margin < 5.0:
            status = "SURGE"
            self._surge_detected = True
        else:
            self._surge_detected = False

        # 4. Формирование управляющего сигнала
        return ControlSignal(
            valveOpenPercent=max(0.0, min(100.0, valve_pos)),
            timestamp=datetime.now(),
            status=status
        )

    def is_surge_detected(self) -> bool:
        return self._surge_detected
        
    def get_last_processed(self) -> ProcessedData:
        """Возвращает последние обработанные данные (для построения графика Q-H)."""
        return self._last_processed


class CoreBridge:
    """Адаптер для связи Python ↔ C++ (pybind11). В моке просто оборачивает ядро."""
    def __init__(self):
        self.core = AntiSurgeCore()
        
    def init_py(self):
        self.core.initialize("mock_config.ini")
        
    def process_sensor_data(self, Q: float, P_in: float, P_out: float, T: float) -> ControlSignal:
        data = SensorData(Q=Q, P_in=P_in, P_out=P_out, T=T)
        return self.core.process_sensor_data(data)