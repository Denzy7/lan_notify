import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox

from client.theme import BORDER, ACCENT, CARD, TEXT, BG
from client.tray import STATUS_LABELS
from shared.protocol import MAX_MESSAGE_CHARS, FEATURE_DELIVERY_RECEIPTS, FEATURE_STATUS


class MainFrame(ttk.Frame):

    def __init__(self, parent, app):
        super().__init__(parent)

        self.app = app

        self.selected_users = []

        # Treeview item id -> username. Never read usernames back out of
        # the row's values: Tk converts numeric-looking strings, so
        # "007" would come back as the int 7.
        self._user_iids = {}

        # Treeview item id -> history entry.
        self._history_iids = {}
        self._unread = 0

        # Recipients of the last send still waiting on a notify_result.
        self._pending = None

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self._build_header()

        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=20, pady=(12, 16))

        self.send_tab = self._build_send_tab(self.notebook)
        self.history_tab = self._build_history_tab(self.notebook)

        self.notebook.add(self.send_tab, text="Send")
        self.notebook.add(self.history_tab, text="History")

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        for entry in self.app.history.entries:
            self._insert_history_row(entry)

    # -----------------------------
    # Header
    # -----------------------------

    def _build_header(self):
        header = ttk.Frame(self, padding=(20, 16, 20, 0))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        title_box = ttk.Frame(header)
        title_box.grid(row=0, column=0, sticky="w")

        ttk.Label(
            title_box,
            text="OfficeTalk",
            style="Heading.TLabel"
        ).pack(anchor="w")

        self.username_label = ttk.Label(
            title_box,
            text="",
            style="Muted.TLabel"
        )

        self.username_label.pack(anchor="w")

        self.status_choice = tk.StringVar(value=STATUS_LABELS["available"])

        status_box = ttk.Combobox(
            header,
            textvariable=self.status_choice,
            values=list(STATUS_LABELS.values()),
            state="readonly",
            width=10
        )
        status_box.grid(row=0, column=1, sticky="e", padx=(0, 8))
        status_box.bind("<<ComboboxSelected>>", self._on_status_selected)

        ttk.Button(
            header,
            text="Settings",
            command=self.app.open_settings
        ).grid(row=0, column=2, sticky="e", padx=(0, 8))

        ttk.Button(
            header,
            text="Disconnect",
            style="Danger.TButton",
            command=self.disconnect
        ).grid(row=0, column=3, sticky="e")

    def _on_status_selected(self, event=None):
        label = self.status_choice.get()

        for status, status_label in STATUS_LABELS.items():
            if status_label == label:
                self.app.change_status(status)
                break

    def set_server_features(self, features):
        # Older servers don't track status - hide a column that would
        # only ever be blank.
        if FEATURE_STATUS in features:
            self.tree.configure(displaycolumns=("username", "status", "ip"))
        else:
            self.tree.configure(displaycolumns=("username", "ip"))

    def show_status(self, status):
        self.status_choice.set(STATUS_LABELS.get(status, ""))

    # -----------------------------
    # Send tab
    # -----------------------------

    def _build_send_tab(self, notebook):
        tab = ttk.Frame(notebook)
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(0, weight=1)

        # Scrollable content area: on small/short windows the users list +
        # message box + button can be taller than the window, which was
        # clipping the Send button. A canvas + scrollbar lets it scroll
        # instead of just disappearing off the bottom.
        canvas = tk.Canvas(tab, background=BG, highlightthickness=0)
        canvas.grid(row=0, column=0, sticky="nsew")

        v_scroll = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        v_scroll.grid(row=0, column=1, sticky="ns")
        canvas.configure(yscrollcommand=v_scroll.set)

        wrapper = ttk.Frame(canvas, padding=(0, 12, 8, 0))
        wrapper_id = canvas.create_window((0, 0), window=wrapper, anchor="nw")
        wrapper.columnconfigure(0, weight=1)
        wrapper.rowconfigure(1, weight=1)

        def _on_wrapper_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_configure(event):
            # Keep the inner frame exactly as wide as the visible canvas.
            canvas.itemconfig(wrapper_id, width=event.width)

        wrapper.bind("<Configure>", _on_wrapper_configure)
        canvas.bind("<Configure>", _on_canvas_configure)

        def _should_scroll(event):
            # bind_all fires for every widget in the app, including
            # popups and widgets that scroll themselves - only scroll
            # this canvas when the wheel is over the visible Send tab.
            widget = event.widget

            if not isinstance(widget, tk.Misc):
                return False

            if isinstance(widget, (tk.Text, ttk.Treeview)):
                return False

            if str(widget.winfo_toplevel()) != str(self.app):
                return False

            return (
                self.app.current_frame == "MainFrame"
                and self.notebook.select() == str(tab)
            )

        def _on_mousewheel(event):
            if _should_scroll(event):
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _on_linux_wheel(event, direction):
            if _should_scroll(event):
                canvas.yview_scroll(direction, "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)   # Windows / macOS
        canvas.bind_all("<Button-4>", lambda e: _on_linux_wheel(e, -1))  # Linux
        canvas.bind_all("<Button-5>", lambda e: _on_linux_wheel(e, 1))   # Linux

        self._build_users_card(wrapper)
        self._build_message_card(wrapper)

        return tab

    def _build_users_card(self, wrapper):
        users_card = ttk.Frame(wrapper, style="Card.TFrame", padding=16)
        users_card.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        users_card.columnconfigure(0, weight=1)

        users_header = ttk.Frame(users_card, style="Card.TFrame")
        users_header.grid(row=0, column=0, sticky="ew")
        users_header.columnconfigure(0, weight=1)

        ttk.Label(
            users_header,
            text="Connected Users",
            style="CardHeading.TLabel"
        ).grid(row=0, column=0, sticky="w")

        ttk.Button(
            users_header,
            text="Select all",
            command=self.select_all
        ).grid(row=0, column=1, sticky="e", padx=(0, 6))

        ttk.Button(
            users_header,
            text="Clear",
            command=self.clear_selection
        ).grid(row=0, column=2, sticky="e")

        ttk.Label(
            users_card,
            text="Ctrl+click to select multiple · Shift+click for a range",
            style="CardMuted.TLabel"
        ).grid(row=1, column=0, sticky="w", pady=(2, 10))

        tree_frame = ttk.Frame(users_card, style="Card.TFrame")
        tree_frame.grid(row=2, column=0, sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(
            tree_frame,
            columns=("username", "status", "ip"),
            show="headings",
            # "extended" is what gives Ctrl+click (toggle one) and
            # Shift+click (select a range) for free - "browse" only
            # ever allows a single row selected at a time.
            selectmode="extended",
            height=4
        )

        self.tree.heading("username", text="USERNAME")
        self.tree.heading("status", text="STATUS")
        self.tree.heading("ip", text="IP ADDRESS")

        self.tree.column("username", width=220)
        self.tree.column("status", width=100)
        self.tree.column("ip", width=160)

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

    def _build_message_card(self, wrapper):
        message_card = ttk.Frame(wrapper, style="Card.TFrame", padding=16)
        message_card.grid(row=1, column=0, sticky="nsew")
        message_card.columnconfigure(0, weight=1)
        message_card.rowconfigure(1, weight=1)

        self.selected_label = ttk.Label(
            message_card,
            text="No user selected",
            style="CardHeading.TLabel"
        )

        self.selected_label.grid(row=0, column=0, sticky="w", pady=(0, 10))

        self.message = tk.Text(
            message_card,
            height=3,
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
            font=self.app.fonts["body"]
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

        self.quick_button = ttk.Menubutton(
            buttons,
            text="Quick message",
            state="disabled"
        )
        self.quick_menu = tk.Menu(
            self.quick_button,
            tearoff=False,
            postcommand=self._fill_quick_menu
        )
        self.quick_button["menu"] = self.quick_menu
        self.quick_button.grid(row=0, column=1, sticky="e", padx=(0, 8))

        self.send_button = ttk.Button(
            buttons,
            text="Send Notification",
            style="Accent.TButton",
            command=self.send,
            state="disabled"
        )

        self.send_button.grid(row=0, column=2, sticky="e")

    def _fill_quick_menu(self):
        self.quick_menu.delete(0, "end")

        presets = self.app.config_data.get("quick_messages") or []

        for preset in presets:
            self.quick_menu.add_command(
                label=preset,
                command=lambda text=preset: self.send(text=text)
            )

        if presets:
            self.quick_menu.add_separator()

        self.quick_menu.add_command(
            label="Edit quick messages...",
            command=self.app.open_settings
        )

    # -----------------------------
    # History tab
    # -----------------------------

    def _build_history_tab(self, notebook):
        tab = ttk.Frame(notebook, padding=(0, 12, 0, 0))
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(0, weight=1)

        card = ttk.Frame(tab, style="Card.TFrame", padding=16)
        card.grid(row=0, column=0, sticky="nsew")
        card.columnconfigure(0, weight=1)
        card.rowconfigure(0, weight=1)

        self.history_tree = ttk.Treeview(
            card,
            columns=("time", "direction", "user", "message"),
            show="headings",
            selectmode="browse"
        )

        self.history_tree.heading("time", text="TIME")
        self.history_tree.heading("direction", text="")
        self.history_tree.heading("user", text="USER")
        self.history_tree.heading("message", text="MESSAGE")

        self.history_tree.column("time", width=110, stretch=False)
        self.history_tree.column("direction", width=50, stretch=False)
        self.history_tree.column("user", width=130, stretch=False)
        self.history_tree.column("message", width=260)

        scrollbar = ttk.Scrollbar(card, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=scrollbar.set)

        self.history_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.history_tree.bind("<Double-1>", lambda e: self.open_history_entry())
        self.history_tree.bind("<Return>", lambda e: self.open_history_entry())

        buttons = ttk.Frame(card, style="Card.TFrame")
        buttons.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(12, 0))
        buttons.columnconfigure(0, weight=1)

        ttk.Label(
            buttons,
            text="Double-click a message to read or reply",
            style="CardMuted.TLabel"
        ).grid(row=0, column=0, sticky="w")

        ttk.Button(
            buttons,
            text="Clear history",
            style="Danger.TButton",
            command=self.clear_history
        ).grid(row=0, column=1, sticky="e", padx=(0, 8))

        ttk.Button(
            buttons,
            text="Open",
            style="Accent.TButton",
            command=self.open_history_entry
        ).grid(row=0, column=2, sticky="e")

        return tab

    @staticmethod
    def _format_time(iso):
        try:
            when = datetime.fromisoformat(iso)
        except (TypeError, ValueError):
            return ""

        if when.date() == datetime.now().date():
            return when.strftime("%H:%M")

        return when.strftime("%d %b %H:%M")

    def _insert_history_row(self, entry):
        incoming = entry.get("direction") == "in"
        preview = " ".join(str(entry.get("message", "")).split()) or "(empty)"

        iid = self.history_tree.insert(
            "",
            0,  # newest first
            values=(
                self._format_time(entry.get("time")),
                "From" if incoming else "To",
                entry.get("user", ""),
                preview[:200]
            )
        )

        self._history_iids[iid] = entry

    def history_added(self, entry, unread=False):
        self._insert_history_row(entry)

        if unread and self.notebook.select() != str(self.history_tab):
            self._unread += 1
            self.notebook.tab(self.history_tab, text=f"History ({self._unread} new)")

    def _on_tab_changed(self, event=None):
        if self.notebook.select() == str(self.history_tab):
            self._unread = 0
            self.notebook.tab(self.history_tab, text="History")

    def open_history_entry(self):
        selection = self.history_tree.selection()

        if not selection:
            return

        entry = self._history_iids.get(selection[0])

        if entry is not None:
            self.app.show_message_dialog(entry)

    def clear_history(self):
        if not self._history_iids:
            return

        if not messagebox.askyesno(
            "Clear history",
            "Delete all saved messages? This can't be undone.",
            parent=self
        ):
            return

        self.app.history.clear()
        self.history_tree.delete(*self.history_tree.get_children())
        self._history_iids.clear()

    # -----------------------------
    # Users
    # -----------------------------

    def tkraise(self, *args, **kwargs):
        super().tkraise(*args, **kwargs)

        self.username_label.config(
            text=f"signed in as {self.app.username}"
        )
        self.show_status(self.app.current_status)

    def update_users(self, users):
        # Rebuilding the list happens whenever anyone joins, leaves or
        # changes status - keep whoever was selected still selected.
        previous = set(self.selected_users)

        self.tree.delete(
            *self.tree.get_children()
        )

        self._user_iids = {}

        others = [
            user for user in users
            if user.get("username") != self.app.username
        ]

        reselect = []

        for user in others:
            username = user.get("username", "")

            iid = self.tree.insert(
                "",
                "end",
                values=(
                    username,
                    STATUS_LABELS.get(user.get("status"), ""),
                    user.get("ip", "")
                )
            )

            self._user_iids[iid] = username

            if username in previous:
                reselect.append(iid)

        # Set this *before* selection_set(): the <<TreeviewSelect>> it
        # triggers then sees no change and won't yank keyboard focus
        # into the message box.
        self.selected_users = [self._user_iids[iid] for iid in reselect]

        if reselect:
            self.tree.selection_set(reselect)

        self._update_selected_label()
        self._update_send_state()

        if others:
            self.empty_label.grid_forget()
        else:
            self.empty_label.grid(row=3, column=0, sticky="w", pady=(10, 0))

    def _update_selected_label(self):
        count = len(self.selected_users)

        if count == 0:
            self.selected_label.config(text="No user selected")
        elif count == 1:
            self.selected_label.config(text=f"Message {self.selected_users[0]}")
        elif count <= 3:
            self.selected_label.config(text=f"Message {', '.join(self.selected_users)}")
        else:
            self.selected_label.config(text=f"Message {count} users")

    def _update_send_state(self):
        # Sending only makes sense while we actually have a live
        # connection and at least one recipient selected.
        state = "normal" if (self.selected_users and self.app.network.connected) else "disabled"

        self.send_button.config(state=state)
        self.quick_button.config(state=state)

    def user_selected(self, event=None):
        usernames = [
            self._user_iids[item_id]
            for item_id in self.tree.selection()
            if item_id in self._user_iids
        ]

        changed = set(usernames) != set(self.selected_users)

        self.selected_users = usernames

        self._update_selected_label()
        self._update_send_state()

        if usernames and changed:
            self.message.focus_set()

    def select_all(self):
        children = self.tree.get_children()

        if children:
            self.tree.selection_set(children)

    def clear_selection(self):
        self.tree.selection_remove(*self.tree.selection())

    # -----------------------------
    # Sending
    # -----------------------------

    def send(self, event=None, text=None):
        """Send the typed message, or `text` (a quick message) if given."""

        if not self.selected_users:
            return "break"

        if not self.app.network.connected:
            self.app.set_status("Not connected - can't send")
            self._update_send_state()
            return "break"

        from_box = text is None

        if from_box:
            text = self.message.get(
                "1.0",
                "end-1c"
            )

        if len(text) > MAX_MESSAGE_CHARS:
            self.app.set_status(f"Message is too long (max {MAX_MESSAGE_CHARS} characters)")
            return "break"

        # Sent individually to each recipient - the wire protocol is
        # still a single-target "notify" message, so a multi-select
        # send is just that message repeated once per selected user.
        sent_to = []
        connection_dropped = False

        for username in self.selected_users:

            # Empty messages are intentionally allowed.
            if not self.app.send_message(username, text):
                connection_dropped = True
                break

            sent_to.append(username)

        if not sent_to:
            # Connection dropped before anything went out at all.
            self.app.set_status("Not connected - message not sent")
            self._update_send_state()
            return "break"

        if from_box:
            self.message.delete(
                "1.0",
                "end"
            )

        if connection_dropped:
            self._pending = None
            self.app.set_status(
                f"Sent to {len(sent_to)} of {len(self.selected_users)} "
                f"— connection dropped"
            )
            self._update_send_state()
            return "break"

        self.app.set_status(self._sent_summary(sent_to))

        if FEATURE_DELIVERY_RECEIPTS not in self.app.network.features:
            # Older server: no delivery results are coming.
            self._pending = None
            return "break"

        # The server answers each send with a notify_result; this
        # optimistic status gets corrected if anyone turned out to be
        # offline (see on_notify_result).
        self._pending = {
            "waiting": set(sent_to),
            "total": len(sent_to),
            "offline": [],
            "busy": []
        }

        return "break"

    @staticmethod
    def _sent_summary(sent_to):
        if len(sent_to) == 1:
            return f"Notification sent to {sent_to[0]}"

        return f"Notification sent to {len(sent_to)} users"

    def on_notify_result(self, event):
        target = event.get("target")
        delivered = event.get("delivered")
        busy = event.get("status") == "busy"

        pending = self._pending

        if pending is None or target not in pending["waiting"]:
            # A one-off send (e.g. a reply from a notification popup).
            if not delivered:
                self.app.set_status(f"{target} is offline - message not delivered")
            elif busy:
                self.app.set_status(f"Notification sent to {target} (they're busy)")
            return

        pending["waiting"].discard(target)

        if not delivered:
            pending["offline"].append(target)
        elif busy:
            pending["busy"].append(target)

        if pending["waiting"]:
            return

        self._pending = None

        offline = pending["offline"]
        delivered_count = pending["total"] - len(offline)

        if offline:
            names = ", ".join(offline)
            if delivered_count:
                self.app.set_status(f"Sent to {delivered_count} — offline, not delivered: {names}")
            else:
                self.app.set_status(f"{names} offline - message not delivered")
        elif pending["busy"]:
            self.app.set_status(
                f"Notification sent — busy, will see it later: {', '.join(pending['busy'])}"
            )

    def disconnect(self):
        self.app.disconnect()
