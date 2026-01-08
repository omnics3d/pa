import importlib
import os
import shutil
import sys
import time
from typing import Final, Any

# Локальные импорты
from core.logger_v2026_2_code import setup_logging, get_logger

# Константы (PEP 8: до 79 символов)
SCRIPTS_DIR: Final[str] = "tasks"
MENU_STRUCTURE: Final[dict[str, dict[str, Any]]] = {
    "1": {
        "title": "СТАТИСТИКА",
        "scripts": {
            "1": ("trend_validator", "Trend Validator (Анализ свечей)")
        }
    },
    "2": {
        "title": "АНАЛИТИКА",
        "scripts": {}
    }
}

setup_logging(
    level="DEBUG",
    log_files={"DEBUG": "logs/all_scripts.log"},
    json_format=True,
    use_colors=True
)

logger = get_logger("MainManager")


def clear_screen() -> None:
    """Очищает консоль терминала."""
    os.system('cls' if os.name == 'nt' else 'clear')


def move_cursor_to_bottom(menu_height: int) -> None:
    """Смещает меню к нижней части экрана."""
    _, lines = shutil.get_terminal_size()
    start_line = max(1, lines - menu_height)
    sys.stdout.write(f"\033[{start_line};1H")
    sys.stdout.flush()


def run_task(script_name: str) -> None:
    """Динамически импортирует и запускает функцию run() модуля."""
    clear_screen()
    module_path: str = f"{SCRIPTS_DIR}.{script_name}"

    try:
        logger.info("Запуск модуля: %s", module_path)

        if module_path in sys.modules:
            module = importlib.reload(sys.modules[module_path])
        else:
            module = importlib.import_module(module_path)

        if (run_func := getattr(module, 'run', None)) and callable(run_func):
            run_func()
        else:
            logger.error("Функция run() не найдена в %s", module_path)

    except Exception as e:
        logger.critical(
            "Ошибка в %s: %s", script_name, e, exc_info=True
        )

    print(f"\n{'-' * 40}")
    input("Нажмите Enter для возврата в меню...")


def main() -> None:
    """Главный цикл управления программой."""
    try:
        while True:
            clear_screen()
            menu_h = len(MENU_STRUCTURE) + 6
            move_cursor_to_bottom(menu_h)

            print("--- ГЛАВНОЕ МЕНЮ (2026.2) ---")
            for key, section in MENU_STRUCTURE.items():
                print(f"{key}. Раздел: {section['title']}")
            print("0. Выход")

            choice = input("\nВыберите раздел: ").strip()

            if choice == "0":
                logger.info("Пользователь инициировал выход.")
                break

            if section := MENU_STRUCTURE.get(choice):
                while True:
                    clear_screen()
                    scripts = section['scripts']
                    sub_menu_h = len(scripts) + 6
                    move_cursor_to_bottom(sub_menu_h)

                    print(f"--- РАЗДЕЛ: {section['title']} ---")
                    for s_key, (_, s_desc) in scripts.items():
                        print(f"{s_key}. {s_desc}")
                    print("0. Назад")

                    s_choice = input("\nВыберите скрипт: ").strip()

                    if s_choice == "0":
                        break

                    if script_data := scripts.get(s_choice):
                        script_name, _ = script_data
                        run_task(script_name)
                        break
            else:
                if choice:
                    print("Ошибка: неверный пункт.")
                    time.sleep(0.5)

    except KeyboardInterrupt:
        logger.info("Программа остановлена пользователем.")
    finally:
        clear_screen()
        print("Программа завершена.")


if __name__ == "__main__":
    main()

