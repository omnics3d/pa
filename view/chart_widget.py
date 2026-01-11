import math
import time
from PySide6.QtWidgets import (QWidget, QScrollBar, QVBoxLayout, 
    QHBoxLayout, QSpacerItem, QSizePolicy)
from PySide6.QtGui import (QPainter, QColor, QPen, QBrush, 
    QMouseEvent)
from PySide6.QtCore import Qt, QPoint, QRect, QRectF

class CandlestickChart(QWidget):
    def __init__(self, data, title="Chart", candle_width_px=4):
        super().__init__()
        self.data = data
        self.title = title
        self.candle_width = float(candle_width_px)
        self.scroll_offset = 0 
        self.price_scale_width = 70 
        
        # Вертикальный зум
        self.vertical_zoom = 1.0
        self._is_scaling_price = False
        
        self.btn_zoom_in = QRect()
        self.btn_zoom_out = QRect()
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.main_layout.addStretch()

        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.setContentsMargins(0, 0, 0, 0)
        self.bottom_layout.setSpacing(0)

        self.scrollbar = QScrollBar(Qt.Horizontal)
        self.scrollbar.setStyleSheet("""
            QScrollBar:horizontal { 
                height: 12px; background: #1e1e1e; border: none; 
            }
            QScrollBar::handle:horizontal { 
                background: #444; min-width: 20px; border-radius: 4px; 
            }
            QScrollBar::handle:horizontal:hover { background: #666; }
            QScrollBar::add-line, QScrollBar::sub-line { 
                background: none; width: 0px; 
            }
        """)
        
        self.bottom_layout.addWidget(self.scrollbar)
        self.spacer = QSpacerItem(self.price_scale_width, 12, 
                                  QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.bottom_layout.addSpacerItem(self.spacer)

        self.main_layout.addLayout(self.bottom_layout)
        
        self.scrollbar.valueChanged.connect(self._on_scrollbar_moved)
        self.setMouseTracking(True)
        self._last_mouse_pos = QPoint()
        self._update_scroll_range()

    def _apply_zoom(self, delta):
        # ЛИНЕЙНЫЙ ШАГ БЕЗ ПРОГРЕССИИ
        # delta это +1 или -1. Просто прибавляем/вычитаем единицу.
        # Нижний порог 1.0 не дает графику схлопнуться.
        self.candle_width = max(1.0, self.candle_width + delta)
        
        try:
            main_win = self.window()
            if hasattr(main_win, 'zoom_level_px'):
                main_win.zoom_level_px = int(self.candle_width)
        except: pass
        self._update_scroll_range()
        self.update()

    def _update_scroll_range(self):
        if not self.data:
            self.scrollbar.hide()
            return
        self.scrollbar.show()
        chart_w = self.width() - self.price_scale_width
        num_on_screen = max(1, int(chart_w // (self.candle_width + 0.001)))
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
        new_off = max(0, min(self.scroll_offset + delta_candles, max_s))
        if new_off != self.scroll_offset:
            self.scroll_offset = new_off
            self.scrollbar.blockSignals(True)
            self.scrollbar.setValue(max_s - self.scroll_offset)
            self.scrollbar.blockSignals(False)
            self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_scroll_range()

    def mousePressEvent(self, event: QMouseEvent):
        pos = event.pos()
        if pos.x() > self.width() - self.price_scale_width:
            self._is_scaling_price = True
            self._last_mouse_pos = pos
            return
        if self.btn_zoom_in.contains(pos):
            self._apply_zoom(1.0)
            return
        if self.btn_zoom_out.contains(pos):
            self._apply_zoom(-1.0)
            return
        if event.button() == Qt.LeftButton:
            self._last_mouse_pos = event.pos()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() & Qt.LeftButton:
            pos = event.pos()
            dy = pos.y() - self._last_mouse_pos.y()
            
            if self._is_scaling_price:
                # ПЛАВНЫЙ ПРОГРЕССИВНЫЙ ВЕРТИКАЛЬНЫЙ ЗУМ (СОХРАНЕН)
                zoom_factor = math.pow(2.0, dy / 150.0)
                self.vertical_zoom = max(0.000001, self.vertical_zoom * zoom_factor)
                self._last_mouse_pos = pos
                self.update()
                return

            if (self.btn_zoom_in.contains(pos) or 
                self.btn_zoom_out.contains(pos)):
                return
            
            dx = pos.x() - self._last_mouse_pos.x()
            delta_c = int(dx / (self.candle_width + 0.001))
            if delta_c != 0:
                self.apply_scroll_delta(-delta_c)
                self._last_mouse_pos = pos

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._is_scaling_price = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.fillRect(self.rect(), QColor("#121212"))
        if not self.data:
            painter.setPen(QColor("#FFFFFF"))
            painter.drawText(self.rect(), Qt.AlignCenter, "No Data")
            return
        rev_data = list(reversed(self.data))
        vis_list = rev_data[self.scroll_offset:]
        chart_w = self.width() - self.price_scale_width
        n_scr = max(1, int(chart_w // (self.candle_width + 0.001)))
        on_scr = rev_data[self.scroll_offset:self.scroll_offset+n_scr]
        if not on_scr: return
        
        avg_p = (max(c['h'] for c in on_scr) + min(c['l'] for c in on_scr)) / 2
        range_p = (max(c['h'] for c in on_scr) - min(c['l'] for c in on_scr)) or 1
        
        max_p = avg_p + (range_p * self.vertical_zoom) / 2
        min_p = avg_p - (range_p * self.vertical_zoom) / 2
        diff = (max_p - min_p) or 1
        
        chart_h = self.height() - 42; top_m = 30
        self._draw_price_scale_and_grid(painter, min_p, max_p, 
                                        chart_h, top_m, chart_w)
        for i, c in enumerate(vis_list):
            x = float(chart_w - (i * (self.candle_width + 0.001)) - 10)
            if x < -self.candle_width: break
            y_o = chart_h - ((c['o']-min_p)/diff)*chart_h + top_m
            y_c = chart_h - ((c['c']-min_p)/diff)*chart_h + top_m
            y_h = chart_h - ((c['h']-min_p)/diff)*chart_h + top_m
            y_l = chart_h - ((c['l']-min_p)/diff)*chart_h + top_m
            color = QColor("#00FF00") if c['c'] >= c['o'] else QColor("#FF0000")
            painter.setPen(QPen(color, 0.5 if self.candle_width < 1 else 1))
            painter.setBrush(QBrush(color))
            cw2 = self.candle_width / 2.0
            painter.drawLine(x + cw2, y_h, x + cw2, y_l)
            painter.drawRect(QRectF(x, min(y_o, y_c), 
                             self.candle_width, 
                             max(0.1, abs(y_o - y_c))))
        b_sz = 40; x_b = chart_w - b_sz - 10
        self.btn_zoom_in = QRect(x_b, 10, b_sz, b_sz)
        self.btn_zoom_out = QRect(x_b, 10 + b_sz + 10, b_sz, b_sz)
        painter.setPen(Qt.NoPen); painter.setBrush(QColor(60, 60, 60, 160))
        painter.drawRoundedRect(self.btn_zoom_in, 5, 5)
        painter.drawRoundedRect(self.btn_zoom_out, 5, 5)
        painter.setPen(QColor("white")); f = painter.font()
        f.setPixelSize(22); painter.setFont(f)
        painter.drawText(self.btn_zoom_in, Qt.AlignCenter, "+")
        painter.drawText(self.btn_zoom_out, Qt.AlignCenter, "-")
        painter.setPen(QColor("#FFFFFF")); f.setPixelSize(10); painter.setFont(f)
        painter.drawText(20, 20, f"{self.title} | Zoom: {self.candle_width:.2f}px")

    def _draw_price_scale_and_grid(self, painter, min_p, max_p, 
                                   chart_h, top_m, chart_w):
        if max_p == min_p: return
        s_rect = QRect(chart_w, 0, self.price_scale_width, self.height())
        painter.fillRect(s_rect, QColor("#1e1e1e"))
        painter.setPen(QPen(QColor("#444444"), 1))
        painter.drawLine(chart_w, 0, chart_w, self.height())
        r_step = (max_p - min_p) / 15
        mag = 10**math.floor(math.log10(abs(r_step))) if r_step != 0 else 1
        res = abs(r_step / mag)
        if res < 1.5: step = 1 * mag
        elif res < 3: step = 2 * mag
        elif res < 7: step = 5 * mag
        else: step = 10 * mag
        start_p = math.ceil(min_p / step) * step
        prec = max(0, -math.floor(math.log10(step))) if step < 1 else 0
        fmt = "{:." + str(prec) + "f}"; curr_p = start_p
        while curr_p <= max_p:
            y = chart_h - ((curr_p - min_p)/(max_p-min_p)*chart_h) + top_m
            if 0 <= y <= self.height():
                painter.setPen(QPen(QColor(255, 255, 255, 30), 1))
                painter.drawLine(0, int(y), chart_w, int(y))
                painter.setPen(QColor("#CCCCCC"))
                painter.drawText(chart_w + 5, int(y + 5), fmt.format(curr_p))
            curr_p += step
            if step <= 0: break

