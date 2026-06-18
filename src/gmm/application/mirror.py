import sys

from gmm.domain.monitor import find_best_mode, find_common_resolution_multi, get_active_mode_id, get_monitor_width
from gmm.infrastructure.dbus_builders import monitor_struct, logical_monitor_struct


def _validate(source_conn, target_conns, physical_map):
    if source_conn not in physical_map:
        print(f"Error: Source monitor '{source_conn}' not found.", file=sys.stderr)
        sys.exit(1)
    for conn in target_conns:
        if conn not in physical_map:
            print(f"Error: Target monitor '{conn}' not found.", file=sys.stderr)
            sys.exit(1)


def _try_resolution(w, h, target_conns, physical_map):
    """Return target mode IDs if all targets support WxH, else None."""
    ids = {}
    for target in target_conns:
        mode_id = find_best_mode(physical_map[target]['modes'], w, h)
        if not mode_id:
            return None
        ids[target] = mode_id
    return ids


def _find_mode_ids(source_conn, target_conns, physical_map):
    source_curr = physical_map[source_conn]['current']
    if source_curr:
        w, h = source_curr[1], source_curr[2]
        ids = _try_resolution(w, h, target_conns, physical_map)
        if ids is not None:
            print(f"Mirroring at source resolution: {w}x{h}")
            return source_curr[0], ids

    source_pref = physical_map[source_conn]['preferred']
    if source_pref:
        w, h = source_pref[1], source_pref[2]
        ids = _try_resolution(w, h, target_conns, physical_map)
        if ids is not None:
            print(f"Mirroring at source preferred resolution: {w}x{h}")
            return source_pref[0], ids

    common = find_common_resolution_multi(source_conn, target_conns, physical_map)
    if common:
        source_mode_id, target_mode_ids, res = common
        print(f"Mirroring at common resolution: {res[0]}x{res[1]}")
        return source_mode_id, target_mode_ids

    print(f"Error: No common resolution found between '{source_conn}' and targets: {', '.join(target_conns)}.", file=sys.stderr)
    sys.exit(1)


def _ensure_source_active(source_conn, physical_map, logical_monitors):
    if any(m[0] == source_conn for lm in logical_monitors for m in lm[5]):
        return
    rightmost_x = max(
        (lm[0] + max((get_monitor_width(m[0], physical_map) for m in lm[5]), default=0))
        for lm in logical_monitors
    ) if logical_monitors else 0
    print(f"Source monitor '{source_conn}' was not in the active layout. Enabling it at pos: ({rightmost_x}, 0)...")
    logical_monitors.append((rightmost_x, 0, 1.0, 0, False, [(source_conn, '', '', '')], {}))


def _build_lm_monitors(monitors, source_conn, target_conns, source_mode_id, target_mode_ids, physical_map):
    result = []
    for mon in monitors:
        conn = mon[0]
        if conn in target_conns:
            continue
        mode_id = source_mode_id if conn == source_conn else get_active_mode_id(conn, physical_map, mon[1])
        result.append((conn, mode_id))
        if conn == source_conn:
            result.extend((t, target_mode_ids[t]) for t in target_conns)
    return result


def _build_config(source_conn, target_conns, source_mode_id, target_mode_ids, physical_map, logical_monitors):
    result = []
    for lm in logical_monitors:
        x, y, scale, transform, primary, monitors, *_ = lm
        new_monitors = _build_lm_monitors(monitors, source_conn, target_conns, source_mode_id, target_mode_ids, physical_map)
        if not new_monitors:
            continue
        mons = [monitor_struct(c, m) for c, m in new_monitors]
        result.append(logical_monitor_struct(x, y, scale, transform, primary, mons))
    return result


def build_mirror_config(source_conn, target_conns, physical_map, logical_monitors):
    _validate(source_conn, target_conns, physical_map)
    source_mode_id, target_mode_ids = _find_mode_ids(source_conn, target_conns, physical_map)
    print(f"Mirroring targets: {', '.join(target_conns)} onto source: '{source_conn}'...")
    _ensure_source_active(source_conn, physical_map, logical_monitors)
    return _build_config(source_conn, target_conns, source_mode_id, target_mode_ids, physical_map, logical_monitors)
