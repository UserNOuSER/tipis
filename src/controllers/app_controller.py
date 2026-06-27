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
            logger.error(f" Ошибка загрузки конфигурации: {e}")

    def initialize_system(self):
        """Инициализация системы"""
        try:
            self.bridge.init_py()
            status = "ГОТОВ К РАБОТЕ"
            if dpg.does_item_exist("status_text"):
                dpg.configure_item("status_text", default_value=f"Статус: {status}")
                dpg.configure_item("status_text", color=(16, 185, 129, 255))
        except Exception as e:
            logger.error(f"Ошибка инициализации: {e}")
            if dpg.does_item_exist("status_text"):
                dpg.configure_item("status_text", default_value=f"Ошибка: {str(e)}")
                dpg.configure_item("status_text", color=(239, 68, 68, 255))

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
                        dpg.configure_item("status_text", 
                            default_value="⚠️ АКТИВНА ЗАЩИТА (ПОМПАЖ)", 
                            color=(239, 68, 68, 255))
                    elif status == "WARNING":
                        dpg.configure_item("status_text", 
                            default_value="⚠️ ПРИБЛИЖЕНИЕ К ПОМПАЖУ", 
                            color=(245, 158, 11, 255))
                    else:
                        dpg.configure_item("status_text", 
                            default_value="✅ НОРМА", 
                            color=(16, 185, 129, 255))

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
            if dpg.does_item_exist("status_text"):
                dpg.configure_item("status_text", default_value=f"✅ Экспорт: {filename}")
                
        except Exception as e:
            logger.error(f"Ошибка экспорта: {e}")

    def test_alarm(self, sender=None, app_data=None):
        """Тестовое отображение модального окна тревоги"""
        if dpg.does_item_exist("surge_alert"):
            dpg.configure_item("surge_alert", show=True)

    def get_event_log(self, 
                      compressor_id: int = 1,
                      start_date=None,
                      end_date=None,
                      limit: int = 100):
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

    def update_user(self, user_id: int, username: str | None = None, role: str | None = None, is_active: bool | None = None) -> bool:
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
    