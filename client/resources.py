import sys
from pathlib import Path


def resource_path(relative_path: str) -> Path:
    """Resolve a path to a bundled asset (image, icon, etc).

    Works two ways:
    - Running from source: relative to the project root.
    - Frozen into a PyInstaller --onefile exe: PyInstaller unpacks
      bundled data into a temp folder at runtime and exposes it via
      sys._MEIPASS. Assets must be resolved through that at runtime,
      not through a normal relative/__file__ path, or they won't be
      found once frozen.
    """

    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # Not frozen - resolve relative to the project root (this file's
        # grandparent directory), not the current working directory.
        # os.path.abspath(".") would silently break if this app is ever
        # launched from somewhere other than the project root (a desktop
        # shortcut with a different "Start in" folder, a different cwd,
        # etc.) - __file__ is always correct regardless of cwd.
        base_path = Path(__file__).resolve().parent.parent

    return Path(base_path) / relative_path
