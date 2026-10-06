import ctypes
import logging
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QPoint
from PyQt6.QtGui import QCursor
from backend.win_api import get_folder_under_cursor, FolderHit
from backend.config_manager import config

log = logging.getLogger("reincarnation")

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

def get_physical_cursor_pos() -> tuple[int, int]:
    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y

class MouseTracker(QObject):
    hover = pyqtSignal(FolderHit, QPoint)

    def __init__(self):
        super().__init__()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_cursor)
        self.last_hit = None
        self.hover_time = 0.0
        self.check_interval = 50
        
        self.last_physical_pos = (-1, -1)

    def start(self):
        self.timer.start(self.check_interval)
        log.info("Mouse tracker started with physical DPI awareness.")

    def stop(self):
        self.timer.stop()
        log.info("Mouse tracker stopped.")

    def check_cursor(self):
        physical_x, physical_y = get_physical_cursor_pos()
        current_pos = (physical_x, physical_y)
        
        if current_pos != self.last_physical_pos:
            self.last_physical_pos = current_pos
            self.hover_time = 0.0
            self.last_hit = None
            return
            
        self.hover_time += self.check_interval / 1000.0
        
        if self.hover_time >= config.hover_delay:
            hit = get_folder_under_cursor(physical_x, physical_y)
            
            if hit and hit != self.last_hit:
                self.last_hit = hit
                
                logical_pos = QCursor.pos()
                self.hover.emit(hit, logical_pos)