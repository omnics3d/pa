import os
from datetime import datetime
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QInputDialog
from core.logger_v2026 import get_logger
from .menu_manager import MenuManager
from core.data_loader import DataLoader
from view.chart_widget import CandlestickChart

try:
    from core.exchange_manager import ExchangeDataManager
except ImportError:
    ExchangeDataManager = None


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

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        xml_path = os.path.join(base_dir, "storage", "state", "exchanges_config.xml")
        self.manager = (
            ExchangeDataManager(xml_path)
            if ExchangeDataManager and os.path.exists(xml_path)
            else None
        )

        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.layout = QVBoxLayout(self.central)
        self.menu_controller = MenuManager(self)
        self.menu_controller.setup_ui()

    def show_default_chart(self):
        self.clear_layout()
        self.layout.addWidget(CandlestickChart([], "Welcome Screen"))

    def on_tool_selected(self, e, m, t):
        self.current_tool = (e, m, t)
        path = self.manager.get_tool_data_path(e, m, t)
        s_date = self.manager.get_start_date_for_tool(e, m, t)
        e_date = self.manager.get_end_date_for_tool(e, m, t)

        if all([path, s_date, e_date]):
            win_w = max(self.central.width(), 1000)
            limit = (win_w // self.zoom_level_px) + 1500
            self.loader = DataLoader(path, t)
            self.all_candles = self.loader.get_candles(
                s_date, e_date, timeframe_min=self.current_tf, limit=limit
            )
            self._update_chart()

    def _update_chart(self):
        self.clear_layout()
        title = (
            f"{self.current_tool} > {self.current_tool}"
            if self.current_tool
            else "Chart"
        )
        chart = CandlestickChart(self.all_candles, title, self.zoom_level_px)
        chart.need_more_data.connect(self.load_more_history)
        self.layout.addWidget(chart)

    def load_more_history(self):
        """Дозагрузка истории при скроллинге влево"""
        if not self.current_tool or not self.all_candles or not self.loader:
            return
        e, m, t = self.current_tool
        path = self.manager.get_tool_data_path(e, m, t)
        s_date = self.manager.get_start_date_for_tool(e, m, t)

        # Используем дату из последней обработанной точки DataLoader'а
        offset_dt = datetime.fromtimestamp(self.loader._last_ts)

        new_data = self.loader.get_candles(
            s_date, "", timeframe_min=self.current_tf, limit=1000, offset_date=offset_dt
        )
        if new_data:
            added_count = len(new_data)
            self.all_candles = new_data + self.all_candles
            chart = self.layout.itemAt(0).widget()
            if isinstance(chart, CandlestickChart):
                chart.data = self.all_candles
                chart.scroll_offset += added_count
                chart._update_scroll_range()
                chart.update()

    def custom_tf_multiplier(self, base_minutes: int, label: str):
        val, ok = QInputDialog.getInt(
            self, "Timeframe", f"Enter multiplier for {label}:", 1, 1, 100000
        )
        if ok:
            self.current_tf = base_minutes * val
            if self.current_tool:
                self.on_tool_selected(*self.current_tool)

    def clear_layout(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
