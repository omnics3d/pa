"""Модуль для автоматического управления версиями проекта в pyproject.toml.

Данный скрипт предназначен для инкремента четвертого сегмента версии (Build),
следуя формату MAJOR.MINOR.PATCH.BUILD (например, 1.0.0.1 -> 1.0.0.2).

:platform: Unix, Windows
:synopsis: Автоматизация инкремента версии и интеграция с Git-хуками.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Final

# Импорт системы логирования проекта
try:
    from logger_v2026 import get_logger, setup_logging
except ImportError:
    # На случай запуска из корня как модуля
    from core.logger_v2026 import get_logger, setup_logging	

    def get_logger(name: str) -> logging.Logger:
        """Возвращает стандартный логгер при отсутствии core."""
        return logging.getLogger(name)

    def setup_logging(**kwargs: str | bool | dict) -> None:
        """Настраивает базовое логирование при отсутствии core."""
        logging.basicConfig(level=logging.INFO)

# Инициализация констант
VERSION_PATTERN: Final[str] = (
    r'(?P<pre>version\s*=\s*")'
    r'(?P<base>\d+\.\d+\.\d+\.)'
    r'(?P<build>\d+)'
    r'(?P<suf>")'
)

logger = get_logger("VersionBumper")


def increment_build_number(file_path: str = "pyproject.toml") -> bool:
    """Выполняет инкремент четвертого сегмента номера версии.

    Считывает файл конфигурации, находит строку версии и увеличивает последнее
    число на единицу. После записи изменений пытается добавить файл в индекс Git.

    :param file_path: Путь к файлу конфигурации. По умолчанию 'pyproject.toml'.
    :type file_path: str
    :return: True, если обновление прошло успешно или строка версии не найдена.
             False при критических ошибках доступа к файлу.
    :rtype: bool
    :raises OSError: При невозможности чтения или записи в файловой системе.
    """
    path = Path(file_path)

    if not path.exists():
        logger.error("Ошибка: Файл конфигурации '%s' не найден.", file_path)
        return False

    try:
        content = path.read_text(encoding="utf-8")
    except OSError:
        logger.exception("Критическая ошибка чтения %s", file_path)
        return False

    match = re.search(VERSION_PATTERN, content)
    if not match:
        logger.warning("Строка версии X.X.X.X не найдена в %s.", file_path)
        return True

    try:
        new_build = int(match.group("build")) + 1
        new_version = (
            f"{match.group('pre')}{match.group('base')}{new_build}"
            f"{match.group('suf')}"
        )
    except (ValueError, IndexError):
        logger.exception("Ошибка парсинга сегментов версии")
        return False

    new_content = re.sub(VERSION_PATTERN, new_version, content, count=1)

    try:
        path.write_text(new_content, encoding="utf-8")
        logger.info("Версия обновлена до: %s%s", match.group("base"), new_build)
    except OSError:
        logger.exception("Ошибка записи в %s", file_path)
        return False

    return _stage_to_git(file_path)


def _stage_to_git(file_path: str) -> bool:
    """Добавляет измененный файл в индекс (Staging Area) Git.

    Используется для того, чтобы изменения версии попали в текущий коммит
    при работе скрипта в режиме Git-хука.

    :param file_path: Путь к индексируемому файлу.
    :type file_path: str
    :return: Всегда возвращает True, чтобы не блокировать коммит ошибками Git.
    :rtype: bool
    """
    try:
        subprocess.run(
            ["git", "add", file_path],
            check=True,
            capture_output=True,
            text=True,
        )
        logger.info("Файл '%s' проиндексирован в Git.", file_path)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.debug("Git add пропущен или не удался для %s", file_path)

    return True


def run() -> None:
    """Интерфейсная функция для запуска из внешних менеджеров (main.py).

    Выполняет запуск процесса обновления версии в интерактивном режиме.
    """
    logger.info("Ручной запуск обновления версии...")
    increment_build_number()


if __name__ == "__main__":
    # Теперь всегда используются те же настройки, что и в main.py
    setup_logging(
        level="DEBUG",
        log_files={"DEBUG": "logs/all_scripts.log"},
        json_format=True,
        use_colors=True,
    )

    if not increment_build_number():
        sys.exit(1)

