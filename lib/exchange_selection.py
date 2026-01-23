import sys
import os
import shutil

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from exchange_config_loader import get_full_names_of_all_exchanges, get_full_names_of_all_markets, get_names_all_tools


class ExchangeMenu:
    """Класс для отображения меню выбора бирж, рынков и инструментов."""
    
    def __init__(self):
        self.selection = {"exchange": "", "market": "", "tool": ""}
    
    def _clear_screen(self):
        """Очистить экран."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def _display_at_bottom(self, lines: list[str]):
        """Отобразить строки в левом нижнем углу экрана со сдвигом на 1 позицию вверх."""
        # Очищаем экран
        self._clear_screen()
        
        # Добавляем 10 пустых строк
        for _ in range(10):
            print()
        
        try:
            # Получаем размер терминала
            _, terminal_lines = shutil.get_terminal_size()
            menu_height = len(lines) + 1  # +1 для пустой строки в начале
            
            # Вычисляем начальную строку (сдвиг на 1 вверх: -1)
            start_line = max(1, terminal_lines - menu_height - 1)
            
            # Перемещаем курсор
            sys.stdout.write(f"\033[{start_line};1H")
            
            # Выводим строки меню с пробелом в начале каждой строки
            for line in lines:
                print(" " + line)
            
            sys.stdout.flush()
        except Exception:
            # Если не удалось определить размер терминала, выводим обычным способом
            for line in lines:
                print(" " + line)
    
    def display_exchanges(self):
        """Отобразить меню выбора бирж."""
        exchanges = get_full_names_of_all_exchanges()
        
        menu_lines = [
            "--- ВЫБОР БИРЖИ ---"
        ]
        
        for i, exchange in enumerate(exchanges, 1):
            menu_lines.append(f"{i}. {exchange}")
        
        menu_lines.append("0. Назад")
        
        self._display_at_bottom(menu_lines)
        
        try:
            choice = int(input("\n Выберите пункт: "))
            if choice == 0:
                return None
            elif 1 <= choice <= len(exchanges):
                selected_exchange = exchanges[choice-1]
                self.selection["exchange"] = selected_exchange
                result = self.display_markets(selected_exchange)
                if result is None:
                    return None
                return self.selection
            else:
                print("Неверный выбор")
                return self.display_exchanges()
        except ValueError:
            print("Введите число")
            return self.display_exchanges()
    
    def display_markets(self, exchange: str):
        """Отобразить меню выбора рынков для выбранной биржи."""
        markets = get_full_names_of_all_markets(exchange)
        
        menu_lines = [
            f"--- ВЫБОР РЫНКА (Биржа: {exchange}) ---"
        ]
        
        for i, market in enumerate(markets, 1):
            menu_lines.append(f"{i}. {market}")
        
        menu_lines.append("0. Назад")
        
        self._display_at_bottom(menu_lines)
        
        try:
            choice = int(input("\n Выберите пункт: "))
            if choice == 0:
                return self.display_exchanges()
            elif 1 <= choice <= len(markets):
                selected_market = markets[choice-1]
                self.selection["market"] = selected_market
                result = self.display_tools(exchange, selected_market)
                if result is None:
                    return None
                return self.selection
            else:
                print("Неверный выбор рынка")
                return self.display_markets(exchange)
        except ValueError:
            print("Введите число")
            return self.display_markets(exchange)
    
    def display_tools(self, exchange: str, market: str):
        """Отобразить меню выбора инструментов для выбранного рынка."""
        tools = get_names_all_tools(exchange, market)
        
        menu_lines = [
            f"--- ВЫБОР ИНСТРУМЕНТА (Биржа: {exchange}, Рынок: {market}) ---"
        ]
        
        for i, tool in enumerate(tools, 1):
            menu_lines.append(f"{i}. {tool}")
        
        menu_lines.append("0. Назад")
        
        self._display_at_bottom(menu_lines)
        
        try:
            choice = int(input("\n Выберите пункт: "))
            if choice == 0:
                return self.display_markets(exchange)
            elif 1 <= choice <= len(tools):
                selected_tool = tools[choice-1]
                self.selection["tool"] = selected_tool
                return self.selection
            else:
                print("Неверный выбор инструмента")
                return self.display_tools(exchange, market)
        except ValueError:
            print("Введите число")
            return self.display_tools(exchange, market)


if __name__ == "__main__":
    menu = ExchangeMenu()
    result = menu.display_exchanges()
    if result is None:
        print("\nВыбор отменен")
    else:
        print(f"\nВыбран: {result}")
