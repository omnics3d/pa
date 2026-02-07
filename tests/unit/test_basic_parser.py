# tests/unit/test_basic_parser.py

import sys
import os
import unittest

# Добавляем путь к корню проекта для импорта модулей
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(parent_dir)
sys.path.insert(0, root_dir)

# Импортируем только то, что нужно для этих тестов
try:
    from core.basic_parser import ParserArgs

    print("✅ Импорт ParserArgs успешен")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print(f"📁 Текущий путь Python: {sys.path}")
    raise


class TestParserArgs(unittest.TestCase):
    """Тесты для класса ParserArgs (самый простой класс для начала)."""

    def test_parser_args_creation_simple(self):
        """Тестирование создания объекта ParserArgs с простыми значениями."""
        print("📝 Тест: test_parser_args_creation_simple")

        args = ParserArgs(exchange="Binance", market="spot", tool="BTC/USDT")

        # Проверяем значения полей
        self.assertEqual(args.exchange, "Binance")
        self.assertEqual(args.market, "spot")
        self.assertEqual(args.tool, "BTC/USDT")
        print("✅ Объект создан успешно")

    def test_parser_args_creation_with_special_chars(self):
        """Тестирование создания объекта ParserArgs с особыми символами."""
        print("📝 Тест: test_parser_args_creation_with_special_chars")

        args = ParserArgs(
            exchange="OKX Futures", market="perpetual", tool="ETH-USD-SWAP"
        )

        self.assertEqual(args.exchange, "OKX Futures")
        self.assertEqual(args.market, "perpetual")
        self.assertEqual(args.tool, "ETH-USD-SWAP")
        print("✅ Объект с особыми символами создан успешно")

    def test_parser_args_creation_empty_strings(self):
        """Тестирование создания объекта ParserArgs с пустыми строками."""
        print("📝 Тест: test_parser_args_creation_empty_strings")

        args = ParserArgs(exchange="", market="", tool="")

        self.assertEqual(args.exchange, "")
        self.assertEqual(args.market, "")
        self.assertEqual(args.tool, "")
        print("✅ Объект с пустыми строками создан успешно")

    def test_parser_args_string_representation(self):
        """Тестирование строкового представления объекта ParserArgs."""
        print("📝 Тест: test_parser_args_string_representation")

        args = ParserArgs(exchange="TestExchange", market="TestMarket", tool="TestTool")

        string_repr = str(args)

        # Проверяем, что все поля присутствуют в строковом представлении
        self.assertIn("TestExchange", string_repr)
        self.assertIn("TestMarket", string_repr)
        self.assertIn("TestTool", string_repr)

        # Проверяем, что это не пустая строка
        self.assertTrue(len(string_repr) > 0)
        print(f"✅ Строковое представление: {string_repr}")

    def test_parser_args_equality(self):
        """Тестирование сравнения объектов ParserArgs."""
        print("📝 Тест: test_parser_args_equality")

        args1 = ParserArgs("Binance", "spot", "BTC/USDT")
        args2 = ParserArgs("Binance", "spot", "BTC/USDT")
        args3 = ParserArgs("Bybit", "futures", "ETH/USDT")

        # Объекты с одинаковыми значениями должны быть равны
        # (dataclass автоматически реализует __eq__)
        self.assertEqual(args1, args2)

        # Объекты с разными значениями не должны быть равны
        self.assertNotEqual(args1, args3)
        print("✅ Сравнение объектов работает корректно")

    def test_parser_args_as_dict(self):
        """Тестирование преобразования ParserArgs в словарь."""
        print("📝 Тест: test_parser_args_as_dict")

        args = ParserArgs("Binance", "spot", "BTC/USDT")

        # Dataclasses имеют метод __dict__ или можно использовать asdict
        try:
            # Пробуем получить словарь
            args_dict = args.__dict__

            self.assertEqual(args_dict.get("exchange"), "Binance")
            self.assertEqual(args_dict.get("market"), "spot")
            self.assertEqual(args_dict.get("tool"), "BTC/USDT")
            print("✅ Преобразование в словарь успешно")
        except AttributeError:
            # Если __dict__ нет, пропускаем этот тест
            self.skipTest("Класс не имеет атрибута __dict__")
            print("⚠️  Пропуск теста преобразования в словарь")


def run_single_test_class():
    """Запускает только тесты для класса TestParserArgs."""
    print("\n" + "=" * 50)
    print("🚀 ЗАПУСК ТЕСТОВ ДЛЯ ParserArgs")
    print("=" * 50)

    # Создаем TestSuite только с тестами для TestParserArgs
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestParserArgs)

    # Запускаем тесты
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 50)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ ParserArgs")
    print("=" * 50)

    if result.wasSuccessful():
        print(f"✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ ({result.testsRun} тестов)")
    else:
        print(
            f"❌ ЕСТЬ ОШИБКИ: {len(result.failures)} failures, {len(result.errors)} errors"
        )

    return result.wasSuccessful()


if __name__ == "__main__":
    print("🧪 Тестирование модуля basic_parser.py")
    print(f"📁 Корневая директория: {root_dir}")

    # Запускаем только тесты для ParserArgs
    success = run_single_test_class()

    # Возвращаем код выхода
    sys.exit(0 if success else 1)
