"""Start OfficeTalk when the user logs in.

Each OS has its own per-user mechanism - none of them need admin rights:
- Windows: HKCU\\...\\Run registry value
- Linux:   ~/.config/autostart/*.desktop (XDG autostart)
- macOS:   ~/Library/LaunchAgents/*.plist
"""

import os
import plistlib
import shlex
import subprocess
import sys
from pathlib import Path


APP_NAME = "OfficeTalk"

# Passed on login so the app starts tucked away in the tray.
TRAY_ARG = "--tray"

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_DESKTOP_FILE = Path(
    os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config"
) / "autostart" / "officetalk.desktop"
_PLIST_FILE = Path.home() / "Library" / "LaunchAgents" / "com.officetalk.client.plist"


def _launch_args():
    if getattr(sys, "frozen", False):
        return [sys.executable, TRAY_ARG]

    # Running from source: launch the root-level entry script so the
    # project root ends up on sys.path regardless of working directory.
    python = Path(sys.executable)

    if sys.platform == "win32":
        # pythonw.exe has no console window.
        pythonw = python.with_name("pythonw.exe")
        if pythonw.exists():
            python = pythonw

    script = Path(__file__).resolve().parent.parent / "run_client.py"

    return [str(python), str(script), TRAY_ARG]


def is_supported():
    return sys.platform in ("win32", "darwin") or sys.platform.startswith("linux")


def is_enabled():
    try:
        if sys.platform == "win32":
            import winreg

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY) as key:
                winreg.QueryValueEx(key, APP_NAME)
            return True

        if sys.platform == "darwin":
            return _PLIST_FILE.exists()

        return _DESKTOP_FILE.exists()

    except OSError:
        return False


def set_enabled(enabled):
    """Returns True on success."""

    try:
        if sys.platform == "win32":
            _set_windows(enabled)
        elif sys.platform == "darwin":
            _set_macos(enabled)
        else:
            _set_linux(enabled)

        return True

    except OSError as ex:
        print(f"[Autostart] Could not update start-on-login: {ex}")
        return False


def _set_windows(enabled):
    import winreg

    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE
    ) as key:
        if enabled:
            command = subprocess.list2cmdline(_launch_args())
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass


def _set_linux(enabled):
    if not enabled:
        _DESKTOP_FILE.unlink(missing_ok=True)
        return

    _DESKTOP_FILE.parent.mkdir(parents=True, exist_ok=True)

    exec_line = " ".join(shlex.quote(arg) for arg in _launch_args())

    _DESKTOP_FILE.write_text(
        "[Desktop Entry]\n"
        "Type=Application\n"
        f"Name={APP_NAME}\n"
        f"Exec={exec_line}\n"
        "X-GNOME-Autostart-enabled=true\n",
        encoding="utf-8"
    )


def _set_macos(enabled):
    if not enabled:
        _PLIST_FILE.unlink(missing_ok=True)
        return

    _PLIST_FILE.parent.mkdir(parents=True, exist_ok=True)

    with _PLIST_FILE.open("wb") as file:
        plistlib.dump(
            {
                "Label": "com.officetalk.client",
                "ProgramArguments": _launch_args(),
                "RunAtLoad": True,
            },
            file
        )
