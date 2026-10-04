import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QFileIconProvider
from PyQt6.QtCore import Qt, QTimer, QPoint, QFileInfo, QSize
from PyQt6.QtGui import QCursor
from backend.config_manager import config
from backend.icon_extractor import get_file_icon

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
        
        self.setFixedWidth(config.window_width)

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
            QScrollBar:vertical {
                border: none;
                background: rgba(30, 30, 30, 100);
                width: 6px;
                border-radius: 3px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 80);
                min-height: 20px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 150);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        self.list_widget = QListWidget(self)
        self.list_widget.setIconSize(QSize(16, 16))
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

    def show_at(self, x, y):
        self.setFixedWidth(config.window_width) # Обновляем ширину при показе
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
        
        provider = QFileIconProvider()
        
        header_item = QListWidgetItem(f"{folder_name}")
        header_item.setFlags(Qt.ItemFlag.NoItemFlags)
        
        if files:
            first_file_info = QFileInfo(files[0]['path'])
            parent_dir_info = QFileInfo(first_file_info.absolutePath())
            header_item.setIcon(provider.icon(parent_dir_info))
        else:
            header_item.setIcon(provider.icon(QFileIconProvider.IconType.Folder))
             
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
                name = f['name'] if len(f['name']) < 25 else f['name'][:22] + "..."
                item = QListWidgetItem(name)
                
                icon = get_file_icon(f['path'], provider)
                item.setIcon(icon)
                
                item.setData(Qt.ItemDataRole.UserRole, f['path'])
                self.list_widget.addItem(item)
        
        calculated_height = (self.list_widget.count() * 28) + 25
        final_height = min(calculated_height, config.window_height)
        self.setFixedHeight(final_height)

    def on_item_clicked(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            try:
                os.startfile(path)
                self.hide_window()
            except Exception:
                pass