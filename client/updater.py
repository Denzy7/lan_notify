import json
import re
import threading
import urllib.error
import urllib.request

from client.version import __version__


# Set this to your actual "owner/repo".
GITHUB_REPO = "Denzy7/lan_notify"

API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
REQUEST_TIMEOUT = 5  # seconds

_VERSION_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)$")


def parse_version(tag):
    """'v1.4.2' -> (1, 4, 2). Returns None if it isn't in the expected
    vMAJOR.MINOR.PATCH shape (pre-releases, 'latest', etc.)."""

    if not tag:
        return None

    match = _VERSION_RE.match(tag.strip())

    if not match:
        return None

    return tuple(int(part) for part in match.groups())


def check_for_update(callback):
    """Check GitHub for a release newer than the running build.

    Runs entirely on a background thread so it can never block the UI or
    delay connecting to a server - update checks are a nice-to-have, not
    something that should get in the way if GitHub is slow/unreachable.

    `callback` fires exactly once, with:
        callback(latest_tag, html_url)   if a newer version is available
        callback(None, None)             if up to date, or the check failed

    NOTE: callback runs on the background thread. If it touches Tk widgets,
    marshal it back onto the main thread first (e.g. `widget.after(0, ...)`).
    """

    def worker():
        try:
            request = urllib.request.Request(
                API_URL,
                headers={
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "OfficeTalk-Update-Check"
                }
            )

            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
                data = json.load(response)

            latest_tag = data.get("tag_name", "")
            html_url = data.get("html_url", "")

            callback(latest_tag, html_url, None)

        except Exception as e:
            # No internet, GitHub rate-limited us, repo has no releases
            # yet, etc. - fail quietly. This must never surface as an
            # error to someone just trying to connect to a server.
            callback(None, None, e)

    threading.Thread(target=worker, daemon=True).start()
