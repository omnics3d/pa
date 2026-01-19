#!/bin/bash

# Определяем абсолютный путь к текущей папке проекта
PROJECT_DIR=$(pwd)
# Имя файла для запуска (по умолчанию main_v.py в этой же папке)
FILE_NAME="${1:-main_v.py}"
FULL_PATH="$PROJECT_DIR/$FILE_NAME"

# Разрешаем подключения к X-серверу
xhost + > /dev/null 2>&1

# Запуск через Ubuntu
proot-distro login ubuntu --user root --shared-tmp -- env \
    DISPLAY=:0 \
    QT_QPA_PLATFORM=xcb \
    QT_X11_NO_MITSHM=1 \
    PYTHONPATH="$PROJECT_DIR" \
    python3 "$FULL_PATH"

