#!/usr/bin/env python3
"""
Version bumper для автоматического увеличения билд-номера в pyproject.toml.

Используется как git pre-commit hook. При каждом коммите автоматически
увеличивает билд-номер (4-я цифра версии, отделенная тире) в файле
pyproject.toml в разделе [project] и добавляет обновленный файл в git
staging area.

Формат версии: MAJOR.MINOR.PATCH-BUILD
Пример: 1.0.0-1 → 1.0.0-2
"""

import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
import toml


class VersionInfo:
    """
    Представление версии проекта в формате семантического версионирования.

    Версия состоит из четырех компонентов: major, minor, patch и build,
    где билд-номер отделен от первых трех компонентов тире в соответствии
    с SemVer 2.0.0.

    Attributes
    ----------
    major : int
        Мажорная версия, увеличивается при несовместимых изменениях API.
    minor : int
        Минорная версия, увеличивается при добавлении функциональности с
        обратной совместимостью.
    patch : int
        Патч-версия, увеличивается при обратно-совместимых исправлениях
        ошибок.
    build : int
        Билд-номер, увеличивается автоматически при каждом коммите для
        уникальной идентификации сборки.
    """

    def __init__(self, major: int, minor: int, patch: int,
                 build: Optional[int] = None):
        """
        Инициализирует новый экземпляр VersionInfo.

        Parameters
        ----------
        major : int
            Мажорная версия (положительное целое число).
        minor : int
            Минорная версия (положительное целое число).
        patch : int
            Патч-версия (положительное целое число).
        build : int, optional
            Билд-номер (положительное целое число), по умолчанию 0.
        """
        self.major = major
        self.minor = minor
        self.patch = patch
        self.build = build if build is not None else 0

    def __str__(self) -> str:
        """
        Возвращает строковое представление версии.

        Returns
        -------
        str
            Версия в формате 'MAJOR.MINOR.PATCH-BUILD'.

        Examples
        --------
        >>> v = VersionInfo(1, 2, 3, 4)
        >>> str(v)
        '1.2.3-4'
        """
        return f"{self.major}.{self.minor}.{self.patch}-{self.build}"

    def bump_build(self) -> None:
        """
        Увеличивает билд-номер на единицу.

        Этот метод используется для автоматического увеличения номера
        сборки при каждом коммите в репозиторий. Билд-номер инкрементируется
        независимо от других компонентов версии.

        Examples
        --------
        >>> v = VersionInfo(1, 2, 3, 4)
        >>> v.bump_build()
        >>> str(v)
        '1.2.3-5'
        """
        self.build += 1

    @classmethod
    def from_string(cls, version_str: str) -> "VersionInfo":
        """
        Создает экземпляр VersionInfo из строкового представления.

        Поддерживает только формат с тире: 'MAJOR.MINOR.PATCH-BUILD'.
        Префикс 'v' или 'V' в начале строки игнорируется.

        Parameters
        ----------
        version_str : str
            Строковое представление версии в формате
            'MAJOR.MINOR.PATCH-BUILD'.

        Returns
        -------
        VersionInfo
            Новый экземпляр класса VersionInfo.

        Raises
        ------
        ValueError
            Если строка не соответствует формату 'MAJOR.MINOR.PATCH-BUILD'
            или содержит нечисловые компоненты.

        Examples
        --------
        >>> VersionInfo.from_string('1.2.3-4')
        VersionInfo(1, 2, 3, 4)
        >>> VersionInfo.from_string('v1.2.3-5')
        VersionInfo(1, 2, 3, 5)
        """
        version_str = version_str.lstrip('vV').strip()

        if '-' not in version_str:
            raise ValueError(
                f"Версия должна быть в формате MAJOR.MINOR.PATCH-BUILD: "
                f"{version_str}"
            )

        main_part, build_part = version_str.split('-', 1)
        build_part = build_part.split('+')[0]

        try:
            build = int(build_part)
        except ValueError:
            raise ValueError(
                f"Билд-номер должен быть целым числом: {build_part}"
            )

        main_parts = main_part.split('.')
        if len(main_parts) != 3:
            raise ValueError(
                f"Основная часть версии должна содержать 3 компонента: "
                f"{main_part}"
            )

        try:
            major = int(main_parts[0])
            minor = int(main_parts[1])
            patch = int(main_parts[2])
        except ValueError as e:
            raise ValueError(
                f"Компоненты версии должны быть целыми числами: {e}"
            )

        return cls(major, minor, patch, build)


