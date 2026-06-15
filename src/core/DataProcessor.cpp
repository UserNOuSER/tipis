#include "DataProcessor.h"
#include <numeric>

DataProcessor::DataProcessor() {}

std::vector<double> DataProcessor::filterNoise(const std::vector<double>& data) {
    // Простая реализация - скользящее среднее
    return smoothData(data, 3);
}

std::vector<double> DataProcessor::calculateDerivative(const std::vector<double>& data) {
    std::vector<double> result;
    for (size_t i = 1; i < data.size(); ++i) {
        result.push_back(data[i] - data[i - 1]);
    }
    return result;
}

std::vector<double> DataProcessor::smoothData(const std::vector<double>& data, int window_size) {
    std::vector<double> result;
    for (size_t i = 0; i < data.size(); ++i) {
        int start = (i >= window_size / 2) ? i - window_size / 2 : 0;
        int end = (i + window_size / 2 < data.size()) ? i + window_size / 2 : data.size() - 1;

        double sum = 0.0;
        int count = 0;
        for (int j = start; j <= end; ++j) {
            sum += data[j];
            count++;
        }
        result.push_back(sum / count);
    }
    return result;
}