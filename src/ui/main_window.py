# ui/main_window.py
import dearpygui.dearpygui as dpg  # ty:ignore[unresolved-import]
from ui.control_panel import ControlPanel
from ui.telemetry_panel import TelemetryPanel
from ui.surge_plot import SurgePlot
from ui.modals import Modals
from ui.event_log import EventLogWindow
from ui.user_management import UserManagementWindow 
import sys

class MainWindow:
    def __init__(self, palette, controller, theme_manager):
        self.palette = palette
        self.controller = controller
        self.theme_manager = theme_manager
        self.control_panel = ControlPanel(palette)
        self.telemetry_panel = TelemetryPanel(palette)
        self.surge_plot = SurgePlot(palette)
        self.event_log_window = EventLogWindow(palette, controller)
        self.user_management_window = UserManagementWindow(palette, controller) 
        
        self.controller.set_telemetry_panel(self.telemetry_panel)
        self.theme_manager.set_telemetry_panel(self.telemetry_panel)
        
        self.plot_ratio = 0.70
        self.telemetry_ratio = 0.30
        self.window_padding_x = 100
        self.window_padding_y = 150
        self.control_panel_height = 100

    def create(self):
        # --- Меню ---
        with dpg.viewport_menu_bar():
            dpg.add_menu_item(label="Журнал событий", callback=self.show_event_log)
            dpg.add_menu_item(label="Управление пользователями", callback=self.show_user_management) 
            dpg.add_menu_item(label="Экспорт отчета", callback=lambda: print("Export"))
            with dpg.menu(label="Настройки"):
                dpg.add_menu_item(label="Поменять цвет темы", callback=self.toggle_theme)
            dpg.add_menu_item(label="Справка", callback=self.show_help)

        # --- Главное окно ---
        with dpg.window(label="Система защиты от помпажа", tag="main_window", width=1200, height=800):
            dpg.add_text("СИСТЕМА ЗАЩИТЫ КОМПРЕССОРА ОТ ПОМПАЖА", color=self.palette.primary + (255,))
            dpg.add_separator()
            
            dpg.add_text("Статус: Ожидание данных...", tag="status_text", color=self.palette.warning + (255,))
            dpg.add_spacer(height=10)
            
            # Основная сетка
            with dpg.group(horizontal=True, tag="main_content_group"):
                with dpg.child_window(tag="plot_container", width=840, height=400, label="График ГДХ"):
                    dpg.add_text("Мониторинг рабочей точки", color=self.palette.primary + (255,))
                    dpg.add_separator()
                    self.surge_plot.create(parent_tag="plot_container")
                
                with dpg.child_window(tag="telemetry_container", width=360, height=400, label="Телеметрия"):
                    self.telemetry_panel.create(parent_tag="telemetry_container")

            with dpg.child_window(tag="control_container", width=-1, height=self.control_panel_height, label="Управление"):
                callbacks = self.controller.get_callbacks()
                self.control_panel.create(parent_tag="control_container", callbacks=callbacks)
        
        # Модальные окна
        Modals(self.palette).create()
        
        # Окно журнала событий
        self.event_log_window.create()
        
        # Окно управления пользователями
        self.user_management_window.create()  
        
        # Регистрируем коллбэк на изменение размера окна
        dpg.set_viewport_resize_callback(self._on_viewport_resize)
        
        # Viewport
        dpg.create_viewport(title='Система защиты от помпажа v1.0', width=1220, height=850)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("main_window", True)
        
        # Первичный расчет размеров
        self._on_viewport_resize(None)

    def show_event_log(self, sender=None, app_data=None):
        """Показывает окно журнала событий"""
        self.event_log_window.show()

    def show_user_management(self, sender=None, app_data=None):
        """Показывает окно управления пользователями"""
        self.user_management_window.show()

    def _on_viewport_resize(self, sender):
        try:
            viewport_width = dpg.get_viewport_width()
            viewport_height = dpg.get_viewport_height()
            
            available_width = viewport_width - self.window_padding_x
            available_height = viewport_height - self.window_padding_y
            
            plot_width = int(available_width * self.plot_ratio)
            telemetry_width = int(available_width * self.telemetry_ratio)
            content_height = available_height - self.control_panel_height
            
            if dpg.does_item_exist("plot_container"):
                dpg.configure_item("plot_container", width=plot_width, height=content_height)
            
            if dpg.does_item_exist("telemetry_container"):
                dpg.configure_item("telemetry_container", width=telemetry_width, height=content_height)
            
            if dpg.does_item_exist("control_container"):
                dpg.configure_item("control_container", width=available_width, height=self.control_panel_height)
                
        except Exception as e:
            print(f"Ошибка при ресайзе: {e}", file=sys.stderr)

    def toggle_theme(self, sender, app_data=None):
        self.theme_manager.toggle_theme()

    def show_help(self):
        dpg.configure_item("help_window", show=True)