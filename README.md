
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

On Linux, `notify-send` (part of libnotify, installed on most desktops) is used first; `notify2` is only a fallback.

### Optional: System Tray

```bash
pip install pystray pillow
```

With `pystray` installed, OfficeTalk shows a tray icon (Windows/Linux) with **Show**, **Status** and **Quit**, and closing the window keeps it running in the tray.

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

Server options:

```text
-p PORT          TCP port (default 5000)
-a ADDRESS       address to bind (default 0.0.0.0)
-n NAME          name shown in clients' server list (default: hostname)
--no-discovery   don't answer LAN discovery broadcasts
```

The server also answers discovery broadcasts on **UDP port 5001**, so clients can find it automatically.

## Running the Client

Open another terminal:

```bash
python -m client.main
```

The client will open the Tkinter interface.

Servers on your network are listed automatically under **Servers on your network** - pick one, or enter the server's LAN IP address and port yourself (click **Scan** to search again).

For example:

```text
Server Address: 192.168.1.100
Port:           5000
```

Then click **Connect**.

## Configuration

The client automatically saves connection information, the username and settings in a per-user `config.json`:

```text
Windows: %APPDATA%\LAN Notify\config.json
Linux:   ~/.config/lan-notify/config.json
macOS:   ~/Library/Application Support/LAN Notify/config.json
```

Message history is saved next to it in `history.json` (last 500 messages).

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

* **Select all** / **Clear** pick every connected user at once.
* **Quick message** sends a saved preset (e.g. "Lunch?") to the selected users in one click. Edit the list in **Settings**.
* The status bar tells you if a recipient was offline and the message wasn't delivered.
* **Status** (Available / Busy / Away) is shown to everyone in the user list. While **Busy**, incoming messages only show a native notification and go to History - no popup and no window stealing focus.
* **History** lists sent and received messages. Double-click one to read it again or reply.
* **Settings** has: start OfficeTalk when you log in, connect and sign in automatically (and keep reconnecting if the server goes away), and keep running in the tray when the window is closed.

Usernames must be unique on the server (case-insensitive).

## Compatibility

Clients and servers of any version work together. Everything added after v0.0.1 is opt-in: the server lists the extra features it supports when a client connects, and a client only asks for (and uses) the ones the server lists.

* **New client, old server:** the original protocol is used. Messaging, replies, history, quick messages, tray and auto-connect all work. Status is local only (Busy still silences popups), usernames aren't checked for duplicates, and there's no offline-delivery warning.
* **Old client, new server:** the old client gets exactly the original behaviour.

## Notifications

When a notification is received, the client:

1. Brings the LAN Notify window to the foreground (unless your status is Busy).
2. Attempts to display a native operating-system notification.
3. Displays a message dialog with **Copy** and **Reply** buttons (unless Busy).
4. Saves the message to History.

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

TCP port `5000` must be allowed for connections from the local network, and UDP port `5001` for automatic server discovery.

The server itself listens on:

```text
0.0.0.0:5000
```

You can change the port with `-p`:

```bash
python -m server.main -p 6000
```

If you change the server port, use the same port when connecting from the clients (discovered servers report their port automatically).

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
* Automatic server discovery on the LAN
* Reply from the notification dialog
* Message history
* System tray icon, start on login, auto-connect/reconnect
* Select all + quick messages
* Available / Busy / Away status
* Unique usernames and delivery feedback

## License

zlib
