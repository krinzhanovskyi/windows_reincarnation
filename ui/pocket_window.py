import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QCursor
from config import WINDOW_WIDTH, WINDOW_HEIGHT

class PocketWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.trigger_pos = None
        self.init_ui()
        
        self.mouse_timer = QTimer(self)
        self.mouse_timer.timeout.connect(self.check_mouse_leave)
        self.mouse_timer.start(50)

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
            QListWidget {
                background: transparent;
                border: none;
                color: white;
                font-size: 14px;
                outline: 0;
            }
            QListWidget::item {
                padding: 4px;
                border-radius: 5px;
            }
            QListWidget::item:hover {
                background-color: rgba(255, 255, 255, 30);
            }
        """)

        layout = QVBoxLayout()
        self.list_widget = QListWidget(self)
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

    def show_at(self, x, y):
        self.trigger_pos = QPoint(x, y)
        
        target_x = x + 5
        target_y = y + 5
        
        screen_geo = self.screen().availableGeometry()
        
        if target_x + self.width() > screen_geo.right():
            target_x = x - self.width() - 5
            
        if target_y + self.height() > screen_geo.bottom():
            target_y = y - self.height() - 5
            
        self.move(int(target_x), int(target_y))
        self.show()

    def check_mouse_leave(self):
        if not self.isVisible() or not self.trigger_pos:
            return

        pos = QCursor.pos()

        if self.geometry().contains(pos):
            return

        dist_x = abs(pos.x() - self.trigger_pos.x())
        dist_y = abs(pos.y() - self.trigger_pos.y())
        
        if dist_x < 60 and dist_y < 60:
            return

        self.hide_window()

    def hide_window(self):
        self.hide()

    def set_data(self, folder_name, files):
        self.list_widget.clear()
        
        header_item = QListWidgetItem(f"📁 {folder_name}")
        header_item.setFlags(Qt.ItemFlag.NoItemFlags)
        self.list_widget.addItem(header_item)
        
        separator = QListWidgetItem("─" * 25)
        separator.setFlags(Qt.ItemFlag.NoItemFlags)
        self.list_widget.addItem(separator)
        
        if not files:
            empty_item = QListWidgetItem("Папка пуста")
            empty_item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_widget.addItem(empty_item)
        else:
            for f in files:
                icon = "📂" if f['is_dir'] else "📄"
                name = f['name'] if len(f['name']) < 25 else f['name'][:22] + "..."
                
                item = QListWidgetItem(f"{icon} {name}")
                item.setData(Qt.ItemDataRole.UserRole, f['path'])
                self.list_widget.addItem(item)

    def on_item_clicked(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            try:
                os.startfile(path)
                self.hide_window()
            except Exception:
                pass