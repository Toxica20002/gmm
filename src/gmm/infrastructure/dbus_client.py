import sys
import dbus


def get_dbus_interface():
    try:
        bus = dbus.SessionBus()
        obj = bus.get_object("org.gnome.Mutter.DisplayConfig", "/org/gnome/Mutter/DisplayConfig")
        return dbus.Interface(obj, "org.gnome.Mutter.DisplayConfig")
    except Exception as e:
        print(f"Error: Cannot connect to GNOME DisplayConfig D-Bus interface: {e}", file=sys.stderr)
        print("This tool requires a running GNOME Wayland/X11 session.", file=sys.stderr)
        sys.exit(1)
