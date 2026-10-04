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

_user32 = ctypes.WinDLL("user32", use_last_error=True)
_shell32 = ctypes.WinDLL("shell32", use_last_error=True)
_ole32 = ctypes.WinDLL("ole32")

_user32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
_user32.GetCursorPos.restype = wintypes.BOOL

class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    ]
    @classmethod
    def from_string(cls, value: str) -> "GUID":
        return cls.from_buffer_copy(uuid.UUID(value).bytes_le)

_shell32.SHGetKnownFolderPath.argtypes = [
    ctypes.POINTER(GUID), wintypes.DWORD, wintypes.HANDLE, ctypes.POINTER(ctypes.c_void_p)
]
_shell32.SHGetKnownFolderPath.restype = ctypes.HRESULT

_ole32.CoTaskMemFree.argtypes = [ctypes.c_void_p]
_ole32.CoTaskMemFree.restype = None

class SHFILEINFOW(ctypes.Structure):
    _fields_ = [
        ("hIcon", wintypes.HANDLE),
        ("iIcon", ctypes.c_int),
        ("dwAttributes", wintypes.DWORD),
        ("szDisplayName", wintypes.WCHAR * 260),
        ("szTypeName", wintypes.WCHAR * 80),
    ]

_shell32.SHGetFileInfoW.argtypes = [
    wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(SHFILEINFOW), ctypes.c_uint, ctypes.c_uint
]
_shell32.SHGetFileInfoW.restype = ctypes.c_void_p
SHGFI_DISPLAYNAME = 0x00000200

FOLDERID_DESKTOP = "{B4BFCC3A-DB2C-424C-B029-7FE99A87C641}"
FOLDERID_PUBLIC_DESKTOP = "{C4AA340D-F20F-4863-AFEF-F87EF2E6BA25}"

DESKTOP_WINDOW_CLASSES = frozenset({"Progman", "WorkerW"})
DESKTOP_LIST_CLASS = "SysListView32"

def get_physical_cursor_pos() -> tuple[int, int] | None:
    pt = wintypes.POINT()
    if not _user32.GetCursorPos(ctypes.byref(pt)):
        return None
    return pt.x, pt.y

def _get_known_folder(folder_id: str) -> str | None:
    guid = GUID.from_string(folder_id)
    buf = ctypes.c_void_p()
    try:
        _shell32.SHGetKnownFolderPath(ctypes.byref(guid), 0, None, ctypes.byref(buf))
        return ctypes.wstring_at(buf.value)
    except OSError:
        return None
    finally:
        if buf.value:
            _ole32.CoTaskMemFree(buf)

@lru_cache(maxsize=1)
def get_desktop_dirs() -> tuple[str, ...]:
    dirs: list[str] = []
    user_desktop = _get_known_folder(FOLDERID_DESKTOP)
    if not user_desktop:
        user_desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    dirs.append(user_desktop)
    
    public_desktop = _get_known_folder(FOLDERID_PUBLIC_DESKTOP)
    if public_desktop:
        dirs.append(public_desktop)
    return tuple(dirs)

def uia_thread_initializer() -> object:
    return auto.UIAutomationInitializerInThread()

@dataclass(frozen=True, slots=True)
class FolderHit:
    path: str
    name: str

def _is_safe_item_name(name: str) -> bool:
    return bool(name) and name not in (".", "..") and os.path.basename(name) == name and not os.path.isabs(name)

def get_desktop_folder_under_cursor(x: int, y: int) -> FolderHit | None:
    try:
        control = auto.ControlFromPoint(x, y)
        if control is None or control.ControlType != auto.ControlType.ListItemControl:
            return None

        parent = control.GetParentControl()
        if parent is None or parent.ClassName != DESKTOP_LIST_CLASS:
            return None

        top = control.GetTopLevelControl()
        if top is None or top.ClassName not in DESKTOP_WINDOW_CLASSES:
            return None

        name = control.Name
        if not _is_safe_item_name(name):
            return None

    except Exception:
        return None

    for desktop_dir in get_desktop_dirs():
        try:
            for entry in os.scandir(desktop_dir):
                if entry.is_dir():
                    shfi = SHFILEINFOW()
                    res = _shell32.SHGetFileInfoW(
                        entry.path, 0, ctypes.byref(shfi), ctypes.sizeof(shfi), SHGFI_DISPLAYNAME
                    )
                    if res and shfi.szDisplayName == name:
                        return FolderHit(path=entry.path, name=name)
                    elif entry.name == name:
                        return FolderHit(path=entry.path, name=name)
        except OSError:
            pass

    return None