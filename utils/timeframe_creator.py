import os
import glob
import csv
import sys
from datetime import datetime
from pathlib import Path


class TimeframeCreator:
    """
    Класс для создания файлов таймфреймов из сырых данных.
    """

    def __init__(self, selection_dict=None):
        """
        Инициализация.

        Args:
            selection_dict (dict, optional): Словарь с ключами "exchange", "market", "tool"
                                           Если None, будет предложен выбор через меню
        """
        self.selection = selection_dict
        self.base_path = None

    def _get_selection_from_menu(self):
        """
        Получает выбор биржи, рынка и инструмента через меню.

        Returns:
            dict or None: Словарь с выбором или None если отменено
        """
        try:
            # Добавляем путь к lib для импорта exchange_selection
            utils_dir = Path(__file__).parent
            parent_dir = utils_dir.parent
            lib_dir = parent_dir / "lib"

            if lib_dir.exists():
                sys.path.insert(0, str(lib_dir))

            import exchange_selection

            return exchange_selection.run()
        except ImportError as e:
            print(f"Ошибка импорта exchange_selection: {e}")
            return None

    def _ensure_selection(self):
        """
        Обеспечивает наличие выбора (либо переданного, либо через меню).
        """
        if self.selection is None:
            self.selection = self._get_selection_from_menu()

        if not self.selection:
            raise ValueError("Выбор не сделан или отменен")

        exchange = self.selection.get("exchange")
        market = self.selection.get("market")
        tool = self.selection.get("tool")

        if not all([exchange, market, tool]):
            raise ValueError("В словаре выбора отсутствуют необходимые ключи")

    def _build_storage_path(self):
        """
        Строит путь к папке с сырыми данными (storage находится на том же уровне что и папка utils/).
        """
        self._ensure_selection()

        # Получаем директорию utils (где находится текущий скрипт)
        utils_dir = Path(__file__).parent
        # Поднимаемся на уровень выше (к директории содержащей utils и storage)
        parent_dir = utils_dir.parent
        self.base_path = (
            parent_dir
            / f"storage/raw/{self.selection['exchange']}/{self.selection['market']}/{self.selection['tool']}"
        )

    def _load_all_data(self):
        """
        Загружает все файлы данных по датам из папки.

        Returns:
            list: Список словарей с данными, отсортированный по времени
        """
        if not self.base_path.exists():
            raise FileNotFoundError(f"Папка не найдена: {self.base_path}")

        # Ищем все файлы в папке
        file_pattern = str(self.base_path / "*")
        files = glob.glob(file_pattern)

        if not files:
            raise FileNotFoundError(f"Файлы не найдены в папке: {self.base_path}")

        all_data = []

        for file_path in files:
            try:
                # Читаем файл CSV
                with open(file_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Конвертируем время из миллисекунд в datetime
                        open_time_ms = int(row["open_time"])
                        timestamp = datetime.fromtimestamp(open_time_ms / 1000.0)

                        data = {
                            "timestamp": timestamp,
                            "open_time": open_time_ms,
                            "open": float(row["open"]),
                            "high": float(row["high"]),
                            "low": float(row["low"]),
                            "close": float(row["close"]),
                            "volume": float(row["volume"]),
                            "turnover": float(row["turnover"]),
                        }
                        all_data.append(data)
            except Exception as e:
                print(f"Ошибка при чтении файла {file_path}: {e}")

        if not all_data:
            raise ValueError("Не удалось загрузить данные из файлов")

        # Сортируем данные по времени
        all_data.sort(key=lambda x: x["timestamp"])

        return all_data

    def _create_timeframe_files(self, data):
        """
        Создает файлы таймфреймов с 5 до 14400 минут.

        Args:
            data (list): Исходные данные
        """
        if not data:
            raise ValueError("Данные отсутствуют")

        # Создаем папку для таймфреймов (storage находится на том же уровне что и папка utils/)
        utils_dir = Path(__file__).parent
        parent_dir = utils_dir.parent
        output_path = (
            parent_dir
            / f"storage/processed/normalized/{self.selection['exchange']}/{self.selection['market']}/{self.selection['tool']}"
        )
        output_path.mkdir(parents=True, exist_ok=True)

        # Перебираем все таймфреймы от 5 до 14400 минут
        for minutes in range(5, 14401):
            try:
                timeframe_data = self._resample_to_timeframe(data, minutes)
                self._save_timeframe_file(timeframe_data, minutes, output_path)

                # Выводим сообщение о создании файла на той же строке
                sys.stdout.write(f"\rСоздан файл таймфрейма: {minutes}.csv")
                sys.stdout.flush()

            except Exception as e:
                print(f"\rОшибка при создании таймфрейма {minutes} минут: {e}")

        # Завершаем вывод новой строкой
        print()

    def _resample_to_timeframe(self, data, minutes):
        """
        Ресемплит данные до указанного таймфрейма.

        Args:
            data (list): Исходные данные
            minutes (int): Таймфрейм в минутах

        Returns:
            list: Данные с указанным таймфреймом
        """
        timeframe_data = []
        current_candle = None
        candle_end_time = None

        for row in data:
            timestamp = row["timestamp"]

            # Вычисляем начало свечи таймфрейма
            total_minutes = timestamp.hour * 60 + timestamp.minute
            candle_start_minute = (total_minutes // minutes) * minutes

            candle_start_time = timestamp.replace(
                hour=candle_start_minute // 60,
                minute=candle_start_minute % 60,
                second=0,
                microsecond=0,
            )

            # Если это начало новой свечи
            if current_candle is None or candle_start_time != candle_end_time:
                # Сохраняем предыдущую свечу
                if current_candle is not None:
                    timeframe_data.append(current_candle)

                # Начинаем новую свечу
                current_candle = {
                    "datetime": candle_start_time,
                    "open": row["open"],
                    "high": row["high"],
                    "low": row["low"],
                    "close": row["close"],
                    "volume": row["volume"],
                    "turnover": row["turnover"],
                }
                candle_end_time = candle_start_time
            else:
                # Обновляем текущую свечу
                current_candle["high"] = max(current_candle["high"], row["high"])
                current_candle["low"] = min(current_candle["low"], row["low"])
                current_candle["close"] = row["close"]
                current_candle["volume"] += row["volume"]
                current_candle["turnover"] += row["turnover"]

        # Добавляем последнюю свечу
        if current_candle is not None:
            timeframe_data.append(current_candle)

        return timeframe_data

    def _save_timeframe_file(self, timeframe_data, minutes, output_path):
        """
        Сохраняет данные таймфрейма в файл.

        Args:
            timeframe_data (list): Данные таймфрейма
            minutes (int): Таймфрейм в минутах
            output_path (Path): Путь для сохранения
        """
        filename = output_path / f"{minutes}.csv"

        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # Записываем заголовок
            writer.writerow(
                ["datetime", "open", "high", "low", "close", "volume", "turnover"]
            )

            # Записываем данные
            for candle in timeframe_data:
                writer.writerow(
                    [
                        candle["datetime"].isoformat(),
                        candle["open"],
                        candle["high"],
                        candle["low"],
                        candle["close"],
                        candle["volume"],
                        candle["turnover"],
                    ]
                )

    def process(self):
        """
        Основной метод обработки: загружает данные и создает таймфреймы.
        """
        try:
            self._build_storage_path()
            data = self._load_all_data()
            self._create_timeframe_files(data)
            print("Таймфреймы успешно созданы")
        except Exception as e:
            print(f"Ошибка при обработке: {e}")
            raise

    def run(self):
        """
        Запускает процесс создания таймфреймов.
        """
        self.process()


def run():
    """Запустить создание таймфреймов."""

    # Очищаем экран перед запуском
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()

    # Получаем выбор инструмента через меню
    creator = TimeframeCreator()

    try:
        creator.run()

        # Задержка перед завершением
        try:
            import shutil

            _, terminal_lines = shutil.get_terminal_size()
            sys.stdout.write(f"\033[{terminal_lines};1H")
            print("Нажмите Enter для выхода...")
            input()
        except:
            print("\nНажмите Enter для выхода...")
            input()

    except ValueError as e:
        # Выход в левом нижнем углу
        sys.stdout.write("\033[2J\033[H")
        try:
            import shutil

            _, terminal_lines = shutil.get_terminal_size()
            sys.stdout.write(f"\033[{terminal_lines};1H")
            print(f"Ошибка: {e}")
            print("Нажмите Enter для выхода...")
            input()
        except:
            print(f"Ошибка: {e}")
            print("\nНажмите Enter для выхода...")
            input()


if __name__ == "__main__":
    run()
