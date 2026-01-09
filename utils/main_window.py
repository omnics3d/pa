import sys
import os
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QMenu
from PySide6.QtGui import QPainter, QColor, QPen, QAction
from PySide6.QtCore import Qt
from core.logger_v2026 import get_logger

# Импорт менеджера
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
        # Тестовая отрисовка линии тренда
        painter.setPen(QPen(QColor("#00FF00"), 2))
        painter.drawLine(0, self.height()//2, self.width(), self.height()//2)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.log = get_logger("GUI_2026")
        self.setWindowTitle("Termux FinChart 2026")
        self.resize(800, 600)
        
        # Настройка пути к XML (storage/state/exchanges_config.xml)
        self.manager = None
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        xml_path = os.path.join(base_dir, "storage", "state", "exchanges_config.xml")
        
        if ExchangeDataManager:
            if os.path.exists(xml_path):
                try:
                    self.manager = ExchangeDataManager(xml_path)
                    self.log.info(f"Конфигурация загружена из: {xml_path}")
                except Exception as e:
                    self.log.error(f"Ошибка загрузки XML: {e}")
            else:
                self.log.warning(f"Файл конфигурации не найден: {xml_path}")

        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.layout = QVBoxLayout(self.central)
        self.init_menu()

    def init_menu(self):
        bar = self.menuBar()
        
        # 1. Кнопка Graph
        graph_act = bar.addAction("Graph")
        graph_act.triggered.connect(self.show_default_chart)
        
        # 2. Динамическое меню выбора (Select)
        if self.manager:
            self.select_menu = bar.addMenu("Select")
            self.build_dynamic_menu(self.select_menu)

    def build_dynamic_menu(self, menu):
        try:
            exchanges = self.manager.get_exchange_names()
            for ex in exchanges:
                ex_m = menu.addMenu(ex)
                markets = self.manager.get_markets_for_exchange(ex) or []
                for mk in markets:
                    mk_m = ex_m.addMenu(mk)
                    tools = self.manager.get_tools_for_market(ex, mk) or []
                    for tl in tools:
                        act = QAction(tl, self)
                        # Используем lambda с дефолтными значениями для фиксации итератора
                        act.triggered.connect(lambda chk=False, e=ex, m=mk, t=tl: self.on_tool_selected(e,m,t))
                        mk_m.addAction(act)
        except Exception as e:
            self.log.error(f"Ошибка построения меню: {e}")

    def show_default_chart(self):
        self.clear_layout()
        chart = CandlestickChart([(10,20,5,15)], "Default Chart")
        self.layout.addWidget(chart)

    def on_tool_selected(self, e, m, t):
        self.log.info(f"Выбран инструмент: {e} -> {m} -> {t}")
        self.clear_layout()
        chart = CandlestickChart([(10,20,5,15)], f"Chart: {e} | {t}")
        self.layout.addWidget(chart)

    def clear_layout(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

