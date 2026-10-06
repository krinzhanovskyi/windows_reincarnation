import os
import winreg
import logging
import uiautomation as auto
from dataclasses import dataclass

log = logging.getLogger("reincarnation")

@dataclass
class FolderHit:
    name: str
    path: str

def get_real_desktop_path() -> str:
    """Safely retrieves the actual Desktop path from Windows Registry (handles OneDrive/Localization)."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, 
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
        )
        path, _ = winreg.QueryValueEx(key, "Desktop")
        winreg.CloseKey(key)
        
        return os.path.expandvars(path)
    except Exception as e:
        log.warning("Failed to read Desktop path from registry: %s. Using fallback.", e)
        return os.path.join(os.path.expanduser("~"), "Desktop")

def is_desktop_element(control) -> bool:
    try:
        top_level_window = control.GetTopLevelControl()
        class_name = top_level_window.ClassName

        return class_name in ("Progman", "WorkerW")
    except Exception:
        return False

def get_folder_under_cursor(physical_x: int, physical_y: int) -> FolderHit | None:
    try:

        control = auto.ControlFromPoint(physical_x, physical_y)

        if control.ControlType != auto.ControlType.ListItemControl:
            return None
            
        if not is_desktop_element(control):
            return None
            
        name = control.Name
        if not name:
            return None
            
        desktop_path = get_real_desktop_path()
        folder_path = os.path.join(desktop_path, name)
        
        if os.path.isdir(folder_path):
            return FolderHit(name=name, path=folder_path)
            
    except Exception:
        pass
        
    return None