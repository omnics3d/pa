import sys
import os
import importlib.util
import shutil
from PySide6.QtWidgets import QApplication


def check_x11():
    """Проверка DISPLAY из .bashrc для работы в Termux X11"""
    display = os.environ.get("DISPLAY")
    if not display:
        print("ОШИБКА: Переменная DISPLAY не найдена. Проверьте запуск X-сервера!")
        return False
    print(f"[*] X11 OK: DISPLAY={display}")
    return True


def clear_cache():
    """Очистка кэша Python для чистого запуска модулей в 2026"""
    print("--- ОЧИСТКА КЭША (2026) ---")
    for folder in ["view", "core", "utils"]:
        pycache = os.path.join(folder, "__pycache__")
        if os.path.exists(pycache):
            shutil.rmtree(pycache)
            print(f"  [+] Очищен кэш: {folder}")


def load_module_from_file(module_name, file_path):
    """Загрузка модуля напрямую из локального файла"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл {file_path} отсутствует!")

    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def main():
    # Установка рабочей директории
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
    app.setApplicationName("Termux_FinChart_2026")

    # 1. Загрузка логгера (из папки core)
    try:
        core_log = load_module_from_file("core.logger_v2026", "core/logger_v2026.py")
        core_log.setup_logging(level="DEBUG")
        log = core_log.get_logger("Bootloader")
        log.info("Приложение запущено: среда X11/XFCE инициализирована")
    except Exception as e:
        print(f"[-] Ошибка инициализации логгера: {e}")

    # 2. Загрузка основного окна из новой папки view
    try:
        main_window_module = load_module_from_file(
            "view.main_window", "view/main_window.py"
        )

        global win
        win = main_window_module.MainWindow()
        win.show()

        print("[*] GUI успешно выведен на рабочий стол из папки view/.")
        sys.exit(app.exec())
    except Exception as e:
        # Теперь логгер (если загрузился) запишет ошибку, либо выведем в консоль
        error_msg = f"[-] Критическая ошибка при открытии окна: {e}"
        print(error_msg)
        if "log" in locals():
            log.error(error_msg)


if __name__ == "__main__":
    main()
