# Building a Windows .exe for the client

This has to be built on a Windows machine (or in a Windows VM) — PyInstaller
bundles the interpreter for whatever OS you build on, and reliably
cross-building a Windows .exe from Linux/macOS isn't something I can do
from here.

## One-time setup (on Windows)

1. Install Python 3.10+ from python.org. **Use the official installer** —
   it includes tkinter by default. (The Microsoft Store version and some
   other distributions sometimes strip it out.)
2. Open a terminal in the project root (the folder containing `client/`,
   `server/`, `shared/`, `run_client.py`) and run:

```
pip install pyinstaller
pip install winotify   :: optional, enables native Windows toast notifications
```

## Build the exe

From the project root:

```
pyinstaller --noconfirm --onefile --windowed --name "LAN Notify" run_client.py
```

- `--onefile` — one single .exe to hand out, easiest to share on the LAN.
- `--windowed` — no console window popping up behind the GUI.
- Output lands at `dist\LAN Notify.exe`. That's the only file people need —
  they don't need Python installed at all.

Optional: add an icon with `--icon path\to\icon.ico`.

## Handing it out

- Just share `dist\LAN Notify.exe` (e.g. drop it in a shared folder, or a
  group chat). No installer needed.
- First run on someone else's machine may get a SmartScreen warning since
  the exe isn't code-signed ("Windows protected your PC" → More info → Run
  anyway). That's expected for an unsigned indie exe, not a sign anything's
  wrong.
- Each person still needs to know the server's LAN IP and port when they
  open it — same as running from source.
- Settings (host/port/username) now save to
  `%APPDATA%\LAN Notify\config.json` per user, so this now correctly
  persists between runs of the packaged exe (it wouldn't have with the
  original config.py, which saved next to the script — a folder that gets
  wiped after every run once frozen).

## The server

The exe above is the **client only**. Keep running `server/main.py` the
normal way (`python -m server.main`) on whichever machine is acting as the
host — it's a console app, nobody needs a shortcut for it, and freezing it
isn't necessary unless you specifically want to hand the server off to
someone without Python too.

If you do want a server .exe later: build against `run_server.py` at the
project root (not `server/main.py` directly), for the same reason as the
client — `server/main.py` does `from shared.protocol import ...`, a
sibling-package import that only resolves if the project root is on
sys.path. Building from `server/main.py` directly would put `server/`
itself on the path instead and break that import.

```
pyinstaller --noconfirm --onefile --console --name "LAN Notify Server" run_server.py
```

(`--console` here, not `--windowed` — you want to see connect/disconnect
log lines.)
