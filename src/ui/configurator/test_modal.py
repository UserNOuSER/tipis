import dearpygui.dearpygui as dpg  # ty:ignore[unresolved-import]
import sys


class TestModal:
    """Модальное окно с результатами теста на истории"""
    
    def __init__(self, palette, controller):
        self.palette = palette
        self.controller = controller
    
    def create(self):
        """Создаёт модальное окно"""
        with dpg.window(
            label="Результаты теста на истории",
            tag="test_results_modal",
            show=False,
            modal=False,  # Не модальное, чтобы можно было свернуть
            no_move=False,
            width=1100,
            height=600,
            no_scrollbar=True
        ):
            dpg.add_text("СРАВНЕНИЕ СТАРОГО И НОВОГО ПОВЕДЕНИЯ", 
                        color=self.palette.primary + (255,))
            dpg.add_separator()
            dpg.add_spacer(height=8)
            
            # Статистика
            with dpg.group(horizontal=True):
                dpg.add_text("Всего событий:", color=self.palette.text_primary + (255,))
                dpg.add_text("0", tag="test_total_count", 
                            color=self.palette.primary + (255,))
                dpg.add_spacer(width=30)
                dpg.add_text("Совпадений:", color=self.palette.text_primary + (255,))
                dpg.add_text("0", tag="test_match_count", 
                            color=self.palette.success + (255,))
                dpg.add_spacer(width=30)
                dpg.add_text("Расхождений:", color=self.palette.text_primary + (255,))
                dpg.add_text("0", tag="test_diff_count", 
                            color=self.palette.error + (255,))
            
            dpg.add_spacer(height=10)
            
            # Таблица результатов
            with dpg.child_window(height=450, tag="test_results_container", border=True):
                with dpg.table(
                    header_row=True,
                    borders_innerH=True, borders_outerH=True,
                    borders_innerV=True, borders_outerV=True,
                    height=-1,
                    tag="test_results_table"
                ):
                    dpg.add_table_column(label="Время", width_fixed=True, init_width_or_weight=150)
                    dpg.add_table_column(label="Маржа", width_fixed=True, init_width_or_weight=70)
                    dpg.add_table_column(label="dQ/dt", width_fixed=True, init_width_or_weight=70)
                    dpg.add_table_column(label="Старый клапан", width_fixed=True, init_width_or_weight=100)
                    dpg.add_table_column(label="Новый клапан", width_fixed=True, init_width_or_weight=100)
                    dpg.add_table_column(label="Разница", width_fixed=True, init_width_or_weight=80)
                    dpg.add_table_column(label="Старый статус", width_fixed=True, init_width_or_weight=100)
                    dpg.add_table_column(label="Новый статус", width_fixed=True, init_width_or_weight=100)
            
            dpg.add_spacer(height=10)
            
            with dpg.group(horizontal=True):
                dpg.add_button(label="[X] Закрыть", 
                              callback=lambda: dpg.configure_item("test_results_modal", show=False), 
                              width=150)
    
    def show_results(self, results):
        """Показывает результаты теста"""
        # Очищаем таблицу
        if dpg.does_item_exist("test_results_table"):
            children = dpg.get_item_children("test_results_table", slot=1)
            for child in children:
                dpg.delete_item(child)
        
        if not results:
            dpg.set_value("test_total_count", "0")
            dpg.set_value("test_match_count", "0")
            dpg.set_value("test_diff_count", "0")
            dpg.configure_item("test_results_modal", show=True)
            return
        
        # Считаем статистику
        match_count = 0
        diff_count = 0
        
        for result in results:
            timestamp = result["timestamp"]
            if hasattr(timestamp, "strftime"):
                timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            else:
                timestamp_str = str(timestamp)
            
            # Цвет для разницы
            diff = result["valve_diff"]
            if abs(diff) < 0.1:
                diff_color = self.palette.success + (255,)
                match_count += 1
            elif abs(diff) > 10:
                diff_color = self.palette.error + (255,)
                diff_count += 1
            else:
                diff_color = self.palette.warning + (255,)
                diff_count += 1
            
            with dpg.table_row(parent="test_results_table"):
                dpg.add_text(timestamp_str)
                dpg.add_text(f"{result['margin']:.1f}")
                dpg.add_text(f"{result['dqdt']:.2f}")
                dpg.add_text(f"{result['old_valve']:.1f}%")
                dpg.add_text(f"{result['new_valve']:.1f}%")
                dpg.add_text(f"{diff:+.1f}", color=diff_color)
                dpg.add_text(result["old_status"])
                dpg.add_text(result["new_status"])
        
        # Обновляем статистику
        dpg.set_value("test_total_count", str(len(results)))
        dpg.set_value("test_match_count", str(match_count))
        dpg.set_value("test_diff_count", str(diff_count))
        
        dpg.configure_item("test_results_modal", show=True)
        print(f"✅ Тест завершён: {len(results)} событий, {match_count} совпадений", 
              file=sys.stderr)