import importlib
import sys
import time
import os
import shutil
from core.logger_v2026_2_code import setup_logging, get_logger

setup_logging(
    level="DEBUG",
    log_files={"DEBUG": "logs/all_scripts.log"},
    json_format=True,
    use_colors=True
)

logger = get_logger("MainManager")
SCRIPTS_DIR = "tasks"

MENU_STRUCTURE = {
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

def clear_screen():
    """Очищает консоль."""
    os.system('cls' if os.name == 'nt' else 'clear')

def move_cursor_to_bottom(menu_height: int):
    """Прижимает меню к нижней части экрана."""
    columns, lines = shutil.get_terminal_size()
    start_line = max(1, lines - menu_height)
    sys.stdout.write(f"\033[{start_line};1H")
    sys.stdout.flush()

def run_task(script_name: str):
    clear_screen()
    full_module_path = f"{SCRIPTS_DIR}.{script_name}"
    try:
        logger.info(f"Запуск модуля: {full_module_path}")
        if full_module_path in sys.modules:
            module = importlib.reload(sys.modules[full_module_path])
        else:
            module = importlib.import_module(full_module_path)

        if hasattr(module, 'run'):
            module.run()
        else:
            logger.error(f"Функция run() не найдена в {full_module_path}")
    except Exception as e:
        logger.critical(f"Ошибка в {script_name}: {e}", exc_info=True)
    
    print("\n" + "-"*40)
    input("Нажмите Enter для возврата в меню...")

def main():
    try:
        while True:
            clear_screen()
            menu_h = len(MENU_STRUCTURE) + 4 
            move_cursor_to_bottom(menu_h)
            
            print(f"--- ГЛАВНОЕ МЕНЮ (2026.2) ---")
            for key, section in MENU_STRUCTURE.items():
                print(f"{key}. Раздел: {section['title']}")
            print("0. Выход")
            
            choice = input("\nВыберите раздел: ")

            if choice == "0":
                logger.info("Пользователь инициировал выход.")
                break

            if choice in MENU_STRUCTURE:
                section = MENU_STRUCTURE[choice]
                while True:
                    clear_screen()
                    sub_menu_h = len(section['scripts']) + 4
                    move_cursor_to_bottom(sub_menu_h)
                    
                    print(f"--- РАЗДЕЛ: {section['title']} ---")
                    for s_key, (s_name, s_desc) in section['scripts'].items():
                        print(f"{s_key}. {s_desc}")
                    print("0. Назад")

                    s_choice = input("\nВыберите скрипт: ")

                    if s_choice == "0":
                        break
                    
                    if s_choice in section['scripts']:
                        script_name, _ = section['scripts'][s_choice]
                        run_task(script_name)
                        break
            else:
                print("Неверный ввод...")
                time.sleep(0.5)
    
    finally:
        clear_screen()
        print("Программа завершена. Консоль очищена.")

if __name__ == "__main__":
    main()

