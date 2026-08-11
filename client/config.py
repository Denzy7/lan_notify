import json
import os
import sys
from pathlib import Path


DEFAULT_CONFIG = {
    "host": "127.0.0.1",
    "port": 5000,
    "username": ""
}


def _config_dir() -> Path:
    """Where to store persistent settings.

    Deliberately NOT based on this file's own location: when this app is
    frozen into a single .exe (PyInstaller --onefile), the running script
    lives in a temp extraction folder that gets deleted after the process
    exits, so anything saved next to it would vanish every launch. Using
    the OS's normal per-user app-data location works the same whether
    running from source or from a frozen executable.
    """

    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or str(Path.home())
        return Path(base) / "LAN Notify"

    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "LAN Notify"

    # Linux and other Unix-likes.
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "lan-notify"


CONFIG_FILE = _config_dir() / "config.json"


def load_config():
    if not CONFIG_FILE.exists():
        return DEFAULT_CONFIG.copy()

    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as file:
            config = json.load(file)

        result = DEFAULT_CONFIG.copy()
        result.update(config)

        return result

    except (OSError, json.JSONDecodeError):
        return DEFAULT_CONFIG.copy()


def save_config(host, port, username):
    config = {
        "host": host,
        "port": int(port),
        "username": username
    }

    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

        with CONFIG_FILE.open("w", encoding="utf-8") as file:
            json.dump(
                config,
                file,
                indent=4
            )

    except OSError as ex:
        print(f"[Config] Could not save configuration: {ex}")
