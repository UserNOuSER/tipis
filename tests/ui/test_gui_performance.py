# tests/ui/test_gui_performance.py
import sys
import os
import time
import statistics

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

import dearpygui.dearpygui as dpg  # ty:ignore[unresolved-import]


def benchmark_gui(duration_sec=10):
    """Замеряет FPS DearPyGUI в течение duration_sec секунд"""
    
    dpg.create_context()
    
    # Создаём тестовое окно с графиком (нагрузка как в реальном приложении)
    with dpg.window(label="Test", tag="test_window", width=800, height=600):
        with dpg.plot(label="Test Plot", width=-1, height=-1, tag="test_plot"):
            dpg.add_plot_axis(dpg.mvXAxis, tag="x_axis")
            dpg.add_plot_axis(dpg.mvYAxis, tag="y_axis")
            dpg.add_line_series([0, 1], [0, 1], tag="test_line", parent="y_axis")
        
        dpg.add_text("FPS: --", tag="fps_text")
    
    dpg.create_viewport(title='FPS Test', width=800, height=600)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    
    # Собираем данные о FPS
    frame_times = []
    start_time = time.perf_counter()
    last_time = start_time
    frame_count = 0
    
    print(f"Запуск теста на {duration_sec} секунд...")
    
    while dpg.is_dearpygui_running():
        dpg.render_dearpygui_frame()
        
        current_time = time.perf_counter()
        frame_time = current_time - last_time
        frame_times.append(frame_time)
        last_time = current_time
        frame_count += 1
        
        # Обновляем данные графика (эмуляция нагрузки)
        import random
        x = list(range(100))
        y = [random.uniform(0, 100) for _ in range(100)]
        dpg.set_value("test_line", [x, y])
        
        # Проверяем, не истекло ли время теста
        if current_time - start_time >= duration_sec:
            break
    
    dpg.destroy_context()
    
    # Статистика
    fps_values = [1.0 / t for t in frame_times if t > 0]
    
    avg_fps = statistics.mean(fps_values)
    median_fps = statistics.median(fps_values)
    min_fps = min(fps_values)
    max_fps = max(fps_values)
    p5_fps = sorted(fps_values)[int(len(fps_values) * 0.05)]
    p95_fps = sorted(fps_values)[int(len(fps_values) * 0.95)]
    
    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТЫ ТЕСТА GUI PERFORMANCE")
    print("=" * 60)
    print(f"Длительность теста:     {duration_sec} с")
    print(f"Всего кадров:           {frame_count}")
    print(f"Средний FPS:            {avg_fps:.1f}")
    print(f"Медианный FPS:          {median_fps:.1f}")
    print(f"Минимальный FPS:        {min_fps:.1f}")
    print(f"Максимальный FPS:       {max_fps:.1f}")
    print(f"5-й перцентиль (худший): {p5_fps:.1f}")
    print(f"95-й перцентиль (лучший): {p95_fps:.1f}")
    print(f"Требование (>=30 FPS):  {'✅ ВЫПОЛНЕНО' if p5_fps >= 30 else '❌ НЕ ВЫПОЛНЕНО'}")
    print("=" * 60)
    
    # Сохраняем результаты
    import json
    results = {
        "duration_sec": duration_sec,
        "total_frames": frame_count,
        "avg_fps": avg_fps,
        "median_fps": median_fps,
        "min_fps": min_fps,
        "max_fps": max_fps,
        "p5_fps": p5_fps,
        "p95_fps": p95_fps,
        "requirement_met": p5_fps >= 30
    }
    
    with open("gui_performance_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\nРезультаты сохранены в gui_performance_results.json")
    
    return results


if __name__ == "__main__":
    benchmark_gui(duration_sec=10)