"""
Entry point for building a standalone executable.

This must live at the project root (not inside client/) so that when
PyInstaller analyzes it, the project root ends up on sys.path and
`import client...` / `import shared...` resolve correctly. Running
client/main.py directly as the PyInstaller entry point would instead
put client/ itself on sys.path, breaking those package-qualified imports.

For normal (non-packaged) use, `python -m client.main` from the project
root still works exactly as before - this file only matters for building
the .exe.

Also wraps startup in a try/except that writes a crash log: a --windowed
build has no console, so an unhandled exception on startup would otherwise
just vanish with zero indication anything went wrong.
"""

import sys
import traceback


def main():
    from client.gui import App

    app = App()
    app.mainloop()


def _write_crash_log(exc):
    try:
        from client.config import _config_dir

        log_dir = _config_dir()
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "crash.log"

        with log_path.open("a", encoding="utf-8") as f:
            f.write("---- crash ----\n")
            traceback.print_exc(file=f)

        return log_path

    except Exception:
        # If even crash logging fails, there's nothing more we can do -
        # don't let the crash-logging path itself raise and mask the
        # original error.
        return None


if __name__ == "__main__":
    try:
        main()

    except Exception as ex:
        log_path = _write_crash_log(ex)

        try:
            import tkinter.messagebox as messagebox

            detail = f"\n\nDetails were saved to:\n{log_path}" if log_path else ""

            messagebox.showerror(
                "OfficeTalk - Startup Error",
                f"OfficeTalk failed to start.\n\n{ex}{detail}"
            )

        except Exception:
            # If tkinter itself is what's broken, there's no dialog to
            # show - the crash log (if it was written) is the only
            # record of what happened.
            pass

        sys.exit(1)
