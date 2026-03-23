# jacammander/app/net/server.py

import os
import socket
import threading
from app.common import constants
from app.debug.logger import get_logger
from app.net import packet
from app.core import protocol, file_ops, transfer

log = get_logger()

class JacammanderServer:
    def __init__(self, port, root_dir, password=""):
        self.port = port
        self.root_dir = root_dir
        self.password = password
        self.sock = None
        self.is_running = False

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.sock.bind((constants.DEFAULT_HOST, self.port))
            self.sock.listen(5)
            self.is_running = True
            log.info("Server listening on port {0}. Root: {1}".format(self.port, self.root_dir))
            
            accept_thread = threading.Thread(target=self._accept_loop)
            accept_thread.daemon = True
            accept_thread.start()
        except Exception as e:
            log.error("Failed to start server: {0}".format(e))
            self.is_running = False

    def stop(self):
        self.is_running = False
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
        log.info("Server stopped.")

    def _accept_loop(self):
        while self.is_running:
            try:
                client_sock, client_addr = self.sock.accept()
                log.info("Accepted connection from {0}:{1}".format(client_addr[0], client_addr[1]))
                
                client_thread = threading.Thread(
                    target=self._handle_client, 
                    args=(client_sock, client_addr)
                )
                client_thread.daemon = True
                client_thread.start()
            except Exception as e:
                if self.is_running:
                    log.error("Accept loop error: {0}".format(e))

    def _handle_client(self, client_sock, client_addr):
        authenticated = False if self.password else True
        
        try:
            while self.is_running:
                msg = packet.recv_message(client_sock)
                if msg is None:
                    log.info("Client {0} disconnected cleanly.".format(client_addr[0]))
                    break
                    
                cmd = msg.get(constants.KEY_CMD)
                payload = msg.get(constants.KEY_PAYLOAD, {})
                
                if cmd == constants.CMD_PING:
                    packet.send_message(client_sock, protocol.build_response("OK", "PONG"))
                    
                elif cmd == constants.CMD_AUTH:
                    if payload.get("password") == self.password:
                        authenticated = True
                        packet.send_message(client_sock, protocol.build_response("OK", "Authenticated"))
                    else:
                        packet.send_message(client_sock, protocol.build_error("Invalid password"))
                        
                elif cmd == constants.CMD_LIST:
                    if not authenticated:
                        packet.send_message(client_sock, protocol.build_error("Not authenticated"))
                        continue
                        
                    rel_path = payload.get("path", "")
                    try:
                        items = file_ops.list_directory(self.root_dir, rel_path)
                        packet.send_message(client_sock, protocol.build_response(
                            "OK", payload={"items": items, "path": rel_path}
                        ))
                    except ValueError as ve:
                        packet.send_message(client_sock, protocol.build_error(str(ve)))

                elif cmd == constants.CMD_DOWNLOAD:
                    if not authenticated:
                        packet.send_message(client_sock, protocol.build_error("Not authenticated"))
                        continue
                        
                    rel_path = payload.get("path", "")
                    target_path = os.path.abspath(os.path.join(self.root_dir, rel_path))
                    
                    if not file_ops.is_path_safe(self.root_dir, target_path):
                        packet.send_message(client_sock, protocol.build_error("Access denied"))
                        continue
                        
                    if not os.path.exists(target_path) or not os.path.isfile(target_path):
                        packet.send_message(client_sock, protocol.build_error("File not found"))
                        continue
                        
                    file_size = os.path.getsize(target_path)
                    packet.send_message(client_sock, protocol.build_response("OK", payload={"size": file_size}))
                    transfer.send_file(client_sock, target_path)

                elif cmd == constants.CMD_UPLOAD:
                    if not authenticated:
                        packet.send_message(client_sock, protocol.build_error("Not authenticated"))
                        continue
                        
                    rel_path = payload.get("path", "")
                    file_size = payload.get("size", 0)
                    target_path = os.path.abspath(os.path.join(self.root_dir, rel_path))
                    
                    if not file_ops.is_path_safe(self.root_dir, target_path):
                        packet.send_message(client_sock, protocol.build_error("Access denied"))
                        continue
                        
                    packet.send_message(client_sock, protocol.build_response("OK"))
                    transfer.receive_file(client_sock, target_path, file_size)

                else:
                    packet.send_message(client_sock, protocol.build_error("Unknown command"))
                    
        except Exception as e:
            log.error("Connection error with {0}: {1}".format(client_addr[0], e))
        finally:
            client_sock.close()