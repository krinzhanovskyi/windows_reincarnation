import os
import sys
from pathlib import Path
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QStyle
from PyQt6.QtGui import QAction, QIcon
from ui.settings_window import SettingsWindow

class AppTrayIcon(QSystemTrayIcon):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.is_paused = False
        
        self.settings_window = SettingsWindow()
        
        if getattr(sys, 'frozen', False):
            root_dir = sys._MEIPASS
        else:
            root_dir = os.path.dirname(os.path.dirname(__file__))
            
        icon_path = os.path.join(root_dir, 'icon.ico')
        
        if os.path.exists(icon_path):
            self.setIcon(QIcon(icon_path))
        else:
            self.setIcon(self.app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
            
        self.setToolTip("Project Reincarnation")

        self.menu = QMenu()

        self.settings_action = QAction("Settings", self.menu)
        self.settings_action.triggered.connect(self.settings_window.show)
        self.menu.addAction(self.settings_action)

        self.logs_action = QAction("View Logs", self.menu)
        self.logs_action.triggered.connect(self.open_logs)
        self.menu.addAction(self.logs_action)

        self.pause_action = QAction("Pause", self.menu)
        self.pause_action.triggered.connect(self.toggle_pause)
        self.menu.addAction(self.pause_action)

        self.menu.addSeparator()

        self.exit_action = QAction("Exit", self.menu)
        self.exit_action.triggered.connect(self.app.quit)
        self.menu.addAction(self.exit_action)

        self.setContextMenu(self.menu)

        self.show()
        self.showMessage(
            "Folder viewer by reincarnation", 
            "Widget is active. Go over any folder to see its contents.", 
            QSystemTrayIcon.MessageIcon.Information, 
            3000
        )

    def open_logs(self):
        """Opens the log file in the default text editor (Notepad)."""
        log_dir = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "ProjectReincarnation" / "logs"
        log_file = log_dir / "app.log"
        if log_file.exists():
            try:
                os.startfile(str(log_file))
            except Exception:
                pass

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_action.setText("Resume")
            self.setToolTip("Project Reincarnation (Paused)")
        else:
            self.pause_action.setText("Pause")
            self.setToolTip("Project Reincarnation")