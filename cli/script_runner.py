# script_runner.py
"""
Модуль для динамической загрузки и выполнения скриптов.
"""
import importlib
import sys
from typing import Optional

# Абсолютные импорты
from core.logger_v2026 import get_logger
from cli.menu_manager import clear_screen

logger = get_logger("ScriptRunner")


class ScriptRunner:
    """
    Класс для управления выполнением скриптов.
    Поддерживает динамическую загрузку и горячую перезагрузку модулей.
    """
    
    def __init__(self):
        """
        Инициализация раннера скриптов.
        Теперь путь к модулю передается напрямую при запуске скрипта.
        """
        self._module_cache = {}
    
    def run_script(self, module_path: str) -> Optional[bool]:
        """
        Динамически импортирует и запускает функцию run() модуля.
        
        Args:
            module_path: Полный путь к модулю (например, "tasks.trend_validator")
            
        Returns:
            True если скрипт выполнен успешно, False при ошибке, 
            None если функция run не найдена
        """
        clear_screen()
        
        try:
            logger.info("Запуск модуля: %s", module_path)
            
            # Получаем или загружаем модуль
            module = self._load_module(module_path)
            
            # Ищем и выполняем функцию run
            return self._execute_run_function(module, module_path)
            
        except ImportError as e:
            logger.error("Модуль не найден: %s. Ошибка: %s", module_path, e)
            return False
        except Exception as e:
            logger.critical(
                "Критическая ошибка в %s: %s", 
                module_path, e, 
                exc_info=True
            )
            return False
    
    def _load_module(self, module_path: str):
        """
        Загружает модуль с поддержкой горячей перезагрузки.
        
        Args:
            module_path: Полный путь к модулю
            
        Returns:
            Загруженный модуль
        """
        if module_path in sys.modules:
            # Горячая перезагрузка для разработки
            logger.debug("Перезагрузка модуля: %s", module_path)
            return importlib.reload(sys.modules[module_path])
        else:
            logger.debug("Первая загрузка модуля: %s", module_path)
            return importlib.import_module(module_path)
    
    def _execute_run_function(self, module, module_path: str) -> Optional[bool]:
        """
        Ищет и выполняет функцию run в модуле.
        
        Args:
            module: Загруженный модуль
            module_path: Путь к модулю для логирования
            
        Returns:
            True если успешно, None если функция не найдена
        """
        run_func = getattr(module, 'run', None)
        
        if run_func and callable(run_func):
            try:
                run_func()
                logger.info("Модуль %s выполнен успешно", module_path)
                return True
            except Exception as e:
                logger.error(
                    "Ошибка выполнения run() в %s: %s", 
                    module_path, e,
                    exc_info=True
                )
                raise
        else:
            logger.error("Функция run() не найдена в %s", module_path)
            return None
    
    def wait_for_return(self) -> None:
        """
        Ожидает подтверждения пользователя для возврата в меню.
        """
        print(f"\n{'-' * 40}")
        input("Нажмите Enter для возврата в меню...")
