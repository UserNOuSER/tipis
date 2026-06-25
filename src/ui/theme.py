import dearpygui.dearpygui as dpg  # ty:ignore[unresolved-import]
import os
from typing import NamedTuple

_FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")
INTER_REGULAR = os.path.join(_FONTS_DIR, "Inter-Regular.ttf")
INTER_MEDIUM  = os.path.join(_FONTS_DIR, "Inter-Medium.ttf")
INTER_BOLD    = os.path.join(_FONTS_DIR, "Inter-Bold.ttf")
MONO_REGULAR  = os.path.join(_FONTS_DIR, "JetBrainsMono-Regular.ttf")


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

def setup_design_system(dark_mode=False):
    """Инициализация глобальной темы и шрифтов"""
    
    # Твоя палитра цветов
    if dark_mode:
        bg_base = (15, 17, 21)       # Background #0F1115
        bg_surface = (30, 33, 40)    # Surface #1E2128
        border_col = (51, 65, 85)    # Border #334155
        text_primary = (226, 232, 240) # Text Primary #E2E8F0
        text_disabled = (148, 163, 184) # Text Secondary #94A3B8
        primary = (14, 165, 233)     # Primary Action #0EA5E9
        success = (16, 185, 129)     # Success/OK #10B981
        warning = (245, 158, 11)     # Warning #F59E0B
        error = (239, 68, 68)        # Danger/Surge #EF4444
        plot_grid = (30, 41, 59)     # Plot Grid #1E293B
    else:
        bg_base = (248, 250, 252)    # Background #F8FAFC
        bg_surface = (255, 255, 255) # Surface #FFFFFF
        border_col = (226, 232, 240) # Border #E2E8F0
        text_primary = (30, 41, 59)  # Text Primary #1E293B
        text_disabled = (100, 116, 139) # Text Secondary #64748B
        primary = (2, 132, 199)      # Primary Action #0284C7
        success = (5, 150, 105)      # Success/OK #059669
        warning = (217, 119, 6)      # Warning #D97706
        error = (220, 38, 38)        # Danger/Surge #DC2626
        plot_grid = (241, 245, 249)  # Plot Grid #F1F5F9

    # 1. Глобальная тема
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            # Фон и поверхности
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, bg_base)
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, bg_surface)
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg, bg_surface)
            
            # Границы и Текст
            dpg.add_theme_color(dpg.mvThemeCol_Border, border_col)
            dpg.add_theme_color(dpg.mvThemeCol_Text, text_primary)
            dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, text_disabled)

            # Поля ввода / Фон графика
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, plot_grid)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, border_col)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, border_col)

            # Основные кнопки и акценты
            dpg.add_theme_color(dpg.mvThemeCol_Button, primary)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, primary)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, primary)
            dpg.add_theme_color(dpg.mvThemeCol_Header, primary)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, primary)

            # Графики
            dpg.add_theme_color(dpg.mvThemeCol_PlotLines, primary)
            dpg.add_theme_color(dpg.mvThemeCol_PlotLinesHovered, primary)
            dpg.add_theme_color(dpg.mvPlotCol_PlotBg, plot_grid)
            
            # Таблицы
            dpg.add_theme_color(dpg.mvThemeCol_TableHeaderBg, plot_grid)
            dpg.add_theme_color(dpg.mvThemeCol_TableBorderStrong, border_col)
            dpg.add_theme_color(dpg.mvThemeCol_TableBorderLight, border_col)
            dpg.add_theme_color(dpg.mvThemeCol_TableRowBg, bg_surface)
            dpg.add_theme_color(dpg.mvThemeCol_TableRowBgAlt, bg_base)

            # Меню
            dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg, bg_surface)
            

    palette = ThemePalette(
        bg_base=bg_base,
        bg_surface=bg_surface,
        border_col=border_col,
        text_primary=text_primary,
        text_disabled=text_disabled,
        primary=primary,
        success=success,
        warning=warning,
        error=error,
        plot_grid=plot_grid,
    )

    # 2. Темы статусов
    status_themes = {}
    for name, color in {"success": success, "warning": warning, "error": error}.items():
        with dpg.theme() as theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_Text, color)
                dpg.add_theme_color(dpg.mvThemeCol_Button, color)
        status_themes[name] = theme

    # 3. Регистрация шрифтов
    with dpg.font_registry():
        try:
            body_font = dpg.add_font(INTER_REGULAR, 16)
            h2_font   = dpg.add_font(INTER_MEDIUM, 20)
            h1_font   = dpg.add_font(INTER_BOLD, 24)
            mono_font = dpg.add_font(MONO_REGULAR, 16)
        except Exception:
            # Fallback на системный шрифт, если папки fonts нет
            body_font = dpg.add_font("C:\\Windows\\Fonts\\Arial.ttf", 16)
            h2_font = body_font
            h1_font = body_font
            mono_font = body_font

    dpg.bind_theme(global_theme)
    dpg.bind_font(body_font)

    return global_theme, status_themes, palette, body_font, h1_font, h2_font, mono_font