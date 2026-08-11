import json
from pathlib import Path


CONFIG_FILE = Path(__file__).resolve().parent.parent / "config.json"

DEFAULT_CONFIG = {
    "host": "127.0.0.1",
    "port": 5000,
    "username": ""
}


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
        with CONFIG_FILE.open("w", encoding="utf-8") as file:
            json.dump(
                config,
                file,
                indent=4
            )

    except OSError as ex:
        print(f"[Config] Could not save configuration: {ex}")
