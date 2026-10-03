import queue
import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox

from client.network import NetworkClient
from client.notifications import Notifier
from client.config import load_config, save_config
from client.history import History
from client.tray import Tray, STATUS_LABELS
from client.theme import apply_theme, status_style_for, MUTED, CARD, SUCCESS, WARNING, DANGER, TEXT, BORDER, ACCENT
from client.version import __version__
from client.resources import resource_path
from shared.protocol import MAX_MESSAGE_CHARS, FEATURES, FEATURE_STATUS

from client.frames.connect import ConnectFrame
from client.frames.username import UsernameFrame
from client.frames.mainframe import MainFrame
from client.frames.settings import SettingsDialog


# Seconds between reconnect attempts while auto-connect is on.
RECONNECT_DELAY = 10

DOT_COLORS = {
    "CardStatusOk.TLabel": SUCCESS,
    "CardStatusWarn.TLabel": WARNING,
    "CardStatusBad.TLabel": DANGER,
}


class App(tk.Tk):

    def __init__(self, start_hidden=False):
        super().__init__()
        self.version = __version__

        self.title(f"OfficeTalk {self.version}")
        self.geometry("780x640")
        self.minsize(620, 460)

        self._set_window_icon()

        self.fonts = apply_theme(self)

        self.network = NetworkClient()
        self.history = History()

        # Functions queued from background threads (tray menu, update
        # check, discovery) - run on the Tk thread by process_events().
        self._calls = queue.Queue()

        self.users = {}
        self.current_status = "available"
        self.current_frame = None

        # Load saved configuration.
        self.config_data = load_config()

        self.host = self.config_data["host"]
        self.port = self.config_data["port"]
        self.username = self.config_data["username"]

        self._connecting = False

        # True while we should sign in with the saved username as soon
        # as we connect, and keep retrying if the connection fails/drops.
        self._keep_connected = False
        self._reconnect_job = None

        self._tray_notice_shown = False

        self.status = tk.StringVar(
            value="Disconnected"
        )

        container = ttk.Frame(self)

        self.frames = {}

        for Frame in (
            ConnectFrame,
            UsernameFrame,
            MainFrame
        ):

            frame = Frame(
                container,
                self
            )

            self.frames[Frame.__name__] = frame

            frame.grid(
                row=0,
                column=0,
                sticky="nsew"
            )

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # -----------------------------
        # Status bar
        # -----------------------------

        status_bar = ttk.Frame(self, style="Card.TFrame")
        status_bar.pack(side="bottom", fill="x")

        separator = ttk.Frame(status_bar, height=1)
        separator.pack(side="top", fill="x")

        self.status_dot = tk.Canvas(
            status_bar,
            width=10,
            height=10,
            bg=CARD,
            highlightthickness=0
        )
        self.status_dot.pack(side="left", padx=(15, 6), pady=8)
        self._dot_id = self.status_dot.create_oval(1, 1, 9, 9, fill=MUTED, outline="")

        self.status_label = ttk.Label(
            status_bar,
            textvariable=self.status,
            style="CardMuted.TLabel"
        )

        self.status_label.pack(
            side="left",
            pady=8
        )
        container.pack(
                fill="both",
                expand=True
                )

        # Give the connection screen the saved values.
        self.frames["ConnectFrame"].host.set(
            self.host
        )

        self.frames["ConnectFrame"].port.set(
            str(self.port)
        )

        self.show_frame("ConnectFrame")
        self.set_status("Disconnected")

        self.tray = Tray(self)
        self.tray.start()

        if start_hidden:
            if self.tray.running:
                self.withdraw()
            else:
                self.iconify()

        if self.config_data.get("auto_connect") and self.username and self.host:
            self._keep_connected = True
            self.after(200, self._auto_connect)

        self.after(
            50,
            self.process_events
        )

        self.protocol(
            "WM_DELETE_WINDOW",
            self.on_close
        )

    def _set_window_icon(self):
        icon_path = resource_path("assets/logo.png")

        if not icon_path.exists():
            return

        try:
            # PhotoImage supports PNG natively since Tk 8.6 - no need for
            # an .ico conversion just to set the window/taskbar icon.
            # Keep a reference (self._icon_image) for the window's
            # lifetime - PhotoImage has no refcount tie to iconphoto(),
            # so without it Tk can garbage-collect it and the icon
            # silently reverts to the default.
            self._icon_image = tk.PhotoImage(file=str(icon_path))
            self.iconphoto(True, self._icon_image)

        except Exception as ex:
            print(f"[App] Could not set window icon: {ex}")

    def call_soon(self, func):
        """Thread-safe: run `func` on the Tk thread shortly."""
        self._calls.put(func)

    def save_settings(self):
        self.config_data["host"] = self.host
        self.config_data["port"] = int(self.port)
        self.config_data["username"] = self.username
        save_config(self.config_data)

    def show_frame(self, name):
        self.current_frame = name
        self.frames[name].tkraise()

    def set_status(self, text):
        self.status.set(text)

        style = status_style_for(text)
        self.status_label.configure(style=style)
        self.status_dot.itemconfig(self._dot_id, fill=DOT_COLORS.get(style, MUTED))

    # -----------------------------
    # Connection
    # -----------------------------

    def connect(self, host, port):

        if self._connecting or self.network.connected:
            return

        self._cancel_reconnect()

        self.host = host
        self.port = int(port)

        # Save server information immediately.
        self.save_settings()

        self._connecting = True

        self.set_status("Connecting...")
        self.frames["ConnectFrame"].set_connecting(True)

        self.network.connect(
            self.host,
            self.port
        )

    def _auto_connect(self):
        self._reconnect_job = None

        if self._keep_connected:
            self.connect(self.host, self.port)

    def _schedule_reconnect(self, reason):
        self._cancel_reconnect()
        self.set_status(f"{reason} - retrying in {RECONNECT_DELAY}s")
        self._reconnect_job = self.after(RECONNECT_DELAY * 1000, self._auto_connect)

    def _cancel_reconnect(self):
        if self._reconnect_job is not None:
            self.after_cancel(self._reconnect_job)
            self._reconnect_job = None

    def set_username(self, username):
        return self.network.set_username(
            username
        )

    def change_status(self, status):
        if status not in STATUS_LABELS:
            return

        self.current_status = status

        # Busy still works locally against an old server (no popups);
        # it just isn't shown to anyone else.
        if self.network.connected and FEATURE_STATUS in self.network.features:
            self.network.set_status(status)

        self.frames["MainFrame"].show_status(status)
        self.tray.set_tooltip(f"OfficeTalk — {STATUS_LABELS[status]}")

    def send_message(self, target, message):
        """Send one notification and record it in history. Returns False
        if it couldn't be sent at all (not connected)."""

        message = message[:MAX_MESSAGE_CHARS]

        if not self.network.send_notification(target, message):
            return False

        entry = self.history.add("out", target, message)
        self.frames["MainFrame"].history_added(entry)

        return True

    def disconnect(self):

        self._keep_connected = False
        self._cancel_reconnect()

        self.network.disconnect()

        self.users.clear()

        self.show_frame(
            "ConnectFrame"
        )

        self.set_status(
            "Disconnected"
        )

    # -----------------------------
    # Incoming messages
    # -----------------------------

    def handle_notification(self, sender, message):
        entry = self.history.add("in", sender, message)
        self.frames["MainFrame"].history_added(entry, unread=True)

        Notifier.notify(
            f"Message from {sender}",
            message or "(empty notification)"
        )

        # Busy: the native notification + history is enough - don't
        # steal focus or pop a dialog over whatever they're doing.
        if self.current_status == "busy":
            return

        self.bring_to_front()
        self.show_message_dialog(entry)

    def show_message_dialog(self, entry):
        """A small custom dialog (instead of messagebox.showinfo) so the
        message text is selectable, has an explicit Copy button, and can
        be replied to in place."""

        user = entry["user"]
        message = entry["message"]
        incoming = entry["direction"] == "in"

        try:
            when = datetime.fromisoformat(entry["time"]).strftime("%X")
        except (KeyError, ValueError):
            when = ""

        dialog = tk.Toplevel(self)
        dialog.title(f"Notification from {user}" if incoming else f"Message to {user}")
        dialog.configure(bg=CARD)
        dialog.transient(self)
        dialog.resizable(False, False)

        wrapper = ttk.Frame(dialog, style="Card.TFrame", padding=20)
        wrapper.pack(fill="both", expand=True)

        heading = f"From {user}" if incoming else f"To {user}"

        ttk.Label(
            wrapper,
            text=f"{heading} at {when}" if when else heading,
            style="CardHeading.TLabel"
        ).pack(anchor="w", pady=(0, 10))

        text = tk.Text(
            wrapper,
            width=44,
            height=6,
            wrap="word",
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER,
            bg=CARD,
            fg=TEXT,
            font=self.fonts["body"]
        )

        text.insert("1.0", message)
        text.configure(state="disabled")  # read-only, but still selectable/copyable
        text.pack(fill="both", expand=True, pady=(0, 14))

        # Reply box - hidden until Reply is clicked.
        reply_frame = ttk.Frame(wrapper, style="Card.TFrame")

        reply_text = tk.Text(
            reply_frame,
            width=44,
            height=3,
            wrap="word",
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=ACCENT,
            bg=CARD,
            fg=TEXT,
            insertbackground=TEXT,
            padx=8,
            pady=6,
            font=self.fonts["body"]
        )
        reply_text.pack(fill="x")

        reply_hint = ttk.Label(
            reply_frame,
            text="Ctrl+Enter to send",
            style="CardMuted.TLabel"
        )
        reply_hint.pack(anchor="w", pady=(4, 0))

        buttons = ttk.Frame(wrapper, style="Card.TFrame")
        buttons.pack(fill="x")

        def copy_message():
            self.clipboard_clear()
            self.clipboard_append(message)
            copy_button.config(text="Copied!")
            dialog.after(1200, lambda: copy_button.config(text="Copy"))

        def send_reply(event=None):
            body = reply_text.get("1.0", "end-1c")

            if self.send_message(user, body):
                self.set_status(f"Notification sent to {user}")
                dialog.destroy()
            else:
                reply_hint.config(text="Not connected - reply not sent.")

            return "break"

        def open_reply():
            reply_frame.pack(before=buttons, fill="x", pady=(0, 12))
            reply_button.config(text="Send", style="Accent.TButton", command=send_reply)
            close_button.config(text="Close", style="TButton")
            reply_text.focus_set()

        copy_button = ttk.Button(
            buttons,
            text="Copy",
            command=copy_message
        )
        copy_button.pack(side="left")

        close_button = ttk.Button(
            buttons,
            text="OK",
            style="Accent.TButton",
            command=dialog.destroy
        )
        close_button.pack(side="right")

        reply_button = ttk.Button(
            buttons,
            text="Reply" if incoming else "Send another",
            command=open_reply
        )
        reply_button.pack(side="right", padx=(0, 8))

        reply_text.bind("<Control-Return>", send_reply)
        dialog.bind("<Escape>", lambda e: dialog.destroy())

        # No grab_set(): several notifications can arrive back to back,
        # and a modal grab per dialog makes all but the newest unusable.
        dialog.focus_set()

    # -----------------------------
    # Event pump
    # -----------------------------

    def process_events(self):

        while not self._calls.empty():
            try:
                self._calls.get()()
            except Exception as ex:
                print(f"[App] Queued call failed: {ex}")

        while not self.network.events.empty():

            event = self.network.events.get()

            try:
                self.handle_event(event)
            except Exception as ex:
                print(f"[App] Error handling {event.get('type')}: {ex}")

        self.after(
            50,
            self.process_events
        )

    def handle_event(self, event):

        msg_type = event.get("type")

        if msg_type == "connect_result":

            self._connecting = False
            self.frames["ConnectFrame"].set_connecting(False)

            if not event.get("success"):
                if self._keep_connected:
                    self._schedule_reconnect("Could not reach server")
                    return

                messagebox.showerror(
                    "Connection Error",
                    event.get("error", "Could not connect to the server."),
                    parent=self
                )
                self.set_status("Disconnected")

        elif msg_type == "connected":

            self.set_status(
                "Connected"
            )

            # Only ask for features this server says it has. A v0.0.1
            # server sends no list, so it gets the original protocol.
            offered = event.get("features")
            wanted = set(offered) & set(FEATURES) if isinstance(offered, list) else set()

            self.network.request_features(wanted)
            self.frames["MainFrame"].set_server_features(self.network.features)

            # If a username was already saved,
            # pre-fill the username screen.
            username_frame = self.frames[
                "UsernameFrame"
            ]

            username_frame.username.set(
                self.username
            )

            self.show_frame(
                "UsernameFrame"
            )

            if self._keep_connected and self.username:
                username_frame.submit()

        elif msg_type == "username_result":

            username_frame = self.frames["UsernameFrame"]
            username_frame.on_result(event)

            if not event.get("success"):
                # Saved name got taken - stop auto-signing-in and let
                # them pick another one.
                self._keep_connected = False
                self.show_frame("UsernameFrame")
                return

            self.username = event.get("username", self.username)
            self.save_settings()

            if self.config_data.get("auto_connect"):
                self._keep_connected = True

            if self.current_status != "available" and FEATURE_STATUS in self.network.features:
                self.network.set_status(self.current_status)

            self.show_frame("MainFrame")

        elif msg_type == "user_list":

            self.users = {}

            for user in event["users"]:

                self.users[
                    user["username"]
                ] = user

            self.frames[
                "MainFrame"
            ].update_users(
                event["users"]
            )

        elif msg_type == "notification":

            self.handle_notification(
                event.get("from", "?"),
                event.get("message", "")
            )

        elif msg_type == "notify_result":

            self.frames["MainFrame"].on_notify_result(event)

        elif msg_type == "error":

            # A dropped connection is reported by the "disconnected"
            # event that always follows - no need for two dialogs.
            print(f"[App] Network error: {event.get('message')}")

        elif msg_type == "disconnected":

            voluntary = event.get("voluntary", False)

            self.users.clear()
            self.frames["UsernameFrame"].on_disconnected()

            self.show_frame(
                "ConnectFrame"
            )

            if voluntary:
                self.set_status("Disconnected")
            elif self._keep_connected:
                self._schedule_reconnect("Connection lost")
            else:
                self.set_status("Connection lost")

                messagebox.showwarning(
                    "Connection Lost",
                    "The connection to the server was lost.",
                    parent=self
                )

    # -----------------------------
    # Window management
    # -----------------------------

    def open_settings(self):
        SettingsDialog(self)

    def bring_to_front(self):

        self.deiconify()

        self.lift()

        self.focus_force()

        self.attributes(
            "-topmost",
            True
        )

        self.after(
            200,
            lambda: self.attributes(
                "-topmost",
                False
            )
        )

    def show_window(self):
        self.deiconify()
        self.lift()
        self.focus_force()

    def on_close(self):

        if self.tray.running and self.config_data.get("close_to_tray", True):
            self.withdraw()

            if not self._tray_notice_shown:
                self._tray_notice_shown = True
                Notifier.notify(
                    "OfficeTalk is still running",
                    "It's in the system tray - right-click the icon to quit."
                )
            return

        self.quit_app()

    def quit_app(self):

        try:
            self.network.disconnect()

        except Exception:
            pass

        self.tray.stop()

        self.destroy()
