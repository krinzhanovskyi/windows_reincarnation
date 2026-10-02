import os
from pathlib import Path

def get_folder_contents(folder_path, max_items=15):
    """
    Читает содержимое папки, фильтрует системные файлы и возвращает отсортированный список.
    """
    if not folder_path or not os.path.exists(folder_path):
        return []

    try:
        path_obj = Path(folder_path)
        items = []

        for item in path_obj.iterdir():
            # Пропускаем скрытые файлы (начинаются с точки) и системные вроде desktop.ini
            if item.name.startswith('.') or item.name.lower() == 'desktop.ini':
                continue
            
            is_dir = item.is_dir()
            
            # Собираем базовую информацию о файле/папке
            stat = item.stat()
            items.append({
                'name': item.name,
                'path': str(item),
                'is_dir': is_dir,
                'size': stat.st_size if not is_dir else 0,
                'modified': stat.st_mtime
            })

        # Сортировка: сначала папки, потом файлы. Внутри групп — по дате изменения (самые свежие сверху)
        items.sort(key=lambda x: (not x['is_dir'], -x['modified']))

        # Возвращаем только нужное количество элементов
        return items[:max_items]

    except PermissionError:
        print(f"[!] Нет доступа к папке: {folder_path}")
        return []
    except Exception as e:
        print(f"[!] Ошибка чтения папки {folder_path}: {e}")
        return []