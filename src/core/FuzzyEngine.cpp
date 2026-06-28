#include "FuzzyEngine.h"
#include <fstream>
#include <iostream>
#include <sstream>
#include <cmath>
#include <algorithm>
#include <numeric>

double FuzzySet::membership(double x) const {
    switch (type) {
        case MembershipType::Triangular: {
            if (params.size() < 3) return 0.0;
            double a = params[0], b = params[1], c = params[2];
            if (x <= a || x >= c) return 0.0;
            if (x <= b) return (x - a) / (b - a);
            return (c - x) / (c - b);
        }
        case MembershipType::Trapezoidal: {
            if (params.size() < 4) return 0.0;
            double a = params[0], b = params[1], c = params[2], d = params[3];
            if (x <= a || x >= d) return 0.0;
            if (x >= b && x <= c) return 1.0;
            if (x < b) return (x - a) / (b - a);
            return (d - x) / (d - c);
        }
        case MembershipType::Gaussian: {
            if (params.size() < 2) return 0.0;
            double center = params[0], sigma = params[1];
            if (sigma <= 0.0) return 0.0;
            return std::exp(-0.5 * std::pow((x - center) / sigma, 2));
        }
    }
    return 0.0;
}

FuzzyEngine::FuzzyEngine() {}

void FuzzyEngine::addVariable(const LinguisticVariable& var) {
    variables_[var.name] = var;
}

void FuzzyEngine::addRule(const FuzzyRule& rule) {
    rules_.push_back(rule);
}

bool FuzzyEngine::addRule(const std::string& rule_str) {
    FuzzyRule rule;
    std::istringstream iss(rule_str);
    std::string token;
    std::vector<std::string> tokens;

    while (iss >> token) {
        std::string upper = token;
        std::transform(upper.begin(), upper.end(), upper.begin(), ::toupper);
        tokens.push_back(upper);
    }

    if (tokens.size() < 7) return false;
    if (tokens[0] != "IF") return false;
    if (tokens[2] != "IS") return false;
    if (tokens[4] != "THEN") return false;
    if (tokens[6] != "IS") return false;

    rule.input_var = rule_str.substr(rule_str.find("IF ") + 3,
                                     rule_str.find(" IS ") - rule_str.find("IF ") - 3);
    size_t is1 = rule_str.find(" IS ");
    size_t then_pos = rule_str.find(" THEN ");
    size_t is2 = rule_str.find(" IS ", then_pos);

    if (is1 == std::string::npos || then_pos == std::string::npos || is2 == std::string::npos)
        return false;

    rule.input_var = rule_str.substr(3, is1 - 3); // после "IF "
    rule.input_term = rule_str.substr(is1 + 4, then_pos - is1 - 4);
    rule.output_var = rule_str.substr(then_pos + 6, is2 - then_pos - 6);
    rule.output_term = rule_str.substr(is2 + 4);

    auto trim = [](std::string& s) {
        s.erase(0, s.find_first_not_of(" \t"));
        s.erase(s.find_last_not_of(" \t") + 1);
    };
    trim(rule.input_var);
    trim(rule.input_term);
    trim(rule.output_var);
    trim(rule.output_term);

    size_t weight_pos = rule_str.find("WEIGHT ");
    if (weight_pos != std::string::npos) {
        std::string w_str = rule_str.substr(weight_pos + 7);
        trim(w_str);
        try {
            rule.weight = std::stod(w_str);
        } catch (...) {
            rule.weight = 1.0;
        }
    }

    rules_.push_back(rule);
    return true;
}

