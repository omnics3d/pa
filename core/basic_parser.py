import sys
import os
import shutil
from dataclasses import dataclass
from typing import Optional
from core.exchange_manager import ExchangeDataManager

@dataclass
class ParserArgs:
    """Структура аргументов, выбранных пользователем."""
    exchange: str
    market: str
    tool: str

class CLIParser:
    """Класс для интерактивного выбора параметров через консоль.
    Актуально для 2026.2.
    """

    def __init__(self, manager: ExchangeDataManager):
        self.manager = manager

    def _clear_screen(self):
        """Очищает консоль."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def _move_cursor_to_bottom(self, menu_height: int):
        """Прижимает меню к нижней части экрана."""
        columns, lines = shutil.get_terminal_size()
        start_line = max(1, lines - menu_height)
        sys.stdout.write(f"\033[{start_line};1H")
        sys.stdout.flush()

    def _select_from_list(self, items: list[str], prompt: str) -> str:
        """Вспомогательный метод для выбора элемента из списка с очисткой экрана."""
        while True:
            self._clear_screen()
            # Расчет высоты: заголовок + элементы + пустая строка + ввод
            menu_h = len(items) + 4
            self._move_cursor_to_bottom(menu_h)

            print(f"--- {prompt} ---")
            for idx, item in enumerate(items, 1):
                print(f"{idx}. {item}")
            
            choice = input("\nВыберите номер (или 0 для выхода): ")
            if choice == "0":
                sys.exit(0)
            
            try:
                index = int(choice) - 1
                if 0 <= index < len(items):
                    return items[index]
            except ValueError:
                pass
            
            print("Ошибка: Неверный выбор. Попробуйте снова...")
            import time
            time.sleep(0.6)

    def parse(self) -> ParserArgs:
        """Запускает пошаговый процесс выбора параметров."""
        # 1. Выбор биржи
        exchanges = self.manager.get_exchange_names()
        if not exchanges:
            print("Ошибка: Список бирж пуст.")
            sys.exit(1)
        selected_ex = self._select_from_list(exchanges, "ВЫБОР БИРЖИ")

        # 2. Выбор рынка
        markets = self.manager.get_markets_for_exchange(selected_ex)
        if not markets:
            print(f"Ошибка: Для биржи {selected_ex} не найдены рынки.")
            sys.exit(1)
        selected_mk = self._select_from_list(markets, f"ВЫБОР РЫНКА ({selected_ex})")

        # 3. Выбор инструмента
        tools = self.manager.get_tools_for_market(selected_ex, selected_mk)
        if not tools:
            print(f"Ошибка: На рынке {selected_mk} не найдены инструменты.")
            sys.exit(1)
        selected_tl = self._select_from_list(tools, f"ВЫБОР ИНСТРУМЕНТА ({selected_mk})")

        return ParserArgs(
            exchange=selected_ex,
            market=selected_mk,
            tool=selected_tl
        )

