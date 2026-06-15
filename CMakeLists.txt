cmake_minimum_required(VERSION 3.15)
project(AntiSurgeCore LANGUAGES CXX)

# Указываем стандарт C++
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Находим pybind11 (должен быть установлен через pip install pybind11)
find_package(pybind11 REQUIRED)

# Объявляем наш C++ модуль как библиотеку для Python
pybind11_add_module(fuzzy_core
    # Файл с привязками pybind11
    src/bindings/bindings.cpp
    
    # Исходники вашего ядра
    src/core/AntiSurgeCore.cpp
    src/core/DataProcessor.cpp
    src/core/FuzzyEngine.cpp
)

# Указываем, где искать заголовочные файлы (.h), если они есть в src/core и src/dto
target_include_directories(fuzzy_core PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/src/core
    ${CMAKE_CURRENT_SOURCE_DIR}/src/dto
)

# Настраиваем вывод скомпилированного файла (.pyd для Windows) 
# прямо в папку src/ui, чтобы Python мог его импортировать
set_target_properties(fuzzy_core PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/src/ui"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/src/ui"
)