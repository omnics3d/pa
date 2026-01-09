import sys
import os
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PySide6.QtGui import QPainter, QColor, QPen
from core.logger_v2026 import get_logger
from utils.menu_manager import MenuManager
from core.data_loader import DataLoader # Новый импорт

try:
    from core.exchange_manager import ExchangeDataManager
except ImportError:
    ExchangeDataManager = None

class CandlestickChart(QWidget):
    def __init__(self, data, title="Chart"):
        super().__init__()
        self.data = data # Теперь это список агрегированных свечей
        self.title = title

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#121212"))
        painter.setPen(QColor("#FFFFFF"))
        
        info_text = f"{self.title} | Candles: {len(self.data)}"
        painter.drawText(20, 20, info_text)
        
        # Если есть данные, рисуем тестовую линию по ценам закрытия
        if self.data:
            painter.setPen(QPen(QColor("#00FF00"), 2))
            painter.drawLine(0, self.height()//2, self.width(), self.height()//2)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.log = get_logger("GUI_2026")
        self.setWindowTitle("Termux FinChart 2026")
        self.resize(800, 600)
        
        self.manager = None
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        xml_path = os.path.join(base_dir, "storage", "state", "exchanges_config.xml")
        
        if ExchangeDataManager and os.path.exists(xml_path):
            try:
                self.manager = ExchangeDataManager(xml_path)
                self.log.info(f"Config loaded: {xml_path}")
            except Exception as e:
                self.log.error(f"XML Error: {e}")

        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.layout = QVBoxLayout(self.central)

        self.menu_controller = MenuManager(self)
        self.menu_controller.setup_ui()

    def show_default_chart(self):
        self.clear_layout()
        chart = CandlestickChart(data=[], title="No Data Loaded")
        self.layout.addWidget(chart)

    def on_tool_selected(self, e, m, t):
        """Выбор инструмента с автоматической загрузкой и агрегацией ТФ."""
        if not self.manager: return
            
        path = self.manager.get_tool_data_path(e, m, t)
        start_date = self.manager.get_start_date_for_tool(e, m, t)
        end_date = self.manager.get_end_date_for_tool(e, m, t)
        
        if all([path, start_date, end_date]):
            self.log.info(f"Selected: {t} | DATA PATH: {path}")
            
            # Инициализируем загрузчик
            loader = DataLoader(path, t)
            # Пример: собираем 15-минутные свечи (timeframe_min=15)
            # Сюда можно передать и 10032 для экстремальных ТФ
            candles = loader.get_candles(start_date, end_date, timeframe_min=15)
            
            self.clear_layout()
            chart = CandlestickChart(data=candles, title=f"Chart: {e}:{t} (15m)")
            self.layout.addWidget(chart)
        else:
            self.log.error(f"Incomplete data in XML for tool: {t}")

    def clear_layout(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

