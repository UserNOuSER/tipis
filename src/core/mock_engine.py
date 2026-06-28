import sys
import time
import random
from datetime import datetime
from typing import Dict, Any, Optional
from dto.dto import SensorData, ProcessedData, FuzzySet, RuleOutput, ControlSignal, Point
from simpful import FuzzySystem, AutoTriangle  # ty:ignore[unresolved-import]
from core.base_engine import IEngine 

# ==========================================
# Слой Controller: Вычислительное ядро (Mock)
# ==========================================

class DataProcessor:
    """Эмуляция предварительной обработки данных с датчиков."""
    
    def __init__(self):
        self.filter_window = 5
        self._q_history = []
        self._noise_level = 0.02  # Уровень шума датчиков (2%)
        
    def add_noise(self, value: float) -> float:
        """Эмуляция шума датчиков"""
        return value * (1.0 + random.uniform(-self._noise_level, self._noise_level))
    
    def filter(self, data: SensorData) -> ProcessedData:
        """Фильтрация шума, нормализация и расчет производной."""
        # Добавляем шум к показаниям датчиков
        q_noisy = self.add_noise(data.Q)
        p_in_noisy = self.add_noise(data.P_in)
        p_out_noisy = self.add_noise(data.P_out)
        
        # Нормализация (приведение к относительным величинам)
        q_nom = 100.0  # Номинальный расход
        h_nom = 2000.0  # Номинальный напор
        
        q_rel = q_noisy / q_nom
        
        # Расчет напора из разницы давлений
        h = (p_out_noisy - p_in_noisy) * 100.0
        h_rel = h / h_nom
        
        # Эмуляция расчета маржи помпажа
        surge_line_q = 0.4
        if q_rel > surge_line_q:
            margin = ((q_rel - surge_line_q) / (1.0 - surge_line_q)) * 100.0
        else:
            margin = 0.0  # Ниже линии помпажа
        
        # Расчет производной dQ/dt
        self._q_history.append(q_noisy)
        if len(self._q_history) > 1:
            dt = 0.1  # Эмуляция частоты 10 Гц
            dqdt = (self._q_history[-1] - self._q_history[-2]) / dt
        else:
            dqdt = 0.0
            
        # Ограничиваем историю
        if len(self._q_history) > self.filter_window:
            self._q_history.pop(0)

        return ProcessedData(Q_rel=q_rel, H_rel=h_rel, margin=margin, dQdt=dqdt)

    def filter_noise(self, data_list: list) -> list:
        """Метод-заглушка для обратной совместимости"""
        return data_list


