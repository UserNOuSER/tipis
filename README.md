# Система нечеткого антипомпажного регулирования центробежного компрессора

## 📌 О проекте
Программный комплекс для предотвращения помпажа центробежного компрессора на основе нечеткой логики (метод Мамдани).  
Реализует вычислительное ядро на C++ (≤10 мс на цикл), интерфейс оператора на Python (DearPyGUI) и локальную реляционную БД (SQLite).

## 🛠 Стек
| Компонент | Технология |
|-----------|------------|
| Ядро | C++17, CMake, pybind11 |
| Интерфейс | Python 3.10+, DearPyGUI, SQLAlchemy |
| БД | SQLite |
| Управление версиями | Git, Git Flow, Conventional Commits |

## 🚀 Быстрый старт
```bash
# 1. Клонирование
git clone <url> && cd <repo>

# 2. Python-окружение
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Сборка ядра
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --config Release

# 4. Запуск
cd ../src
python main.py
```
##  Тест мощности
```bash
cd ../tests

python /ui/test_gui_performance.py

python /core/test_performance.py 