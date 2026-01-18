#!/usr/bin/env python3
"""
Version bumper для автоматического увеличения билд-номера в pyproject.toml.

Модуль предназначен для использования в качестве git pre-commit hook.
При каждом коммите автоматически увеличивает билд-номер (4-я цифра версии,
отделенная тире) в файле pyproject.toml в разделе [project] и добавляет
обновленный файл в git staging area.

Формат версии: MAJOR.MINOR.PATCH-BUILD
Пример: 1.0.0-1 → 1.0.0-2

Основные возможности:
    - Автоматическое увеличение билд-номера при каждом коммите
    - Сохранение форматирования и комментариев в pyproject.toml
    - Автоматическое добавление обновленного файла в git staging area
    - Проверка корректности формата версии

Использование:
    1. Поместить скрипт в репозиторий
    2. Сделать исполняемым: chmod +x bump_version.py
    3. Настроить как pre-commit hook:
       ln -s ../../bump_version.py .git/hooks/pre-commit

Требования:
    - Python 3.7+
    - tomlkit>=0.11.0
    - Git

.. note::
    Скрипт ищет поле 'version' ТОЛЬКО в разделе [project] pyproject.toml
    в соответствии со спецификацией PEP 621. Другие разделы (tool.poetry,
    tool.pdm) игнорируются.

.. warning::
    Скрипт не проверяет, является ли текущая директория git репозиторием.
    Эта проверка должна быть выполнена перед вызовом скрипта.

Пример структуры pyproject.toml:
    [project]
    name = "my-project"
    version = "1.0.0-1"  # Эта строка будет изменена

Автор: Автоматически сгенерировано
Лицензия: MIT

Pseudo Code:
    1. Инициализировать скрипт при вызове из командной строки
    2. Проверить существование файла pyproject.toml в текущей директории
    3. Прочитать файл pyproject.toml с помощью tomlkit с сохранением структуры
    4. Извлечь текущую версию из раздела [project].version
    5. Разобрать версию на компоненты: major, minor, patch, build
    6. Увеличить билд-номер на 1
    7. Собрать новую строку версии
    8. Обновить значение version в документе TOML
    9. Записать обновленный документ обратно в pyproject.toml
    10. Выполнить команду 'git add pyproject.toml' для добавления в staging
    11. Вернуть код завершения 0 при успехе, 1 при ошибке
    12. Завершить выполнение с соответствующим кодом возврата
"""

import subprocess
from pathlib import Path
from typing import Tuple, Optional
import tomlkit


def bump_build_number(version_str: str) -> str:
    """
    Увеличивает билд-номер в строке версии.

    Parameters
    ----------
    version_str : str
        Строка версии в одном из форматов:
        - 'MAJOR.MINOR.PATCH-BUILD'
        - 'vMAJOR.MINOR.PATCH-BUILD'
        - 'VMAJOR.MINOR.PATCH-BUILD'
        Примеры: '1.2.3-4', 'v1.0.0-1', 'V2.1.0-10'

    Returns
    -------
    str
        Новая строка версии с увеличенным билд-номером в формате
        'MAJOR.MINOR.PATCH-(BUILD+1)'.

    Raises
    ------
    ValueError
        Возникает в следующих случаях:
        1. Если строка не содержит тире для разделения билд-номера
        2. Если билд-номер не является целым числом
        3. Если основная часть версии (до тире) не содержит ровно 3 компонента
        4. Если любой из компонентов major/minor/patch не является целым числом

    Notes
    -----
    Функция не поддерживает:
        - Предрелизные метки (alpha, beta, rc)
        - Метаданные сборки (часть после +)
        - Нестандартные форматы версий

    Examples
    --------
    >>> bump_build_number('1.2.3-4')
    '1.2.3-5'
    >>> bump_build_number('v1.0.0-1')
    '1.0.0-2'
    >>> bump_build_number('0.1.0-10')
    '0.1.0-11'

    Pseudo Code:
        1. Удалить префикс 'v' или 'V' из начала version_str
        2. Удалить ведущие и завершающие пробельные символы
        3. Проверить наличие символа '-' в строке:
           - Если '-' отсутствует: выбросить ValueError с описанием ошибки
        4. Разделить строку по первому '-' на две части:
           - main_part = часть до первого символа '-'
           - build_part = часть после первого символа '-'
        5. Удалить метаданные сборки из build_part (все после '+', если есть)
        6. Преобразовать build_part в целое число build:
           - Если преобразование невозможно: выбросить ValueError
        7. Разделить main_part по '.' на части:
           - Если количество частей ≠ 3: выбросить ValueError
        8. Попытаться преобразовать каждую часть в целое число:
           - Если любое преобразование невозможно: выбросить ValueError
        9. Увеличить build на 1
        10. Собрать новую строку версии: main_part + '-' + str(build)
        11. Вернуть новую строку версии
    """
    version_str = version_str.lstrip('vV').strip()

    if '-' not in version_str:
        raise ValueError(
            f"Версия должна быть в формате MAJOR.MINOR.PATCH-BUILD: {version_str}"
        )

    main_part, build_part = version_str.split('-', 1)
    build_part = build_part.split('+')[0]

    try:
        build = int(build_part)
    except ValueError:
        raise ValueError(f"Билд-номер должен быть целым числом: {build_part}")

    main_parts = main_part.split('.')
    if len(main_parts) != 3:
        raise ValueError(
            f"Основная часть версии должна содержать 3 компонента: {main_part}"
        )

    try:
        int(main_parts[0])
        int(main_parts[1])
        int(main_parts[2])
    except ValueError as e:
        raise ValueError(f"Компоненты версии должны быть целыми числами: {e}")

    return f"{main_part}-{build + 1}"


