#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/chrono.h>  // ВАЖНО: для поддержки std::chrono

#include "../core/AntiSurgeCore.h"
#include "../core/DataProcessor.h"
#include "../core/FuzzyEngine.h"
#include "../dto/Contracts.h"

namespace py = pybind11;

PYBIND11_MODULE(fuzzy_core, m) {
    m.doc() = R"pbdoc(
        Fuzzy Core Module - Anti-surge Protection System
        =================================================
        Модуль для защиты компрессорных установок от помпажа
        с использованием нечеткой логики
    )pbdoc";

    // Структура SensorData
    py::class_<SensorData>(m, "SensorData")
        .def(py::init<>())
        .def_readwrite("flow_rate", &SensorData::flow_rate)
        .def_readwrite("pressure_in", &SensorData::pressure_in)
        .def_readwrite("pressure_out", &SensorData::pressure_out)
        .def_readwrite("temperature", &SensorData::temperature)
        .def_readwrite("timestamp", &SensorData::timestamp);

    // Структура ControlCommand
    py::class_<ControlCommand>(m, "ControlCommand")
        .def(py::init<>())
        .def_readwrite("bypass_valve_position", &ControlCommand::bypass_valve_position)
        .def_readwrite("alarm_status", &ControlCommand::alarm_status)
        .def_readwrite("timestamp", &ControlCommand::timestamp);

    // Класс AntiSurgeCore
    py::class_<AntiSurgeCore>(m, "AntiSurgeCore")
        .def(py::init<>())
        .def("initialize", &AntiSurgeCore::initialize,
            "Инициализация системы защиты",
            py::arg("config_path"))
        .def("process_sensor_data", &AntiSurgeCore::processSensorData,
            "Обработка данных с датчиков",
            py::arg("sensor_data"))
        .def("get_control_command", &AntiSurgeCore::getControlCommand,
            "Получение управляющей команды")
        .def("is_surge_detected", &AntiSurgeCore::isSurgeDetected,
            "Проверка наличия помпажа")
        .def("get_system_status", &AntiSurgeCore::getSystemStatus,
            "Получение статуса системы");

    // Класс DataProcessor
    py::class_<DataProcessor>(m, "DataProcessor")
        .def(py::init<>())
        .def("filter_noise", &DataProcessor::filterNoise,
            "Фильтрация шумов",
            py::arg("data"))
        .def("calculate_derivative", &DataProcessor::calculateDerivative,
            "Расчет производной",
            py::arg("data"))
        .def("smooth_data", &DataProcessor::smoothData,
            "Сглаживание данных",
            py::arg("data"),
            py::arg("window_size") = 5);

    // Класс FuzzyEngine
    py::class_<FuzzyEngine>(m, "FuzzyEngine")
        .def(py::init<>())
        .def("load_rules", &FuzzyEngine::loadRules,
            "Загрузка правил нечеткого вывода",
            py::arg("rules_file"))
        .def("infer", &FuzzyEngine::infer,
            "Нечеткий вывод",
            py::arg("inputs"))
        .def("defuzzify", &FuzzyEngine::defuzzify,
            "Дефаззификация результата",
            py::arg("fuzzy_set"))
        .def("add_rule", &FuzzyEngine::addRule,
            "Добавление правила",
            py::arg("rule"));

#ifdef VERSION_INFO
    m.attr("__version__") = VERSION_INFO;
#else
    m.attr("__version__") = "dev";
#endif
}