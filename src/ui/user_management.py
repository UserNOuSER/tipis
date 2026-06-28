import dearpygui.dearpygui as dpg  # ty:ignore[unresolved-import]
from datetime import datetime
import sys

class UserManagementWindow:
    """Окно управления пользователями системы"""
    
    # Цвета для ролей
    ROLE_COLORS = {
        "ADMIN": (239, 68, 68),      # Красный
        "ENGINEER": (14, 165, 233),  # Синий
        "OPERATOR": (16, 185, 129),  # Зелёный
    }
    
    def __init__(self, palette, controller):
        self.palette = palette
        self.controller = controller
        self.users = []
        self.selected_user_id = None
        
        # Фиксированные размеры
        self.window_height = 700
        self.window_width = 1000
        self.table_height = 450
        
    def create(self):
        """Создаёт окно управления пользователями"""
        with dpg.window(
            label="Управление пользователями",
            tag="user_management_window",
            show=False,
            width=self.window_width,
            height=self.window_height,
            no_scrollbar=True,
            no_collapse=True
        ):
            # ВЕРХ: Заголовок
            dpg.add_text("УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ СИСТЕМЫ АПЗ", 
                        color=self.palette.primary + (255,))
            dpg.add_separator()
            dpg.add_spacer(height=10)
            
            # ПАНЕЛЬ ДЕЙСТВИЙ
            with dpg.group(horizontal=True):
                dpg.add_button(label="[+] Добавить пользователя", 
                              callback=self._show_add_dialog, width=200)
                dpg.add_button(label="[Ред] Редактировать", 
                              callback=self._show_edit_dialog, width=170)
                dpg.add_button(label="[Ключ] Сбросить пароль", 
                              callback=self._show_reset_password_dialog, width=200)
                dpg.add_button(label="[Обн] Обновить список", 
                              callback=self._load_users, width=170)
                
                dpg.add_spacer(width=30)
                dpg.add_text("Всего: 0", tag="user_count", 
                            color=self.palette.text_primary + (255,))
            
            dpg.add_spacer(height=10)
            
            # ТАБЛИЦА ПОЛЬЗОВАТЕЛЕЙ
            with dpg.child_window(
                height=self.table_height,
                tag="user_table_container",
                border=True
            ):
                with dpg.table(
                    header_row=True,
                    borders_innerH=True, borders_outerH=True,
                    borders_innerV=True, borders_outerV=True,
                    height=-1,
                    tag="user_table"
                ):
                    dpg.add_table_column(label="ID", width_fixed=True, init_width_or_weight=50)
                    dpg.add_table_column(label="Имя пользователя", width_fixed=True, init_width_or_weight=200)
                    dpg.add_table_column(label="Роль", width_fixed=True, init_width_or_weight=120)
                    dpg.add_table_column(label="Статус", width_fixed=True, init_width_or_weight=100)
                    dpg.add_table_column(label="Действия", width_fixed=True, init_width_or_weight=250)
            
            dpg.add_spacer(height=10)
            
            # НИЗ: Кнопки закрытия
            with dpg.group(horizontal=True):
                dpg.add_button(label="[X] Закрыть", 
                              callback=lambda: dpg.configure_item("user_management_window", show=False), 
                              width=100)
        
        # === МОДАЛЬНЫЕ ОКНА ===
        self._create_add_user_modal()
        self._create_edit_user_modal()
        self._create_reset_password_modal()
        self._create_delete_confirm_modal()
        
        # Загружаем пользователей
        self._load_users()
    
    def _create_add_user_modal(self):
        """Создаёт модальное окно добавления пользователя"""
        with dpg.window(
            label="Добавить пользователя",
            tag="add_user_modal",
            show=False,
            modal=True,
            no_move=True,
            width=400,
            height=300
        ):
            dpg.add_text("Имя пользователя:")
            dpg.add_input_text(tag="new_username", width=-1)
            
            dpg.add_spacer(height=10)
            dpg.add_text("Пароль:")
            dpg.add_input_text(tag="new_password", password=True, width=-1)
            
            dpg.add_spacer(height=10)
            dpg.add_text("Подтвердите пароль:")
            dpg.add_input_text(tag="new_password_confirm", password=True, width=-1)
            
            dpg.add_spacer(height=10)
            dpg.add_text("Роль:")
            dpg.add_combo(
                ["OPERATOR", "ENGINEER", "ADMIN"],
                default_value="OPERATOR",
                tag="new_user_role",
                width=-1
            )
            
            dpg.add_spacer(height=15)
            with dpg.group(horizontal=True):
                dpg.add_button(label="[OK] Создать", callback=self._create_user, width=150)
                dpg.add_button(label="[X] Отмена", 
                              callback=lambda: dpg.configure_item("add_user_modal", show=False), 
                              width=150)
    
    def _create_edit_user_modal(self):
        """Создаёт модальное окно редактирования пользователя"""
        with dpg.window(
            label="Редактировать пользователя",
            tag="edit_user_modal",
            show=False,
            modal=True,
            no_move=True,
            width=400,
            height=250
        ):
            dpg.add_text("ID пользователя:", tag="edit_user_id_text")
            dpg.add_spacer(height=10)
            
            dpg.add_text("Имя пользователя:")
            dpg.add_input_text(tag="edit_username", width=-1)
            
            dpg.add_spacer(height=10)
            dpg.add_text("Роль:")
            dpg.add_combo(
                ["OPERATOR", "ENGINEER", "ADMIN"],
                default_value="OPERATOR",
                tag="edit_user_role",
                width=-1
            )
            
            dpg.add_spacer(height=10)
            dpg.add_text("Статус:")
            dpg.add_checkbox(label="Активен", tag="edit_user_active", default_value=True)
            
            dpg.add_spacer(height=15)
            with dpg.group(horizontal=True):
                dpg.add_button(label="[Сохранить]", callback=self._update_user, width=130)
                dpg.add_button(label="[Удалить]", callback=self._show_delete_confirm, width=130)
                dpg.add_button(label="[X] Отмена", 
                              callback=lambda: dpg.configure_item("edit_user_modal", show=False), 
                              width=130)
    
    def _create_reset_password_modal(self):
        """Создаёт модальное окно сброса пароля"""
        with dpg.window(
            label="Сброс пароля",
            tag="reset_password_modal",
            show=False,
            modal=True,
            no_move=True,
            width=400,
            height=200
        ):
            dpg.add_text("Новый пароль:")
            dpg.add_input_text(tag="reset_password", password=True, width=-1)
            
            dpg.add_spacer(height=10)
            dpg.add_text("Подтвердите пароль:")
            dpg.add_input_text(tag="reset_password_confirm", password=True, width=-1)
            
            dpg.add_spacer(height=15)
            with dpg.group(horizontal=True):
                dpg.add_button(label="[Ключ] Сбросить", callback=self._reset_password, width=150)
                dpg.add_button(label="[X] Отмена", 
                              callback=lambda: dpg.configure_item("reset_password_modal", show=False), 
                              width=150)
    
    def _create_delete_confirm_modal(self):
        """Создаёт модальное окно подтверждения удаления"""
        with dpg.window(
            label="Подтверждение удаления",
            tag="delete_confirm_modal",
            show=False,
            modal=True,
            no_move=True,
            width=400,
            height=150
        ):
            dpg.add_text("Вы уверены, что хотите удалить пользователя?", 
                        color=self.palette.error + (255,))
            dpg.add_text("Это действие нельзя отменить!", 
                        color=self.palette.warning + (255,))
            
            dpg.add_spacer(height=15)
            with dpg.group(horizontal=True):
                dpg.add_button(label="[Удалить]", callback=self._delete_user, width=150)
                dpg.add_button(label="[X] Отмена", 
                              callback=lambda: dpg.configure_item("delete_confirm_modal", show=False), 
                              width=150)
    
    def _load_users(self, sender=None, app_data=None):
        """Загружает список пользователей"""
        try:
            self.users = self.controller.get_all_users()
            self._render_table()
        except Exception as e:
            print(f"Ошибка загрузки пользователей: {e}", file=sys.stderr)
    
    def _render_table(self):
        """Отрисовывает таблицу пользователей"""
        # Удаляем старые строки
        if dpg.does_item_exist("user_table"):
            children = dpg.get_item_children("user_table", slot=1)
            for child in children:
                dpg.delete_item(child)
        
        # Добавляем пользователей
        for user in self.users:
            # Цвет роли
            role_color = self.ROLE_COLORS.get(user["role"], (100, 116, 139))
            
            # Статус
            status_text = "Активен" if user["is_active"] else "Заблокирован"
            status_color = self.palette.success if user["is_active"] else self.palette.error
            
            with dpg.table_row(parent="user_table"):
                dpg.add_text(str(user["user_id"]))
                dpg.add_text(user["username"])
                dpg.add_text(user["role"], color=role_color + (255,))
                dpg.add_text(status_text, color=status_color + (255,))
                
                # Кнопки действий (текстовые, без эмодзи)
                with dpg.group(horizontal=True):
                    dpg.add_button(
                        label="[Ред]",
                        callback=lambda s, a, u=user: self._open_edit_modal(u),
                        width=50, height=25
                    )
                    dpg.add_button(
                        label="[Ключ]",
                        callback=lambda s, a, u=user: self._open_reset_modal(u),
                        width=60, height=25
                    )
                    dpg.add_button(
                        label="[Удал]",
                        callback=lambda s, a, u=user: self._open_delete_modal(u),
                        width=60, height=25
                    )
        
        # Обновляем счётчик
        if dpg.does_item_exist("user_count"):
            dpg.set_value("user_count", f"Всего: {len(self.users)}")
    
    def _show_add_dialog(self, sender=None, app_data=None):
        """Показывает диалог добавления пользователя"""
        dpg.set_value("new_username", "")
        dpg.set_value("new_password", "")
        dpg.set_value("new_password_confirm", "")
        dpg.set_value("new_user_role", "OPERATOR")
        dpg.configure_item("add_user_modal", show=True)
    
    def _create_user(self, sender=None, app_data=None):
        """Создаёт нового пользователя"""
        try:
            username = dpg.get_value("new_username").strip()
            password = dpg.get_value("new_password")
            password_confirm = dpg.get_value("new_password_confirm")
            role = dpg.get_value("new_user_role")
            
            # Валидация
            if not username:
                print("Имя пользователя не может быть пустым", file=sys.stderr)
                return
            
            if len(password) < 4:
                print("Пароль должен быть не менее 4 символов", file=sys.stderr)
                return
            
            if password != password_confirm:
                print("Пароли не совпадают", file=sys.stderr)
                return
            
            # Создаём пользователя
            if self.controller.create_user(username, password, role):
                dpg.configure_item("add_user_modal", show=False)
                self._load_users()
                print(f"Пользователь {username} создан", file=sys.stderr)
            else:
                print("Ошибка создания пользователя", file=sys.stderr)
        except Exception as e:
            print(f"Ошибка: {e}", file=sys.stderr)
    
    def _show_edit_dialog(self, sender=None, app_data=None):
        """Показывает диалог редактирования (если выбран пользователь)"""
        if self.selected_user_id is None:
            print("Выберите пользователя для редактирования", file=sys.stderr)
            return
        user = next((u for u in self.users if u["user_id"] == self.selected_user_id), None)
        if user:
            self._open_edit_modal(user)
    
    def _open_edit_modal(self, user):
        """Открывает модальное окно редактирования для конкретного пользователя"""
        self.selected_user_id = user["user_id"]
        dpg.set_value("edit_user_id_text", f"ID: {user['user_id']}")
        dpg.set_value("edit_username", user["username"])
        dpg.set_value("edit_user_role", user["role"])
        dpg.set_value("edit_user_active", user["is_active"])
        dpg.configure_item("edit_user_modal", show=True)
    
    def _update_user(self, sender=None, app_data=None):
        """Обновляет данные пользователя"""
        try:
            if self.selected_user_id is None:
                return
            
            username = dpg.get_value("edit_username").strip()
            role = dpg.get_value("edit_user_role")
            is_active = dpg.get_value("edit_user_active")
            
            if not username:
                print("Имя пользователя не может быть пустым", file=sys.stderr)
                return
            
            if self.controller.update_user(self.selected_user_id, username, role, is_active):
                dpg.configure_item("edit_user_modal", show=False)
                self._load_users()
                print("Пользователь обновлён", file=sys.stderr)
            else:
                print("Ошибка обновления пользователя", file=sys.stderr)
        except Exception as e:
            print(f"Ошибка: {e}", file=sys.stderr)
    
    def _show_reset_password_dialog(self, sender=None, app_data=None):
        """Показывает диалог сброса пароля"""
        if self.selected_user_id is None:
            print("Выберите пользователя для сброса пароля", file=sys.stderr)
            return
        dpg.set_value("reset_password", "")
        dpg.set_value("reset_password_confirm", "")
        dpg.configure_item("reset_password_modal", show=True)
    
    def _open_reset_modal(self, user):
        """Открывает модальное окно сброса пароля"""
        self.selected_user_id = user["user_id"]
        dpg.set_value("reset_password", "")
        dpg.set_value("reset_password_confirm", "")
        dpg.configure_item("reset_password_modal", show=True)
    
    def _reset_password(self, sender=None, app_data=None):
        """Сбрасывает пароль пользователя"""
        try:
            if self.selected_user_id is None:
                return
            
            password = dpg.get_value("reset_password")
            password_confirm = dpg.get_value("reset_password_confirm")
            
            if len(password) < 4:
                print("Пароль должен быть не менее 4 символов", file=sys.stderr)
                return
            
            if password != password_confirm:
                print("Пароли не совпадают", file=sys.stderr)
                return
            
            if self.controller.reset_password(self.selected_user_id, password):
                dpg.configure_item("reset_password_modal", show=False)
                print("Пароль сброшен", file=sys.stderr)
            else:
                print("Ошибка сброса пароля", file=sys.stderr)
        except Exception as e:
            print(f"Ошибка: {e}", file=sys.stderr)
    
    def _open_delete_modal(self, user):
        """Открывает модальное окно подтверждения удаления"""
        self.selected_user_id = user["user_id"]
        dpg.configure_item("delete_confirm_modal", show=True)
    
    def _show_delete_confirm(self, sender=None, app_data=None):
        """Показывает диалог подтверждения удаления"""
        dpg.configure_item("edit_user_modal", show=False)
        dpg.configure_item("delete_confirm_modal", show=True)
    
    def _delete_user(self, sender=None, app_data=None):
        """Удаляет пользователя"""
        try:
            if self.selected_user_id is None:
                return
            
            if self.controller.delete_user(self.selected_user_id):
                dpg.configure_item("delete_confirm_modal", show=False)
                dpg.configure_item("edit_user_modal", show=False)
                self.selected_user_id = None
                self._load_users()
                print("Пользователь удалён", file=sys.stderr)
            else:
                print("Ошибка удаления пользователя", file=sys.stderr)
        except Exception as e:
            print(f"Ошибка: {e}", file=sys.stderr)
    
    def show(self):
        """Показывает окно управления пользователями"""
        self._load_users()
        dpg.configure_item("user_management_window", show=True)