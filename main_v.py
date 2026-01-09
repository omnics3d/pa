import sys
import os
import importlib.util
import shutil
from PySide6.QtWidgets import QApplication

def check_x11():
    """Проверка DISPLAY из .bashrc"""
    display = os.environ.get("DISPLAY")
    if not display:
        print("ОШИБКА: Переменная DISPLAY не найдена. Проверьте .bashrc")
        return False
    print(f"[*] X11 OK: DISPLAY={display}")
    return True

def clear_cache():
    """Очистка кэша Python для чистого запуска модулей"""
    print("--- ОЧИСТКА КЭША (2026) ---")
    for folder in ["utils", "core"]:
        pycache = os.path.join(folder, "__pycache__")
        if os.path.exists(pycache):
            shutil.rmtree(pycache)
            print(f"  [+] Очищен кэш: {folder}")

def load_module_from_file(module_name, file_path):
    """Загрузка модуля напрямую из локального файла"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл {file_path} отсутствует в корне проекта!")
    
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def main():
    # Установка рабочей директории в корень проекта
    base = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base)
    if base not in sys.path:
        sys.path.insert(0, base)

    # Проверка графической среды
    if not check_x11():
        sys.exit(1)

    # Очистка старых данных перед импортом
    clear_cache()

    # Инициализация Qt
    app = QApplication(sys.argv)
    app.setStyle("Fusion") 
    app.setApplicationName("Termux_Local_XFCE")

    # 1. Загрузка логгера (локально)
    try:
        core_log = load_module_from_file("core.logger_v2026", "core/logger_v2026.py")
        core_log.setup_logging(level="DEBUG")
        log = core_log.get_logger("Bootloader")
        log.info("Приложение запущено локально в XFCE")
    except Exception as e:
        print(f"[-] Ошибка логгера: {e}")

    # 2. Загрузка основного окна (локально)
    try:
        main_window_module = load_module_from_file("utils.main_window", "utils/main_window.py")
        
        global win
        win = main_window_module.MainWindow()
        win.show()
        
        print("[*] GUI успешно выведен на рабочий стол.")
        sys.exit(app.exec())
    except Exception as e:
        print(f"[-] Критическая ошибка при открытии окна: {e}")

if __name__ == "__main__":
    main()

