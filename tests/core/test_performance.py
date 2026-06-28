# tests/core/test_performance.py
import sys
import os
import time
import statistics

# ✅ Добавляем путь к src/ в sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
from core.mock_engine import CoreBridge
from dto.dto import SensorData

def benchmark_core(iterations=1000):
    """Замеряет производительность ядра"""
    bridge = CoreBridge()
    bridge.init_py()
    
    # Тестовые данные
    test_data = [
        SensorData(Q=65.0, P_in=5.0, P_out=8.0, T=25.0),
        SensorData(Q=45.0, P_in=4.5, P_out=7.5, T=26.0),
        SensorData(Q=30.0, P_in=4.0, P_out=7.0, T=27.0),
    ]
    
    times = []
    
    print(f"Запуск теста: {iterations} итераций...")
    start_total = time.perf_counter()
    
    for i in range(iterations):
        data = test_data[i % len(test_data)]
        
        start = time.perf_counter()
        result = bridge.process_sensor_data(
            Q=data.Q, P_in=data.P_in, P_out=data.P_out, T=data.T
        )
        end = time.perf_counter()
        
        times.append((end - start) * 1000.0)  # В миллисекундах
    
    total_time = time.perf_counter() - start_total
    
    # Статистика
    avg_time = statistics.mean(times)
    median_time = statistics.median(times)
    min_time = min(times)
    max_time = max(times)
    std_dev = statistics.stdev(times) if len(times) > 1 else 0
    p95 = sorted(times)[int(len(times) * 0.95)]
    p99 = sorted(times)[int(len(times) * 0.99)]
    
    print("\n" + "="*60)
    print("РЕЗУЛЬТАТЫ ТЕСТА ПРОИЗВОДИТЕЛЬНОСТИ")
    print("="*60)
    print(f"Всего итераций:      {iterations}")
    print(f"Общее время:         {total_time:.2f} с")
    print(f"Среднее время:       {avg_time:.3f} мс")
    print(f"Медиана:             {median_time:.3f} мс")
    print(f"Минимум:             {min_time:.3f} мс")
    print(f"Максимум:            {max_time:.3f} мс")
    print(f"Стандартное откл.:   {std_dev:.3f} мс")
    print(f"95-й перцентиль:     {p95:.3f} мс")
    print(f"99-й перцентиль:     {p99:.3f} мс")
    print(f"Требование (≤10 мс): {'✅ ВЫПОЛНЕНО' if p99 < 10 else '❌ НЕ ВЫПОЛНЕНО'}")
    print("="*60)
    
    # Сохраняем результаты в JSON
    import json
    results = {
        "iterations": iterations,
        "total_time_s": total_time,
        "avg_time_ms": avg_time,
        "median_time_ms": median_time,
        "min_time_ms": min_time,
        "max_time_ms": max_time,
        "std_dev_ms": std_dev,
        "p95_ms": p95,
        "p99_ms": p99,
        "requirement_met": p99 < 10
    }
    
    with open("performance_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print("\nРезультаты сохранены в performance_results.json")
    
    return results

if __name__ == "__main__":
    benchmark_core(iterations=10000)