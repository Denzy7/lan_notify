import json
import socket
import threading
import time

from shared.protocol import DISCOVERY_PORT, DISCOVERY_REQUEST


def _broadcast_addresses():
    """255.255.255.255 only leaves through one network adapter on some
    systems (notably Windows with VPN/VM adapters), so also try each local
    IPv4 address's /24 broadcast - that covers typical office/home LANs."""

    addresses = {"255.255.255.255"}

    try:
        infos = socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)
    except OSError:
        infos = []

    local_ips = {info[4][0] for info in infos}

    # The address used for the default route - often the only real LAN
    # address when the hostname resolves to 127.0.x.x (common on Linux).
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe.connect(("10.255.255.255", 1))
        local_ips.add(probe.getsockname()[0])
        probe.close()
    except OSError:
        pass

    for ip in local_ips:
        if ip.startswith("127."):
            continue

        addresses.add(ip.rsplit(".", 1)[0] + ".255")

    return addresses


def discover_servers(timeout=1.5):
    """Broadcast a discovery request and collect replies for `timeout`
    seconds. Returns a list of {"name", "host", "port", "users"}."""

    found = {}

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(0.2)

        for address in _broadcast_addresses():
            try:
                sock.sendto(DISCOVERY_REQUEST, (address, DISCOVERY_PORT))
            except OSError:
                pass

        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            try:
                data, addr = sock.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError:
                break

            try:
                reply = json.loads(data.decode("utf-8"))
                port = int(reply["port"])
            except (ValueError, KeyError, TypeError):
                continue

            found[(addr[0], port)] = {
                "name": str(reply.get("name") or addr[0]),
                "host": addr[0],
                "port": port,
                "users": reply.get("users")
            }

    finally:
        sock.close()

    return sorted(found.values(), key=lambda s: s["name"].lower())


def discover_servers_async(callback, timeout=1.5):
    """Run discover_servers() on a background thread; `callback(servers)`
    is called on that thread, so marshal back to Tk before touching
    widgets."""

    threading.Thread(
        target=lambda: callback(discover_servers(timeout)),
        daemon=True
    ).start()
