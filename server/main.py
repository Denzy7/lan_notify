import json
import socket
import threading
import argparse

from shared.protocol import (
    send_json,
    receive_json,
    make_reader,
    MAX_MESSAGE_CHARS,
    MAX_USERNAME_CHARS,
    STATUSES,
    FEATURES,
    FEATURE_UNIQUE_USERNAMES,
    FEATURE_DELIVERY_RECEIPTS,
    DISCOVERY_PORT,
    DISCOVERY_REQUEST,
)

parser = argparse.ArgumentParser(description="LAN Notify server")

parser.add_argument("-p", dest="port", help="port", default=5000, type=int)
parser.add_argument("-a", dest="address", help="address", default="0.0.0.0", type=str)
parser.add_argument("-n", dest="name", help="server name shown to clients", default=socket.gethostname(), type=str)
parser.add_argument("--no-discovery", dest="discovery", help="don't answer LAN discovery broadcasts", action="store_false")
args = parser.parse_args()

HOST = args.address
PORT = args.port
NAME = args.name


clients = {}
lock = threading.Lock()


def broadcast_user_list():
    """Send the current user list to everyone. Sockets are sent to
    *outside* the lock - a slow or stuck client shouldn't be able to
    freeze every other client's view of who's online."""

    with lock:
        users = [
            {
                "username": info["username"],
                "ip": info["ip"],
                "status": info["status"]
            }
            for info in clients.values()
            if info["username"]
        ]

        targets = [info["socket"] for info in clients.values()]

    for sock in targets:
        try:
            send_json(
                sock,
                {
                    "type": "user_list",
                    "users": users
                }
            )
        except Exception:
            # If the send fails the client's own receive loop will
            # notice the drop and clean it up; nothing to do here.
            pass


def remove_client(sock):
    with lock:
        if sock in clients:
            del clients[sock]

    broadcast_user_list()

    try:
        sock.close()
    except Exception:
        pass


def find_user(username):
    """Caller must hold `lock`. An exact match wins (that's all v0.0.1
    did, and legacy clients can still register names differing only by
    case); otherwise match case-insensitively, the way new clients'
    names are kept unique."""

    for info in clients.values():
        if info["username"] == username:
            return info

    wanted = str(username).casefold()

    for info in clients.values():
        if info["username"] and str(info["username"]).casefold() == wanted:
            return info

    return None


def handle_hello(sock, message):
    """A newer client asking for features beyond the v0.0.1 protocol.
    Clients that never send this keep the original behaviour."""

    requested = message.get("features")

    if not isinstance(requested, list):
        return

    with lock:
        clients[sock]["features"] = {f for f in requested if f in FEATURES}


def handle_set_username(sock, message):
    with lock:
        features = clients[sock]["features"]

    if FEATURE_UNIQUE_USERNAMES not in features:
        handle_set_username_legacy(sock, message)
        return

    username = message.get("username")

    if not isinstance(username, str):
        username = ""

    username = username.strip()

    error = None

    if not username:
        error = "Username cannot be empty."
    elif len(username) > MAX_USERNAME_CHARS:
        error = "Username is too long."

    if error is None:
        with lock:
            existing = find_user(username)

            if existing is not None and existing["socket"] is not sock:
                error = f'"{username}" is already taken.'
            else:
                clients[sock]["username"] = username

    send_json(
        sock,
        {
            "type": "username_result",
            "success": error is None,
            "username": username,
            "error": error
        }
    )

    if error is None:
        print(f"User set name: {username}")
        broadcast_user_list()


def handle_set_username_legacy(sock, message):
    """Exactly what v0.0.1 did: accept any non-empty name, no reply."""

    username = message.get("username")

    if not username:
        return

    with lock:
        clients[sock]["username"] = username

    print(f"User set name: {username}")

    broadcast_user_list()


def handle_notify(sock, message):
    target = message.get("target")
    text = message.get("message", "")

    if not isinstance(text, str):
        text = ""

    text = text[:MAX_MESSAGE_CHARS]

    with lock:
        sender = clients[sock]["username"]
        wants_receipt = FEATURE_DELIVERY_RECEIPTS in clients[sock]["features"]
        target_info = find_user(target) if target is not None else None
        target_socket = target_info["socket"] if target_info else None
        target_status = target_info["status"] if target_info else None

    delivered = False

    if target_socket is not None:
        try:
            send_json(
                target_socket,
                {
                    "type": "notification",
                    "from": sender,
                    "message": text
                }
            )
            delivered = True

        except Exception:
            # Target dropped mid-send; its own receive loop will
            # detect and clean it up.
            pass

    if not wants_receipt:
        return

    send_json(
        sock,
        {
            "type": "notify_result",
            "target": target,
            "delivered": delivered,
            "status": target_status
        }
    )


def handle_set_status(sock, message):
    status = message.get("status")

    if status not in STATUSES:
        return

    with lock:
        clients[sock]["status"] = status

    broadcast_user_list()


def handle_client(sock, address):
    print(f"Connected: {address}")

    file = make_reader(sock)

    with lock:
        clients[sock] = {
            "socket": sock,
            "username": None,
            "status": "available",
            "ip": address[0],
            # Features this client asked for with "hello" (none = v0.0.1).
            "features": set()
        }

    try:
        send_json(
            sock,
            {
                "type": "connected",
                "server": NAME,
                "features": list(FEATURES)
            }
        )
    except Exception:
        remove_client(sock)
        return

    try:
        while True:

            message = receive_json(file)

            if message is None:
                break

            if not isinstance(message, dict):
                continue

            msg_type = message.get("type")

            if msg_type == "hello":
                handle_hello(sock, message)

            elif msg_type == "set_username":
                handle_set_username(sock, message)

            elif msg_type == "notify":
                handle_notify(sock, message)

            elif msg_type == "set_status":
                handle_set_status(sock, message)

            elif msg_type == "disconnect":
                break

            elif msg_type == "ping":
                send_json(sock, {"type": "pong"})

    except Exception as ex:
        print(ex)

    print(f"Disconnected: {address}")

    remove_client(sock)


def discovery_responder():
    """Answer clients' UDP broadcasts with this server's name and port so
    they can list it on the connect screen."""

    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        udp.bind(("", DISCOVERY_PORT))
    except OSError as ex:
        print(f"Discovery disabled - could not bind UDP {DISCOVERY_PORT}: {ex}")
        return

    print(f"Answering discovery on UDP {DISCOVERY_PORT}")

    while True:
        try:
            data, addr = udp.recvfrom(1024)

            if data.strip() != DISCOVERY_REQUEST:
                continue

            with lock:
                user_count = sum(1 for info in clients.values() if info["username"])

            reply = {
                "name": NAME,
                "port": PORT,
                "users": user_count
            }

            udp.sendto(json.dumps(reply).encode("utf-8"), addr)

        except Exception as ex:
            print(f"Discovery error: {ex}")


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.bind((HOST, PORT))

    server.listen()

    print(f"Listening on {HOST}:{PORT} as \"{NAME}\"")

    if args.discovery:
        threading.Thread(target=discovery_responder, daemon=True).start()

    while True:

        client, addr = server.accept()

        thread = threading.Thread(
            target=handle_client,
            args=(client, addr),
            daemon=True
        )

        thread.start()


if __name__ == "__main__":
    main()
