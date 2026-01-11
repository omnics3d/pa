import math
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import Qt, QRect, QPoint

class PriceScale:
    def __init__(self, parent_chart):
        self.chart = parent_chart
        self.width = 70
        self.vertical_zoom = 1.0
        self.is_scaling = False

    def handle_press(self, pos: QPoint):
        if pos.x() > self.chart.width() - self.width:
            self.is_scaling = True
            return True
        return False

    def handle_move(self, pos: QPoint, last_pos: QPoint):
        if self.is_scaling:
            dy = pos.y() - last_pos.y()
            # Плавный прогрессивный зум: 150px для изменения в 2 раза
            zoom_factor = math.pow(2.0, dy / 150.0)
            self.vertical_zoom = max(0.000001, 
                                     self.vertical_zoom * zoom_factor)
            return True
        return False

    def handle_release(self):
        self.is_scaling = False

    def draw(self, painter: QPainter, min_p, max_p, chart_h, top_m):
        if max_p == min_p: return
        chart_w = self.chart.width() - self.width
        
        # Фон шкалы
        s_rect = QRect(chart_w, 0, self.width, self.chart.height())
        painter.fillRect(s_rect, QColor("#1e1e1e"))
        painter.setPen(QPen(QColor("#444444"), 1))
        painter.drawLine(chart_w, 0, chart_w, self.chart.height())

        # Расчет шага (Оригинальный алгоритм)
        r_step = (max_p - min_p) / 15
        mag = 10**math.floor(math.log10(abs(r_step))) if r_step != 0 else 1
        res = abs(r_step / mag)
        if res < 1.5: step = 1 * mag
        elif res < 3: step = 2 * mag
        elif res < 7: step = 5 * mag
        else: step = 10 * mag

        start_p = math.ceil(min_p / step) * step
        prec = max(0, -math.floor(math.log10(step))) if step < 1 else 0
        fmt = "{:." + str(prec) + "f}"
        
        curr_p = start_p
        while curr_p <= max_p:
            y = chart_h - ((curr_p-min_p)/(max_p-min_p)*chart_h) + top_m
            if 0 <= y <= self.chart.height():
                # Сетка
                painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
                painter.drawLine(0, int(y), chart_w, int(y))
                # Текст цены
                painter.setPen(QColor("#CCCCCC"))
                painter.drawText(chart_w + 5, int(y + 5), fmt.format(curr_p))
            curr_p += step
            if step <= 0: break

