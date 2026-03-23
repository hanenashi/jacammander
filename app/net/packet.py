# jacammander/app/net/packet.py

import json
import socket
from app.common.constants import ENCODING

HEADER_LENGTH = 10

def send_message(sock, message_dict):
    """
    Serializes a dict to JSON, adds a length header, and sends it over the socket.
    """
    try:
        # Convert dict to JSON string, then to bytes using our strict encoding
        json_data = json.dumps(message_dict)
        payload_bytes = json_data.encode(ENCODING)
        
        # Create a fixed-length header: e.g., "0000000142"
        header = "{:010d}".format(len(payload_bytes))
        header_bytes = header.encode(ENCODING)
        
        # Send header then payload
        sock.sendall(header_bytes + payload_bytes)
        return True
    except Exception as e:
        # We will catch this higher up in the connection handler
        raise RuntimeError("Failed to send message: {0}".format(str(e)))

def recv_exactly(sock, num_bytes):
    """
    Helper to ensure we receive exactly the number of bytes requested,
    handling partial reads from the socket.
    """
    data = bytearray()
    while len(data) < num_bytes:
        chunk = sock.recv(num_bytes - len(data))
        if not chunk:
            # Socket closed prematurely
            return None 
        data.extend(chunk)
    return bytes(data)

def recv_message(sock):
    """
    Reads the header, then reads the exact payload size, and parses the JSON.
    """
    try:
        # 1. Read the header
        header_bytes = recv_exactly(sock, HEADER_LENGTH)
        if not header_bytes:
            return None # Connection closed cleanly
            
        # 2. Parse the payload length
        payload_length = int(header_bytes.decode(ENCODING))
        
        # 3. Read the exact payload
        payload_bytes = recv_exactly(sock, payload_length)
        if not payload_bytes:
            return None
            
        # 4. Decode and parse JSON
        json_data = payload_bytes.decode(ENCODING)
        return json.loads(json_data)
        
    except ValueError:
        raise RuntimeError("Received malformed header or JSON payload.")
    except Exception as e:
        raise RuntimeError("Failed to receive message: {0}".format(str(e)))