import dearpygui.dearpygui as dpg  # ty:ignore[unresolved-import]

class Modals:
    def __init__(self, palette):  
        self.palette = palette

    def create(self):
        # Окно алерта помпажа
        with dpg.window(label="ВНИМАНИЕ!", tag="surge_alert", show=False, modal=True, no_move=True):
            dpg.add_text("ОБНАРУЖЕН ПОМПАЖ!", tag="surge_alert_text", color=self.palette.error + (255,))
            dpg.add_text("Принимаются меры защиты...")
            dpg.add_button(label="Подтвердить", callback=lambda: dpg.configure_item("surge_alert", show=False))

        # Окно справки
        with dpg.window(label="Справочное окно", tag="help_window", show=False, modal=True, no_move=False):
            dpg.add_text("Справка по системе АПЗ", tag="help_text", color=self.palette.text_primary + (255,))
            dpg.add_text("Тут будет справка...")
            dpg.add_button(label="Ознакомился", callback=lambda: dpg.configure_item("help_window", show=False))