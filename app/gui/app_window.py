# jacammander/app/gui/app_window.py

import tkinter as tk
from app.common.constants import APP_NAME, APP_VERSION
from app.gui.server_panel import ServerPanel
from app.gui.client_panel import ClientPanel

class JacammanderApp(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("{0} v{1}".format(APP_NAME, APP_VERSION))
        
        # Default starting size, but allow the user to resize it dynamically
        self.geometry("750x500")
        self.minsize(500, 400)
        
        self.current_panel = None
        self.show_chooser()

    def show_chooser(self):
        """Displays the initial mode selection screen."""
        if self.current_panel:
            self.current_panel.destroy()
            
        self.current_panel = tk.Frame(self)
        self.current_panel.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Center everything in the chooser
        self.current_panel.grid_rowconfigure(0, weight=1)
        self.current_panel.grid_rowconfigure(3, weight=1)
        self.current_panel.grid_columnconfigure(0, weight=1)
        
        lbl = tk.Label(self.current_panel, text="Select Operating Mode", font=("Arial", 16, "bold"))
        lbl.grid(row=1, column=0, pady=20)
        
        btn_frame = tk.Frame(self.current_panel)
        btn_frame.grid(row=2, column=0)
        
        # Big chunky buttons
        btn_server = tk.Button(btn_frame, text="Run as Server\n(Share files)", 
                               width=20, height=3, command=self.load_server)
        btn_server.pack(side=tk.LEFT, padx=10)
        
        btn_client = tk.Button(btn_frame, text="Run as Client\n(Browse and Transfer)", 
                               width=20, height=3, command=self.load_client)
        btn_client.pack(side=tk.LEFT, padx=10)

    def load_server(self):
        """Loads the walled-garden server control panel."""
        if self.current_panel:
            self.current_panel.destroy()
        self.current_panel = ServerPanel(self, self.show_chooser)
        self.current_panel.pack(fill=tk.BOTH, expand=True)

    def load_client(self):
        """Loads the dual-pane remote file browser and transfer tool."""
        if self.current_panel:
            self.current_panel.destroy()
        self.current_panel = ClientPanel(self, self.show_chooser)
        self.current_panel.pack(fill=tk.BOTH, expand=True)