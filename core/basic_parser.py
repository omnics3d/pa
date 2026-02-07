"""
Интерактивный парсер аргументов командной строки для выбора биржевых данных.

Модуль предоставляет CLI-интерфейс для пошагового выбора:
1. Биржи
2. Рынка
3. Инструмента

Принципы SOLID соблюдены, каждый класс имеет одну ответственность.
"""

import sys
import os
import shutil
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from core.exchange_manager import ExchangeDataManager


@dataclass
class ParserArgs:
    """Структура аргументов, выбранных пользователем."""

    exchange: str
    market: str
    tool: str


class ExchangeDataError(Exception):
    """Исключение для ошибок данных биржи."""

    pass


class DisplayManager:
    """Отвечает только за управление отображением в консоли."""

    @staticmethod
    def clear_screen() -> None:
        """Очищает консоль."""
        os.system("cls" if os.name == "nt" else "clear")

    @staticmethod
    def move_cursor_to_bottom(menu_height: int) -> None:
        """Прижимает меню к нижней части экрана."""
        _, lines = shutil.get_terminal_size()
        start_line = max(1, lines - menu_height)
        with open("/dev/stdout", "w", encoding="utf-8") as stdout:
            stdout.write(f"\033[{start_line};1H")
            stdout.flush()


class ListSelector:
    """Отвечает только за выбор элементов из списка."""

    ERROR_MESSAGE_DELAY = 0.6

    def __init__(self, display_manager: DisplayManager) -> None:
        """Инициализирует селектор с менеджером отображения."""
        self.display = display_manager

    def select_item(
        self,
        items: list[str],
        prompt: str,
        exit_allowed: bool = True,
    ) -> str:
        """
        Выбирает элемент из списка.

        Args:
            items: Список элементов для выбора
            prompt: Текст подсказки для пользователя
            exit_allowed: Разрешает ли выход по "0"

        Returns:
            Выбранный элемент из списка

        Raises:
            SystemExit: Если пользователь выбрал выход (0)
        """
        while True:
            self.display.clear_screen()
            menu_height = len(items) + 4
            self.display.move_cursor_to_bottom(menu_height)

            print(f"--- {prompt} ---")
            for idx, item in enumerate(items, 1):
                print(f"{idx}. {item}")

            exit_text = " (или 0 для выхода)" if exit_allowed else ""
            choice = input(f"\nВыберите номер{exit_text}: ")

            if exit_allowed and choice == "0":
                sys.exit(0)

            try:
                index = int(choice) - 1
                if 0 <= index < len(items):
                    return items[index]
            except (ValueError, IndexError):
                pass

            error_msg = "Ошибка: Неверный выбор. Попробуйте снова..."
            print(error_msg)
            time.sleep(self.ERROR_MESSAGE_DELAY)


class DataValidator:
    """Отвечает только за валидацию данных биржи."""

    @staticmethod
    def validate_exchanges(exchanges: list[str]) -> None:
        """Проверяет список бирж."""
        if not exchanges:
            raise ExchangeDataError("Список бирж пуст.")

    @staticmethod
    def validate_markets(exchange: str, markets: list[str]) -> None:
        """Проверяет список рынков для биржи."""
        if not markets:
            msg = f"Для биржи {exchange} не найдены рынки."
            raise ExchangeDataError(msg)

    @staticmethod
    def validate_tools(market: str, tools: list[str]) -> None:
        """Проверяет список инструментов для рынка."""
        if not tools:
            msg = f"На рынке {market} не найдены инструменты."
            raise ExchangeDataError(msg)


class SelectionStep(ABC):
    """Абстрактный класс для шага выбора."""

    @abstractmethod
    def execute(self, context: dict) -> tuple[str, dict]:
        """Выполняет шаг выбора и возвращает результат и контекст."""
        pass


class ExchangeSelectionStep(SelectionStep):
    """Шаг выбора биржи."""

    def __init__(
        self,
        manager: ExchangeDataManager,
        selector: ListSelector,
        validator: DataValidator,
    ) -> None:
        self.manager = manager
        self.selector = selector
        self.validator = validator

    def execute(self, context: dict) -> tuple[str, dict]:
        """Выполняет выбор биржи."""
        exchanges = self.manager.get_exchange_names()
        self.validator.validate_exchanges(exchanges)

        selected = self.selector.select_item(exchanges, "ВЫБОР БИРЖИ")

        context["exchange"] = selected
        context["exchange_step_completed"] = True
        return selected, context


