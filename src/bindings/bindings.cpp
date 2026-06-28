#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/chrono.h>
#include "../core/AntiSurgeCore.h"
#include "../core/DataProcessor.h"
#include "../core/FuzzyEngine.h"
#include "../dto/Contracts.h"

namespace py = pybind11;

PYBIND11_MODULE(fuzzy_core, m) {
    m.doc() = R"pbdoc(
        Fuzzy Core Module - Anti-surge Protection System
        =================================================
        ������ ��� ������ ������������� ��������� �� �������
        � �������������� �������� ������
    )pbdoc";

    // ��������� SensorData
    py::class_<SensorData>(m, "SensorData")
        .def(py::init<>())
        .def_readwrite("flow_rate", &SensorData::flow_rate)
        .def_readwrite("pressure_in", &SensorData::pressure_in)
        .def_readwrite("pressure_out", &SensorData::pressure_out)
        .def_readwrite("temperature", &SensorData::temperature)
        .def_readwrite("timestamp", &SensorData::timestamp);

    // ��������� ControlCommand
    py::class_<ControlCommand>(m, "ControlCommand")
        .def(py::init<>())
        .def_readwrite("bypass_valve_position", &ControlCommand::bypass_valve_position)
        .def_readwrite("alarm_status", &ControlCommand::alarm_status)
        .def_readwrite("timestamp", &ControlCommand::timestamp);

    // ����� AntiSurgeCore
    py::class_<AntiSurgeCore>(m, "AntiSurgeCore")
        .def(py::init<>())
        .def("initialize", &AntiSurgeCore::initialize,
            "������������� ������� ������",
            py::arg("config_path"))
        .def("process_sensor_data", &AntiSurgeCore::processSensorData,
            "��������� ������ � ��������",
            py::arg("sensor_data"))
        .def("get_control_command", &AntiSurgeCore::getControlCommand,
            "��������� ����������� �������")
        .def("is_surge_detected", &AntiSurgeCore::isSurgeDetected,
            "�������� ������� �������")
        .def("get_system_status", &AntiSurgeCore::getSystemStatus,
            "��������� ������� �������");

    // ����� DataProcessor
    py::class_<DataProcessor>(m, "DataProcessor")
        .def(py::init<>())
        .def("filter_noise", &DataProcessor::filterNoise,
            "���������� �����",
            py::arg("data"))
        .def("calculate_derivative", &DataProcessor::calculateDerivative,
            "������ �����������",
            py::arg("data"))
        .def("smooth_data", &DataProcessor::smoothData,
            "����������� ������",
            py::arg("data"),
            py::arg("window_size") = 5);

    // ����� FuzzyEngine
    py::class_<FuzzyEngine>(m, "FuzzyEngine")
        .def(py::init<>())
        .def("load_rules", &FuzzyEngine::loadRules,
            "Загрузка правил из файла",
            py::arg("rules_file"))
        .def("infer", &FuzzyEngine::infer,
            "Нечеткий вывод",
            py::arg("inputs"))
        .def("defuzzify", &FuzzyEngine::defuzzify,
            "Дефаззификация результата",
            py::arg("fuzzy_set"))
        .def("add_rule", py::overload_cast<const std::string&>(&FuzzyEngine::addRule),
            "Добавление правила из строки",
            py::arg("rule"))
        .def("add_rule_struct", py::overload_cast<const FuzzyRule&>(&FuzzyEngine::addRule),
            "Добавление правила (структура)",
            py::arg("rule"));

#ifdef VERSION_INFO
    m.attr("__version__") = VERSION_INFO;
#else
    m.attr("__version__") = "dev";
#endif
}