class FuzzyEngine:
    """Механизм нечёткого вывода на базе simpful (Мамдани)."""
    
    def __init__(self):
        self.fs = FuzzySystem(show_banner=False)  # Отключаем баннер
        self._setup_default_fuzzy_system()
        self._last_rule_fired = ""
    
    def _setup_default_fuzzy_system(self):
        """Создаёт базовую систему нечёткого вывода"""
        
        # 1. Входная переменная: Маржа помпажа (0-100%)
        # AutoTriangle автоматически создаёт 3 треугольных нечётких множества
        margin_lv = AutoTriangle(
            n_sets=3, 
            terms=["Low", "Mid", "High"], 
            universe_of_discourse=[0, 100]
        )
        self.fs.add_linguistic_variable("margin", margin_lv)
        
        # 2. Входная переменная: Скорость изменения расхода dQ/dt (-10 до +10)
        dqdt_lv = AutoTriangle(
            n_sets=3, 
            terms=["Neg", "Zero", "Pos"], 
            universe_of_discourse=[-10, 10]
        )
        self.fs.add_linguistic_variable("dqdt", dqdt_lv)
        
        # 3. Выходная переменная: Положение клапана (0-100%)
        valve_lv = AutoTriangle(
            n_sets=5, 
            terms=["Close", "Open_25", "Open_50", "Open_75", "Open_100"], 
            universe_of_discourse=[0, 100]
        )
        self.fs.add_linguistic_variable("valve", valve_lv)
        
        # 4. База правил (IF-THEN)
        self.fs.add_rules([
            "IF (margin IS Low) AND (dqdt IS Neg) THEN (valve IS Open_100)",
            "IF (margin IS Low) AND (dqdt IS Zero) THEN (valve IS Open_75)",
            "IF (margin IS Low) THEN (valve IS Open_50)",
            "IF (margin IS Mid) AND (dqdt IS Neg) THEN (valve IS Open_50)",
            "IF (margin IS Mid) THEN (valve IS Open_25)",
            "IF (margin IS High) THEN (valve IS Close)",
        ])
        
        print("✅ FuzzyEngine инициализирован с simpful")
    
    def load_rules_from_db(self, rules_config: dict):
        """Загрузка правил из БД (через CoreBridge)"""
        if "rules" not in rules_config or not rules_config["rules"]:
            return
        
        # В будущем здесь будет динамическая загрузка правил из БД
        print(f"ℹ️ Загрузка правил из БД: {len(rules_config['rules'])} правил")
    
    def fuzzify(self, inputs: ProcessedData) -> FuzzySet:
        """Фаззификация: перевод четких значений в степени принадлежности."""
        # Устанавливаем входные значения
        margin_val = max(0, min(100, inputs.margin))
        dqdt_val = max(-10, min(10, inputs.dQdt))
        
        self.fs.set_variable("margin", margin_val)
        self.fs.set_variable("dqdt", dqdt_val)
        
        # Получаем степени принадлежности через прямой вызов функций
        try:
            margin_sets = self.fs.get_fuzzy_sets("margin")
            degrees = {
                "Low": margin_sets["Low"].get_value(margin_val),
                "Mid": margin_sets["Mid"].get_value(margin_val),
                "High": margin_sets["High"].get_value(margin_val),
            }
        except Exception as e:
            print(f"⚠️ Ошибка фаззификации: {e}", file=sys.stderr)
            degrees = {"Low": 0.0, "Mid": 0.0, "High": 0.0}
        
        return FuzzySet(degrees=degrees)
    
    def evaluate_rules(self, fuzzied: FuzzySet) -> RuleOutput:
        """Оценка базы правил (IF-THEN) через simpful"""
        try:
            # Выполняем нечёткий вывод (Метод Мамдани)
            result = self.fs.Mamdani_inference(["valve"])
            valve_pos = result["valve"]
            
            # Определяем, какое правило сработало (упрощённо)
            if valve_pos > 75:
                rule_label = "margin=Low AND dqdt=Neg → valve=Open_100"
            elif valve_pos > 50:
                rule_label = "margin=Low → valve=Open_75"
            elif valve_pos > 25:
                rule_label = "margin=Mid → valve=Open_50"
            else:
                rule_label = "margin=High → valve=Close"
            
            self._last_rule_fired = rule_label
            
            return RuleOutput(
                aggregatedArea=1.0,
                centroidSum=valve_pos,
                label=rule_label
            )
        except Exception as e:
            print(f"❌ Ошибка нечёткого вывода: {e}", file=sys.stderr)
            return RuleOutput(aggregatedArea=0.0, centroidSum=0.0, label="Error")
    
    def defuzzify(self, output: RuleOutput) -> float:
        """Дефаззификация (уже выполнена в evaluate_rules через simpful)"""
        return output.centroidSum
    
    def get_last_rule_fired(self) -> str:
        """Возвращает последнее сработавшее правило"""
        return self._last_rule_fired


