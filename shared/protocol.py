import json


def send_json(sock, data):
    """Send one JSON message terminated by a newline."""
    message = json.dumps(data) + "\n"
    sock.sendall(message.encode("utf-8"))


def receive_json(file):
    """Read one JSON message from a socket.makefile()."""
    line = file.readline()

    if not line:
        return None

    return json.loads(line)
