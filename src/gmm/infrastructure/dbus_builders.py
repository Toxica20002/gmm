import dbus


def monitor_struct(conn, mode_id):
    return dbus.Struct(
        (dbus.String(conn), dbus.String(mode_id), dbus.Dictionary({}, signature='sv')),
        signature='(ssa{sv})'
    )


def logical_monitor_struct(x, y, scale, transform, primary, monitors_list):
    return dbus.Struct((
        dbus.Int32(x), dbus.Int32(y), dbus.Double(scale),
        dbus.UInt32(transform), dbus.Boolean(primary),
        dbus.Array(monitors_list, signature='(ssa{sv})')
    ), signature='(iiduba(ssa{sv}))')
