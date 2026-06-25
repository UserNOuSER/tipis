import dearpygui.dearpygui as dpg  # ty:ignore[unresolved-import]
from ui.surge_plot import SurgePlot
from ui.control_panel import ControlPanel
from ui.modals import Modals
import sys

class MainWindow:
    def __init__(self, palette, controller):
        self.palette = palette
        self.controller = controller

    def create(self):
        # Меню
        with dpg.viewport_menu_bar():
            dpg.add_menu_item(label="Журнал событий", callback=lambda: print("Journal"))
            dpg.add_menu_item(label="Экспорт отчета", callback=lambda: print("Export"))
            with dpg.menu(label="Настройки"):
                dpg.add_menu_item(label="Поменять цвет темы", callback=self.toggle_theme)
            dpg.add_menu_item(label="Справка", callback=self.show_help)

        # Главное окно
        with dpg.window(label="Система защиты от помпажа", tag="main_window", width=1200, height=800):
            dpg.add_text("СИСТЕМА ЗАЩИТЫ КОМПРЕССОРА ОТ ПОМПАЖА", 
                        color=self.palette.primary + (255,))
            dpg.add_separator()
            
            dpg.add_text("Статус: Не инициализировано", tag="status_text", 
                        color=self.palette.warning + (255,))
            dpg.add_spacer(height=10)
            
            with dpg.group(horizontal=True):
                # График
                with dpg.child_window(width=800, height=400, label="Графики"):
                    dpg.add_text("Мониторинг в реальном времени", 
                                color=self.palette.primary + (255,))
                    dpg.add_separator()
                    
                    with dpg.plot(label="", height=-1, width=-1):
                        dpg.add_plot_axis(dpg.mvXAxis, label="Q, кг/с", tag="x_axis_flow")
                        dpg.add_plot_axis(dpg.mvYAxis, label="H, кПа", tag="y_axis_flow")
                        dpg.add_line_series([], [], label="", parent="y_axis_flow", tag="flow_plot")
                
                # Правая панель
                with dpg.child_window(width=380, height=400, label="Панель"):
                    self._create_control_section()
        
        # Модальные окна
        Modals(self.palette).create()
        
        # Viewport
        dpg.create_viewport(title='Система защиты от помпажа v1.0', width=1220, height=850)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("main_window", True)

    def _create_control_section(self):
        """Создает секцию управления"""
        dpg.add_text("Управление", color=self.palette.primary + (255,))
        dpg.add_separator()
        
        dpg.add_text("Позиция байпасного клапана:")
        dpg.add_text("0.00%", tag="valve_position_text", 
                    color=self.palette.success + (255,))
        
        dpg.add_spacer(height=10)
        dpg.add_text("Статус тревоги:")
        dpg.add_text("НОРМА", tag="alarm_status_text", 
                    color=self.palette.success + (255,))
        
        dpg.add_spacer(height=20)
        dpg.add_button(label="🚨 Тест тревоги", 
                      callback=self.controller.test_alarm, width=-1)
        dpg.add_button(label="📊 Экспорт данных", 
                      callback=self.controller.export_data, width=-1)
        dpg.add_button(label="🔄 Обновить данные", 
                      callback=self.controller.process_data, width=-1)

    def toggle_theme(self, sender, app_data=None):
        """Переключение темы"""
        print("Theme toggle not implemented yet", file=sys.stderr)

    def show_help(self):
        """Показать справку"""
        dpg.configure_item("help_window", show=True)