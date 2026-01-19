"""
Модуль управления консольным меню.
Отвечает за отображение и навигацию по меню.
"""
import os
import shutil
import sys
import time
from typing import Any, Tuple

# Абсолютный импорт
from core.logger_v2026 import get_logger

logger = get_logger("MenuManager")


def clear_screen() -> None:
    """
    Очищает консоль терминала.
    Кросс-платформенная реализация.
    """
    os.system('cls' if os.name == 'nt' else 'clear')


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


def display_main_menu(menu_structure: dict[str, dict[str, Any]]) -> None:
    """
    Отображает главное меню программы.
    
    Args:
        menu_structure: Структура меню
    """
    menu_height = len(menu_structure) + 6
    move_cursor_to_bottom(menu_height)
    
    print("--- ГЛАВНОЕ МЕНЮ (2026.2) ---")
    for key, section in menu_structure.items():
        print(f"{key}. Раздел: {section['title']}")
    print("0. Выход")


def display_section_menu(
    section_title: str, 
    scripts: dict[str, Tuple[str, str]]
) -> None:
    """
    Отображает меню раздела со скриптами.
    
    Args:
        section_title: Название раздела
        scripts: Словарь скриптов {key: (script_name, description)}
    """
    sub_menu_h = len(scripts) + 6
    move_cursor_to_bottom(sub_menu_h)
    
    print(f"--- РАЗДЕЛ: {section_title} ---")
    for s_key, (_, s_desc) in scripts.items():
        print(f"{s_key}. {s_desc}")
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

