"""
Central visual theme for LAN Notify.

Keeping every color/font/spacing choice in one place means the whole
app looks like one product instead of a pile of default ttk widgets,
and it's easy to re-skin later.
"""

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk

# -----------------------------------------------------------------------
# Palette
# -----------------------------------------------------------------------

BG = "#f5f6fa"          # app background
CARD = "#ffffff"        # panels / cards
BORDER = "#e3e5ec"

TEXT = "#1f2430"
MUTED = "#7a7f8d"

ACCENT = "#5b5fef"       # primary brand color
ACCENT_HOVER = "#4a4ee0"
ACCENT_PRESSED = "#3d40c9"

SUCCESS = "#1fa971"
DANGER = "#e5484d"
DANGER_HOVER = "#d13c40"
WARNING = "#e8a33d"

FONT_FAMILY = "Segoe UI"
FONT_FALLBACK = "TkDefaultFont"


def _font(family_ok, size, weight="normal"):
    family = FONT_FAMILY if family_ok else FONT_FALLBACK
    return (family, size, weight)


def apply_theme(root: tk.Tk) -> dict:
    """Configure ttk styles for the whole app. Returns a small dict of
    fonts other modules can reuse so text stays consistent."""

    # Segoe UI isn't available on every platform (e.g. Linux) - fall back
    # gracefully rather than silently using an ugly default everywhere.
    available = set(tkfont.families(root))
    family_ok = FONT_FAMILY in available

    fonts = {
        "title": _font(family_ok, 22, "bold"),
        "heading": _font(family_ok, 13, "bold"),
        "body": _font(family_ok, 10),
        "small": _font(family_ok, 9),
        "mono": ("Consolas" if family_ok else FONT_FALLBACK, 10),
    }

    root.configure(bg=BG)

    style = ttk.Style(root)
    # 'clam' is the only built-in theme that lets us actually recolor
    # things like Treeview headings, borders, etc.
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure(".", background=BG, foreground=TEXT, font=fonts["body"])

    style.configure("TFrame", background=BG)
    style.configure("Card.TFrame", background=CARD)

    style.configure("TLabel", background=BG, foreground=TEXT, font=fonts["body"])
    style.configure("Card.TLabel", background=CARD, foreground=TEXT, font=fonts["body"])
    style.configure("Title.TLabel", background=BG, foreground=TEXT, font=fonts["title"])
    style.configure("Heading.TLabel", background=BG, foreground=TEXT, font=fonts["heading"])
    style.configure("CardHeading.TLabel", background=CARD, foreground=TEXT, font=fonts["heading"])
    style.configure("Muted.TLabel", background=BG, foreground=MUTED, font=fonts["small"])
    style.configure("CardMuted.TLabel", background=CARD, foreground=MUTED, font=fonts["small"])

    # Status pill text colors, swapped at runtime via style name.
    style.configure("StatusOk.TLabel", background=BG, foreground=SUCCESS, font=fonts["small"])
    style.configure("StatusBad.TLabel", background=BG, foreground=DANGER, font=fonts["small"])
    style.configure("StatusWarn.TLabel", background=BG, foreground=WARNING, font=fonts["small"])
    style.configure("StatusMuted.TLabel", background=BG, foreground=MUTED, font=fonts["small"])

    # Same statuses, but for use on a CARD-colored background (status bar).
    style.configure("CardStatusOk.TLabel", background=CARD, foreground=SUCCESS, font=fonts["small"])
    style.configure("CardStatusBad.TLabel", background=CARD, foreground=DANGER, font=fonts["small"])
    style.configure("CardStatusWarn.TLabel", background=CARD, foreground=WARNING, font=fonts["small"])
    style.configure("CardStatusMuted.TLabel", background=CARD, foreground=MUTED, font=fonts["small"])

    # Buttons
    style.configure(
        "TButton",
        background=CARD,
        foreground=TEXT,
        bordercolor=BORDER,
        lightcolor=CARD,
        darkcolor=CARD,
        focusthickness=0,
        focuscolor=CARD,
        padding=(14, 8),
        font=fonts["body"],
    )
    style.map(
        "TButton",
        background=[("active", "#f0f1f6"), ("disabled", CARD)],
        foreground=[("disabled", MUTED)],
    )

    style.configure(
        "Accent.TButton",
        background=ACCENT,
        foreground="#ffffff",
        bordercolor=ACCENT,
        focusthickness=0,
        focuscolor=ACCENT,
        padding=(16, 9),
        font=fonts["heading"],
    )
    style.map(
        "Accent.TButton",
        background=[
            ("disabled", "#c7c8f5"),
            ("pressed", ACCENT_PRESSED),
            ("active", ACCENT_HOVER),
        ],
        foreground=[("disabled", "#ffffff")],
    )

    style.configure(
        "Danger.TButton",
        background=CARD,
        foreground=DANGER,
        bordercolor=BORDER,
        focusthickness=0,
        focuscolor=CARD,
        padding=(14, 8),
        font=fonts["body"],
    )
    style.map(
        "Danger.TButton",
        background=[("active", "#fdecec")],
    )

    # Entries
    style.configure(
        "TEntry",
        fieldbackground=CARD,
        background=CARD,
        bordercolor=BORDER,
        lightcolor=BORDER,
        darkcolor=BORDER,
        padding=8,
        font=fonts["body"],
    )
    style.map(
        "TEntry",
        bordercolor=[("focus", ACCENT)],
        lightcolor=[("focus", ACCENT)],
        darkcolor=[("focus", ACCENT)],
    )

    # Treeview (user list)
    style.configure(
        "Treeview",
        background=CARD,
        fieldbackground=CARD,
        foreground=TEXT,
        rowheight=30,
        borderwidth=0,
        font=fonts["body"],
    )
    style.configure(
        "Treeview.Heading",
        background="#eceef5",
        foreground=MUTED,
        relief="flat",
        font=fonts["small"],
    )
    style.map(
        "Treeview",
        background=[("selected", ACCENT)],
        foreground=[("selected", "#ffffff")],
    )
    style.map("Treeview.Heading", background=[("active", "#eceef5")])

    style.configure("Vertical.TScrollbar", background=BG, troughcolor=BG, bordercolor=BG)

    return fonts


def status_style_for(text: str) -> str:
    """Pick a status-label style based on the current status text, so the
    status bar communicates state at a glance instead of via plain text."""

    lowered = text.lower()

    if lowered == "connected":
        return "CardStatusOk.TLabel"
    if "connecting" in lowered:
        return "CardStatusWarn.TLabel"
    if "lost" in lowered or "error" in lowered or "failed" in lowered:
        return "CardStatusBad.TLabel"
    return "CardStatusMuted.TLabel"
