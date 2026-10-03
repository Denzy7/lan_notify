import sys

from client.autostart import TRAY_ARG
from client.gui import App


if __name__ == "__main__":
    app = App(start_hidden=TRAY_ARG in sys.argv)
    app.mainloop()
