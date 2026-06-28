import dearpygui.dearpygui as dpg  # ty:ignore[unresolved-import]
import sys


class LoginWindow:
    """Окно авторизации пользователя"""
    
    def __init__(self, palette, auth_controller):
        self.palette = palette
        self.auth_controller = auth_controller
        self.login_success = False
    
    def create(self):
        """Создаёт окно авторизации"""
        with dpg.window(
            label="Авторизация",
            tag="login_window",
            show=True,
            width=450,
            height=350,
            no_close=True,
            no_collapse=True,
            no_move=True,
            no_resize=True,
            no_title_bar=False
        ):            
            # Заголовок
            dpg.add_text("СИСТЕМА ЗАЩИТЫ ОТ ПОМПАЖА", 
                        color=self.palette.primary + (255,))
            dpg.add_text("Вход в систему", 
                        color=self.palette.text_primary + (255,))
            dpg.add_separator()
            dpg.add_spacer(height=15)
            
            # Поля ввода
            dpg.add_text("Логин:")
            dpg.add_input_text(
                tag="login_username",
                width=-1,
                hint="Введите логин",
                default_value=""
            )
            
            dpg.add_spacer(height=10)
            
            dpg.add_text("Пароль:")
            dpg.add_input_text(
                tag="login_password",
                password=True,
                width=-1,
                hint="Введите пароль",
                default_value=""
            )
            
            dpg.add_spacer(height=15)
            
            # Сообщение об ошибке
            dpg.add_text("", tag="login_error", 
                        color=self.palette.error + (255,))
            
            
            # Кнопка входа
            dpg.add_button(
                label="Войти",
                callback=self._on_login,
                width=-1,
                height=40
            )
            
            dpg.add_spacer(height=10)
            
            # Подсказка
            dpg.add_text("Первый запуск? Создайте администратора в консоли.",
                        color=self.palette.text_disabled + (255,))
    
    def _on_login(self, sender=None, app_data=None):
        """Обработчик кнопки входа"""
        username = dpg.get_value("login_username").strip()
        password = dpg.get_value("login_password")
        
        if not username or not password:
            dpg.set_value("login_error", "Заполните все поля")
            return
        
        if self.auth_controller.login(username, password):
            self.login_success = True
            dpg.configure_item("login_window", show=False)
            print(f"✅ Вход выполнен: {username}", file=sys.stderr)
        else:
            dpg.set_value("login_error", "Неверный логин или пароль")
            dpg.set_value("login_password", "")
    
    def is_logged_in(self) -> bool:
        """Возвращает True, если пользователь успешно авторизован"""
        return self.login_success