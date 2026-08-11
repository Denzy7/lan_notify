import tkinter as tk
from tkinter import ttk


class ConnectFrame(ttk.Frame):

    def __init__(self, parent, app):
        super().__init__(parent)

        self.app = app

        self.host = tk.StringVar(value="127.0.0.1")
        self.port = tk.StringVar(value="5000")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Centered card.
        outer = ttk.Frame(self)
        outer.grid(row=0, column=0)

        ttk.Label(
            outer,
            text="\U0001F4E1",
            font=("Segoe UI Emoji", 40),
            style="TLabel"
        ).pack(pady=(0, 6))

        ttk.Label(
            outer,
            text="LAN Notify",
            style="Title.TLabel"
        ).pack(pady=(0, 4))

        ttk.Label(
            outer,
            text="Connect to a notification server on your network",
            style="Muted.TLabel"
        ).pack(pady=(0, 28))

        card = ttk.Frame(outer, style="Card.TFrame", padding=24)
        card.pack()

        form = ttk.Frame(card, style="Card.TFrame")
        form.pack()

        ttk.Label(
            form,
            text="Server Address",
            style="CardMuted.TLabel"
        ).grid(row=0, column=0, sticky="w", pady=(0, 4))

        ttk.Entry(
            form,
            textvariable=self.host,
            width=30
        ).grid(row=1, column=0, pady=(0, 14))

        ttk.Label(
            form,
            text="Port",
            style="CardMuted.TLabel"
        ).grid(row=2, column=0, sticky="w", pady=(0, 4))

        ttk.Entry(
            form,
            textvariable=self.port,
            width=30
        ).grid(row=3, column=0, pady=(0, 4))

        self.connect_button = ttk.Button(
            card,
            text="Connect",
            style="Accent.TButton",
            command=self.connect
        )

        self.connect_button.pack(fill="x", pady=(18, 0))

        self.hint = ttk.Label(
            card,
            text="",
            style="CardMuted.TLabel"
        )

        self.hint.pack(pady=(10, 0))

        for entry in form.winfo_children():
            if isinstance(entry, ttk.Entry):
                entry.bind("<Return>", lambda e: self.connect())

    def set_connecting(self, connecting):
        """Reflect the real connection-attempt state, driven by network
        results rather than a fixed timer guessing when it's safe."""

        if connecting:
            self.connect_button.config(state="disabled", text="Connecting...")
            self.hint.config(text="Reaching out to the server...")
        else:
            self.connect_button.config(state="normal", text="Connect")
            self.hint.config(text="")

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

        self.app.connect(host, port)
