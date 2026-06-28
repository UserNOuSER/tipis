#include "CompressorEmulator.h"
#include <cmath>
#include <random>
#include <algorithm>
#include <iostream>

// ═══════════════════════════════════════════════════════════════════════
//  Конструктор / Деструктор
// ═══════════════════════════════════════════════════════════════════════

CompressorEmulator::CompressorEmulator() 
    : current_scenario_(TestScenario::NormalOperation) {
    stats_.min_flow = 1e9;
    stats_.max_flow = -1e9;
}

CompressorEmulator::~CompressorEmulator() {}

// ═══════════════════════════════════════════════════════════════════════
//  Инициализация
// ═══════════════════════════════════════════════════════════════════════

bool CompressorEmulator::initialize(TestScenario scenario) {
    current_scenario_ = scenario;
    simulation_time_ = 0.0;
    
    // Начальное состояние
    state_.flow_rate = 50.0;
    state_.pressure_in = 1.0;
    state_.pressure_out = 2.0;
    state_.temperature = 25.0;
    state_.rpm = 3000.0;
    state_.bypass_valve = 0.0;
    state_.surge_margin = 100.0;
    state_.target_flow = 50.0;
    state_.inertia = 0.8;
    state_.surge_active = false;
    state_.surge_phase = 0.0;

    std::cout << "[Emulator] Initialized with scenario: " << getScenarioName() << std::endl;
    return true;
}

// ═══════════════════════════════════════════════════════════════════════
//  Обновление состояния
// ═══════════════════════════════════════════════════════════════════════

void CompressorEmulator::update(double dt) {
    simulation_time_ += dt;

    // Выполняем сценарий
    switch (current_scenario_) {
        case TestScenario::NormalOperation:
            executeNormalScenario(dt);
            break;
        case TestScenario::ApproachingSurge:
            executeApproachingSurgeScenario(dt);
            break;
        case TestScenario::SurgeEvent:
            executeSurgeScenario(dt);
            break;
        case TestScenario::ValveResponse:
            executeValveResponseScenario(dt);
            break;
        case TestScenario::SensorNoise:
            executeSensorNoiseScenario(dt);
            break;
        default:
            executeNormalScenario(dt);
    }

    // Моделирование помпажа (если активен)
    if (state_.surge_active) {
        simulateSurge(dt);
    }

    // Расчёт давления на выходе
    double pressure_ratio = state_.pressure_out / state_.pressure_in;
    state_.pressure_out = calculatePressureOut(state_.flow_rate, state_.rpm);

    // Расчёт температуры
    state_.temperature = calculateTemperature(state_.flow_rate, pressure_ratio);

    // Расчёт запаса по помпажу
    double surge_threshold = 15.0;  // минимальный безопасный расход
    state_.surge_margin = ((state_.flow_rate - surge_threshold) / surge_threshold) * 100.0;
    state_.surge_margin = std::max(0.0, std::min(state_.surge_margin, 200.0));

    // Обновление статистики
    updateStatistics();
}

// ═══════════════════════════════════════════════════════════════════════
//  Физическая модель
// ═══════════════════════════════════════════════════════════════════════

double CompressorEmulator::calculateFlowRate(double valve_position, double rpm, double pressure_ratio) {
    // Базовый расход зависит от оборотов
    double base_flow = (rpm / 3000.0) * 60.0;  // 60 м³/ч при 3000 об/мин

    // Клапан рециркуляции уменьшает полезный расход
    double valve_factor = 1.0 - (valve_position / 100.0) * 0.5;  // до 50% рециркуляции

    // Давление влияет на расход (чем выше перепад, тем меньше расход)
    double pressure_factor = 1.0 / std::max(1.0, pressure_ratio * 0.8);

    double flow = base_flow * valve_factor * pressure_factor;

    // Инерционность (плавный переход)
    flow = state_.inertia * state_.flow_rate + (1.0 - state_.inertia) * flow;

    return flow;
}

