#!/data/data/com.termux/files/usr/bin/bash
# cleanup-termux-ubuntu.sh
# Скрипт очистки после kill -9 -1
# Версия 2.0 - безопасная и надежная

echo "======================================="
echo "  Очистка Termux + Ubuntu/XFCE + X11  "
echo "======================================="

# Проверяем, запущен ли Termux нормально
if [ -z "$PREFIX" ]; then
    echo "Ошибка: Termux не инициализирован!"
    echo "Запустите скрипт внутри Termux"
    exit 1
fi

# Функция для безопасного удаления с поддержкой ~ и шаблонов
clean_file() {
    if [ -z "$1" ]; then
        return
    fi
    
    # Раскрываем тильду в домашнюю директорию
    local path="${1/#\~/$HOME}"
    
    # Проверяем, есть ли шаблон *
    if [[ "$path" == *"*"* ]]; then
        # Безопасная обработка шаблона
        local base_dir="$(dirname "$path")"
        local pattern="$(basename "$path")"
        
        # Раскрываем тильду в dirname тоже
        base_dir="${base_dir/#\~/$HOME}"
        
        # Проверяем существование директории
        if [ ! -d "$base_dir" ]; then
            return
        fi
        
        echo "Удаляю файлы по шаблону: $1"
        # Используем find без xargs для безопасности
        find "$base_dir" -maxdepth 1 -name "$pattern" -exec rm -rf {} \; 2>/dev/null || true
    else
        # Обычный файл/директория
        if [ -e "$path" ] || [ -L "$path" ]; then
            echo "Удаляю: $1"
            rm -rf "$path" 2>/dev/null || true
        fi
    fi
}

echo ""
echo "[1/4] Очистка Termux временных файлов..."
echo "---------------------------------------"

# Основные временные файлы Termux
TMPDIR="${TMPDIR:-/data/data/com.termux/files/usr/tmp}"
echo "Используем TMPDIR: $TMPDIR"

# Безопасная очистка TMPDIR
if [ -d "$TMPDIR" ]; then
    echo "Очистка TMPDIR..."
    # Сохраняем содержимое, если нужно
    if [ "$(ls -A "$TMPDIR" 2>/dev/null)" ]; then
        # Удаляем только файлы, не саму папку
        find "$TMPDIR" -mindepth 1 -maxdepth 1 ! -name '.' ! -name '..' \
            -exec rm -rf {} \; 2>/dev/null || true
    fi
    # Гарантируем существование с правильными правами
    mkdir -p "$TMPDIR" 2>/dev/null
    chmod 700 "$TMPDIR" 2>/dev/null || true
else
    mkdir -p "$TMPDIR" 2>/dev/null && chmod 700 "$TMPDIR" 2>/dev/null || true
fi

# Файлы блокировок пакетов
echo "Проверка lock-файлов пакетов..."
for lock in "$PREFIX/var/lib/dpkg/lock-frontend" \
            "$PREFIX/var/lib/dpkg/lock" \
            "$PREFIX/var/cache/apt/archives/lock"; do
    if [ -f "$lock" ]; then
        rm -f "$lock" 2>/dev/null && echo "  Удален: $(basename "$lock")"
    fi
done

# SSH агент
echo "Очистка SSH агента..."
clean_file "$HOME/.ssh/agent.*"
clean_file "$HOME/.ssh/*.sock"

# Termux X11
echo "Очистка X11 файлов..."
clean_file "/data/data/com.termux/files/usr/tmp/.X11-unix"
clean_file "/data/data/com.termux/files/usr/tmp/.X0-lock"
clean_file "/tmp/.X11-unix"
clean_file "/tmp/.X0-lock"
clean_file "$HOME/.cache/termux-x11"

# Убиваем остаточные процессы
echo "Завершение остаточных процессов..."
for proc in "termux-x11" "Xvfb" "Xorg" "xfce" "proot" "Xtightvnc" "Xvnc"; do
    if pgrep -f "$proc" >/dev/null 2>&1; then
        echo "  Останавливаю: $proc"
        pkill -9 -f "$proc" 2>/dev/null || true
    fi
done

echo ""
echo "[2/4] Очистка proot/Ubuntu временных файлов..."
echo "---------------------------------------------"

