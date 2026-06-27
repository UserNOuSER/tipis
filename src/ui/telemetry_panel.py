import dearpygui.dearpygui as dpg  # ty:ignore[unresolved-import]

class TelemetryPanel:
    TAGS = {
        'compressor': 'val_compressor',
        'gas_composition': 'val_gas_composition',
        'p_in': 'val_p_in',
        'p_out': 'val_p_out',
        't': 'val_t',
        'q': 'val_q',
        'h': 'val_h',
        'dqdt': 'val_dqdt',
        'margin': 'val_margin',
        'valve': 'val_valve',
        'status': 'val_status',
        'last_used_rule': 'val_last_used_rule',
        'reaction_time': 'val_reaction_time',
    }
    
    def __init__(self, palette):
        self.palette = palette

    def create(self, parent_tag):
        """Заполняет родительский контейнер таблицей телеметрии"""
        dpg.add_text("ПАРАМЕТРЫ В РЕАЛЬНОМ ВРЕМЕНИ", parent=parent_tag, 
                    color=self.palette.primary + (255,), tag="telemetry_header")
        dpg.add_separator(parent=parent_tag)
        dpg.add_spacer(height=8, parent=parent_tag)

        with dpg.table(header_row=False, borders_innerH=True, borders_outerH=True, 
                       borders_innerV=True, borders_outerV=True, height=-1, parent=parent_tag):
            dpg.add_table_column(width_fixed=True, init_width_or_weight=240)
            dpg.add_table_column(width_stretch=True)

            params = [
                ("Компрессор:", self.TAGS['compressor'], ""),
                ("Состав газа:", self.TAGS['gas_composition'], ""),
                ("Давление на входе (P_in):", self.TAGS['p_in'], "бар"),
                ("Давление на выходе (P_out):", self.TAGS['p_out'], "бар"),
                ("Температура (T):", self.TAGS['t'], "°C"),
                ("Расход (Q):", self.TAGS['q'], "кг/с"),
                ("Напор (H):", self.TAGS['h'], "кПа"),
                ("Скорость изменения (dQ/dt):", self.TAGS['dqdt'], "кг/с²"),
                ("Маржа помпажа (ΔP):", self.TAGS['margin'], "%"),
                ("Положение клапана:", self.TAGS['valve'], "%"),
                ("Статус АПЗ:", self.TAGS['status'], ""),
                ("Последнее использованное правило:", self.TAGS['last_used_rule'], ""),
                ("Время реакции ядра:", self.TAGS['reaction_time'], "мс"),
            ]

            for label, tag, unit in params:
                with dpg.table_row():
                    dpg.add_text(label, tag=f"{tag}_label")
                    with dpg.group(horizontal=True):
                        dpg.add_text("0.00", tag=tag, color=self.palette.text_primary + (255,))
                        if unit:
                            dpg.add_text(unit, tag=f"{tag}_unit", 
                                       color=self.palette.text_disabled + (255,))

    def update(self, sensor_data, processed, command):
        """Обновляет значения в таблице по переданным DTO"""
        if not all([sensor_data, processed, command]):
            return
            
        try:
            dpg.set_value(self.TAGS['q'], f"{sensor_data.Q:.2f}")
            dpg.set_value(self.TAGS['h'], f"{processed.H_rel:.0f}")
            dpg.set_value(self.TAGS['p_in'], f"{sensor_data.P_in:.2f}")
            dpg.set_value(self.TAGS['p_out'], f"{sensor_data.P_out:.2f}")
            dpg.set_value(self.TAGS['t'], f"{sensor_data.T:.1f}")
            dpg.set_value(self.TAGS['margin'], f"{processed.margin:.1f}")
            dpg.set_value(self.TAGS['dqdt'], f"{processed.dQdt:.2f}")
            dpg.set_value(self.TAGS['valve'], f"{command.valveOpenPercent:.1f}")
            dpg.set_value(self.TAGS['last_used_rule'], command.lastUsedRule)
            dpg.set_value(self.TAGS['compressor'], command.compressorName)
            dpg.set_value(self.TAGS['gas_composition'], command.gasComposition)
            dpg.set_value(self.TAGS['reaction_time'], f"{command.reactionTime:.0f}")
            
            status = command.status
            dpg.set_value(self.TAGS['status'], status)
            
            if status == "SURGE":
                dpg.configure_item(self.TAGS['status'], color=self.palette.error + (255,))
            elif status == "WARNING":
                dpg.configure_item(self.TAGS['status'], color=self.palette.warning + (255,))
            else:
                dpg.configure_item(self.TAGS['status'], color=self.palette.success + (255,))
                
        except Exception as e:
            print(f"Ошибка обновления телеметрии: {e}")

    def update_theme_colors(self, palette):
        """Обновляет цвета всех элементов при смене темы"""
        self.palette = palette
        
        try:
            # Обновляем заголовок
            if dpg.does_item_exist("telemetry_header"):
                dpg.configure_item("telemetry_header", color=palette.primary + (255,))
            
            # Обновляем все значения и единицы измерения
            for key, tag in self.TAGS.items():
                # Значения
                if dpg.does_item_exist(tag):
                    # Для статуса цвет зависит от значения, не обновляем здесь
                    if key != 'status':
                        dpg.configure_item(tag, color=palette.text_primary + (255,))
                    else:
                        dpg.configure_item(tag, color=palette.text_primary + (255,))
                
                # Единицы измерения
                unit_tag = f"{tag}_unit"
                if dpg.does_item_exist(unit_tag):
                    dpg.configure_item(unit_tag, color=palette.text_disabled + (255,))
                
                # Названия параметров
                label_tag = f"{tag}_label"
                if dpg.does_item_exist(label_tag):
                    dpg.configure_item(label_tag, color=palette.text_primary + (255,))
                    
        except Exception as e:
            print(f"Ошибка обновления цветов телеметрии: {e}")