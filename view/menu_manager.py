from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import QMenu # Добавлен импорт QMenu для читаемости типов

class MenuManager:
    def __init__(self, main_window):
        self.win = main_window
        self.bar = main_window.menuBar()
        
        # Установка системного жирного шрифта (размер 16pt)
        self.menu_font = QFont()
        self.menu_font.setPointSize(16)
        self.menu_font.setBold(True)
        self.bar.setFont(self.menu_font)

    def setup_ui(self):
        # 1. Options
        opt = self.bar.addMenu("Options")
        opt.setFont(self.menu_font)
        exit_act = QAction("Exit", self.win)
        exit_act.triggered.connect(self.win.close)
        opt.addAction(exit_act)
        
        # 2. Graph
        graph_menu = self.bar.addMenu("Graph")
        graph_menu.setFont(self.menu_font)
        
        # Подменю Tool в разделе Graph для динамических пунктов
        graph_tool_menu = graph_menu.addMenu("Tool")
        graph_tool_menu.setFont(self.menu_font)
        
        # Перенос Timeframe в меню Graph (нижним пунктом) с подпунктами
        tf_menu = graph_menu.addMenu("Timeframe")
        tf_menu.setFont(self.menu_font)
        
        # Пункт Other (используем логику минут как базовую)
        other_act = QAction("Other", self.win)
        other_act.triggered.connect(
            lambda: self.win.custom_tf_multiplier(1, "Minutes")
        )
        tf_menu.addAction(other_act)
        
        tf_menu.addSeparator()
        
        # Блок минут
        for t, m, u in [("1min", 1, "Minutes"), ("5 min", 5, "Minutes"),
                        ("15 min", 15, "Minutes"), ("30 min", 30, "Minutes")]:
            act = QAction(t, self.win)
            act.triggered.connect(lambda c=False, mm=m, uu=u: 
                                  self.win.custom_tf_multiplier(mm, uu))
            tf_menu.addAction(act)
        
        tf_menu.addSeparator()
        
        # Блок часов
        for t, m, u in [("1 hour", 60, "Hours"), ("2 hour", 120, "Hours"),
                        ("3 hour", 180, "Hours"), ("4 hour", 240, "Hours")]:
            act = QAction(t, self.win)
            act.triggered.connect(lambda c=False, mm=m, uu=u: 
                                  self.win.custom_tf_multiplier(mm, uu))
            tf_menu.addAction(act)
            
        tf_menu.addSeparator()
        
        # Блок дней/недель
        for t, m, u in [("1 day", 1440, "Days"), ("1 week", 10080, "Days")]:
            act = QAction(t, self.win)
            act.triggered.connect(lambda c=False, mm=m, uu=u: 
                                  self.win.custom_tf_multiplier(mm, uu))
            tf_menu.addAction(act)
        
        # 3. Settings
        self.win.settings_menu = self.bar.addMenu("Settings")
        self.win.settings_menu.setFont(self.menu_font)
        
        # !!! ИСПРАВЛЕНИЕ !!!
        if self.win.manager:
            self._build_dynamic_menu(graph_tool_menu)

    def _build_dynamic_menu(self, menu: QMenu): # Указываем тип QMenu
        for ex in self.win.manager.get_exchange_names():
            # Здесь ex_m - это подменю внутри menu (Graph -> Tool)
            ex_m = menu.addMenu(ex) 
            ex_m.setFont(self.menu_font)
            for mk in self.win.manager.get_markets_for_exchange(ex) or []:
                mk_m = ex_m.addMenu(mk)
                mk_m.setFont(self.menu_font)
                for tl in self.win.manager.get_tools_for_market(ex, mk) or []:
                    act = QAction(tl, self.win)
                    act.setFont(self.menu_font)
                    act.triggered.connect(
                        lambda chk=False, e=ex, m=mk, t=tl: 
                        self.win.on_tool_selected(e, m, t)
                    )
                    mk_m.addAction(act)

