import json
from datetime import datetime
from dto.dto import SensorData
import dearpygui.dearpygui as dpg  # ty:ignore[unresolved-import]
import sys

class AppController:
    """Контроллер: связывает UI, Core и БД"""
    
    def __init__(self, core):
        self.core = core
        self.current_sensor_data = SensorData()
        self.current_command = None
        
        # История для графиков
        self.flow_history = []
        self.pressure_history = []
        self.time_history = []

    def initialize_system(self):
        """Инициализация системы"""
        try:
            status = self.core.get_system_status()
            dpg.configure_item("status_text", default_value=f"Статус: {status}")
        except Exception as e:
            dpg.configure_item("status_text", default_value=f"Ошибка: {str(e)}")

    def process_data(self, sender=None, app_data=None):
        """Обработка данных с датчиков"""
        try:
            # Собираем данные из UI
            self.current_sensor_data = SensorData(
                Q=dpg.get_value("flow_rate_input") if dpg.does_item_exist("flow_rate_input") else 69.0,
                P_in=dpg.get_value("pressure_in_input") if dpg.does_item_exist("pressure_in_input") else 5.0,
                P_out=dpg.get_value("pressure_out_input") if dpg.does_item_exist("pressure_out_input") else 8.0,
                T=dpg.get_value("temperature_input") if dpg.does_item_exist("temperature_input") else 20.0
            )
            
            # Прогоняем через ядро
            self.current_command = self.core.process_sensor_data(self.current_sensor_data)
            
            # Обновляем UI
            if self.current_command:
                dpg.configure_item("valve_position_text", 
                    default_value=f"{self.current_command.valveOpenPercent:.2f}%")
                
                status_text = "НОРМА"
                if self.current_command.status == "WARNING":
                    status_text = "ПРИБЛИЖЕНИЕ К ПОМПАЖУ"
                elif self.current_command.status == "SURGE":
                    status_text = "АКТИВНА"
                
                dpg.configure_item("alarm_status_text", default_value=status_text)
                
                if self.core.is_surge_detected():
                    dpg.configure_item("surge_alert", show=True)
            
            self.update_charts()
            
        except Exception as e:
            print(f"Ошибка обработки: {e}", file=sys.stderr)

    def update_charts(self):
        """Обновление графиков"""
        processed = self.core.get_last_processed()
        if not processed:
            return
        
        self.flow_history.append(processed.Q_rel)
        self.pressure_history.append(processed.H_rel)
        
        max_points = 50
        if len(self.flow_history) > max_points:
            self.flow_history = self.flow_history[-max_points:]
            self.pressure_history = self.pressure_history[-max_points:]
        
        try:
            x = list(range(len(self.flow_history)))
            dpg.set_value("flow_plot", [x, self.flow_history])
        except Exception as e:
            print(f"Ошибка обновления графика: {e}", file=sys.stderr)

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
                    "status": self.current_command.status if self.current_command else "UNKNOWN"
                }
            }
            
            filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"Данные экспортированы в {filename}", file=sys.stderr)
        except Exception as e:
            print(f"Ошибка экспорта: {e}", file=sys.stderr)

    def test_alarm(self, sender=None, app_data=None):
        """Тест тревоги"""
        dpg.configure_item("surge_alert", show=True)