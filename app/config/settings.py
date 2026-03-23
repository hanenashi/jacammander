# jacammander/app/config/settings.py
import sys
import os
import json
from app.common import constants
from app.debug.logger import get_logger

# --- The PyInstaller Fix ---
if getattr(sys, 'frozen', False):
    # If running as a compiled EXE, save next to the executable
    base_dir = os.path.dirname(sys.executable)
else:
    # If running as a script, go up 3 levels from app/config/settings.py to the root
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CONFIG_FILE = os.path.join(base_dir, "jacammander_config.json")

_default_settings = {
    "server_root": "C:/JACANA_SHARE" if os.name == 'nt' else "/tmp/JACANA_SHARE",
    "server_port": str(constants.DEFAULT_PORT),
    "client_ip": "127.0.0.1",
    "client_port": str(constants.DEFAULT_PORT),
    "client_local_path": os.path.abspath(os.path.expanduser("~"))
}

def load():
    """Loads settings from disk, merging with defaults for any missing keys."""
    if not os.path.exists(CONFIG_FILE):
        return _default_settings.copy()
    try:
        with open(CONFIG_FILE, 'r') as f:
            saved_data = json.load(f)
            merged = _default_settings.copy()
            merged.update(saved_data)
            return merged
    except Exception:
        return _default_settings.copy()

def save(new_settings_dict):
    """Updates the existing settings with new values and writes to disk."""
    current = load()
    current.update(new_settings_dict)
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(current, f, indent=4)
    except Exception as e:
        log = get_logger()
        log.error("Failed to save settings: {0}".format(e))