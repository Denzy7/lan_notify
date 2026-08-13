import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox

from client.network import NetworkClient
from client.notifications import Notifier
from client.config import load_config, save_config
from client.theme import apply_theme, status_style_for, MUTED, CARD, SUCCESS, WARNING, DANGER, TEXT, BORDER
from client.version import __version__

from client.frames.connect import ConnectFrame
from client.frames.username import UsernameFrame
from client.frames.mainframe import MainFrame


class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.version = __version__

        self.title(f"OfficeTalk {self.version}")
        self.geometry("760x560")
        self.minsize(620, 460)

        self.fonts = apply_theme(self)

        self.network = NetworkClient()

        self.users = {}
        self.username = ""

        # Load saved configuration.
        config = load_config()

        self.host = config["host"]
        self.port = config["port"]
        self.username = config["username"]

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

        self.after(
            50,
            self.process_events
        )

        self.protocol(
            "WM_DELETE_WINDOW",
            self.on_close
        )

    def show_frame(self, name):
        self.frames[name].tkraise()

    def set_status(self, text):
        self.status.set(text)
        self.status_label.configure(style=status_style_for(text))

        lowered = text.lower()

        if lowered == "connected":
            dot_color = SUCCESS
        elif "connecting" in lowered:
            dot_color = WARNING
        elif "lost" in lowered or "error" in lowered or "failed" in lowered:
            dot_color = DANGER
        else:
            dot_color = MUTED

        self.status_dot.itemconfig(self._dot_id, fill=dot_color)

    def connect(self, host, port):

        self.host = host
        self.port = int(port)

        # Save server information immediately.
        save_config(
            self.host,
            self.port,
            self.username
        )

        self.set_status("Connecting...")
        self.frames["ConnectFrame"].set_connecting(True)

        self.network.connect(
            self.host,
            self.port
        )

    def set_username(self, username):

        self.username = username

        # Save username immediately.
        save_config(
            self.host,
            self.port,
            self.username
        )

        return self.network.set_username(
            username
        )

    def send_notification(
        self,
        target,
        message
    ):

        return self.network.send_notification(
            target,
            message
        )

    def disconnect(self):

        self.network.disconnect()

        self.users.clear()

        self.show_frame(
            "ConnectFrame"
        )

        self.set_status(
            "Disconnected"
        )

    def show_notification_dialog(self, sender, message):
        """A small custom dialog (instead of messagebox.showinfo) so the
        message text is selectable and has an explicit Copy button —
        plain tk message boxes don't offer that reliably on every OS."""

        dialog = tk.Toplevel(self)
        dialog.title(f"Notification from {sender}")
        dialog.configure(bg=CARD)
        dialog.transient(self)
        dialog.resizable(False, False)

        wrapper = ttk.Frame(dialog, style="Card.TFrame", padding=20)
        wrapper.pack(fill="both", expand=True)

        ttk.Label(
            wrapper,
            text=f"From {sender} at {datetime.now().strftime("%X")}",
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
            font=("Segoe UI", 10)
        )

        text.insert("1.0", message)
        text.configure(state="disabled")  # read-only, but still selectable/copyable
        text.pack(fill="both", expand=True, pady=(0, 14))

        buttons = ttk.Frame(wrapper, style="Card.TFrame")
        buttons.pack(fill="x")

        def copy_message():
            self.clipboard_clear()
            self.clipboard_append(message)
            copy_button.config(text="Copied!")
            dialog.after(1200, lambda: copy_button.config(text="Copy"))

        copy_button = ttk.Button(
            buttons,
            text="Copy",
            command=copy_message
        )
        copy_button.pack(side="left")

        ttk.Button(
            buttons,
            text="OK",
            style="Accent.TButton",
            command=dialog.destroy
        ).pack(side="right")

        dialog.bind("<Escape>", lambda e: dialog.destroy())
        dialog.grab_set()
        dialog.focus_set()

    def process_events(self):

        while not self.network.events.empty():

            event = self.network.events.get()

            msg_type = event.get("type")

            if msg_type == "connect_result":

                self.frames["ConnectFrame"].set_connecting(False)

                if not event.get("success"):
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

                sender = event["from"]
                message = event["message"]

                self.bring_to_front()

                Notifier.notify(
                    f"Message from {sender}",
                    message
                )

                self.show_notification_dialog(sender, message)

            elif msg_type == "error":

                messagebox.showerror(
                    "Error",
                    event.get(
                        "message",
                        "Unknown error"
                    ),
                    parent=self
                )

            elif msg_type == "disconnected":

                voluntary = event.get("voluntary", False)

                self.users.clear()

                self.show_frame(
                    "ConnectFrame"
                )

                if voluntary:
                    self.set_status("Disconnected")
                else:
                    self.set_status("Connection lost")

                    messagebox.showwarning(
                        "Connection Lost",
                        "The connection to the server was lost.",
                        parent=self
                    )

        self.after(
            50,
            self.process_events
        )

    def username_accepted(self):

        self.show_frame(
            "MainFrame"
        )

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

    def on_close(self):

        try:
            self.network.disconnect()

        except Exception:
            pass

        self.destroy()