double CompressorEmulator::calculatePressureOut(double flow_rate, double rpm) {
    // Давление на выходе зависит от расхода и оборотов
    double base_pressure = 1.0;  // базовое давление (бар)
    
    // Чем меньше расход, тем выше давление (характеристика компрессора)
    double flow_factor = 1.0 + (60.0 - flow_rate) / 60.0 * 0.5;
    
    // Обороты увеличивают давление
    double rpm_factor = rpm / 3000.0;

    double pressure = base_pressure * flow_factor * rpm_factor;

    return pressure;
}

double CompressorEmulator::calculateTemperature(double flow_rate, double pressure_ratio) {
    // Температура зависит от степени сжатия и расхода
    double base_temp = 25.0;  // базовая температура (°C)
    
    // Сжатие нагревает газ
    double compression_heating = (pressure_ratio - 1.0) * 30.0;
    
    // Меньший расход = больший нагрев
    double flow_factor = 60.0 / std::max(10.0, flow_rate);

    double temp = base_temp + compression_heating * flow_factor;

    return temp;
}

void CompressorEmulator::simulateSurge(double dt) {
    // Помпаж — это колебания расхода и давления
    state_.surge_phase += dt * 5.0;  // частота колебаний

    // Резкое падение расхода
    double surge_amplitude = 30.0;  // амплитуда падения расхода
    double flow_drop = surge_amplitude * std::sin(state_.surge_phase);
    
    state_.flow_rate = state_.target_flow - surge_amplitude + flow_drop;
    state_.flow_rate = std::max(5.0, state_.flow_rate);  // минимум 5 м³/ч

    // Колебания давления
    double pressure_oscillation = 0.5 * std::sin(state_.surge_phase * 1.3);
    state_.pressure_out += pressure_oscillation;
}

double CompressorEmulator::addNoise(double value, double noise_percent) const {
    static std::random_device rd;
    static std::mt19937 gen(rd());
    static std::normal_distribution<> dist(0.0, 1.0);

    double noise = dist(gen) * noise_percent / 100.0 * value;
    return value + noise;
}

// ═══════════════════════════════════════════════════════════════════════
//  Сценарии
// ═══════════════════════════════════════════════════════════════════════

void CompressorEmulator::executeNormalScenario(double dt) {
    // Стабильная работа с небольшим изменением целевого расхода
    state_.target_flow = 50.0 + 5.0 * std::sin(simulation_time_ * 0.1);
    
    state_.flow_rate = calculateFlowRate(state_.bypass_valve, state_.rpm, 
                                         state_.pressure_out / state_.pressure_in);
}

void CompressorEmulator::executeApproachingSurgeScenario(double dt) {
    // Постепенное снижение расхода (приближение к помпажу)
    if (simulation_time_ < 10.0) {
        state_.target_flow = 50.0;
    } else if (simulation_time_ < 30.0) {
        // Линейное снижение от 50 до 20 м³/ч
        double progress = (simulation_time_ - 10.0) / 20.0;
        state_.target_flow = 50.0 - progress * 30.0;
    } else {
        state_.target_flow = 20.0;
    }

    state_.flow_rate = calculateFlowRate(state_.bypass_valve, state_.rpm,
                                         state_.pressure_out / state_.pressure_in);
}

void CompressorEmulator::executeSurgeScenario(double dt) {
    // Нормальная работа, затем помпаж
    if (simulation_time_ < 5.0) {
        state_.target_flow = 50.0;
        state_.surge_active = false;
    } else if (simulation_time_ < 15.0) {
        // Помпаж активен
        state_.surge_active = true;
        state_.target_flow = 25.0;
    } else {
        // Восстановление
        state_.surge_active = false;
        state_.target_flow = 50.0;
    }

    if (!state_.surge_active) {
        state_.flow_rate = calculateFlowRate(state_.bypass_valve, state_.rpm,
                                             state_.pressure_out / state_.pressure_in);
    }
}

