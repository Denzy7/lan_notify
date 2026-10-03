"""System tray icon (optional - needs `pystray` + Pillow).

pystray runs its own event loop on a background thread, so every menu
action is handed back to Tk via app.call_soon() rather than touching
widgets directly.
"""

import sys

from client.resources import resource_path

try:
    import pystray
    from PIL import Image
    # pystray's macOS backend has to own the main thread, which Tk
    # already does - so no tray there.
    _AVAILABLE = sys.platform != "darwin"
except Exception:
    _AVAILABLE = False


STATUS_LABELS = {
    "available": "Available",
    "busy": "Busy",
    "away": "Away",
}


class Tray:

    def __init__(self, app):
        self.app = app
        self.icon = None

    @property
    def running(self):
        return self.icon is not None

    def start(self):
        if not _AVAILABLE:
            return False

        try:
            image = Image.open(resource_path("assets/logo.png"))

            status_items = [
                pystray.MenuItem(
                    label,
                    self._status_action(status),
                    checked=lambda item, s=status: self.app.current_status == s,
                    radio=True
                )
                for status, label in STATUS_LABELS.items()
            ]

            menu = pystray.Menu(
                pystray.MenuItem("Show OfficeTalk", self._show, default=True),
                pystray.MenuItem("Status", pystray.Menu(*status_items)),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quit", self._quit),
            )

            self.icon = pystray.Icon("OfficeTalk", image, "OfficeTalk", menu)
            self.icon.run_detached()
            return True

        except Exception as ex:
            print(f"[Tray] Could not start tray icon: {ex}")
            self.icon = None
            return False

    def stop(self):
        if self.icon is None:
            return

        try:
            self.icon.stop()
        except Exception:
            pass

        self.icon = None

    def set_tooltip(self, text):
        if self.icon is not None:
            try:
                self.icon.title = text
            except Exception:
                pass

    def _show(self, icon=None, item=None):
        self.app.call_soon(self.app.show_window)

    def _quit(self, icon=None, item=None):
        self.app.call_soon(self.app.quit_app)

    def _status_action(self, status):
        def action(icon, item):
            self.app.call_soon(lambda: self.app.change_status(status))
        return action
