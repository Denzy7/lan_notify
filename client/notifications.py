import platform
import shutil
import subprocess


class Notifier:

    @staticmethod
    def notify(title, message):
        system = platform.system()

        if system == "Windows":
            return Notifier._windows(title, message)

        if system == "Linux":
            return Notifier._linux(title, message)

        if system == "Darwin":
            return Notifier._macos(title, message)

        print(
            f"[Notifications] Unsupported operating system: {system}"
        )

        return False

    @staticmethod
    def _windows(title, message):
        try:
            from winotify import Notification
        except ImportError:
            print(
                "[Notifications] winotify is not installed.\n"
                "Install it with:\n"
                "    pip install winotify"
            )

            return False

        try:
            notification = Notification(
                app_id="LAN Notify",
                title=title,
                msg=message
            )

            notification.show()

            return True

        except Exception as ex:
            print(
                f"[Notifications] Windows notification failed: {ex}"
            )

            return False

    @staticmethod
    def _linux(title, message):
        # notify-send ships with libnotify on practically every desktop
        # and, unlike notify2, doesn't depend on dbus-python being
        # bundled correctly into a frozen binary.
        if shutil.which("notify-send"):
            try:
                subprocess.Popen(
                    ["notify-send", "--app-name=OfficeTalk", title, message],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                return True

            except Exception as ex:
                print(
                    f"[Notifications] notify-send failed: {ex}"
                )

        try:
            import notify2
        except ImportError:
            print(
                "[Notifications] Neither notify-send nor notify2 is available.\n"
                "Install libnotify (notify-send) or:\n"
                "    pip install notify2"
            )

            return False

        try:
            notify2.init("LAN Notify")

            notification = notify2.Notification(
                title,
                message
            )

            notification.show()

            return True

        except Exception as ex:
            print(
                f"[Notifications] Linux notification failed: {ex}"
            )

            return False

    @staticmethod
    def _macos(title, message):
        # Uses the built-in `osascript` so there's no extra dependency
        # to install on macOS.
        def escape(text):
            return text.replace("\\", "\\\\").replace('"', '\\"')

        script = (
            f'display notification "{escape(message)}" '
            f'with title "{escape(title)}"'
        )

        try:
            # Popen rather than run() so a slow osascript never stalls
            # the Tk event loop that called us.
            subprocess.Popen(
                ["osascript", "-e", script],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            return True

        except Exception as ex:
            print(
                f"[Notifications] macOS notification failed: {ex}"
            )

            return False
