#pragma once
#include <vector>
#include <deque>
#include <cmath>
#include <functional>

struct Statistics {
    double mean = 0.0;
    double variance = 0.0;
    double stddev = 0.0;
    double min_val = 0.0;
    double max_val = 0.0;
    double median = 0.0;
    size_t count = 0;
};

struct LinearFit {
    double slope = 0.0;
    double intercept = 0.0;
    double r_squared = 0.0;
};

class DataProcessor {
public:
    DataProcessor();
    ~DataProcessor();

    std::vector<double> filterNoise(const std::vector<double>& data);
    std::vector<double> calculateDerivative(const std::vector<double>& data);
    std::vector<double> smoothData(const std::vector<double>& data, int window_size = 5);

    std::vector<double> medianFilter(const std::vector<double>& data, int window_size = 5);

    std::vector<double> exponentialSmoothing(const std::vector<double>& data, double alpha = 0.3);

    std::vector<double> lowPassFilter(const std::vector<double>& data, double cutoff_freq, double sample_rate);

    std::vector<double> kalmanFilter(const std::vector<double>& data,
                                     double process_noise = 1e-5,
                                     double measurement_noise = 0.01);

    std::vector<double> weightedMovingAverage(const std::vector<double>& data, int window_size = 5);

    std::vector<double> centralDifference(const std::vector<double>& data, double dt = 1.0);

    std::vector<double> secondDerivative(const std::vector<double>& data, double dt = 1.0);

    std::vector<double> integrate(const std::vector<double>& data, double dt = 1.0);

    Statistics calculateStatistics(const std::vector<double>& data);

    double movingAverage(const std::vector<double>& data, int window_size);

    double movingStdDev(const std::vector<double>& data, int window_size);

    LinearFit linearRegression(const std::vector<double>& data);

    int detectTrend(const std::vector<double>& data, double threshold = 0.01);

    std::vector<bool> detectOutliers(const std::vector<double>& data, double sigma_multiplier = 3.0);

    std::vector<double> removeOutliers(const std::vector<double>& data, double sigma_multiplier = 3.0);

    std::vector<double> fftMagnitude(const std::vector<double>& data);

    double dominantFrequency(const std::vector<double>& data, double sample_rate);

    bool detectSurge(const std::vector<double>& flow_history,
                     const std::vector<double>& pressure_history,
                     double flow_threshold,
                     double oscillation_threshold = 0.25);

    double calculateOscillationIndex(const std::vector<double>& data);

private:
    struct KalmanState {
        double x = 0.0;
        double P = 1.0;
        bool initialized = false;
    };

    KalmanState kalman_state_;

    static double clamp(double val, double min_val, double max_val);
    static std::vector<double> nextPowerOf2(const std::vector<double>& data);
    static void fftRecursive(std::vector<double>& real, std::vector<double>& imag, bool inverse);
};