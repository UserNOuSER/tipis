import dearpygui.dearpygui as dpg
import fuzzy_core
import json
from datetime import datetime
import time

class DispatcherGUI:
    def __init__(self):
        # Инициализация ядра
        self.core = fuzzy_core.AntiSurgeCore()
        self.data_processor = fuzzy_core.DataProcessor()
        self.fuzzy_engine = fuzzy_core.FuzzyEngine()
        
        # Текущие данные
        self.current_sensor_data = fuzzy_core.SensorData()
        self.current_command = None
        
        # История данных для графиков
        self.flow_history = []
        self.pressure_history = []
        self.valve_position_history = []
        self.time_history = []
        
    def initialize_system(self, config_path="system_config.ini"):
        """Инициализация системы"""
        try:
            self.core.initialize(config_path)
            dpg.configure_item("status_text", default_value=f"Статус: {self.core.get_system_status()}")
            dpg.configure_item("status_text", color=(0, 255, 0, 255))
        except Exception as e:
            dpg.configure_item("status_text", default_value=f"Ошибка инициализации: {str(e)}")
            dpg.configure_item("status_text", color=(255, 0, 0, 255))
    
    def update_sensor_data(self):
        """Обновление данных с датчиков (симуляция)"""
        # В реальном приложении здесь будет чтение из PLC/контроллера
        self.current_sensor_data.flow_rate = dpg.get_value("flow_rate_input")
        self.current_sensor_data.pressure_in = dpg.get_value("pressure_in_input")
        self.current_sensor_data.pressure_out = dpg.get_value("pressure_out_input")
        self.current_sensor_data.temperature = dpg.get_value("temperature_input")
        
        return self.current_sensor_data
    
    def process_data(self):
        """Обработка данных и получение управляющей команды"""
        try:
            # Фильтрация шумов
            filtered_data = self.data_processor.filter_noise([self.current_sensor_data.flow_rate])
            
            # Обработка в ядре
            self.current_command = self.core.process_sensor_data(self.current_sensor_data)
            
            # Обновление UI
            dpg.configure_item("valve_position_text", default_value=f"{self.current_command.bypass_valve_position:.2f}%")
            dpg.configure_item("alarm_status_text", default_value="АКТИВНА" if self.current_command.alarm_status else "НОРМА")
            dpg.configure_item("alarm_status_text", color=(255, 0, 0, 255) if self.current_command.alarm_status else (0, 255, 0, 255))
            
            # Обновление графиков
            self.update_charts()
            
            # Проверка на помпаж
            if self.core.is_surge_detected():
                dpg.configure_item("surge_alert", show=True)
                
        except Exception as e:
            dpg.configure_item("status_text", default_value=f"Ошибка обработки: {str(e)}")
            dpg.configure_item("status_text", color=(255, 165, 0, 255))
    
    def update_charts(self):
        """Обновление графиков"""
        current_time = datetime.now().strftime("%H:%M:%S")
        
        self.time_history.append(current_time)
        self.flow_history.append(self.current_sensor_data.flow_rate)
        self.pressure_history.append(self.current_sensor_data.pressure_in)
        self.valve_position_history.append(self.current_command.bypass_valve_position if self.current_command else 0)
        
        # Ограничиваем историю последними 50 точками
        max_points = 50
        if len(self.time_history) > max_points:
            self.time_history = self.time_history[-max_points:]
            self.flow_history = self.flow_history[-max_points:]
            self.pressure_history = self.pressure_history[-max_points:]
            self.valve_position_history = self.valve_position_history[-max_points:]
        
        # Обновление графиков
        dpg.set_value("flow_plot", [self.flow_history])
        dpg.set_value("pressure_plot", [self.pressure_history])
        dpg.set_value("valve_plot", [self.valve_position_history])
    
    def create_gui(self):
        """Создание интерфейса"""
        dpg.create_context()
        
        with dpg.font_registry():
            with dpg.font("C:\\Windows\\Fonts\\Arial.ttf", 16) as default_font:
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)
        
        dpg.bind_font(default_font)
        
        # Главное окно
        with dpg.window(label="Система защиты от помпажа", tag="main_window", width=1200, height=800):
            
            # Заголовок
            dpg.add_text("🔧 СИСТЕМА ЗАЩИТЫ КОМПРЕССОРА ОТ ПОМПАЖА", color=(0, 150, 255, 255))
            dpg.add_separator()
            
            # Статус системы
            dpg.add_text("Статус: Не инициализировано", tag="status_text", color=(255, 165, 0, 255))
            dpg.add_spacer(height=10)
            
            # Группа ввода данных
            with dpg.group(horizontal=True):
                with dpg.child_window(width=300, height=400, label="Параметры"):
                    dpg.add_text("📊 Параметры датчиков", color=(0, 150, 255, 255))
                    dpg.add_separator()
                    
                    dpg.add_input_float(label="Расход (м³/ч)", tag="flow_rate_input", default_value=0.0, step=1.0)
                    dpg.add_input_float(label="Давление на входе (бар)", tag="pressure_in_input", default_value=0.0, step=0.1)
                    dpg.add_input_float(label="Давление на выходе (бар)", tag="pressure_out_input", default_value=0.0, step=0.1)
                    dpg.add_input_float(label="Температура (°C)", tag="temperature_input", default_value=20.0, step=0.5)
                    
                    dpg.add_spacer(height=20)
                    dpg.add_button(label="🔄 Обновить данные", callback=lambda: self.process_data(), width=-1)
                    dpg.add_button(label="⚙️ Инициализировать систему", callback=lambda: self.initialize_system(), width=-1)
            
            # Группа графиков
            with dpg.child_window(width=600, height=400, label="Графики"):
                dpg.add_text("📈 Мониторинг в реальном времени", color=(0, 150, 255, 255))
                dpg.add_separator()
                
                with dpg.plot(label="Расход", height=120, width=-1):
                    dpg.add_plot_axis(dpg.mvXAxis, label="Время")
                    dpg.add_plot_axis(dpg.mvYAxis, label="м³/ч", tag="y_axis_flow")
                    dpg.add_line_series([], [], label="Расход", parent="y_axis_flow", tag="flow_plot")
                
                with dpg.plot(label="Давление", height=120, width=-1):
                    dpg.add_plot_axis(dpg.mvXAxis, label="Время")
                    dpg.add_plot_axis(dpg.mvYAxis, label="бар", tag="y_axis_pressure")
                    dpg.add_line_series([], [], label="Давление", parent="y_axis_pressure", tag="pressure_plot")
                
                with dpg.plot(label="Позиция клапана", height=120, width=-1):
                    dpg.add_plot_axis(dpg.mvXAxis, label="Время")
                    dpg.add_plot_axis(dpg.mvYAxis, label="%", tag="y_axis_valve", min_value=0, max_value=100)
                    dpg.add_line_series([], [], label="Позиция", parent="y_axis_valve", tag="valve_plot")
            
            # Группа управления
            with dpg.child_window(width=280, height=400, label="Управление"):
                dpg.add_text("🎛️ Управление", color=(0, 150, 255, 255))
                dpg.add_separator()
                
                dpg.add_text("Позиция байпасного клапана:", color=(255, 255, 255, 255))
                dpg.add_text("0.00%", tag="valve_position_text", color=(0, 255, 0, 255))
                
                dpg.add_spacer(height=10)
                dpg.add_text("Статус тревоги:", color=(255, 255, 255, 255))
                dpg.add_text("НОРМА", tag="alarm_status_text", color=(0, 255, 0, 255))
                
                dpg.add_spacer(height=20)
                dpg.add_button(label="🚨 Тест тревоги", callback=self.test_alarm, width=-1)
                dpg.add_button(label="📊 Экспорт данных", callback=self.export_data, width=-1)
                
                dpg.add_spacer(height=20)
                dpg.add_text(" Лог событий:", color=(255, 255, 255, 255))
                dpg.add_listbox([], tag="event_log", width=-1, height=10)
            
            # Предупреждение о помпаже (скрыто по умолчанию)
            with dpg.window(label="⚠️ ВНИМАНИЕ!", tag="surge_alert", show=False, modal=True, no_move=True):
                dpg.add_text("ОБНАРУЖЕН ПОМПАЖ!", color=(255, 0, 0, 255))
                dpg.add_text("Принимаются меры защиты...")
                dpg.add_button(label="Подтвердить", callback=lambda: dpg.configure_item("surge_alert", show=False))
        
        dpg.create_viewport(title='Система защиты от помпажа v1.0', width=1220, height=850)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("main_window", True)
    
    def test_alarm(self):
        """Тестирование системы тревоги"""
        dpg.configure_item("surge_alert", show=True)
    
    def export_data(self):
        """Экспорт данных в файл"""
        try:
            data = {
                "timestamp": datetime.now().isoformat(),
                "sensor_data": {
                    "flow_rate": self.current_sensor_data.flow_rate,
                    "pressure_in": self.current_sensor_data.pressure_in,
                    "pressure_out": self.current_sensor_data.pressure_out,
                    "temperature": self.current_sensor_data.temperature
                },
                "control_command": {
                    "valve_position": self.current_command.bypass_valve_position if self.current_command else 0,
                    "alarm": self.current_command.alarm_status if self.current_command else False
                }
            }
            
            with open(f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", "w") as f:
                json.dump(data, f, indent=2)
            
            dpg.configure_item("status_text", default_value="Данные экспортированы")
        except Exception as e:
            dpg.configure_item("status_text", default_value=f"Ошибка экспорта: {str(e)}")
    
    def run(self):
        """Запуск приложения"""
        self.create_gui()
        
        # Инициализация при старте
        self.initialize_system()
        
        while dpg.is_dearpygui_running():
            # Автообновление каждые 2 секунды
            if dpg.get_frame_count() % 120 == 0:  # Примерно 2 секунды при 60 FPS
                self.update_sensor_data()
                self.process_data()
            
            dpg.render_dearpygui_frame()
        
        dpg.destroy_context()

if __name__ == "__main__":
    app = DispatcherGUI()
    app.run()