void CompressorEmulator::executeValveResponseScenario(double dt) {
    // Проверка реакции на изменение положения клапана
    if (simulation_time_ < 5.0) {
        state_.bypass_valve = 0.0;
    } else if (simulation_time_ < 10.0) {
        state_.bypass_valve = 50.0;
    } else if (simulation_time_ < 15.0) {
        state_.bypass_valve = 100.0;
    } else {
        state_.bypass_valve = 0.0;
    }

    state_.target_flow = 50.0;
    state_.flow_rate = calculateFlowRate(state_.bypass_valve, state_.rpm,
                                         state_.pressure_out / state_.pressure_in);
}

void CompressorEmulator::executeSensorNoiseScenario(double dt) {
    // Работа с высоким уровнем шума
    noise_level_ = 5.0;  // 5% шума
    
    state_.target_flow = 50.0;
    state_.flow_rate = calculateFlowRate(state_.bypass_valve, state_.rpm,
                                         state_.pressure_out / state_.pressure_in);
}

// ═══════════════════════════════════════════════════════════════════════
//  Публичные методы
// ═══════════════════════════════════════════════════════════════════════

SensorData CompressorEmulator::getSensorData() const {
    SensorData data;
    
    // Добавляем шум к показаниям
    data.flow_rate = addNoise(state_.flow_rate, noise_level_);
    data.pressure_in = addNoise(state_.pressure_in, noise_level_ * 0.5);
    data.pressure_out = addNoise(state_.pressure_out, noise_level_);
    data.temperature = addNoise(state_.temperature, noise_level_ * 0.3);
    data.rpm = addNoise(state_.rpm, noise_level_ * 0.2);

    return data;
}

void CompressorEmulator::applyControl(const ControlCommand& command) {
    state_.bypass_valve = command.bypass_valve_position;
}

void CompressorEmulator::setScenario(TestScenario scenario) {
    current_scenario_ = scenario;
    simulation_time_ = 0.0;
    std::cout << "[Emulator] Scenario changed to: " << getScenarioName() << std::endl;
}

void CompressorEmulator::setTargetFlow(double flow) {
    state_.target_flow = flow;
}

void CompressorEmulator::setRPM(double rpm) {
    state_.rpm = rpm;
}

void CompressorEmulator::setInertia(double inertia) {
    state_.inertia = std::max(0.0, std::min(inertia, 1.0));
}

void CompressorEmulator::triggerSurge() {
    state_.surge_active = true;
    state_.surge_phase = 0.0;
    std::cout << "[Emulator] Surge triggered!" << std::endl;
}

void CompressorEmulator::stopSurge() {
    state_.surge_active = false;
    std::cout << "[Emulator] Surge stopped" << std::endl;
}

CompressorState CompressorEmulator::getState() const {
    return state_;
}

std::string CompressorEmulator::getScenarioName() const {
    switch (current_scenario_) {
        case TestScenario::NormalOperation: return "Normal Operation";
        case TestScenario::ApproachingSurge: return "Approaching Surge";
        case TestScenario::SurgeEvent: return "Surge Event";
        case TestScenario::ValveResponse: return "Valve Response Test";
        case TestScenario::SensorNoise: return "Sensor Noise Test";
        default: return "Unknown";
    }
}

CompressorEmulator::Statistics CompressorEmulator::getStatistics() const {
    return stats_;
}

void CompressorEmulator::updateStatistics() {
    stats_.min_flow = std::min(stats_.min_flow, state_.flow_rate);
    stats_.max_flow = std::max(stats_.max_flow, state_.flow_rate);
    stats_.avg_flow = (stats_.avg_flow * stats_.total_time + state_.flow_rate * 0.1) 
                      / (stats_.total_time + 0.1);
    stats_.total_time += 0.1;

    if (state_.surge_active && state_.flow_rate < 20.0) {
        stats_.surge_count++;
    }
}