from PySide6.QtWidgets import QWidget, QScrollBar, QVBoxLayout
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QWheelEvent, QMouseEvent
from PySide6.QtCore import Qt, QPoint

class CandlestickChart(QWidget):
    def __init__(self, data, title="Chart", candle_width_px=4):
        super().__init__()
        self.data = data
        self.title = title
        self.candle_width = candle_width_px
        self.scroll_offset = 0 # 0 — это самые новые свечи
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.scrollbar = QScrollBar(Qt.Horizontal)
        # Стиль остается прежним
        self.scrollbar.setStyleSheet("""
            QScrollBar:horizontal { height: 12px; background: #1e1e1e; }
            QScrollBar::handle:horizontal { background: #444; min-width: 20px; border-radius: 4px; }
            QScrollBar::add-line, QScrollBar::sub-line { background: none; }
        """)
        
        self.layout.addStretch()
        self.layout.addWidget(self.scrollbar)
        
        self.scrollbar.valueChanged.connect(self._on_scrollbar_moved)
        self.setMouseTracking(True)
        self._last_mouse_pos = QPoint()
        
        self._update_scroll_range()

    def _update_scroll_range(self):
        if not self.data:
            self.scrollbar.hide()
            return
        
        self.scrollbar.show()
        num_on_screen = self.width() // (self.candle_width + 1)
        max_scroll = max(0, len(self.data) - num_on_screen)
        
        self.scrollbar.setRange(0, max_scroll)
        self.scrollbar.blockSignals(True)
        # ИНВЕРСИЯ: Чтобы ползунок был справа при offset=0, ставим max - offset
        self.scrollbar.setValue(max_scroll - self.scroll_offset)
        self.scrollbar.blockSignals(False)

    def _on_scrollbar_moved(self, value):
        # ИНВЕРСИЯ: offset = max - текущее_значение_ползунка
        self.scroll_offset = self.scrollbar.maximum() - value
        self.update()

    def apply_scroll_delta(self, delta_candles):
        # delta > 0 — скролл в прошлое (увеличиваем offset)
        new_offset = max(0, min(self.scroll_offset + delta_candles, self.scrollbar.maximum()))
        if new_offset != self.scroll_offset:
            self.scroll_offset = new_offset
            # Обновляем ползунок (с инверсией)
            self.scrollbar.blockSignals(True)
            self.scrollbar.setValue(self.scrollbar.maximum() - self.scroll_offset)
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
                # Тянем вправо (dx > 0) -> уменьшаем offset (движемся к новым свечам)
                self.apply_scroll_delta(-delta_candles)
                self._last_mouse_pos = event.pos()

    def wheelEvent(self, event: QWheelEvent):
        if event.angleDelta().y() != 0:
            if event.angleDelta().y() > 0:
                self.candle_width = min(self.candle_width + 1, 50)
            else:
                self.candle_width = max(self.candle_width - 1, 1)
            
            try:
                main_win = self.window()
                if hasattr(main_win, 'zoom_level_px'):
                    main_win.zoom_level_px = self.candle_width
            except: pass
            
            self._update_scroll_range()
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#121212"))
        if not self.data: return

        # Справа — последние свечи
        reversed_data = list(reversed(self.data))
        visible_list = reversed_data[self.scroll_offset:]
        
        num_on_screen = self.width() // (self.candle_width + 1)
        on_screen_data = visible_list[:num_on_screen] or visible_list

        max_p = max(c['h'] for c in on_screen_data)
        min_p = min(c['l'] for c in on_screen_data)
        diff = (max_p - min_p) or 1
        h, w = self.height() - 72, self.width() - 20

        for i, c in enumerate(visible_list):
            x = w - (i * (self.candle_width + 1)) - 10
            if x < -self.candle_width: break
            
            y_o = h - ((c['o'] - min_p) / diff) * h + 30
            y_c = h - ((c['c'] - min_p) / diff) * h + 30
            y_h = h - ((c['h'] - min_p) / diff) * h + 30
            y_l = h - ((c['l'] - min_p) / diff) * h + 30
            
            color = QColor("#00FF00") if c['c'] >= c['o'] else QColor("#FF0000")
            painter.setPen(QPen(color, 1))
            painter.setBrush(QBrush(color))
            painter.drawLine(x + self.candle_width//2, y_h, x + self.candle_width//2, y_l)
            painter.drawRect(x, min(y_o, y_c), self.candle_width, max(1, abs(y_o - y_c)))

        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(20, 20, f"{self.title} | Zoom: {self.candle_width}px")

