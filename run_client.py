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
"""

from client.gui import App


if __name__ == "__main__":
    app = App()
    app.mainloop()
