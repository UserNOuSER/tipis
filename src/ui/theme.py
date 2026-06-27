import dearpygui.dearpygui as dpg  # ty:ignore[unresolved-import]
import os
from typing import NamedTuple

_FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")
INTER_REGULAR = os.path.join(_FONTS_DIR, "Inter-Regular.ttf")
INTER_MEDIUM = os.path.join(_FONTS_DIR, "Inter-Medium.ttf")
INTER_BOLD = os.path.join(_FONTS_DIR, "Inter-Bold.ttf")
MONO_REGULAR = os.path.join(_FONTS_DIR, "JetBrainsMono-Regular.ttf")

class ThemePalette(NamedTuple):
    bg_base: tuple
    bg_surface: tuple
    border_col: tuple
    text_primary: tuple
    text_disabled: tuple
    primary: tuple
    success: tuple
    warning: tuple
    error: tuple
    plot_grid: tuple

class ThemeManager:
    """Менеджер тем для динамического переключения"""
    
    def __init__(self):
        self.current_dark_mode = False
        self.themes = {}
        self.palettes = {}
        self.fonts = {}
        self._initialized = False
        self.telemetry_panel = None  # Ссылка на панель телеметрии
        
    def initialize(self):
        """Инициализирует обе темы при старте приложения"""
        if self._initialized:
            return
            
        self.themes['dark'], self.palettes['dark'], self.fonts['dark'] = self._create_theme(dark_mode=True)
        self.themes['light'], self.palettes['light'], self.fonts['light'] = self._create_theme(dark_mode=False)
        
        self.apply_theme('light')
        self._initialized = True
    
    def set_telemetry_panel(self, panel):
        """Устанавливает ссылку на панель телеметрии для обновления цветов"""
        self.telemetry_panel = panel
    
    def _create_theme(self, dark_mode=False):
        """Создаёт тему и возвращает (theme, palette, fonts)"""
        if dark_mode:
            bg_base = (15, 17, 21)
            bg_surface = (30, 33, 40)
            border_col = (51, 65, 85)
            text_primary = (226, 232, 240)
            text_disabled = (148, 163, 184)
            primary = (14, 165, 233)
            success = (16, 185, 129)
            warning = (245, 158, 11)
            error = (239, 68, 68)
            plot_grid = (30, 41, 59)
        else:
            bg_base = (248, 250, 252)
            bg_surface = (255, 255, 255)
            border_col = (226, 232, 240)
            text_primary = (30, 41, 59)
            text_disabled = (100, 116, 139)
            primary = (2, 132, 199)
            success = (5, 150, 105)
            warning = (217, 119, 6)
            error = (220, 38, 38)
            plot_grid = (241, 245, 249)

        palette = ThemePalette(
            bg_base=bg_base, bg_surface=bg_surface, border_col=border_col,
            text_primary=text_primary, text_disabled=text_disabled,
            primary=primary, success=success, warning=warning,
            error=error, plot_grid=plot_grid,
        )

        with dpg.theme() as theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, bg_base)
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, bg_surface)
                dpg.add_theme_color(dpg.mvThemeCol_PopupBg, bg_surface)
                dpg.add_theme_color(dpg.mvThemeCol_Border, border_col)
                dpg.add_theme_color(dpg.mvThemeCol_Text, text_primary)
                dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, text_disabled)
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, plot_grid)
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, border_col)
                dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, border_col)
                dpg.add_theme_color(dpg.mvThemeCol_Button, primary)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, primary)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, primary)
                dpg.add_theme_color(dpg.mvThemeCol_Header, primary)
                dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, primary)
                dpg.add_theme_color(dpg.mvThemeCol_PlotLines, primary)
                dpg.add_theme_color(dpg.mvThemeCol_PlotLinesHovered, primary)
                dpg.add_theme_color(dpg.mvPlotCol_PlotBg, plot_grid)
                dpg.add_theme_color(dpg.mvThemeCol_TableHeaderBg, plot_grid)
                dpg.add_theme_color(dpg.mvThemeCol_TableBorderStrong, border_col)
                dpg.add_theme_color(dpg.mvThemeCol_TableBorderLight, border_col)
                dpg.add_theme_color(dpg.mvThemeCol_TableRowBg, bg_surface)
                dpg.add_theme_color(dpg.mvThemeCol_TableRowBgAlt, bg_base)
                dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg, bg_surface)

        with dpg.font_registry():
            try:
                body_font = dpg.add_font(INTER_REGULAR, 16)
                h2_font = dpg.add_font(INTER_MEDIUM, 20)
                h1_font = dpg.add_font(INTER_BOLD, 24)
                mono_font = dpg.add_font(MONO_REGULAR, 16)
            except Exception:
                body_font = dpg.add_font("C:\\Windows\\Fonts\\Arial.ttf", 16)
                h2_font = body_font
                h1_font = body_font
                mono_font = body_font

        fonts = {
            'body': body_font,
            'h1': h1_font,
            'h2': h2_font,
            'mono': mono_font
        }

        return theme, palette, fonts
    
    def apply_theme(self, theme_name='light'):
        """Применяет тему по имени"""
        if theme_name not in self.themes:
            raise ValueError(f"Тема '{theme_name}' не найдена")
        
        self.current_dark_mode = (theme_name == 'dark')
        dpg.bind_theme(self.themes[theme_name])
        dpg.bind_font(self.fonts[theme_name]['body'])
        
        # Обновляем цвета для специфичных элементов
        self._update_special_elements(self.palettes[theme_name])
    
    def toggle_theme(self):
        """Переключает между светлой и тёмной темой"""
        new_theme = 'dark' if not self.current_dark_mode else 'light'
        self.apply_theme(new_theme)
        return new_theme

    def get_palette(self):
        """Возвращает текущую палитру"""
        mode = 'dark' if self.current_dark_mode else 'light'
        return self.palettes[mode]
    
    def _update_special_elements(self, palette):
        """Обновляет цвета для элементов с жёстко заданными цветами"""
        try:
            # Обновляем панель телеметрии
            if self.telemetry_panel:
                self.telemetry_panel.update_theme_colors(palette)
            
            # Статусные тексты
            if dpg.does_item_exist("status_text"):
                dpg.configure_item("status_text", color=palette.warning + (255,))
            if dpg.does_item_exist("surge_alert_text"):
                dpg.configure_item("surge_alert_text", color=palette.error + (255,))
            
            # Заголовки
            if dpg.does_item_exist("header_text_main"):
                dpg.configure_item("header_text_main", color=palette.primary + (255,))
            if dpg.does_item_exist("monitoring_header"):
                dpg.configure_item("monitoring_header", color=palette.primary + (255,))
        except Exception as e:
            print(f"Ошибка обновления специальных элементов: {e}")

theme_manager = ThemeManager()