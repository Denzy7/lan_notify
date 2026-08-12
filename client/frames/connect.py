import tkinter as tk
from tkinter import ttk

from client.resources import resource_path
from client.theme import BG

try:
    from PIL import Image, ImageTk
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False


# Drop a background photo at assets/background.jpg (project root) to use it.
# Any size/aspect works - it's scaled and center-cropped to always fully
# cover the window ("cover" fit, like CSS background-size: cover).
BACKGROUND_PATH = "assets/logo.png"

# Optional small logo shown inside the card itself, above the title.
# Leave the file out if you don't want one - falls back to an emoji.
LOGO_PATH = "assets/logo.png"
LOGO_MAX_WIDTH = 96

# Redraw the scaled background at most this often while the user is
# actively dragging a resize handle, so a full-window photo resize isn't
# recomputed on every single pixel of movement.
RESIZE_DEBOUNCE_MS = 120


class ConnectFrame(ttk.Frame):

    def __init__(self, parent, app):
        super().__init__(parent)

        self.app = app

        self.host = tk.StringVar(value="127.0.0.1")
        self.port = tk.StringVar(value="5000")

        # --- Background canvas ---
        # ttk widgets can't have a background image directly, so the
        # background lives on a plain tk.Canvas that fills the whole
        # frame, and the actual form is floated on top of it as a
        # "window" item, like a card sitting over a hero image.
        self.canvas = tk.Canvas(self, highlightthickness=0, bg=BG)
        self.canvas.pack(fill="both", expand=True)

        self._bg_source = self._load_background_source()
        self._bg_photo = None
        self._bg_image_id = None
        self._resize_job = None

        # --- Card (built once, floated on the canvas) ---
        self.panel = self._build_panel(self.canvas)
        self._panel_id = self.canvas.create_window(
            0, 0, window=self.panel, anchor="center"
        )

        self.canvas.bind("<Configure>", self._on_canvas_configure)

    # -----------------------------------------------------------------
    # Background image handling
    # -----------------------------------------------------------------

    def _load_background_source(self):
        if not _PIL_AVAILABLE:
            return None

        path = resource_path(BACKGROUND_PATH)

        if not path.exists():
            return None

        try:
            # Keep the original, unscaled image around so each resize
            # rescales from full quality rather than re-shrinking an
            # already-shrunk copy.
            return Image.open(path).convert("RGB")

        except Exception as ex:
            print(f"[ConnectFrame] Could not load background: {ex}")
            return None

    def _on_canvas_configure(self, event):
        # Always keep the card centered immediately - that's cheap.
        self.canvas.coords(self._panel_id, event.width / 2, event.height / 2)

        if self._bg_source is None:
            return

        # But the expensive part (rescaling the photo) gets debounced.
        if self._resize_job is not None:
            self.after_cancel(self._resize_job)

        self._resize_job = self.after(
            RESIZE_DEBOUNCE_MS,
            lambda: self._render_background(event.width, event.height)
        )

    def _render_background(self, width, height):
        self._resize_job = None

        if width < 2 or height < 2:
            return

        source = self._bg_source

        # "Cover" fit: scale so the image fully covers width x height
        # (overshooting one dimension), then crop the centered excess.
        scale = max(width / source.width, height / source.height)
        scaled_size = (
            max(1, round(source.width * scale)),
            max(1, round(source.height * scale))
        )

        resized = source.resize(scaled_size, Image.LANCZOS)

        left = (resized.width - width) // 2
        top = (resized.height - height) // 2
        cropped = resized.crop((left, top, left + width, top + height))

        # Keep a reference on self - PhotoImage has no refcount tie to
        # the canvas item, so without this Tk garbage-collects it and
        # the background silently goes blank on the next redraw.
        self._bg_photo = ImageTk.PhotoImage(cropped)

        if self._bg_image_id is None:
            self._bg_image_id = self.canvas.create_image(
                0, 0, anchor="nw", image=self._bg_photo
            )
            # Make sure the card stays above the background image.
            self.canvas.tag_lower(self._bg_image_id)
        else:
            self.canvas.itemconfig(self._bg_image_id, image=self._bg_photo)

    # -----------------------------------------------------------------
    # Card contents (unchanged in spirit from before, just built onto
    # its own standalone frame instead of being grid-packed into self)
    # -----------------------------------------------------------------

    def _build_panel(self, parent):
        panel = ttk.Frame(parent)

        self._logo_image = self._load_logo()

        if self._logo_image is not None:
            ttk.Label(
                panel,
                image=self._logo_image
            ).pack(pady=(0, 6))
        else:
            ttk.Label(
                panel,
                text="\U0001F4E1",
                font=("Segoe UI Emoji", 40),
                style="TLabel"
            ).pack(pady=(0, 6))

        ttk.Label(
            panel,
            text="OfficeTalk",
            style="Title.TLabel"
        ).pack(pady=(0, 4))

        ttk.Label(
            panel,
            text="Connect to a notification server on your network",
            style="Muted.TLabel"
        ).pack(pady=(0, 28))

        card = ttk.Frame(panel, style="Card.TFrame", padding=24)
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

        return panel

    def _load_logo(self):
        if not _PIL_AVAILABLE:
            return None

        path = resource_path(LOGO_PATH)

        if not path.exists():
            return None

        try:
            image = Image.open(path)

            ratio = LOGO_MAX_WIDTH / image.width
            new_size = (LOGO_MAX_WIDTH, int(image.height * ratio))

            image = image.resize(new_size, Image.LANCZOS)

            return ImageTk.PhotoImage(image)

        except Exception as ex:
            print(f"[ConnectFrame] Could not load logo: {ex}")
            return None

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
