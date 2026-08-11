import socket
import threading
import queue
import time

from shared.protocol import send_json, receive_json


PING_INTERVAL = 5      # seconds between pings
PONG_TIMEOUT = 15      # seconds without a pong before we consider it dead
CONNECT_TIMEOUT = 10   # seconds to wait for the initial TCP connect


class NetworkClient:

    def __init__(self):

        self.socket = None
        self.file = None

        self.connected = False

        self.events = queue.Queue()

        self.receiver = None
        self.heartbeat = None
        self.connector = None

        self.last_pong = 0

        self.lock = threading.Lock()

        # Set the instant disconnect() is called, *before* any socket I/O.
        # This matters because calling disconnect() sends a message that
        # can make the server close its end of the socket, which can wake
        # up receive_loop's own automatic mark_disconnected() call before
        # disconnect() gets to call it. Reading this flag (rather than
        # passing voluntary=True as an argument at the call site) means
        # whichever thread gets there first still reports the correct
        # reason.
        self._voluntary_disconnect = False

    def connect(self, host, port):
        """Kick off a connection attempt in the background so the GUI
        thread never blocks on the socket timeout. Result arrives on
        `events` as a 'connect_result' message."""

        self.connector = threading.Thread(
            target=self._connect_worker,
            args=(host, port),
            daemon=True
        )

        self.connector.start()

    def _connect_worker(self, host, port):

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        try:
            sock.settimeout(CONNECT_TIMEOUT)
            sock.connect((host, port))
            sock.settimeout(None)

        except Exception as ex:
            try:
                sock.close()
            except Exception:
                pass

            self.events.put(
                {
                    "type": "connect_result",
                    "success": False,
                    "error": str(ex)
                }
            )
            return

        with self.lock:
            self.socket = sock
            self.file = sock.makefile("r")
            self.connected = True
            self.last_pong = time.monotonic()
            self._voluntary_disconnect = False

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

        self.events.put(
            {
                "type": "connect_result",
                "success": True
            }
        )

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

            time.sleep(PING_INTERVAL)

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

            # If we haven't received a pong in a while, the connection
            # is dead even though the OS may not have noticed yet.
            if (
                time.monotonic() - self.last_pong
                > PONG_TIMEOUT
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
                "type": "disconnected",
                "voluntary": self._voluntary_disconnect
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
            return False

        try:
            send_json(
                self.socket,
                {
                    "type": "set_username",
                    "username": username
                }
            )
            return True

        except Exception:
            self.mark_disconnected()
            return False

    def send_notification(
        self,
        target,
        message
    ):

        if not self.connected:
            return False

        try:
            send_json(
                self.socket,
                {
                    "type": "notify",
                    "target": target,
                    "message": message
                }
            )
            return True

        except Exception:
            self.mark_disconnected()
            return False

    def disconnect(self):

        if not self.connected:
            return

        # Set this *before* touching the socket - see the comment on
        # the attribute definition for why ordering matters here.
        self._voluntary_disconnect = True

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
