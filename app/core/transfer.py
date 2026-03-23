# jacammander/app/core/transfer.py

import os
from app.common import constants
from app.debug.logger import get_logger

log = get_logger()

def send_file(sock, file_path, progress_cb=None):
    """Reads a file in chunks and sends it over the socket."""
    try:
        file_size = os.path.getsize(file_path)
        with open(file_path, 'rb') as f:
            bytes_sent = 0
            while True:
                # --- FIXED: Now uses BUFFER_SIZE ---
                chunk = f.read(constants.BUFFER_SIZE)
                if not chunk:
                    break
                sock.sendall(chunk)
                bytes_sent += len(chunk)
                
                # Report progress back to the UI
                if progress_cb:
                    progress_cb(bytes_sent, file_size)
                    
        return True
    except Exception as e:
        log.error("Error sending file: {0}".format(e))
        return False

def receive_file(sock, save_path, expected_size, progress_cb=None):
    """Receives chunks from the socket and writes them to a file."""
    try:
        bytes_received = 0
        with open(save_path, 'wb') as f:
            while bytes_received < expected_size:
                # Calculate how much is left so we don't over-read and block the socket
                remaining = expected_size - bytes_received
                
                # --- FIXED: Now uses BUFFER_SIZE ---
                chunk_size = min(constants.BUFFER_SIZE, remaining)
                
                chunk = sock.recv(chunk_size)
                if not chunk:
                    raise ConnectionError("Connection lost during transfer.")
                    
                f.write(chunk)
                bytes_received += len(chunk)
                
                # Report progress back to the UI
                if progress_cb:
                    progress_cb(bytes_received, expected_size)
                    
        return True
    except Exception as e:
        log.error("Error receiving file: {0}".format(e))
        # Clean up the corrupted partial file
        if os.path.exists(save_path):
            try:
                os.remove(save_path)
            except OSError:
                pass
        return False