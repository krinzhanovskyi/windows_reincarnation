import os
from pathlib import Path

def get_folder_contents(folder_path, max_items=15):
    if not folder_path or not os.path.exists(folder_path):
        return []

    try:
        path_obj = Path(folder_path)
        items = []

        for item in path_obj.iterdir():
            if item.name.startswith('.') or item.name.lower() == 'desktop.ini':
                continue
            
            is_dir = item.is_dir()
            
            stat = item.stat()
            items.append({
                'name': item.name,
                'path': str(item),
                'is_dir': is_dir,
                'size': stat.st_size if not is_dir else 0,
                'modified': stat.st_mtime
            })

        items.sort(key=lambda x: (not x['is_dir'], -x['modified']))

        return items[:max_items]

    except PermissionError:
        print(f"[!] Нет доступа к папке: {folder_path}")
        return []
    except Exception as e:
        print(f"[!] Ошибка чтения папки {folder_path}: {e}")
        return []