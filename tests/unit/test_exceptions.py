# tests/unit/test_exceptions.py

import unittest
from core.basic_parser import ExchangeDataError


class TestExchangeDataError(unittest.TestCase):
    """Тесты для исключений."""

    def test_exception_creation(self):
        """Тестирование создания исключения."""
        error = ExchangeDataError("Test error message")
        self.assertEqual(str(error), "Test error message")

    def test_exception_inheritance(self):
        """Тестирование наследования исключения."""
        error = ExchangeDataError("Test")
        self.assertIsInstance(error, Exception)

    def test_exception_with_formatting(self):
        """Тестирование исключения с форматированием строк."""
        exchange = "Binance"
        error = ExchangeDataError(f"Ошибка для {exchange}")
        self.assertEqual(str(error), "Ошибка для Binance")
