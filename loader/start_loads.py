#{{{
""" start_loads.py - загрузчик данных ByBit """
#}}}

import sys
import os
import subprocess

class StartLoads:
    """Класс для запуска загрузки данных"""
    
    def __init__(self):
        pass
    
    def run(self):
        """Основной метод запуска"""
        self._run_loads()
    
    def _run_loads(self):
        """Логика запуска загрузки"""
        # Добавляем родительскую папку в путь для импорта
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

        # Импортируем ExchangeMenu из папки lib
        from lib.exchange_selection import ExchangeMenu

        # Создаем меню и получаем выбор
        menu = ExchangeMenu()
        result = menu.display_exchanges()

        if result is None:
            print("Выбор отменен")
            return
        
        print(f"Полученный словарь: {result}")
        
        # Если выбрана биржа bybit
        if result.get("exchange", "").lower() == "bybit":
            # Формируем аргументы для запуска скрипта load_bybit.py
            exchange = result.get("exchange", "")
            market = result.get("market", "")
            tool = result.get("tool", "")
            
            # Путь к файлу load_bybit.py
            load_bybit_path = os.path.join(os.path.dirname(__file__), 'load_bybit.py')
            
            # Устанавливаем рабочую директорию на родительскую папку
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Запускаем скрипт с параметрами
            command = [
                sys.executable,
                load_bybit_path,
                "-e", exchange,
                "-m", market,
                "-t", tool
            ]
            
            print(f"Запуск: {' '.join(command)}")
            print(f"Рабочая директория: {parent_dir}")
            
            # Запускаем с правильной рабочей директорией
            subprocess.run(command, cwd=parent_dir)
        else:
            print(f"Биржа {result.get('exchange', '')} пока не поддерживается")

# Создаем экземпляр для импорта
start_loads = StartLoads()

# Функция для совместимости
def run():
    """Функция для вызова меню-системой"""
    start_loads.run()

def main():
    """Функция для прямого запуска"""
    run()

if __name__ == "__main__":
    main()
#}}}
