import ctypes
import time
import logging
from PyQt6.QtCore import QThread, pyqtSignal, QPoint
from PyQt6.QtGui import QCursor
from backend.win_api import get_folder_under_cursor, FolderHit
from backend.config_manager import config

log = logging.getLogger("reincarnation")

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

def get_physical_cursor_pos() -> tuple[int, int]:
    """Bypasses UI scaling to get absolute physical pixels for Windows API."""
    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y

class MouseTracker(QThread):
    hover = pyqtSignal(FolderHit, QPoint)

    def __init__(self):
        super().__init__()
        self._is_running = False
        self.last_hit = None
        self.hover_time = 0.0
        self.check_interval = 0.05  
        self.last_physical_pos = (-1, -1)

    def run(self):
        self._is_running = True
        log.info("Mouse tracker thread started with physical DPI awareness.")
        
        while self._is_running:
            time.sleep(self.check_interval)
            
            physical_x, physical_y = get_physical_cursor_pos()
            current_pos = (physical_x, physical_y)
            
            if current_pos != self.last_physical_pos:
                self.last_physical_pos = current_pos
                self.hover_time = 0.0
                self.last_hit = None
                continue
                
            self.hover_time += self.check_interval
            
            if self.hover_time >= config.hover_delay:
                hit = get_folder_under_cursor(physical_x, physical_y)
                
                if hit and hit != self.last_hit:
                    self.last_hit = hit

                    logical_pos = QCursor.pos()
                    self.hover.emit(hit, logical_pos)

    def stop(self):
        self._is_running = False
        self.wait() 
        log.info("Mouse tracker thread stopped.")