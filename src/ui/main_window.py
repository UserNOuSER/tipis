import dearpygui.dearpygui as dpg  # ty:ignore[unresolved-import]
from ui.control_panel import ControlPanel
from ui.telemetry_panel import TelemetryPanel
from ui.surge_plot import SurgePlot
from ui.modals import Modals
from ui.event_log import EventLogWindow
from ui.user_management import UserManagementWindow
from ui.configurator import ConfiguratorWindow
from controllers.configurator_controller import ConfiguratorController
import sys

class MainWindow:
    def __init__(self, palette, controller, auth_controller):
        self.palette = palette
        self.controller = controller
        self.auth_controller = auth_controller
        
        self.control_panel = ControlPanel(palette)
        self.telemetry_panel = TelemetryPanel(palette)
        self.surge_plot = SurgePlot(palette)
        self.event_log_window = EventLogWindow(palette, controller)
        self.user_management_window = UserManagementWindow(palette, controller)
        
        self.configurator_controller = ConfiguratorController()
        self.configurator_window = ConfiguratorWindow(palette, self.configurator_controller)
        
        self.controller.set_telemetry_panel(self.telemetry_panel)
        
        self.plot_ratio = 0.70
        self.telemetry_ratio = 0.30
        self.window_padding_x = 100
        self.window_padding_y = 150
        self.control_panel_height = 100

    def create(self):
        # --- Меню ---
        with dpg.viewport_menu_bar():
            username = self.auth_controller.get_username()
            role = self.auth_controller.get_role()
            dpg.add_text(f"{role}: {username}", 
                        color=self.palette.text_primary + (255,))
            
            dpg.add_menu_item(label="Журнал событий", callback=self.show_event_log)
            dpg.add_menu_item(label="Управление пользователями", 
                             callback=self.show_user_management)
            
            if self.auth_controller.can_access_configurator():
                dpg.add_menu_item(label="Конфигуратор", callback=self.show_configurator)
            
            dpg.add_menu_item(label="Экспорт отчета", callback=lambda: print("Export"))
            with dpg.menu(label="Настройки"):
                dpg.add_menu_item(label="Поменять цвет темы", callback=self.toggle_theme)
            dpg.add_menu_item(label="Справка", callback=self.show_help)
            dpg.add_menu_item(label="Выйти", callback=self._logout)

        # --- Главное окно ---
        with dpg.window(label="Система защиты от помпажа", tag="main_window", width=1200, height=800):
            dpg.add_text("СИСТЕМА ЗАЩИТЫ КОМПРЕССОРА ОТ ПОМПАЖА", color=self.palette.primary + (255,))
            dpg.add_separator()
            
            dpg.add_text("Статус: Ожидание данных...", tag="status_text", color=self.palette.warning + (255,))
            dpg.add_spacer(height=10)
            
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
        
        # Окна журналов
        self.event_log_window.create()
        self.user_management_window.create()
        self.configurator_window.create()
        
        # ❌ УДАЛЕНО: Создание viewport (оно уже создано в main.py)
        # dpg.create_viewport(...)  ← УДАЛИТЬ
        # dpg.setup_dearpygui()     ← УДАЛИТЬ
        # dpg.show_viewport()       ← УДАЛИТЬ
        
        # ✅ ОСТАВИТЬ ТОЛЬКО:
        dpg.set_viewport_resize_callback(self._on_viewport_resize)
        dpg.set_primary_window("main_window", True)
        
        self._on_viewport_resize(None)

    def show_event_log(self, sender=None, app_data=None):
        self.event_log_window.show()

    def show_user_management(self, sender=None, app_data=None):
        self.user_management_window.show()

    def show_configurator(self, sender=None, app_data=None):
        if self.auth_controller.can_access_configurator():
            self.configurator_window.show()

    def _logout(self, sender=None, app_data=None):
        self.auth_controller.logout()
        print("👋 Выход из системы", file=sys.stderr)
        dpg.stop_dearpygui()

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
        print("Theme toggle not implemented yet", file=sys.stderr)

    def show_help(self):
        dpg.configure_item("help_window", show=True)