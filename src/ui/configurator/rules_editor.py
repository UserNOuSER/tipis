# ui/configurator/rules_editor.py
import dearpygui.dearpygui as dpg  # ty:ignore[unresolved-import]
import sys


class RulesEditor:
    """Редактор базы правил нечёткого вывода"""
    
    def __init__(self, palette, controller):
        self.palette = palette
        self.controller = controller
        self.rules = []
        self.editing_rule_index = None
        self.deleting_rule_index = None  # ✅ НОВОЕ: индекс удаляемого правила
    
    def create(self, parent_tag):
        """Создаёт таблицу правил"""
        with dpg.child_window(height=-1, tag="rules_table_container", border=True):
            with dpg.table(
                header_row=True,
                borders_innerH=True, borders_outerH=True,
                borders_innerV=True, borders_outerV=True,
                height=-1,
                tag="rules_table"
            ):
                dpg.add_table_column(label="#", width_fixed=True, init_width_or_weight=40)
                dpg.add_table_column(label="Правило", width_stretch=True)
                # ✅ Увеличили ширину колонки для 3 кнопок
                dpg.add_table_column(label="Действия", width_fixed=True, init_width_or_weight=200)
    
    def create_modals(self):
        """Создаёт модальные окна"""
        self._create_rule_modal("add_rule_modal", "Добавить правило", self._add_rule)
        self._create_rule_modal("edit_rule_modal", "Редактировать правило", self._save_edited_rule)
        self._create_delete_rule_modal()  # ✅ НОВОЕ
    
    def _create_rule_modal(self, tag, title, callback):
        """Создаёт модальное окно для правила"""
        prefix = tag.replace("_modal", "")
        
        with dpg.window(
            label=title,
            tag=tag,
            show=False,
            modal=True,
            no_move=True,
            width=550,
            height=300
        ):
            dpg.add_text("Antecedent (IF):")
            dpg.add_input_text(
                tag=f"{prefix}_antecedent",
                width=-1,
                hint="Например: (Маржа IS Низкая) AND (dQdt IS Neg)"
            )
            
            dpg.add_spacer(height=10)
            dpg.add_text("Consequent (THEN):")
            dpg.add_input_text(
                tag=f"{prefix}_consequent",
                width=-1,
                hint="Например: (valve IS Open_100)"
            )
            
            dpg.add_spacer(height=10)
            with dpg.group(horizontal=True):
                dpg.add_text("Weight:")
                dpg.add_input_float(tag=f"{prefix}_weight", default_value=1.0, 
                                   width=80, min_value=0.0, max_value=1.0)
                dpg.add_spacer(width=20)
                dpg.add_text("Priority:")
                dpg.add_input_int(tag=f"{prefix}_priority", default_value=1, 
                                 width=80, min_value=1)
            
            dpg.add_spacer(height=15)
            with dpg.group(horizontal=True):
                dpg.add_button(label="[OK] Сохранить", callback=callback, width=180)
                dpg.add_button(label="[X] Отмена", 
                              callback=lambda: dpg.configure_item(tag, show=False), 
                              width=180)
    
    def _create_delete_rule_modal(self):
        """Создаёт модальное окно подтверждения удаления правила"""
        with dpg.window(
            label="Подтверждение удаления",
            tag="delete_rule_modal",
            show=False,
            modal=True,
            no_move=True,
            width=500,
            height=200
        ):
            dpg.add_text("Вы уверены, что хотите удалить правило?", 
                        color=self.palette.error + (255,))
            dpg.add_spacer(height=10)
            dpg.add_text("Правило:", color=self.palette.text_primary + (255,))
            dpg.add_text("", tag="delete_rule_preview", 
                        color=self.palette.text_primary + (255,))
            
            dpg.add_spacer(height=15)
            with dpg.group(horizontal=True):
                dpg.add_button(label="[Удалить]", callback=self._confirm_delete_rule, width=180)
                dpg.add_button(label="[X] Отмена", 
                              callback=lambda: dpg.configure_item("delete_rule_modal", show=False), 
                              width=180)
    
    def refresh(self, sender=None, app_data=None):
        """Обновляет таблицу правил из контроллера"""
        self.rules = self.controller.get_current_rules()
        self._render_table()
    
    def get_rules(self):
        """Возвращает текущий список правил"""
        return self.rules
    
    def _render_table(self):
        """Отрисовывает таблицу правил"""
        if dpg.does_item_exist("rules_table"):
            children = dpg.get_item_children("rules_table", slot=1)
            for child in children:
                dpg.delete_item(child)
        
        if not self.rules:
            with dpg.table_row(parent="rules_table"):
                dpg.add_text("")
                dpg.add_text("Нет правил. Нажмите 'Добавить правило'.", 
                            color=self.palette.text_disabled + (255,))
                dpg.add_text("")
            return
        
        for idx, rule in enumerate(self.rules):
            antecedent = rule.get("antecedent", "")
            consequent = rule.get("consequent", "")
            rule_text = f"IF {antecedent} THEN {consequent}"
            
            with dpg.table_row(parent="rules_table"):
                dpg.add_text(str(idx + 1))
                dpg.add_text(rule_text)
                
                with dpg.group(horizontal=True):
                    dpg.add_button(
                        label="[Ред]",
                        callback=self._edit_rule,
                        user_data=idx,
                        width=50, height=25
                    )
                    # ✅ НОВАЯ КНОПКА УДАЛЕНИЯ
                    dpg.add_button(
                        label="[Удал]",
                        callback=self._show_delete_modal,
                        user_data=idx,
                        width=60, height=25
                    )
    
    def show_add_modal(self, sender=None, app_data=None):
        """Открывает модалку добавления правила"""
        dpg.set_value("add_rule_antecedent", "")
        dpg.set_value("add_rule_consequent", "")
        dpg.set_value("add_rule_weight", 1.0)
        dpg.set_value("add_rule_priority", 1)
        dpg.configure_item("add_rule_modal", show=True)
    
    def _add_rule(self, sender=None, app_data=None):
        """Добавляет новое правило"""
        try:
            antecedent = dpg.get_value("add_rule_antecedent").strip()
            consequent = dpg.get_value("add_rule_consequent").strip()
            weight = dpg.get_value("add_rule_weight")
            priority = dpg.get_value("add_rule_priority")
            
            if not antecedent or not consequent:
                print("Antecedent и Consequent не могут быть пустыми", file=sys.stderr)
                return
            
            self.rules.append({
                "antecedent": antecedent,
                "consequent": consequent,
                "weight": weight,
                "priority": priority
            })
            
            dpg.configure_item("add_rule_modal", show=False)
            self._render_table()
            print("Правило добавлено (не сохранено в БД)", file=sys.stderr)
        except Exception as e:
            print(f"Ошибка добавления: {e}", file=sys.stderr)
    
    def _edit_rule(self, sender, app_data, user_data):
        """Открывает модалку редактирования"""
        index = user_data
        
        if index is None or not (0 <= index < len(self.rules)):
            print(f"Ошибка: некорректный индекс {index}", file=sys.stderr)
            return
        
        self.editing_rule_index = index
        rule = self.rules[index]
        
        dpg.set_value("edit_rule_antecedent", rule.get("antecedent", ""))
        dpg.set_value("edit_rule_consequent", rule.get("consequent", ""))
        dpg.set_value("edit_rule_weight", float(rule.get("weight", 1.0)))
        dpg.set_value("edit_rule_priority", int(rule.get("priority", 1)))
        dpg.configure_item("edit_rule_modal", show=True)
    
    def _save_edited_rule(self, sender=None, app_data=None):
        """Сохраняет изменения в правиле"""
        try:
            if self.editing_rule_index is None:
                return
            
            antecedent = dpg.get_value("edit_rule_antecedent").strip()
            consequent = dpg.get_value("edit_rule_consequent").strip()
            weight = dpg.get_value("edit_rule_weight")
            priority = dpg.get_value("edit_rule_priority")
            
            if not antecedent or not consequent:
                print("Antecedent и Consequent не могут быть пустыми", file=sys.stderr)
                return
            
            self.rules[self.editing_rule_index] = {
                "antecedent": antecedent,
                "consequent": consequent,
                "weight": weight,
                "priority": priority
            }
            
            dpg.configure_item("edit_rule_modal", show=False)
            self.editing_rule_index = None
            self._render_table()
            print("Правило обновлено (не сохранено в БД)", file=sys.stderr)
        except Exception as e:
            print(f"Ошибка редактирования: {e}", file=sys.stderr)
    
    # ==========================================
    # ✅ НОВЫЕ МЕТОДЫ ДЛЯ УДАЛЕНИЯ
    # ==========================================
    def _show_delete_modal(self, sender, app_data, user_data):
        """Показывает модалку подтверждения удаления"""
        index = user_data
        
        if index is None or not (0 <= index < len(self.rules)):
            print(f"Ошибка: некорректный индекс {index}", file=sys.stderr)
            return
        
        self.deleting_rule_index = index
        rule = self.rules[index]
        
        # Формируем текст правила для превью
        antecedent = rule.get("antecedent", "")
        consequent = rule.get("consequent", "")
        preview_text = f"IF {antecedent} THEN {consequent}"
        
        dpg.set_value("delete_rule_preview", preview_text)
        dpg.configure_item("delete_rule_modal", show=True)
    
    def _confirm_delete_rule(self, sender=None, app_data=None):
        """Подтверждает удаление правила"""
        if self.deleting_rule_index is None:
            return
        
        if not (0 <= self.deleting_rule_index < len(self.rules)):
            print(f"Ошибка: индекс {self.deleting_rule_index} вне диапазона", file=sys.stderr)
            return
        
        removed = self.rules.pop(self.deleting_rule_index)
        self.deleting_rule_index = None
        
        dpg.configure_item("delete_rule_modal", show=False)
        self._render_table()
        
        antecedent = removed.get("antecedent", "")
        print(f"Правило удалено: IF {antecedent} ... (не сохранено в БД)", file=sys.stderr)