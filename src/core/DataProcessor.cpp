#include "DataProcessor.h"
#include <algorithm>
#include <numeric>
#include <cmath>
#include <complex>
#include <iostream>

DataProcessor::DataProcessor() {}
DataProcessor::~DataProcessor() {}

std::vector<double> DataProcessor::filterNoise(const std::vector<double>& data) {
    if (data.size() < 3) return data;

    auto median_filtered = medianFilter(data, 3);
    return exponentialSmoothing(median_filtered, 0.4);
}

std::vector<double> DataProcessor::calculateDerivative(const std::vector<double>& data) {
    std::vector<double> result;
    if (data.size() < 2) return result;

    for (size_t i = 1; i < data.size(); ++i) {
        result.push_back(data[i] - data[i - 1]);
    }
    return result;
}

std::vector<double> DataProcessor::smoothData(const std::vector<double>& data, int window_size) {
    // Обратная совместимость — скользящее среднее
    return weightedMovingAverage(data, window_size);
}

std::vector<double> DataProcessor::medianFilter(const std::vector<double>& data, int window_size) {
    std::vector<double> result;
    if (data.empty() || window_size <= 0) return result;

    int half = window_size / 2;
    result.reserve(data.size());

    for (size_t i = 0; i < data.size(); ++i) {
        int start = static_cast<int>(i) - half;
        int end = static_cast<int>(i) + half;

        std::vector<double> window;
        for (int j = start; j <= end; ++j) {
            if (j >= 0 && j < static_cast<int>(data.size())) {
                window.push_back(data[j]);
            }
        }

        std::sort(window.begin(), window.end());
        result.push_back(window[window.size() / 2]);
    }

    return result;
}

std::vector<double> DataProcessor::exponentialSmoothing(const std::vector<double>& data, double alpha) {
    std::vector<double> result;
    if (data.empty()) return result;

    alpha = clamp(alpha, 0.01, 0.99);
    result.reserve(data.size());
    result.push_back(data[0]);

    for (size_t i = 1; i < data.size(); ++i) {
        double smoothed = alpha * data[i] + (1.0 - alpha) * result.back();
        result.push_back(smoothed);
    }

    return result;
}

std::vector<double> DataProcessor::lowPassFilter(const std::vector<double>& data,
                                                  double cutoff_freq,
                                                  double sample_rate) {
    std::vector<double> result;
    if (data.empty() || cutoff_freq <= 0.0 || sample_rate <= 0.0) return data;

    double dt = 1.0 / sample_rate;
    double RC = 1.0 / (2.0 * M_PI * cutoff_freq);
    double alpha = dt / (RC + dt);
    alpha = clamp(alpha, 0.001, 0.999);

    result.reserve(data.size());
    result.push_back(data[0]);

    for (size_t i = 1; i < data.size(); ++i) {
        double y = result.back() + alpha * (data[i] - result.back());
        result.push_back(y);
    }

    return result;
}

std::vector<double> DataProcessor::kalmanFilter(const std::vector<double>& data,
                                                 double process_noise,
                                                 double measurement_noise) {
    std::vector<double> result;
    if (data.empty()) return result;

    result.reserve(data.size());

    if (!kalman_state_.initialized) {
        kalman_state_.x = data[0];
        kalman_state_.P = 1.0;
        kalman_state_.initialized = true;
    }

    for (size_t i = 0; i < data.size(); ++i) {
        double x_pred = kalman_state_.x;
        double P_pred = kalman_state_.P + process_noise;

        double K = P_pred / (P_pred + measurement_noise);
        double x_est = x_pred + K * (data[i] - x_pred);
        double P_est = (1.0 - K) * P_pred;

        kalman_state_.x = x_est;
        kalman_state_.P = P_est;

        result.push_back(x_est);
    }

    return result;
}

