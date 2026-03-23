# jacammander/main.py

import sys
import os

# Ensure the 'app' directory is in the path so we can import cleanly
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.common.constants import APP_NAME, APP_VERSION
from app.debug.logger import get_logger

def main():
    log = get_logger()
    log.info(f"Starting {APP_NAME} v{APP_VERSION}...")
    log.debug("Initializing Python LAN file manager.")
    
    # TODO: Load settings
    # TODO: Launch GUI Chooser (Server vs Client)
    
    log.info("Initialization complete. Awaiting GUI hookup.")

if __name__ == "__main__":
    main()
