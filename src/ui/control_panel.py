# ui/control_panel.py
import dearpygui.dearpygui as dpg  # ty:ignore[unresolved-import]

class ControlPanel:
    def __init__(self, palette):
        self.palette = palette

    def create(self, parent_tag, callbacks):
        with dpg.child_window(width=280, height=400, label="Управление", parent=parent_tag):
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
                          callback=callbacks['test_alarm'], width=-1)
            dpg.add_button(label="📊 Экспорт данных", 
                          callback=callbacks['export_data'], width=-1)