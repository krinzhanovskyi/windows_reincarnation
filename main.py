"""
Точка входа Project Reincarnation.
"""

from __future__ import annotations

import logging
import os
import signal
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from PyQt6.QtCore import QPoint
from PyQt6.QtWidgets import QApplication

log = logging.getLogger("reincarnation")

def setup_logging() -> Path:
    """Логирование в %LOCALAPPDATA%\\ProjectReincarnation\\logs\\app.log"""
    base = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "ProjectReincarnation" / "logs"
    base.mkdir(parents=True, exist_ok=True)
    log_file = base / "app.log"

    fmt = logging.Formatter("%(asctime)s %(levelname)-7s [%(threadName)s] %(name)s: %(message)s")

    file_handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG if os.environ.get("REINCARNATION_DEBUG") else logging.INFO)
    root.addHandler(file_handler)

    if sys.stderr is not None:
        console = logging.StreamHandler()
        console.setFormatter(fmt)
        root.addHandler(console)

    return log_file

def main() -> int:
    log_file = setup_logging()
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    from backend.mouse_tracker import MouseTracker
    from backend.win_api import FolderHit
    from ui.pocket_window import PocketWindow
    from backend.file_reader import get_folder_contents

    pocket = PocketWindow()
    tracker = MouseTracker()

    def on_hover(hit: FolderHit, logical_pos: QPoint) -> None:
        files = get_folder_contents(hit.path, max_items=20)
        pocket.set_data(hit.name, files)
        pocket.show_at(logical_pos.x(), logical_pos.y())

    tracker.hover.connect(on_hover)
    #tracker.moved.connect(pocket.hide_window)
    app.aboutToQuit.connect(tracker.stop)

    log.info("Project Reincarnation started, log: %s", log_file)
    tracker.start()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())