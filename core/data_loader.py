import csv
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class DataLoader:
    def __init__(self, base_path: str, tool_name: str):
        self.base_path = base_path
        self.tool_name = tool_name
        # Сохраняем дату, на которой остановились, для подгрузки истории
        self._last_processed_date: Optional[datetime] = None

    def _get_filename(self, date: datetime) -> str:
        """Формирует имя файла: DOGEUSDT-1m-2021-08-30.csv"""
        return f"{self.tool_name}-1m-{date.strftime('%Y-%m-%d')}.csv"

    def get_candles(self, start_date_str: str, end_date_str: str, timeframe_min: int = 1, 
                    limit: int = 1000, offset_date: datetime = None) -> List[Dict]:
        """
        Загружает свечи с конца. 
        limit: сколько свечей нужно (экран + запас).
        offset_date: с какой даты начинать (для подгрузки глубокой истории).
        """
        abs_start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
        search_end_dt = offset_date if offset_date else datetime.strptime(end_date_str, "%Y-%m-%d")
        
        tf_seconds = timeframe_min * 60
        loaded_candles = []
        current_candle = None
        
        current_dt = search_end_dt
        
        while current_dt >= abs_start_dt and len(loaded_candles) < limit:
            file_path = os.path.join(self.base_path, self._get_filename(current_dt))
            
            if os.path.exists(file_path):
                day_minutes = self._read_csv(file_path)
                # Перебор минут дня в обратном порядке
                for m in reversed(day_minutes):
                    interval_start = (m['t'] // tf_seconds) * tf_seconds
                    
                    if current_candle is None or current_candle['t'] != interval_start:
                        if current_candle:
                            loaded_candles.append(current_candle)
                            if len(loaded_candles) >= limit: break
                        
                        current_candle = {
                            't': interval_start, 'o': m['o'], 'h': m['h'], 'l': m['l'], 'c': m['c']
                        }
                    else:
                        # Движемся назад: Open — это самая ранняя точка
                        current_candle['o'] = m['o']
                        if m['h'] > current_candle['h']: current_candle['h'] = m['h']
                        if m['l'] < current_candle['l']: current_candle['l'] = m['l']
                
                if len(loaded_candles) >= limit: break
            
            current_dt -= timedelta(days=1)
        
        if current_candle and len(loaded_candles) < limit:
            loaded_candles.append(current_candle)

        self._last_processed_date = current_dt - timedelta(days=1)
        
        # Сортируем от старых к новым для правильной отрисовки слева направо
        return sorted(loaded_candles, key=lambda x: x['t'])

    def _read_csv(self, path: str) -> List[Dict]:
        data = []
        try:
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) < 5: continue
                    t_str = row[0].strip().replace('"', '')
                    if not t_str.replace('.', '', 1).isdigit(): continue
                    try:
                        t_val = int(float(t_str))
                        if t_val > 2000000000: t_val //= 1000 # Коррекция ms -> s
                        data.append({
                            't': t_val,
                            'o': float(row[1]), 'h': float(row[2]), 
                            'l': float(row[3]), 'c': float(row[4])
                        })
                    except: continue
        except Exception as e:
            print(f"Error reading {path}: {e}")
        return data

