import sys
import dearpygui.dearpygui as dpg  # ty:ignore[unresolved-import]
from datetime import datetime, timedelta
import csv
from db.repository import Database


class EventLogWindow:
    """Окно журнала событий системы"""
    
    def __init__(self, palette, controller):
        self.palette = palette
        self.controller = controller
        self.db = Database()
        self.events = []
        self.filtered_events = []
        self.current_compressor_id = 1
        
        self.window_height = 750
        self.window_width = 1200
        self.table_height = 580
        
        # Данные для мини-графика в деталях
        self.detail_gdx_curves = {}
        self.detail_surge_line = {'x': [], 'y': []}
    
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
                    dpg.add_table_column(label="", width_fixed=True, init_width_or_weight=100)  #  Колонка для кнопки

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

        #  Создаём окно деталей
        self._create_details_window()
        
        #  Загружаем данные ГДХ для мини-графика
        self._load_detail_gdx_data()
        
        self._load_events()
    
    def _create_details_window(self):
        """Создаёт модальное окно с деталями события"""
        with dpg.window(
            label="Детали события",
            tag="event_details_window",
            show=False,
            width=900,
            height=650,
            modal=True,
            no_collapse=True,
            no_resize=True
        ):
            dpg.add_text("ДЕТАЛИ СОБЫТИЯ", color=self.palette.primary + (255,))
            dpg.add_separator()
            dpg.add_spacer(height=10)
            
            with dpg.group(horizontal=True):
                # Левая панель: мета-информация
                with dpg.child_window(width=420, height=300, border=True):
                    dpg.add_text("Параметры события", color=self.palette.primary + (255,))
                    dpg.add_separator()
                    dpg.add_spacer(height=5)
                    
                    dpg.add_text("Время:", color=self.palette.text_disabled + (255,))
                    dpg.add_text("—", tag="detail_timestamp", color=self.palette.text_primary + (255,))
                    
                    dpg.add_spacer(height=5)
                    dpg.add_text("Компрессор:", color=self.palette.text_disabled + (255,))
                    dpg.add_text("—", tag="detail_compressor", color=self.palette.text_primary + (255,))
                    
                    dpg.add_spacer(height=5)
                    dpg.add_text("Состав газа:", color=self.palette.text_disabled + (255,))
                    dpg.add_text("—", tag="detail_gas", color=self.palette.text_primary + (255,))
                    
                    dpg.add_spacer(height=5)
                    dpg.add_text("Статус АПЗ:", color=self.palette.text_disabled + (255,))
                    dpg.add_text("—", tag="detail_status", color=self.palette.text_primary + (255,))
                    
                    dpg.add_spacer(height=5)
                    dpg.add_text("Сработавшее правило:", color=self.palette.text_disabled + (255,))
                    dpg.add_text("—", tag="detail_rule", color=self.palette.text_primary + (255,))
                    
                    dpg.add_spacer(height=5)
                    dpg.add_text("Время реакции:", color=self.palette.text_disabled + (255,))
                    dpg.add_text("—", tag="detail_reaction", color=self.palette.text_primary + (255,))
                
                # Правая панель: телеметрия
                with dpg.child_window(width=420, height=300, border=True):
                    dpg.add_text("Телеметрия", color=self.palette.primary + (255,))
                    dpg.add_separator()
                    dpg.add_spacer(height=5)
                    
                    dpg.add_text("Расход Q:", color=self.palette.text_disabled + (255,))
                    dpg.add_text("—", tag="detail_q", color=self.palette.text_primary + (255,))
                    
                    dpg.add_spacer(height=5)
                    dpg.add_text("Напор H:", color=self.palette.text_disabled + (255,))
                    dpg.add_text("—", tag="detail_h", color=self.palette.text_primary + (255,))
                    
                    dpg.add_spacer(height=5)
                    dpg.add_text("Давление на входе P_in:", color=self.palette.text_disabled + (255,))
                    dpg.add_text("—", tag="detail_p_in", color=self.palette.text_primary + (255,))
                    
                    dpg.add_spacer(height=5)
                    dpg.add_text("Давление на выходе P_out:", color=self.palette.text_disabled + (255,))
                    dpg.add_text("—", tag="detail_p_out", color=self.palette.text_primary + (255,))
                    
                    dpg.add_spacer(height=5)
                    dpg.add_text("Температура T:", color=self.palette.text_disabled + (255,))
                    dpg.add_text("—", tag="detail_t", color=self.palette.text_primary + (255,))
                    
                    dpg.add_spacer(height=5)
                    dpg.add_text("Маржа помпажа:", color=self.palette.text_disabled + (255,))
                    dpg.add_text("—", tag="detail_margin", color=self.palette.text_primary + (255,))
                    
                    dpg.add_spacer(height=5)
                    dpg.add_text("Скорость изменения dQ/dt:", color=self.palette.text_disabled + (255,))
                    dpg.add_text("—", tag="detail_dqdt", color=self.palette.text_primary + (255,))
                    
                    dpg.add_spacer(height=5)
                    dpg.add_text("Положение клапана:", color=self.palette.text_disabled + (255,))
                    dpg.add_text("—", tag="detail_valve", color=self.palette.text_primary + (255,))
            
            
            # Мини-график ГДХ
            with dpg.child_window(width=-1, height=250, border=True, tag="detail_plot_container"):
                with dpg.plot(
                    label="ГДХ — состояние в момент события",
                    width=-1,
                    height=-1,
                    tag="detail_plot",
                    no_title=True,
                    no_menus=True
                ):
                    dpg.add_plot_axis(dpg.mvXAxis, label="Расход Q, кг/с", tag="detail_x_axis")
                    dpg.add_plot_axis(dpg.mvYAxis, label="Напор H, кПа", tag="detail_y_axis")
                    
                    # Точка события
                    dpg.add_scatter_series(
                        [0], [0],
                        label="Состояние",
                        parent="detail_y_axis",
                        tag="detail_event_point"
                    )
                    with dpg.theme() as point_theme:
                        with dpg.theme_component(dpg.mvScatterSeries):
                            dpg.add_theme_color(dpg.mvPlotCol_Line, (255, 255, 0, 255))
                            dpg.add_theme_color(dpg.mvPlotCol_Fill, (255, 255, 0, 255))
                    dpg.bind_item_theme("detail_event_point", point_theme)
            
    
    def _load_detail_gdx_data(self):
        """Загружает данные ГДХ для мини-графика в деталях"""
        try:
            points = self.db.get_gdx_points(compressor_id=1)
            
            for point in points:
                rpm = point['rpm']
                if rpm not in self.detail_gdx_curves:
                    self.detail_gdx_curves[rpm] = {'x': [], 'y': []}
                self.detail_gdx_curves[rpm]['x'].append(point['q'])
                self.detail_gdx_curves[rpm]['y'].append(point['h'])
            
            surge_points = self.db.get_surge_boundary(compressor_id=1)
            for point in surge_points:
                self.detail_surge_line['x'].append(point['q_surge'])
                self.detail_surge_line['y'].append(point['h_surge'])
            
            # Рисуем кривые на мини-графике
            colors = [(14, 165, 233), (16, 185, 129), (245, 158, 11), (239, 68, 68)]
            for idx, (rpm, data) in enumerate(self.detail_gdx_curves.items()):
                color = colors[idx % len(colors)]
                dpg.add_line_series(
                    data['x'], data['y'],
                    label=f"{rpm} об/мин",
                    parent="detail_y_axis",
                    tag=f"detail_curve_{rpm}"
                )
                with dpg.theme() as curve_theme:
                    with dpg.theme_component(dpg.mvLineSeries):
                        dpg.add_theme_color(dpg.mvPlotCol_Line, color + (255,))
                dpg.bind_item_theme(f"detail_curve_{rpm}", curve_theme)
            
            # Линия помпажа
            if self.detail_surge_line['x']:
                dpg.add_line_series(
                    self.detail_surge_line['x'],
                    self.detail_surge_line['y'],
                    label="Линия помпажа",
                    parent="detail_y_axis",
                    tag="detail_surge_line"
                )
                with dpg.theme() as surge_theme:
                    with dpg.theme_component(dpg.mvLineSeries):
                        dpg.add_theme_color(dpg.mvPlotCol_Line, (239, 68, 68, 255))
                dpg.bind_item_theme("detail_surge_line", surge_theme)
            
        except Exception as e:
            print(f"Ошибка загрузки ГДХ для деталей: {e}", file=sys.stderr)
    
    def _show_event_details(self, sender=None, app_data=None, user_data=None):
        """Показывает детали события по клику на кнопку """
        if user_data is None:
            return
        
        event_id = user_data
        event = self.db.get_event_details(event_id)
        
        if not event:
            print(f"Событие {event_id} не найдено", file=sys.stderr)
            return
        
        # Заполняем поля
        timestamp = event.get("timestamp")
        if isinstance(timestamp, datetime):
            timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        else:
            timestamp_str = str(timestamp)
        
        dpg.set_value("detail_timestamp", timestamp_str)
        
        # Компрессор
        compressor_id = event.get("compressor_id", 1)
        compressor_name = next((name for name, cid in self.compressor_map.items() if cid == compressor_id), "Неизвестно")
        dpg.set_value("detail_compressor", compressor_name)
        
        # Состав газа
        gas_comp = event.get("gas_composition", "—") or "—"
        dpg.set_value("detail_gas", gas_comp)
        
        # Статус
        status = "SURGE" if event.get("status") else ("WARNING" if event.get("margin", 100) < 10 else "NORMAL")
        if status == "SURGE":
            dpg.configure_item("detail_status", color=self.palette.error + (255,))
        elif status == "WARNING":
            dpg.configure_item("detail_status", color=self.palette.warning + (255,))
        else:
            dpg.configure_item("detail_status", color=self.palette.success + (255,))
        dpg.set_value("detail_status", status)
        
        # Правило
        dpg.set_value("detail_rule", event.get("rule_fired", "—") or "—")
        
        # Время реакции
        reaction_time = event.get("reaction_time", 0.0) or 0.0
        dpg.set_value("detail_reaction", f"{reaction_time:.2f} мс")
        
        # Телеметрия
        dpg.set_value("detail_q", f"{event.get('q', 0):.2f} кг/с")
        dpg.set_value("detail_h", f"{event.get('h', 0):.2f} кПа")
        dpg.set_value("detail_p_in", f"{event.get('p_in', 0):.2f} бар")
        dpg.set_value("detail_p_out", f"{event.get('p_out', 0):.2f} бар")
        dpg.set_value("detail_t", f"{event.get('t_in', 0):.1f} °C")
        dpg.set_value("detail_margin", f"{event.get('margin', 0):.1f} %")
        dpg.set_value("detail_dqdt", f"{event.get('dqdt', 0):.2f} кг/с²")
        dpg.set_value("detail_valve", f"{event.get('valve_position', 0):.1f} %")
        
        #  Обновляем точку на мини-графике
        q = event.get('q', 0)
        h = event.get('h', 0)
        
        # Цвет точки зависит от статуса
        if status == "SURGE":
            point_color = (239, 68, 68, 255)  # Красный
        elif status == "WARNING":
            point_color = (245, 158, 11, 255)  # Жёлтый
        else:
            point_color = (16, 185, 129, 255)  # Зелёный
        
        dpg.set_value("detail_event_point", [[q], [h]])
        
        # Обновляем цвет точки
        with dpg.theme() as new_point_theme:
            with dpg.theme_component(dpg.mvScatterSeries):
                dpg.add_theme_color(dpg.mvPlotCol_Line, point_color)
                dpg.add_theme_color(dpg.mvPlotCol_Fill, point_color)
        dpg.bind_item_theme("detail_event_point", new_point_theme)
        
        # Показываем окно
        dpg.configure_item("event_details_window", show=True)
    
    def set_compressor(self, compressor_id: int):
        """Устанавливает компрессор для фильтрации событий"""
        self.current_compressor_id = compressor_id
        
        compressor_name = next((name for name, cid in self.compressor_map.items() if cid == compressor_id), None)
        if compressor_name and dpg.does_item_exist("event_compressor"):
            dpg.set_value("event_compressor", compressor_name)
        
        self._load_events()
    
    def _load_events(self, sender=None, app_data=None):
        """Загружает события из БД"""
        try:
            selected_name = dpg.get_value("event_compressor") if dpg.does_item_exist("event_compressor") else "CC-45X"
            compressor_id = self.compressor_map.get(selected_name, 1)
            self.current_compressor_id = compressor_id
            
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
            
            selected_name = dpg.get_value("event_compressor")
            compressor_id = self.compressor_map.get(selected_name, 1)
            
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
            
            #  Получаем event_id для кнопки
            event_id = event.get("event_id")
            
            with dpg.table_row(parent="event_table"):
                dpg.add_text(timestamp_str)
                dpg.add_text(f"{event['q']:.2f}" if event.get('q') else "0.00")
                dpg.add_text(f"{event['h']:.2f}" if event.get('h') else "0.00")
                dpg.add_text(f"{event['margin']:.1f}" if event.get('margin') else "0.0")
                dpg.add_text(f"{event['dqdt']:.2f}" if event.get('dqdt') else "0.00")
                dpg.add_text(f"{event['valve_position']:.1f}%" if event.get('valve_position') else "0.0%")
                dpg.add_text(status, color=status_color)
                
                #  Кнопка  вместо двойного клика
                dpg.add_button(
                    label="Еще",
                    callback=self._show_event_details,
                    user_data=event_id,  #  Передаём ID события
                    width=80,
                    height=20
                )
        
        if dpg.does_item_exist("event_count"):
            dpg.set_value("event_count", f"Всего событий: {len(self.filtered_events)}")
    
    def _export_csv(self, sender=None, app_data=None):
        """Экспортирует события в CSV"""
        try:
            filename = f"event_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            compressor_id_to_name = {cid: name for name, cid in self.compressor_map.items()}
            
            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Время", "Q", "H", "Маржа", "dQ/dt", "Клапан", "Статус",
                    "Время реакции (мс)", "Компрессор", "Состав газа"
                ])
                
                for event in self.filtered_events:
                    status = "SURGE" if event["status"] else ("WARNING" if event.get("margin", 0) < 10 else "NORMAL")
                    timestamp = event["timestamp"]
                    if isinstance(timestamp, datetime):
                        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        timestamp_str = str(timestamp)
                    
                    reaction_time = event.get("reaction_time", 0.0) or 0.0
                    gas_composition = event.get("gas_composition", "") or "—"
                    compressor_name = compressor_id_to_name.get(event.get("compressor_id", 1), "Неизвестно")
                    
                    writer.writerow([
                        timestamp_str,
                        f"{event.get('q', 0):.2f}",
                        f"{event.get('h', 0):.2f}",
                        f"{event.get('margin', 0):.1f}",
                        f"{event.get('dqdt', 0):.2f}",
                        f"{event.get('valve_position', 0):.1f}",
                        status,
                        f"{reaction_time:.2f}",
                        compressor_name,
                        gas_composition
                    ])
            
            print(f" Экспорт в {filename} завершен", file=sys.stderr)
            if dpg.does_item_exist("event_count"):
                dpg.set_value("event_count", f"Экспорт: {filename}")
                
        except Exception as e:
            print(f" Ошибка экспорта: {e}", file=sys.stderr)
    
    def show(self):
        """Показывает окно журнала событий"""
        self._load_events()
        dpg.configure_item("event_log_window", show=True)