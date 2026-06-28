import dearpygui.dearpygui as dpg  # ty:ignore[unresolved-import]
import sys
from datetime import datetime, timedelta


class ExportWindow:
    """Окно экспорта отчёта"""
    
    def __init__(self, palette, controller):
        self.palette = palette
        self.controller = controller
        
        self.window_width = 600
        self.window_height = 550
    
    def create(self):
        """Создаёт окно экспорта"""
        with dpg.window(
            label="Экспорт отчёта",
            tag="export_window",
            show=False,
            width=self.window_width,
            height=self.window_height,
            no_collapse=True,
            no_resize=True
        ):
            dpg.add_text("ЭКСПОРТ ОТЧЁТА", 
                        color=self.palette.primary + (255,))
            dpg.add_separator()
            dpg.add_spacer(height=10)
            
            # === СЕКЦИЯ 1: Компрессор ===
            dpg.add_text("Компрессор:", color=self.palette.text_primary + (255,))
            dpg.add_spacer(height=5)
            
            # Загружаем компрессоры из БД
            compressors = self.controller.get_all_compressors()
            self.compressor_map = {c["name"]: c["compressor_id"] for c in compressors}
            compressor_names = list(self.compressor_map.keys())
            
            dpg.add_combo(
                compressor_names,
                default_value=compressor_names[0] if compressor_names else "",
                tag="export_compressor",
                width=-1
            )
            
            dpg.add_spacer(height=15)
            
           # === СЕКЦИЯ 2: Период ===
            dpg.add_text("Период:", color=self.palette.text_primary + (255,))
            dpg.add_spacer(height=5)
            
            with dpg.group(horizontal=True):
                dpg.add_text("С:")  # ✅ Убрали width=30
                dpg.add_input_text(
                    tag="export_start_date",
                    default_value=(datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                    width=150,
                    hint="ГГГГ-ММ-ДД"
                )
                dpg.add_spacer(width=10)  # ✅ Добавили отступ вместо width у текста
                dpg.add_text("По:")  # ✅ Убрали width=30
                dpg.add_input_text(
                    tag="export_end_date",
                    default_value=datetime.now().strftime("%Y-%m-%d"),
                    width=150,
                    hint="ГГГГ-ММ-ДД"
                )
                
            dpg.add_spacer(height=15)
            
            # === СЕКЦИЯ 3: Фильтры по статусу ===
            dpg.add_text("Фильтры по статусу:", color=self.palette.text_primary + (255,))
            dpg.add_spacer(height=5)
            
            with dpg.group(horizontal=True):
                dpg.add_checkbox(label="Норма", tag="export_include_normal", default_value=True)
                dpg.add_spacer(width=20)
                dpg.add_checkbox(label="Предупреждения", tag="export_include_warning", default_value=True)
                dpg.add_spacer(width=20)
                dpg.add_checkbox(label="Помпаж", tag="export_include_surge", default_value=True)
            
            dpg.add_spacer(height=15)
            
            # === СЕКЦИЯ 4: Включить конфигурацию ===
            dpg.add_text("Дополнительно:", color=self.palette.text_primary + (255,))
            dpg.add_spacer(height=5)
            
            dpg.add_checkbox(
                label="Включить базу правил в отчёт",
                tag="export_include_rules",
                default_value=True
            )
            
            dpg.add_spacer(height=20)
            
            # === СЕКЦИЯ 5: Информация о формате ===
            with dpg.group(horizontal=True):
                dpg.add_text("Формат:", color=self.palette.text_primary + (255,))
                dpg.add_text("JSON", color=self.palette.primary + (255,))
            
            dpg.add_spacer(height=20)
            dpg.add_separator()
            dpg.add_spacer(height=10)
            
            # === КНОПКИ ===
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="[OK] Экспортировать",
                    callback=self._export_report,
                    width=200,
                    height=40
                )
                dpg.add_spacer(width=20)
                dpg.add_button(
                    label="[X] Отмена",
                    callback=lambda: dpg.configure_item("export_window", show=False),
                    width=150,
                    height=40
                )
            
            dpg.add_spacer(height=15)
            
            # === Статус экспорта ===
            dpg.add_text("", tag="export_status", 
                        color=self.palette.text_primary + (255,))
    
    def _export_report(self, sender=None, app_data=None):
        """Выполняет экспорт отчёта"""
        try:
            # Собираем параметры из UI
            selected_compressor = dpg.get_value("export_compressor")
            compressor_id = self.compressor_map.get(selected_compressor, 1)
            
            start_date_str = dpg.get_value("export_start_date")
            end_date_str = dpg.get_value("export_end_date")
            
            include_normal = dpg.get_value("export_include_normal")
            include_warning = dpg.get_value("export_include_warning")
            include_surge = dpg.get_value("export_include_surge")
            include_rules = dpg.get_value("export_include_rules")
            
            # Преобразуем даты
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d") if start_date_str else None
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d") if end_date_str else None
                
                if start_date:
                    start_date = start_date.replace(hour=0, minute=0, second=0)
                if end_date:
                    end_date = end_date.replace(hour=23, minute=59, second=59)
            except ValueError:
                dpg.set_value("export_status", "❌ Неверный формат даты")
                dpg.configure_item("export_status", color=self.palette.error + (255,))
                return
            
            # Формируем фильтры статусов
            status_filters = []
            if include_normal:
                status_filters.append("normal")
            if include_warning:
                status_filters.append("warning")
            if include_surge:
                status_filters.append("surge")
            
            if not status_filters:
                dpg.set_value("export_status", "❌ Выберите хотя бы один статус")
                dpg.configure_item("export_status", color=self.palette.error + (255,))
                return
            
            # Вызываем экспорт в контроллере
            dpg.set_value("export_status", "⏳ Экспорт...")
            dpg.configure_item("export_status", color=self.palette.warning + (255,))
            
            success, message = self.controller.export_report(
                compressor_id=compressor_id,
                start_date=start_date,
                end_date=end_date,
                status_filters=status_filters,
                include_rules=include_rules
            )
            
            if success:
                dpg.set_value("export_status", f"✅ {message}")
                dpg.configure_item("export_status", color=self.palette.success + (255,))
            else:
                dpg.set_value("export_status", f"❌ {message}")
                dpg.configure_item("export_status", color=self.palette.error + (255,))
        
        except Exception as e:
            dpg.set_value("export_status", f"❌ Ошибка: {e}")
            dpg.configure_item("export_status", color=self.palette.error + (255,))
            print(f"Ошибка экспорта: {e}", file=sys.stderr)
    
    def show(self):
        """Показывает окно экспорта"""
        dpg.configure_item("export_window", show=True)