"""
Скрипт №1: Анализ свечей и последовательностей (v2026.2).

Считает подтверждения с 2 по 6 свечу после смены тренда или старта.
Результаты сохраняются в динамический CSV отчет.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

# Добавление корня проекта в sys.path для доступа к core
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.exchange_manager import ExchangeDataManager
from core.logger_v2026_code import setup_logging, get_logger
from core.basic_parser import CLIParser

logger = get_logger("script_1")


class TaskRunner:
    """Класс для выполнения анализа свечей и генерации отчетов."""

    manager: ExchangeDataManager
    candle_count: int
    color_changes: int
    green_changes: int
    red_changes: int
    g_follows_2: int
    r_follows_2: int
    g_follows_3: int
    r_follows_3: int
    g_follows_4: int
    r_follows_4: int
    g_follows_5: int  # Подтверждение 5-й свечи
    r_follows_5: int
    g_follows_6: int  # Подтверждение 6-й свечи
    r_follows_6: int
    last_color: str | None
    is_awaiting_2nd: bool
    is_awaiting_3rd: bool
    is_awaiting_4th: bool
    is_awaiting_5th: bool  # Ожидаем ли мы 5-ю свечу
    is_awaiting_6th: bool  # Ожидаем ли мы 6-ю свечу

    def __init__(self, manager: ExchangeDataManager) -> None:
        """Инициализация свойств раннера."""
        self.manager = manager
        self.candle_count = 0
        self.color_changes = 0
        self.green_changes = 0
        self.red_changes = 0
        self.g_follows_2 = 0
        self.r_follows_2 = 0
        self.g_follows_3 = 0
        self.r_follows_3 = 0
        self.g_follows_4 = 0
        self.r_follows_4 = 0
        self.g_follows_5 = 0
        self.r_follows_5 = 0
        self.g_follows_6 = 0
        self.r_follows_6 = 0
        self.last_color = None
        self.is_awaiting_2nd = False
        self.is_awaiting_3rd = False
        self.is_awaiting_4th = False
        self.is_awaiting_5th = False
        self.is_awaiting_6th = False

    def _get_candle_color(self, open_p: float, close_p: float) -> str:
        """Определяет цвет. Доджи (close >= open) считаются GREEN."""
        return "GREEN" if close_p >= open_p else "RED"

    def _save_to_csv(self, data: dict, report_path: Path) -> None:
        """Дописывает результаты обработки файла в CSV отчет."""
        report_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            file_exists = report_path.exists()
            with open(report_path, "a", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=data.keys())
                if not file_exists or f.tell() == 0:
                    writer.writeheader()
                writer.writerow(data)
        except Exception as e:
            logger.error(f"Ошибка сохранения CSV: {e}")

    def process_file(self, path: Path, report_path: Path) -> None:
        """Анализирует один файл и фиксирует статистику."""
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
                    ts = parts; open_p = float(parts); close_p = float(parts)
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
                        self.is_awaiting_2nd = True
                        self.is_awaiting_3rd = False
                        self.is_awaiting_4th = False
                        self.is_awaiting_5th = False
                        self.is_awaiting_6th = False
                        continue
                    
                    if self.is_awaiting_2nd:
                        if curr_col == "GREEN": self.g_follows_2 += 1
                        else: self.r_follows_2 += 1
                        self.is_awaiting_2nd = False
                        self.is_awaiting_3rd = True; continue
                    if self.is_awaiting_3rd:
                        if curr_col == "GREEN": self.g_follows_3 += 1
                        else: self.r_follows_3 += 1
                        self.is_awaiting_3rd = False
                        self.is_awaiting_4th = True; continue
                    if self.is_awaiting_4th:
                        if curr_col == "GREEN": self.g_follows_4 += 1
                        else: self.r_follows_4 += 1
                        self.is_awaiting_4th = False
                        self.is_awaiting_5th = True; continue
                    if self.is_awaiting_5th:
                        if curr_col == "GREEN": self.g_follows_5 += 1
                        else: self.r_follows_5 += 1
                        self.is_awaiting_5th = False
                        self.is_awaiting_6th = True; continue
                    if self.is_awaiting_6th:
                        if curr_col == "GREEN": self.g_follows_6 += 1
                        else: self.r_follows_6 += 1
                        self.is_awaiting_6th = False
                        logger.debug(f"Follow 6 (6-я св.) на {ts}")

            res = {
                "file": path.name, "candles": self.candle_count,
                "ch_total": self.color_changes, "ch_green": self.green_changes,
                "ch_red": self.red_changes,
                "f2_total": self.g_follows_2 + self.r_follows_2,
                "f2_green": self.g_follows_2, "f2_red": self.r_follows_2,
                "f3_total": self.g_follows_3 + self.r_follows_3,
                "f3_green": self.g_follows_3, "f3_red": self.r_follows_3,
                "f4_total": self.g_follows_4 + self.r_follows_4,
                "f4_green": self.g_follows_4, "f4_red": self.r_follows_4,
                "f5_total": self.g_follows_5 + self.r_follows_5,
                "f5_green": self.g_follows_5, "f5_red": self.r_follows_5,
                "f6_total": self.g_follows_6 + self.r_follows_6,
                "f6_green": self.g_follows_6, "f6_red": self.r_follows_6
            }
            self._save_to_csv(res, report_path)
            logger.info(f"Файл {path.name} обработан: {self.candle_count}")

        except Exception as e:
            logger.error(f"Сбой при обработке {path.name}: {e}")

    # run() и main() остаются прежними
    def run(self, args: any) -> None:
        """Запуск цикла обработки файлов."""
        rep_dir = Path(
            f"storage/reports/{args.exchange}/{args.market}/{args.tool}"
        )
        rep_file = rep_dir / "script_1_report.csv"
        if rep_file.exists(): rep_file.unlink()
        data_dir = Path(
            f"data/{args.exchange}/{args.market}/{args.tool}/tf_base"
        )
        if not data_dir.exists():
            logger.error(f"Путь не найден: {data_dir}")
            sys.exit(1)
        idx = 5
        while (f_path := data_dir / f"{idx}.csv").exists():
            self.process_file(f_path, rep_file)
            idx += 1
        logger.info(f"Скрипт завершен. Отчет: {rep_file}")

def main() -> None:
    """Точка входа."""
    setup_logging(
        level="DEBUG",
        log_files={"DEBUG": "logs/all_scripts.log"},
        json_format=True, use_colors=True,
    )
    try:
        manager = ExchangeDataManager("storage/state/exchanges_config.xml")
        args = CLIParser(manager).parse()
        runner = TaskRunner(manager)
        runner.run(args)
    except Exception as exc: logger.exception(f"Сбой: {exc}"); sys.exit(1)

if __name__ == "__main__":
    main()

