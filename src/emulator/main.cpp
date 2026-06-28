#include "CompressorEmulator.h"
#include "../core/AntiSurgeCore.h"
#include <iostream>
#include <iomanip>
#include <thread>
#include <chrono>
#include <vector>

// ─── Визуализация ASCII-графика (без спецсимволов для Windows) ────────
void printFlowChart(const std::vector<double>& flow_history, int width = 50) {
    if (flow_history.empty()) return;

    double min_val = *std::min_element(flow_history.begin(), flow_history.end());
    double max_val = *std::max_element(flow_history.begin(), flow_history.end());
    double range = max_val - min_val;
    if (range < 1e-6) range = 1.0;

    std::cout << "\n  +-- Flow History ";
    for (int i = 0; i < width - 15; ++i) std::cout << "-";
    std::cout << "+\n";

    // Рисуем 3 ряда (верхний, средний, нижний)
    for (int row = 2; row >= 0; --row) {
        std::cout << "  | ";
        
        // Порог для этого ряда
        double threshold = min_val + (row + 0.5) * range / 3.0;
        
        // Рисуем каждую точку ВРЕМЕНИ (слева направо)
        for (size_t i = 0; i < flow_history.size() && i < static_cast<size_t>(width); ++i) {
            // Если значение в этом временном слоте выше порога — рисуем #
            if (flow_history[i] >= threshold) {
                std::cout << "#";
            } else {
                std::cout << " ";
            }
        }
        
        // Заполняем остаток пробелами
        for (size_t i = flow_history.size(); i < static_cast<size_t>(width); ++i) {
            std::cout << " ";
        }
        
        std::cout << " |\n";
    }

    std::cout << "  +";
    for (int i = 0; i < width; ++i) std::cout << "-";
    std::cout << "+\n";
    
    std::cout << "  Min: " << std::fixed << std::setprecision(1) << min_val 
              << " | Max: " << max_val 
              << " | Current: " << flow_history.back() << " m3/h\n";
}

// ─── Печать состояния системы ────────────────────────────────────────
void printSystemState(const CompressorState& state, const ControlCommand& cmd) {
    std::cout << "\n  +------------------------------------------------+\n";
    std::cout << "  | ANTI-SURGE SYSTEM STATUS                       |\n";
    std::cout << "  +------------------------------------------------+\n";
    std::cout << "  | FLOW:     " << std::setw(6) << std::fixed << std::setprecision(1) 
              << state.flow_rate << " m3/h                           |\n";
    std::cout << "  | PRESS:    " << std::setw(6) << std::setprecision(2) 
              << state.pressure_out << " bar                          |\n";
    std::cout << "  | VALVE:    " << std::setw(6) << std::setprecision(1) 
              << cmd.bypass_valve_position << " % (Command)              |\n";
    std::cout << "  | ALARM:    " << (cmd.alarm_status ? "!!! ON !!!" : "OK      ") 
              << "                                  |\n";
    std::cout << "  +------------------------------------------------+\n";
}

// ─── Главная функция ─────────────────────────────────────────────────
int main() {
    std::cout << "=== COMPRESSOR EMULATOR & CORE INTEGRATION TEST ===\n\n";

    // 1. Создаем объекты
    CompressorEmulator emulator;
    AntiSurgeCore core;

    // 2. Инициализируем их
    emulator.initialize(TestScenario::SurgeEvent); // Тестируем приближение к помпажу
    core.initialize(""); // Пустая строка = настройки по умолчанию

    std::cout << "[OK] Emulator initialized.\n";
    std::cout << "[OK] AntiSurgeCore initialized.\n\n";

    std::vector<double> flow_history;
    const double dt = 0.1; // Шаг времени 0.1 сек
    int iteration = 0;
    const int max_iterations = 150;

    // ГЛАВНЫЙ ЦИКЛ
    while (iteration < max_iterations) {
        
        // ---------------------------------------------------------
        // ШАГ 1: Эмулятор обновляет физику компрессора
        // ---------------------------------------------------------
        emulator.update(dt);

        // ---------------------------------------------------------
        // ШАГ 2: ЭМУЛЯТОР -> ЯДРО (Передача данных)
        // ---------------------------------------------------------
        // Мы берем "грязные" данные с датчиков эмулятора
        SensorData sensor_data = emulator.getSensorData();

        // *** ОТЛАДКА: Видим, что отправляем в ядро ***
        std::cout << ">>> [EMULATOR -> CORE] Sending Flow=" << sensor_data.flow_rate 
                  << ", P_out=" << sensor_data.pressure_out << "\n";

        // ---------------------------------------------------------
        // ШАГ 3: ЯДРО ОБРАБАТЫВАЕТ ДАННЫЕ
        // ---------------------------------------------------------
        // Ядро фильтрует шум, считает нечеткую логику и решает, что делать
        ControlCommand command = core.processSensorData(sensor_data);

        // *** ОТЛАДКА: Видим, что ядро решило ***
        std::cout << "<<< [CORE -> EMULATOR] Command: Valve=" << command.bypass_valve_position 
                  << "%, Alarm=" << (command.alarm_status ? "YES" : "NO") << "\n";

        // ---------------------------------------------------------
        // ШАГ 4: ЯДРО -> ЭМУЛЯТОР (Применение команды)
        // ---------------------------------------------------------
        // Эмулятор меняет положение клапана на основе команды ядра
        emulator.applyControl(command);

        // Сохраняем историю для графика
        flow_history.push_back(emulator.getState().flow_rate);
        if (flow_history.size() > 50) flow_history.erase(flow_history.begin());

        // Вывод состояния на экран каждые 10 шагов (1 секунда)
        if (iteration % 10 == 0) {
            std::cout << "\033[2J\033[H"; // Очистка экрана
            CompressorState state = emulator.getState();
            printSystemState(state, command);
            printFlowChart(flow_history);
            
            std::cout << "  Time: " << iteration * dt << "s | Iter: " << iteration << "\n";
        }

        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        iteration++;
    }

    std::cout << "\n=== SIMULATION FINISHED ===\n";
    return 0;
}