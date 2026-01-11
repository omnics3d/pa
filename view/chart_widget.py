import math
from PySide6.QtWidgets import QWidget, QScrollBar, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QWheelEvent, QMouseEvent
from PySide6.QtCore import Qt, QPoint, QRect

class CandlestickChart(QWidget):
    def __init__(self, data, title="Chart", candle_width_px=4):
        super().__init__()
        self.data = data
        self.title = title
        self.candle_width = candle_width_px
        self.scroll_offset = 0 
        self.price_scale_width = 70 
        
        # Основной вертикальный лейаут
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        self.main_layout.addStretch() # Место для самого графика (painter)

        # Нижний горизонтальный лейаут для скроллбара
        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.setContentsMargins(0, 0, 0, 0)
        self.bottom_layout.setSpacing(0)

        # Настройка скроллбара
        self.scrollbar = QScrollBar(Qt.Horizontal)
        self.scrollbar.setStyleSheet("""
            QScrollBar:horizontal { height: 12px; background: #1e1e1e; border: none; }
            QScrollBar::handle:horizontal { background: #444; min-width: 20px; border-radius: 4px; }
            QScrollBar::handle:horizontal:hover { background: #666; }
            QScrollBar::add-line, QScrollBar::sub-line { background: none; width: 0px; }
        """)
        
        self.bottom_layout.addWidget(self.scrollbar)
        
        # Добавляем пустой отступ справа под шкалой цен
        self.spacer = QSpacerItem(self.price_scale_width, 12, QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.bottom_layout.addSpacerItem(self.spacer)

        self.main_layout.addLayout(self.bottom_layout)
        
        self.scrollbar.valueChanged.connect(self._on_scrollbar_moved)
        self.setMouseTracking(True)
        self._last_mouse_pos = QPoint()
        
        self._update_scroll_range()

    def _update_scroll_range(self):
        if not self.data:
            self.scrollbar.hide()
            return
        
        self.scrollbar.show()
        chart_width = self.width() - self.price_scale_width
        num_on_screen = max(1, chart_width // (self.candle_width + 1))
        max_scroll = max(0, len(self.data) - num_on_screen)
        
        self.scrollbar.setRange(0, max_scroll)
        self.scrollbar.blockSignals(True)
        self.scrollbar.setValue(max_scroll - self.scroll_offset)
        self.scrollbar.blockSignals(False)

    def _on_scrollbar_moved(self, value):
        self.scroll_offset = self.scrollbar.maximum() - value
        self.update()

    def apply_scroll_delta(self, delta_candles):
        max_s = self.scrollbar.maximum()
        new_offset = max(0, min(self.scroll_offset + delta_candles, max_s))
        if new_offset != self.scroll_offset:
            self.scroll_offset = new_offset
            self.scrollbar.blockSignals(True)
            self.scrollbar.setValue(max_s - self.scroll_offset)
            self.scrollbar.blockSignals(False)
            self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_scroll_range()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._last_mouse_pos = event.pos()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() & Qt.LeftButton:
            dx = event.pos().x() - self._last_mouse_pos.x()
            delta_candles = dx // (self.candle_width + 1)
            if delta_candles != 0:
                self.apply_scroll_delta(-delta_candles)
                self._last_mouse_pos = event.pos()

    def wheelEvent(self, event: QWheelEvent):
        ay = event.angleDelta().y()
        if ay != 0:
            if ay > 0: self.candle_width = min(self.candle_width + 1, 50)
            else: self.candle_width = max(self.candle_width - 1, 1)
            
            try:
                main_win = self.window()
                if hasattr(main_win, 'zoom_level_px'):
                    main_win.zoom_level_px = self.candle_width
            except: pass
            
            self._update_scroll_range()
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#121212"))
        
        if not self.data:
            painter.setPen(QColor("#FFFFFF"))
            painter.drawText(self.rect(), Qt.AlignCenter, "No Data")
            return

        reversed_data = list(reversed(self.data))
        visible_list = reversed_data[self.scroll_offset:]
        
        chart_width = self.width() - self.price_scale_width
        num_on_screen = max(1, chart_width // (self.candle_width + 1))
        on_screen_data = reversed_data[self.scroll_offset : self.scroll_offset + num_on_screen] or visible_list

        if not on_screen_data: return

        max_p = max(c['h'] for c in on_screen_data)
        min_p = min(c['l'] for c in on_screen_data)
        diff = (max_p - min_p) or 1
        
        # Высота графика теперь ограничена только скроллбаром (12px)
        chart_height = self.height() - 42 
        top_margin = 30

        # 1. Шкала цен (фон рисуем до самого низа окна)
        self._draw_price_scale_and_grid(painter, min_p, max_p, chart_height, top_margin, chart_width)

        # 2. Отрисовка свечей
        for i, c in enumerate(visible_list):
            x = chart_width - (i * (self.candle_width + 1)) - 10
            if x < -self.candle_width: break
            
            y_o = chart_height - ((c['o'] - min_p) / diff) * chart_height + top_margin
            y_c = chart_height - ((c['c'] - min_p) / diff) * chart_height + top_margin
            y_h = chart_height - ((c['h'] - min_p) / diff) * chart_height + top_margin
            y_l = chart_height - ((c['l'] - min_p) / diff) * chart_height + top_margin
            
            color = QColor("#00FF00") if c['c'] >= c['o'] else QColor("#FF0000")
            painter.setPen(QPen(color, 1))
            painter.setBrush(QBrush(color))
            painter.drawLine(x + self.candle_width//2, int(y_h), x + self.candle_width//2, int(y_l))
            painter.drawRect(x, int(min(y_o, y_c)), self.candle_width, max(1, int(abs(y_o - y_c))))

        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(20, 20, f"{self.title} | Zoom: {self.candle_width}px")

    def _draw_price_scale_and_grid(self, painter, min_p, max_p, chart_height, top_margin, chart_width):
        """Рисует шкалу цен до самого низа окна."""
        if max_p == min_p: return

        # Фон шкалы рисуем на всю высоту виджета (self.height())
        scale_rect = QRect(chart_width, 0, self.price_scale_width, self.height())
        painter.fillRect(scale_rect, QColor("#1e1e1e"))
        painter.setPen(QPen(QColor("#444444"), 1))
        painter.drawLine(chart_width, 0, chart_width, self.height())

        raw_step = (max_p - min_p) / 15
        magnitude = 10 ** math.floor(math.log10(raw_step)) if raw_step > 0 else 1
        res = raw_step / magnitude
        
        if res < 1.5: step = 1 * magnitude
        elif res < 3: step = 2 * magnitude
        elif res < 7: step = 5 * magnitude
        else: step = 10 * magnitude

        start_price = math.ceil(min_p / step) * step
        precision = max(0, -math.floor(math.log10(step))) if step < 1 else 0
        fmt = "{:." + str(precision) + "f}"

        current_price = start_price
        while current_price <= max_p:
            y_pos = chart_height - ((current_price - min_p) / (max_p - min_p) * chart_height) + top_margin
            
            # Сетка
            painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
            painter.drawLine(0, int(y_pos), chart_width, int(y_pos))

            # Цена
            painter.setPen(QColor("#CCCCCC"))
            painter.drawText(chart_width + 5, int(y_pos + 5), fmt.format(current_price))
            
            current_price += step
            if step <= 0: break

