# main.py
import argparse
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)


def parse_args():
    """Парсит аргументы командной строки"""
    parser = argparse.ArgumentParser(
        description="Система защиты от помпажа компрессора",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Запуск в тестовом режиме с симулятором данных\n'
             '(без этого флага используется реальное C++ ядро)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Включить режим отладки (подробные логи)'
    )
    return parser.parse_args()


def main():
    args = parse_args()
    
    # Устанавливаем уровень логирования
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("Debug mode enabled")
        print("[1/10] Database initialization...", flush=True)
        from db.init_db import initialize_database
        initialize_database()
        print("[1/10] Database ready", flush=True)
        
        # 2. Создание AppController
        print("[2/10] Creating AppController...", flush=True)
        from controllers.app_controller import AppController
        app_controller = AppController()
        print("[2/10] AppController created", flush=True)
        
        # 3. Инициализация ядра в зависимости от режима
        if args.test:
            print("[3/10] Core initialization (TEST MODE)...", flush=True)
            app_controller.initialize_system(test_mode=True)
            print("[3/10] Core initialized (simulator)", flush=True)
        else:
            print("[3/10] Core initialization (C++ CORE)...", flush=True)
            app_controller.initialize_system(test_mode=False)
            print("[3/10] Core initialized (real)", flush=True)
        
        # 4. Creating AuthController
        print("[4/10] Creating AuthController...", flush=True)
        from controllers.auth_controller import AuthController
        auth_controller = AuthController()
        print("[4/10] AuthController created", flush=True)
        
        # Передаём auth_controller в app_controller
        app_controller.set_auth_controller(auth_controller)
        
        # 5. Инициализация DearPyGUI
        print("[5/10] DearPyGUI initialization...", flush=True)
        import dearpygui.dearpygui as dpg  # ty:ignore[unresolved-import]
        dpg.create_context()
        print("[5/10] DearPyGUI context created", flush=True)
        
        # 6. Создание темы
        print("[6/10] Creating theme...", flush=True)
        from ui.theme import ThemeManager
        theme_manager = ThemeManager()
        theme_manager.initialize()
        palette = theme_manager.get_palette()
        print("[6/10] Theme ready", flush=True)
        
        # 7. Окно авторизации
        print("[7/10] Creating login window...", flush=True)
        from ui.login_window import LoginWindow
        login_window = LoginWindow(palette, auth_controller)
        login_window.create()
        print("[7/10] Login window created", flush=True)
        
        # 8. Viewport
        print("🪟 [8/10] Создание viewport...", flush=True)
        dpg.create_viewport(title='Система защиты от помпажа', width=450, height=350)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        print(" [8/10] Viewport создан", flush=True)
        
        # 9. Ожидание входа
        print("⏳ [9/10] Ожидание входа пользователя...", flush=True)
        while dpg.is_dearpygui_running() and not login_window.is_logged_in():
            dpg.render_dearpygui_frame()
        
        if not login_window.is_logged_in():
            print(" Вход отменён", flush=True)
            dpg.destroy_context()
            return
        
        print(" [9/10] Вход выполнен", flush=True)
        dpg.delete_item("login_window")
        
        # 10. Главное окно
        print(" [10/10] Создание главного окна...", flush=True)
        from ui.main_window import MainWindow
        main_window = MainWindow(palette, app_controller, auth_controller, theme_manager)
        main_window.create()
        print(" [10/10] Главное окно создано", flush=True)
        
        # Устанавливаем ссылки
        app_controller.set_surge_plot(main_window.surge_plot)
        app_controller.set_telemetry_panel(main_window.telemetry_panel)
        
        if args.test:
            # Тестовый режим — запускаем симулятор
            app_controller.start_simulation(interval_ms=100)
            print("Simulation started (test mode)", flush=True)
        else:
            # Реальный режим — запускаем таймер для опроса C++ ядра
            # process_data() будет вызываться каждые 100 мс
            dpg.add_timer(interval=100, callback=app_controller.process_data)
            print("C++ core polling timer started (real mode)", flush=True)
        
        # Обновляем статус в UI
        app_controller.update_status_ui("OK", "READY FOR WORK")
        
        # Обновление viewport
        dpg.set_viewport_title('Система защиты от помпажа v1.0')
        dpg.set_viewport_width(1220)
        dpg.set_viewport_height(850)
        
        # Запуск
        print("Starting render loop...", flush=True)
        dpg.start_dearpygui()
        
        print("Shutting down...", flush=True)
        dpg.destroy_context()
        


if __name__ == "__main__":
    main()