from __future__ import annotations

import logging
import time

from PyQt6.QtCore import QObject, QPoint, QThread, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QCursor

from backend.win_api import (
    FolderHit,
    get_desktop_folder_under_cursor,
    get_physical_cursor_pos,
    uia_thread_initializer,
)
from backend.config_manager import config

log = logging.getLogger(__name__)
POLL_INTERVAL_MS = 50
SLOW_PROBE_THRESHOLD_S = 0.2
THREAD_STOP_TIMEOUT_MS = 2000


class HitTestWorker(QObject):
    result_ready = pyqtSignal(int, object)

    def __init__(self) -> None:
        super().__init__()
        self._uia_init: object | None = None

    @pyqtSlot()
    def init_in_thread(self) -> None:
        self._uia_init = uia_thread_initializer()
        log.info("UIA initialized in worker thread")

    @pyqtSlot(int, int, int)
    def probe(self, request_id: int, x: int, y: int) -> None:
        started = time.perf_counter()
        hit = get_desktop_folder_under_cursor(x, y)
        elapsed = time.perf_counter() - started

        if elapsed > SLOW_PROBE_THRESHOLD_S:
            log.warning("Slow UIA hit-test: %.0f ms at (%d, %d)", elapsed * 1000, x, y)
        else:
            log.debug("Hit-test %.1f ms at (%d, %d) -> %s", elapsed * 1000, x, y, hit)

        self.result_ready.emit(request_id, hit)

    @pyqtSlot()
    def shutdown_in_thread(self) -> None:
        self._uia_init = None
        log.info("UIA released in worker thread")


class MouseTracker(QObject):

    hover = pyqtSignal(object, QPoint)
    moved = pyqtSignal()
    _probe_requested = pyqtSignal(int, int, int)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

        self._last_pos: tuple[int, int] | None = None
        self._last_move_at = time.monotonic()
        self._hover_fired = False
        self._hover_logical_pos = QPoint()

        self._request_id = 0
        self._in_flight = False
        self._pending: tuple[int, int, int] | None = None

        self._timer = QTimer(self)
        self._timer.setInterval(POLL_INTERVAL_MS)
        self._timer.timeout.connect(self._check_mouse)

        self._thread = QThread()
        self._thread.setObjectName("uia-hit-test")

        self._worker = HitTestWorker()
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.init_in_thread)
        self._thread.finished.connect(self._worker.shutdown_in_thread)
        self._thread.finished.connect(self._worker.deleteLater)

        self._probe_requested.connect(self._worker.probe)
        self._worker.result_ready.connect(self._on_probe_result)

    def start(self) -> None:

        self._thread.start()
        self._last_move_at = time.monotonic()
        self._timer.start()
        log.info("MouseTracker started (poll=%d ms, hover_delay=%.2f s)",
                 POLL_INTERVAL_MS, config.hover_delay)

    def stop(self) -> None:
        self._timer.stop()
        self._thread.quit()
        if not self._thread.wait(THREAD_STOP_TIMEOUT_MS):
            log.error("UIA worker did not stop in %d ms (Explorer hung?)",
                      THREAD_STOP_TIMEOUT_MS)
        else:
            log.info("MouseTracker stopped")

    @pyqtSlot()
    def _check_mouse(self) -> None:
        pos = get_physical_cursor_pos()
        if pos is None:
            return  

        now = time.monotonic()

        if pos != self._last_pos:
            self._last_pos = pos
            self._last_move_at = now
            self._request_id += 1 
            self._pending = None  

            if self._hover_fired:
                self._hover_fired = False
                self.moved.emit()
            return

        if self._hover_fired or (now - self._last_move_at) < config.hover_delay:
            return

        self._hover_fired = True
        self._hover_logical_pos = QCursor.pos()
        self._request_probe(self._request_id, *pos)

    def _request_probe(self, request_id: int, x: int, y: int) -> None:
        if self._in_flight:
            self._pending = (request_id, x, y)
            return
        self._in_flight = True
        self._probe_requested.emit(request_id, x, y)

    @pyqtSlot(int, object)
    def _on_probe_result(self, request_id: int, hit: FolderHit | None) -> None:
        self._in_flight = False

        if self._pending is not None:
            pending, self._pending = self._pending, None
            self._request_probe(*pending)

        if request_id != self._request_id:
            log.debug("Dropped stale hit-test result #%d (current #%d)",
                      request_id, self._request_id)
            return

        if hit is not None:
            log.info("Folder under cursor: %s", hit.path)
            self.hover.emit(hit, self._hover_logical_pos)
