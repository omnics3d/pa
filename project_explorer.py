#!/usr/bin/env python3
"""
Умный навигатор по проекту с автоматическим извлечением докстрингов.
Отображает структуру проекта, создает документацию в TXT файлах.
Архитектура построена по принципу SRP (Single Responsibility Principle).
"""

import os
import sys
import ast
import textwrap
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime

# =============================================================================
# МОДЕЛЬ ДАННЫХ
# =============================================================================


@dataclass
class PyDocInfo:
    """Информация о докстрингах Python файла."""

    module_doc: str = ""
    classes: Dict[str, str] = field(default_factory=dict)
    functions: Dict[str, str] = field(default_factory=dict)


@dataclass
class FileNode:
    """Узел файловой системы с метаданными."""

    name: str
    path: Path
    is_dir: bool
    size: int = 0
    modified: datetime = None
    py_doc: Optional[PyDocInfo] = None
    txt_path: Optional[Path] = None
    children: List["FileNode"] = field(default_factory=list)


# =============================================================================
# КОМПОНЕНТ 1: СКАНЕР ФАЙЛОВОЙ СИСТЕМЫ
# =============================================================================


class FileScanner:
    """Сканирует файловую систему и создает древовидную структуру."""

    IGNORE_PATTERNS = {
        "__pycache__",
        ".git",
        ".DS_Store",
        ".pyc",
        ".pyo",
        ".so",
        ".dll",
        ".exe",
        ".log",
        ".tmp",
        ".swp",
        ".idea",
        ".vscode",
        "venv",
        ".env",
        "node_modules",
        "dist",
        "build",
        ".pytest_cache",
        ".coverage",
    }

    def __init__(self, doc_extractor: "DocstringExtractor" = None):
        self.doc_extractor = doc_extractor

    def scan_directory(self, directory: Path) -> Optional[FileNode]:
        try:
            if not directory.exists() or not directory.is_dir():
                return None

            node = FileNode(
                name=directory.name,
                path=directory,
                is_dir=True,
                modified=datetime.fromtimestamp(directory.stat().st_mtime),
            )

            sorted_items = self._get_sorted_items(directory)

            for item in sorted_items:
                if item.is_dir():
                    child = self.scan_directory(item)
                    if child:
                        node.children.append(child)
                else:
                    file_node = self._create_file_node(item)
                    node.children.append(file_node)

            return node

        except (PermissionError, OSError):
            return None

    def _get_sorted_items(self, directory: Path) -> List[Path]:
        items = []
        for item in directory.iterdir():
            if self._should_ignore(item):
                continue
            items.append(item)

        items.sort(key=lambda x: (not x.is_dir(), x.name.lower()))
        return items

    def _should_ignore(self, path: Path) -> bool:
        return any(pattern in path.name for pattern in self.IGNORE_PATTERNS)

    def _create_file_node(self, filepath: Path) -> FileNode:
        try:
            stat = filepath.stat()
            file_node = FileNode(
                name=filepath.name,
                path=filepath,
                is_dir=False,
                size=stat.st_size,
                modified=datetime.fromtimestamp(stat.st_mtime),
            )

            if filepath.suffix == ".py" and self.doc_extractor is not None:
                file_node.py_doc = self.doc_extractor.extract_from_file(filepath)

            return file_node

        except (PermissionError, OSError):
            return FileNode(name=filepath.name, path=filepath, is_dir=False)


# =============================================================================
# КОМПОНЕНТ 2: ЭКСТРАКТОР ДОКСТРИНГОВ
# =============================================================================


