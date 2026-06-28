#pragma once
#include <string>
#include <memory>
#include <vector>
#include "../dto/Contracts.h"

class AntiSurgeCore {
public:
    AntiSurgeCore();
    ~AntiSurgeCore();

    bool initialize(const std::string& config_path);
    ControlCommand processSensorData(const SensorData& data);
    ControlCommand getControlCommand() const;
    bool isSurgeDetected() const;
    std::string getSystemStatus() const;

    // Новые методы
    double getSurgeMargin() const;
    std::vector<double> getRecentFlowRates() const;
    void setSurgeThreshold(double threshold);

private:
    struct Impl;
    std::unique_ptr<Impl> pImpl;
};