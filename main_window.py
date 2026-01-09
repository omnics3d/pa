from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                             QPushButton, QSplitter, QFrame)
from PySide6.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Flat Structure UI')
        self.resize(360, 640)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        splitter = QSplitter(Qt.Vertical)
        top = QFrame()
        top_lay = QVBoxLayout(top)
        top_lay.addWidget(QPushButton("Кнопка из соседнего файла"))
        
        bottom = QFrame()
        bottom.setStyleSheet("background-color: #333;")
        
        splitter.addWidget(top)
        splitter.addWidget(bottom)
        layout.addWidget(splitter)

