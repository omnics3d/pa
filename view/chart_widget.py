from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QWheelEvent, QMouseEvent
from PySide6.QtCore import Qt, QPoint

class CandlestickChart(QWidget):
    def __init__(self, data, title="Chart", candle_width_px=4):
        super().__init__()
        self.data = data
        self.title = title
        self.candle_width = candle_width_px
        self.scroll_offset = 0
        self.setMouseTracking(True)
        self._last_mouse_pos = QPoint()

    def apply_scroll_delta(self, delta_candles):
        old_offset = self.scroll_offset
        self.scroll_offset = max(0, min(self.scroll_offset + delta_candles, len(self.data) - 5))
        if old_offset != self.scroll_offset:
            self.update()

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
        delta = event.angleDelta().y()
        if delta != 0:
            old_zoom = self.candle_width
            if delta > 0:
                self.candle_width = min(self.candle_width + 1, 50)
            else:
                self.candle_width = max(self.candle_width - 1, 1)
            
            if old_zoom != self.candle_width:
                try:
                    main_win = self.window()
                    if hasattr(main_win, 'zoom_level_px'):
                        main_win.zoom_level_px = self.candle_width
                except Exception: 
                    pass
                self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#121212"))
        
        if not self.data:
            painter.setPen(QColor("#FFFFFF"))
            painter.drawText(self.rect(), Qt.AlignCenter, "No Data")
            return

        visible_list = list(reversed(self.data))[self.scroll_offset:]
        num_on_screen = self.width() // (self.candle_width + 1)
        on_screen_data = visible_list[:num_on_screen] or visible_list

        max_p = max(c['h'] for c in on_screen_data)
        min_p = min(c['l'] for c in on_screen_data)
        diff = (max_p - min_p) or 1
        h, w = self.height() - 60, self.width() - 20

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

