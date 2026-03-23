# jacammander/app/debug/logger.py

import logging
import sys

# Create a master logger for the app
_logger = logging.getLogger("jacammander")
_logger.setLevel(logging.DEBUG) # Catch everything during dev

# Prevent adding multiple handlers if this module is imported multiple times
if not _logger.handlers:
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # Clean, readable format: [INFO] 2026-03-23 13:05:12 - Server started
    formatter = logging.Formatter('[%(levelname)s] %(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    console_handler.setFormatter(formatter)
    
    _logger.addHandler(console_handler)

def get_logger():
    """Returns the shared application logger."""
    return _logger
