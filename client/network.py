import socket
import threading
import queue

from shared.protocol import send_json, receive_json


class NetworkClient:

    def __init__(self):

        self.socket = None
        self.file = None

        self.connected = False

        self.events = queue.Queue()

        self.receiver = None

    def connect(self, host, port):

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.socket.connect((host, port))

        self.file = self.socket.makefile("r")

        self.connected = True

        self.receiver = threading.Thread(
            target=self.receive_loop,
            daemon=True
        )

        self.receiver.start()

    def receive_loop(self):

        try:

            while self.connected:

                message = receive_json(self.file)

                if message is None:
                    break

                self.events.put(message)

        except Exception as ex:

            self.events.put(
                {
                    "type": "error",
                    "message": str(ex)
                }
            )

        finally:

            self.connected = False

            self.events.put(
                {
                    "type": "disconnected"
                }
            )

    def set_username(self, username):

        send_json(
            self.socket,
            {
                "type": "set_username",
                "username": username
            }
        )

    def send_notification(self, target, message):

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

        except:
            pass

        self.connected = False

        try:
            self.socket.close()
        except:
            pass
