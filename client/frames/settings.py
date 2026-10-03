import tkinter as tk
from tkinter import ttk

from client import autostart
from client.config import DEFAULT_QUICK_MESSAGES
from client.theme import BORDER, ACCENT, CARD, TEXT


class SettingsDialog(tk.Toplevel):

    def __init__(self, app):
        super().__init__(app)

        self.app = app
        config = app.config_data

        self.title("Settings")
        self.configure(bg=CARD)
        self.transient(app)
        self.resizable(False, False)

        self.start_on_login = tk.BooleanVar(value=autostart.is_enabled())
        self.auto_connect = tk.BooleanVar(value=bool(config.get("auto_connect")))
        self.close_to_tray = tk.BooleanVar(value=bool(config.get("close_to_tray", True)))

        wrapper = ttk.Frame(self, style="Card.TFrame", padding=20)
        wrapper.pack(fill="both", expand=True)

        ttk.Label(
            wrapper,
            text="Startup",
            style="CardHeading.TLabel"
        ).pack(anchor="w", pady=(0, 6))

        start_check = ttk.Checkbutton(
            wrapper,
            text="Start OfficeTalk when I log in",
            variable=self.start_on_login,
            style="Card.TCheckbutton",
            command=self._on_start_on_login_toggled
        )
        start_check.pack(anchor="w", pady=2)

        if not autostart.is_supported():
            start_check.config(state="disabled")

        ttk.Checkbutton(
            wrapper,
            text="Connect and sign in automatically (and reconnect if dropped)",
            variable=self.auto_connect,
            style="Card.TCheckbutton"
        ).pack(anchor="w", pady=2)

        tray_check = ttk.Checkbutton(
            wrapper,
            text="Closing the window keeps OfficeTalk running in the tray",
            variable=self.close_to_tray,
            style="Card.TCheckbutton"
        )
        tray_check.pack(anchor="w", pady=2)

        if not app.tray.running:
            tray_check.config(state="disabled")
            ttk.Label(
                wrapper,
                text="Tray icon unavailable (install pystray to enable it).",
                style="CardMuted.TLabel"
            ).pack(anchor="w", padx=(24, 0))

        ttk.Label(
            wrapper,
            text="Quick messages",
            style="CardHeading.TLabel"
        ).pack(anchor="w", pady=(18, 2))

        ttk.Label(
            wrapper,
            text="One per line - shown in the \"Quick message\" menu.",
            style="CardMuted.TLabel"
        ).pack(anchor="w", pady=(0, 6))

        self.quick_text = tk.Text(
            wrapper,
            width=48,
            height=7,
            wrap="none",
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=ACCENT,
            bg=CARD,
            fg=TEXT,
            insertbackground=TEXT,
            padx=8,
            pady=6,
            font=app.fonts["body"]
        )
        self.quick_text.insert("1.0", "\n".join(config.get("quick_messages", [])))
        self.quick_text.pack(fill="x")

        self.error_label = ttk.Label(wrapper, text="", style="CardMuted.TLabel")
        self.error_label.pack(anchor="w", pady=(8, 0))

        buttons = ttk.Frame(wrapper, style="Card.TFrame")
        buttons.pack(fill="x", pady=(8, 0))

        ttk.Button(
            buttons,
            text="Reset messages",
            command=self._reset_quick_messages
        ).pack(side="left")

        ttk.Button(
            buttons,
            text="Save",
            style="Accent.TButton",
            command=self.save
        ).pack(side="right")

        ttk.Button(
            buttons,
            text="Cancel",
            command=self.destroy
        ).pack(side="right", padx=(0, 8))

        self.bind("<Escape>", lambda e: self.destroy())
        self.focus_set()

    def _on_start_on_login_toggled(self):
        # Starting on login is pointless if you then have to click
        # through Connect + username every morning.
        if self.start_on_login.get():
            self.auto_connect.set(True)

    def _reset_quick_messages(self):
        self.quick_text.delete("1.0", "end")
        self.quick_text.insert("1.0", "\n".join(DEFAULT_QUICK_MESSAGES))

    def save(self):
        config = self.app.config_data

        if self.start_on_login.get() != autostart.is_enabled():
            if not autostart.set_enabled(self.start_on_login.get()):
                self.error_label.config(text="Could not change the start-on-login setting.")
                return

        config["auto_connect"] = self.auto_connect.get()
        config["close_to_tray"] = self.close_to_tray.get()

        # Applies to the current session too: reconnect if it drops.
        self.app._keep_connected = config["auto_connect"] and self.app.network.connected

        lines = self.quick_text.get("1.0", "end").splitlines()
        config["quick_messages"] = [line.strip() for line in lines if line.strip()]

        self.app.save_settings()
        self.destroy()
