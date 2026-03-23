# jacammander/app/gui/client_panel.py

import os
import queue
import threading
import logging
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from app.common import constants
from app.net.client import JacammanderClient
from app.debug.logger import get_logger
from app.config import settings
from app.core import protocol, transfer
from app.net import packet

log = get_logger()

class QueueHandler(logging.Handler):
    """Custom logging handler that drops log messages into a thread-safe queue."""
    def __init__(self, log_queue):
        logging.Handler.__init__(self)
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(self.format(record))

class ClientPanel(tk.Frame):
    def __init__(self, parent, go_back_callback):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.go_back_callback = go_back_callback
        
        self.client = None
        self.log_queue = queue.Queue()
        
        cfg = settings.load()
        
        # State tracking
        self.local_current_path = cfg.get("client_local_path")
        if not self.local_current_path or not os.path.exists(self.local_current_path):
            self.local_current_path = os.path.abspath(os.path.expanduser("~"))
            
        self.remote_current_path = "" # Empty string means root in our protocol
        
        self._setup_ui()
        self._setup_logging()
        self._poll_log_queue()
        self._refresh_local()
        
    def _update_progress(self, current_bytes, total_bytes):
        """Thread-safe UI update for the progress bar."""
        if total_bytes > 0:
            percentage = (current_bytes / total_bytes) * 100
            self.progress_var.set(percentage)

    def _setup_ui(self):
        cfg = settings.load()

        # --- Connection Frame (Top) ---
        conn_frame = tk.LabelFrame(self, text="Server Connection", padx=5, pady=5)
        conn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(conn_frame, text="IP:").pack(side=tk.LEFT, padx=2)
        self.ip_var = tk.StringVar(value=cfg.get("client_ip"))
        tk.Entry(conn_frame, textvariable=self.ip_var, width=15).pack(side=tk.LEFT, padx=2)
        
        tk.Label(conn_frame, text="Port:").pack(side=tk.LEFT, padx=2)
        self.port_var = tk.StringVar(value=cfg.get("client_port"))
        tk.Entry(conn_frame, textvariable=self.port_var, width=6).pack(side=tk.LEFT, padx=2)
        
        tk.Label(conn_frame, text="Pass:").pack(side=tk.LEFT, padx=2)
        self.pass_var = tk.StringVar()
        tk.Entry(conn_frame, textvariable=self.pass_var, width=15, show="*").pack(side=tk.LEFT, padx=2)
        
        self.btn_connect = tk.Button(conn_frame, text="Connect", bg="lightgreen", command=self._toggle_connection)
        self.btn_connect.pack(side=tk.LEFT, padx=10)
        
        btn_back = tk.Button(conn_frame, text="< Back", command=self._go_back)
        btn_back.pack(side=tk.RIGHT, padx=5)

        # --- Dual Pane Frame (Middle) ---
        pane_frame = tk.Frame(self)
        pane_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        pane_frame.grid_columnconfigure(0, weight=1) # Local
        pane_frame.grid_columnconfigure(1, weight=0) # Buttons
        pane_frame.grid_columnconfigure(2, weight=1) # Remote
        pane_frame.grid_rowconfigure(0, weight=1)

        # -- Local Side --
        local_frame = tk.LabelFrame(pane_frame, text="Local Files")
        local_frame.grid(row=0, column=0, sticky="nsew", padx=5)
        
        self.local_path_lbl = tk.Label(local_frame, text=self.local_current_path, anchor="w", bg="white", relief="sunken")
        self.local_path_lbl.pack(fill=tk.X, padx=2, pady=2)
        
        self.local_tree = self._create_treeview(local_frame)
        self.local_tree.bind("<Double-1>", self._on_local_double_click)

        # -- Action Buttons (Middle) --
        action_frame = tk.Frame(pane_frame)
        action_frame.grid(row=0, column=1, sticky="ns", padx=5)
        
        self.btn_upload = tk.Button(action_frame, text="Upload ->", state=tk.DISABLED, command=self._do_upload)
        self.btn_upload.pack(pady=20)
        
        self.btn_download = tk.Button(action_frame, text="<- Download", state=tk.DISABLED, command=self._do_download)
        self.btn_download.pack(pady=20)
        
        self.btn_refresh = tk.Button(action_frame, text="Refresh Both", state=tk.DISABLED, command=self._refresh_all)
        self.btn_refresh.pack(pady=20)
        
        # (Inside _setup_ui, right below btn_refresh)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(action_frame, variable=self.progress_var, maximum=100, length=120)
        self.progress_bar.pack(pady=10)

        # -- Remote Side --
        remote_frame = tk.LabelFrame(pane_frame, text="Remote Files")
        remote_frame.grid(row=0, column=2, sticky="nsew", padx=5)
        
        self.remote_path_lbl = tk.Label(remote_frame, text="/", anchor="w", bg="white", relief="sunken")
        self.remote_path_lbl.pack(fill=tk.X, padx=2, pady=2)

        # Action Buttons (Bottom of Remote Pane)
        remote_btn_frame = tk.Frame(remote_frame)
        remote_btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=2, pady=2)
        
        self.btn_remote_mkdir = tk.Button(remote_btn_frame, text="New Folder", state=tk.DISABLED, command=self._remote_mkdir)
        self.btn_remote_mkdir.pack(side=tk.LEFT, padx=2)
        
        self.btn_remote_delete = tk.Button(remote_btn_frame, text="Delete", fg="red", state=tk.DISABLED, command=self._remote_delete)
        self.btn_remote_delete.pack(side=tk.RIGHT, padx=2)
        
        self.remote_tree = self._create_treeview(remote_frame)
        self.remote_tree.bind("<Double-1>", self._on_remote_double_click)

        # --- Log Frame (Bottom) ---
        log_frame = tk.Frame(self)
        log_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.log_text = tk.Text(log_frame, height=6, state=tk.DISABLED, bg="#f0f0f0")
        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _create_treeview(self, parent_frame):
        """Helper to create consistent file lists."""
        columns = ("name", "size", "type")
        tree = ttk.Treeview(parent_frame, columns=columns, show="headings", selectmode="browse")
        
        tree.heading("name", text="Name")
        tree.heading("size", text="Size")
        tree.heading("type", text="Type")
        
        tree.column("name", width=200, anchor="w")
        tree.column("size", width=80, anchor="e")
        tree.column("type", width=60, anchor="center")
        
        scrollbar = ttk.Scrollbar(parent_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        return tree

    # --- Logging ---
    def _setup_logging(self):
        self.queue_handler = QueueHandler(self.log_queue)
        formatter = logging.Formatter('[%(levelname)s] %(message)s')
        self.queue_handler.setFormatter(formatter)
        log.addHandler(self.queue_handler)

    def _poll_log_queue(self):
        while not self.log_queue.empty():
            msg = self.log_queue.get()
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, msg + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
        self.after(100, self._poll_log_queue)

    # --- Core Logic ---
    def _toggle_connection(self):
        if self.client and self.client.connected:
            self.client.disconnect()
            self.client = None
            self.btn_connect.config(text="Connect", bg="lightgreen")
            self.remote_tree.delete(*self.remote_tree.get_children())
            self._set_buttons_state(tk.DISABLED)
        else:
            try:
                port = int(self.port_var.get())
            except ValueError:
                log.error("Invalid port.")
                return
                
            self.client = JacammanderClient(self.ip_var.get(), port, self.pass_var.get())
            if self.client.connect():
                # Save connection info for next launch
                settings.save({
                    "client_ip": self.ip_var.get(),
                    "client_port": str(port)
                })
                
                self.btn_connect.config(text="Disconnect", bg="lightcoral")
                self._set_buttons_state(tk.NORMAL)
                self._refresh_remote()
            else:
                self.client = None

    def _set_buttons_state(self, state):
        self.btn_upload.config(state=state)
        self.btn_download.config(state=state)
        self.btn_refresh.config(state=state)
        self.btn_remote_mkdir.config(state=state)
        self.btn_remote_delete.config(state=state)

    def _refresh_all(self):
        self._refresh_local()
        self._refresh_remote()

    # --- Local File Handling ---
    def _refresh_local(self):
        self.local_tree.delete(*self.local_tree.get_children())
        self.local_path_lbl.config(text=self.local_current_path)
        
        # Add ".." to go up
        parent_dir = os.path.dirname(self.local_current_path)
        if parent_dir and parent_dir != self.local_current_path:
            self.local_tree.insert("", tk.END, text="..", values=("..", "", "<DIR>"))
            
        try:
            items = []
            for entry in os.listdir(self.local_current_path):
                full_path = os.path.join(self.local_current_path, entry)
                is_dir = os.path.isdir(full_path)
                try:
                    size = os.path.getsize(full_path) if not is_dir else 0
                except OSError:
                    continue # Skip locked files
                items.append((entry, is_dir, size))
                
            items.sort(key=lambda x: (not x[1], x[0].lower()))
            
            for item in items:
                size_str = "{0:,}".format(item[2]) if not item[1] else ""
                type_str = "<DIR>" if item[1] else "FILE"
                self.local_tree.insert("", tk.END, text=item[0], values=(item[0], size_str, type_str))
        except Exception as e:
            log.error("Failed to read local dir: {0}".format(e))

    def _on_local_double_click(self, event):
        sel = self.local_tree.selection()
        if not sel: return
        
        item_text = self.local_tree.item(sel[0])['text']
        if item_text == "..":
            self.local_current_path = os.path.dirname(self.local_current_path)
        else:
            target_path = os.path.join(self.local_current_path, item_text)
            if os.path.isdir(target_path):
                self.local_current_path = target_path
            else:
                return # It's a file, do nothing on double click for now
                
        # Save the new path to config
        settings.save({"client_local_path": self.local_current_path})
        self._refresh_local()

    # --- Remote File Handling ---
    def _refresh_remote(self):
        if not self.client or not self.client.connected: return
        
        self.remote_tree.delete(*self.remote_tree.get_children())
        display_path = "/" + self.remote_current_path.replace("\\", "/")
        self.remote_path_lbl.config(text=display_path)
        
        # Add ".." to go up if not at root
        if self.remote_current_path:
            self.remote_tree.insert("", tk.END, text="..", values=("..", "", "<DIR>"))
            
        items = self.client.list_directory(self.remote_current_path)
        if items is not None:
            for item in items:
                size_str = "{0:,}".format(item['size']) if not item['is_dir'] else ""
                type_str = "<DIR>" if item['is_dir'] else "FILE"
                self.remote_tree.insert("", tk.END, text=item['name'], values=(item['name'], size_str, type_str))

    def _on_remote_double_click(self, event):
        sel = self.remote_tree.selection()
        if not sel: return
        
        item_text = self.remote_tree.item(sel[0])['text']
        is_dir = self.remote_tree.item(sel[0])['values'][2] == "<DIR>"
        
        if not is_dir: return
        
        if item_text == "..":
            # Go up one level (handle both windows and unix slashes)
            parts = self.remote_current_path.replace("\\", "/").strip("/").split("/")
            self.remote_current_path = "/".join(parts[:-1])
        else:
            if self.remote_current_path:
                self.remote_current_path += "/" + item_text
            else:
                self.remote_current_path = item_text
                
        self._refresh_remote()

    # --- Remote Action Commands (v0.2) ---
    def _remote_mkdir(self):
        folder_name = simpledialog.askstring("New Folder", "Enter folder name:")
        if not folder_name: return
        
        remote_path = folder_name if not self.remote_current_path else self.remote_current_path + "/" + folder_name
        if self.client.create_directory(remote_path):
            self._refresh_remote()

    def _remote_delete(self):
        sel = self.remote_tree.selection()
        if not sel: return
        
        item_text = self.remote_tree.item(sel[0])['text']
        if item_text == "..": return
        
        if not messagebox.askyesno("Confirm Delete", "Are you sure you want to permanently delete '{0}'?".format(item_text)):
            return
            
        remote_path = item_text if not self.remote_current_path else self.remote_current_path + "/" + item_text
        if self.client.delete_item(remote_path):
            self._refresh_remote()

    # --- Transfers (Threaded) ---
    def _do_upload(self):
        sel = self.local_tree.selection()
        if not sel: return
        item = self.local_tree.item(sel[0])
        if item['values'][2] == "<DIR>":
            log.warning("Cannot upload entire folders yet.")
            return
            
        filename = item['text']
        local_path = os.path.join(self.local_current_path, filename)
        remote_path = filename if not self.remote_current_path else self.remote_current_path + "/" + filename
        
        # --- OVERWRITE SAFETY CHECK ---
        # Look through the remote file list to see if the name already exists
        for child in self.remote_tree.get_children():
            if self.remote_tree.item(child)['text'] == filename:
                if not messagebox.askyesno("Confirm Overwrite", "'{0}' already exists on the server. Overwrite it?".format(filename)):
                    return
                break
        # ------------------------------
        
        self._set_buttons_state(tk.DISABLED)
        threading.Thread(target=self._thread_upload, args=(local_path, remote_path)).start()

    def _thread_upload(self, local_path, remote_path):
        # Reset the progress bar
        self.after(0, self.progress_var.set, 0)
        
        # Create a thread-safe callback
        progress_cb = lambda curr, total: self.after(0, self._update_progress, curr, total)
        
        # We need to temporarily hijack the client's internal transfer call to pass the callback
        # (This avoids needing to rewrite client.py just to pass one variable)
        file_size = os.path.getsize(local_path)
        req = protocol.build_request(constants.CMD_UPLOAD, {"path": remote_path, "size": file_size})
        packet.send_message(self.client.sock, req)
        
        resp = packet.recv_message(self.client.sock)
        if resp and resp.get(constants.KEY_STATUS) == "OK":
            transfer.send_file(self.client.sock, local_path, progress_cb)
            
        self.after(0, self._post_transfer_cleanup)
            
    def _do_download(self):
        sel = self.remote_tree.selection()
        if not sel: return
        item = self.remote_tree.item(sel[0])
        if item['values'][2] == "<DIR>":
            log.warning("Cannot download entire folders yet.")
            return
            
        filename = item['text']
        local_path = os.path.join(self.local_current_path, filename)
        remote_path = filename if not self.remote_current_path else self.remote_current_path + "/" + filename
        
        # --- OVERWRITE SAFETY CHECK ---
        # Check the local hard drive to see if the file is already there
        if os.path.exists(local_path):
            if not messagebox.askyesno("Confirm Overwrite", "'{0}' already exists in your local folder. Overwrite it?".format(filename)):
                return
        # ------------------------------
        
        self._set_buttons_state(tk.DISABLED)
        threading.Thread(target=self._thread_download, args=(remote_path, local_path)).start()

    def _thread_download(self, remote_path, local_path):
        # Reset the progress bar
        self.after(0, self.progress_var.set, 0)
        
        progress_cb = lambda curr, total: self.after(0, self._update_progress, curr, total)
        
        req = protocol.build_request(constants.CMD_DOWNLOAD, {"path": remote_path})
        packet.send_message(self.client.sock, req)
        
        resp = packet.recv_message(self.client.sock)
        if resp and resp.get(constants.KEY_STATUS) == "OK":
            file_size = resp.get(constants.KEY_PAYLOAD, {}).get("size", 0)
            transfer.receive_file(self.client.sock, local_path, file_size, progress_cb)
            
        self.after(0, self._post_transfer_cleanup)

    def _post_transfer_cleanup(self):
        self._set_buttons_state(tk.NORMAL)
        self._refresh_all()

    def _go_back(self):
        if self.client and self.client.connected:
            self.client.disconnect()
        log.removeHandler(self.queue_handler)
        self.go_back_callback()