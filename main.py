# jacammander/main.py

import sys
import os

# --- The cx_Freeze / PyInstaller Fix ---
if getattr(sys, 'frozen', False):
    # If running as a compiled EXE, the base dir is where the EXE lives
    base_dir = os.path.dirname(sys.executable)
else:
    # If running as a script, the base dir is where this file lives
    base_dir = os.path.abspath(os.path.dirname(__file__))

# Ensure the 'app' directory is in the path so we can import cleanly
sys.path.insert(0, base_dir)
# ---------------------------------------

from app.debug.logger import get_logger
from app.gui.app_window import JacammanderApp

def main():
    log = get_logger()
    log.info("Starting Jacammander UI...")
    
    # Launch the Tkinter loop
    app = JacammanderApp()
    app.mainloop()
    
    log.info("Application closed.")

if __name__ == "__main__":
    main()