bool FuzzyEngine::loadRules(const std::string& rules_file) {
    std::ifstream file(rules_file);
    if (!file.is_open()) {
        std::cerr << "Failed to open rules file: " << rules_file << std::endl;
        return false;
    }

    std::string line;
    int loaded = 0;
    while (std::getline(file, line)) {
        if (line.empty() || line[0] == '#' || line[0] == '/') continue;

        std::string upper_line = line;
        std::transform(upper_line.begin(), upper_line.end(), upper_line.begin(), ::toupper);

        if (upper_line.find("VAR ") == 0) {
            std::istringstream iss(line);
            std::string keyword, name;
            double min_v, max_v;
            iss >> keyword >> name >> min_v >> max_v;
            LinguisticVariable var;
            var.name = name;
            var.min_val = min_v;
            var.max_val = max_v;
            variables_[name] = var;
        }
        else if (upper_line.find("TERM ") == 0) {
            std::istringstream iss(line);
            std::string keyword, var_name, term_name, type_str;
            iss >> keyword >> var_name >> term_name >> type_str;

            FuzzySet set;
            set.name = term_name;

            if (type_str.find("tri") == 0) {
                set.type = MembershipType::Triangular;
                double a, b, c;
                char paren;
                iss >> paren >> a >> paren >> b >> paren >> c >> paren;
                set.params = {a, b, c};
            } else if (type_str.find("trap") == 0) {
                set.type = MembershipType::Trapezoidal;
                double a, b, c, d;
                char paren;
                iss >> paren >> a >> paren >> b >> paren >> c >> paren >> d >> paren;
                set.params = {a, b, c, d};
            } else if (type_str.find("gauss") == 0) {
                set.type = MembershipType::Gaussian;
                double center, sigma;
                char paren;
                iss >> paren >> center >> paren >> sigma >> paren;
                set.params = {center, sigma};
            }

            if (variables_.count(var_name)) {
                variables_[var_name].terms.push_back(set);
            }
        }
        else if (upper_line.find("IF ") == 0) {
            if (addRule(line)) {
                loaded++;
            }
        }
    }

    file.close();
    std::cout << "FuzzyEngine: loaded " << loaded << " rules, "
              << variables_.size() << " variables" << std::endl;
    return true;
}

double FuzzyEngine::fuzzify(const std::string& var_name,
                            const std::string& term_name,
                            double value) const {
    auto it = variables_.find(var_name);
    if (it == variables_.end()) return 0.0;

    for (const auto& term : it->second.terms) {
        if (term.name == term_name) {
            return term.membership(value);
        }
    }
    return 0.0;
}

std::map<std::string, double> FuzzyEngine::infer(
    const std::map<std::string, double>& inputs) {

    std::map<std::string, double> result;

    if (rules_.empty() || variables_.empty()) {
        std::cerr << "FuzzyEngine: no rules or variables loaded" << std::endl;
        return result;
    }

    std::map<std::string, std::map<std::string, double>> activated_outputs;

    for (const auto& rule : rules_) {
        auto input_it = inputs.find(rule.input_var);
        if (input_it == inputs.end()) continue;

        double firing = fuzzify(rule.input_var, rule.input_term, input_it->second);
        firing *= rule.weight;

        if (firing > 0.0) {
            auto& out_terms = activated_outputs[rule.output_var];
            if (out_terms.find(rule.output_term) == out_terms.end()) {
                out_terms[rule.output_term] = firing;
            } else {
                out_terms[rule.output_term] = std::max(out_terms[rule.output_term], firing);
            }
        }
    }

    for (auto& [var_name, activated_terms] : activated_outputs) {
        result[var_name] = centroidDefuzzify(var_name, activated_terms);
    }

    return result;
}

double FuzzyEngine::centroidDefuzzify(
    const std::string& var_name,
    const std::map<std::string, double>& activated_terms) const {

    auto it = variables_.find(var_name);
    if (it == variables_.end()) return 0.0;

    const auto& var = it->second;
    if (var.max_val <= var.min_val) return 0.0;

    const int N = 100;
    double step = (var.max_val - var.min_val) / N;
    double numerator = 0.0;
    double denominator = 0.0;

    for (int i = 0; i <= N; ++i) {
        double x = var.min_val + i * step;

        double max_mu = 0.0;
        for (const auto& [term_name, strength] : activated_terms) {
            for (const auto& term : var.terms) {
                if (term.name == term_name) {
                    double mu = term.membership(x);
                    double clipped = std::min(mu, strength);
                    max_mu = std::max(max_mu, clipped);
                    break;
                }
            }
        }

        numerator += x * max_mu;
        denominator += max_mu;
    }

    if (denominator < 1e-10) return (var.min_val + var.max_val) / 2.0;
    return numerator / denominator;
}

double FuzzyEngine::defuzzify(const std::vector<double>& fuzzy_set) {
    if (fuzzy_set.empty()) return 0.0;
    double sum = 0.0;
    for (double val : fuzzy_set) {
        sum += val;
    }
    return sum / fuzzy_set.size();
}

std::vector<std::string> FuzzyEngine::getVariableNames() const {
    std::vector<std::string> names;
    for (const auto& [name, var] : variables_) {
        names.push_back(name);
    }
    return names;
}

size_t FuzzyEngine::getRuleCount() const {
    return rules_.size();
}