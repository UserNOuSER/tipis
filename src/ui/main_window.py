# ui/main_window.py
import dearpygui.dearpygui as dpg  # ty:ignore[unresolved-import]
from ui.control_panel import ControlPanel
from ui.telemetry_panel import TelemetryPanel
from ui.surge_plot import SurgePlot
from ui.modals import Modals
from ui.event_log import EventLogWindow
from ui.user_management import UserManagementWindow
from ui.configurator import ConfiguratorWindow
from ui.export_window import ExportWindow  # ✅ НОВОЕ
from controllers.configurator_controller import ConfiguratorController
import sys


class MainWindow:
    def __init__(self, palette, controller, auth_controller, theme_manager): 
        self.palette = palette
        self.controller = controller
        self.auth_controller = auth_controller
        self.theme_manager = theme_manager  
        
        self.control_panel = ControlPanel(palette)
        self.telemetry_panel = TelemetryPanel(palette)
        self.surge_plot = SurgePlot(palette)
        self.event_log_window = EventLogWindow(palette, controller)
        self.user_management_window = UserManagementWindow(palette, controller)
        self.export_window = ExportWindow(palette, controller)  
        
        self.configurator_controller = ConfiguratorController()
        self.configurator_window = ConfiguratorWindow(
            palette, 
            self.configurator_controller,
            app_controller=self.controller,
            event_log_window=self.event_log_window  # ✅ Передаём для синхронизации
        )
        
        self.controller.set_telemetry_panel(self.telemetry_panel)
        
        # ✅ Устанавливаем текущего пользователя в симулятор
        current_user = auth_controller.get_current_user()
        if current_user:
            controller.set_current_user(current_user["user_id"])
        
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
            
            # ✅ ЗАМЕНЕНО: вместо print теперь открываем окно экспорта
            dpg.add_menu_item(label="Экспорт отчёта", callback=self.show_export_window)
            
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
                
                # Кнопки управления симуляцией
                dpg.add_spacer(height=5)
                with dpg.group(horizontal=True):
                    dpg.add_text("Симуляция:", color=self.palette.text_primary + (255,))
                    dpg.add_button(label="▶ Старт", callback=self._start_sim, width=80)
                    dpg.add_button(label="⏸ Стоп", callback=self._stop_sim, width=80)
                    dpg.add_spacer(width=20)
                    dpg.add_button(label="Норма", callback=lambda: self.controller.set_simulation_mode("normal"), width=80)
                    dpg.add_button(label="Предупреждение", callback=lambda: self.controller.set_simulation_mode("warning"), width=120)
                    dpg.add_button(label="Помпаж", callback=lambda: self.controller.set_simulation_mode("surge"), width=80)
        
        # Модальные окна
        Modals(self.palette).create()
        
        # Окна журналов
        self.event_log_window.create()
        self.user_management_window.create()
        self.configurator_window.create()
        self.export_window.create()  # ✅ НОВОЕ
        
        # ✅ Устанавливаем текущий компрессор в журнал событий
        self.event_log_window.set_compressor(1)  # По умолчанию CC-45X
        
        dpg.set_viewport_resize_callback(self._on_viewport_resize)
        dpg.set_primary_window("main_window", True)
        
        self._on_viewport_resize(None)
        self.controller.set_surge_plot(self.surge_plot)

    def show_event_log(self, sender=None, app_data=None):
        self.event_log_window.show()

    def show_user_management(self, sender=None, app_data=None):
        self.user_management_window.show()

    def show_configurator(self, sender=None, app_data=None):
        if self.auth_controller.can_access_configurator():
            self.configurator_window.show()

    def show_export_window(self, sender=None, app_data=None):  # ✅ НОВОЕ
        """Показывает окно экспорта отчёта"""
        self.export_window.show()

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
        """Переключает тему между светлой и тёмной"""
        # ✅ ИСПРАВЛЕНО: используем self.theme_manager, а не self.controller
        if self.theme_manager:
            new_theme = self.theme_manager.toggle_theme()
            print(f"🎨 Тема переключена на: {new_theme}", file=sys.stderr)
            
            # Обновляем палитру
            palette = self.theme_manager.get_palette()
            self.palette = palette
            
            # Обновляем все компоненты
            self.surge_plot.palette = palette
            self.telemetry_panel.palette = palette
            self.control_panel.palette = palette
            self.event_log_window.palette = palette
            self.user_management_window.palette = palette
            self.configurator_window.palette = palette
            self.export_window.palette = palette  # ✅ НОВОЕ
            
            # Вызываем update_theme_colors для компонентов
            if hasattr(self.telemetry_panel, 'update_theme_colors'):
                self.telemetry_panel.update_theme_colors(palette)
        else:
            print("⚠️ ThemeManager не установлен", file=sys.stderr)

    def show_help(self):
        dpg.configure_item("help_window", show=True)

    def _start_sim(self, sender=None, app_data=None):
        """Запускает симуляцию"""
        self.controller.start_simulation(interval_ms=100)

    def _stop_sim(self, sender=None, app_data=None):
        """Останавливает симуляцию"""
        self.controller.stop_simulation()