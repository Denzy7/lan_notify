import sys
import os
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
    except Exception:
        base_path = os.path.abspath(".")

    return Path(os.path.join(base_path, relative_path))
