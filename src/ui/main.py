import dearpygui.dearpygui as dpg
import sys
import os
from theme import setup_design_system
sys.path.insert(0, os.path.abspath("../../python_pkg"))

def main():
    dpg.create_context()
    with dpg.window(label="Anti-Surge Control System", width=1920, height=1080, pos=(0, 0)):
        dpg.add_text("Система готова к работе. Запустите CMake-сборку ядра.")
    dpg.create_viewport(title="АСУ ТК", width=1920, height=1080)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()

if __name__ == "__main__":
    main()
