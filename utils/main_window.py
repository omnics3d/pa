import sys
import os
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PySide6.QtGui import QPainter, QColor, QPen
from core.logger_v2026 import get_logger
from utils.menu_manager import MenuManager # Новый импорт

try:
    from core.exchange_manager import ExchangeDataManager
except ImportError:
    ExchangeDataManager = None

class CandlestickChart(QWidget):
    def __init__(self, data, title="Chart"):
        super().__init__()
        self.data = data
        self.title = title

    def paintEvent(self, event):
        if not self.data: return
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#121212"))
        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(20, 20, self.title)
        painter.setPen(QPen(QColor("#00FF00"), 2))
        painter.drawLine(0, self.height()//2, self.width(), self.height()//2)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.log = get_logger("GUI_2026")
        self.setWindowTitle("Termux FinChart 2026")
        self.resize(800, 600)
        
        # Загрузка менеджера данных
        self.manager = None
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        xml_path = os.path.join(base_dir, "storage", "state", "exchanges_config.xml")
        
        if ExchangeDataManager and os.path.exists(xml_path):
            try:
                self.manager = ExchangeDataManager(xml_path)
            except Exception as e:
                self.log.error(f"XML Error: {e}")

        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.layout = QVBoxLayout(self.central)

        # Инициализация меню через внешний менеджер
        self.menu_controller = MenuManager(self)
        self.menu_controller.setup_ui()

    def show_default_chart(self):
        self.clear_layout()
        chart = CandlestickChart([(10, 20, 5, 15)], "Default Chart")
        self.layout.addWidget(chart)

    def on_tool_selected(self, e, m, t):
        self.log.info(f"Selected: {e} -> {t}")
        self.clear_layout()
        chart = CandlestickChart([(10, 20, 5, 15)], f"Chart: {e} | {t}")
        self.layout.addWidget(chart)

    def clear_layout(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

