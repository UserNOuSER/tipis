import dearpygui.dearpygui as dpg  # ty:ignore[unresolved-import]

class ControlPanel:
    def __init__(self, palette):
        self.palette = palette

    def create(self, parent_tag, callbacks):
        # ВАЖНО: используем parent=parent_tag
        with dpg.group(horizontal=True, parent=parent_tag):
            dpg.add_spacer(width=10)
            
            dpg.add_button(label="Тест тревоги (Помпаж)", 
                          callback=callbacks['test_alarm'], width=250, height=60)
            
            dpg.add_spacer(width=20)
            
            dpg.add_button(label="Экспорт телеметрии", 
                          callback=callbacks['export_data'], width=250, height=60)
            
            dpg.add_spacer(width=20)
            
            dpg.add_button(label="Подтвердить тревогу", 
                          callback=lambda: dpg.configure_item("surge_alert", show=False), 
                          width=250, height=60)