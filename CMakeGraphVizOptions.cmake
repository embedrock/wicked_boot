# CMakeGraphVizOptions.cmake
# Настройки для генерации графа зависимостей через Graphviz

# 1. Визуальное оформление графа
# rankdir=LR делает граф слева-направо (читается лучше, чем стандартный сверху-вниз)
# splines=true делает линии изогнутыми, что сильно уменьшает визуальное перекрытие узлов
# fontsize и fontname улучшают читаемость
set(GRAPHVIZ_GRAPH_HEADER "node [fontsize=11, fontname=\"Helvetica\"]; graph [rankdir=LR, overlap=false, splines=true];")

# 2. Фильтрация целей (Regex)
# Исключаем цели, которые засоряют архитектурный граф, но не являются частью прошивки
set(GRAPHVIZ_IGNORE_TARGETS
    ".*test.*"       # Все цели с словом test (например, run_test)
    ".*unity.*"      # Цели фреймворка Unity
    ".*cmock.*"      # Цели фреймворка CMock
    ".*ceedling.*"   # Цели сборщика Ceedling
    "flash"          # Утилитарные цели
    "size"
    "clean"
    "docs"
)

# 3. Управление типами отображаемых библиотек
# Оставляем только то, что формирует реальный бинарный образ
set(GRAPHVIZ_EXECUTABLES TRUE)       # Показывать исполняемые файлы (например, main_app, CanTester)
set(GRAPHVIZ_STATIC_LIBS TRUE)       # Показывать статические библиотеки (основа embedded-архитектуры)
set(GRAPHVIZ_OBJECT_LIBS TRUE)       # Показывать объектные библиотеки (удобно для группировки исходников без линковки)
set(GRAPHVIZ_INTERFACE_LIBS TRUE)    # Показывать интерфейсные библиотеки (важно для контроля PUBLIC/PRIVATE заголовков)
set(GRAPHVIZ_EXTERNAL_LIBS TRUE)     # Показывать внешние зависимости (FreeRTOS, HAL, драйверы из подмодулей)
set(GRAPHVIZ_SHARED_LIBS FALSE)      # В embedded shared libs используются крайне редко, можно скрыть
set(GRAPHVIZ_MODULE_LIBS FALSE)      # Аналогично
set(GRAPHVIZ_UNKNOWN_LIBS FALSE)     # Скрыть нераспознанные цели, чтобы не было мусора
set(GRAPHVIZ_CUSTOM_TARGETS FALSE)   # Скрыть add_custom_target, если они не являются библиотеками

# 4. Оптимизация вывода (чтобы не генерировать кучу лишних файлов)
# Отключаем генерацию отдельного .dot файла для каждого таргета и файла dependers
# Оставляем только один общий граф, который ты чистишь через sed
set(GRAPHVIZ_GENERATE_PER_TARGET FALSE)
set(GRAPHVIZ_GENERATE_DEPENDERS FALSE)
