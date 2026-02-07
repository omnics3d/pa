# config_menu.py
"""
Конфигурация меню приложения.
"""

from typing import Final, Any
import json
import os

# Путь к JSON файлу конфигурации меню и скриптов
MENU_CONFIG_PATH: Final[str] = os.path.join("config", "menu_scripts.json")


def load_menu_config() -> dict[str, Any]:
    """
    Загружает конфигурацию меню и скриптов из JSON файла.

    Returns:
        Словарь с конфигурацией меню и скриптов
    """
    try:
        with open(MENU_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Ошибка: Файл конфигурации меню не найден: {MENU_CONFIG_PATH}")
        raise
    except json.JSONDecodeError as e:
        print(f"Ошибка: Неверный формат JSON в {MENU_CONFIG_PATH}: {e}")
        raise


# Загружаем конфигурацию меню и скриптов
menu_config = load_menu_config()

# Константы приложения из конфигурации
SCRIPTS_DIR: Final[str] = menu_config["SCRIPTS_DIR"]
MENU_STRUCTURE: Final[dict[str, dict[str, Any]]] = menu_config["MENU_STRUCTURE"]