std::vector<double> DataProcessor::weightedMovingAverage(const std::vector<double>& data, int window_size) {
    std::vector<double> result;
    if (data.empty() || window_size <= 0) return result;

    result.reserve(data.size());

    for (size_t i = 0; i < data.size(); ++i) {
        int start = static_cast<int>(i) - window_size + 1;
        if (start < 0) start = 0;

        double weighted_sum = 0.0;
        double weight_total = 0.0;

        for (int j = start; j <= static_cast<int>(i); ++j) {
            double weight = (j - start + 1.0);
            weighted_sum += data[j] * weight;
            weight_total += weight;
        }

        result.push_back(weighted_sum / weight_total);
    }

    return result;
}

std::vector<double> DataProcessor::centralDifference(const std::vector<double>& data, double dt) {
    std::vector<double> result;
    if (data.size() < 3 || dt <= 0.0) return result;

    result.reserve(data.size());

    result.push_back((data[1] - data[0]) / dt);

    for (size_t i = 1; i + 1 < data.size(); ++i) {
        result.push_back((data[i + 1] - data[i - 1]) / (2.0 * dt));
    }

    result.push_back((data.back() - data[data.size() - 2]) / dt);

    return result;
}

std::vector<double> DataProcessor::secondDerivative(const std::vector<double>& data, double dt) {
    std::vector<double> result;
    if (data.size() < 3 || dt <= 0.0) return result;

    result.reserve(data.size() - 2);

    for (size_t i = 1; i + 1 < data.size(); ++i) {
        double d2 = (data[i + 1] - 2.0 * data[i] + data[i - 1]) / (dt * dt);
        result.push_back(d2);
    }

    return result;
}

std::vector<double> DataProcessor::integrate(const std::vector<double>& data, double dt) {
    std::vector<double> result;
    if (data.empty() || dt <= 0.0) return result;

    result.reserve(data.size());
    result.push_back(0.0);

    double integral = 0.0;
    for (size_t i = 1; i < data.size(); ++i) {
        integral += (data[i] + data[i - 1]) * dt / 2.0;
        result.push_back(integral);
    }

    return result;
}

Statistics DataProcessor::calculateStatistics(const std::vector<double>& data) {
    Statistics stats;
    if (data.empty()) return stats;

    stats.count = data.size();

    stats.min_val = *std::min_element(data.begin(), data.end());
    stats.max_val = *std::max_element(data.begin(), data.end());

    stats.mean = std::accumulate(data.begin(), data.end(), 0.0) / data.size();

    double sq_sum = 0.0;
    for (double v : data) {
        sq_sum += (v - stats.mean) * (v - stats.mean);
    }
    stats.variance = sq_sum / data.size();
    stats.stddev = std::sqrt(stats.variance);

    std::vector<double> sorted_data = data;
    std::sort(sorted_data.begin(), sorted_data.end());
    size_t mid = sorted_data.size() / 2;
    if (sorted_data.size() % 2 == 0) {
        stats.median = (sorted_data[mid - 1] + sorted_data[mid]) / 2.0;
    } else {
        stats.median = sorted_data[mid];
    }

    return stats;
}

double DataProcessor::movingAverage(const std::vector<double>& data, int window_size) {
    if (data.empty() || window_size <= 0) return 0.0;

    size_t start = (data.size() > static_cast<size_t>(window_size))
                   ? data.size() - window_size
                   : 0;

    double sum = 0.0;
    for (size_t i = start; i < data.size(); ++i) {
        sum += data[i];
    }
    return sum / (data.size() - start);
}

double DataProcessor::movingStdDev(const std::vector<double>& data, int window_size) {
    if (data.size() < 2 || window_size <= 1) return 0.0;

    size_t start = (data.size() > static_cast<size_t>(window_size))
                   ? data.size() - window_size
                   : 0;

    double sum = 0.0, sq_sum = 0.0;
    size_t count = 0;
    for (size_t i = start; i < data.size(); ++i) {
        sum += data[i];
        sq_sum += data[i] * data[i];
        count++;
    }

    if (count < 2) return 0.0;
    double mean = sum / count;
    double variance = (sq_sum / count) - (mean * mean);
    return std::sqrt(std::max(0.0, variance));
}

