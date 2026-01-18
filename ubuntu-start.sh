#!/data/data/com.termux/files/usr/bin/bash
# xfce-manager.sh - Управление XFCE в Termux

# Функция запуска XFCE
start_xfce() {
    echo "🚀 Запуск XFCE..."
    
    # Проверяем, не запущен ли уже X11
    if pgrep -f "termux-x11" > /dev/null; then
        echo "⚠️  Termux X11 уже запущен"
    else
        echo "🖥️  Запускаю Termux X11 сервер..."
        termux-x11 :0 &
        sleep 3
    fi
    
    echo "🐧 Запускаю XFCE в Ubuntu..."
    proot-distro login ubuntu -- bash -c 'export DISPLAY=:0 && startxfce4'
}

# Функция остановки XFCE
stop_xfce() {
    echo "🛑 Остановка XFCE..."
    
    # Останавливаем процессы в Ubuntu
    timeout 5 proot-distro login ubuntu -- /bin/bash -c '
        pkill -9 -f startxfce4 2>/dev/null || true
        pkill -9 -f xfce 2>/dev/null || true
    ' 2>/dev/null || true
    
    # Останавливаем X11 сервер
    pkill -9 -f "termux-x11" 2>/dev/null && echo "✅ Termux X11 остановлен" || echo "⚠️  Termux X11 не был запущен"
    
    echo "✅ XFCE остановлен"
}

# Функция проверки статуса
check_status() {
    echo "📊 Статус системы:"
    
    if pgrep -f "termux-x11" > /dev/null; then
        echo "   ✅ Termux X11: ЗАПУЩЕН (PID: $(pgrep -f 'termux-x11'))"
    else
        echo "   ❌ Termux X11: НЕ ЗАПУЩЕН"
    fi
    
    if pgrep -f "proot.*ubuntu" > /dev/null; then
        echo "   ✅ Ubuntu proot: ЗАПУЩЕН (PID: $(pgrep -f 'proot.*ubuntu'))"
    else
        echo "   ❌ Ubuntu proot: НЕ ЗАПУЩЕН"
    fi
    
    if pgrep -f "startxfce4" > /dev/null; then
        echo "   ✅ XFCE4: ЗАПУЩЕН (PID: $(pgrep -f 'startxfce4'))"
    else
        echo "   ❌ XFCE4: НЕ ЗАПУЩЕН"
    fi
}

# Функция перезапуска
restart_xfce() {
    echo "🔄 Перезапуск XFCE..."
    stop_xfce
    sleep 2
    start_xfce
}

# Функция справки
show_help() {
    echo "📖 Использование: $0 [КОМАНДА]"
    echo ""
    echo "Команды:"
    echo "  start     - Запустить XFCE (по умолчанию)"
    echo "  stop      - Остановить XFCE"
    echo "  status    - Показать статус"
    echo "  restart   - Перезапустить XFCE"
    echo "  help      - Показать эту справку"
    echo ""
    echo "Примеры:"
    echo "  $0          # Запустить XFCE"
    echo "  $0 stop     # Остановить XFCE"
    echo "  $0 status   # Проверить статус"
}

# Обработка аргументов
case "${1:-start}" in
    "start")
        start_xfce
        ;;
    "stop")
        stop_xfce
        ;;
    "status")
        check_status
        ;;
    "restart")
        restart_xfce
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        echo "❌ Неизвестная команда: $1"
        echo "   Используйте: $0 help"
        exit 1
        ;;
esac
