import sys
import dearpygui.dearpygui as dpg  # ty:ignore[unresolved-import]
from datetime import datetime, timedelta
import csv


class EventLogWindow:
    """Окно журнала событий системы"""
    
    def __init__(self, palette, controller):
        self.palette = palette
        self.controller = controller
        self.events = []
        self.filtered_events = []
        self.current_compressor_id = 1  # ✅ По умолчанию CC-45X
        
        self.window_height = 750
        self.window_width = 1200
        self.table_height = 580
    
    def create(self):
        """Создает окно журнала событий"""
        with dpg.window(
            label="Журнал событий", 
            tag="event_log_window", 
            show=False, 
            width=self.window_width, 
            height=self.window_height,
            no_scrollbar=True,
            no_collapse=True
        ):
            dpg.add_text("ЖУРНАЛ СОБЫТИЙ СИСТЕМЫ АПЗ", color=self.palette.primary + (255,))
            dpg.add_separator()

            with dpg.group(horizontal=True):
                dpg.add_text("Период:", color=self.palette.text_primary + (255,))
                dpg.add_input_text(tag="event_start_date", 
                                  default_value=(datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"), 
                                  width=100)
                dpg.add_text("—", color=self.palette.text_primary + (255,))
                dpg.add_input_text(tag="event_end_date", 
                                  default_value=datetime.now().strftime("%Y-%m-%d"), 
                                  width=100)
                
                dpg.add_spacer(width=20)
                dpg.add_text("Компрессор:", color=self.palette.text_primary + (255,))
                
                # ✅ Загружаем компрессоры из БД
                compressors = self.controller.get_all_compressors()
                self.compressor_map = {c["name"]: c["compressor_id"] for c in compressors}
                compressor_names = list(self.compressor_map.keys())
                
                dpg.add_combo(
                    compressor_names, 
                    default_value=compressor_names[0] if compressor_names else "CC-45X", 
                    tag="event_compressor", 
                    width=150
                )
                
                dpg.add_spacer(width=20)
                dpg.add_button(label="Применить фильтры", callback=self._apply_filters, width=150)
                dpg.add_button(label="Сбросить", callback=self._reset_filters, width=100)

            dpg.add_spacer(height=8)

            with dpg.child_window(
                height=self.table_height,
                tag="event_table_container", 
                border=True
            ):
                with dpg.table(
                    header_row=True, 
                    borders_innerH=True, borders_outerH=True,
                    borders_innerV=True, borders_outerV=True, 
                    height=-1,
                    tag="event_table"
                ):
                    dpg.add_table_column(label="Время", width_fixed=True, init_width_or_weight=160)
                    dpg.add_table_column(label="Q, кг/с", width_fixed=True, init_width_or_weight=80)
                    dpg.add_table_column(label="H, кПа", width_fixed=True, init_width_or_weight=80)
                    dpg.add_table_column(label="Маржа, %", width_fixed=True, init_width_or_weight=90)
                    dpg.add_table_column(label="dQ/dt", width_fixed=True, init_width_or_weight=80)
                    dpg.add_table_column(label="Клапан, %", width_fixed=True, init_width_or_weight=90)
                    dpg.add_table_column(label="Статус", width_fixed=True, init_width_or_weight=120)

            dpg.add_spacer(height=8)

            with dpg.group(horizontal=True):
                dpg.add_button(label="Скачать CSV", callback=self._export_csv, width=150)
                dpg.add_button(label="Обновить", callback=self._load_events, width=120)
                dpg.add_button(label="Закрыть", 
                              callback=lambda: dpg.configure_item("event_log_window", show=False), 
                              width=100)
                
                dpg.add_spacer(width=20)
                dpg.add_text("Всего событий: 0", tag="event_count", 
                            color=self.palette.text_primary + (255,))

        self._load_events()
    
    def set_compressor(self, compressor_id: int):
        """✅ Устанавливает компрессор для фильтрации событий"""
        self.current_compressor_id = compressor_id
        
        # Обновляем combo box
        compressor_name = next((name for name, cid in self.compressor_map.items() if cid == compressor_id), None)
        if compressor_name and dpg.does_item_exist("event_compressor"):
            dpg.set_value("event_compressor", compressor_name)
        
        # Перезагружаем события
        self._load_events()
    
    def _load_events(self, sender=None, app_data=None):
        """Загружает события из БД с учётом выбранного компрессора"""
        try:
            # ✅ Получаем выбранный компрессор из combo box
            selected_name = dpg.get_value("event_compressor") if dpg.does_item_exist("event_compressor") else "CC-45X"
            compressor_id = self.compressor_map.get(selected_name, 1)
            self.current_compressor_id = compressor_id
            
            # ✅ Загружаем события для конкретного компрессора
            self.events = self.controller.get_event_log(
                compressor_id=compressor_id,
                limit=500
            )
            self.filtered_events = self.events
            self._render_table()
        except Exception as e:
            print(f"Ошибка загрузки событий: {e}", file=sys.stderr)
    
    def _apply_filters(self, sender=None, app_data=None):
        """Применяет фильтры к событиям"""
        try:
            start_date_str = dpg.get_value("event_start_date")
            end_date_str = dpg.get_value("event_end_date")
            
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d") if start_date_str else None
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d") if end_date_str else None
            
            if start_date:
                start_date = start_date.replace(hour=0, minute=0, second=0)
            if end_date:
                end_date = end_date.replace(hour=23, minute=59, second=59)
            
            # ✅ Также учитываем компрессор
            selected_name = dpg.get_value("event_compressor")
            compressor_id = self.compressor_map.get(selected_name, 1)
            
            # Перезагружаем события для выбранного компрессора
            self.events = self.controller.get_event_log(
                compressor_id=compressor_id,
                start_date=start_date,
                end_date=end_date,
                limit=500
            )
            self.filtered_events = self.events
            self._render_table()
        except Exception as e:
            print(f"Ошибка применения фильтров: {e}", file=sys.stderr)
    
    def _reset_filters(self, sender=None, app_data=None):
        """Сбрасывает фильтры"""
        dpg.set_value("event_start_date", (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"))
        dpg.set_value("event_end_date", datetime.now().strftime("%Y-%m-%d"))
        self._load_events()
    
    def _render_table(self):
        """Отрисовывает таблицу событий"""
        if dpg.does_item_exist("event_table"):
            children = dpg.get_item_children("event_table", slot=1)
            for child in children:
                dpg.delete_item(child)
        
        for event in self.filtered_events:
            status = "SURGE" if event["status"] else ("WARNING" if event["margin"] < 10 else "NORMAL")
            
            if status == "SURGE":
                status_color = self.palette.error + (255,)
            elif status == "WARNING":
                status_color = self.palette.warning + (255,)
            else:
                status_color = self.palette.success + (255,)
            
            timestamp = event["timestamp"]
            if isinstance(timestamp, datetime):
                timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            else:
                timestamp_str = str(timestamp)
            
            with dpg.table_row(parent="event_table"):
                dpg.add_text(timestamp_str)
                dpg.add_text(f"{event['q']:.2f}" if event.get('q') else "0.00")
                dpg.add_text(f"{event['h']:.2f}" if event.get('h') else "0.00")
                dpg.add_text(f"{event['margin']:.1f}" if event.get('margin') else "0.0")
                dpg.add_text(f"{event['dqdt']:.2f}" if event.get('dqdt') else "0.00")
                dpg.add_text(f"{event['valve_position']:.1f}%" if event.get('valve_position') else "0.0%")
                dpg.add_text(status, color=status_color)
        
        if dpg.does_item_exist("event_count"):
            dpg.set_value("event_count", f"Всего событий: {len(self.filtered_events)}")
    
    def _export_csv(self, sender=None, app_data=None):
        """Экспортирует события в CSV"""
        try:
            filename = f"event_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Время", "Q", "H", "Маржа", "dQ/dt", "Клапан", "Статус"])
                
                for event in self.filtered_events:
                    status = "SURGE" if event["status"] else ("WARNING" if event.get("margin", 0) < 10 else "NORMAL")
                    timestamp = event["timestamp"]
                    if isinstance(timestamp, datetime):
                        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        timestamp_str = str(timestamp)
                    
                    writer.writerow([
                        timestamp_str,
                        f"{event.get('q', 0):.2f}",
                        f"{event.get('h', 0):.2f}",
                        f"{event.get('margin', 0):.1f}",
                        f"{event.get('dqdt', 0):.2f}",
                        f"{event.get('valve_position', 0):.1f}",
                        status
                    ])
            
            print(f"✅ Экспорт в {filename} завершен", file=sys.stderr)
            if dpg.does_item_exist("event_count"):
                dpg.set_value("event_count", f"Экспорт: {filename}")
                
        except Exception as e:
            print(f"❌ Ошибка экспорта: {e}", file=sys.stderr)
    
    def show(self):
        """Показывает окно журнала событий"""
        self._load_events()
        dpg.configure_item("event_log_window", show=True)