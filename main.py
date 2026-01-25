# main.py
"""
Главный управляющий скрипт программы.
Точка входа в приложение.
"""

import os
import shutil

# Абсолютные импорты (явные, без реэкспорта)
from core.logger_v2026 import setup_logging, get_logger

# Импорты из cli с явным указанием модулей
from cli.config_menu import SCRIPTS_DIR, MENU_STRUCTURE
from cli.menu_manager import (
    clear_screen, 
    display_main_menu, 
    display_section_menu,
    get_user_choice,
    handle_invalid_choice
)
from cli.script_runner import ScriptRunner

# Настройка логирования
setup_logging(
    level="DEBUG",
    log_files={"DEBUG": "logs/all_scripts.log"},
    json_format=True,
    use_colors=True
)

logger = get_logger("MainManager")


def display_menu_at_bottom(menu_title, menu_items, is_main_section=False):
    """Отображает меню в нижней части экрана с позиционированием курсора."""
    # Получаем текущий размер терминала
    terminal_size = shutil.get_terminal_size()
    terminal_height = terminal_size.lines
    
    # Очищаем экран
    clear_screen()
    
    # Рассчитываем позицию для меню
    # Количество строк, которое займет меню
    menu_lines_count = 2 + len(menu_items) + 1  # заголовок + пункты + "0. Назад"
    
    # Начинаем отображение меню за (menu_lines_count) строк от низа
    # (без дополнительной строки для ввода)
    menu_start_line = terminal_height - menu_lines_count
    
    # Перемещаем курсор в начало позиции меню
    print(f"\033[{menu_start_line};0H", end="")
    
    # Отображаем меню
    print(f" --- {menu_title} ---")
    
    if is_main_section:
        # Для главного меню (разделы)
        for key, item in menu_items.items():
            print(f" {key}. {item['description']}")
    else:
        # Для подменю (скрипты)
        for key, item in menu_items.items():
            print(f" {key}. {item['description']}")
    
    print(" 0. Назад")
    
    # Перемещаем курсор на строку ввода (сразу под меню)
    print(f"\033[{terminal_height};0H", end="")


def get_user_choice_bottom(prompt):
    """Получает выбор пользователя с позиционированием внизу."""
    # Получаем размер терминала
    terminal_size = shutil.get_terminal_size()
    terminal_height = terminal_size.lines
    
    # Перемещаем курсор вниз и выводим prompt
    print(f"\033[{terminal_height - 1};0H", end="")
    choice = input(f" {prompt} ")
    
    # Возвращаем курсор на последнюю строку
    print(f"\033[{terminal_height};0H", end="")
    
    return choice.strip()


class Application:
    """
    Основной класс приложения.
    Управляет жизненным циклом и навигацией.
    """
    
    def __init__(self):
        """Инициализация приложения."""
        self.script_runner = ScriptRunner()
        self.menu_structure = MENU_STRUCTURE
    
    def run(self) -> None:
        """
        Главный цикл управления программой.
        """
        try:
            self._main_loop()
        except KeyboardInterrupt:
            logger.info("Программа остановлена пользователем.")
        except Exception as e:
            logger.critical("Неожиданная ошибка: %s", e, exc_info=True)
        finally:
            self._shutdown()
    
    def _main_loop(self) -> None:
        """Основной цикл навигации."""
        while True:
            # Главное меню - отображаем разделы внизу
            display_menu_at_bottom(
                "Главное меню",
                {key: {"description": section['title']} for key, section in self.menu_structure.items()},
                is_main_section=True
            )
            
            choice = get_user_choice_bottom("Выберите раздел:")
            
            if choice == "0":
                logger.info("Пользователь инициировал выход.")
                break
            
            if self._handle_section_choice(choice):
                continue
    
    def _handle_section_choice(self, choice: str) -> bool:
        """
        Обрабатывает выбор раздела меню.
        
        Args:
            choice: Выбор пользователя
            
        Returns:
            True если нужно продолжить цикл, False если выход
        """
        if section := self.menu_structure.get(choice):
            # Проверяем, есть ли module_path для прямого запуска
            if 'module_path' in section and not section.get('scripts'):
                # Прямой запуск скрипта
                self._execute_script(section['module_path'])
                return True  # Возврат в главное меню
            
            # Для раздела передаем его скрипты и путь
            return self._navigate_menu(section, section['title'])
        
        if choice:
            handle_invalid_choice()
        
        return True
    
    def _navigate_menu(self, menu_data: dict, menu_path: str) -> bool:
        """
        Рекурсивная навигация по меню любой вложенности.
        
        Args:
            menu_data: Данные меню
            menu_path: Текущий путь меню для отображения
            
        Returns:
            True если нужно вернуться в главное меню, False если на уровень выше
        """
        while True:
            # Отображаем меню внизу экрана
            scripts = menu_data.get('scripts', {})
            
            # Проверяем, есть ли module_path для прямого запуска (если scripts пуст)
            if not scripts and 'module_path' in menu_data:
                # Прямой запуск скрипта
                self._execute_script(menu_data['module_path'])
                return True  # Возврат в главное меню
            
            display_menu_at_bottom(menu_path, scripts)
            
            s_choice = get_user_choice_bottom("Выберите пункт:")
            
            if s_choice == "0":
                return True  # Возврат в предыдущее меню
            
            if script_data := scripts.get(s_choice):
                # Проверяем, есть ли вложенные скрипты
                if 'scripts' in script_data and script_data['scripts']:
                    # Рекурсивный вход в подменю
                    new_menu_path = f"{menu_path} → {script_data['description']}"
                    should_return_to_main = self._navigate_menu(script_data, new_menu_path)
                    
                    if should_return_to_main:
                        # Если вернулись из подменю, продолжаем в текущем
                        continue
                    else:
                        return False  # Возврат на уровень выше
                
                # Это конечный пункт с module_path
                module_path = script_data.get('module_path')
                
                if module_path:
                    self._execute_script(module_path)
                else:
                    # Получаем размер терминала для позиционирования
                    terminal_size = shutil.get_terminal_size()
                    terminal_height = terminal_size.lines
                    
                    # Перемещаем курсор вниз для сообщения
                    print(f"\033[{terminal_height - 2};0H", end="")
                    print(f" Пункт '{script_data.get('description', 'Unknown')}' не содержит исполняемого скрипта.")
                    print(f"\033[{terminal_height - 1};0H", end="")
                    input(" Нажмите Enter для продолжения...")
                
                # После выполнения остаемся в текущем меню
                continue
        
        return True
    
    def _execute_script(self, module_path: str) -> None:
        """
        Выполняет выбранный скрипт.
        
        Args:
            module_path: Полный путь к модулю (например, "tasks.trend_validator")
        """
        result = self.script_runner.run_script(module_path)
        
        if result is False:
            # Ошибка выполнения
            # Получаем размер терминала
            terminal_size = shutil.get_terminal_size()
            terminal_height = terminal_size.lines
            
            print(f"\033[{terminal_height - 2};0H", end="")
            print(" Ошибка при выполнении скрипта. Подробности в логах.")
            print(f"\033[{terminal_height - 1};0H", end="")
        
        self.script_runner.wait_for_return()
    
    def _shutdown(self) -> None:
        """Корректное завершение программы."""
        clear_screen()
        print(" Программа завершена.")
        logger.info("Приложение завершено.")


def main() -> None:
    """Точка входа в приложение."""
    app = Application()
    app.run()


if __name__ == "__main__":
    main()
