import csv
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class DataLoader:
    def __init__(self, base_path: str, tool_name: str):
        self.base_path = base_path
        self.tool_name = tool_name

    def _get_filename(self, date: datetime) -> str:
        """Формирует имя файла: DOGEUSDT-1m-2021-08-30.csv"""
        return f"{self.tool_name}-1m-{date.strftime('%Y-%m-%d')}.csv"

    def get_candles(self, start_date_str: str, end_date_str: str, timeframe_min: int = 1) -> List[Dict]:
        """
        Потоковая агрегация: читает файлы по дням и собирает свечу заданного размера.
        Эффективно работает с любыми таймфреймами (от 1 до 10032+ минут).
        """
        start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date_str, "%Y-%m-%d")
        
        aggregated_candles = []
        buffer = []  # Накопитель минут для формирования одной свечи ТФ
        
        current_dt = start_dt
        while current_dt <= end_dt:
            file_path = os.path.join(self.base_path, self._get_filename(current_dt))
            
            if os.path.exists(file_path):
                # Читаем данные дня через универсальный парсер
                day_minutes = self._read_csv(file_path)
                
                for minute_candle in day_minutes:
                    buffer.append(minute_candle)
                    
                    # Если накопили достаточно минут для одного ТФ
                    if len(buffer) == timeframe_min:
                        aggregated_candles.append(self._make_candle(buffer))
                        buffer = []
            
            current_dt += timedelta(days=1)
            
        # Добавляем последнюю неполную свечу, если в буфере что-то осталось
        if buffer:
            aggregated_candles.append(self._make_candle(buffer))
            
        return aggregated_candles

    def _read_csv(self, path: str) -> List[Dict]:
        """
        Универсальное чтение CSV: поддерживает файлы с заголовками и без.
        Использует позиционное чтение колонок (0-time, 1-open, 2-high, 3-low, 4-close).
        """
        day_data = []
        try:
            with open(path, mode='r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    # Пропуск пустых строк или строк с недостаточным кол-вом данных
                    if not row or len(row) < 5:
                        continue
                    
                    # Проверка: если первая колонка не число (заголовок), пропускаем строку
                    # Очищаем от возможных кавычек и пробелов перед проверкой
                    first_val = row[0].strip().replace('"', '')
                    if not first_val.replace('.', '', 1).replace('-', '', 1).isdigit():
                        continue
                        
                    try:
                        day_data.append({
                            't': int(float(row[0])), # timestamp
                            'o': float(row[1]),      # open
                            'h': float(row[2]),      # high
                            'l': float(row[3]),      # low
                            'c': float(row[4])       # close
                        })
                    except (ValueError, IndexError):
                        continue # Пропуск битых строк данных
        except Exception as e:
            # Логируем ошибку, но не прерываем работу программы
            print(f"Error reading {path}: {e}")
            
        return day_data

    def _make_candle(self, chunk: List[Dict]) -> Dict:
        """Превращает набор минут в одну итоговую японскую свечу."""
        return {
            't': chunk[0]['t'],               # Время открытия (первая минута)
            'o': chunk[0]['o'],               # Цена открытия
            'h': max(m['h'] for m in chunk),  # Максимум за период
            'l': min(m['l'] for m in chunk),  # Минимум за период
            'c': chunk[-1]['c']               # Цена закрытия (последняя минута)
        }

