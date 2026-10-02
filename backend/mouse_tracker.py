"""
Отслеживание курсора и асинхронный хит-тест папок рабочего стола.

Архитектура:

    GUI-поток                                  Воркер-поток (uia-hit-test)
    ─────────                                  ───────────────────────────
    QTimer 50 мс
      └─ MouseTracker._check_mouse()
           ├─ GetCursorPos (физ. px, дёшево)
           └─ курсор стоит >= HOVER_DELAY
                └─ _probe_requested ──queued──▶ HitTestWorker.probe()
                                                  └─ UIA ControlFromPoint (медленно,
                                                     может блокироваться)
      MouseTracker._on_probe_result() ◀─queued── result_ready
           └─ hover(FolderHit, QPoint логич.)

GUI-поток никогда не ждёт explorer.exe: даже если Explorer завис,
интерфейс продолжает отвечать.
"""

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
from config import HOVER_DELAY

log = logging.getLogger(__name__)

# Период опроса курсора. 50 мс = 20 Гц: незаметно для пользователя
# и практически бесплатно по CPU (GetCursorPos — не межпроцессный вызов).
POLL_INTERVAL_MS = 50

# Порог «медленного» хит-теста. Если UIA отвечает дольше, пишем WARNING:
# это признак проблем с Explorer, полезно видеть в логах.
SLOW_PROBE_THRESHOLD_S = 0.2

# Сколько ждать завершения воркер-потока при остановке.
THREAD_STOP_TIMEOUT_MS = 2000


class HitTestWorker(QObject):
    """
    Выполняет UIA-хит-тест в отдельном потоке.

    Объект перемещается в QThread через moveToThread(), поэтому все его
    слоты, вызванные через сигналы, исполняются в воркер-потоке.
    """

    # (request_id, FolderHit | None). Тип object, т.к. передаём Python-объект.
    result_ready = pyqtSignal(int, object)

    def __init__(self) -> None:
        super().__init__()
        self._uia_init: object | None = None

    @pyqtSlot()
    def init_in_thread(self) -> None:
        """Вызывается по QThread.started, то есть уже внутри воркер-потока."""
        self._uia_init = uia_thread_initializer()
        log.info("UIA initialized in worker thread")

    @pyqtSlot(int, int, int)
    def probe(self, request_id: int, x: int, y: int) -> None:
        """Хит-тест точки (x, y) в физических пикселях."""
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
        """
        Вызывается по QThread.finished. Этот сигнал испускается в самом
        воркер-потоке перед его завершением, поэтому CoUninitialize
        (в деструкторе инициализатора) выполнится в правильном потоке.
        """
        self._uia_init = None
        log.info("UIA released in worker thread")


