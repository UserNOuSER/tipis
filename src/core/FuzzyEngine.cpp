#include "FuzzyEngine.h"
#include <fstream>
#include <iostream>

FuzzyEngine::FuzzyEngine() {}

bool FuzzyEngine::loadRules(const std::string& rules_file) {
    std::ifstream file(rules_file);
    if (!file.is_open()) {
        std::cerr << "Failed to open rules file: " << rules_file << std::endl;
        return false;
    }
    // Здесь будет загрузка правил из JSON
    return true;
}

std::map<std::string, double> FuzzyEngine::infer(const std::map<std::string, double>& inputs) {
    std::map<std::string, double> result;
    // Здесь будет логика нечеткого вывода
    result["bypass_valve"] = 50.0;  // Пример
    return result;
}

double FuzzyEngine::defuzzify(const std::vector<double>& fuzzy_set) {
    if (fuzzy_set.empty()) return 0.0;
    double sum = 0.0;
    for (double val : fuzzy_set) {
        sum += val;
    }
    return sum / fuzzy_set.size();
}

bool FuzzyEngine::addRule(const std::string& rule) {
    // Здесь будет добавление правила
    return true;
}