LinearFit DataProcessor::linearRegression(const std::vector<double>& data) {
    LinearFit fit;
    size_t n = data.size();
    if (n < 2) return fit;

    double sum_x = 0.0, sum_y = 0.0, sum_xy = 0.0, sum_x2 = 0.0, sum_y2 = 0.0;

    for (size_t i = 0; i < n; ++i) {
        double x = static_cast<double>(i);
        double y = data[i];
        sum_x += x;
        sum_y += y;
        sum_xy += x * y;
        sum_x2 += x * x;
        sum_y2 += y * y;
    }

    double denom = n * sum_x2 - sum_x * sum_x;
    if (std::abs(denom) < 1e-12) return fit;

    fit.slope = (n * sum_xy - sum_x * sum_y) / denom;
    fit.intercept = (sum_y - fit.slope * sum_x) / n;

    double ss_tot = sum_y2 - (sum_y * sum_y) / n;
    double ss_res = 0.0;
    for (size_t i = 0; i < n; ++i) {
        double predicted = fit.slope * i + fit.intercept;
        ss_res += (data[i] - predicted) * (data[i] - predicted);
    }

    fit.r_squared = (ss_tot > 1e-12) ? (1.0 - ss_res / ss_tot) : 0.0;

    return fit;
}

int DataProcessor::detectTrend(const std::vector<double>& data, double threshold) {
    if (data.size() < 3) return 0;

    LinearFit fit = linearRegression(data);

    double range = 0.0;
    if (!data.empty()) {
        auto [min_it, max_it] = std::minmax_element(data.begin(), data.end());
        range = *max_it - *min_it;
    }

    if (range < 1e-12) return 0;

    double normalized_slope = fit.slope / range;

    if (normalized_slope > threshold) return 1;
    if (normalized_slope < -threshold) return -1;
}

std::vector<bool> DataProcessor::detectOutliers(const std::vector<double>& data, double sigma_multiplier) {
    std::vector<bool> result(data.size(), false);
    if (data.size() < 3) return result;

    Statistics stats = calculateStatistics(data);
    if (stats.stddev < 1e-12) return result;

    double bound = stats.stddev * sigma_multiplier;
    for (size_t i = 0; i < data.size(); ++i) {
        if (std::abs(data[i] - stats.mean) > bound) {
            result[i] = true;
        }
    }

    return result;
}

std::vector<double> DataProcessor::removeOutliers(const std::vector<double>& data, double sigma_multiplier) {
    if (data.size() < 3) return data;

    std::vector<bool> outliers = detectOutliers(data, sigma_multiplier);
    std::vector<double> result = data;

    for (size_t i = 0; i < result.size(); ++i) {
        if (outliers[i]) {
            double left = (i > 0 && !outliers[i - 1]) ? result[i - 1] : data[i];
            double right = (i + 1 < result.size() && !outliers[i + 1]) ? result[i + 1] : data[i];
            result[i] = (left + right) / 2.0;
        }
    }

    return result;
}

std::vector<double> DataProcessor::nextPowerOf2(const std::vector<double>& data) {
    size_t n = 1;
    while (n < data.size()) n <<= 1;

    std::vector<double> padded(n, 0.0);
    for (size_t i = 0; i < data.size(); ++i) {
        padded[i] = data[i];
    }
    return padded;
}

