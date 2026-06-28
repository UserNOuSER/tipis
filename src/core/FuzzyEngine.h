#pragma once
#include <string>
#include <vector>
#include <map>
#include <functional>

enum class MembershipType {
    Triangular,
    Trapezoidal,
    Gaussian
};

struct FuzzySet {
    std::string name;
    MembershipType type;
    std::vector<double> params;

    double membership(double x) const;
};

struct LinguisticVariable {
    std::string name;
    double min_val;
    double max_val;
    std::vector<FuzzySet> terms;
};

struct FuzzyRule {
    std::string input_var;
    std::string input_term;
    std::string output_var;
    std::string output_term;
    double weight = 1.0;
};

class FuzzyEngine {
public:
    FuzzyEngine();

    bool loadRules(const std::string& rules_file);
    std::map<std::string, double> infer(const std::map<std::string, double>& inputs);
    double defuzzify(const std::vector<double>& fuzzy_set);
    bool addRule(const std::string& rule);

    void addVariable(const LinguisticVariable& var);
    void addRule(const FuzzyRule& rule);
    double fuzzify(const std::string& var_name, const std::string& term_name, double value) const;
    std::vector<std::string> getVariableNames() const;
    size_t getRuleCount() const;

private:
    std::map<std::string, LinguisticVariable> variables_;
    std::vector<FuzzyRule> rules_;

    double centroidDefuzzify(const std::string& var_name,
                             const std::map<std::string, double>& activated_terms) const;
};