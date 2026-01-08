from __future__ import annotations

import atexit
import logging
import logging.config
import logging.handlers
import queue
import sys
from pathlib import Path
from types import TracebackType
from typing import Any, Final, Literal, Type, Union

LogLevel = int | Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

try:
    import concurrent_log_handler
    _HAS_CONCURRENT = True
except ImportError:
    _HAS_CONCURRENT = False

try:
    from pythonjsonlogger import jsonlogger
    _HAS_JSON = True
except ImportError:
    _HAS_JSON = False

try:
    import colorlog
    _HAS_COLORS = True
except ImportError:
    _HAS_COLORS = False

__all__ = ["setup_logging", "get_logger"]

DEFAULT_FORMAT: Final = (
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
COLOR_FORMAT: Final = (
        "%(log_color)s" + DEFAULT_FORMAT + "%(reset)s"
)
MAX_LOG_SIZE: Final = 20 * 1024 * 1024  # 20 MB
BACKUP_COUNT: Final = 7

_LOG_QUEUE: queue.Queue[logging.LogRecord] = queue.Queue(-1)
_LISTENER: logging.handlers.QueueListener | None = None

class SpecificLevelFilter(logging.Filter):

    def __init__(self, level: int) -> None:
        super().__init__()
        self._level = level

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno == self._level

class SafeJsonFormatter(
        jsonlogger.JsonFormatter if _HAS_JSON else object
):

    SENSITIVE_KEYS: Final = {
            "password", "token", "secret", "authorization", "key","api_key",
            "cookie"
    }

    def add_fields(
            self,
            log_record: dict[str, Any],
            record: logging.LogRecord,
            message_dict: dict[str, Any],
    ) -> None:
        if _HAS_JSON:
            super().add_fields(log_record, record, message_dict)

        for key in self.SENSITIVE_KEYS:
            if key in log_record:
                log_record[key] = "********"

def _get_level_int(level: LogLevel) -> int:
    if isinstance(level, int):
        return level
    return getattr(logging, level.upper(), logging.INFO)

def handle_exception(
        exc_type: Type[BaseException],
        exc_value: BaseException,
        exc_traceback: TracebackType | None,
) -> None:
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logging.getLogger().critical(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback)
    )

def setup_logging(
        level: LogLevel = "INFO",
        log_files: dict[LogLevel, str | Path] | None = None,
        json_format: bool = True,
        use_colors: bool = True,
) -> None:
    global _LISTENER
    if _LISTENER is not None:
        return
    
    main_numeric_level = _get_level_int(level)
    target_handlers: list[logging.Handler] = []

    # 1. Консольный вывод
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(main_numeric_level)

    if _HAS_COLORS and use_colors:
        console_handler.setFormatter(
                colorlog.ColoredFormatter(COLOR_FORMAT)
        )
    else:
        console_handler.setFormatter(
                logging.Formatter(DEFAULT_FORMAT)
        )
    target_handlers.append(console_handler)

    # 2. Файловые выводы
    required_levels: list[int] = [main_numeric_level]

    if log_files:
        handler_cls = (
                concurrent_log_handler.ConcurrentRotatingFileHandler
                if _HAS_CONCURRENT
                else logging.handlers.RotatingFileHandler
        )

        for lvl_key, path in log_files.items():
            lvl_int = _get_level_int(lvl_key)
            required_levels.append(lvl_int)

            log_path = Path(path).absolute()
            log_path.parent.mkdir(parents=True, exist_ok=True)

            h = handler_cls(
                    str(log_path), "a", MAX_LOG_SIZE,
                    BACKUP_COUNT, encoding="utf-8"
            )
            h.addFilter(SpecificLevelFilter(lvl_int))

            if json_format and _HAS_JSON:
                h.setFormatter(SafeJsonFormatter(
                    "%(asctime)s %(levelname)s %(name)s %(message)s"
                ))
            else:
                h.setFormatter(logging.Formatter(DEFAULT_FORMAT))

            target_handlers.append(h)

    # 3. Привязка к Root логгеру
    root_logger = logging.getLogger()
    root_logger.setLevel(min(required_levels))

    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)

    root_logger.addHandler(logging.handlers.QueueHandler(_LOG_QUEUE))

    _LISTENER = logging.handlers.QueueListener(
            _LOG_QUEUE, *target_handlers, respect_handler_level=True
    )
    _LISTENER.start()

    atexit.register(_LISTENER.stop)
    sys.excepthook = handle_exception

def get_logger(name: str | None = None) -> logging.Logger:
    return logging.getLogger(name)
