import sys
import os
import traceback

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    import dearpygui.dearpygui as dpg  # ty:ignore[unresolved-import]
    from ui.theme import theme_manager  # <-- Импортируем глобальный экземпляр
    from db.init_db import initialize_database
    from controllers.app_controller import AppController
    from ui.main_window import MainWindow
    from core.mock_engine import AntiSurgeCore
except Exception as e:
    print(f"❌ Ошибка импорта: {e}", file=sys.stderr)
    traceback.print_exc()
    sys.exit(1)

def main():
    try:
        print("🔌 Инициализация базы данных...", file=sys.stderr)
        initialize_database()
        
        print("⚙️ Инициализация ядра...", file=sys.stderr)
        core = AntiSurgeCore()
        core.initialize("mock_config.ini")
        
        print("🎨 Создание GUI...", file=sys.stderr)
        dpg.create_context()
        
        # Инициализируем глобальный менеджер тем
        theme_manager.initialize()
        palette = theme_manager.get_palette()
        
        # Создаем контроллер и передаем ему ядро
        controller = AppController()
        
        # Передаем theme_manager в MainWindow
        main_window = MainWindow(palette, controller, theme_manager)
        main_window.create()
        
        # Инициализируем систему
        controller.initialize_system()
        
        print("✅ Запуск цикла отрисовки...", file=sys.stderr)
        dpg.start_dearpygui()
        dpg.destroy_context()
        
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()