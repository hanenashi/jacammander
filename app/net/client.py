# jacammander/app/net/client.py

import os
import socket
from app.common import constants
from app.debug.logger import get_logger
from app.net import packet
from app.core import protocol, transfer

log = get_logger()

class JacammanderClient:
    def __init__(self, host, port, password=""):
        self.host = host
        self.port = port
        self.password = password
        self.sock = None
        self.connected = False

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5.0) 
            self.sock.connect((self.host, self.port))
            
            self.sock.settimeout(None) 
            self.connected = True
            log.info("Connected to {0}:{1}".format(self.host, self.port))
            
            return self.authenticate()
            
        except socket.timeout:
            log.error("Connection timed out to {0}:{1}".format(self.host, self.port))
            self.connected = False
            return False
        except Exception as e:
            log.error("Connection failed: {0}".format(e))
            self.connected = False
            return False

    def disconnect(self):
        self.connected = False
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None
        log.info("Disconnected from server.")

    def authenticate(self):
        if not self.connected:
            return False
        
        log.debug("Sending AUTH request...")
        req = protocol.build_auth_request(self.password)
        packet.send_message(self.sock, req)
        
        resp = packet.recv_message(self.sock)
        if resp and resp.get(constants.KEY_STATUS) == "OK":
            log.info("Authentication successful.")
            return True
        else:
            err = resp.get(constants.KEY_MESSAGE, "Unknown error") if resp else "No response from server"
            log.error("Authentication failed: {0}".format(err))
            self.disconnect()
            return False

    def list_directory(self, rel_path=""):
        if not self.connected:
            log.error("Cannot list directory: Not connected.")
            return None
            
        req = protocol.build_request(constants.CMD_LIST, {"path": rel_path})
        packet.send_message(self.sock, req)
        
        resp = packet.recv_message(self.sock)
        if resp and resp.get(constants.KEY_STATUS) == "OK":
            return resp.get(constants.KEY_PAYLOAD, {}).get("items", [])
        else:
            err = resp.get(constants.KEY_MESSAGE, "Unknown error") if resp else "No response"
            log.error("Failed to list directory: {0}".format(err))
            return None

    def download_file(self, remote_rel_path, local_save_path):
        if not self.connected:
            return False
            
        log.info("Requesting download of {0}...".format(remote_rel_path))
        req = protocol.build_request(constants.CMD_DOWNLOAD, {"path": remote_rel_path})
        packet.send_message(self.sock, req)
        
        resp = packet.recv_message(self.sock)
        if resp and resp.get(constants.KEY_STATUS) == "OK":
            file_size = resp.get(constants.KEY_PAYLOAD, {}).get("size", 0)
            log.debug("Server ready. Expecting {0} bytes.".format(file_size))
            
            success = transfer.receive_file(self.sock, local_save_path, file_size)
            if success:
                log.info("Download complete: {0}".format(local_save_path))
            return success
        else:
            err = resp.get(constants.KEY_MESSAGE, "Unknown error") if resp else "No response"
            log.error("Download failed: {0}".format(err))
            return False

    def upload_file(self, local_file_path, remote_rel_path):
        if not self.connected:
            return False
            
        if not os.path.exists(local_file_path) or not os.path.isfile(local_file_path):
            log.error("Local file does not exist: {0}".format(local_file_path))
            return False
            
        file_size = os.path.getsize(local_file_path)
        log.info("Requesting upload of {0} ({1} bytes)...".format(local_file_path, file_size))
        
        req = protocol.build_request(constants.CMD_UPLOAD, {"path": remote_rel_path, "size": file_size})
        packet.send_message(self.sock, req)
        
        resp = packet.recv_message(self.sock)
        if resp and resp.get(constants.KEY_STATUS) == "OK":
            log.debug("Server ready. Sending file...")
            success = transfer.send_file(self.sock, local_file_path)
            if success:
                log.info("Upload complete.")
            return success
        else:
            err = resp.get(constants.KEY_MESSAGE, "Unknown error") if resp else "No response"
            log.error("Upload failed: {0}".format(err))
            return False