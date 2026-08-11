import tkinter as tk
from tkinter import ttk


class UsernameFrame(ttk.Frame):

    def __init__(self, parent, app):
        super().__init__(parent)

        self.app = app

        self.username = tk.StringVar(
            value=app.username
        )

        ttk.Label(
            self,
            text="Choose Username",
            font=("TkDefaultFont", 18, "bold")
        ).pack(pady=(60, 30))

        ttk.Label(
            self,
            text="Username:"
        ).pack()

        entry = ttk.Entry(
            self,
            textvariable=self.username,
            width=30
        )

        entry.pack(pady=10)

        entry.bind(
            "<Return>",
            lambda event: self.submit()
        )

        self.submit_button = ttk.Button(
            self,
            text="Continue",
            command=self.submit
        )

        self.submit_button.pack(pady=15)

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)

        self.after(
            100,
            self.focus_username
        )

    def focus_username(self):
        for child in self.winfo_children():
            if isinstance(child, ttk.Entry):
                child.focus_set()
                child.selection_range(
                    0,
                    tk.END
                )
                break

    def submit(self):
        username = self.username.get().strip()

        if not username:
            self.app.set_status(
                "Username cannot be empty"
            )
            return

        if len(username) > 32:
            self.app.set_status(
                "Username is too long"
            )
            return

        self.submit_button.config(
            state="disabled"
        )

        self.app.set_username(
            username
        )

        self.app.username_accepted()

        self.submit_button.config(
            state="normal"
        )