class DocstringExtractor:
    """Извлекает докстринги из Python файлов."""

    @staticmethod
    def extract_from_file(filepath: Path) -> Optional[PyDocInfo]:
        if not filepath.exists() or filepath.suffix != ".py":
            return None

        try:
            with open(filepath, "r", encoding="utf-8") as file:
                content = file.read()

            return DocstringExtractor.extract_from_source(content)

        except (UnicodeDecodeError, PermissionError, OSError):
            return None

    @staticmethod
    def extract_from_source(source_code: str) -> PyDocInfo:
        doc_info = PyDocInfo()

        try:
            tree = ast.parse(source_code)

            module_doc = ast.get_docstring(tree)
            if module_doc:
                doc_info.module_doc = textwrap.dedent(module_doc).strip()

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_doc = ast.get_docstring(node)
                    if class_doc:
                        clean_doc = textwrap.dedent(class_doc).strip()
                        doc_info.classes[node.name] = clean_doc

                elif isinstance(node, ast.FunctionDef):
                    parent = node.parent if hasattr(node, "parent") else None
                    if not isinstance(parent, ast.ClassDef):
                        func_doc = ast.get_docstring(node)
                        if func_doc:
                            clean_doc = textwrap.dedent(func_doc).strip()
                            doc_info.functions[node.name] = clean_doc

        except SyntaxError:
            pass

        return doc_info


# =============================================================================
# КОМПОНЕНТ 3: МЕНЕДЖЕР ФАЙЛОВ ДОКУМЕНТАЦИИ
# =============================================================================


