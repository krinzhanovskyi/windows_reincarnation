from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QStyle
from PyQt6.QtGui import QAction

class AppTrayIcon(QSystemTrayIcon):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.is_paused = False
        
        icon = self.app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.setIcon(icon)
        self.setToolTip("Project Reincarnation")

        self.menu = QMenu()

        self.pause_action = QAction("Пауза", self.menu)
        self.pause_action.triggered.connect(self.toggle_pause)
        self.menu.addAction(self.pause_action)

        self.menu.addSeparator()

        self.exit_action = QAction("Выход", self.menu)
        self.exit_action.triggered.connect(self.app.quit)
        self.menu.addAction(self.exit_action)

        self.setContextMenu(self.menu)

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_action.setText("Возобновить")
            self.setToolTip("Project Reincarnation (Пауза)")
        else:
            self.pause_action.setText("Пауза")
            self.setToolTip("Project Reincarnation")