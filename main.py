# jacammander/main.py

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

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