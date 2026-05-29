import dearpygui.dearpygui as dpg
import os

_FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")

INTER_REGULAR = os.path.join(_FONTS_DIR, "Inter-Regular.ttf")
INTER_MEDIUM  = os.path.join(_FONTS_DIR, "Inter-Medium.ttf")   # или Inter-SemiBold.ttf
INTER_BOLD    = os.path.join(_FONTS_DIR, "Inter-Bold.ttf")
MONO_REGULAR  = os.path.join(_FONTS_DIR, "JetBrainsMono-Regular.ttf")


def setup_design_system():
    """Инициализация глобальной темы и шрифтов"""
    # 1. Глобальная тема (Background, Surface, Border, Text, Inputs, Primary)
    # Замените блок темы в setup_design_system() на этот:
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            # Фон и поверхности
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (248, 250, 252))  # Background #F8FAFC
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (255, 255, 255))   # Surface #FFFFFF
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg, (255, 255, 255))

            table_theme_map = {
                "mvThemeCol_TableHeaderBg": (241, 245, 249),      # Input/Chart BG
                "mvThemeCol_TableBorderStrong": (226, 232, 240),   # Border #E2E8F0
                "mvThemeCol_TableBorderLight": (241, 245, 249),
                "mvThemeCol_TableRowBg": (255, 255, 255),          # Surface #FFFFFF
                "mvThemeCol_TableRowBgAlt": (248, 250, 252),       # Background #F8FAFC (чётные строки)
                "mvThemeCol_HeaderHovered": (226, 232, 240),       # Hover для заголовков и строк
            }

            for token_name, rgb in table_theme_map.items():
                if hasattr(dpg, token_name):
                    dpg.add_theme_color(getattr(dpg, token_name), rgb)

    # Границы
    dpg.add_theme_color(dpg.mvThemeCol_Border, (226, 232, 240))

    # Текст
    dpg.add_theme_color(dpg.mvThemeCol_Text, (30, 41, 59))            # Text Primary #1E293B
    dpg.add_theme_color(dpg.mvThemeCol_TextDisabled, (100, 116, 139)) # Text Secondary #64748B

    # Поля ввода / Фон графика
    dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (241, 245, 249))      # Input/Chart BG #F1F5F9
    dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (226, 232, 240))
    dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (226, 232, 240))

    # Основные кнопки и акценты
    dpg.add_theme_color(dpg.mvThemeCol_Button, (2, 132, 199))         # Primary #0284C7
    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (3, 105, 161))
    dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (7, 89, 133))
    dpg.add_theme_color(dpg.mvThemeCol_Header, (2, 132, 199))
    dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (3, 105, 161))

    # Графики
    dpg.add_theme_color(dpg.mvThemeCol_PlotLines, (2, 132, 199))
    dpg.add_theme_color(dpg.mvThemeCol_PlotLinesHovered, (3, 105, 161))

    # 2. Темы статусов (динамическое применение)
    status_themes = {}
    for name, color in {
        "success": (5, 150, 105),   # #059669
        "warning": (217, 119, 6),   # #D97706
        "error":   (220, 38, 38)    # #DC2626
    }.items():
        with dpg.theme() as theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_Text, color)
                dpg.add_theme_color(dpg.mvThemeCol_Button, color)
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, color)
        status_themes[name] = theme

    # 3️⃣ Регистрация шрифтов с разными начертаниями
    with dpg.font_registry():
        body_font = dpg.add_font(INTER_REGULAR, 16)          # Body 16px
        h2_font   = dpg.add_font(INTER_MEDIUM, 20)           # H2 20px (полужирный)
        h1_font   = dpg.add_font(INTER_BOLD, 24)             # H1 24px (жирный)
        mono_font = dpg.add_font(MONO_REGULAR, 16)           # Mono 16px (цифры, логи)

    # Привязка темы и шрифта по умолчанию
    dpg.bind_theme(global_theme)
    dpg.bind_font(body_font)

    return global_theme, status_themes, body_font, h1_font, h2_font, mono_font