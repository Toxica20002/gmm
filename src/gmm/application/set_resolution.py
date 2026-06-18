import sys

from gmm.domain.monitor import find_best_mode, get_active_mode_id
from gmm.infrastructure.dbus_builders import monitor_struct, logical_monitor_struct


def _find_target_lm(monitor_target, logical_monitors):
    for i, lm in enumerate(logical_monitors):
        if any(m[0] == monitor_target for m in lm[5]):
            return i
    return None


def _resolve_new_mode_ids(group_monitors, w, h, target_rate, physical_map):
    new_mode_ids = {}
    for mon in group_monitors:
        conn = mon[0]
        mode_id = find_best_mode(physical_map[conn]['modes'], w, h, target_rate)
        if not mode_id:
            rate_str = f" @ {target_rate}Hz" if target_rate is not None else ""
            print(f"Error: Resolution {w}x{h}{rate_str} is not supported by monitor '{conn}'.", file=sys.stderr)
            sys.exit(1)
        new_mode_ids[conn] = mode_id
    return new_mode_ids


def build_set_resolution_config(monitor_target, w, h, target_rate, physical_map, logical_monitors):
    if monitor_target not in physical_map:
        print(f"Error: Monitor '{monitor_target}' not found.", file=sys.stderr)
        sys.exit(1)

    target_lm_idx = _find_target_lm(monitor_target, logical_monitors)
    if target_lm_idx is None:
        print(f"Error: Monitor '{monitor_target}' is not currently active.", file=sys.stderr)
        sys.exit(1)

    new_mode_ids = _resolve_new_mode_ids(logical_monitors[target_lm_idx][5], w, h, target_rate, physical_map)

    rate_str = f" @ {target_rate}Hz" if target_rate is not None else ""
    print(f"Setting resolution of group containing '{monitor_target}' to {w}x{h}{rate_str}...")

    result = []
    for i, lm in enumerate(logical_monitors):
        x, y, scale, transform, primary, monitors, *_ = lm
        mons = [
            monitor_struct(m[0], new_mode_ids[m[0]] if i == target_lm_idx else get_active_mode_id(m[0], physical_map, m[1]))
            for m in monitors
        ]
        result.append(logical_monitor_struct(x, y, scale, transform, primary, mons))

    return result