class DocFileManager:
    """Управляет TXT файлами с документацией."""

    def __init__(self, docs_dir: Path):
        self.docs_dir = docs_dir
        self.docs_dir.mkdir(parents=True, exist_ok=True)

    def find_txt_for_file(self, file_node: FileNode) -> Optional[Path]:
        safe_name = file_node.name.replace(".", "_")
        txt_name = f"FILE_{safe_name}.txt"
        txt_path = self.docs_dir / txt_name

        return txt_path if txt_path.exists() else None

    def create_or_update_txt(
        self, file_node: FileNode, force_update: bool = False
    ) -> Path:
        safe_name = file_node.name.replace(".", "_")
        txt_name = f"FILE_{safe_name}.txt"
        txt_path = self.docs_dir / txt_name

        if txt_path.exists() and not force_update:
            return txt_path

        self._write_txt_file(txt_path, file_node, force_update)
        file_node.txt_path = txt_path

        return txt_path

    def _write_txt_file(
        self, txt_path: Path, file_node: FileNode, force_update: bool
    ) -> None:
        with open(txt_path, "w", encoding="utf-8") as file:
            file.write("=" * 60 + "\n")
            file.write(f"ФАЙЛ: {file_node.name}\n")
            file.write(f"ПУТЬ: {file_node.path}\n")
            file.write(f"РАЗМЕР: {self._format_size(file_node.size)}\n")
            file.write(f"ИЗМЕНЕН: {file_node.modified}\n")
            file.write(f"ОБНОВЛЕНО: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

            if force_update:
                file.write("СТАТУС: Документация обновлена автоматически\n")
            else:
                file.write("СТАТУС: Документация создана автоматически\n")

            file.write("=" * 60 + "\n\n")

            if file_node.py_doc:
                doc_info = file_node.py_doc

                file.write("🐍 PYTHON МОДУЛЬ\n")
                file.write("-" * 40 + "\n")

                if doc_info.module_doc:
                    file.write("📝 ОПИСАНИЕ МОДУЛЯ:\n")
                    file.write(doc_info.module_doc + "\n\n")

                if doc_info.classes:
                    file.write(f"🏛  КЛАССЫ ({len(doc_info.classes)}):\n")
                    for class_name, class_doc in doc_info.classes.items():
                        file.write("\n" + "━" * 30 + "\n")
                        file.write(f"class {class_name}:\n")
                        if class_doc:
                            file.write(textwrap.indent(class_doc, "  ") + "\n")
                    file.write("\n")

                if doc_info.functions:
                    file.write(f"⚙️  ФУНКЦИИ ({len(doc_info.functions)}):\n")
                    for func_name, func_doc in doc_info.functions.items():
                        file.write("\n" + "─" * 30 + "\n")
                        file.write(f"def {func_name}():\n")
                        if func_doc:
                            file.write(textwrap.indent(func_doc, "  ") + "\n")
                    file.write("\n")

            file.write("=" * 60 + "\n")
            file.write("\n🎯 ИСПОЛЬЗОВАНИЕ:\n")
            file.write("(Опишите как использовать этот файл)\n\n")

            file.write("🔗 СВЯЗИ:\n")
            file.write("(Какие файлы импортирует/экспортирует)\n\n")

            file.write("✏️  ПРИМЕЧАНИЯ РАЗРАБОТЧИКА:\n")
            file.write("(Добавляйте сюда заметки по мере работы)\n")

    def _format_size(self, size_bytes: int) -> str:
        for unit in ["Б", "КБ", "МБ", "ГБ"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0

        return f"{size_bytes:.1f} ТБ"


# =============================================================================
# КОМПОНЕНТ 4: ОТОБРАЖАТЕЛЬ ДЕРЕВА
# =============================================================================


class TreeRenderer:
    """Отображает древовидную структуру проекта."""

    ICON_MAP = {
        "dir": "📁",
        ".py": "🐍",
        ".json": "📋",
        ".yaml": "⚙️",
        ".yml": "⚙️",
        ".md": "📘",
        ".sh": "🐚",
        ".txt": "📝",
    }

    def __init__(self):
        self.expanded: Set[str] = set()

    def get_display_name(self, node: FileNode) -> str:
        if node.is_dir:
            return f"{self.ICON_MAP['dir']} {node.name}/"

        suffix = node.path.suffix.lower()
        icon = self.ICON_MAP.get(suffix, "📄")

        if node.name == "__init__.py":
            icon = "🎯"

        return f"{icon} {node.name}"

    def display(self, root_node: FileNode) -> List[FileNode]:
        self._clear_screen()
        numbered_items = self._render_tree(root_node)
        return numbered_items

    def _clear_screen(self) -> None:
        os.system("cls" if os.name == "nt" else "clear")

    def _render_tree(self, root_node: FileNode) -> List[FileNode]:
        numbered_items = []
        self._render_node(root_node, 0, True, numbered_items, True)
        return numbered_items

    def _render_node(
        self,
        node: FileNode,
        depth: int,
        parent_expanded: bool,
        numbered_items: List[FileNode],
        is_root: bool = False,
    ) -> None:
        if depth > 0 and not parent_expanded:
            return

        if not is_root:
            self._print_node_line(node, depth, numbered_items)

        current_expanded = node.is_dir and (is_root or node.name in self.expanded)

        if current_expanded:
            for child in node.children:
                self._render_node(child, depth + 1, current_expanded, numbered_items)

    def _print_node_line(
        self, node: FileNode, depth: int, numbered_items: List[FileNode]
    ) -> None:
        indent = "│   " * (depth - 1) if depth > 0 else ""
        connector = "├── " if depth > 0 else ""

        display_line = f"{indent}{connector}{self.get_display_name(node)}"

        if not node.is_dir and node.txt_path:
            display_line += "  [📝]"

        item_number = len(numbered_items) + 1
        numbered_items.append(node)
        print(f"{item_number:3}. {display_line}")

    def toggle_folder(self, folder_name: str) -> None:
        if folder_name in self.expanded:
            self.expanded.remove(folder_name)
        else:
            self.expanded.add(folder_name)


# =============================================================================
# КОМПОНЕНТ 5: ОБРАБОТЧИК КОМАНД
# =============================================================================


class CommandHandler:
    """Обрабатывает пользовательские команды."""

    def __init__(self, tree_renderer: TreeRenderer, doc_file_manager: DocFileManager):
        self.tree_renderer = tree_renderer
        self.doc_file_manager = doc_file_manager

    def handle_command(
        self, command: str, items: List[FileNode], editor_opener: "EditorOpener"
    ) -> bool:
        if command == "q":
            print("👋 Выход")
            return False

        elif command in ["h", "help"]:
            self._show_help()
            input("\n↵ Нажмите Enter для продолжения...")
            return True

        elif command == "d":
            self._handle_update_all(items)
            return True

        elif command.startswith("s "):
            self._handle_search(command[2:].strip(), items, editor_opener)
            return True

        elif command.startswith("u "):
            self._handle_force_update(command[2:].strip(), items, editor_opener)
            return True

        elif command.isdigit():
            return self._handle_item_select(command, items, editor_opener)

        else:
            print(f"❌ Неизвестная команда: {command}")
            time.sleep(1)
            return True

    def _show_help(self) -> None:
        """Показывает справку по командам."""
        print("\n" + "=" * 60)
        print("📚 СПРАВКА ПО КОМАНДАМ")
        print("=" * 60)
        print("\n📁 НАВИГАЦИЯ:")
        print("  [номер]    - открыть/создать TXT или раскрыть папку")

        print("\n🔍 ПОИСК:")
        print("  s [текст]  - поиск в докстрингах")

        print("\n📝 ДОКУМЕНТАЦИЯ:")
        print("  u [номер]  - обновить TXT (пересоздать)")
        print("  d          - обновить все TXT файлы")

        print("\n⚙️  СИСТЕМА:")
        print("  h, help    - эта справка")
        print("  q          - выход")
        print("\n" + "=" * 60)

    def _handle_update_all(self, items: List[FileNode]) -> None:
        all_files = []
        for item in items:
            if not item.is_dir:
                all_files.append(item)

        count = 0
        for file_node in all_files:
            self.doc_file_manager.create_or_update_txt(file_node, True)
            count += 1

        print(f"🔄 Пересоздано {count} TXT файлов")
        time.sleep(1)

    def _handle_search(
        self, query: str, items: List[FileNode], editor_opener: "EditorOpener"
    ) -> None:
        if not query:
            return

        results = []
        for item in items:
            if not item.is_dir and item.py_doc:
                doc_info = item.py_doc

                if query.lower() in doc_info.module_doc.lower():
                    results.append(item)
                    continue

                for class_name in doc_info.classes.keys():
                    if query.lower() in class_name.lower():
                        results.append(item)
                        break

                for func_name in doc_info.functions.keys():
                    if query.lower() in func_name.lower():
                        results.append(item)
                        break

        if not results:
            print("🤷 Ничего не найдено")
            time.sleep(1)
            return

        print(f"\n🔍 Найдено {len(results)} файлов:")
        for i, item in enumerate(results[:10], 1):
            print(f"{i:2}. {item.path}")

        if len(results) > 10:
            print(f"... и ещё {len(results) - 10}")

        choice = input("\nОткрыть TXT для номера (или Enter): ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(results):
                txt_path = self.doc_file_manager.create_or_update_txt(
                    results[idx], False
                )
                print(f"📄 Открываю: {txt_path.name}")
                editor_opener.open_in_editor(txt_path)

    def _handle_force_update(
        self, num_str: str, items: List[FileNode], editor_opener: "EditorOpener"
    ) -> None:
        if not num_str.isdigit():
            print("❌ Номер должен быть числом")
            time.sleep(1)
            return

        idx = int(num_str) - 1
        if 0 <= idx < len(items):
            item = items[idx]
            if not item.is_dir:
                txt_path = self.doc_file_manager.create_or_update_txt(item, True)
                print(f"🔄 Пересоздан: {txt_path.name}")
                editor_opener.open_in_editor(txt_path)
            else:
                print("❌ Можно обновлять только файлы")
        else:
            print(f"❌ Нет элемента с номером {num_str}")

        time.sleep(1)

    def _handle_item_select(
        self, command: str, items: List[FileNode], editor_opener: "EditorOpener"
    ) -> bool:
        idx = int(command) - 1
        if 0 <= idx < len(items):
            item = items[idx]

            if item.is_dir:
                self._handle_folder_toggle(item)
            else:
                self._handle_file_open(item, editor_opener)
        else:
            print(f"❌ Нет элемента с номером {command}")
            time.sleep(1)

        return True

    def _handle_folder_toggle(self, item: FileNode) -> None:
        self.tree_renderer.toggle_folder(item.name)
        state = "раскрыта" if item.name in self.tree_renderer.expanded else "свёрнута"
        print(f"📁 Папка '{item.name}' {state}")
        time.sleep(0.5)

    def _handle_file_open(self, item: FileNode, editor_opener: "EditorOpener") -> None:
        if item.txt_path:
            print(f"📄 Открываю существующий TXT: {item.txt_path.name}")
        else:
            print(f"📝 Создаю документацию для {item.name}...")

        txt_path = self.doc_file_manager.create_or_update_txt(item, False)
        print(f"✅ Готово: {txt_path.name}")
        editor_opener.open_in_editor(txt_path)


# =============================================================================
# КОМПОНЕНТ 6: ОТКРЫВАТЕЛЬ РЕДАКТОРА
# =============================================================================


class EditorOpener:
    """Открывает файлы в текстовом редакторе."""

    def __init__(self):
        self.editor = os.environ.get("EDITOR", "vim")

    def open_in_editor(self, filepath: Path) -> None:
        try:
            subprocess.run([self.editor, str(filepath)], check=False)
        except FileNotFoundError:
            print(f"Редактор '{self.editor}' не найден")
            input("Нажмите Enter...")


# =============================================================================
# КОМПОНЕНТ 7: КООРДИНАТОР
# =============================================================================


class SmartNavigator:
    """Координирует работу всех компонентов навигатора."""

    def __init__(self, root_dir: str = ".") -> None:
        self.root = Path(root_dir).resolve()

        self.doc_extractor = DocstringExtractor()
        self.file_scanner = FileScanner(self.doc_extractor)
        self.doc_file_manager = DocFileManager(self.root / "docs" / "structure_docs")
        self.tree_renderer = TreeRenderer()
        self.command_handler = CommandHandler(self.tree_renderer, self.doc_file_manager)
        self.editor_opener = EditorOpener()

        self.root_node = self.file_scanner.scan_directory(self.root)
        self._link_txt_files()

    def _link_txt_files(self) -> None:
        def link_node(node: FileNode) -> None:
            if not node.is_dir:
                txt_path = self.doc_file_manager.find_txt_for_file(node)
                if txt_path:
                    node.txt_path = txt_path

            for child in node.children:
                link_node(child)

        for child in self.root_node.children:
            link_node(child)

    def run(self) -> None:
        """Запускает интерактивный режим."""
        while True:
            items = self.tree_renderer.display(self.root_node)

            try:
                command = input("\nкоманда: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                print("\n👋 Выход")
                break

            should_continue = self.command_handler.handle_command(
                command, items, self.editor_opener
            )

            if not should_continue:
                break

    def update_all_txt(self, force: bool = False) -> int:
        count = 0

        def process_node(node: FileNode) -> None:
            nonlocal count
            if not node.is_dir:
                self.doc_file_manager.create_or_update_txt(node, force)
                count += 1

            for child in node.children:
                process_node(child)

        for child in self.root_node.children:
            process_node(child)

        return count


# =============================================================================
# ТОЧКА ВХОДА
# =============================================================================


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Умный навигатор по проекту с извлечением докстрингов."
    )
    parser.add_argument(
        "--path",
        type=str,
        default=".",
        help="Путь к проекту (по умолчанию текущая директория)",
    )
    parser.add_argument(
        "--export-all", action="store_true", help="Создать TXT для всех файлов"
    )
    parser.add_argument(
        "--force-update", action="store_true", help="Принудительно пересоздать все TXT"
    )

    args = parser.parse_args()

    navigator = SmartNavigator(args.path)

    if args.export_all:
        force = args.force_update
        count = navigator.update_all_txt(force=force)
        action = "Создано" if not force else "Пересоздано"
        print(f"✅ {action} {count} TXT файлов")
    else:
        navigator.run()


if __name__ == "__main__":
    main()
