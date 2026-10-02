from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from config import WINDOW_WIDTH, WINDOW_HEIGHT

class PocketWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        flags = (
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool | 
            Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)

        self.setStyleSheet("""
            QWidget {
                background-color: rgba(30, 30, 30, 230);
                border-radius: 15px;
                border: 1px solid #555;
            }
        """)

        layout = QVBoxLayout()
        # Имя папки будет писаться сюда
        self.label = QLabel("", self)
        self.label.setStyleSheet("color: white; font-size: 14px; background: transparent; border: none;")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.label)
        self.setLayout(layout)

    def show_at(self, x, y):
        # Изначально пробуем открыться справа-снизу от курсора
        target_x = x + 20
        target_y = y + 20
        
        # Получаем рабочую область текущего экрана (без учета панели задач)
        screen_geo = self.screen().availableGeometry()
        
        # Если окно вылезает за правый край — сдвигаем его влево от курсора
        if target_x + self.width() > screen_geo.right():
            target_x = x - self.width() - 10
            
        # Если окно вылезает за нижний край — сдвигаем его вверх от курсора
        if target_y + self.height() > screen_geo.bottom():
            target_y = y - self.height() - 10
            
        self.move(int(target_x), int(target_y))
        self.show()

    def hide_window(self):
        self.hide()