import json
from datetime import datetime

from client.config import _config_dir


HISTORY_FILE = _config_dir() / "history.json"

# Oldest entries are dropped past this, so the file never grows forever.
MAX_ENTRIES = 500


class History:
    """Sent/received messages, newest last, saved next to config.json so
    a closed popup isn't the only record of a message."""

    def __init__(self):
        self.entries = self._load()

    def _load(self):
        try:
            with HISTORY_FILE.open("r", encoding="utf-8") as file:
                entries = json.load(file)

            if isinstance(entries, list):
                return [e for e in entries if isinstance(e, dict)][-MAX_ENTRIES:]

        except (OSError, json.JSONDecodeError):
            pass

        return []

    def _save(self):
        try:
            HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

            with HISTORY_FILE.open("w", encoding="utf-8") as file:
                json.dump(self.entries, file, indent=1)

        except OSError as ex:
            print(f"[History] Could not save history: {ex}")

    def add(self, direction, user, message):
        """direction is "in" (received) or "out" (sent)."""

        entry = {
            "time": datetime.now().isoformat(timespec="seconds"),
            "direction": direction,
            "user": user,
            "message": message
        }

        self.entries.append(entry)
        del self.entries[:-MAX_ENTRIES]
        self._save()

        return entry

    def clear(self):
        self.entries = []
        self._save()