class AntiSurgeCore:
    """Главный оркестратор цикла защиты (Фасад)."""
    
    def __init__(self):
        self._is_initialized = False
        self._surge_detected = False
        self.processor = DataProcessor()
        self.engine = FuzzyEngine()
        self._last_processed = ProcessedData()
        self._cycle_count = 0

    def initialize(self, config_path: str = "mock_config.ini"):
        """Инициализация ядра (загрузка конфигов, правил)."""
        self._is_initialized = True
        print(f"✅ AntiSurgeCore инициализирован (config: {config_path})")

    def update_config(self, config: dict):
        """Обновление конфигурации на лету (без перезапуска)"""
        if "rules" in config:
            self.engine.load_rules_from_db(config)

    def get_system_status(self) -> str:
        return "ГОТОВ К РАБОТЕ" if self._is_initialized else "ОШИБКА"

    def process_sensor_data(self, data: SensorData) -> ControlSignal:
        """Основной цикл обработки одного среза данных с датчиков."""
        start_time = time.perf_counter()  # Замер времени начала цикла
        
        if not self._is_initialized:
            return ControlSignal(
                valveOpenPercent=0.0, 
                status="ERROR",
                lastUsedRule="N/A",
                reactionTime=0.0
            )

        try:
            # 1. Предобработка
            processed = self.processor.filter(data)
            self._last_processed = processed

            # 2. Нечетный вывод (через simpful)
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

            # 4. Замер времени реакции
            end_time = time.perf_counter()
            reaction_time_ms = (end_time - start_time) * 1000.0  # Конвертируем в мс
            
            self._cycle_count += 1
            
            # 5. Формирование управляющего сигнала
            return ControlSignal(
                valveOpenPercent=max(0.0, min(100.0, valve_pos)),
                timestamp=datetime.now(),
                status=status,
                lastUsedRule=rule_out.label,
                reactionTime=reaction_time_ms
            )
            
        except Exception as e:
            print(f"❌ Ошибка в цикле обработки: {e}", file=sys.stderr)
            return ControlSignal(
                valveOpenPercent=0.0,
                status="ERROR",
                lastUsedRule="Exception",
                reactionTime=0.0
            )

    def is_surge_detected(self) -> bool:
        return self._surge_detected
        
    def get_last_processed(self) -> ProcessedData:
        """Возвращает последние обработанные данные"""
        return self._last_processed
    
    def get_cycle_count(self) -> int:
        """Возвращает количество обработанных циклов"""
        return self._cycle_count


class CoreBridge(IEngine):  # ✅ Наследуем от IEngine
    """Адаптер для связи Python ↔ C++ (pybind11). В моке оборачивает AntiSurgeCore."""

    def __init__(self):
        self.core = AntiSurgeCore()
        self._db_repository = None

    def set_db_repository(self, repository):
        self._db_repository = repository

    def init_py(self) -> None:  # ✅ Добавляем аннотацию
        """Инициализация ядра"""
        self.core.initialize("mock_config.ini")
        if self._db_repository:
            try:
                config = self._db_repository.load_fuzzy_config(config_id=1, version="1.0.0")
                if config:
                    self.core.update_config(config)
            except Exception as e:
                print(f"⚠️ Не удалось загрузить конфиг из БД: {e}", file=sys.stderr)

    def process_sensor_data(self, Q: float, P_in: float, P_out: float, T: float) -> ControlSignal:  # ✅
        """Основной метод для обработки данных"""
        data = SensorData(Q=Q, P_in=P_in, P_out=P_out, T=T)
        return self.core.process_sensor_data(data)

    def update_config(self, config: Dict[str, Any]) -> None:  # ✅ Добавляем аннотацию
        """Обновление конфигурации на лету"""
        self.core.update_config(config)

    # ===== ✅ НОВЫЕ МЕТОДЫ (делегирование к self.core) =====

    def get_last_processed(self) -> ProcessedData:
        """Возвращает последние обработанные данные"""
        return self.core.get_last_processed()

    def is_surge_detected(self) -> bool:
        """Проверяет, обнаружен ли помпаж"""
        return self.core.is_surge_detected()

    def get_sensor_data(self) -> Optional[SensorData]:
        """Получает данные с датчиков (заглушка для мока)"""
        return None