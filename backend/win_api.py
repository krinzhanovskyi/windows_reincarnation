"""
Низкоуровневая работа с Windows: координаты курсора, пути рабочего стола,
определение папки под курсором через UI Automation.

Ключевое правило модуля: ВСЕ координаты здесь — ФИЗИЧЕСКИЕ пиксели экрана.
Qt (QCursor.pos(), QWidget.move()) работает в ЛОГИЧЕСКИХ пикселях.
Смешивать их нельзя: при масштабе 150% логическая точка (1000, 500)
соответствует физической (1500, 750), и хит-тест попадёт не в ту иконку.
"""

from __future__ import annotations

import ctypes
import logging
import os
import uuid
from ctypes import wintypes
from dataclasses import dataclass
from functools import lru_cache

import uiautomation as auto

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# WinAPI-прототипы
# ---------------------------------------------------------------------------
# Явно задаём argtypes/restype: без них ctypes угадывает типы, и на x64
# указатели/хэндлы могут обрезаться до 32 бит. use_last_error=True даёт
# корректный GetLastError() через ctypes.get_last_error().

_user32 = ctypes.WinDLL("user32", use_last_error=True)
_shell32 = ctypes.WinDLL("shell32", use_last_error=True)
_ole32 = ctypes.WinDLL("ole32")

_user32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
_user32.GetCursorPos.restype = wintypes.BOOL


class GUID(ctypes.Structure):
    """Структура GUID в раскладке Windows (little-endian для первых трёх полей)."""

    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    ]

    @classmethod
    def from_string(cls, value: str) -> "GUID":
        # uuid.bytes_le совпадает с бинарной раскладкой GUID в памяти Windows.
        return cls.from_buffer_copy(uuid.UUID(value).bytes_le)


# restype = HRESULT: ctypes сам бросит OSError при отрицательном коде возврата,
# ручная проверка не нужна.
_shell32.SHGetKnownFolderPath.argtypes = [
    ctypes.POINTER(GUID),
    wintypes.DWORD,
    wintypes.HANDLE,
    ctypes.POINTER(ctypes.c_void_p),
]
_shell32.SHGetKnownFolderPath.restype = ctypes.HRESULT

_ole32.CoTaskMemFree.argtypes = [ctypes.c_void_p]
_ole32.CoTaskMemFree.restype = None

# Идентификаторы известных папок (KNOWNFOLDERID) из ShlObj.h.
FOLDERID_DESKTOP = "{B4BFCC3A-DB2C-424C-B029-7FE99A87C641}"        # личный рабочий стол
FOLDERID_PUBLIC_DESKTOP = "{C4AA340D-F20F-4863-AFEF-F87EF2E6BA25}"  # C:\Users\Public\Desktop

# Классы окон, которые являются рабочим столом.
# Progman — обычный режим; WorkerW — после Win+D или при включённых обоях-слайдшоу.
DESKTOP_WINDOW_CLASSES = frozenset({"Progman", "WorkerW"})
# Список иконок рабочего стола — это ListView (FolderView) класса SysListView32.
DESKTOP_LIST_CLASS = "SysListView32"


# ---------------------------------------------------------------------------
# Курсор
# ---------------------------------------------------------------------------

def get_physical_cursor_pos() -> tuple[int, int] | None:
    """
    Возвращает позицию курсора в ФИЗИЧЕСКИХ пикселях виртуального экрана.

    Физические координаты GetCursorPos отдаёт только в DPI-aware процессе.
    Qt6 делает процесс Per-Monitor-V2-aware при создании QApplication,
    поэтому вызывать функцию нужно ПОСЛЕ создания QApplication.

    Возвращает None, если координаты недоступны (например, открыт
    secure desktop: UAC-запрос или экран блокировки).
    """
    pt = wintypes.POINT()
    if not _user32.GetCursorPos(ctypes.byref(pt)):
        log.debug("GetCursorPos failed, winerror=%s", ctypes.get_last_error())
        return None
    return pt.x, pt.y


# ---------------------------------------------------------------------------
# Пути рабочего стола
# ---------------------------------------------------------------------------

def _get_known_folder(folder_id: str) -> str | None:
    """
    Путь известной папки через SHGetKnownFolderPath.

    Этот способ надёжнее чтения реестра "User Shell Folders": он учитывает
    перенос Desktop в OneDrive, групповые политики и редирект папок.
    """
    guid = GUID.from_string(folder_id)  # держим ссылку, пока идёт вызов
    buf = ctypes.c_void_p()
    try:
        _shell32.SHGetKnownFolderPath(ctypes.byref(guid), 0, None, ctypes.byref(buf))
        return ctypes.wstring_at(buf.value)
    except OSError:
        log.warning("SHGetKnownFolderPath(%s) failed", folder_id, exc_info=True)
        return None
    finally:
        # Строку выделяет Shell, освобождать её обязаны мы, иначе утечка памяти.
        if buf.value:
            _ole32.CoTaskMemFree(buf)


