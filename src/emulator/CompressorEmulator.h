#pragma once

#include <string>
#include <vector>
#include <functional>
#include "../dto/Contracts.h"

// ─── Сценарии тестирования ───────────────────────────────────────────
enum class TestScenario {
    NormalOperation,        // Нормальная работа
    ApproachingSurge,       // Приближение к помпажу
    SurgeEvent,             // Помпаж
    ValveResponse,          // Проверка реакции на клапан
    SensorNoise,            // Работа с шумом датчиков
    Custom                  // Пользовательский сценарий
};

// ─── Структура состояния компрессора ─────────────────────────────────
struct CompressorState {
    double flow_rate = 50.0;           // м³/ч
    double pressure_in = 1.0;          // бар (вход)
    double pressure_out = 2.0;         // бар (выход)
    double temperature = 25.0;         // °C
    double rpm = 3000.0;               // об/мин
    double bypass_valve = 0.0;         // % (0-100)
    double surge_margin = 100.0;       // %
    
    // Внутренние параметры модели
    double target_flow = 50.0;         // целевой расход
    double inertia = 0.8;              // инерционность (0-1)
    bool surge_active = false;         // активен ли помпаж
    double surge_phase = 0.0;          // фаза помпажа (для колебаний)
};

// ─── Класс эмулятора компрессора ─────────────────────────────────────
class CompressorEmulator {
public:
    CompressorEmulator();
    ~CompressorEmulator();

    // ─── Основные методы ─────────────────────────────────────────────

    // Инициализация эмулятора
    bool initialize(TestScenario scenario = TestScenario::NormalOperation);

    // Обновление состояния (вызывается каждый такт симуляции)
    void update(double dt);

    // Получение текущих данных с датчиков
    SensorData getSensorData() const;

    // Применение команды управления (позиция клапана)
    void applyControl(const ControlCommand& command);

    // ─── Управление сценарием ────────────────────────────────────────

    // Установка сценария
    void setScenario(TestScenario scenario);

    // Пользовательское изменение параметров
    void setTargetFlow(double flow);
    void setRPM(double rpm);
    void setInertia(double inertia);

    // Ручной запуск помпажа
    void triggerSurge();
    void stopSurge();

    // ─── Получение состояния ─────────────────────────────────────────

    CompressorState getState() const;
    std::string getScenarioName() const;

    // ─── Статистика ──────────────────────────────────────────────────

    struct Statistics {
        double min_flow = 0.0;
        double max_flow = 0.0;
        double avg_flow = 0.0;
        int surge_count = 0;
        double total_time = 0.0;
    };

    Statistics getStatistics() const;

private:
    CompressorState state_;
    TestScenario current_scenario_;
    Statistics stats_;
    
    double simulation_time_ = 0.0;
    double noise_level_ = 0.5;         // уровень шума датчиков (%)
    
    // ─── Физическая модель ───────────────────────────────────────────

    // Расчёт расхода на основе параметров
    double calculateFlowRate(double valve_position, double rpm, double pressure_ratio);

    // Расчёт давления на выходе
    double calculatePressureOut(double flow_rate, double rpm);

    // Расчёт температуры
    double calculateTemperature(double flow_rate, double pressure_ratio);

    // Моделирование помпажа
    void simulateSurge(double dt);

    // Добавление шума к данным
    double addNoise(double value, double noise_percent) const;

    // ─── Сценарии ────────────────────────────────────────────────────

    void executeNormalScenario(double dt);
    void executeApproachingSurgeScenario(double dt);
    void executeSurgeScenario(double dt);
    void executeValveResponseScenario(double dt);
    void executeSensorNoiseScenario(double dt);

    // ─── Обновление статистики ───────────────────────────────────────

    void updateStatistics();
};