void DataProcessor::fftRecursive(std::vector<double>& real, std::vector<double>& imag, bool inverse) {
    size_t n = real.size();
    if (n <= 1) return;

    std::vector<double> even_r(n / 2), even_i(n / 2);
    std::vector<double> odd_r(n / 2), odd_i(n / 2);

    for (size_t i = 0; i < n / 2; ++i) {
        even_r[i] = real[2 * i];
        even_i[i] = imag[2 * i];
        odd_r[i] = real[2 * i + 1];
        odd_i[i] = imag[2 * i + 1];
    }

    fftRecursive(even_r, even_i, inverse);
    fftRecursive(odd_r, odd_i, inverse);

    double angle = 2.0 * M_PI / n * (inverse ? -1.0 : 1.0);
    double w_r = std::cos(angle), w_i = std::sin(angle);

    double cur_r = 1.0, cur_i = 0.0;
    for (size_t k = 0; k < n / 2; ++k) {
        double t_r = cur_r * odd_r[k] - cur_i * odd_i[k];
        double t_i = cur_r * odd_i[k] + cur_i * odd_r[k];

        real[k] = even_r[k] + t_r;
        imag[k] = even_i[k] + t_i;
        real[k + n / 2] = even_r[k] - t_r;
        imag[k + n / 2] = even_i[k] - t_i;

        double new_r = cur_r * w_r - cur_i * w_i;
        cur_i = cur_r * w_i + cur_i * w_r;
        cur_r = new_r;
    }
}

std::vector<double> DataProcessor::fftMagnitude(const std::vector<double>& data) {
    if (data.size() < 2) return {};

    std::vector<double> padded = nextPowerOf2(data);
    size_t n = padded.size();

    std::vector<double> real = padded;
    std::vector<double> imag(n, 0.0);

    fftRecursive(real, imag, false);

    std::vector<double> magnitude(n / 2);
    for (size_t i = 0; i < n / 2; ++i) {
        magnitude[i] = std::sqrt(real[i] * real[i] + imag[i] * imag[i]) / n;
    }

    return magnitude;
}

double DataProcessor::dominantFrequency(const std::vector<double>& data, double sample_rate) {
    if (data.size() < 4 || sample_rate <= 0.0) return 0.0;

    double mean = std::accumulate(data.begin(), data.end(), 0.0) / data.size();
    std::vector<double> centered(data.size());
    for (size_t i = 0; i < data.size(); ++i) {
        centered[i] = data[i] - mean;
    }

    std::vector<double> spectrum = fftMagnitude(centered);
    if (spectrum.empty()) return 0.0;

    size_t max_idx = 1;
    for (size_t i = 2; i < spectrum.size(); ++i) {
        if (spectrum[i] > spectrum[max_idx]) {
            max_idx = i;
        }
    }

    size_t n = nextPowerOf2(data).size();
    double freq_resolution = sample_rate / n;

    return max_idx * freq_resolution;
}

bool DataProcessor::detectSurge(const std::vector<double>& flow_history,
                                 const std::vector<double>& pressure_history,
                                 double flow_threshold,
                                 double oscillation_threshold) {
    if (flow_history.size() < 5) return false;

    double recent_flow = flow_history.back();
    if (recent_flow < flow_threshold) {
        return true;
    }

    size_t n = flow_history.size();
    double old_avg = 0.0;
    size_t old_count = std::min(static_cast<size_t>(3), n - 2);
    for (size_t i = n - old_count - 2; i < n - 2; ++i) {
        old_avg += flow_history[i];
    }
    old_avg /= old_count;

    double recent_avg = 0.0;
    size_t recent_count = std::min(static_cast<size_t>(2), n);
    for (size_t i = n - recent_count; i < n; ++i) {
        recent_avg += flow_history[i];
    }
    recent_avg /= recent_count;

    if (old_avg > 0.0 && (old_avg - recent_avg) / old_avg > 0.30) {
        return true;
    }

    if (pressure_history.size() >= 5) {
        double osc_index = calculateOscillationIndex(pressure_history);
        if (osc_index > oscillation_threshold) {
            return true;
        }
    }

    int trend = detectTrend(flow_history, 0.05);
    if (trend == -1 && recent_flow < flow_threshold * 1.5) {
        return true;
    }

    return false;
}

double DataProcessor::calculateOscillationIndex(const std::vector<double>& data) {
    if (data.size() < 3) return 0.0;

    Statistics stats = calculateStatistics(data);
    if (stats.mean <= 0.0) return 0.0;

    return stats.stddev / stats.mean;
}

double DataProcessor::clamp(double val, double min_val, double max_val) {
    return std::max(min_val, std::min(val, max_val));
}