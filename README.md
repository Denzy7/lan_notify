
# LAN Notify

A simple local-network notification application built with Python and Tkinter.

LAN Notify consists of two parts:

* **Server** — accepts clients and keeps track of connected users.
* **Client** — connects to the server, lets users select other connected users, and sends notifications.

Communication between the client and server uses TCP sockets with newline-delimited JSON messages.

## Requirements

* Python 3.10+
* Tkinter
* A local network connection between the server and clients

Tkinter is normally included with Python on Windows.

On Debian/Ubuntu-based Linux distributions, you may need to install it separately:

```bash
sudo apt install python3-tk
```

## Installation

Clone or download the project:

```bash
git clone <repository-url>
cd lan_notify
```

No third-party Python packages are required for the basic application.

### Optional: Native Notifications

LAN Notify can also display native operating-system notifications.

#### Windows

```bash
pip install winotify
```

#### Linux

```bash
pip install notify2
```

These packages are optional. If they are not installed, LAN Notify will continue to work and will still display the Tkinter notification dialog.

## Project Structure

```text
lan_notify/
├── client/
│   ├── __init__.py
│   ├── main.py
│   ├── gui.py
│   ├── network.py
│   ├── notifications.py
│   └── frames/
│       ├── __init__.py
│       ├── connect.py
│       ├── username.py
│       └── mainframe.py
│
├── server/
│   ├── __init__.py
│   └── main.py
│
├── shared/
│   ├── __init__.py
│   └── protocol.py
│
└── config.json
```

## Running the Server

Open a terminal in the project directory:

```bash
python -m server.main
```

The server listens on:

```text
0.0.0.0:5000
```

This allows clients on the local network to connect to the machine running the server.

## Running the Client

Open another terminal:

```bash
python -m client.main
```

The client will open the Tkinter interface.

Enter the server's LAN IP address and port.

For example:

```text
Server Address: 192.168.1.100
Port:           5000
```

Then click **Connect**.

## Configuration

The client automatically saves connection information and the username in:

```text
config.json
```

Example:

```json
{
    "host": "192.168.1.100",
    "port": 5000,
    "username": "Alice"
}
```

The saved values are loaded automatically when the client starts.

The connection screen remembers:

* Server address
* Server port

The username screen remembers:

* Username

The configuration file can be edited manually if needed.

## Using the Client

1. Start the server.
2. Start the client.
3. Enter the server address and port.
4. Connect.
5. Enter your username.
6. Click **Continue**.
7. Connected users will appear in the list.
8. Select a user.
9. Enter a message.
10. Click **Send Notification**.

Empty messages are also allowed.

Pressing `Ctrl+Enter` while typing a message will also send it.

## Notifications

When a notification is received, the client:

1. Brings the LAN Notify window to the foreground.
2. Attempts to display a native operating-system notification.
3. Displays a Tkinter message box.

Native notifications are optional.

If `winotify` or `notify2` is not installed, the application will print a message explaining which package is missing and the Tkinter message box will still be displayed.

## Local Network Setup

The server needs to be reachable from the other computers on the LAN.

For example:

```text
Server
192.168.1.100
     │
     ├── Client A
     │   192.168.1.101
     │
     ├── Client B
     │   192.168.1.102
     │
     └── Client C
         192.168.1.103
```

Clients should connect to the server's **LAN IP address**, not `127.0.0.1`.

For example:

```text
192.168.1.100
```

`127.0.0.1` only works when the client and server are running on the same computer.

## Firewall

If clients cannot connect, check the firewall on the computer running the server.

TCP port `5000` must be allowed for connections from the local network.

The server itself listens on:

```text
0.0.0.0:5000
```

You can change the port in `server/main.py`:

```python
HOST = "0.0.0.0"
PORT = 5000
```

If you change the server port, use the same port when connecting from the clients.

## Troubleshooting

### `ModuleNotFoundError: No module named 'gui'`

Run the client from the project root using:

```bash
python -m client.main
```

rather than:

```bash
python client/main.py
```

Likewise, start the server with:

```bash
python -m server.main
```

### Linux: Tkinter is missing

Install it with:

```bash
sudo apt install python3-tk
```

### Native notifications do not appear

Install the optional notification package.

Windows:

```bash
pip install winotify
```

Linux:

```bash
pip install notify2
```

The application will still work without these packages.

### Client cannot connect

Check:

* The server is running.
* The client is using the server's LAN IP.
* The port numbers match.
* The server computer's firewall allows TCP port `5000`.
* Both computers are connected to the same network.

## Current Features

* TCP LAN communication
* Multiple simultaneous clients
* Username registration
* Connected-user list
* User IP addresses
* Custom notifications
* Empty notifications
* Native Windows/Linux notifications
* Tkinter notification dialogs
* Automatic window foregrounding
* Saved connection settings
* Saved username
* Client disconnect handling

## License

Add your preferred license here.