def read_and_bump_version(pyproject_path: Path) -> Tuple[str, str, tomlkit.TOMLDocument]:
    """
    Читает версию из pyproject.toml и увеличивает билд-номер.

    Parameters
    ----------
    pyproject_path : Path
        Путь к файлу pyproject.toml. Должен существовать и быть читаемым.

    Returns
    -------
    Tuple[str, str, tomlkit.TOMLDocument]
        Кортеж из трех элементов:
        1. old_version : str
            Текущая версия из файла pyproject.tomл
        2. new_version : str
            Новая версия с увеличенным билд-номером
        3. doc : tomlkit.TOMLDocument
            Объект документа TOML с сохраненной структурой, комментариями
            и форматированием

    Raises
    ------
    ValueError
        Возникает в следующих случаях:
        1. Если файл pyproject.toml не существует
        2. Если в файле отсутствует раздел [project]
        3. Если в разделе [project] отсутствует поле 'version'
        4. Если возникает ошибка при чтении или парсинге TOML

    FileNotFoundError
        Если файл pyproject.toml не найден по указанному пути.

    PermissionError
        Если нет прав на чтение файла.

    Notes
    -----
    Функция использует tomlkit.parse() для чтения TOML с сохранением
    оригинального форматирования и комментариев. Это важно для того,
    чтобы не нарушать структуру файла при последующей записи.

    Examples
    --------
    >>> from pathlib import Path
    >>> old_ver, new_ver, doc = read_and_bump_version(Path('pyproject.toml'))
    >>> print(f"{old_ver} -> {new_ver}")
    '1.0.0-1 -> 1.0.0-2'

    Pseudo Code:
        1. Проверить существование файла по pyproject_path:
           - Если файл не существует: выбросить ValueError
        2. Открыть файл для чтения в текстовом режиме с кодировкой UTF-8
        3. Прочитать всё содержимое файла в строку content
        4. Распарсить content с помощью tomlkit.parse() для получения doc
        5. Проверить наличие ключа 'project' в doc:
           - Если отсутствует: выбросить ValueError
        6. Проверить наличие ключа 'version' в doc['project']:
           - Если отсутствует: выбросить ValueError
        7. Извлечь текущую версию: old_version = str(doc['project']['version'])
        8. Вызвать bump_build_number(old_version) для получения new_version
        9. Вернуть кортеж (old_version, new_version, doc)
    """
    if not pyproject_path.exists():
        raise ValueError(f"Файл не найден: {pyproject_path}")

    try:
        with open(pyproject_path, 'r', encoding='utf-8') as f:
            content = f.read()
            doc = tomlkit.parse(content)

        if 'project' not in doc:
            raise ValueError("Раздел [project] не найден в pyproject.toml")

        if 'version' not in doc['project']:
            raise ValueError("Поле 'version' не найдено в разделе [project]")

        old_version = str(doc['project']['version'])
        new_version = bump_build_number(old_version)

        return old_version, new_version, doc

    except Exception as e:
        raise ValueError(f"Ошибка чтения pyproject.toml: {e}")


def write_pyproject_version(
    pyproject_path: Path,
    new_version: str,
    doc: tomlkit.TOMLDocument
) -> bool:
    """
    Записывает обновленную версию в файл pyproject.toml.

    Parameters
    ----------
    pyproject_path : Path
        Путь к файлу pyproject.toml для записи. Файл будет перезаписан.
    new_version : str
        Новая строка версии для записи в поле 'version'.
    doc : tomlkit.TOMLDocument
        Объект TOMLDocument с обновленным полем 'version'.

    Returns
    -------
    bool
        True - если запись прошла успешно.
        False - если произошла ошибка при записи.

    Notes
    -----
    Функция перезаписывает весь файл pyproject.toml, но сохраняет
    все оригинальное форматирование и комментарии благодаря использованию
    tomlkit.dumps().

    Side Effects
    ------------
    Перезаписывает файл pyproject.toml по указанному пути.

    Examples
    --------
    >>> from pathlib import Path
    >>> import tomlkit
    >>> doc = tomlkit.parse('''[project]\nversion = "1.0.0-1"''')
    >>> success = write_pyproject_version(Path('test.toml'), '1.0.0-2', doc)
    >>> success
    True

    Pseudo Code:
        1. Попытаться выполнить запись в блоке try-except
        2. Обновить поле 'version' в doc['project'] значением new_version
        3. Открыть файл pyproject_path для записи в текстовом режиме с UTF-8
        4. Сериализовать doc в строку с помощью tomlkit.dumps(doc)
        5. Записать полученную строку в файл
        6. Закрыть файл (автоматически при выходе из with)
        7. Если операция успешна: вернуть True
        8. Если возникло исключение:
           - Вывести сообщение об ошибке с деталями
           - Вернуть False
    """
    try:
        doc['project']['version'] = new_version

        with open(pyproject_path, 'w', encoding='utf-8') as f:
            f.write(tomlkit.dumps(doc))
        return True

    except Exception as e:
        print(f"Ошибка записи в pyproject.toml: {e}")
        return False


