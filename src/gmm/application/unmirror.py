import sys

from gmm.domain.layout import get_mode_width
from gmm.domain.monitor import get_active_mode_id, get_monitor_width
from gmm.infrastructure.dbus_builders import monitor_struct, logical_monitor_struct


def _rightmost_x(logical_monitors, physical_map):
    rightmost = 0
    for lm in logical_monitors:
        x = lm[0]
        width = max((get_monitor_width(m[0], physical_map) for m in lm[5]), default=0)
        rightmost = max(rightmost, x + width)
    return rightmost


def _preferred_mode_id(conn, physical_map):
    pref = physical_map[conn]['preferred']
    return pref[0] if pref else physical_map[conn]['modes'][0][0]


def build_unmirror_all_config(physical_map, logical_monitors):
    print("Separating all mirrored monitors...")
    new_lms = []
    to_separate = []

    for lm in logical_monitors:
        x, y, scale, transform, primary, monitors, *_ = lm
        if not monitors:
            continue

        first_mon = monitors[0]
        conn, vendor, product, serial_str = first_mon
        to_separate.extend(m[0] for m in monitors[1:])

        mode_id = get_active_mode_id(conn, physical_map, first_mon[1])
        new_lms.append(logical_monitor_struct(x, y, scale, transform, primary, [monitor_struct(conn, mode_id)]))

    if not to_separate:
        print("No monitors are currently mirrored. Nothing to separate.")
        return None

    for conn in to_separate:
        rx = max(
            (int(nlm[0]) + max((get_mode_width(m[1]) for m in nlm[5]), default=0))
            for nlm in new_lms
        ) if new_lms else 0
        print(f"Placing separated monitor '{conn}' at coordinate x={rx}...")
        mode_id = _preferred_mode_id(conn, physical_map)
        new_lms.append(logical_monitor_struct(rx, 0, 1.0, 0, False, [monitor_struct(conn, mode_id)]))

    return new_lms


def build_unmirror_config(unmirror_target, physical_map, logical_monitors):
    if unmirror_target not in physical_map:
        print(f"Error: Monitor '{unmirror_target}' not found.", file=sys.stderr)
        sys.exit(1)

    is_mirrored = any(
        len(lm[5]) > 1 and any(m[0] == unmirror_target for m in lm[5])
        for lm in logical_monitors
    )
    if not is_mirrored:
        print(f"Monitor '{unmirror_target}' is not currently mirrored in any group.", file=sys.stderr)

    rx = _rightmost_x(logical_monitors, physical_map)
    print(f"Separating '{unmirror_target}' and placing it at coordinate x={rx}...")

    new_lms = []
    for lm in logical_monitors:
        x, y, scale, transform, primary, monitors, *_ = lm
        kept = [(m[0], get_active_mode_id(m[0], physical_map, m[1])) for m in monitors if m[0] != unmirror_target]
        if not kept:
            continue
        new_lms.append(logical_monitor_struct(x, y, scale, transform, primary, [monitor_struct(c, mid) for c, mid in kept]))

    mode_id = _preferred_mode_id(unmirror_target, physical_map)
    new_lms.append(logical_monitor_struct(rx, 0, 1.0, 0, False, [monitor_struct(unmirror_target, mode_id)]))

    return new_lms
