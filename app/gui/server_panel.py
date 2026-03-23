# jacammander/app/gui/server_panel.py

import os
import queue
import logging
import tkinter as tk
from tkinter import filedialog, messagebox
from app.common import constants
from app.net.server import JacammanderServer
from app.debug.logger import get_logger
from app.config import settings

log = get_logger()

class QueueHandler(logging.Handler):
    """Custom logging handler that drops log messages into a thread-safe queue."""
    def __init__(self, log_queue):
        logging.Handler.__init__(self)
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(self.format(record))

class ServerPanel(tk.Frame):
    def __init__(self, parent, go_back_callback):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.go_back_callback = go_back_callback
        
        self.server = None
        self.log_queue = queue.Queue()
        
        self._setup_ui()
        self._setup_logging()
        self._poll_log_queue()

    def _setup_ui(self):
        cfg = settings.load()

        # --- Top Config Frame ---
        config_frame = tk.LabelFrame(self, text="Server Configuration", padx=10, pady=10)
        config_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Shared Folder
        tk.Label(config_frame, text="Shared Root Folder:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.path_var = tk.StringVar(value=cfg.get("server_root"))
        self.path_entry = tk.Entry(config_frame, textvariable=self.path_var, width=50)
        self.path_entry.grid(row=0, column=1, padx=5, pady=2, sticky=tk.EW)
        
        btn_browse = tk.Button(config_frame, text="Browse...", command=self._browse_folder)
        btn_browse.grid(row=0, column=2, padx=5, pady=2)
        
        # Port and Password
        tk.Label(config_frame, text="Port:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.port_var = tk.StringVar(value=cfg.get("server_port"))
        tk.Entry(config_frame, textvariable=self.port_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=5)
        
        tk.Label(config_frame, text="Password (Optional):").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.pass_var = tk.StringVar()
        tk.Entry(config_frame, textvariable=self.pass_var, width=20, show="*").grid(row=2, column=1, sticky=tk.W, padx=5)
        
        # Make the path entry expand if the window gets wider
        config_frame.grid_columnconfigure(1, weight=1)

        # --- Controls Frame ---
        control_frame = tk.Frame(self)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.btn_start = tk.Button(control_frame, text="Start Server", bg="lightgreen", width=15, command=self._start_server)
        self.btn_start.pack(side=tk.LEFT, padx=5)
        
        self.btn_stop = tk.Button(control_frame, text="Stop Server", bg="lightcoral", width=15, state=tk.DISABLED, command=self._stop_server)
        self.btn_stop.pack(side=tk.LEFT, padx=5)
        
        btn_back = tk.Button(control_frame, text="< Back to Menu", command=self._go_back)
        btn_back.pack(side=tk.RIGHT, padx=5)

        # --- Log Frame ---
        log_frame = tk.LabelFrame(self, text="Server Console")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        log_btn_frame = tk.Frame(log_frame)
        log_btn_frame.pack(fill=tk.X, padx=5, pady=2)
        
        btn_copy = tk.Button(log_btn_frame, text="Copy Log", command=self._copy_log)
        btn_copy.pack(side=tk.LEFT)
        btn_clear = tk.Button(log_btn_frame, text="Clear Log", command=self._clear_log)
        btn_clear.pack(side=tk.LEFT, padx=5)
        
        # The Scrollbar and Text Widget
        self.log_text = tk.Text(log_frame, height=15, state=tk.DISABLED, bg="#f0f0f0")
        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _setup_logging(self):
        """Hooks the app's master logger into our local Tkinter queue."""
        self.queue_handler = QueueHandler(self.log_queue)
        formatter = logging.Formatter('[%(levelname)s] %(asctime)s - %(message)s', datefmt='%H:%M:%S')
        self.queue_handler.setFormatter(formatter)
        log.addHandler(self.queue_handler)

    def _poll_log_queue(self):
        """Checks the queue for new log messages and prints them safely."""
        while not self.log_queue.empty():
            msg = self.log_queue.get()
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, msg + "\n")
            self.log_text.see(tk.END) # Auto-scroll to bottom
            self.log_text.config(state=tk.DISABLED)
        
        # Schedule the next check in 100ms
        self.after(100, self._poll_log_queue)

    def _browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.path_var.get(), title="Select Root Folder")
        if folder:
            self.path_var.set(folder)

    def _start_server(self):
        root_dir = self.path_var.get()
        if not os.path.exists(root_dir):
            try:
                os.makedirs(root_dir)
            except OSError as e:
                messagebox.showerror("Error", "Cannot create root directory: {0}".format(e))
                return
                
        try:
            port = int(self.port_var.get())
        except ValueError:
            messagebox.showerror("Error", "Port must be a number.")
            return

        pwd = self.pass_var.get()
        
        # Save settings for next time
        settings.save({
            "server_root": root_dir,
            "server_port": str(port)
        })
        
        self.server = JacammanderServer(port, root_dir, password=pwd)
        self.server.start()
        
        # Lock the UI inputs while running
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.path_entry.config(state=tk.DISABLED)

    def _stop_server(self):
        if self.server:
            self.server.stop()
            self.server = None
            
        # Unlock the UI
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.path_entry.config(state=tk.NORMAL)

    def _copy_log(self):
        self.parent.clipboard_clear()
        self.parent.clipboard_append(self.log_text.get("1.0", tk.END))
        
    def _clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _go_back(self):
        self._stop_server()
        log.removeHandler(self.queue_handler) # Clean up the logger hook
        self.go_back_callback()