import tkinter as tk
from tkinter import ttk


class ConnectFrame(ttk.Frame):

    def __init__(self, parent, app):
        super().__init__(parent)

        self.app = app

        self.host = tk.StringVar(value="127.0.0.1")
        self.port = tk.StringVar(value="5000")

        ttk.Label(
            self,
            text="LAN Notify",
            font=("TkDefaultFont", 20, "bold")
        ).pack(pady=(50, 30))

        form = ttk.Frame(self)
        form.pack()

        ttk.Label(
            form,
            text="Server Address:"
        ).grid(row=0, column=0, sticky="w", pady=5)

        ttk.Entry(
            form,
            textvariable=self.host,
            width=30
        ).grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(
            form,
            text="Port:"
        ).grid(row=1, column=0, sticky="w", pady=5)

        ttk.Entry(
            form,
            textvariable=self.port,
            width=30
        ).grid(row=1, column=1, padx=10, pady=5)

        self.connect_button = ttk.Button(
            self,
            text="Connect",
            command=self.connect
        )

        self.connect_button.pack(pady=25)

    def connect(self):
        host = self.host.get().strip()
        port = self.port.get().strip()

        if not host:
            self.app.set_status("Enter a server address")
            return

        try:
            port = int(port)

            if not 1 <= port <= 65535:
                raise ValueError

        except ValueError:
            self.app.set_status("Invalid port")
            return

        self.connect_button.config(
            state="disabled"
        )

        self.app.connect(host, port)

        # Re-enable the button shortly afterward.
        # If the connection succeeds, the frame will no longer
        # be visible anyway.
        self.after(
            1000,
            lambda: self.connect_button.config(
                state="normal"
            )
        )
