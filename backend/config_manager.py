import json
import os
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal

class _ConfigManager(QObject):
    updated = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.config_dir = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "ProjectReincarnation"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "settings.json"
        
        self.data = {
            "hover_delay": 0.5,
            "max_files": 15,
            "window_width": 300,
            "window_height": 400,
            "theme": "system",
            "show_sizes": True 
        }
        self.load()

    def load(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self.data.update(json.load(f))
            except Exception:
                pass

    def save(self):
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4)
            self.updated.emit()
        except Exception:
            pass

    @property
    def hover_delay(self): return self.data.get("hover_delay", 0.5)
    
    @property
    def max_files(self): return self.data.get("max_files", 15)
    
    @property
    def window_width(self): return self.data.get("window_width", 300)
    
    @property
    def window_height(self): return self.data.get("window_height", 400)

    @property
    def theme(self): return self.data.get("theme", "dark")

    @property
    def show_sizes(self): return self.data.get("show_sizes", True)

    def update_settings(self, max_files, hover_delay, theme, show_sizes):
        self.data["max_files"] = max_files
        self.data["hover_delay"] = hover_delay
        self.data["theme"] = theme
        self.data["show_sizes"] = show_sizes
        self.save()

config = _ConfigManager()