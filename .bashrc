run_ub() {
    if [ -z "$1" ]; then echo "Использование: run_ub файл.py"; return 1; fi
    ABS_PATH=$(pwd)

    # 1. Проверка наличия запущенного дисплея (улучшенный поиск процесса)
    if ! pgrep -f "termux.x11" >/dev/null; then
        echo "[!] Ошибка: Termux-X11 не запущен. Сначала запустите XFCE."
        return 1
    fi

    # 2. Авторизация
    export DISPLAY=:1
    xhost +local:root > /dev/null 2>&1

    # 3. Вход в Ubuntu и запуск скрипта в текущем окружении
    proot-distro login ubuntu --shared-tmp --bind "$ABS_PATH":"$ABS_PATH" -- bash -c "
        export DISPLAY=:1
        export QT_QPA_PLATFORM=xcb
        export LIBGL_ALWAYS_SOFTWARE=1
        export QT_X11_NO_MITSHM=1
        export QT_XCB_GL_INTEGRATION=none
        export XDG_RUNTIME_DIR=/tmp

        cd '$ABS_PATH'
        if [ -f '$1' ]; then
            python3 '$1'
        else
            echo 'Ошибка: Файл $1 не найден'
        fi
    "
}

# Ваш alias для обычного входа
alias u='proot-distro login ubuntu --shared-tmp'

