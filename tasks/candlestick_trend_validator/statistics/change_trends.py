# tasks/candlestick_trend_validator/statistics/change_trends.py
import sys
import os
import csv

parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(parent_dir)

try:
    from lib.exchange_selection import ExchangeMenu
except ImportError:
    print("Ошибка: Не удалось импортировать модуль exchange_selection из lib")
    sys.exit(1)


class StatisticsTrendAnalyzer:
    def __init__(self):
        self.exchange_name = None
        self.market_name = None
        self.tool_name = None
        self.normalized_data_path = None
        self.report_data_path = None
    
    def get_selection(self):
        try:
            menu = ExchangeMenu()
            result = menu.display_exchanges()
            
            if result is None:
                print("Выбор отменен пользователем")
                return False
                
            self.exchange_name = result.get("exchange", "")
            self.market_name = result.get("market", "")
            self.tool_name = result.get("tool", "")
            
            return True
            
        except Exception as e:
            print(f"Ошибка при работе с меню выбора: {e}")
            return False
    
    def build_paths(self):
        if not all([self.exchange_name, self.market_name, self.tool_name]):
            print("Ошибка: Не все значения выбраны")
            return False
            
        self.normalized_data_path = os.path.join(
            "storage",
            "processed",
            "normalized",
            self.exchange_name,
            self.market_name,
            self.tool_name
        )
        
        self.report_data_path = os.path.join(
            "storage",
            "reports",
            "concept",
            "1",
            self.exchange_name,
            self.market_name,
            self.tool_name
        )
        
        return True
    
    def get_candle_color(self, close, open_price):
        if close > open_price:
            return 'зелёная'
        elif close < open_price:
            return 'красная'
        else:
            return 'нейтральная'
    
    def analyze_all_csv_files(self):
        """Анализирует все CSV файлы и записывает результаты в 1_GENERAL_STATISTICS.csv"""
        if not os.path.exists(self.normalized_data_path):
            print(f"Ошибка: Путь не существует: {self.normalized_data_path}")
            return
        
        print(f"\nАнализ файлов в директории: {self.normalized_data_path}")
        print("-" * 60)
        
        results = []
        file_counter = 1
        
        while True:
            file_name = f"{file_counter}.csv"
            file_path = os.path.join(self.normalized_data_path, file_name)
            
            if not os.path.exists(file_path):
                print(f"\nФайл {file_name} не найден. Анализ завершен.")
                break
            
            # Выводим только имя файла
            print(f"Анализирую файл: {file_name}")
            
            try:
                stats = self.analyze_single_file(file_path, file_name)
                if stats:
                    results.append(stats)
                else:
                    print(f"  ✗ Ошибка обработки: {file_name}")
                    
            except Exception as e:
                print(f"  ✗ Ошибка при анализе {file_name}: {e}")
            
            file_counter += 1
        
        # Сохраняем результаты в 1_GENERAL_STATISTICS.csv
        if results:
            self.save_results_to_csv(results)
        else:
            print("Нет данных для сохранения")
    
    def analyze_single_file(self, file_path, file_name):
        """Анализирует один CSV файл и возвращает статистику"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                
                # Пропускаем заголовок, если есть
                try:
                    headers = next(reader)
                except StopIteration:
                    return None
                
                # Находим индексы нужных столбцов
                try:
                    open_idx = headers.index('open')
                    close_idx = headers.index('close')
                except ValueError:
                    # Если заголовков нет, предполагаем стандартный порядок
                    open_idx = 1  # второй столбец
                    close_idx = 4  # пятый столбец
                    # Возвращаемся к началу файла
                    file.seek(0)
                    reader = csv.reader(file)
                    next(reader)  # снова пропускаем заголовок
                
                total_candles = 0
                total_changes = 0
                previous_color = None
                
                for row in reader:
                    # Пропускаем пустые строки
                    if not row or len(row) < 5:
                        continue
                    
                    try:
                        open_price = float(row[open_idx])
                        close_price = float(row[close_idx])
                        current_color = self.get_candle_color(close_price, open_price)
                        
                        total_candles += 1
                        
                        # Подсчитываем смены (игнорируем нейтральные свечи)
                        if previous_color is not None and current_color != 'нейтральная':
                            if previous_color != current_color:
                                total_changes += 1
                        
                        previous_color = current_color
                        
                    except (ValueError, IndexError):
                        continue
            
            if total_candles == 0:
                return None
            
            total_transitions = total_candles - 1
            
            # Рассчитываем проценты с округлением до 2 знаков
            change_percentage_transitions = round((total_changes / total_transitions * 100) if total_transitions > 0 else 0, 2)
            change_percentage_candles = round((total_changes / total_candles * 100) if total_candles > 0 else 0, 2)
            
            # Возвращаем статистику
            return {
                'file_name': file_name,
                'total_candles': total_candles,
                'total_transitions': total_transitions,
                'total_changes': total_changes,
                'change_percentage_transitions': change_percentage_transitions,
                'change_percentage_candles': change_percentage_candles
            }
            
        except Exception as e:
            print(f"Ошибка при анализе файла {file_name}: {e}")
            return None
    
    def save_results_to_csv(self, results):
        """Сохраняет результаты анализа в файл 1_GENERAL_STATISTICS.csv"""
        try:
            # Создаем директорию для отчетов, если она не существует
            os.makedirs(self.report_data_path, exist_ok=True)
            
            # Путь к файлу отчета
            report_file = os.path.join(self.report_data_path, "1_GENERAL_STATISTICS.csv")
            
            # Заголовки для CSV файла
            headers = [
                "file_name",
                "total_candles",
                "total_transitions",
                "total_changes",
                "change_percentage_transitions",
                "change_percentage_candles"
            ]
            
            # Записываем данные в CSV
            with open(report_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                
                # Записываем заголовки
                writer.writeheader()
                
                # Записываем данные по каждому файлу
                for result in results:
                    writer.writerow(result)
            
            print(f"\nРезультаты сохранены в: {report_file}")
            print(f"Всего обработано файлов: {len(results)}")
            
        except Exception as e:
            print(f"Ошибка при сохранении результатов: {e}")
    
    def analyze_trends(self):
        """Основной метод анализа тенденций"""
        if not self.get_selection():
            return
            
        if not self.build_paths():
            return
            
        print(f"\nВыбрано: {self.exchange_name}/{self.market_name}/{self.tool_name}")
        
        # Анализируем все CSV файлы
        self.analyze_all_csv_files()
        
        print("\nАнализ завершен.")


def run():
    """Основная функция запуска скрипта"""
    analyzer = StatisticsTrendAnalyzer()
    analyzer.analyze_trends()


if __name__ == "__main__":
    run()
