#include "AntiSurgeCore.h"
#include "FuzzyEngine.h"
#include "DataProcessor.h"
#include <iostream>
#include <cmath>
#include <algorithm>
#include <numeric>
#include <chrono>

struct AntiSurgeCore::Impl {
    bool surge_detected = false;
    ControlCommand current_command;
    std::string status = "Initialized";

    FuzzyEngine fuzzy_engine;
    DataProcessor data_processor;

    double surge_threshold_flow = 0.0;
    double surge_threshold_pressure = 0.0;
    double surge_margin = 100.0;
    double max_bypass_valve = 100.0;

    std::vector<double> flow_history;
    std::vector<double> pressure_ratio_history;
    size_t history_size = 50;

    bool fuzzy_initialized = false;

    void initFuzzyVariables() {
        LinguisticVariable flow_var;
        flow_var.name = "flow_rate";
        flow_var.min_val = 0.0;
        flow_var.max_val = 100.0;

        FuzzySet low_flow;
        low_flow.name = "low";
        low_flow.type = MembershipType::Trapezoidal;
        low_flow.params = {0.0, 0.0, 20.0, 40.0};

        FuzzySet mid_flow;
        mid_flow.name = "medium";
        mid_flow.type = MembershipType::Triangular;
        mid_flow.params = {30.0, 50.0, 70.0};

        FuzzySet high_flow;
        high_flow.name = "high";
        high_flow.type = MembershipType::Trapezoidal;
        high_flow.params = {60.0, 80.0, 100.0, 100.0};

        flow_var.terms = {low_flow, mid_flow, high_flow};
        fuzzy_engine.addVariable(flow_var);

        LinguisticVariable pressure_var;
        pressure_var.name = "pressure_ratio";
        pressure_var.min_val = 0.5;
        pressure_var.max_val = 3.0;

        FuzzySet low_pr;
        low_pr.name = "low";
        low_pr.type = MembershipType::Trapezoidal;
        low_pr.params = {0.5, 0.5, 1.0, 1.5};

        FuzzySet mid_pr;
        mid_pr.name = "medium";
        mid_pr.type = MembershipType::Triangular;
        mid_pr.params = {1.2, 1.8, 2.4};

        FuzzySet high_pr;
        high_pr.name = "high";
        high_pr.type = MembershipType::Trapezoidal;
        high_pr.params = {2.0, 2.5, 3.0, 3.0};

        pressure_var.terms = {low_pr, mid_pr, high_pr};
        fuzzy_engine.addVariable(pressure_var);

        LinguisticVariable deriv_var;
        deriv_var.name = "flow_derivative";
        deriv_var.min_val = -10.0;
        deriv_var.max_val = 10.0;

        FuzzySet neg_deriv;
        neg_deriv.name = "negative";
        neg_deriv.type = MembershipType::Trapezoidal;
        neg_deriv.params = {-10.0, -10.0, -5.0, -1.0};

        FuzzySet zero_deriv;
        zero_deriv.name = "zero";
        zero_deriv.type = MembershipType::Triangular;
        zero_deriv.params = {-3.0, 0.0, 3.0};

        FuzzySet pos_deriv;
        pos_deriv.name = "positive";
        pos_deriv.type = MembershipType::Trapezoidal;
        pos_deriv.params = {1.0, 5.0, 10.0, 10.0};

        deriv_var.terms = {neg_deriv, zero_deriv, pos_deriv};
        fuzzy_engine.addVariable(deriv_var);

        LinguisticVariable valve_var;
        valve_var.name = "bypass_valve";
        valve_var.min_val = 0.0;
        valve_var.max_val = 100.0;

        FuzzySet valve_closed;
        valve_closed.name = "closed";
        valve_closed.type = MembershipType::Trapezoidal;
        valve_closed.params = {0.0, 0.0, 10.0, 25.0};

        FuzzySet valve_partial;
        valve_partial.name = "partial";
        valve_partial.type = MembershipType::Triangular;
        valve_partial.params = {20.0, 50.0, 80.0};

        FuzzySet valve_open;
        valve_open.name = "open";
        valve_open.type = MembershipType::Trapezoidal;
        valve_open.params = {70.0, 90.0, 100.0, 100.0};

        valve_var.terms = {valve_closed, valve_partial, valve_open};
        fuzzy_engine.addVariable(valve_var);

        FuzzyRule r1;
        r1.input_var = "flow_rate"; r1.input_term = "low";
        r1.output_var = "bypass_valve"; r1.output_term = "open";
        r1.weight = 1.0;
        fuzzy_engine.addRule(r1);

        FuzzyRule r2;
        r2.input_var = "flow_rate"; r2.input_term = "low";
        r2.output_var = "bypass_valve"; r2.output_term = "open";
        r2.weight = 1.2;
        fuzzy_engine.addRule(r2);

        FuzzyRule r3;
        r3.input_var = "flow_rate"; r3.input_term = "medium";
        r3.output_var = "bypass_valve"; r3.output_term = "partial";
        r3.weight = 0.8;
        fuzzy_engine.addRule(r3);

        FuzzyRule r4;
        r4.input_var = "flow_rate"; r4.input_term = "high";
        r4.output_var = "bypass_valve"; r4.output_term = "closed";
        r4.weight = 1.0;
        fuzzy_engine.addRule(r4);

        FuzzyRule r5;
        r5.input_var = "flow_derivative"; r5.input_term = "negative";
        r5.output_var = "bypass_valve"; r5.output_term = "open";
        r5.weight = 1.1;
        fuzzy_engine.addRule(r5);

        fuzzy_initialized = true;
    }

