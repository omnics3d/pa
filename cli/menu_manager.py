# menu_manager.py
"""
Модуль управления консольным меню.
Отвечает за отображение и навигацию по меню.
"""

import os
import shutil
import sys
import time
from typing import Any, Dict

# Абсолютный импорт
from core.logger_v2026 import get_logger
from cli.config_menu import MENU_STRUCTURE

logger = get_logger("MenuManager")


def clear_screen() -> None:
    """
    Очищает консоль терминала.
    Кросс-платформенная реализация.
    """
    os.system("cls" if os.name == "nt" else "clear")


def move_cursor_to_bottom(menu_height: int) -> None:
    """
    Смещает курсор и отображение меню к нижней части экрана.

    Args:
        menu_height: Высота меню в строках
    """
    try:
        _, lines = shutil.get_terminal_size()
        start_line = max(1, lines - menu_height)
        sys.stdout.write(f"\033[{start_line};1H")
        sys.stdout.flush()
    except Exception as e:
        logger.warning("Не удалось определить размер терминала: %s", e)


def display_main_menu() -> None:
    """
    Отображает главное меню программы.
    """
    menu_height = len(MENU_STRUCTURE) + 6
    move_cursor_to_bottom(menu_height)

    print("--- ГЛАВНОЕ МЕНЮ (2026.2) ---")
    for key, section in MENU_STRUCTURE.items():
        print(f"{key}. Раздел: {section['title']}")
    print("0. Выход")


def display_section_menu(
    section_title: str, scripts: Dict[str, Dict[str, str]]
) -> None:
    """
    Отображает меню раздела со скриптами.

    Args:
        section_title: Название раздела
        scripts: Словарь скриптов {key: {module_path: str, description: str}}
    """
    sub_menu_h = len(scripts) + 6
    move_cursor_to_bottom(sub_menu_h)

    print(f"--- РАЗДЕЛ: {section_title} ---")
    for s_key, script_info in scripts.items():
        print(f"{s_key}. {script_info['description']}")
    print("0. Назад")


def get_user_choice(prompt: str = "\nВыберите пункт: ") -> str:
    """
    Получает выбор пользователя с базовой валидацией.

    Args:
        prompt: Приглашение для ввода

    Returns:
        Очищенная строка выбора пользователя
    """
    try:
        choice = input(prompt).strip()
        return choice
    except (EOFError, KeyboardInterrupt):
        logger.debug("Пользователь прервал ввод")
        return "0"


def handle_invalid_choice() -> None:
    """
    Обработка неверного выбора пользователя.
    """
    print("Ошибка: неверный пункт.")
    time.sleep(0.5)
