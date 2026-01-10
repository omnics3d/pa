import os
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QInputDialog
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QWheelEvent, QMouseEvent
from PySide6.QtCore import Qt, QPoint, Slot
from core.logger_v2026 import get_logger
from utils.menu_manager import MenuManager
from core.data_loader import DataLoader

try:
    from core.exchange_manager import ExchangeDataManager
except ImportError:
    ExchangeDataManager = None

class CandlestickChart(QWidget):
    def __init__(self, data, title="Chart", candle_width_px=4):
        super().__init__()
        self.data = data
        self.title = title
        self.candle_width = candle_width_px
        
        # Переменные для прокрутки (скроллинга)
        self.scroll_offset = 0  
        self.last_mouse_pos = QPoint()
        self.is_dragging = False

        self.setMouseTracking(True)

    def mousePressEvent(self, event: QMouseEvent):
        """Начало прокрутки одним пальцем"""
        if event.button() == Qt.LeftButton:
            self.last_mouse_pos = event.pos()
            self.is_dragging = True

    def mouseReleaseEvent(self, event: QMouseEvent):
        """Конец прокрутки одним пальцем"""
        if event.button() == Qt.LeftButton:
            self.is_dragging = False

    def mouseMoveEvent(self, event: QMouseEvent):
        """Прокрутка графика одним пальцем или мышью"""
        if self.is_dragging and self.data:
            delta_x = event.pos().x() - self.last_mouse_pos.x()
            
            # Рассчитываем сдвиг в количестве свечей
            candles_delta = delta_x / (self.candle_width + 1)
            
            if abs(candles_delta) >= 1:
                old_offset = self.scroll_offset
                # Инвертируем: тянем вправо -> идем назад в историю (offset увеличивается)
                self.scroll_offset -= int(candles_delta)
                
                # Ограничение прокрутки, чтобы не уйти за пределы списка данных
                self.scroll_offset = max(0, min(self.scroll_offset, len(self.data) - 5))
                
                if old_offset != self.scroll_offset:
                    self.last_mouse_pos = event.pos()
                    self.update()

    def wheelEvent(self, event: QWheelEvent):
        """
        Обработка жестов 2 пальцами:
        Вертикально (angleDelta.y) -> Масштабирование (Zoom)
        Горизонтально (angleDelta.x) -> Прокрутка (Scroll)
        """
        angle_y = event.angleDelta().y()
        angle_x = event.angleDelta().x()

        # 1. Масштабирование (Зум)
        if angle_y != 0:
            old_w = self.candle_width
            step = 1 if self.candle_width < 20 else 2
            if angle_y > 0:
                self.candle_width = min(150, self.candle_width + step)
            else:
                self.candle_width = max(1, self.candle_width - step)
            
            if old_w != self.candle_width:
                # Пытаемся обновить глобальный зум в MainWindow для будущих загрузок
                try:
                    self.parentWidget().parent().zoom_level_px = self.candle_width
                except: pass
                self.update()

        # 2. Прокрутка двумя пальцами по горизонтали
        elif angle_x != 0:
            scroll_step = 3 # Скорость прокрутки
            old_offset = self.scroll_offset
            self.scroll_offset -= (angle_x // abs(angle_x)) * scroll_step
            self.scroll_offset = max(0, min(self.scroll_offset, len(self.data) - 5))
            if old_offset != self.scroll_offset:
                self.update()

    def paintEvent(self, event):
        """Отрисовка графика свечей"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#121212"))
        
        if not self.data:
            painter.setPen(QColor("#FFFFFF"))
            painter.drawText(self.rect(), Qt.AlignCenter, "No Data")
            return

        # Срез данных для отображения с учетом прокрутки (от новых к старым)
        visible_list = list(reversed(self.data))[self.scroll_offset:]
        if not visible_list: return

        # Автомасштаб цены: считаем Min/Max только для тех свечей, что влезают в ширину окна
        num_on_screen = self.width() // (self.candle_width + 1)
        on_screen_data = visible_list[:num_on_screen]
        if not on_screen_data: on_screen_data = visible_list

        max_p = max(c['h'] for c in on_screen_data)
        min_p = min(c['l'] for c in on_screen_data)
        diff = max_p - min_p if max_p != min_p else 1
        
        h = self.height() - 60
        w = self.width() - 20
        spacing = 1

        for i, c in enumerate(visible_list):
            # Рассчитываем X координату (новые справа, старые слева)
            x = w - (i * (self.candle_width + spacing)) - 10
            if x < -self.candle_width: break # Оптимизация: не рисуем то, что за левым краем
            
            y_o = h - ((c['o'] - min_p) / diff) * h + 30
            y_c = h - ((c['c'] - min_p) / diff) * h + 30
            y_h = h - ((c['h'] - min_p) / diff) * h + 30
            y_l = h - ((c['l'] - min_p) / diff) * h + 30

            color = QColor("#00FF00") if c['c'] >= c['o'] else QColor("#FF0000")
            painter.setPen(QPen(color, 1))
            painter.setBrush(QBrush(color))
            
            painter.drawLine(x + self.candle_width//2, y_h, x + self.candle_width//2, y_l)
            painter.drawRect(x, min(y_o, y_c), self.candle_width, max(1, abs(y_o - y_c)))

        # Вывод информации в углу
        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(20, 20, f"{self.title} | Offs: {self.scroll_offset} | Zoom: {self.candle_width}px")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.log = get_logger("GUI_2026")
        self.setWindowTitle("Termux FinChart 2026")
        self.resize(1000, 700)
        
        self.current_tf = 1 
        self.current_tool = None 
        self.zoom_level_px = 4 
        self.all_candles = []
        self.loader = None

        # Определение путей
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        xml_path = os.path.join(base_dir, "storage", "state", "exchanges_config.xml")
        
        # Инициализация менеджера конфигурации
        self.manager = ExchangeDataManager(xml_path) if ExchangeDataManager and os.path.exists(xml_path) else None
        
        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.layout = QVBoxLayout(self.central)
        self.menu_controller = MenuManager(self)
        self.menu_controller.setup_ui()

    def show_default_chart(self):
        """Очистка экрана и показ приветствия"""
        self.clear_layout()
        self.layout.addWidget(CandlestickChart([], "Welcome Screen"))

    def on_tool_selected(self, e, m, t):
        """Срабатывает при выборе торговой пары в меню"""
        self.current_tool = (e, m, t)
        path = self.manager.get_tool_data_path(e, m, t)
        s_date = self.manager.get_start_date_for_tool(e, m, t)
        e_date = self.manager.get_end_date_for_tool(e, m, t)
        
        if all([path, s_date, e_date]):
            # Рассчитываем лимит: сколько влезет в окно + запас 1500 для скроллинга
            win_w = self.central.width() if self.central.width() > 100 else 1000
            visible_count = win_w // self.zoom_level_px
            limit = visible_count + 1500 
            
            self.loader = DataLoader(path, t)
            # Загружаем свечи (с конца, через DataLoader)
            self.all_candles = self.loader.get_candles(s_date, e_date, timeframe_min=self.current_tf, limit=limit)
            self._update_chart()

    def _update_chart(self):
        """Перерисовка виджета графика"""
        self.clear_layout()
        title = f"{self.current_tool[0]} > {self.current_tool[2]}" if self.current_tool else "Chart"
        chart = CandlestickChart(self.all_candles, title, self.zoom_level_px)
        self.layout.addWidget(chart)

    def custom_tf_multiplier(self, base_minutes: int, label: str):
        """Выбор множителя таймфрейма (минуты, часы, дни)"""
        val, ok = QInputDialog.getInt(self, "Timeframe", f"Enter multiplier for {label}:", 1, 1, 100000)
        if ok:
            self.current_tf = base_minutes * val
            if self.current_tool: self.on_tool_selected(*self.current_tool)

    def clear_layout(self):
        """Удаление старых виджетов из компоновщика"""
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()

