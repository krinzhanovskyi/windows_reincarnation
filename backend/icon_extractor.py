import os
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QFileInfo

def get_file_icon(file_path: str, provider) -> QIcon:
    if file_path.lower().endswith('.url'):
        try:
            for enc in ['utf-8', 'mbcs']:
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        for line in f:
                            if line.lower().startswith('iconfile='):
                                icon_path = line.split('=', 1)[1].strip()
                                if os.path.exists(icon_path):
                                    return QIcon(icon_path)
                    break 
                except UnicodeDecodeError:
                    continue
        except Exception:
            pass
    return provider.icon(QFileInfo(file_path))