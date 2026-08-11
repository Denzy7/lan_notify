import socket
import threading
import argparse

from shared.protocol import send_json, receive_json

parser = argparse.ArgumentParser(description="LAN Notify server")

parser.add_argument("-p", dest="port", help="port", default=5000, type=int)
parser.add_argument("-a", dest="address", help="address", default="0.0.0.0", type=str)
args = parser.parse_args()

HOST = args.address
PORT = args.port


clients = {}
lock = threading.Lock()


def broadcast_user_list():
    """Send the current user list to everyone. Sockets are sent to
    *outside* the lock - a slow or stuck client shouldn't be able to
    freeze every other client's view of who's online."""

    with lock:
        users = [
            {"username": info["username"], "ip": info["ip"]}
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


def handle_client(sock, address):
    print(f"Connected: {address}")

    file = sock.makefile("r")

    with lock:
        clients[sock] = {
            "socket": sock,
            "username": None,
            "ip": address[0]
        }

    try:
        send_json(sock, {"type": "connected"})
    except Exception:
        remove_client(sock)
        return

    try:
        while True:

            message = receive_json(file)

            if message is None:
                break

            msg_type = message.get("type")

            if msg_type == "set_username":

                username = message.get("username")

                if not username:
                    continue

                with lock:
                    clients[sock]["username"] = username

                print(f"User set name: {username}")

                broadcast_user_list()

            elif msg_type == "notify":

                target = message.get("target")
                text = message.get("message", "")

                with lock:
                    sender = clients[sock]["username"]
                    target_socket = None

                    for info in clients.values():
                        if info["username"] == target:
                            target_socket = info["socket"]
                            break

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
                    except Exception:
                        # Target dropped mid-send; its own receive loop
                        # will detect and clean it up.
                        pass

            elif msg_type == "disconnect":
                break

            elif msg_type == "ping":

                try:
                    send_json(sock, {"type": "pong"})
                except Exception:
                    break

    except Exception as ex:
        print(ex)

    print(f"Disconnected: {address}")

    remove_client(sock)


def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.bind((HOST, PORT))

    server.listen()

    print(f"Listening on {HOST}:{PORT}")

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
