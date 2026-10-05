import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QListWidget, QListWidgetItem, 
                             QFileIconProvider, QStyleOption, QStyle, QStyledItemDelegate)
from PyQt6.QtCore import Qt, QTimer, QPoint, QFileInfo, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QCursor, QPainter, QColor
from backend.config_manager import config
from backend.icon_extractor import get_file_icon
from ui.styles import get_pocket_style

def format_bytes(size: int) -> str:
    if size == 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}".replace('.0', '')
        size /= 1024.0
    return f"{size:.1f} TB"

class FileItemDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        
        size_str = index.data(Qt.ItemDataRole.UserRole + 1)
        if size_str:
            painter.save()
            font = painter.font()
            
            if font.pointSize() > 0:
                font.setPointSize(max(1, font.pointSize() - 2))
            elif font.pixelSize() > 0:
                font.setPixelSize(max(1, font.pixelSize() - 2))
                
            painter.setFont(font)
            painter.setPen(QColor("#888888"))
            
            rect = option.rect
            rect.setRight(rect.right() - 8)
            painter.drawText(rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, size_str)
            painter.restore()


class PocketWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.trigger_pos = None
        self._is_fading_out = False
        self.current_path = None 
        self.init_ui()
        
        self.mouse_timer = QTimer(self)
        self.mouse_timer.timeout.connect(self.check_mouse_leave)
        self.mouse_timer.start(50)
        
        config.updated.connect(self.update_theme)

    def init_ui(self):
        flags = (
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool | 
            Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("PocketWindow")
        
        self.setFixedWidth(config.window_width)
        self.update_theme()

        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(150)
        self.fade_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.fade_anim.finished.connect(self._on_fade_finished)

        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        self.list_widget = QListWidget(self)
        self.list_widget.setIconSize(QSize(18, 18))
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        
        self.list_widget.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.list_widget.setItemDelegate(FileItemDelegate(self))
        
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

    def update_theme(self):
        self.setStyleSheet(get_pocket_style(config.theme))

    def paintEvent(self, event):
        opt = QStyleOption()
        opt.initFrom(self)
        p = QPainter(self)
        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_Widget, opt, p, self)

    def wheelEvent(self, event):
        scrollbar = self.list_widget.verticalScrollBar()
        delta = event.angleDelta().y()
        if delta != 0:
            step = int(-delta / 120) * 40
            scrollbar.setValue(scrollbar.value() + step)
        event.accept()

    def show_at(self, x, y):
        self.setFixedWidth(config.window_width)
        self.trigger_pos = QPoint(x, y)
        
        target_x = x + 15
        target_y = y + 15
        
        screen_geo = self.screen().availableGeometry()
        
        if target_x + self.width() > screen_geo.right():
            target_x = x - self.width() - 15
            
        if target_y + self.height() > screen_geo.bottom():
            target_y = y - self.height() - 15
            
        self.move(int(target_x), int(target_y))
        
        if not self.isVisible():
            self.setWindowOpacity(0.0)
            self.show()

        self._is_fading_out = False
        self.fade_anim.stop()
        self.fade_anim.setStartValue(self.windowOpacity())
        self.fade_anim.setEndValue(1.0)
        self.fade_anim.start()

    def check_mouse_leave(self):
        if not self.isVisible() or not self.trigger_pos or self._is_fading_out:
            return

        pos = QCursor.pos()
        if self.geometry().contains(pos):
            return

        dist_x = abs(pos.x() - self.trigger_pos.x())
        dist_y = abs(pos.y() - self.trigger_pos.y())

        if dist_x < 100 and dist_y < 100:
            return

        self.hide_window()

    def hide_window(self):
        if not self.isVisible() or self._is_fading_out:
            return

        self._is_fading_out = True
        self.fade_anim.stop()
        self.fade_anim.setStartValue(self.windowOpacity())
        self.fade_anim.setEndValue(0.0)
        self.fade_anim.start()

    def _on_fade_finished(self):
        if self._is_fading_out:
            self.hide()
            self._is_fading_out = False

    def set_data(self, folder_name, files, folder_path=""):
        self.current_path = folder_path
        self.list_widget.clear()
        provider = QFileIconProvider()
        
        header_item = QListWidgetItem(f"{folder_name}")
        header_item.setFlags(Qt.ItemFlag.NoItemFlags)
        
        font = header_item.font()
        font.setBold(True)
        header_item.setFont(font)
        
        if files:
            first_file_info = QFileInfo(files[0]['path'])
            parent_dir_info = QFileInfo(first_file_info.absolutePath())
            header_item.setIcon(provider.icon(parent_dir_info))
        else:
            header_item.setIcon(provider.icon(QFileIconProvider.IconType.Folder))
             
        self.list_widget.addItem(header_item)
        
        separator = QListWidgetItem("─" * 25)
        separator.setFlags(Qt.ItemFlag.NoItemFlags)
        separator.setForeground(Qt.GlobalColor.gray)
        self.list_widget.addItem(separator)
        
        if not files:
            empty_item = QListWidgetItem("Folder is empty")
            empty_item.setFlags(Qt.ItemFlag.NoItemFlags)
            empty_item.setForeground(Qt.GlobalColor.gray)
            self.list_widget.addItem(empty_item)
        else:
            for f in files:
                clean_name = os.path.splitext(f['name'])[0]
                
                max_len = 20 if config.show_sizes else 28
                display_name = clean_name if len(clean_name) <= max_len else clean_name[:max_len-3] + "..."
                
                item = QListWidgetItem(display_name)
                
                icon = get_file_icon(f['path'], provider)
                item.setIcon(icon)
                item.setData(Qt.ItemDataRole.UserRole, f['path'])
                
                if config.show_sizes and not f.get('is_dir', False):
                    size_str = format_bytes(f.get('size', 0))
                    item.setData(Qt.ItemDataRole.UserRole + 1, size_str)
                
                self.list_widget.addItem(item)
        
        calculated_height = (self.list_widget.count() * 32) + 25
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