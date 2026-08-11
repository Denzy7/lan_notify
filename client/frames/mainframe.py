import tkinter as tk
from tkinter import ttk


class MainFrame(ttk.Frame):

    def __init__(self, parent, app):
        super().__init__(parent)

        self.app = app

        self.selected_user = None

        # -----------------------------
        # Header
        # -----------------------------

        header = ttk.Frame(self)
        header.pack(
            fill="x",
            padx=15,
            pady=15
        )

        self.username_label = ttk.Label(
            header,
            text="",
            font=("TkDefaultFont", 14, "bold")
        )

        self.username_label.pack(
            side="left"
        )

        # -----------------------------
        # Users
        # -----------------------------

        ttk.Label(
            self,
            text="Connected Users"
        ).pack(
            anchor="w",
            padx=15
        )

        users_frame = ttk.Frame(self)
        users_frame.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=5
        )

        self.tree = ttk.Treeview(
            users_frame,
            columns=("username", "ip"),
            show="headings",
            selectmode="browse"
        )

        self.tree.heading(
            "username",
            text="Username"
        )

        self.tree.heading(
            "ip",
            text="IP Address"
        )

        self.tree.column(
            "username",
            width=250
        )

        self.tree.column(
            "ip",
            width=250
        )

        scrollbar = ttk.Scrollbar(
            users_frame,
            orient="vertical",
            command=self.tree.yview
        )

        self.tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.tree.bind(
            "<<TreeviewSelect>>",
            self.user_selected
        )

        # -----------------------------
        # Selected user
        # -----------------------------

        self.selected_label = ttk.Label(
            self,
            text="No user selected"
        )

        self.selected_label.pack(
            anchor="w",
            padx=15,
            pady=(5, 0)
        )

        # -----------------------------
        # Message
        # -----------------------------

        ttk.Label(
            self,
            text="Message"
        ).pack(
            anchor="w",
            padx=15,
            pady=(10, 0)
        )

        self.message = tk.Text(
            self,
            height=4,
            wrap="word"
        )

        self.message.pack(
            fill="x",
            padx=15,
            pady=5
        )

        self.message.bind(
            "<Control-Return>",
            self.send
        )

        # -----------------------------
        # Buttons
        # -----------------------------

        buttons = ttk.Frame(self)
        buttons.pack(
            fill="x",
            padx=15,
            pady=10
        )

        self.send_button = ttk.Button(
            buttons,
            text="Send Notification",
            command=self.send,
            state="disabled"
        )

        self.send_button.pack(
            side="left"
        )

        ttk.Button(
            buttons,
            text="Disconnect",
            command=self.disconnect
        ).pack(
            side="right"
        )

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)

        self.username_label.config(
            text=f"Username: {self.app.username}"
        )

    def update_users(self, users):
        self.tree.delete(
            *self.tree.get_children()
        )

        self.selected_user = None

        self.selected_label.config(
            text="No user selected"
        )

        self.send_button.config(
            state="disabled"
        )

        for user in users:

            username = user.get("username", "")
            ip = user.get("ip", "")

            # Don't show ourselves.
            if username == self.app.username:
                continue

            self.tree.insert(
                "",
                "end",
                values=(username, ip)
            )

    def user_selected(self, event=None):
        selection = self.tree.selection()

        if not selection:
            self.selected_user = None

            self.selected_label.config(
                text="No user selected"
            )

            self.send_button.config(
                state="disabled"
            )

            return

        item = self.tree.item(
            selection[0]
        )

        values = item.get("values", [])

        if not values:
            return

        self.selected_user = str(values[0])

        self.selected_label.config(
            text=f"Selected: {self.selected_user}"
        )

        self.send_button.config(
            state="normal"
        )

        self.message.focus_set()

    def send(self, event=None):
        if not self.selected_user:
            return

        message = self.message.get(
            "1.0",
            "end-1c"
        )

        # Empty messages are intentionally allowed.
        self.app.send_notification(
            self.selected_user,
            message
        )

        self.message.delete(
            "1.0",
            "end"
        )

        self.app.set_status(
            f"Notification sent to {self.selected_user}"
        )

        return "break"

    def disconnect(self):
        self.app.disconnect()
