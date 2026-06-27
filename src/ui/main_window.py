import dearpygui.dearpygui as dpg  # ty:ignore[unresolved-import]
from ui.control_panel import ControlPanel
from ui.telemetry_panel import TelemetryPanel
from ui.surge_plot import SurgePlot
from ui.modals import Modals
import sys

class MainWindow:
    def __init__(self, palette, controller, theme_manager):
        self.palette = palette
        self.controller = controller
        self.theme_manager = theme_manager
        self.control_panel = ControlPanel(palette)
        self.telemetry_panel = TelemetryPanel(palette)
        self.surge_plot = SurgePlot(palette)
        
        self.controller.set_telemetry_panel(self.telemetry_panel)
        self.theme_manager.set_telemetry_panel(self.telemetry_panel)
        
        self.plot_ratio = 0.70
        self.telemetry_ratio = 0.30
        self.window_padding_x = 100
        self.window_padding_y = 150
        self.control_panel_height = 100
        self.min_plot_width = 600
        self.min_telemetry_width = 320
        self.min_content_height = 300
        self.min_control_height = 80
        self.min_viewport_width = 1020
        self.min_viewport_height = 700

    def create(self):
        # --- Меню ---
        with dpg.viewport_menu_bar():
            dpg.add_menu_item(label="Журнал событий", callback=lambda: print("Journal"))
            dpg.add_menu_item(label="Экспорт отчета", callback=lambda: print("Export"))
            with dpg.menu(label="Настройки"):
                dpg.add_menu_item(label="Поменять цвет темы", callback=self.toggle_theme)
            dpg.add_menu_item(label="Справка", callback=self.show_help)

        # --- Главное окно ---
        with dpg.window(label="Система защиты от помпажа", tag="main_window", width=1200, height=800):
            dpg.add_spacer(height=10)
            
            # Основная сетка
            with dpg.group(horizontal=True, tag="main_content_group"):
                # График
                with dpg.child_window(tag="plot_container", width=840, height=400, label="График ГДХ"):
                    dpg.add_text("Мониторинг рабочей точки", color=self.palette.primary + (255,))
                    dpg.add_separator()
                    self.surge_plot.create(parent_tag="plot_container")
                
                # Телеметрия
                with dpg.child_window(tag="telemetry_container", width=360, height=400, label="Телеметрия"):
                    self.telemetry_panel.create(parent_tag="telemetry_container")

            # Панель управления
            with dpg.child_window(tag="control_container", width=-1, height=self.control_panel_height, label="Управление"):
                callbacks = self.controller.get_callbacks()
                self.control_panel.create(parent_tag="control_container", callbacks=callbacks)
        
        # Модальные окна
        Modals(self.palette).create()
        
        # === ЕДИНСТВЕННЫЙ БЛОК ИНИЦИАЛИЗАЦИИ VIEWPORT ===
        dpg.create_viewport(
            title='Система защиты от помпажа v1.0', 
            width=1220, 
            height=850,
            min_width=self.min_viewport_width,
            min_height=self.min_viewport_height
        )
        dpg.setup_dearpygui()
        dpg.show_viewport()
        
        # Проверка существования окна
        if dpg.does_item_exist("main_window"):
            dpg.set_primary_window("main_window", True)
        else:
            raise RuntimeError("❌ Окно 'main_window' не найдено! Проверь создание виджетов.")
        
        # Регистрируем коллбэк на изменение размера окна
        dpg.set_viewport_resize_callback(self._on_viewport_resize)
        
        # Первичный расчет размеров
        self._on_viewport_resize(None)

    def toggle_theme(self, sender, app_data=None):
        """Переключает тему через меню"""
        try:
            new_theme = self.theme_manager.toggle_theme()
            self.palette = self.theme_manager.get_palette()
            print(f"Тема переключена на: {'тёмная' if new_theme == 'dark' else 'светлая'}")
        except Exception as e:
            print(f"Ошибка переключения темы: {e}")

    def show_help(self):
        dpg.configure_item("help_window", show=True)

    def _on_viewport_resize(self, sender):
        try:
            viewport_width = dpg.get_viewport_width()
            viewport_height = dpg.get_viewport_height()
            
            available_width = viewport_width - self.window_padding_x
            available_height = viewport_height - self.window_padding_y
            
            plot_width = max(self.min_plot_width, int(available_width * self.plot_ratio))
            telemetry_width = max(self.min_telemetry_width, int(available_width * self.telemetry_ratio))
            content_height = max(self.min_content_height, available_height - self.control_panel_height)
            control_height = max(self.min_control_height, self.control_panel_height)
            
            if dpg.does_item_exist("plot_container"):
                dpg.configure_item("plot_container", width=plot_width, height=content_height)
            
            if dpg.does_item_exist("telemetry_container"):
                dpg.configure_item("telemetry_container", width=telemetry_width, height=content_height)
            
            if dpg.does_item_exist("control_container"):
                dpg.configure_item("control_container", width=available_width, height=control_height)
                
        except Exception as e:
            print(f"Ошибка при ресайзе: {e}", file=sys.stderr)