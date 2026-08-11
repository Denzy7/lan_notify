import tkinter as tk
from tkinter import ttk, messagebox

from client.network import NetworkClient
from client.notifications import Notifier
from client.config import load_config, save_config

from client.frames.connect import ConnectFrame
from client.frames.username import UsernameFrame
from client.frames.mainframe import MainFrame


class App(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("LAN Notify")
        self.geometry("700x500")

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

        container.pack(
            fill="both",
            expand=True
        )

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

        status = ttk.Label(
            self,
            textvariable=self.status,
            anchor="w"
        )

        status.pack(
            side="bottom",
            fill="x"
        )

        # Give the connection screen the saved values.
        self.frames["ConnectFrame"].host.set(
            self.host
        )

        self.frames["ConnectFrame"].port.set(
            str(self.port)
        )

        self.show_frame("ConnectFrame")

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

        try:

            self.network.connect(
                self.host,
                self.port
            )

        except Exception as ex:

            messagebox.showerror(
                "Connection Error",
                str(ex)
            )

            self.set_status(
                "Disconnected"
            )

    def set_username(self, username):

        self.username = username

        # Save username immediately.
        save_config(
            self.host,
            self.port,
            self.username
        )

        self.network.set_username(
            username
        )

    def send_notification(
        self,
        target,
        message
    ):

        self.network.send_notification(
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

    def process_events(self):

        while not self.network.events.empty():

            event = self.network.events.get()

            msg_type = event.get("type")

            if msg_type == "connected":

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

                messagebox.showinfo(
                    f"Notification from {sender}",
                    message,
                    parent=self
                )

            elif msg_type == "error":

                messagebox.showerror(
                    "Error",
                    event["message"],
                    parent=self
                )

            elif msg_type == "disconnected":

                self.set_status(
                    "Disconnected"
                )

                self.show_frame(
                    "ConnectFrame"
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
