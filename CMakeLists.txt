cmake_minimum_required(VERSION 3.18)
project(AntiSurgeControl VERSION 1.0.0 LANGUAGES CXX)

# === Базовые настройки компилятора ===
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)  # Обязательно для shared-модулей и pybind11

# Режим сборки по умолчанию: Release (для достижения ≤10 мс на цикл)
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

# === Подключение pybind11 (автоматическая загрузка) ===
include(FetchContent)
FetchContent_Declare(
    pybind11
    GIT_REPOSITORY https://github.com/pybind/pybind11.git
    GIT_TAG        v2.12.0  # Стабильная версия, проверенная с Python 3.10+
)
FetchContent_MakeAvailable(pybind11)

# === Вычислительное ядро (C++) ===
# Перечислите все .cpp файлы ядра. В реальном проекте лучше использовать file(GLOB ...)
# или явно прописывать пути для контроля зависимостей.
add_library(core_lib STATIC
    src/core/DataProcessor.cpp
    src/core/FuzzyEngine.cpp
    src/core/AntiSurgeCore.cpp
    # Добавьте остальные файлы ядра при появлении
)

target_include_directories(core_lib PUBLIC
    ${CMAKE_SOURCE_DIR}/src/core/include
)

# Оптимизация для Release (уберите, если мешает отладке)
target_compile_options(core_lib PRIVATE
    $<$<CONFIG:Release>:-O3 -march=native -ffast-math>
)

# === Python-модуль (pybind11 обёртка) ===
pybind11_add_module(anti_surge_core src/bindings/module.cpp)

target_link_libraries(anti_surge_core PRIVATE core_lib)

# Указываем, куда класть скомпилированный .so / .pyd файл
set(PYTHON_MODULE_DIR ${CMAKE_SOURCE_DIR}/python_pkg)
set_target_properties(anti_surge_core PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY ${PYTHON_MODULE_DIR}
    RUNTIME_OUTPUT_DIRECTORY ${PYTHON_MODULE_DIR}
    OUTPUT_NAME anti_surge_core  # Имя для import anti_surge_core
)

# === Опционально: SQLite (если ядро работает с БД напрямую) ===
# find_package(SQLite3 REQUIRED)
# target_link_libraries(core_lib PRIVATE SQLite::SQLite3)

# === Информация при конфигурации ===
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "C++ Compiler: ${CMAKE_CXX_COMPILER_ID} ${CMAKE_CXX_COMPILER_VERSION}")
message(STATUS "Python module will be placed in: ${PYTHON_MODULE_DIR}")