#{{{
""" data_integrity_checker.py

Скрипт для проверки целостности данных минутных свечей.
Использует выбор из exchange_selection.py для определения проверяемого инструмента.
"""
#}}}

import sys
import os
import glob
import csv
import shutil
from datetime import datetime, timedelta, timezone

# Добавляем пути для импортов
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
sys.path.append(os.path.join(parent_dir, 'lib'))

try:
    from exchange_selection import run as exchange_selection_run
except ImportError:
    print("Ошибка: Не найден файл exchange_selection.py")
    sys.exit(1)

#{{{
class DataIntegrityChecker:
    """Класс для проверки целостности данных."""
    
    def __init__(self, exchange: str, market: str, tool: str):
        #{{{
        self.exchange = exchange
        self.market = market
        self.tool = tool
        self.data_path = f"storage/raw/{exchange}/{market}/{tool}/"
        
        # Создаем директорию для отчетов
        self.report_dir = "storage/reports/"
        os.makedirs(self.report_dir, exist_ok=True)
        
        # Формируем путь к отчету
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        self.report_path = f"{self.report_dir}integrity_check_{exchange}_{market}_{tool}_{timestamp}.txt"
        
        self.errors = []
        self.file_count = 0
        self.total_rows = 0
        self.total_errors = 0
        #}}}
    
    def _clear_screen(self):
        """Очистить экран."""
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()
    
    def _display_at_bottom(self, lines: list[str]):
        """Отобразить строки в левом нижнем углу экрана."""
        # Очищаем экран
        self._clear_screen()
        
        try:
            # Получаем размер терминала
            _, terminal_lines = shutil.get_terminal_size()
            menu_height = len(lines)
            
            # Вычисляем начальную строку (нижний угол)
            start_line = max(1, terminal_lines - menu_height)
            
            # Перемещаем курсор
            sys.stdout.write(f"\033[{start_line};1H")
            
            # Выводим строки меню
            for line in lines:
                print(line)
            
            sys.stdout.flush()
        except Exception:
            # Если не удалось определить размер терминала, выводим обычным способом
            for line in lines:
                print(line)
    
    def check_all_files(self):
        #{{{
        """Проверить все файлы в директории."""
        
        self._clear_screen()
        
        # Находим все CSV файлы
        pattern = os.path.join(self.data_path, f"{self.tool}-1m-*.csv")
        files = sorted(glob.glob(pattern))
        
        if not files:
            self.errors.append(f"ОШИБКА: Не найдено файлов по пути {pattern}")
            return
        
        self.file_count = len(files)
        
        # Отображаем информацию в нижнем углу
        info_lines = [
            f"Проверка целостности данных",
            f"Биржа: {self.exchange}",
            f"Рынок: {self.market}",
            f"Инструмент: {self.tool}",
            f"Найдено файлов: {self.file_count}",
            "-" * 40
        ]
        
        # Проверяем каждый файл
        for i, file_path in enumerate(files, 1):
            file_name = os.path.basename(file_path)
            
            # Обновляем строку прогресса
            progress_lines = info_lines + [f"Проверка файла {i}/{self.file_count}: {file_name}"]
            self._display_at_bottom(progress_lines)
            
            self._check_single_file(file_path)
        
        # Финальный вывод
        finish_lines = [
            f"Проверка завершена",
            f"Проверено файлов: {self.file_count}",
            f"Всего строк данных: {self.total_rows}",
            f"Найдено ошибок: {self.total_errors}",
            "-" * 40,
            f"Отчет сохранен: {os.path.basename(self.report_path)}"
        ]
        self._display_at_bottom(finish_lines)
        #}}}
    
    def _check_single_file(self, file_path: str):
        #{{{
        """Проверить один файл."""
        
        file_name = os.path.basename(file_path)
        
        try:
            # Парсим дату из имени файла
            date_str = file_name.replace(f"{self.tool}-1m-", "").replace(".csv", "")
            file_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            
            # Читаем файл
            rows = []
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    rows.append(row)
            
            self.total_rows += len(rows)
            
            # Определяем, есть ли заголовки
            has_header = False
            if rows and len(rows[0]) == 7:
                # Проверяем первую строку - если это не timestamp, то это заголовки
                first_cell = rows[0][0]
                if not (first_cell.isdigit() and len(first_cell) > 10):
                    has_header = True
                    rows = rows[1:]  # Убираем заголовки
            
            if not rows:
                self.errors.append(f"Файл: {file_name} - Файл пуст или содержит только заголовки")
                self.total_errors += 1
                return
            
            # Конвертируем строки в структурированные данные
            data = []
            for i, row in enumerate(rows):
                if len(row) != 7:
                    self.errors.append(f"Файл: {file_name}, строка {i+1} - Неверное количество колонок: {len(row)} вместо 7")
                    self.total_errors += 1
                    continue
                
                try:
                    item = {
                        'open_time': int(row[0]),
                        'open': float(row[1]),
                        'high': float(row[2]),
                        'low': float(row[3]),
                        'close': float(row[4]),
                        'volume': float(row[5]),
                        'turnover': float(row[6])
                    }
                    data.append(item)
                except ValueError as e:
                    self.errors.append(f"Файл: {file_name}, строка {i+1} - Ошибка преобразования данных: {e}")
                    self.total_errors += 1
            
            if not data:
                return
            
            # 1. Проверка хронологического порядка
            self._check_timeline(data, file_name, file_date)
            
            # 2. Проверка пропусков во времени
            self._check_time_gaps(data, file_name, file_date)
            
            # 3. Проверка корректности цен
            self._check_price_integrity(data, file_name)
            
            # 4. Проверка корректности объемов
            self._check_volume_integrity(data, file_name)
            
            # 5. Проверка полноты данных за день
            self._check_daily_completeness(data, file_name, file_date)
            
        except Exception as e:
            self.errors.append(f"Файл: {file_name} - КРИТИЧЕСКАЯ ОШИБКА: {str(e)}")
            self.total_errors += 1
        #}}}
    
    def _check_timeline(self, data: list, file_name: str, file_date: datetime.date):
        #{{{
        """Проверить хронологический порядок."""
        
        if not data:
            return
        
        prev_time = None
        out_of_order_count = 0
        wrong_date_count = 0
        
        for i, item in enumerate(data):
            current_time = item['open_time']
            
            # Конвертируем timestamp в UTC datetime
            dt = datetime.fromtimestamp(current_time / 1000, tz=timezone.utc)
            
            # Проверяем хронологический порядок
            if prev_time is not None and current_time <= prev_time:
                out_of_order_count += 1
            
            # Проверяем, что timestamp относится к правильной дате (в UTC)
            if dt.date() != file_date:
                wrong_date_count += 1
            
            prev_time = current_time
        
        if out_of_order_count > 0:
            self.errors.append(f"Файл: {file_name} - Нарушен хронологический порядок: {out_of_order_count} нарушений")
            self.total_errors += 1
        
        if wrong_date_count > 0:
            self.errors.append(f"Файл: {file_name} - Найдены строки с неправильной датой (UTC): {wrong_date_count} строк")
            self.total_errors += 1
        #}}}
    
    def _check_time_gaps(self, data: list, file_name: str, file_date: datetime.date):
        #{{{
        """Проверить пропуски во времени."""
        
        if len(data) < 2:
            return
        
        # Ожидаем интервал 1 минута (60000 мс)
        expected_interval = 60000
        gap_count = 0
        max_gap = 0
        
        for i in range(1, len(data)):
            time_diff = data[i]['open_time'] - data[i-1]['open_time']
            if time_diff > expected_interval:
                gap_count += 1
                gap_minutes = time_diff / 60000
                if gap_minutes > max_gap:
                    max_gap = gap_minutes
        
        if gap_count > 0:
            self.errors.append(f"Файл: {file_name} - Найдены пропуски: {gap_count} пропусков, максимальный: {max_gap:.1f} мин")
            self.total_errors += 1
        #}}}
    
    def _check_price_integrity(self, data: list, file_name: str):
        #{{{
        """Проверить корректность цен."""
        
        errors_found = {
            'high_low': 0,
            'high_open': 0,
            'high_close': 0,
            'low_open': 0,
            'low_close': 0,
            'negative': 0
        }
        
        for i, item in enumerate(data):
            open_price = item['open']
            high = item['high']
            low = item['low']
            close = item['close']
            
            # 1. Проверяем high >= low
            if high < low:
                errors_found['high_low'] += 1
            
            # 2. Проверяем high >= open
            if high < open_price:
                errors_found['high_open'] += 1
            
            # 3. Проверяем high >= close
            if high < close:
                errors_found['high_close'] += 1
            
            # 4. Проверяем low <= open
            if low > open_price:
                errors_found['low_open'] += 1
            
            # 5. Проверяем low <= close
            if low > close:
                errors_found['low_close'] += 1
            
            # 6. Проверяем на отрицательные цены
            if open_price <= 0 or high <= 0 or low <= 0 or close <= 0:
                errors_found['negative'] += 1
        
        # Формируем сообщения об ошибках
        error_messages = []
        if errors_found['high_low'] > 0:
            error_messages.append(f"high < low: {errors_found['high_low']} строк")
        if errors_found['high_open'] > 0:
            error_messages.append(f"high < open: {errors_found['high_open']} строк")
        if errors_found['high_close'] > 0:
            error_messages.append(f"high < close: {errors_found['high_close']} строк")
        if errors_found['low_open'] > 0:
            error_messages.append(f"low > open: {errors_found['low_open']} строк")
        if errors_found['low_close'] > 0:
            error_messages.append(f"low > close: {errors_found['low_close']} строк")
        if errors_found['negative'] > 0:
            error_messages.append(f"отрицательные/нулевые цены: {errors_found['negative']} строк")
        
        if error_messages:
            self.errors.append(f"Файл: {file_name} - Ошибки цен: {', '.join(error_messages)}")
            self.total_errors += 1
        #}}}
    
    def _check_volume_integrity(self, data: list, file_name: str):
        #{{{
        """Проверить корректность объемов."""
        
        errors_found = {
            'negative_volume': 0,
            'negative_turnover': 0,
            'zero_volume_nonzero_turnover': 0
        }
        
        for i, item in enumerate(data):
            volume = item['volume']
            turnover = item['turnover']
            
            # 1. Проверяем отрицательные объемы
            if volume < 0:
                errors_found['negative_volume'] += 1
            
            # 2. Проверяем отрицательный turnover
            if turnover < 0:
                errors_found['negative_turnover'] += 1
            
            # 3. Проверяем, что при нулевом volume turnover тоже нулевой
            if volume == 0 and turnover != 0:
                errors_found['zero_volume_nonzero_turnover'] += 1
        
        # Формируем сообщения об ошибках
        error_messages = []
        if errors_found['negative_volume'] > 0:
            error_messages.append(f"отрицательный volume: {errors_found['negative_volume']} строк")
        if errors_found['negative_turnover'] > 0:
            error_messages.append(f"отрицательный turnover: {errors_found['negative_turnover']} строк")
        if errors_found['zero_volume_nonzero_turnover'] > 0:
            error_messages.append(f"нулевой volume с ненулевым turnover: {errors_found['zero_volume_nonzero_turnover']} строк")
        
        if error_messages:
            self.errors.append(f"Файл: {file_name} - Ошибки объемов: {', '.join(error_messages)}")
            self.total_errors += 1
        #}}}
    
    def _check_daily_completeness(self, data: list, file_name: str, file_date: datetime.date):
        #{{{
        """Проверить полноту данных за день."""
        
        if not data:
            return
        
        # Ожидаем 1440 минутных свечей (24 часа * 60 минут)
        min_expected_rows = 1440
        actual_rows = len(data)
        
        if actual_rows < min_expected_rows:
            missing = min_expected_rows - actual_rows
            self.errors.append(f"Файл: {file_name} - Недостаточно данных: {actual_rows} строк вместо {min_expected_rows} (пропущено {missing} минут)")
            self.total_errors += 1
        elif actual_rows > min_expected_rows:
            extra = actual_rows - min_expected_rows
            self.errors.append(f"Файл: {file_name} - Избыток данных: {actual_rows} строк вместо {min_expected_rows} (лишних {extra} записей)")
            self.total_errors += 1
        
        # Проверяем первую и последнюю свечу в UTC
        first_dt = datetime.fromtimestamp(data[0]['open_time'] / 1000, tz=timezone.utc)
        last_dt = datetime.fromtimestamp(data[-1]['open_time'] / 1000, tz=timezone.utc)
        
        # Для минутных данных в UTC первая свеча должна быть в 00:00 UTC, последняя в 23:59 UTC
        expected_first = datetime(file_date.year, file_date.month, file_date.day, 0, 0, 0, tzinfo=timezone.utc)
        expected_last = datetime(file_date.year, file_date.month, file_date.day, 23, 59, 0, tzinfo=timezone.utc)
        
        # Преобразуем время в строку для сравнения
        first_time_str = first_dt.strftime('%H:%M:%S')
        last_time_str = last_dt.strftime('%H:%M:%S')
        
        if first_dt != expected_first:
            self.errors.append(f"Файл: {file_name} - Первая свеча не в 00:00 UTC: {first_time_str} UTC")
            self.total_errors += 1
        
        if last_dt != expected_last:
            self.errors.append(f"Файл: {file_name} - Последняя свеча не в 23:59 UTC: {last_time_str} UTC")
            self.total_errors += 1
        
        # Дополнительная проверка: все свечи должны быть в правильный день UTC
        wrong_day_count = 0
        for item in data:
            dt = datetime.fromtimestamp(item['open_time'] / 1000, tz=timezone.utc)
            if dt.date() != file_date:
                wrong_day_count += 1
        
        if wrong_day_count > 0:
            self.errors.append(f"Файл: {file_name} - Свечи не в том дне (UTC): {wrong_day_count} строк")
            self.total_errors += 1
        #}}}
    
    def generate_report(self):
        #{{{
        """Создать текстовый отчет."""
        
        report_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        
        with open(self.report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("ОТЧЕТ ПРОВЕРКИ ЦЕЛОСТНОСТИ ДАННЫХ\n")
            f.write("=" * 70 + "\n\n")
            
            f.write(f"Дата проверки: {report_time}\n")
            f.write(f"Биржа: {self.exchange}\n")
            f.write(f"Рынок: {self.market}\n")
            f.write(f"Инструмент: {self.tool}\n")
            f.write(f"Директория данных: {self.data_path}\n")
            f.write(f"Файл отчета: {self.report_path}\n")
            f.write(f"Временная зона: UTC\n\n")
            
            f.write("-" * 70 + "\n")
            f.write("СТАТИСТИКА ПРОВЕРКИ\n")
            f.write("-" * 70 + "\n")
            f.write(f"Проверено файлов: {self.file_count}\n")
            f.write(f"Всего строк данных: {self.total_rows}\n")
            f.write(f"Найдено ошибок: {self.total_errors}\n\n")
            
            f.write("-" * 70 + "\n")
            f.write("ДЕТАЛЬНЫЙ ОТЧЕТ ОБ ОШИБКАХ\n")
            f.write("-" * 70 + "\n")
            
            if not self.errors:
                f.write("✓ Ошибок не обнаружено. Все данные корректны.\n")
            else:
                for i, error in enumerate(self.errors, 1):
                    f.write(f"{i}. {error}\n")
            
            f.write("\n" + "=" * 70 + "\n")
            f.write("ПРОВЕРКА ЗАВЕРШЕНА\n")
            f.write("=" * 70 + "\n")
        #}}}
    
    def run(self):
        #{{{
        """Запустить проверку."""
        self.check_all_files()
        self.generate_report()
        #}}}
#}}}

#{{{
def run():
    """Запустить проверку целостности данных."""
    
    # Очищаем экран перед запуском
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()
    
    # Получаем выбор инструмента через меню
    selection = exchange_selection_run()
    
    if selection is None:
        # Выход в левом нижнем углу
        sys.stdout.write("\033[2J\033[H")
        try:
            _, terminal_lines = shutil.get_terminal_size()
            sys.stdout.write(f"\033[{terminal_lines};1H")
            print("Выбор отменен. Выход.")
        except:
            print("Выбор отменен. Выход.")
        return None
    
    # Запускаем проверку
    checker = DataIntegrityChecker(
        exchange=selection['exchange'],
        market=selection['market'],
        tool=selection['tool']
    )
    
    checker.run()
    
    # Задержка перед завершением
    try:
        _, terminal_lines = shutil.get_terminal_size()
        sys.stdout.write(f"\033[{terminal_lines};1H")
        print("Нажмите Enter для выхода...")
        input()
    except:
        print("\nНажмите Enter для выхода...")
        input()
    
    return checker.report_path
#}}}

#{{{
if __name__ == "__main__":
    run()
#}}}
