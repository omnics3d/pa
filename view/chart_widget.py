from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QWheelEvent, QMouseEvent
from PySide6.QtCore import Qt
from view.touch_handler import TouchHandler

class CandlestickChart(QWidget):
    def __init__(self, data, title="Chart", candle_width_px=4):
        super().__init__()
        self.data = data
        self.title = title
        self.candle_width = candle_width_px
        self.scroll_offset = 0
        self.touch_handler = TouchHandler(self.apply_scroll_delta)
        self.setMouseTracking(True)

    def apply_scroll_delta(self, delta_candles):
        old_offset = self.scroll_offset
        self.scroll_offset = max(0, min(self.scroll_offset - delta_candles, len(self.data) - 5))
        if old_offset != self.scroll_offset:
            self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.touch_handler.handle_press(event.pos())

    def mouseMoveEvent(self, event: QMouseEvent):
        delta = self.touch_handler.handle_move(event.pos(), self.candle_width)
        if delta != 0: self.apply_scroll_delta(delta)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.touch_handler.handle_release()

    def wheelEvent(self, event: QWheelEvent):
        ay, ax = event.angleDelta().y(), event.angleDelta().x()
        if ay != 0:
            new_zoom = self.touch_handler.handle_wheel_zoom(ay, self.candle_width)
            if new_zoom != self.candle_width:
                self.candle_width = new_zoom
                try: self.parentWidget().parent().zoom_level_px = new_zoom
                except: pass
                self.update()
        elif ax != 0:
            self.apply_scroll_delta(ax // 120 * 3)

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

