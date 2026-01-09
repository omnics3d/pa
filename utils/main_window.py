import sys
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont
from PySide6.QtCore import Qt, QRectF
from core.logger_v2026 import get_logger

class CandlestickChart(QWidget):
    def __init__(self, data):
        super().__init__()
        # Формат данных: [(Open, High, Low, Close), ...]
        self.data = data
        self.resistance_level = 115.0 # Пример уровня сопротивления
        self.support_level = 95.0    # Пример уровня поддержки

    def paintEvent(self, event):
        if not self.data:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 1. Фон
        painter.fillRect(self.rect(), QColor("#121212")) # Темная тема

        # 2. Расчет масштабов
        width = self.width()
        height = self.height()
        padding = 60
        
        # Находим min/max цены для масштабирования по вертикали
        all_prices = []
        for o, h, l, c in self.data:
            all_prices.extend([o, h, l, c])
        all_prices.extend([self.resistance_level, self.support_level])
        
        max_p = max(all_prices) * 1.05
        min_p = min(all_prices) * 0.95
        price_range = max_p - min_p

        def price_to_y(price):
            relative_p = (price - min_p) / price_range
            return height - padding - (relative_p * (height - 2 * padding))

        # 3. Рисуем сетку и ценовые метки
        painter.setPen(QPen(QColor("#333333"), 1))
        for i in range(6):
            p = min_p + (price_range / 5) * i
            y = price_to_y(p)
            painter.drawLine(padding, y, width - padding, y)
            painter.setPen(QPen(QColor("#888888")))
            painter.drawText(width - padding + 5, y + 5, f"{p:.1f}")
            painter.setPen(QPen(QColor("#333333"), 1))

        # 4. Рисуем прерывистые линии (Индикаторы/Уровни)
        # Сопротивление (Красная прерывистая)
        pen_red = QPen(QColor("#FF4444"), 2, Qt.DashLine)
        painter.setPen(pen_red)
        y_res = price_to_y(self.resistance_level)
        painter.drawLine(padding, y_res, width - padding, y_res)
        
        # Поддержка (Зеленая прерывистая)
        pen_green = QPen(QColor("#44FF44"), 2, Qt.CustomDashLine)
        pen_green.setDashPattern([4, 4]) # Настройка пунктира
        painter.setPen(pen_green)
        y_sup = price_to_y(self.support_level)
        painter.drawLine(padding, y_sup, width - padding, y_sup)

        # 5. Рисуем японские свечи
        candle_space = (width - 2 * padding) / len(self.data)
        candle_width = candle_space * 0.8
        
        for i, (O, H, L, C) in enumerate(self.data):
            x_center = padding + i * candle_space + candle_space / 2
            x_left = x_center - candle_width / 2
            
            is_bull = C >= O
            color = QColor("#26a69a") if is_bull else QColor("#ef5350")
            
            # Фитиль (High - Low)
            painter.setPen(QPen(color, 1.5))
            painter.drawLine(x_center, price_to_y(H), x_center, price_to_y(L))
            
            # Тело свечи
            painter.setBrush(QBrush(color))
            y_top = price_to_y(max(O, C))
            y_bottom = price_to_y(min(O, C))
            body_h = max(abs(y_top - y_bottom), 1) # Минимум 1 пиксель
            
            painter.drawRect(QRectF(x_left, y_top, candle_width, body_h))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.log = get_logger("GUI")
        self.setWindowTitle("Termux Native FinChart 2026")
        self.resize(800, 600)
        
        # Пример данных (OHLC)
        self.stock_data = [
            (100, 105, 98, 102),
            (102, 108, 101, 107),
            (107, 118, 106, 115),
            (115, 116, 110, 112),
            (112, 114, 105, 106),
            (106, 110, 95, 98),
            (98, 105, 97, 104)
        ]

        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.layout = QVBoxLayout(self.central)
        
        self.init_menu()
        self.log.info("Native QPainter Chart initialized")

    def init_menu(self):
        bar = self.menuBar()
        bar.setNativeMenuBar(False)
        
        graph_act = bar.addAction("Graph")
        graph_act.triggered.connect(self.show_chart)
        
        bar.addAction("Options")
        bar.addAction("Settings")

    def show_chart(self):
        # Очистка
        for i in reversed(range(self.layout.count())): 
            self.layout.itemAt(i).widget().setParent(None)
            
        # Показ графика
        chart = CandlestickChart(self.stock_data)
        self.layout.addWidget(chart)
        self.log.info("Rendering manual candles with dash lines")

