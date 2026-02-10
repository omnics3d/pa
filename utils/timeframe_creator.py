import os
import glob
import csv
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path


class TimeframeCreator:
    """
    Класс для создания файлов таймфреймов из сырых данных.
    Сначала создает 1-минутный файл, затем на его основе все остальные.
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
        self.one_minute_data = None
        self.one_minute_file_path = None

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
        Строит путь к папке с сырых данных (storage находится на том же уровне что и папка utils/).
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

    def _is_numeric(self, value: str) -> bool:
        """
        Проверяет, можно ли преобразовать строку в число.
        
        Args:
            value (str): Проверяемая строка
            
        Returns:
            bool: True если строка может быть преобразована в число
        """
        try:
            float(value)
            return True
        except ValueError:
            return False

    def _validate_minute_data_count(self, lines, has_header, filename):
        """
        Проверяет, что в файле ровно 1440 минутных свечей.
        
        Args:
            lines (list): Все строки файла
            has_header (bool): Есть ли заголовок
            filename (str): Имя файла для сообщения об ошибке
            
        Raises:
            ValueError: Если количество записей не равно 1440
        """
        # Количество строк данных
        data_lines_count = len(lines) - (1 if has_header else 0)
        
        if data_lines_count != 1440:
            raise ValueError(
                f"Файл {filename}: неверное количество записей. "
                f"Ожидается 1440, получено {data_lines_count}. "
                f"Всего строк в файле: {len(lines)}, заголовок: {'есть' if has_header else 'нет'}"
            )
        
        # Дополнительная проверка: каждая запись должна быть валидной минутной свечой
        valid_data_count = 0
        for i, line in enumerate(lines):
            # Пропускаем заголовок если есть
            if has_header and i == 0:
                continue
            
            line = line.strip()
            if not line:
                continue
                
            parts = line.split(',')
            if len(parts) >= 6:  # Минимум timestamp + OHLCV
                try:
                    # Проверяем, что timestamp - число (миллисекунды)
                    timestamp = int(parts[0])
                    # Преобразуем в GMT/UTC
                    dt = datetime.fromtimestamp(timestamp / 1000.0, tz=timezone.utc)
                    # Проверяем, что дата в разумных пределах (после 2010 года)
                    if dt.year >= 2010:
                        valid_data_count += 1
                except (ValueError, IndexError, OverflowError):
                    pass
        
        if valid_data_count != 1440:
            raise ValueError(
                f"Файл {filename}: количество валидных записей {valid_data_count}, "
                f"ожидается 1440"
            )

    def _load_and_create_one_minute_file(self):
        """
        Загружает все файлы данных и создает 1-минутный файл.
        
        Returns:
            list: Список словарей с 1-минутными данными
            Path: Путь к созданному 1-минутному файлу
        """
        if not self.base_path.exists():
            raise FileNotFoundError(f"Папка не найдена: {self.base_path}")

        # Ищем все файлы в папке
        file_pattern = str(self.base_path / "*")
        files = glob.glob(file_pattern)

        if not files:
            raise FileNotFoundError(f"Файлы не найдены в папке: {self.base_path}")

        all_data = []
        fieldnames = ["open_time", "open", "high", "low", "close", "volume", "turnover"]
        
        print("НАЧАЛО ЗАГРУЗКИ ФАЙЛОВ И СОЗДАНИЯ 1-МИНУТНОГО ФАЙЛА")
        
        for file_path in sorted(files):  # Сортируем файлы для последовательной обработки
            try:
                # Читаем весь файл
                with open(file_path, "r", encoding="utf-8", errors='replace') as f:
                    lines = [line.rstrip('\n') for line in f.readlines()]
                
                if not lines:
                    raise ValueError(f"Файл пустой: {os.path.basename(file_path)}")
                
                # Определяем, есть ли заголовок
                first_line = lines[0].strip()
                has_header = False
                
                if first_line:
                    parts = first_line.split(',')
                    if parts and not self._is_numeric(parts[0]):
                        # Первый элемент не число → это заголовок
                        has_header = True
                
                # ВАЖНО: Проверяем количество записей
                filename = os.path.basename(file_path)
                self._validate_minute_data_count(lines, has_header, filename)
                
                # Индекс строки, с которой начинаются данные
                data_start = 1 if has_header else 0
                
                # Обрабатываем данные
                rows_in_file = 0
                for line in lines[data_start:]:
                    line = line.strip()
                    if not line:
                        continue
                    
                    parts = line.split(',')
                    if len(parts) < 6:  # Минимум 6 колонок (open_time, O, H, L, C, V)
                        raise ValueError(
                            f"Файл {filename}: строка имеет недостаточно колонок ({len(parts)}). "
                            f"Строка: {line[:100]}..."
                        )
                    
                    try:
                        # Создаем словарь вручную по позициям
                        row = {}
                        for i, field in enumerate(fieldnames):
                            if i < len(parts):
                                row[field] = parts[i].strip()
                            else:
                                # Если столбцов меньше, чем fieldnames, заполняем значением по умолчанию
                                row[field] = "0" if field in ["volume", "turnover"] else ""
                        
                        open_time_ms = int(row["open_time"])
                        # ПРЕОБРАЗУЕМ В GMT/UTC
                        timestamp = datetime.fromtimestamp(open_time_ms / 1000.0, tz=timezone.utc)
                        
                        data = {
                            "datetime": timestamp,
                            "open_time": open_time_ms,
                            "open": float(row["open"]),
                            "high": float(row["high"]),
                            "low": float(row["low"]),
                            "close": float(row["close"]),
                            "volume": float(row.get("volume", 0)),
                            "turnover": float(row.get("turnover", 0)),
                        }
                        all_data.append(data)
                        rows_in_file += 1
                        
                    except (ValueError, IndexError) as e:
                        raise ValueError(
                            f"Файл {filename}: ошибка в строке данных: {line[:100]}... "
                            f"Ошибка: {str(e)}"
                        )
                
                # Двойная проверка (на всякий случай)
                if rows_in_file != 1440:
                    raise ValueError(
                        f"Файл {filename}: после обработки записей {rows_in_file}, "
                        f"ожидается 1440"
                    )
                
                print(f"ФАЙЛ: {filename} | ЗАПИСЕЙ: {rows_in_file} | СТАТУС: УСПЕХ")
                        
            except Exception as e:
                # Не продолжаем обработку, а прерываем выполнение
                print(f"\nКРИТИЧЕСКАЯ ОШИБКА в файле {os.path.basename(file_path)}:")
                print(f"{str(e)}")
                print(f"\nВыполнение прервано. Исправьте файл и запустите скрипт заново.")
                sys.exit(1)

        if not all_data:
            raise ValueError("Не удалось загрузить данные из файлов")

        # Проверяем общее количество данных
        total_files = len(files)
        expected_total = total_files * 1440
        
        if len(all_data) != expected_total:
            print(f"\nВнимание: общее количество записей ({len(all_data)}) "
                  f"не соответствует ожидаемому ({expected_total})")
            print(f"Количество файлов: {total_files}")
            print("Продолжение обработки...")

        # Сортируем данные по времени
        all_data.sort(key=lambda x: x["datetime"])
        
        # Подсчитываем количество дней
        if all_data:
            first_date = all_data[0]["datetime"].date()
            last_date = all_data[-1]["datetime"].date()
            days_count = (last_date - first_date).days + 1
            print(f"\nИТОГ ЗАГРУЗКИ:")
            print(f"Всего файлов: {len(files)}")
            print(f"Всего 1-минутных записей: {len(all_data)}")
            print(f"Полных дней: {days_count}")
            print(f"Диапазон дат в GMT: от {all_data[0]['datetime']} до {all_data[-1]['datetime']}")
        else:
            print(f"\nИТОГ ЗАГРУЗКИ:")
            print(f"Всего файлов: {len(files)}")
            print(f"Всего 1-минутных записей: {len(all_data)}")
        
        # Создаем папку для 1-минутного файла
        utils_dir = Path(__file__).parent
        parent_dir = utils_dir.parent
        output_path = (
            parent_dir
            / f"storage/processed/normalized/{self.selection['exchange']}/{self.selection['market']}/{self.selection['tool']}"
        )
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Сохраняем 1-минутный файл
        self.one_minute_file_path = output_path / "1.csv"
        self._save_timeframe_file(all_data, 1, output_path)
        
        print(f"\nСОЗДАН 1-МИНУТНЫЙ ФАЙЛ:")
        print(f"Путь: {self.one_minute_file_path}")
        print(f"Записей: {len(all_data)}")
        
        return all_data

    def _create_timeframe_files_from_one_minute(self, one_minute_data):
        """
        Создает файлы таймфреймов с 2 до 14400 минут из 1-минутных данных.

        Args:
            one_minute_data (list): 1-минутные данные
        """
        if not one_minute_data:
            raise ValueError("1-минутные данные отсутствуют")

        # Создаем папку для таймфреймов (storage находится на том же уровне что и папка utils/)
        utils_dir = Path(__file__).parent
        parent_dir = utils_dir.parent
        output_path = (
            parent_dir
            / f"storage/processed/normalized/{self.selection['exchange']}/{self.selection['market']}/{self.selection['tool']}"
        )

        print(f"\nНАЧАЛО СОЗДАНИЯ ТАЙМФРЕЙМОВ ИЗ 1-МИНУТНОГО ФАЙЛА")
        print(f"Исходных 1-минутных записей: {len(one_minute_data)}")
        print(f"Выходная папка: {output_path}")
        print(f"Количество таймфреймов: от 2 до 14400 минут (всего 14399 файлов)")

        total_start_time = time.time()
        
        # Перебираем все таймфреймы от 2 до 14400 минут
        for minutes in range(2, 14401):
            try:
                file_start_time = time.time()
                timeframe_data = self._resample_to_timeframe(one_minute_data, minutes)
                candles_count = len(timeframe_data)
                file_mid_time = time.time()
                self._save_timeframe_file(timeframe_data, minutes, output_path)
                file_end_time = time.time()
                
                resample_time = file_mid_time - file_start_time
                save_time = file_end_time - file_mid_time
                total_file_time = file_end_time - file_start_time
                
                # Выводим подробную информацию о каждом файле
                print(f"ТФ: {minutes:5}|Ф: {minutes:5}.csv|C: {candles_count:7}|R: {resample_time:4.1f}|S: {save_time:4.1f}|∑: {total_file_time:4.1f}|%: {minutes:5}/14400({(minutes/14400*100):5.1f}%)")

            except Exception as e:
                print(f"ОШИБКА: Таймфрейм {minutes} минут | Ошибка: {str(e)[:100]}")

        total_end_time = time.time()
        total_elapsed = total_end_time - total_start_time
        
        print(f"\nЗАВЕРШЕНИЕ СОЗДАНИЯ ТАЙМФРЕЙМОВ")
        print(f"Всего создано файлов: 14399 (от 2 до 14400 минут)")
        print(f"Общее время выполнения: {total_elapsed:.2f} секунд")
        print(f"Среднее время на файл: {total_elapsed/14399:.3f} секунд")
        print(f"Диапазон таймфреймов: от 2 до 14400 минут")
        print(f"Выходная папка: {output_path}")

    def _resample_to_timeframe(self, one_minute_data, minutes):
        """
        Ресемплит 1-минутные данные до указанного таймфрейма.
        
        Args:
            one_minute_data (list): 1-минутные данные
            minutes (int): Таймфрейм в минуты

        Returns:
            list: Данные с указанным таймфреймом
        """
        if not one_minute_data:
            return []
        
        # Для 1-минутного таймфрейма возвращаем исходные данные
        if minutes == 1:
            timeframe_data = []
            for row in one_minute_data:
                timeframe_data.append({
                    "datetime": row["datetime"],
                    "open": row["open"],
                    "high": row["high"],
                    "low": row["low"],
                    "close": row["close"],
                    "volume": row["volume"],
                    "turnover": row["turnover"],
                })
            return timeframe_data
        
        # Для таймфреймов > 1 минуты
        timeframe_data = []
        current_candle = None
        minute_count_in_candle = 0
        
        for row in one_minute_data:
            timestamp = row["datetime"]  # Уже в GMT/UTC
            
            # Если это начало новой свечи или первая свеча
            if current_candle is None or minute_count_in_candle >= minutes:
                # Сохраняем предыдущую свечу (если она существует и полная)
                if current_candle is not None and minute_count_in_candle == minutes:
                    timeframe_data.append(current_candle)
                
                # Начинаем новую свечу
                current_candle = {
                    "datetime": timestamp.replace(second=0, microsecond=0),
                    "open": row["open"],
                    "high": row["high"],
                    "low": row["low"],
                    "close": row["close"],
                    "volume": row["volume"],
                    "turnover": row["turnover"],
                }
                minute_count_in_candle = 1
            else:
                # Обновляем текущую свечу
                current_candle["high"] = max(current_candle["high"], row["high"])
                current_candle["low"] = min(current_candle["low"], row["low"])
                current_candle["close"] = row["close"]
                current_candle["volume"] += row["volume"]
                current_candle["turnover"] += row["turnover"]
                minute_count_in_candle += 1
        
        # Добавляем последнюю свечу, если она полная
        if current_candle is not None and minute_count_in_candle == minutes:
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
                # Преобразуем aware datetime в строку БЕЗ временной зоны, но в GMT
                dt_str = candle["datetime"].strftime("%Y-%m-%d %H:%M:%S")
                writer.writerow(
                    [
                        dt_str,
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
        Основной метод обработки: загружает данные, создает 1-минутный файл, затем все остальные.
        """
        try:
            self._build_storage_path()
            
            # 1. Загружаем данные и создаем 1-минутный файл
            one_minute_data = self._load_and_create_one_minute_file()
            
            # 2. Создаем все остальные таймфреймы из 1-минутного файла
            self._create_timeframe_files_from_one_minute(one_minute_data)
            
            print(f"\nТАЙМФРЕЙМЫ УСПЕШНО СОЗДАНЫ")
            print(f"Создано файлов: 14400 (от 1 до 14400 минут)")
            
        except Exception as e:
            print(f"\nОшибка при обработке: {e}")
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

    print("ПРОВЕРКА И СОЗДАНИЕ ТАЙМФРЕЙМОВ")
    print("Требования к исходным файлам:")
    print("1. Каждый файл должен содержать ровно 1440 минутных свечей")
    print("2. Заголовок может быть или отсутствовать")
    print("3. Формат: timestamp,open,high,low,close,volume,...")
    print("4. Timestamp в миллисекундах преобразуется в GMT/UTC")
    print("5. Будут созданы таймфреймы от 1 до 14400 минут (всего 14400 файлов)")
    print("6. Сначала создается 1-минутный файл, затем все остальные на его основе")
    print(f"Дата и время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Получаем выбор инструмента через меню
    creator = TimeframeCreator()

    try:
        creator.run()

        # Задержка перед завершением
        try:
            import shutil

            _, terminal_lines = shutil.get_terminal_size()
            sys.stdout.write(f"\033[{terminal_lines};1H")
            print("НАЖМИТЕ ENTER ДЛЯ ВЫХОДА...")
            input()
        except:
            print("\nНАЖМИТЕ ENTER ДЛЯ ВЫХОДА...")
            input()

    except ValueError as e:
        # Выход в левом нижнем углу
        sys.stdout.write("\033[2J\033[H")
        try:
            import shutil

            _, terminal_lines = shutil.get_terminal_size()
            sys.stdout.write(f"\033[{terminal_lines};1H")
            print(f"ОШИБКА: {e}")
            print("НАЖМИТЕ ENTER ДЛЯ ВЫХОДА...")
            input()
        except:
            print(f"ОШИБКА: {e}")
            print("\nНАЖМИТЕ ENTER ДЛЯ ВЫХОДА...")
            input() 
    except SystemExit:
        # Уже выходим, ничего не делаем
        pass
    except Exception as e:
        print(f"\nНЕОЖИДАННАЯ ОШИБКА: {e}")
        print("НАЖМИТЕ ENTER ДЛЯ ВЫХОДА...")
        input()


if __name__ == "__main__":
    run()
