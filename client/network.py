import socket
import threading
import queue
import time

from shared.protocol import send_json, receive_json


class NetworkClient:

    def __init__(self):

        self.socket = None
        self.file = None

        self.connected = False

        self.events = queue.Queue()

        self.receiver = None
        self.heartbeat = None

        self.last_pong = 0

        self.lock = threading.Lock()

    def connect(self, host, port):

        self.socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        self.socket.settimeout(10)

        self.socket.connect(
            (host, port)
        )

        self.socket.settimeout(None)

        self.file = self.socket.makefile("r")

        self.connected = True

        self.last_pong = time.monotonic()

        self.receiver = threading.Thread(
            target=self.receive_loop,
            daemon=True
        )

        self.receiver.start()

        self.heartbeat = threading.Thread(
            target=self.heartbeat_loop,
            daemon=True
        )

        self.heartbeat.start()

    def receive_loop(self):

        try:

            while self.connected:

                message = receive_json(
                    self.file
                )

                if message is None:
                    break

                msg_type = message.get("type")

                if msg_type == "pong":
                    self.last_pong = time.monotonic()

                else:
                    self.events.put(message)

        except Exception as ex:

            if self.connected:
                self.events.put(
                    {
                        "type": "error",
                        "message": str(ex)
                    }
                )

        finally:

            self.mark_disconnected()

    def heartbeat_loop(self):

        while self.connected:

            time.sleep(5)

            if not self.connected:
                break

            try:

                send_json(
                    self.socket,
                    {
                        "type": "ping"
                    }
                )

            except Exception:
                self.mark_disconnected()
                break

            # If we haven't received a pong for 15 seconds,
            # consider the connection lost.
            if (
                time.monotonic() - self.last_pong
                > 15
            ):
                self.mark_disconnected()
                break

    def mark_disconnected(self):

        with self.lock:

            if not self.connected:
                return

            self.connected = False

        self.events.put(
            {
                "type": "disconnected"
            }
        )

        try:
            self.socket.shutdown(
                socket.SHUT_RDWR
            )
        except Exception:
            pass

        try:
            self.socket.close()
        except Exception:
            pass

    def set_username(self, username):

        if not self.connected:
            return

        send_json(
            self.socket,
            {
                "type": "set_username",
                "username": username
            }
        )

    def send_notification(
        self,
        target,
        message
    ):

        if not self.connected:
            return

        send_json(
            self.socket,
            {
                "type": "notify",
                "target": target,
                "message": message
            }
        )

    def disconnect(self):

        if not self.connected:
            return

        try:

            send_json(
                self.socket,
                {
                    "type": "disconnect"
                }
            )

        except Exception:
            pass

        self.mark_disconnected()
