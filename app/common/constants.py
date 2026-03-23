# jacammander/app/common/constants.py

# --- App Metadata ---
APP_NAME = "Jacammander"
APP_VERSION = "0.2.0"  # Welcome to v0.2!

# --- Networking Defaults ---
DEFAULT_PORT = 9009
DEFAULT_HOST = "0.0.0.0" # Listen on all interfaces by default for server

# --- Protocol Specs ---
# Crucial: Enforce UTF-8 to bridge the Windows XP (cp1252) vs Win11 (utf-8) gap
ENCODING = "utf-8" 
# 64KB chunks for file transfer. Safe for 32-bit memory constraints, fast enough for LAN.
BUFFER_SIZE = 65536 

# --- Protocol Commands ---
CMD_AUTH = "AUTH"
CMD_PING = "PING"
CMD_LIST = "LIST"
CMD_UPLOAD = "UPLOAD"
CMD_DOWNLOAD = "DOWNLOAD"
CMD_DELETE = "DELETE"  # <-- New
CMD_MKDIR = "MKDIR"    # <-- New
CMD_ERROR = "ERROR"
CMD_OK = "OK"

# --- JSON Keys ---
# Used for structured metadata messages before binary transfer
KEY_CMD = "command"
KEY_PAYLOAD = "payload"
KEY_STATUS = "status"
KEY_MESSAGE = "message"