# trend_validator.py (исправленная функция run())
from __future__ import annotations

import csv
import sys
from pathlib import Path

project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.exchange_manager import ExchangeDataManager
from core.logger_v2026 import setup_logging, get_logger
from core.basic_parser import CLIParser

logger = get_logger("trend_validator")

class TaskRunner:
    manager: ExchangeDataManager
    candle_count: int
    color_changes: int
    green_changes: int
    red_changes: int
    g_follows_2: int; r_follows_2: int
    g_follows_3: int; r_follows_3: int
    g_follows_4: int; r_follows_4: int
    g_follows_5: int; r_follows_5: int
    g_follows_6: int; r_follows_6: int
    last_color: str | None
    is_awaiting_2nd: bool; is_awaiting_3rd: bool
    is_awaiting_4th: bool; is_awaiting_5th: bool
    is_awaiting_6th: bool

    def __init__(self, manager: ExchangeDataManager) -> None:
        self.manager = manager
        self.candle_count = 0
        self.color_changes = 0
        self.green_changes = 0
        self.red_changes = 0
        self.g_follows_2 = 0; self.r_follows_2 = 0
        self.g_follows_3 = 0; self.r_follows_3 = 0
        self.g_follows_4 = 0; self.r_follows_4 = 0
        self.g_follows_5 = 0; self.r_follows_5 = 0
        self.g_follows_6 = 0; self.r_follows_6 = 0
        self.last_color = None
        self.is_awaiting_2nd = False; self.is_awaiting_3rd = False
        self.is_awaiting_4th = False; self.is_awaiting_5th = False
        self.is_awaiting_6th = False

    def _get_candle_color(self, open_p: float, close_p: float) -> str:
        return "GREEN" if close_p >= open_p else "RED"

    def _save_to_csv(self, data: dict, report_path: Path) -> None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            file_exists = report_path.exists()
            with open(report_path, "a", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=list(data.keys()))
                if not file_exists or f.tell() == 0:
                    writer.writeheader()
                writer.writerow(data)
        except Exception as e:
            logger.error(f"Ошибка сохранения CSV: {e}")

    def process_file(self, path: Path, report_path: Path) -> None:
        self.candle_count = 0; self.color_changes = 0
        self.green_changes = 0; self.red_changes = 0
        self.g_follows_2 = 0; self.r_follows_2 = 0
        self.g_follows_3 = 0; self.r_follows_3 = 0
        self.g_follows_4 = 0; self.r_follows_4 = 0
        self.g_follows_5 = 0; self.r_follows_5 = 0
        self.g_follows_6 = 0; self.r_follows_6 = 0
        self.last_color = None
        self.is_awaiting_2nd = True; self.is_awaiting_3rd = False
        self.is_awaiting_4th = False; self.is_awaiting_5th = False
        self.is_awaiting_6th = False

        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    parts = line.split(",")
                    if len(parts) < 5: continue
                    try:
                        open_p = float(parts[1]); close_p = float(parts[4])
                    except (ValueError, IndexError): continue
                    curr_col = self._get_candle_color(open_p, close_p)
                    self.candle_count += 1
                    if self.last_color is None:
                        self.last_color = curr_col
                        continue
                    if curr_col != self.last_color:
                        self.color_changes += 1
                        if curr_col == "GREEN": self.green_changes += 1
                        else: self.red_changes += 1
                        self.last_color = curr_col
                        self.is_awaiting_2nd = True; self.is_awaiting_3rd = False
                        self.is_awaiting_4th = False; self.is_awaiting_5th = False
                        self.is_awaiting_6th = False
                        continue
                    if self.is_awaiting_2nd:
                        if curr_col == "GREEN": self.g_follows_2 += 1
                        else: self.r_follows_2 += 1
                        self.is_awaiting_2nd = False; self.is_awaiting_3rd = True; continue
                    if self.is_awaiting_3rd:
                        if curr_col == "GREEN": self.g_follows_3 += 1
                        else: self.r_follows_3 += 1
                        self.is_awaiting_3rd = False; self.is_awaiting_4th = True; continue
                    if self.is_awaiting_4th:
                        if curr_col == "GREEN": self.g_follows_4 += 1
                        else: self.r_follows_4 += 1
                        self.is_awaiting_4th = False; self.is_awaiting_5th = True; continue
                    if self.is_awaiting_5th:
                        if curr_col == "GREEN": self.g_follows_5 += 1
                        else: self.r_follows_5 += 1
                        self.is_awaiting_5th = False; self.is_awaiting_6th = True; continue
                    if self.is_awaiting_6th:
                        if curr_col == "GREEN": self.g_follows_6 += 1
                        else: self.r_follows_6 += 1
                        self.is_awaiting_6th = False

            f2 = self.g_follows_2 + self.r_follows_2
            f3 = self.g_follows_3 + self.r_follows_3
            f4 = self.g_follows_4 + self.r_follows_4
            f5 = self.g_follows_5 + self.r_follows_5
            f6 = self.g_follows_6 + self.r_follows_6

            def pc(v): return round((v / self.candle_count * 100), 2) if self.candle_count > 0 else 0
            def prob(curr, prev): return round((curr / prev * 100), 2) if prev > 0 else 0
            def ch_pc(v): return round((v / self.color_changes * 100), 2) if self.color_changes > 0 else 0
            def ratio(v, t): return round((v / t * 100), 2) if t > 0 else 0

            res = {
                "file": path.name, "candles": self.candle_count,
                "ch_t": self.color_changes, "ch_%": pc(self.color_changes),
                "ch_g": self.green_changes, "ch_g_%": ch_pc(self.green_changes),
                "ch_r": self.red_changes, "ch_r_%": ch_pc(self.red_changes),
                "p1_c": prob(f2, self.color_changes), "p1_r": round(100 - prob(f2, self.color_changes), 2) if self.color_changes > 0 else 0,
                "p2_c": prob(f3, f2), "p2_r": round(100 - prob(f3, f2), 2) if f2 > 0 else 0,
                "p3_c": prob(f4, f3), "p3_r": round(100 - prob(f4, f3), 2) if f3 > 0 else 0,
                "p4_c": prob(f5, f4), "p4_r": round(100 - prob(f5, f4), 2) if f4 > 0 else 0,
                "p5_c": prob(f6, f5), "p5_r": round(100 - prob(f6, f5), 2) if f5 > 0 else 0,
                "f2_t": f2, "f2_%": pc(f2), "f2_g": self.g_follows_2, "f2_g_%": ratio(self.g_follows_2, f2), "f2_r": self.r_follows_2, "f2_r_%": ratio(self.r_follows_2, f2),
                "f3_t": f3, "f3_%": pc(f3), "f3_g": self.g_follows_3, "f3_g_%": ratio(self.g_follows_3, f3), "f3_r": self.r_follows_3, "f3_r_%": ratio(self.r_follows_3, f3),
                "f4_t": f4, "f4_%": pc(f4), "f4_g": self.g_follows_4, "f4_g_%": ratio(self.g_follows_4, f4), "f4_r": self.r_follows_4, "f4_r_%": ratio(self.r_follows_4, f4),
                "f5_t": f5, "f5_%": pc(f5), "f5_g": self.g_follows_5, "f5_g_%": ratio(self.g_follows_5, f5), "f5_r": self.r_follows_5, "f5_r_%": ratio(self.r_follows_5, f5),
                "f6_t": f6, "f6_%": pc(f6), "f6_g": self.g_follows_6, "f6_g_%": ratio(self.g_follows_6, f6), "f6_r": self.r_follows_6, "f6_r_%": ratio(self.r_follows_6, f6)
            }
            self._save_to_csv(res, report_path)
            logger.info(f"Файл {path.name} обработан: {self.candle_count}")
        except Exception as e:
            logger.error(f"Ошибка в файле {path.name}: {e}")

    def run_logic(self, args: any) -> None:
        rep_dir = Path(f"storage/reports/{args.exchange}/{args.market}/{args.tool}")
        rep_file = rep_dir / "script_1_report.csv"
        if rep_file.exists(): rep_file.unlink()
        data_dir = Path(f"data/{args.exchange}/{args.market}/{args.tool}/tf_base")
        if not data_dir.exists(): return
        idx = 5
        while (f_path := data_dir / f"{idx}.csv").exists():
            self.process_file(f_path, rep_file)
            idx += 1

def run():
    try:
        # Поднимаемся до корня проекта (папка pa/)
        base_path = Path(__file__).parent.parent.parent.parent
        xml_path = base_path / "config" / "exchanges_config.xml"
        
        manager = ExchangeDataManager(str(xml_path))
        parser = CLIParser(manager)
        args = parser.parse()
        runner = TaskRunner(manager)
        runner.run_logic(args)
    except Exception as e:
        logger.critical(f"Ошибка запуска: {e}", exc_info=True)

if __name__ == "__main__":
    run()
