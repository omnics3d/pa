import sys
import os
import urllib.request
import importlib.util
import shutil
from PySide6.QtWidgets import QApplication

# --- КОНСТАНТЫ ---
SERVER_URL = "http://127.0.0.1:8080/"
REQUIRED_FILES = [
    "utils/__init__.py", 
    "utils/main_window.py", 
    "core/__init__.py", 
    "core/logger_v2026.py"
]

def send_log(message):
    try:
        data = str(message).encode('utf-8')
        req = urllib.request.Request(SERVER_URL + "log", data=data, method='POST')
        with urllib.request.urlopen(req, timeout=2) as r:
            return r.status == 200
    except:
        return False

def sync():
    print("--- ПРИНУДИТЕЛЬНАЯ СИНХРОНИЗАЦИЯ ---")
    
    # 1. Очистка кэша байт-кода
    for folder in ["utils", "core"]:
        pycache = os.path.join(folder, "__pycache__")
        if os.path.exists(pycache):
            shutil.rmtree(pycache)

    # 2. Перезапись файлов
    for file_path in REQUIRED_FILES:
        folder = os.path.dirname(file_path)
        if folder and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            
        try:
            # Анти-кэш параметр в URL
            url = SERVER_URL + file_path + f"?t={os.urandom(4).hex()}"
            with urllib.request.urlopen(url, timeout=5) as r:
                content = r.read()
                with open(file_path, "wb") as f:
                    f.write(content)
            print(f"ОК (загружено): {file_path}")
        except Exception as e:
            print(f"ОШИБКА {file_path}: {e}")

def load_module_from_file(module_name, file_path):
    """Принудительная загрузка модуля прямо из файла"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None:
        raise ImportError(f"Не удалось создать спецификацию для {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def main():
    # Настройка путей
    base = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base)
    if base not in sys.path:
        sys.path.insert(0, base)

    # Выполняем синхронизацию
    sync()

    # Инициализация логгера (из свежезагруженного файла)
    try:
        core_log = load_module_from_file("core.logger_v2026", "core/logger_v2026.py")
        core_log.setup_logging(level="DEBUG")
        log = core_log.get_logger("Bootloader")
        log.info("Система логирования обновлена и запущена")
    except Exception as e:
        print(f"Предупреждение: логгер не инициализирован: {e}")

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    try:
        # Гарантированная загрузка нового GUI
        main_window_module = load_module_from_file("utils.main_window", "utils/main_window.py")
        
        global win
        win = main_window_module.MainWindow()
        win.show()
        
        send_log("GUI запущен: версия с верхним меню")
        sys.exit(app.exec())
    except Exception as e:
        err_msg = f"Критическая ошибка при запуске модуля: {e}"
        print(err_msg)
        send_log(err_msg)

if __name__ == "__main__":
    main()
