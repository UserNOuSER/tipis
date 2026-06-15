#pragma once
#include <vector>

class DataProcessor {
public:
    DataProcessor();

    std::vector<double> filterNoise(const std::vector<double>& data);
    std::vector<double> calculateDerivative(const std::vector<double>& data);
    std::vector<double> smoothData(const std::vector<double>& data, int window_size = 5);
};