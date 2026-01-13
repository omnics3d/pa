#!/bin/bash

# 1. Очистка и запуск графического сервера Termux-X11
killall -9 termux-x11 Xwayland 2>/dev/null
termux-x11 :1 &

# 2. Ожидание инициализации сервера
sleep 2

# 3. Вход в Ubuntu и запуск XFCE
# Флаг --shared-tmp обязателен для работы X11 внутри proot
proot-distro login ubuntu --shared-tmp -- sh -c "
    export DISPLAY=:1
    export XDG_RUNTIME_DIR=/tmp
    export XDG_CURRENT_DESKTOP=XFCE
    export GDK_BACKEND=x11
    
    # Запуск сессии через dbus для исключения ошибок интерфейса
    dbus-launch --exit-with-session startxfce4
"

