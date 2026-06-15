#include "AntiSurgeCore.h"
#include <iostream>

struct AntiSurgeCore::Impl {
    bool surge_detected = false;
    ControlCommand current_command;
    std::string status = "Initialized";
};

AntiSurgeCore::AntiSurgeCore() : pImpl(std::make_unique<Impl>()) {}
AntiSurgeCore::~AntiSurgeCore() = default;

bool AntiSurgeCore::initialize(const std::string& config_path) {
    pImpl->status = "Initialized with config: " + config_path;
    return true;
}

ControlCommand AntiSurgeCore::processSensorData(const SensorData& data) {
    // Здесь будет ваша логика обработки
    pImpl->current_command.bypass_valve_position = 50.0;  // Пример
    pImpl->current_command.alarm_status = false;
    return pImpl->current_command;
}

ControlCommand AntiSurgeCore::getControlCommand() const {
    return pImpl->current_command;
}

bool AntiSurgeCore::isSurgeDetected() const {
    return pImpl->surge_detected;
}

std::string AntiSurgeCore::getSystemStatus() const {
    return pImpl->status;
}