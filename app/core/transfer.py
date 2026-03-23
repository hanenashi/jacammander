# jacammander/app/core/transfer.py

import os
from app.common import constants
from app.debug.logger import get_logger

log = get_logger()

def send_file(sock, file_path):
    """
    Reads a file from disk in chunks and sends it directly over the socket.
    Assumes the receiver already knows the file size and is waiting.
    """
    total_sent = 0
    try:
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(constants.BUFFER_SIZE)
                if not chunk:
                    break
                sock.sendall(chunk)
                total_sent += len(chunk)
        return True
    except Exception as e:
        log.error("Error sending file {0}: {1}".format(file_path, e))
        return False

def receive_file(sock, save_path, expected_size):
    """
    Reads exactly expected_size bytes from the socket in chunks 
    and writes them to disk.
    """
    bytes_received = 0
    try:
        with open(save_path, 'wb') as f:
            while bytes_received < expected_size:
                # Read either the buffer size or whatever is left
                bytes_to_read = min(constants.BUFFER_SIZE, expected_size - bytes_received)
                chunk = sock.recv(bytes_to_read)
                
                if not chunk:
                    raise RuntimeError("Socket closed prematurely during transfer.")
                    
                f.write(chunk)
                bytes_received += len(chunk)
        return True
    except Exception as e:
        log.error("Error receiving file to {0}: {1}".format(save_path, e))
        # Clean up the partial file if the transfer blew up
        if os.path.exists(save_path):
            try:
                os.remove(save_path)
            except OSError:
                pass
        return False