class MarketSelectionStep(SelectionStep):
    """Шаг выбора рынка."""

    def __init__(
        self,
        manager: ExchangeDataManager,
        selector: ListSelector,
        validator: DataValidator,
    ) -> None:
        self.manager = manager
        self.selector = selector
        self.validator = validator

    def execute(self, context: dict) -> tuple[str, dict]:
        """Выполняет выбор рынка."""
        exchange = context.get("exchange")
        if not exchange:
            raise ValueError("Не выбрана биржа для получения рынков")

        markets = self.manager.get_markets_for_exchange(exchange)
        self.validator.validate_markets(exchange, markets)

        prompt = f"ВЫБОР РЫНКА ({exchange})"
        selected = self.selector.select_item(markets, prompt)

        context["market"] = selected
        context["market_step_completed"] = True
        return selected, context


class ToolSelectionStep(SelectionStep):
    """Шаг выбора инструмента."""

    def __init__(
        self,
        manager: ExchangeDataManager,
        selector: ListSelector,
        validator: DataValidator,
    ) -> None:
        self.manager = manager
        self.selector = selector
        self.validator = validator

    def execute(self, context: dict) -> tuple[str, dict]:
        """Выполняет выбор инструмента."""
        exchange = context.get("exchange")
        market = context.get("market")

        if not exchange or not market:
            msg = "Не выбраны биржа и рынок для получения инструментов"
            raise ValueError(msg)

        tools = self.manager.get_tools_for_market(exchange, market)
        self.validator.validate_tools(market, tools)

        prompt = f"ВЫБОР ИНСТРУМЕНТА ({market})"
        selected = self.selector.select_item(tools, prompt)

        context["tool"] = selected
        context["tool_step_completed"] = True
        return selected, context


class SelectionOrchestrator:
    """Оркестратор процесса выбора."""

    def __init__(self, steps: list[SelectionStep]) -> None:
        """Инициализирует оркестратор с последовательностью шагов."""
        self.steps = steps

    def execute(self) -> dict:
        """Выполняет все шаги выбора в последовательности."""
        context = {}

        for step in self.steps:
            _, context = step.execute(context)

        return context


class CLIParser:
    """
    Основной класс CLI парсера.

    Отвечает за инициализацию компонентов и запуск процесса выбора.
    """

    def __init__(self, manager: ExchangeDataManager) -> None:
        """Инициализирует парсер с менеджером данных биржи."""
        self.manager = manager
        self.display_manager: DisplayManager = DisplayManager()
        self.selector: ListSelector = ListSelector(self.display_manager)
        self.validator: DataValidator = DataValidator()
        self.exchange_step: ExchangeSelectionStep = ExchangeSelectionStep(
            self.manager, self.selector, self.validator
        )
        self.market_step: MarketSelectionStep = MarketSelectionStep(
            self.manager, self.selector, self.validator
        )
        self.tool_step: ToolSelectionStep = ToolSelectionStep(
            self.manager, self.selector, self.validator
        )
        self.orchestrator: SelectionOrchestrator = SelectionOrchestrator(
            [
                self.exchange_step,
                self.market_step,
                self.tool_step,
            ]
        )

    def parse(self) -> ParserArgs:
        """
        Запускает процесс выбора параметров.

        Returns:
            ParserArgs: Выбранные параметры
        """
        context = self.orchestrator.execute()

        return ParserArgs(
            exchange=context["exchange"],
            market=context["market"],
            tool=context["tool"],
        )


class ParserFactory:
    """Фабрика для создания настроенного CLI парсера."""

    @staticmethod
    def create_parser(
        manager: ExchangeDataManager,
    ) -> CLIParser:
        """Создает и настраивает экземпляр CLIParser."""
        return CLIParser(manager)


def main() -> None:
    """Основная функция для тестирования модуля."""
    from unittest.mock import Mock

    # Мок менеджера для тестирования
    mock_manager = Mock(spec=ExchangeDataManager)
    mock_manager.get_exchange_names.return_value = [
        "Binance",
        "Bybit",
        "OKX",
    ]
    mock_manager.get_markets_for_exchange.return_value = [
        "spot",
        "futures",
        "margin",
    ]
    mock_manager.get_tools_for_market.return_value = [
        "BTC/USDT",
        "ETH/USDT",
        "BNB/USDT",
    ]

    parser = ParserFactory.create_parser(mock_manager)

    try:
        args = parser.parse()
        print(f"Выбрано: {args}")
    except ExchangeDataError as error:
        print(f"Ошибка данных: {error}")
    except KeyboardInterrupt:
        print("\nПрограмма прервана пользователем")


if __name__ == "__main__":
    main()
