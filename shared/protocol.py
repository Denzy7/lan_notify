import json
import threading
import weakref


# Hard cap on one JSON line. Without it, a client that never sends a
# newline could make readline() buffer forever and eat all the memory.
MAX_LINE_BYTES = 64 * 1024

# Longest notification text a client will send / a server will forward.
MAX_MESSAGE_CHARS = 4000

MAX_USERNAME_CHARS = 32

STATUSES = ("available", "busy", "away")

# Everything beyond the v0.0.1 protocol is opt-in. The server lists what
# it supports in its "connected" message; a client asks for the ones it
# wants with a "hello" message. A v0.0.1 server lists nothing, so a new
# client sends it nothing new; a client that never says hello (anything
# before this) gets the exact v0.0.1 behaviour from a new server.
FEATURE_UNIQUE_USERNAMES = "unique_usernames"    # username_result replies, names must be unique
FEATURE_DELIVERY_RECEIPTS = "delivery_receipts"  # notify_result replies
FEATURE_STATUS = "status"                        # set_status + "status" in user_list

FEATURES = (
    FEATURE_UNIQUE_USERNAMES,
    FEATURE_DELIVERY_RECEIPTS,
    FEATURE_STATUS,
)

# UDP port the server answers "who's out there?" broadcasts on, so
# clients can find it without anyone typing an IP address.
DISCOVERY_PORT = 5001
DISCOVERY_REQUEST = b"OFFICETALK_DISCOVER"


# One send lock per socket. Several threads can write to the same socket
# (heartbeat + GUI on the client; broadcasts, relayed notifications and
# pongs on the server) and sendall() from two threads at once can
# interleave the bytes of two messages into one corrupt line.
_send_locks = weakref.WeakKeyDictionary()
_send_locks_guard = threading.Lock()


def _lock_for(sock):
    with _send_locks_guard:
        lock = _send_locks.get(sock)

        if lock is None:
            lock = threading.Lock()
            _send_locks[sock] = lock

        return lock


def send_json(sock, data):
    """Send one JSON message terminated by a newline."""
    message = (json.dumps(data) + "\n").encode("utf-8")

    with _lock_for(sock):
        sock.sendall(message)


def make_reader(sock):
    """The file object receive_json() expects."""
    return sock.makefile("r", encoding="utf-8", newline="\n")


def receive_json(file):
    """Read one JSON message from make_reader(sock)."""
    line = file.readline(MAX_LINE_BYTES + 1)

    if not line:
        return None

    if len(line) > MAX_LINE_BYTES:
        raise ValueError("Message too large")

    return json.loads(line)
