# jacammander/app/core/file_ops.py

import os
from app.core.security import is_path_safe

def list_directory(root_dir, rel_path=""):
    """
    Returns a sorted list of files and folders in the requested path.
    Directories are sorted first, then alphabetically.
    """
    target_dir = os.path.abspath(os.path.join(root_dir, rel_path))
    
    if not is_path_safe(root_dir, target_dir):
        raise ValueError("Path access denied. Do not try to escape the root.")
        
    if not os.path.exists(target_dir) or not os.path.isdir(target_dir):
        raise ValueError("Directory does not exist.")
        
    items = []
    for entry in os.listdir(target_dir):
        full_path = os.path.join(target_dir, entry)
        is_dir = os.path.isdir(full_path)
        
        try:
            stat = os.stat(full_path)
            size = stat.st_size if not is_dir else 0
            mtime = stat.st_mtime
        except OSError:
            # Skip files locked by the OS (like pagefile.sys)
            continue
            
        items.append({
            "name": entry,
            "is_dir": is_dir,
            "size": size,
            "mtime": mtime
        })
        
    # Sort: folders first, then A-Z
    items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
    return items