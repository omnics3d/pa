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
        Эффективно работает даже с ТФ в 10032 минуты и более.
        """
        start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date_str, "%Y-%m-%d")
        
        aggregated_candles = []
        buffer = []  # Накопитель минут для формирования одной свечи ТФ
        
        current_dt = start_dt
        while current_dt <= end_dt:
            file_path = os.path.join(self.base_path, self._get_filename(current_dt))
            
            if os.path.exists(file_path):
                try:
                    with open(file_path, mode='r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            buffer.append({
                                't': int(row['timestamp']),
                                'o': float(row['open']),
                                'h': float(row['high']),
                                'l': float(row['low']),
                                'c': float(row['close'])
                            })
                            
                            # Если накопили достаточно минут для одного ТФ
                            if len(buffer) == timeframe_min:
                                aggregated_candles.append(self._make_candle(buffer))
                                buffer = []
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
            
            current_dt += timedelta(days=1)
            
        # Добавляем последнюю неполную свечу, если в буфере что-то осталось
        if buffer:
            aggregated_candles.append(self._make_candle(buffer))
            
        return aggregated_candles

    def _make_candle(self, chunk: List[Dict]) -> Dict:
        """Превращает набор минут в одну итоговую свечу."""
        return {
            't': chunk[0]['t'],           # Время открытия (первая минута)
            'o': chunk[0]['o'],           # Цена открытия
            'h': max(m['h'] for m in chunk), # Максимум за период
            'l': min(m['l'] for m in chunk), # Минимум за период
            'c': chunk[-1]['c']           # Цена закрытия (последняя минута)
        }

