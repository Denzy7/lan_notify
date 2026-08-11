import tkinter as tk
from tkinter import ttk


class UsernameFrame(ttk.Frame):

    def __init__(self, parent, app):
        super().__init__(parent)

        self.app = app

        self.username = tk.StringVar(
            value=app.username
        )

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        outer = ttk.Frame(self)
        outer.grid(row=0, column=0)

        ttk.Label(
            outer,
            text="\U0001F4E7",
            font=("Segoe UI Emoji", 36)
        ).pack(pady=(0, 6))

        ttk.Label(
            outer,
            text="Choose a Username",
            style="Title.TLabel"
        ).pack(pady=(0, 4))

        ttk.Label(
            outer,
            text="Other people on the network will see this name",
            style="Muted.TLabel"
        ).pack(pady=(0, 24))

        card = ttk.Frame(outer, style="Card.TFrame", padding=24)
        card.pack()

        self.entry = ttk.Entry(
            card,
            textvariable=self.username,
            width=30
        )

        self.entry.pack(pady=(0, 4))

        self.entry.bind(
            "<Return>",
            lambda event: self.submit()
        )

        self.hint = ttk.Label(
            card,
            text="",
            style="CardMuted.TLabel"
        )
        self.hint.pack(pady=(2, 14))

        self.submit_button = ttk.Button(
            card,
            text="Continue",
            style="Accent.TButton",
            command=self.submit
        )

        self.submit_button.pack(fill="x")

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)

        self.after(
            100,
            self.focus_username
        )

    def focus_username(self):
        self.entry.focus_set()
        self.entry.selection_range(0, tk.END)

    def submit(self):
        # The connection can drop while this screen is showing (e.g. the
        # server closed, or the heartbeat timed out). Sending a stale
        # username request would silently fail, so bail out clearly
        # instead of moving on to the main screen as if we'd succeeded.
        if not self.app.network.connected:
            self.hint.config(text="Not connected to the server.")
            return

        username = self.username.get().strip()

        if not username:
            self.hint.config(text="Username cannot be empty.")
            return

        if len(username) > 32:
            self.hint.config(text="Username is too long.")
            return

        self.submit_button.config(
            state="disabled"
        )

        sent = self.app.set_username(
            username
        )

        self.submit_button.config(
            state="normal"
        )

        if not sent:
            self.hint.config(text="Not connected to the server.")
            return

        self.hint.config(text="")
        self.app.username_accepted()
