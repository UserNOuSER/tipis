#pragma once
#include <string>
#include <vector>
#include <map>

class FuzzyEngine {
public:
    FuzzyEngine();

    bool loadRules(const std::string& rules_file);
    std::map<std::string, double> infer(const std::map<std::string, double>& inputs);
    double defuzzify(const std::vector<double>& fuzzy_set);
    bool addRule(const std::string& rule);
};