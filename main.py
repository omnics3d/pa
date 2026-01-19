"""
Главный управляющий скрипт программы.
Точка входа в приложение.
"""

# Абсолютные импорты (явные, без реэкспорта)
from core.logger_v2026 import setup_logging, get_logger

# Импорты из cli с явным указанием модулей
from cli.config import SCRIPTS_DIR, MENU_STRUCTURE
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


class Application:
    """
    Основной класс приложения.
    Управляет жизненным циклом и навигацией.
    """
    
    def __init__(self):
        """Инициализация приложения."""
        self.script_runner = ScriptRunner(SCRIPTS_DIR)
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
            clear_screen()
            display_main_menu(self.menu_structure)
            
            choice = get_user_choice("\nВыберите раздел: ")
            
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
            return self._section_navigation(section)
        
        if choice:
            handle_invalid_choice()
        
        return True
    
    def _section_navigation(self, section: dict) -> bool:
        """
        Навигация внутри раздела меню.
        
        Args:
            section: Данные раздела
            
        Returns:
            True если нужно вернуться в главное меню
        """
        while True:
            clear_screen()
            scripts = section['scripts']
            display_section_menu(section['title'], scripts)
            
            s_choice = get_user_choice("\nВыберите скрипт: ")
            
            if s_choice == "0":
                return True  # Возврат в главное меню
            
            if script_data := scripts.get(s_choice):
                script_name, _ = script_data
                self._execute_script(script_name)
                break
        
        return True
    
    def _execute_script(self, script_name: str) -> None:
        """
        Выполняет выбранный скрипт.
        
        Args:
            script_name: Имя скрипта для выполнения
        """
        result = self.script_runner.run_script(script_name)
        
        if result is False:
            # Ошибка выполнения
            print("\nОшибка при выполнении скрипта. Подробности в логах.")
        
        self.script_runner.wait_for_return()
    
    def _shutdown(self) -> None:
        """Корректное завершение программы."""
        clear_screen()
        print("Программа завершена.")
        logger.info("Приложение завершено.")


def main() -> None:
    """Точка входа в приложение."""
    app = Application()
    app.run()


if __name__ == "__main__":
    main()

