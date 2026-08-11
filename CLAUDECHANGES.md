# What changed

## Connection / disconnection bugs (the main ask)

1. **Voluntary disconnect was showing "Connection lost" instead of "Disconnected".**
   Clicking Disconnect sends a message to the server, which closes its end of
   the socket. That could wake up the client's own background receive thread
   *before* the disconnect button's code got to mark the disconnect as
   intentional — a genuine race condition, confirmed with a live test.
   Fixed by setting an instance flag the instant `disconnect()` is called,
   before any socket I/O happens, so whichever thread notices first still
   reports the correct reason. (`client/network.py`)

2. **Connecting froze the whole window.** `connect()` ran the blocking
   socket connect (up to a 10s timeout) directly on the Tkinter main thread.
   Now it runs in a background thread and reports back via the existing
   event queue, with the Connect button showing a real "Connecting..." state
   instead of just being disabled on a timer and hoping for the best.
   (`client/network.py`, `client/gui.py`, `client/frames/connect.py`)

3. **Username screen didn't check the connection was still alive.** If the
   connection dropped while choosing a username, the app would still send
   you into the main screen as if the username had been accepted. Now it
   checks and shows a message instead. (`client/frames/username.py`)

4. **"Notification sent" was shown even when it wasn't.** Sending while
   disconnected (or losing the connection mid-send) failed silently but
   still told you it worked. Both `set_username` and `send_notification`
   now return whether the send actually succeeded, and the UI reflects that.
   (`client/network.py`, `client/frames/mainframe.py`)

5. **Server held a lock during blocking network sends.** `broadcast_user_list`
   sent to every client while holding the shared lock — one slow/stuck
   client could delay everyone else's user-list update. Sockets are now
   copied out and sent to outside the lock. (`server/main.py`)

All of the above were verified with live socket tests (connect, voluntary
disconnect, server-initiated disconnect, and heartbeat pong-timeout), not
just read through — the race condition in particular only showed up once
actually run.

## Other fixes
- Added macOS notification support (was Windows/Linux only) via `osascript`,
  no extra dependency needed.

## Visual refresh
Added `client/theme.py` — one place that defines the color palette, fonts,
and ttk widget styles, applied consistently across all three screens
(connect, username, main). Replaced the plain default-tkinter look with a
card-based layout, a status dot + colored status text that reflects
connection state at a glance, and consistent spacing/typography.

I don't have access to your other "batch renames" project, so this uses a
clean modern default palette (indigo accent, white cards, soft gray
background) rather than matching it exactly — if you want it to match,
share the palette/style and I can adjust `client/theme.py` (it's the only
file that needs to change).

## Running it
```
# terminal 1
python -m server.main

# terminal 2
python -m client.main
```
Run both from the project root so the `shared` package resolves.
