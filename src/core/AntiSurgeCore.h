#pragma once
#include <string>
#include <memory>
#include "../dto/Contracts.h"  // ВАЖНО: правильный путь к Contracts.h

class AntiSurgeCore {
public:
    AntiSurgeCore();
    ~AntiSurgeCore();

    bool initialize(const std::string& config_path);
    ControlCommand processSensorData(const SensorData& data); 
    ControlCommand getControlCommand() const;
    bool isSurgeDetected() const;
    std::string getSystemStatus() const;

private:
    struct Impl;
    std::unique_ptr<Impl> pImpl;
};