import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from core.logger_v2026 import setup_logging, get_logger

# 1. Инициализация вашего логгера v2026
# Распределяем потоки: INFO и выше в консоль и файл, ERROR отдельно
setup_logging(
    level="DEBUG",
    log_files={
        "DEBUG": "logs/server.log"
    },
    use_colors=True,
    json_format=True  # Для обычного чтения файлов оставляем текстовый формат
)

logger = get_logger("TermuxServer")
logger.debug("Проверка создания нового файла лога")

class LogHandler(SimpleHTTPRequestHandler):
    def do_POST(self):
        """Обработка входящих логов от main_v.py"""
        if self.path == '/log':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length).decode('utf-8')
                
                # Записываем удаленный лог через нашу систему логирования
                # Используем префикс [REMOTE], чтобы отличать их от логов сервера
                logger.info(f"[REMOTE] {post_data}")
                
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b"OK")
            except Exception as e:
                logger.error(f"Ошибка при приеме лога: {e}")
                self.send_error(500)
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        """Перехват стандартных сообщений сервера (GET запросы и т.д.)"""
        # Направляем их в DEBUG, чтобы не спамить в консоль, 
        # но они сохранятся, если изменить уровень логгера
        logger.debug(f"HTTP {format % args}")

if __name__ == "__main__":
    # Установка рабочей директории
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    port = 8080
    server_address = ('', port)
    
    try:
        httpd = HTTPServer(server_address, LogHandler)
        logger.info(f"=== СЕРВЕР 2026 ЗАПУЩЕН НА ПОРТУ {port} ===")
        logger.info("Логи сохраняются в папку logs/")
        
        httpd.serve_forever()
        
    except KeyboardInterrupt:
        logger.warning("\nОстановка сервера пользователем (Ctrl+C)")
        httpd.server_close()
    except Exception as e:
        logger.critical(f"Критический сбой сервера: {e}")