def read_pyproject_version(pyproject_path: Path) -> tuple[VersionInfo,
                                                          Dict[str, Any]]:
    """
    Извлекает информацию о версии из файла pyproject.toml.

    Функция ищет поле 'version' ТОЛЬКО в разделе [project] pyproject.toml
    в соответствии со спецификацией PEP 621. Другие разделы (tool.poetry,
    tool.pdm) игнорируются.

    Parameters
    ----------
    pyproject_path : Path
        Путь к файлу pyproject.toml.

    Returns
    -------
    tuple[VersionInfo, Dict[str, Any]]
        Кортеж, содержащий:
        - VersionInfo: объект с информацией о версии
        - Dict: полное содержимое pyproject.toml в виде словаря

    Raises
    ------
    ValueError
        Если файл pyproject.toml не существует или не содержит поля
        'version' в разделе [project].

    Examples
    --------
    >>> version, data = read_pyproject_version(Path('pyproject.toml'))
    >>> str(version)
    '1.0.0-1'
    """
    if not pyproject_path.exists():
        raise ValueError(f"Файл не найден: {pyproject_path}")

    try:
        with open(pyproject_path, 'r', encoding='utf-8') as f:
            data = toml.load(f)

        if 'project' not in data:
            raise ValueError("Раздел [project] не найден в pyproject.toml")

        if 'version' not in data['project']:
            raise ValueError(
                "Поле 'version' не найдено в разделе [project]"
            )

        version_str = data['project']['version']
        return VersionInfo.from_string(version_str), data

    except Exception as e:
        raise ValueError(f"Ошибка чтения pyproject.toml: {e}")


def write_pyproject_version(pyproject_path: Path, version_info: VersionInfo,
                            data: Dict[str, Any]) -> bool:
    """
    Записывает обновленную версию обратно в файл pyproject.toml.

    Функция обновляет поле 'version' ТОЛЬКО в разделе [project]
    pyproject.toml. Структура файла сохраняется, включая все комментарии
    и форматирование, за исключением обновленного поля версии.

    Parameters
    ----------
    pyproject_path : Path
        Путь к файлу pyproject.toml.
    version_info : VersionInfo
        Объект с новой версией.
    data : Dict[str, Any]
        Содержимое pyproject.toml в виде словаря.

    Returns
    -------
    bool
        True если запись прошла успешно, False в случае ошибки.

    Examples
    --------
    >>> success = write_pyproject_version(Path('pyproject.toml'),
    ...                                   version_info, data)
    >>> success
    True
    """
    version_str = str(version_info)

    if 'project' not in data:
        data['project'] = {}

    data['project']['version'] = version_str

    try:
        with open(pyproject_path, 'w', encoding='utf-8') as f:
            toml.dump(data, f)
        return True
    except Exception as e:
        print(f"Ошибка записи в pyproject.toml: {e}")
        return False


def git_add_file(file_path: Path) -> bool:
    """
    Добавляет файл в git staging area.

    Выполняет команду 'git add <file_path>' для добавления указанного файла
    в индекс Git. Это необходимо для того, чтобы обновленная версия в
    pyproject.toml была включена в следующий коммит.

    Parameters
    ----------
    file_path : Path
        Путь к файлу для добавления в staging area.

    Returns
    -------
    bool
        True если команда выполнена успешно, False в случае ошибки.

    Notes
    -----
    Функция не проверяет, является ли текущая директория git репозиторием.
    Эта проверка должна быть выполнена перед вызовом этой функции.

    Examples
    --------
    >>> success = git_add_file(Path('pyproject.toml'))
    >>> success
    True
    """
    try:
        subprocess.run(
            ['git', 'add', str(file_path)],
            check=True,
            capture_output=True,
            text=True
        )
        return True
    except subprocess.CalledProcessError:
        return False


def main() -> int:
    """
    Основная функция скрипта.

    Выполняет последовательность действий для автоматического увеличения
    билд-номера:
    1. Находит файл pyproject.toml в текущей директории
    2. Читает текущую версию из раздела [project]
    3. Увеличивает билд-номер на единицу
    4. Записывает новую версию обратно в файл
    5. Добавляет обновленный файл в git staging area

    Returns
    -------
    int
        Код возврата: 0 при успешном выполнении, 1 при ошибке.

    Notes
    -----
    Скрипт предназначен для использования в качестве git pre-commit hook.
    Для настройки автоматического выполнения создайте файл .git/hooks/pre-commit
    со следующим содержимым:
    ```
    #!/bin/sh
    python3 bump_version.py
    ```
    И установите права на выполнение:
    ```
    chmod +x .git/hooks/pre-commit
    ```

    Examples
    --------
    >>> main()
    Увеличение версии: 1.0.0-1 → 1.0.0-2
    Файл pyproject.toml добавлен в git staging
    0
    """
    pyproject_path = Path('pyproject.toml')

    if not pyproject_path.exists():
        print(f"Файл {pyproject_path} не найден")
        return 1

    try:
        version_info, data = read_pyproject_version(pyproject_path)

        old_version = str(version_info)
        version_info.bump_build()
        new_version = str(version_info)

        print(f"Увеличение версии: {old_version} → {new_version}")

        if not write_pyproject_version(pyproject_path, version_info, data):
            return 1

        if git_add_file(pyproject_path):
            print(f"Файл {pyproject_path} добавлен в git staging")
        else:
            print(f"Ошибка при добавлении {pyproject_path} в git staging")

        return 0

    except ValueError as e:
        print(f"Ошибка: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