    bool checkSurgeCondition(const SensorData& data) {
        if (surge_threshold_flow > 0.0 && data.flow_rate < surge_threshold_flow) {
            return true;
        }

        if (flow_history.size() >= 5) {
            double recent_avg = 0.0;
            for (size_t i = flow_history.size() - 3; i < flow_history.size(); ++i) {
                recent_avg += flow_history[i];
            }
            recent_avg /= 3.0;

            double older_avg = 0.0;
            for (size_t i = flow_history.size() - 5; i < flow_history.size() - 3; ++i) {
                older_avg += flow_history[i];
            }
            older_avg /= 2.0;

            if (older_avg > 0.0 && (older_avg - recent_avg) / older_avg > 0.30) {
                return true;
            }
        }

        if (data.pressure_out < data.pressure_in * 0.8) {
            return true;
        }

        if (pressure_ratio_history.size() >= 5) {
            double sum = 0.0;
            for (double v : pressure_ratio_history) sum += v;
            double mean = sum / pressure_ratio_history.size();

            double variance = 0.0;
            for (double v : pressure_ratio_history) {
                variance += (v - mean) * (v - mean);
            }
            variance /= pressure_ratio_history.size();
            double stddev = std::sqrt(variance);

            if (mean > 0.0 && stddev / mean > 0.25) {
                return true;
            }
        }

        return false;
    }

    double calculateSurgeMargin(const SensorData& data) {
        if (surge_threshold_flow <= 0.0) return 100.0;
        double margin = ((data.flow_rate - surge_threshold_flow) / surge_threshold_flow) * 100.0;
        return std::max(0.0, std::min(margin, 200.0));
    }
};

AntiSurgeCore::AntiSurgeCore() : pImpl(std::make_unique<Impl>()) {
    pImpl->initFuzzyVariables();
}

AntiSurgeCore::~AntiSurgeCore() = default;

bool AntiSurgeCore::initialize(const std::string& config_path) {
    // Пытаемся загрузить конфигурацию правил из файла
    if (!config_path.empty()) {
        if (pImpl->fuzzy_engine.loadRules(config_path)) {
            pImpl->status = "Loaded rules from: " + config_path;
        } else {
            pImpl->status = "Using default fuzzy rules (config not loaded)";
        }
    } else {
        pImpl->status = "Initialized with default parameters";
    }

    pImpl->surge_threshold_flow = 15.0;
    pImpl->surge_threshold_pressure = 2.5;

    pImpl->current_command.bypass_valve_position = 0.0;
    pImpl->current_command.alarm_status = false;
    pImpl->current_command.timestamp = std::chrono::system_clock::now();

    return true;
}

ControlCommand AntiSurgeCore::processSensorData(const SensorData& data) {
    pImpl->current_command.timestamp = std::chrono::system_clock::now();

    pImpl->flow_history.push_back(data.flow_rate);
    if (pImpl->flow_history.size() > pImpl->history_size) {
        pImpl->flow_history.erase(pImpl->flow_history.begin());
    }

    double pressure_ratio = (data.pressure_in > 0.0)
                            ? data.pressure_out / data.pressure_in
                            : 0.0;
    pImpl->pressure_ratio_history.push_back(pressure_ratio);
    if (pImpl->pressure_ratio_history.size() > pImpl->history_size) {
        pImpl->pressure_ratio_history.erase(pImpl->pressure_ratio_history.begin());
    }

    std::vector<double> filtered_flow = pImpl->data_processor.filterNoise(pImpl->flow_history);

    std::vector<double> derivative = pImpl->data_processor.calculateDerivative(filtered_flow);
    double current_derivative = derivative.empty() ? 0.0 : derivative.back();

    double valve_position = 0.0;

    if (pImpl->fuzzy_initialized && pImpl->fuzzy_engine.getRuleCount() > 0) {
        std::map<std::string, double> inputs;
        inputs["flow_rate"] = data.flow_rate;
        inputs["pressure_ratio"] = pressure_ratio;
        inputs["flow_derivative"] = current_derivative;

        auto outputs = pImpl->fuzzy_engine.infer(inputs);

        auto it = outputs.find("bypass_valve");
        if (it != outputs.end()) {
            valve_position = it->second;
        }
    }

    bool surge = pImpl->checkSurgeCondition(data);
    pImpl->surge_detected = surge;

    if (surge) {
        valve_position = 100.0;
        pImpl->current_command.alarm_status = true;
        pImpl->status = "SURGE DETECTED! Emergency bypass valve open.";
    } else {
        pImpl->current_command.alarm_status = false;
    }

    pImpl->surge_margin = pImpl->calculateSurgeMargin(data);

    valve_position = std::max(0.0, std::min(valve_position, pImpl->max_bypass_valve));
    pImpl->current_command.bypass_valve_position = valve_position;

    if (!surge) {
        char buf[128];
        snprintf(buf, sizeof(buf),
                 "Normal operation | Flow: %.1f | Margin: %.1f%% | Valve: %.1f%%",
                 data.flow_rate, pImpl->surge_margin, valve_position);
        pImpl->status = buf;
    }

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

double AntiSurgeCore::getSurgeMargin() const {
    return pImpl->surge_margin;
}

std::vector<double> AntiSurgeCore::getRecentFlowRates() const {
    return pImpl->flow_history;
}

void AntiSurgeCore::setSurgeThreshold(double threshold) {
    pImpl->surge_threshold_flow = threshold;
}