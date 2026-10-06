import os
import logging

log = logging.getLogger("reincarnation")

def get_folder_contents(folder_path: str, max_items: int = 15) -> list[dict]:
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        return []

    files = []
    try:
        with os.scandir(folder_path) as entries:
            for entry in entries:
                if entry.name.startswith('.') or entry.is_symlink():
                    continue
                    
                try:
                    is_dir = entry.is_dir()
                    stat = entry.stat()
                    
                    files.append({
                        'name': entry.name,
                        'path': entry.path,
                        'is_dir': is_dir,
                        'size': stat.st_size if not is_dir else 0
                    })
                except (PermissionError, FileNotFoundError):
                    pass
                    
    except PermissionError:
        log.warning("Permission denied to read folder: %s", folder_path)
        return []
    except Exception as e:
        log.error("Error reading folder %s: %s", folder_path, e)
        return []

    files.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))

    return files[:max_items]