import sys
import winreg
import logging
from pathlib import Path

log = logging.getLogger("reincarnation")
APP_NAME = "ProjectReincarnation"

def get_run_command() -> str:
    if getattr(sys, 'frozen', False):
        return f'"{sys.executable}"'
    else:
        script_path = Path(sys.argv[0]).absolute()
        pythonw = Path(sys.executable).parent / "pythonw.exe"
        
        if pythonw.exists():
            return f'"{pythonw}" "{script_path}"'
        return f'"{sys.executable}" "{script_path}"'

def set_startup(enable: bool) -> None:
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
        if enable:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, get_run_command())
            log.info("Added to Windows startup.")
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
                log.info("Removed from Windows startup.")
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
    except Exception as e:
        log.error(f"Failed to modify startup registry: {e}")