class MouseTracker(QObject):
    """
    Детектирует «зависание» курсора и запрашивает хит-тест у воркера.

    Сигналы:
        hover(FolderHit, QPoint): курсор задержался над папкой.
                                  QPoint — ЛОГИЧЕСКИЕ координаты для Qt-окон.
        moved():                  курсор сдвинулся после hover (пора прятать окно).
    """

    hover = pyqtSignal(object, QPoint)
    moved = pyqtSignal()

    # Внутренний сигнал для передачи запроса в воркер-поток.
    # Прямой вызов self._worker.probe() выполнился бы в GUI-потоке,
    # а сигнал к объекту из другого потока автоматически идёт через очередь.
    _probe_requested = pyqtSignal(int, int, int)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

        # --- состояние курсора -------------------------------------------
        self._last_pos: tuple[int, int] | None = None
        # monotonic, а не time.time(): системные часы могут прыгнуть (NTP,
        # ручная смена времени), и задержка hover посчиталась бы неверно.
        self._last_move_at = time.monotonic()
        self._hover_fired = False
        self._hover_logical_pos = QPoint()

        # --- состояние запросов ------------------------------------------
        # request_id растёт при каждом движении мыши. Ответ воркера с устаревшим
        # id отбрасывается: мышь уже ушла, показывать окно поздно.
        self._request_id = 0
        # Не больше одного запроса «в полёте». Если Explorer тормозит,
        # запросы не копятся в очереди: храним только самый свежий.
        self._in_flight = False
        self._pending: tuple[int, int, int] | None = None

        # --- таймер опроса (живёт в GUI-потоке) --------------------------
        self._timer = QTimer(self)
        self._timer.setInterval(POLL_INTERVAL_MS)
        self._timer.timeout.connect(self._check_mouse)

        # --- воркер-поток --------------------------------------------------
        # QThread без родителя: его время жизни контролирует stop().
        # С родителем он мог бы уничтожиться при работающем потоке, а это crash.
        self._thread = QThread()
        self._thread.setObjectName("uia-hit-test")

        self._worker = HitTestWorker()
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.init_in_thread)
        self._thread.finished.connect(self._worker.shutdown_in_thread)
        self._thread.finished.connect(self._worker.deleteLater)

        self._probe_requested.connect(self._worker.probe)
        self._worker.result_ready.connect(self._on_probe_result)

    # ------------------------------------------------------------------
    # Публичный API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Запускает воркер-поток и опрос курсора."""
        self._thread.start()
        self._last_move_at = time.monotonic()
        self._timer.start()
        log.info("MouseTracker started (poll=%d ms, hover_delay=%.2f s)",
                 POLL_INTERVAL_MS, HOVER_DELAY)

    def stop(self) -> None:
        """
        Корректная остановка. Вызывать при выходе (QApplication.aboutToQuit).

        Если воркер завис внутри UIA-вызова, ждём ограниченное время и
        НЕ вызываем terminate(): принудительное убийство потока посреди
        COM-вызова может повредить состояние процесса. Процесс всё равно
        завершается, ОС освободит ресурсы.
        """
        self._timer.stop()
        self._thread.quit()
        if not self._thread.wait(THREAD_STOP_TIMEOUT_MS):
            log.error("UIA worker did not stop in %d ms (Explorer hung?)",
                      THREAD_STOP_TIMEOUT_MS)
        else:
            log.info("MouseTracker stopped")

    # ------------------------------------------------------------------
    # Внутренняя логика (GUI-поток)
    # ------------------------------------------------------------------

    @pyqtSlot()
    def _check_mouse(self) -> None:
        # Физические координаты: только они корректны для UIA.
        pos = get_physical_cursor_pos()
        if pos is None:
            return  # secure desktop / экран блокировки: пропускаем тик

        now = time.monotonic()

        if pos != self._last_pos:
            # Курсор сдвинулся.
            self._last_pos = pos
            self._last_move_at = now
            self._request_id += 1  # все запросы «в полёте» становятся устаревшими
            self._pending = None   # ожидающий запрос тоже больше не нужен

            if self._hover_fired:
                self._hover_fired = False
                self.moved.emit()
            return

        # Курсор стоит на месте.
        if self._hover_fired or (now - self._last_move_at) < HOVER_DELAY:
            return

        self._hover_fired = True
        # Логическую позицию запоминаем в момент hover: по ней Qt позиционирует
        # окно. Пересчитывать физические координаты в логические вручную
        # ненадёжно на мультимониторе со смешанным DPI, поэтому берём у Qt.
        self._hover_logical_pos = QCursor.pos()
        self._request_probe(self._request_id, *pos)

    def _request_probe(self, request_id: int, x: int, y: int) -> None:
        if self._in_flight:
            # Воркер занят (Explorer тормозит): запоминаем только последний запрос.
            self._pending = (request_id, x, y)
            return
        self._in_flight = True
        self._probe_requested.emit(request_id, x, y)

    @pyqtSlot(int, object)
    def _on_probe_result(self, request_id: int, hit: FolderHit | None) -> None:
        self._in_flight = False

        # Если за время ожидания накопился более свежий запрос, отправляем его.
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
