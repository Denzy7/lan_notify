import socket
import threading

from shared.protocol import send_json, receive_json


HOST = "0.0.0.0"
PORT = 5000


clients = {}
lock = threading.Lock()


def broadcast_user_list():
    users = []

    with lock:
        for info in clients.values():
            if info["username"]:
                users.append(
                    {
                        "username": info["username"],
                        "ip": info["ip"]
                    }
                )

        for info in list(clients.values()):
            try:
                send_json(
                    info["socket"],
                    {
                        "type": "user_list",
                        "users": users
                    }
                )
            except Exception:
                pass


def remove_client(sock):
    with lock:
        if sock in clients:
            del clients[sock]

    broadcast_user_list()

    try:
        sock.close()
    except:
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

    send_json(sock, {"type": "connected"})

    try:
        while True:

            message = receive_json(file)

            if message is None:
                break

            msg_type = message.get("type")

            if msg_type == "set_username":

                with lock:
                    clients[sock]["username"] = message["username"]

                print(f"User set name: {message['username']}")

                broadcast_user_list()

            elif msg_type == "notify":

                target = message["target"]
                text = message["message"]

                sender = clients[sock]["username"]

                with lock:

                    for info in clients.values():

                        if info["username"] == target:

                            send_json(
                                info["socket"],
                                {
                                    "type": "notification",
                                    "from": sender,
                                    "message": text
                                }
                            )

                            break

            elif msg_type == "disconnect":
                break
            elif msg_type == "ping":

                send_json(
                        sock,
                        {
                            "type": "pong"
                            }
                        )

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