# Проверяем, установлен ли proot-distro
if command -v proot-distro >/dev/null 2>&1; then
    if proot-distro list 2>/dev/null | grep -q "ubuntu"; then
        echo "Очистка файлов Ubuntu..."
        
        # Определяем команду для выполнения с таймаутом или без
        clean_ubuntu_cmd='
            echo "Выполняю очистку внутри Ubuntu..."
            
            # БЕЗОПАСНАЯ очистка /tmp - только известные временные файлы
            rm -rf /tmp/.X11-unix /tmp/.ICE-unix /tmp/.X[0-9]*-lock 2>/dev/null || true
            rm -rf /tmp/dbus-* /tmp/pulse-* /tmp/.vnc-* 2>/dev/null || true
            
            # Очистка кэша XFCE
            rm -rf ~/.cache/sessions/* ~/.cache/xfce4/* 2>/dev/null || true
            rm -f ~/.ICEauthority ~/.Xauthority 2>/dev/null || true
            
            # VNC
            rm -f ~/.vnc/*.pid ~/.vnc/*.log 2>/dev/null || true
            
            # Воссоздаем необходимые директории
            mkdir -p /tmp ~/.cache ~/.vnc 2>/dev/null || true
            
            echo "✓ Ubuntu очищена"
        '
        
        # Пытаемся выполнить с таймаутом, если доступен
        if command -v timeout >/dev/null 2>&1; then
            echo "Использую timeout (30 секунд)..."
            if ! timeout 30 proot-distro login ubuntu -- /bin/bash -c "$clean_ubuntu_cmd" 2>/dev/null; then
                echo "  Предупреждение: таймаут или ошибка при входе в Ubuntu"
            fi
        else
            echo "Выполняю без таймаута..."
            if ! proot-distro login ubuntu -- /bin/bash -c "$clean_ubuntu_cmd" 2>/dev/null; then
                echo "  Ошибка при входе в Ubuntu"
            fi
        fi
    else
        echo "Ubuntu не установлена в proot-distro"
    fi
else
    echo "proot-distro не установлен"
fi

echo ""
echo "[3/4] Очистка общих временных файлов..."
echo "--------------------------------------"

# Очистка /tmp с фильтрацией
echo "Очистка /tmp от временных файлов..."
if [ -d "/tmp" ]; then
    find /tmp -maxdepth 1 \
        \( -name "ssh-*" -o -name "tmux-*" -o -name "screen-*" \
           -o -name ".esd-*" -o -name ".gdm-*" -o -name ".gnome-*" \
           -o -name ".orbit-*" -o -name ".font-unix" \) \
        -exec rm -rf {} \; 2>/dev/null || true
fi

# Безопасная очистка кэша
echo "Безопасная очистка кэша пользователя..."
for cache_dir in thumbnails sessions dconf gstreamer-1.0 upstart; do
    clean_file "$HOME/.cache/$cache_dir"
done

# Очистка кэша APT
if command -v apt >/dev/null 2>&1; then
    echo "Очистка кэша APT..."
    apt autoclean 2>/dev/null || echo "  Не удалось очистить APT кэш"
fi

echo ""
echo "[4/4] Финальные проверки и восстановление..."
echo "------------------------------------------"

# Воссоздаем необходимые директории
echo "Восстановление необходимых директорий..."
for dir in "$TMPDIR" "$HOME/.cache" "$HOME/.vnc"; do
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir" 2>/dev/null && echo "  Создана: $dir"
    fi
done

# Устанавливаем правильные права
chmod 700 "$HOME/.vnc" 2>/dev/null || true

# Проверяем процессы
echo ""
echo "Проверка текущих процессов Termux..."
if command -v ps >/dev/null 2>&1; then
    running_procs=$(ps -e 2>/dev/null | grep -E "(termux|proot|X)" | grep -v grep || true)
    if [ -n "$running_procs" ]; then
        echo "Найденные процессы:"
        echo "$running_procs"
    else
        echo "  ✓ Нет подозрительных процессов"
    fi
fi

echo ""
echo "======================================="
echo "          ✓ ОЧИСТКА ЗАВЕРШЕНА!        "
echo "======================================="
echo ""
echo "Рекомендуемые действия:"
echo "1. Закройте Termux свайпом из многозадачности"
echo "2. Запустите Termux заново"
echo ""
echo "Для запуска Ubuntu/XFCE выполните:"
echo "   termux-x11 :0 &"
echo "   sleep 2"
echo "   proot-distro login ubuntu -- startxfce4"
echo ""
echo "Или создайте скрипт запуска:"
echo '   cat > ~/start-desktop.sh << "EOF"'
echo '   #!/bin/bash'
echo '   echo "Запуск X11 сервера..."'
echo '   termux-x11 :0 &'
echo '   sleep 3'
echo '   echo "Запуск Ubuntu/XFCE..."'
echo '   proot-distro login ubuntu -- bash -c "export DISPLAY=:0 && startxfce4"'
echo '   EOF'
echo '   chmod +x ~/start-desktop.sh'
echo ""
echo "Запуск рабочего стола:"
echo "   ~/start-desktop.sh"
echo ""
echo "Удачи!"