def git_add_file(file_path: Path) -> bool:
    """
    Добавляет файл в git staging area.

    Parameters
    ----------
    file_path : Path
        Путь к файлу для добавления в staging area. Должен существовать
        и быть отслеживаемым Git.

    Returns
    -------
    bool
        True - если команда 'git add' выполнена успешно (код возврата 0).
        False - если команда завершилась с ошибкой или файл не найден Git.

    Raises
    ------
    FileNotFoundError
        Если команда 'git' не найдена в системе.

    Notes
    -----
    Функция не проверяет:
        1. Является ли текущая директория git репозиторием
        2. Существует ли файл (это проверяется Git)
        3. Отслеживается ли файл Git

    В случае ошибки выводит сообщение об ошибке в stderr команды git.

    Examples
    --------
    >>> from pathlib import Path
    >>> success = git_add_file(Path('pyproject.toml'))
    >>> success
    True

    Pseudo Code:
        1. Попытаться выполнить команду в блоке try-except
        2. Создать список аргументов: ['git', 'add', str(file_path)]
        3. Запустить подпроцесс subprocess.run с параметрами:
           - check=True (выбросить исключение при ненулевом коде возврата)
           - capture_output=True (перехватить stdout и stderr)
           - text=True (работать со строками вместо байтов)
        4. Если подпроцесс завершился успешно (код возврата 0):
           - Вернуть True
        5. Если подпроцесс завершился с ошибкой (subprocess.CalledProcessError):
           - Вернуть False
    """
    try:
        result = subprocess.run(
            ['git', 'add', str(file_path)],
            check=True,
            capture_output=True,
            text=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Git ошибка: {e.stderr}")
        return False


def main() -> int:
    """
    Основная точка входа скрипта.

    Returns
    -------
    int
        Код возврата:
        0 - Скрипт выполнен успешно, билд-номер увеличен
        1 - Произошла ошибка (файл не найден, неверный формат и т.д.)

    Notes
    -----
    Функция предназначена для использования в качестве git pre-commit hook.
    Для настройки создайте симлинк в .git/hooks/pre-commit:
        ln -s ../../bump_version.py .git/hooks/pre-commit

    Или добавьте вызов скрипта в существующий pre-commit hook.

    Workflow
    --------
    1. Пользователь выполняет 'git commit'
    2. Git запускает pre-commit hook (этот скрипт)
    3. Скрипт увеличивает билд-номер в pyproject.toml
    4. Скрипт добавляет pyproject.toml в staging area
    5. Процесс коммита продолжается с обновленной версией

    Examples
    --------
    В терминале:
        $ python bump_version.py
        Увеличение версии: 1.0.0-1 → 1.0.0-2
        Файл pyproject.toml добавлен в git staging
        $ echo $?
        0

    Pseudo Code:
        1. Создать объект Path для pyproject.toml в текущей директории
        2. Проверить существование файла:
           - Если не существует: вывести ошибку, вернуть 1
        3. Попытаться выполнить:
           - Вызвать read_and_bump_version для получения old_version, new_version, doc
           - Вывести сообщение об увеличении версии
           - Вызвать write_pyproject_version для записи новой версии
           - Если запись не удалась: вернуть 1
           - Вызвать git_add_file для добавления файла в staging
           - Если добавление не удалось: вернуть 1
           - Вернуть 0
        4. Если возникла ошибка ValueError:
           - Вывести сообщение об ошибке
           - Вернуть 1
    """
    pyproject_path = Path('pyproject.toml')

    if not pyproject_path.exists():
        print(f"Файл {pyproject_path} не найден")
        print("Убедитесь, что скрипт запущен из корня проекта с pyproject.toml")
        return 1

    try:
        old_version, new_version, doc = read_and_bump_version(pyproject_path)

        print(f"Увеличение версии: {old_version} → {new_version}")

        if not write_pyproject_version(pyproject_path, new_version, doc):
            print("Не удалось записать новую версию в pyproject.toml")
            return 1

        if git_add_file(pyproject_path):
            print(f"Файл {pyproject_path} добавлен в git staging")
        else:
            print(f"Ошибка при добавлении {pyproject_path} в git staging")
            print("Убедитесь, что вы в git репозитории и файл отслеживается Git")
            return 1

        return 0

    except ValueError as e:
        print(f"Ошибка обработки версии: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
