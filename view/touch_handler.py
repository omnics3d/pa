from PySide6.QtCore import QObject, QPoint, QTimer

class TouchHandler(QObject):
    def __init__(self, update_callback):
        super().__init__()
        self.update_callback = update_callback
        self.last_pos = QPoint()
        self.velocity = 0
        self.is_dragging = False
        self.timer = QTimer()
        self.timer.timeout.connect(self._apply_inertia)

    def handle_press(self, pos):
        self.is_dragging = True
        self.last_pos = pos
        self.velocity = 0
        self.timer.stop()

    def handle_move(self, pos, candle_width):
        if not self.is_dragging: return 0
        delta_x = pos.x() - self.last_pos.x()
        self.velocity = delta_x
        candles_delta = delta_x / (candle_width + 1)
        if abs(candles_delta) >= 1:
            self.last_pos = pos
            return int(candles_delta)
        return 0

    def handle_release(self):
        self.is_dragging = False
        if abs(self.velocity) > 5:
            self.timer.start(16)

    def _apply_inertia(self):
        if abs(self.velocity) < 1:
            self.timer.stop()
            return
        shift = int(self.velocity / 5)
        if shift != 0:
            self.update_callback(shift)
        self.velocity *= 0.92

    def handle_wheel_zoom(self, angle_y, current_zoom):
        step = 1 if current_zoom < 20 else 3
        if angle_y > 0:
            return min(150, current_zoom + step)
        return max(1, current_zoom - step)