@lru_cache(maxsize=1)
def get_desktop_dirs() -> tuple[str, ...]:
    """
    Все каталоги, иконки из которых показываются на рабочем столе:
    личный Desktop + общий Public Desktop.

    Результат кэшируется: на каждый hover дёргать Shell незачем.
    Если пользователь перенёс Desktop во время работы программы,
    вызовите get_desktop_dirs.cache_clear().
    """
    dirs: list[str] = []

    user_desktop = _get_known_folder(FOLDERID_DESKTOP)
    if not user_desktop:
        # Крайний фолбэк: стандартное расположение без редиректов.
        user_desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        log.warning("Using fallback desktop path: %s", user_desktop)
    dirs.append(user_desktop)

    public_desktop = _get_known_folder(FOLDERID_PUBLIC_DESKTOP)
    if public_desktop:
        dirs.append(public_desktop)

    log.info("Desktop dirs resolved: %s", dirs)
    return tuple(dirs)


# ---------------------------------------------------------------------------
# UI Automation
# ---------------------------------------------------------------------------

def uia_thread_initializer() -> object:
    """
    Инициализирует COM/UIA в ТЕКУЩЕМ потоке.

    UI Automation — это COM. COM инициализируется для каждого потока
    отдельно, поэтому воркер-поток обязан вызвать это до первого запроса.
    Возвращённый объект нужно держать живым всё время работы потока:
    при его уничтожении вызывается CoUninitialize (в том же потоке).
    """
    return auto.UIAutomationInitializerInThread()


@dataclass(frozen=True, slots=True)
class FolderHit:
    """Результат хит-теста: найденная папка на рабочем столе."""

    path: str  # полный путь на диске
    name: str  # имя иконки, как его видит пользователь


def _is_safe_item_name(name: str) -> bool:
    """
    Защита от выхода за пределы Desktop при склейке пути.

    Имя приходит из чужого процесса (explorer.exe). Строки вида
    "..", "C:\\Windows" или "a\\b" при os.path.join дали бы путь
    вне рабочего стола. Допускаем только «голое» имя без разделителей.
    """
    return (
        bool(name)
        and name not in (".", "..")
        and os.path.basename(name) == name
        and not os.path.isabs(name)
    )


def get_desktop_folder_under_cursor(x: int, y: int) -> FolderHit | None:
    """
    Определяет папку рабочего стола под точкой (x, y) в ФИЗИЧЕСКИХ пикселях.

    ВНИМАНИЕ: функция делает межпроцессный COM-вызов в explorer.exe и может
    блокироваться (подвисший Explorer, сетевой диск, синхронизация OneDrive).
    Вызывать только из воркер-потока, никогда из GUI-потока.

    Возвращает None, если под курсором не папка рабочего стола.
    Ошибки не глушатся молча: они пишутся в лог с трейсбеком.
    """
    try:
        control = auto.ControlFromPoint(x, y)
        if control is None:
            return None

        # 1. Иконки рабочего стола в UIA — элементы списка.
        if control.ControlType != auto.ControlType.ListItemControl:
            return None

        # 2. Родитель — именно ListView рабочего стола (SysListView32).
        #    Это отсекает элементы списков в других приложениях.
        parent = control.GetParentControl()
        if parent is None or parent.ClassName != DESKTOP_LIST_CLASS:
            return None

        # 3. Окно верхнего уровня — рабочий стол, а не окно Проводника
        #    (у Проводника тоже есть ListItem-элементы).
        top = control.GetTopLevelControl()
        if top is None or top.ClassName not in DESKTOP_WINDOW_CLASSES:
            return None

        name = control.Name
        if not _is_safe_item_name(name):
            if name:
                log.warning("Rejected suspicious item name: %r", name)
            return None

    except Exception:
        # Элемент мог исчезнуть между вызовами, Explorer мог перезапуститься:
        # это штатные ситуации, поэтому уровень DEBUG, но с трейсбеком.
        log.debug("UIA hit-test failed at (%d, %d)", x, y, exc_info=True)
        return None

    # 4. Сопоставляем отображаемое имя с каталогами на диске.
    #    Ограничение: папки с локализованным именем из desktop.ini
    #    (LocalizedResourceName) так не резолвятся. Для них нужен Shell API
    #    (IShellFolder::ParseDisplayName). Это отдельная задача.
    for desktop_dir in get_desktop_dirs():
        candidate = os.path.join(desktop_dir, name)
        # isdir отсекает файлы и ярлыки: ярлык "Foo" на диске называется "Foo.lnk".
        if os.path.isdir(candidate):
            return FolderHit(path=candidate, name=name)

    log.debug("Desktop item %r is not a folder (or not resolvable)", name)
    return None
