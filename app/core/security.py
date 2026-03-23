# jacammander/app/core/security.py

import os

def is_path_safe(root_dir, target_path):
    """
    Ensures the target_path does not escape the shared root_dir.
    Resolves relative path jumps like '..' before checking.
    """
    # Normalize paths to absolute, resolving any '..' tricks
    abs_root = os.path.abspath(root_dir)
    abs_target = os.path.abspath(target_path)
    
    # Force a trailing separator on the root to prevent partial name matches
    # e.g., preventing "C:\shared_hacked" from passing if root is "C:\shared"
    prefix = os.path.join(abs_root, '') 
    
    return abs_target.startswith(prefix) or abs_target == abs_root