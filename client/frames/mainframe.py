import tkinter as tk
from tkinter import ttk

from client.theme import BORDER, ACCENT, CARD, TEXT, BG


class MainFrame(ttk.Frame):

    def __init__(self, parent, app):
        super().__init__(parent)

        self.app = app

        self.selected_user = None

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Scrollable content area: on small/short windows the users list +
        # message box + button can be taller than the window, which was
        # clipping the Send button. A canvas + scrollbar lets it scroll
        # instead of just disappearing off the bottom.
        canvas = tk.Canvas(self, background=BG, highlightthickness=0)
        canvas.grid(row=0, column=0, sticky="nsew")

        v_scroll = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        v_scroll.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=v_scroll.set)

        wrapper = ttk.Frame(canvas, padding=20)
        wrapper_id = canvas.create_window((0, 0), window=wrapper, anchor="nw")
        wrapper.columnconfigure(0, weight=1)
        wrapper.rowconfigure(2, weight=1)

        def _on_wrapper_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_configure(event):
            # Keep the inner frame exactly as wide as the visible canvas.
            canvas.itemconfig(wrapper_id, width=event.width)

        wrapper.bind("<Configure>", _on_wrapper_configure)
        canvas.bind("<Configure>", _on_canvas_configure)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)   # Windows / macOS
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))  # Linux
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))   # Linux

        # -----------------------------
        # Header
        # -----------------------------

        header = ttk.Frame(wrapper)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        header.columnconfigure(0, weight=1)

        title_box = ttk.Frame(header)
        title_box.grid(row=0, column=0, sticky="w")

        ttk.Label(
            title_box,
            text="LAN Notify",
            style="Heading.TLabel"
        ).pack(side="left")

        self.username_label = ttk.Label(
            title_box,
            text="",
            style="Muted.TLabel"
        )

        self.username_label.pack(side="left", padx=(10, 0))

        ttk.Button(
            header,
            text="Disconnect",
            style="Danger.TButton",
            command=self.disconnect
        ).grid(row=0, column=1, sticky="e")

        # -----------------------------
        # Users
        # -----------------------------

        users_card = ttk.Frame(wrapper, style="Card.TFrame", padding=16)
        users_card.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        users_card.columnconfigure(0, weight=1)

        ttk.Label(
            users_card,
            text="Connected Users",
            style="CardHeading.TLabel"
        ).grid(row=0, column=0, sticky="w", pady=(0, 10))

        tree_frame = ttk.Frame(users_card, style="Card.TFrame")
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            tree_frame,
            columns=("username", "ip"),
            show="headings",
            selectmode="browse",
            height=6
        )

        self.tree.heading(
            "username",
            text="USERNAME"
        )

        self.tree.heading(
            "ip",
            text="IP ADDRESS"
        )

        self.tree.column(
            "username",
            width=280
        )

        self.tree.column(
            "ip",
            width=200
        )

        scrollbar = ttk.Scrollbar(
            tree_frame,
            orient="vertical",
            command=self.tree.yview
        )

        self.tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.empty_label = ttk.Label(
            users_card,
            text="No one else is online right now.",
            style="CardMuted.TLabel"
        )

        self.tree.bind(
            "<<TreeviewSelect>>",
            self.user_selected
        )

        # -----------------------------
        # Message
        # -----------------------------

        message_card = ttk.Frame(wrapper, style="Card.TFrame", padding=16)
        message_card.grid(row=2, column=0, sticky="nsew")
        message_card.columnconfigure(0, weight=1)
        message_card.rowconfigure(2, weight=1)

        self.selected_label = ttk.Label(
            message_card,
            text="No user selected",
            style="CardHeading.TLabel"
        )

        self.selected_label.grid(row=0, column=0, sticky="w", pady=(0, 10))

        self.message = tk.Text(
            message_card,
            height=5,
            wrap="word",
            relief="flat",
            highlightthickness=1,
            highlightbackground=BORDER,
            highlightcolor=ACCENT,
            bg=CARD,
            fg=TEXT,
            insertbackground=TEXT,
            padx=10,
            pady=8,
            font=("Segoe UI", 10)
        )

        self.message.grid(row=1, column=0, sticky="nsew", pady=(0, 12))

        self.message.bind(
            "<Control-Return>",
            self.send
        )

        buttons = ttk.Frame(message_card, style="Card.TFrame")
        buttons.grid(row=2, column=0, sticky="ew")
        buttons.columnconfigure(0, weight=1)

        self.hint_label = ttk.Label(
            buttons,
            text="Ctrl+Enter to send",
            style="CardMuted.TLabel"
        )
        self.hint_label.grid(row=0, column=0, sticky="w")

        self.send_button = ttk.Button(
            buttons,
            text="Send Notification",
            style="Accent.TButton",
            command=self.send,
            state="disabled"
        )

        self.send_button.grid(row=0, column=1, sticky="e")

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)

        self.username_label.config(
            text=f"signed in as {self.app.username}"
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

        others = [
            user for user in users
            if user.get("username") != self.app.username
        ]

        for user in others:
            self.tree.insert(
                "",
                "end",
                values=(user.get("username", ""), user.get("ip", ""))
            )

        if others:
            self.empty_label.grid_forget()
        else:
            self.empty_label.grid(row=2, column=0, sticky="w", pady=(10, 0))

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
            text=f"Message {self.selected_user}"
        )

        # Sending only makes sense while we actually have a live
        # connection - don't invite a click that can't do anything.
        self.send_button.config(
            state="normal" if self.app.network.connected else "disabled"
        )

        self.message.focus_set()

    def send(self, event=None):
        if not self.selected_user:
            return "break"

        if not self.app.network.connected:
            self.app.set_status("Not connected - can't send")
            self.send_button.config(state="disabled")
            return "break"

        message = self.message.get(
            "1.0",
            "end-1c"
        )

        # Empty messages are intentionally allowed.
        sent = self.app.send_notification(
            self.selected_user,
            message
        )

        if not sent:
            # Connection dropped between the click and the send attempt.
            self.app.set_status("Not connected - message not sent")
            self.send_button.config(state="disabled")
            return "break"

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
