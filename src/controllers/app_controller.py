import json
import random
import logging
from datetime import datetime
from dto.dto import SensorData, ProcessedData, ControlSignal
import dearpygui.dearpygui as dpg  # ty:ignore[unresolved-import]
from db.repository import Database
from core.mock_engine import CoreBridge

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AppController:
    """Контроллер: связывает UI, Core и БД"""
    
    def __init__(self):
        # Инициализация ядра через CoreBridge
        self.bridge = CoreBridge()
        self.db = Database()
        self.telemetry_panel = None
        
        self.current_sensor_data = SensorData()
        self.current_command = None
        
        self.flow_history = []
        self.pressure_history = []
        self.time_history = []
        
        # ✅ ВАЖНО: НЕ вызываем dpg здесь!
        # Загружаем конфигурацию из БД
        self._load_initial_config()

    def set_telemetry_panel(self, panel):
        """Устанавливает ссылку на панель телеметрии"""
        self.telemetry_panel = panel

    def _load_initial_config(self):
        """Загружает правила нечеткой логики из БД при старте"""
        try:
            config = self.db.load_fuzzy_config(config_id=1, version="1.0.0")
            if config:
                self.bridge.update_config(config)
                logger.info("✅ Конфигурация FuzzyEngine загружена из БД")
            else:
                logger.warning("⚠️ Конфигурация не найдена, используются дефолтные правила")
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации: {e}")

    def initialize_system(self):
        """Инициализация системы (БЕЗ обращения к DearPyGUI!)"""
        try:
            self.bridge.init_py()
            logger.info("✅ AntiSurgeCore инициализирован")
            # ✅ НЕ обращаемся к dpg здесь — UI ещё не создан!
        except Exception as e:
            logger.error(f"Ошибка инициализации: {e}")
            raise

    def update_status_ui(self, status: str, message: str):
        """Обновляет статус в UI (вызывается ПОСЛЕ создания UI)"""
        try:
            if not dpg.is_dearpygui_running():
                return
            
            if dpg.does_item_exist("status_text"):
                dpg.set_value("status_text", message)
                
                if status == "OK":
                    dpg.configure_item("status_text", color=(16, 185, 129, 255))
                elif status == "ERROR":
                    dpg.configure_item("status_text", color=(239, 68, 68, 255))
                elif status == "WARNING":
                    dpg.configure_item("status_text", color=(245, 158, 11, 255))
        except Exception as e:
            logger.error(f"Ошибка обновления UI: {e}")

    def process_data(self, sender=None, app_data=None):
        """Главный цикл обработки данных"""
        try:
            # 1. Эмуляция получения данных с датчиков
            q = 69.0 + random.uniform(-2, 2)
            p_in = 5.0 + random.uniform(-0.1, 0.1)
            p_out = 8.0 + random.uniform(-0.1, 0.1)
            t = 20.0 + random.uniform(-0.5, 0.5)
            
            self.current_sensor_data = SensorData(Q=q, P_in=p_in, P_out=p_out, T=t)
            
            # 2. Прогоняем через ядро
            self.current_command = self.bridge.process_sensor_data(
                Q=q, P_in=p_in, P_out=p_out, T=t
            )
            
            # 3. Получаем обработанные данные для телеметрии
            processed = self.bridge.core.get_last_processed()
            
            # Обновляем рабочую точку на графике
            if processed:
                # Предполагаем, что есть ссылка на surge_plot
                if hasattr(self, 'surge_plot') and self.surge_plot:
                    self.surge_plot.update_operating_point(processed.Q_rel, processed.H_rel)
            
            # 4. Обновление телеметрии
            if self.telemetry_panel and processed and self.current_command:
                self.telemetry_panel.update(
                    self.current_sensor_data,
                    processed,
                    self.current_command
                )
                
                # Обновляем общий статус в шапке
                status = self.current_command.status
                if dpg.does_item_exist("status_text"):
                    if status == "SURGE":
                        dpg.set_value("status_text", "⚠️ АКТИВНА ЗАЩИТА (ПОМПАЖ)")
                        dpg.configure_item("status_text", color=(239, 68, 68, 255))
                    elif status == "WARNING":
                        dpg.set_value("status_text", "⚠️ ПРИБЛИЖЕНИЕ К ПОМПАЖУ")
                        dpg.configure_item("status_text", color=(245, 158, 11, 255))
                    else:
                        dpg.set_value("status_text", "✅ НОРМА")
                        dpg.configure_item("status_text", color=(16, 185, 129, 255))

            # 5. Показываем модальное окно при помпаже
            if self.bridge.core.is_surge_detected():
                if dpg.does_item_exist("surge_alert"):
                    dpg.configure_item("surge_alert", show=True)

            # 6. СОХРАНЕНИЕ В БД
            if processed and self.current_command:
                event_data = {
                    "timestamp": datetime.utcnow(),
                    "Q": processed.Q_rel,
                    "H": processed.H_rel,
                    "P_in": self.current_sensor_data.P_in,
                    "P_out": self.current_sensor_data.P_out,
                    "T_in": self.current_sensor_data.T,
                    "margin": processed.margin,
                    "dQdt": processed.dQdt,
                    "valve_position": self.current_command.valveOpenPercent,
                    "status": self.current_command.status == "SURGE",
                    "compressor_id": 1,
                    "user_id": 1
                }
                self.db.save_event_log(event_data)
            
            # 7. Обновление графиков
            self.update_charts()
            
        except Exception as e:
            logger.error(f"Ошибка в process_data: {e}")

    def update_charts(self):
        """Обновление графиков"""
        processed = self.bridge.core.get_last_processed()
        if not processed:
            return
        
        self.flow_history.append(processed.Q_rel)
        self.pressure_history.append(processed.H_rel)
        self.time_history.append(datetime.now().strftime("%H:%M:%S"))
        
        max_points = 50
        if len(self.flow_history) > max_points:
            self.flow_history = self.flow_history[-max_points:]
            self.pressure_history = self.pressure_history[-max_points:]
            self.time_history = self.time_history[-max_points:]
        
        try:
            x = list(range(len(self.flow_history)))
            if dpg.does_item_exist("flow_plot"):
                dpg.set_value("flow_plot", [x, self.flow_history])
        except Exception as e:
            logger.error(f"Ошибка обновления графика: {e}")

    def export_data(self, sender=None, app_data=None):
        """Экспорт данных в JSON"""
        try:
            data = {
                "timestamp": datetime.now().isoformat(),
                "sensor_data": {
                    "Q": self.current_sensor_data.Q,
                    "P_in": self.current_sensor_data.P_in,
                    "P_out": self.current_sensor_data.P_out,
                    "T": self.current_sensor_data.T
                },
                "control_command": {
                    "valveOpenPercent": self.current_command.valveOpenPercent if self.current_command else 0,
                    "status": self.current_command.status if self.current_command else "UNKNOWN",
                    "lastUsedRule": self.current_command.lastUsedRule if self.current_command else "",
                    "reactionTime": self.current_command.reactionTime if self.current_command else 0
                }
            }
            
            filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Данные экспортированы в {filename}")
            self.update_status_ui("OK", f"✅ Экспорт: {filename}")
                
        except Exception as e:
            logger.error(f"Ошибка экспорта: {e}")

    def test_alarm(self, sender=None, app_data=None):
        """Тестовое отображение модального окна тревоги"""
        if dpg.does_item_exist("surge_alert"):
            dpg.configure_item("surge_alert", show=True)

    def get_event_log(self, compressor_id: int = 1, start_date=None, end_date=None, limit: int = 100):
        """Получает журнал событий из БД"""
        try:
            return self.db.get_event_log(
                compressor_id=compressor_id,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Ошибка получения журнала: {e}")
            return []

    def get_callbacks(self):
        """Возвращает словарь коллбэков для привязки к кнопкам UI"""
        return {
            'process_data': self.process_data,
            'export_data': self.export_data,
            'test_alarm': self.test_alarm,
        }

    def set_surge_plot(self, plot):
        """Устанавливает ссылку на график ГДХ"""
        self.surge_plot = plot


    # ==========================================
    # Управление пользователями
    # ==========================================
    def get_all_users(self):
        """Получает список всех пользователей"""
        try:
            return self.db.get_all_users()
        except Exception as e:
            logger.error(f"Ошибка получения пользователей: {e}")
            return []

    def create_user(self, username: str, password: str, role: str) -> bool:
        """Создаёт нового пользователя"""
        try:
            return self.db.create_user(username, password, role)
        except Exception as e:
            logger.error(f"Ошибка создания пользователя: {e}")
            return False

    def update_user(self, user_id: int, username=None, role=None, is_active=None) -> bool:
        """Обновляет данные пользователя"""
        try:
            return self.db.update_user(user_id, username, role, is_active)
        except Exception as e:
            logger.error(f"Ошибка обновления пользователя: {e}")
            return False

    def delete_user(self, user_id: int) -> bool:
        """Удаляет пользователя"""
        try:
            return self.db.delete_user(user_id)
        except Exception as e:
            logger.error(f"Ошибка удаления пользователя: {e}")
            return False

    def reset_password(self, user_id: int, new_password: str) -> bool:
        """Сбрасывает пароль пользователя"""
        try:
            return self.db.reset_password(user_id, new_password)
        except Exception as e:
            logger.error(f"Ошибка сброса пароля: {e}")
            return False

    def shutdown(self):
        """Корректное завершение работы приложения"""
        logger.info("🛑 Завершение работы AppController...")
        logger.info("✅ AppController завершил работу")

    # ==========================================
    # Эмуляция данных (автогенератор через потоки)
    # ==========================================
    def start_simulation(self, interval_ms: int = 100):
        """Запускает автоматическую генерацию данных в отдельном потоке"""
        try:
            import threading
            import time
            
            if hasattr(self, '_simulation_running') and self._simulation_running:
                logger.info("ℹ️ Симуляция уже запущена")
                return
            
            # Инициализируем состояние
            self._sim_q = 60.0
            self._sim_h = 1500.0
            self._sim_mode = "normal"
            self._tick_interval = interval_ms / 1000.0
            self._simulation_running = True
            self._tick_count = 0
            
            # ✅ Создаём отдельный поток для симуляции
            self._sim_thread = threading.Thread(target=self._simulation_loop, daemon=True)
            self._sim_thread.start()
            
            logger.info(f"✅ Симуляция запущена в потоке (интервал: {interval_ms} мс)")
            logger.info(f"   surge_plot: {hasattr(self, 'surge_plot') and self.surge_plot is not None}")
            logger.info(f"   telemetry_panel: {self.telemetry_panel is not None}")
        except Exception as e:
            logger.error(f"Ошибка запуска симуляции: {e}", exc_info=True)
    
    def _simulation_loop(self):
        """Основной цикл симуляции в отдельном потоке"""
        import time
        logger.info("🔄 Поток симуляции запущен")
        
        while self._simulation_running:
            try:
                self._simulation_tick()
                time.sleep(self._tick_interval)
            except Exception as e:
                logger.error(f"Ошибка в цикле симуляции: {e}", exc_info=True)
                time.sleep(0.1)  # Пауза при ошибке
        
        logger.info("🛑 Поток симуляции остановлен")
    
    def stop_simulation(self):
        """Останавливает симуляцию"""
        try:
            self._simulation_running = False
            if hasattr(self, '_sim_thread') and self._sim_thread.is_alive():
                self._sim_thread.join(timeout=1.0)
            logger.info("🛑 Симуляция остановлена")
        except Exception as e:
            logger.error(f"Ошибка остановки симуляции: {e}", exc_info=True)
    
    def set_simulation_mode(self, mode: str):
        """Устанавливает режим симуляции: normal, warning, surge"""
        if mode in ("normal", "warning", "surge"):
            self._sim_mode = mode
            logger.info(f"🔄 Режим симуляции: {mode}")
    
    def _simulation_tick(self):
        """Один тик симуляции — генерирует новые данные и обновляет UI"""
        try:
            import random
            
            # ✅ ЛОГИРОВАНИЕ: каждые 50 тиков
            if self._tick_count % 50 == 0:
                logger.info(f"🔄 Тик #{self._tick_count}: mode={self._sim_mode}, q={self._sim_q:.1f}, h={self._sim_h:.1f}")
            
            # Эмуляция плавного изменения рабочей точки
            if self._sim_mode == "normal":
                self._sim_q += random.uniform(-0.5, 0.5)
                self._sim_h += random.uniform(-5, 5)
                self._sim_q = max(50, min(80, self._sim_q))
                self._sim_h = max(1300, min(1800, self._sim_h))
            elif self._sim_mode == "warning":
                self._sim_q += random.uniform(-1, 0.3)
                self._sim_h += random.uniform(-5, 10)
                self._sim_q = max(30, min(60, self._sim_q))
                self._sim_h = max(1000, min(1900, self._sim_h))
            elif self._sim_mode == "surge":
                self._sim_q += random.uniform(-3, 3)
                self._sim_h += random.uniform(-30, 30)
                self._sim_q = max(20, min(50, self._sim_q))
                self._sim_h = max(800, min(2000, self._sim_h))
            
            # Обновляем рабочую точку на графике
            if hasattr(self, 'surge_plot') and self.surge_plot is not None:
                self.surge_plot.update_operating_point(self._sim_q, self._sim_h)
            
            # Обновляем телеметрию
            if self.telemetry_panel is not None:
                from dto.dto import SensorData, ProcessedData, ControlSignal
                
                sensor = SensorData(
                    Q=self._sim_q,
                    P_in=5.0 + random.uniform(-0.1, 0.1),
                    P_out=8.0 + random.uniform(-0.1, 0.1),
                    T=25.0 + random.uniform(-0.5, 0.5)
                )
                
                if self._sim_mode == "surge":
                    margin = random.uniform(0, 5)
                    status = "SURGE"
                    valve = random.uniform(70, 100)
                elif self._sim_mode == "warning":
                    margin = random.uniform(5, 15)
                    status = "WARNING"
                    valve = random.uniform(30, 70)
                else:
                    margin = random.uniform(20, 50)
                    status = "NORMAL"
                    valve = random.uniform(0, 30)
                
                processed = ProcessedData(
                    Q_rel=self._sim_q,
                    H_rel=self._sim_h,
                    margin=margin,
                    dQdt=random.uniform(-5, 5)
                )
                
                # ✅ ДОБАВЛЕНО compressorName
                command = ControlSignal(
                    valveOpenPercent=valve,
                    status=status,
                    lastUsedRule="SIMULATION",
                    reactionTime=0.05,
                    compressorName="CC-45X"  # ✅ Имя компрессора
                )
                
                self.telemetry_panel.update(sensor, processed, command)
                
                if status == "SURGE":
                    surge_status = "АПЗ: АКТИВНА (помпаж)"
                    last_rule = "Правило #3: Экстренное открытие клапана"
                    gas_comp = "Природный газ (CH₄ 92%)"
                elif status == "WARNING":
                    surge_status = "АПЗ: Предупреждение"
                    last_rule = "Правило #2: Плавное увеличение расхода"
                    gas_comp = "Природный газ (CH₄ 92%)"
                else:
                    surge_status = "АПЗ: Норма"
                    last_rule = "Правило #1: Поддержание режима"
                    gas_comp = "Природный газ (CH₄ 92%)"
                
                command = ControlSignal(
                    valveOpenPercent=valve,
                    status=status,
                    lastUsedRule=last_rule,
                    reactionTime=0.05,
                    compressorName="CC-45X",
                    gasComposition=gas_comp,
                    surgeStatus=surge_status,
                    marginPercent=margin
                )
            
            self._tick_count += 1
        
        except Exception as e:
            logger.error(f"Ошибка тика симуляции: {e}", exc_info=True)