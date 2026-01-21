import os
import subprocess
import sys
import time
import json


class ProjectStructureViewer:
    def __init__(self, json_file='docs/project_structure.json'):
        """Загружает структуру из JSON файла"""
        self.json_file = json_file
        self.expanded_folders = set()  # Сет для хранения раскрытых папок

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            print(f"Ошибка: Файл {json_file} не найден.")
            print("Создайте файл docs/project_structure.json со структурой.")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Ошибка чтения JSON файла {json_file}: {e}")
            sys.exit(1)

        self.project_root = self.data.get('project_root', 'pa')
        self.txt_files_dir = 'docs/project_structure/'
        os.makedirs(self.txt_files_dir, exist_ok=True)

        self.elements = []
        self.numbered_lines = []
        self._parse_structure()
        self.total_elements = len(self.elements)
        self._check_and_create_txt_files()

    def _check_and_create_txt_files(self):
        """Проверяет наличие .txt файлов и создает отсутствующие"""
        print(f"Проверяем наличие .txt файлов в {self.txt_files_dir}...")
        created_count = 0

        for element_info in self.elements:
            element_name = element_info['name']
            is_dir = element_info['is_dir']
            parent_folders = element_info['parent_folders']

            if parent_folders:
                last_parent = parent_folders[-1] if parent_folders else ""
                clean_element_name = element_name.rstrip('/')
                filename = f"{last_parent}_{clean_element_name}.txt"
            else:
                clean_element_name = element_name.rstrip('/')
                filename = f"{clean_element_name}.txt"

            txt_filename = os.path.join(self.txt_files_dir, filename)

            if not os.path.exists(txt_filename):
                try:
                    with open(txt_filename, 'w', encoding='utf-8') as f:
                        f.write(f"Файл для элемента: {element_name}\n")
                        f.write(f"Тип: {'Папка' if is_dir else 'Файл'}\n")

                        full_path_parts = parent_folders + [element_name.rstrip('/')]
                        full_path = '/'.join(full_path_parts)
                        f.write(f"Полный путь: {self.project_root}/{full_path}\n")

                        if element_info['description']:
                            f.write(f"Описание: {element_info['description']}\n")

                        f.write(f"Создан: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write("\n" + "="*50 + "\n")

                        if parent_folders:
                            f.write(f"Родительские папки: {' -> '.join(parent_folders)}\n")
                        f.write("Информация будет добавлена позже.\n")

                    created_count += 1
                    print(f"  Создан: {filename}")
                except Exception as e:
                    print(f"  Ошибка создания {filename}: {e}")

        if created_count > 0:
            print(f"Создано {created_count} .txt файлов в {self.txt_files_dir}")
        else:
            print(f"Все .txt файлы уже существуют в {self.txt_files_dir}")

        time.sleep(1.5)

    def _parse_structure(self):
        """Парсит структуру с учетом раскрытых папок"""
        self.elements = []
        self.numbered_lines = []
        self._parse_item(self.data['structure'], 0, [], [])

    def _parse_item(self, items, level, parent_folders, path_parts):
        """Рекурсивно парсит элементы"""
        for item in items:
            item_type = item.get('type', 'file')
            item_name = item.get('name', '')
            description = item.get('description', '')
            
            current_path = path_parts + [item_name]
            path_key = '/'.join(current_path)
            
            # Проверяем, нужно ли показывать этот элемент
            # Показываем если:
            # 1. Это уровень 0
            # 2. Все родительские папки раскрыты
            should_show = True
            for i in range(len(current_path) - 1):
                parent_path = '/'.join(current_path[:i+1])
                if parent_path not in self.expanded_folders:
                    should_show = False
                    break
            
            if not should_show:
                continue
            
            # Формируем строку для отображения
            if level == 0:
                if item_type == 'directory':
                    line = f"\033[94m{item_name}/\033[0m"  # Синий для папок
                else:
                    line = item_name
            else:
                indent = "│   " * (level - 1)
                connector = "├── " if level > 0 else ""
                
                if item_type == 'directory':
                    line = f"{indent}{connector}\033[94m{item_name}/\033[0m"  # Синий для папок
                else:
                    line = f"{indent}{connector}{item_name}"
            
            if description:
                line += f"                # {description}"
            
            # Сохраняем информацию об элементе
            element_info = {
                'name': item_name,
                'type': item_type,
                'is_dir': item_type == 'directory',
                'description': description,
                'parent_folders': parent_folders.copy(),
                'level': level,
                'path_key': path_key
            }
            self.elements.append(element_info)
            self.numbered_lines.append(line)
            
            # Рекурсивно обрабатываем детей, если это папка
            if 'children' in item and item['children'] and item_type == 'directory':
                new_parent_folders = parent_folders.copy()
                new_parent_folders.append(item_name.rstrip('/'))
                self._parse_item(item['children'], level + 1, new_parent_folders, current_path)

    def _clear_screen(self):
        """Очищает экран консоли"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def _add_empty_lines(self, count=30):
        """Добавляет пустые строки в начало вывода"""
        for _ in range(count):
            print()

    def _display_structure(self):
        """Отображает структуру проекта с пустыми строками сверху"""
        self._add_empty_lines(30)

        print(f"Структура проекта ({self.project_root}/):")
        print(f"Загружено из: {self.json_file}")
        print("-" * 50)

        for i, line in enumerate(self.numbered_lines, 1):
            print(f"{i:2}. {line}")

    def open_txt_file(self, element_number):
        """Открывает .txt файл в Vim для выбранного элемента"""
        if 1 <= element_number <= self.total_elements:
            element_info = self.elements[element_number-1]
            element_name = element_info['name']
            is_dir = element_info['is_dir']
            description = element_info['description']
            parent_folders = element_info['parent_folders']
            path_key = element_info['path_key']

            # Если это папка - раскрываем/скрываем её
            if is_dir:
                if path_key in self.expanded_folders:
                    self.expanded_folders.remove(path_key)
                    print(f"Папка '{element_name}' свернута")
                else:
                    self.expanded_folders.add(path_key)
                    print(f"Папка '{element_name}' раскрыта")
                
                # Перерисовываем структуру
                time.sleep(1)
                self._parse_structure()
                self.total_elements = len(self.elements)
                self._clear_screen()
                self._display_structure()
                return

            # Если это файл - открываем его
            if parent_folders:
                last_parent = parent_folders[-1] if parent_folders else ""
                clean_element_name = element_name.rstrip('/')
                filename = f"{last_parent}_{clean_element_name}.txt"
            else:
                clean_element_name = element_name.rstrip('/')
                filename = f"{clean_element_name}.txt"

            txt_filename = os.path.join(self.txt_files_dir, filename)

            element_type = "Папка" if is_dir else "Файл"
            print(f"\nВы выбрали элемент №{element_number}: {element_name}")
            print(f"Тип: {element_type}")

            full_path_parts = parent_folders + [element_name.rstrip('/')]
            full_path = '/'.join(full_path_parts)
            print(f"Полный путь: {self.project_root}/{full_path}")

            if parent_folders:
                print(f"Родительские папки: {' -> '.join(parent_folders)}")

            if description:
                print(f"Описание: {description}")

            print(f"Имя файла: {filename}")
            print(f"Открываю файл в Vim: {txt_filename}")

            try:
                if not os.path.exists(txt_filename):
                    os.makedirs(self.txt_files_dir, exist_ok=True)
                    with open(txt_filename, 'w', encoding='utf-8') as f:
                        f.write(f"Файл для элемента: {element_name}\n")
                        f.write(f"Тип: {'Папка' if is_dir else 'Файл'}\n")

                        full_path_parts = parent_folders + [element_name.rstrip('/')]
                        full_path = '/'.join(full_path_parts)
                        f.write(f"Полный путь: {self.project_root}/{full_path}\n")

                        if description:
                            f.write(f"Описание: {description}\n")

                        f.write(f"Создан: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write("\n" + "="*50 + "\n")

                        if parent_folders:
                            f.write(f"Родительские папки: {' -> '.join(parent_folders)}\n")
                        f.write("Информация будет добавлена позже.\n")
                    print(f"(Файл был создан заново)")

                # Открываем файл в Vim (блокирующий вызов)
                print("Открываю в Vim... (для выхода: :q или :wq)")
                vim_command = ['vim', txt_filename]
                process = subprocess.Popen(vim_command)
                process.wait()

                # После закрытия Vim - перерисовываем всё
                self._clear_screen()
                self._display_structure()

            except FileNotFoundError:
                print("Ошибка: Vim не найден. Установите Vim или настройте PATH.")
                print("Можно установить: sudo apt install vim (Linux)")
                print("Или: brew install vim (macOS)")
                print("Или скачать с: https://www.vim.org/download.php")
                time.sleep(3)
                self._clear_screen()
                self._display_structure()
            except Exception as e:
                print(f"Не удалось открыть файл в Vim: {e}")
                print("Пробуем открыть в альтернативном редакторе...")
                
                # Пробуем альтернативные редакторы
                try:
                    if sys.platform == "win32":
                        # Для Windows пробуем notepad
                        process = subprocess.Popen(['notepad', txt_filename])
                    elif sys.platform == "darwin":
                        # Для macOS пробуем TextEdit
                        process = subprocess.Popen(['open', '-t', txt_filename])
                    else:
                        # Для Linux пробуем nano
                        process = subprocess.Popen(['nano', txt_filename])
                    
                    process.wait()
                    self._clear_screen()
                    self._display_structure()
                except Exception as e2:
                    print(f"Не удалось открыть файл: {e2}")
                    time.sleep(2)
                    self._clear_screen()
                    self._display_structure()
        else:
            print(f"Ошибка: номер должен быть от 1 до {self.total_elements}")
            time.sleep(2)
            self._clear_screen()
            self._display_structure()

    def run(self):
        """Основной метод запуска программы"""
        self._clear_screen()
        self._display_structure()
        
        while True:
            user_input = input("\nВведите номер файла (или q для выхода): ").strip().lower()
            
            if user_input == 'q':
                print("Выход из программы")
                break
                
            try:
                element_number = int(user_input)
                self.open_txt_file(element_number)
            except ValueError:
                print("Ошибка: введите целое число или q для выхода")
                time.sleep(1)
                self._clear_screen()
                self._display_structure()


if __name__ == "__main__":
    viewer = ProjectStructureViewer('docs/project_structure.json')
    viewer.run()
