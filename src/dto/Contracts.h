#pragma once
#include <string>
#include <chrono>

struct SensorData {
    double flow_rate = 0.0;
    double pressure_in = 0.0;
    double pressure_out = 0.0;
    double temperature = 0.0;
    double rpm = 0.0;
    std::chrono::system_clock::time_point timestamp;
};

struct ControlCommand {
    double bypass_valve_position = 0.0;  // 0.0 - 100.0%
    bool alarm_status = false;
    std::chrono::system_clock::time_point timestamp;
};