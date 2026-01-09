import os
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PySide6.QtGui import QPainter, QColor, QPen, QBrush
from PySide6.QtCore import Qt
from core.logger_v2026 import get_logger
from utils.menu_manager import MenuManager
from core.data_loader import DataLoader

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
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#121212"))
        
        if not self.data:
            painter.setPen(QColor("#FFFFFF"))
            painter.drawText(self.rect(), Qt.AlignCenter, "No Data")
            return

        # Масштабирование
        max_p = max(c['h'] for c in self.data)
        min_p = min(c['l'] for c in self.data)
        diff = max_p - min_p if max_p != min_p else 1
        
        h = self.height() - 60
        w = self.width() - 20
        c_width = max(1, w // len(self.data) - 1)

        for i, c in enumerate(self.data):
            x = i * (c_width + 1) + 10
            # Рассчет Y координат
            y_o = h - ((c['o'] - min_p) / diff) * h + 30
            y_c = h - ((c['c'] - min_p) / diff) * h + 30
            y_h = h - ((c['h'] - min_p) / diff) * h + 30
            y_l = h - ((c['l'] - min_p) / diff) * h + 30

            color = QColor("#00FF00") if c['c'] >= c['o'] else QColor("#FF0000")
            painter.setPen(QPen(color, 1))
            painter.setBrush(QBrush(color))
            
            # Фитиль и тело
            painter.drawLine(x + c_width//2, y_h, x + c_width//2, y_l)
            painter.drawRect(x, min(y_o, y_c), c_width, max(1, abs(y_o - y_c)))

        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(20, 20, f"{self.title} | {len(self.data)} candles")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.log = get_logger("GUI_2026")
        self.setWindowTitle("Termux FinChart 2026")
        self.resize(1000, 700)
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        xml_path = os.path.join(base_dir, "storage", "state", "exchanges_config.xml")
        
        self.manager = ExchangeDataManager(xml_path) if ExchangeDataManager and os.path.exists(xml_path) else None
        
        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.layout = QVBoxLayout(self.central)
        self.menu_controller = MenuManager(self)
        self.menu_controller.setup_ui()

    def show_default_chart(self):
        self.clear_layout()
        self.layout.addWidget(CandlestickChart([], "Welcome"))

    def on_tool_selected(self, e, m, t):
        path = self.manager.get_tool_data_path(e, m, t)
        s_date = self.manager.get_start_date_for_tool(e, m, t)
        e_date = self.manager.get_end_date_for_tool(e, m, t)
        
        if all([path, s_date, e_date]):
            self.log.info(f"Loading {t} | Path: {path}")
            loader = DataLoader(path, t)
            # Загружаем 15-минутные свечи для примера
            candles = loader.get_candles(s_date, e_date, timeframe_min=15)
            self.clear_layout()
            self.layout.addWidget(CandlestickChart(candles, f"{t} (15m)"))

    def clear_layout(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

