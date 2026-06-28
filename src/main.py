# main.py
import sys
import logging
import traceback

logging.basicConfig(
    level=logging.DEBUG,  # ✅ Было INFO, стало DEBUG
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)


def main():
    try:
        # 1. Инициализация БД
        print("🔌 [1/10] Инициализация базы данных...", flush=True)
        from db.init_db import initialize_database
        initialize_database()
        print("✅ [1/10] БД готова", flush=True)
        
        # 2. Создание AppController
        print("⚙️ [2/10] Создание AppController...", flush=True)
        from controllers.app_controller import AppController
        app_controller = AppController()
        print("✅ [2/10] AppController создан", flush=True)
        
        # 3. Инициализация системы
        print("⚙️ [3/10] Инициализация ядра...", flush=True)
        app_controller.initialize_system()
        print("✅ [3/10] Ядро инициализировано", flush=True)
        
        # 4. Создание AuthController
        print("🔐 [4/10] Создание AuthController...", flush=True)
        from controllers.auth_controller import AuthController
        auth_controller = AuthController()
        print("✅ [4/10] AuthController создан", flush=True)
        
        # 5. Инициализация DearPyGUI (ДО ThemeManager!)
        print("🖥️ [5/10] Инициализация DearPyGUI...", flush=True)
        import dearpygui.dearpygui as dpg  # ty:ignore[unresolved-import]
        dpg.create_context()
        print("✅ [5/10] Контекст DearPyGUI создан", flush=True)
        
        # 6. Создание и инициализация темы (ПОСЛЕ create_context!)
        print("🎨 [6/10] Создание темы...", flush=True)
        from ui.theme import ThemeManager
        theme_manager = ThemeManager()
        theme_manager.initialize()  # ✅ ВАЖНО: инициализируем темы!
        palette = theme_manager.get_palette()
        print("✅ [6/10] Тема готова", flush=True)
        
        # 7. Окно авторизации
        print("🔐 [7/10] Создание окна авторизации...", flush=True)
        from ui.login_window import LoginWindow
        login_window = LoginWindow(palette, auth_controller)
        login_window.create()
        print("✅ [7/10] Окно авторизации создано", flush=True)
        
        # 8. Viewport
        print("🪟 [8/10] Создание viewport...", flush=True)
        dpg.create_viewport(title='Система защиты от помпажа', width=450, height=350)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        print("✅ [8/10] Viewport создан", flush=True)
        
        # 9. Ожидание входа
        print("⏳ [9/10] Ожидание входа пользователя...", flush=True)
        while dpg.is_dearpygui_running() and not login_window.is_logged_in():
            dpg.render_dearpygui_frame()
        
        if not login_window.is_logged_in():
            print("❌ Вход отменён", flush=True)
            dpg.destroy_context()
            return
        
        print("✅ [9/10] Вход выполнен", flush=True)
        dpg.delete_item("login_window")
        
        # 10. Главное окно
        print("🏠 [10/10] Создание главного окна...", flush=True)
        from ui.main_window import MainWindow
        main_window = MainWindow(palette, app_controller, auth_controller, theme_manager) 
        main_window.create()
        print("✅ [10/10] Главное окно создано", flush=True)
        
        # Устанавливаем ссылки и запускаем симуляцию ПОСЛЕ создания UI
        app_controller.set_surge_plot(main_window.surge_plot)
        app_controller.set_telemetry_panel(main_window.telemetry_panel)
        app_controller.start_simulation(interval_ms=100)
        
        # Обновляем статус в UI
        app_controller.update_status_ui("OK", "✅ ГОТОВ К РАБОТЕ")
        
        # Обновление viewport
        dpg.set_viewport_title('Система защиты от помпажа v1.0')
        dpg.set_viewport_width(1220)
        dpg.set_viewport_height(850)
        
        # Запуск
        print("✅ Запуск цикла отрисовки...", flush=True)
        dpg.start_dearpygui()
        
        print("👋 Завершение работы...", flush=True)
        dpg.destroy_context()
        
    except Exception as e:
        logger.error(f"💥 Критическая ошибка: {e}", exc_info=True)
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()