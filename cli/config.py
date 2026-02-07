"""
Конфигурация приложения.
"""

from typing import Final, Any

# Константы приложения
SCRIPTS_DIR: Final[str] = "tasks"

# Структура меню
MENU_STRUCTURE: Final[dict[str, dict[str, Any]]] = {
    "1": {
        "title": "СТАТИСТИКА",
        "scripts": {"1": ("trend_validator", "Trend Validator (Анализ свечей)")},
    },
    "2": {"title": "АНАЛИТИКА", "scripts": {}},
}
