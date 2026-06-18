from gmm.infrastructure.dbus_builders import monitor_struct, logical_monitor_struct


def get_mode_width(mode_id):
    try:
        return int(str(mode_id).split('x')[0])
    except Exception:
        return 1920


def _build_rects(logical_monitors, layout_mode):
    lms = []
    for lm in logical_monitors:
        x, y, scale, transform, primary, monitors = int(lm[0]), int(lm[1]), float(lm[2]), int(lm[3]), bool(lm[4]), lm[5]

        if monitors:
            mode_id = str(monitors[0][1])
            try:
                parts = mode_id.split('x')
                mode_w, mode_h = int(parts[0]), int(parts[1].split('@')[0])
            except Exception:
                mode_w, mode_h = 1920, 1080
        else:
            mode_w, mode_h = 1920, 1080

        if transform in (1, 3, 5, 7):
            mode_w, mode_h = mode_h, mode_w

        if layout_mode == 1:  # logical
            w, h = int(round(mode_w / scale)), int(round(mode_h / scale))
        else:  # physical
            w, h = mode_w, mode_h

        lms.append({'x': x, 'y': y, 'w': w, 'h': h, 'scale': scale, 'transform': transform, 'primary': primary, 'monitors': monitors})
    return lms


def _normalize(lms):
    if not lms:
        return
    min_x = min(lm['x'] for lm in lms)
    min_y = min(lm['y'] for lm in lms)
    for lm in lms:
        lm['x'] -= min_x
        lm['y'] -= min_y


def _are_adjacent(a, b):
    if (a['x'] + a['w'] == b['x']) or (b['x'] + b['w'] == a['x']):
        return min(a['y'] + a['h'], b['y'] + b['h']) - max(a['y'], b['y']) > 0
    if (a['y'] + a['h'] == b['y']) or (b['y'] + b['h'] == a['y']):
        return min(a['x'] + a['w'], b['x'] + b['w']) - max(a['x'], b['x']) > 0
    return False


def _find_components(lms):
    visited = set()
    components = []
    for i in range(len(lms)):
        if i in visited:
            continue
        comp, queue = [i], [i]
        visited.add(i)
        while queue:
            curr = queue.pop(0)
            for j in range(len(lms)):
                if j not in visited and _are_adjacent(lms[curr], lms[j]):
                    visited.add(j)
                    comp.append(j)
                    queue.append(j)
        components.append(comp)
    return components


def _best_snap(lms, comp, placed_indices):
    best = None
    min_gap = float('inf')
    for i in comp:
        rem = lms[i]
        for j in placed_indices:
            pl = lms[j]
            oy = min(rem['y'] + rem['h'], pl['y'] + pl['h']) - max(rem['y'], pl['y'])
            if oy > 0:
                if rem['x'] >= pl['x'] + pl['w']:
                    gap = rem['x'] - (pl['x'] + pl['w'])
                    if gap < min_gap:
                        min_gap, best = gap, (-gap, 0)
                elif rem['x'] + rem['w'] <= pl['x']:
                    gap = pl['x'] - (rem['x'] + rem['w'])
                    if gap < min_gap:
                        min_gap, best = gap, (gap, 0)
            ox = min(rem['x'] + rem['w'], pl['x'] + pl['w']) - max(rem['x'], pl['x'])
            if ox > 0:
                if rem['y'] >= pl['y'] + pl['h']:
                    gap = rem['y'] - (pl['y'] + pl['h'])
                    if gap < min_gap:
                        min_gap, best = gap, (0, -gap)
                elif rem['y'] + rem['h'] <= pl['y']:
                    gap = pl['y'] - (rem['y'] + rem['h'])
                    if gap < min_gap:
                        min_gap, best = gap, (0, gap)
    return best


def _place_components(lms, components):
    main_idx = next((i for i, comp in enumerate(components) if any(lms[j]['primary'] for j in comp)), 0)
    placed = set(components[main_idx])
    remaining = [components[i] for i in range(len(components)) if i != main_idx]

    while remaining:
        snap = [(i, _best_snap(lms, comp, placed)) for i, comp in enumerate(remaining)]
        candidates = [(i, s) for i, s in snap if s is not None]

        if candidates:
            best_idx, (dx, dy) = min(candidates, key=lambda t: abs(t[1][0]) + abs(t[1][1]))
            comp = remaining.pop(best_idx)
            for j in comp:
                lms[j]['x'] += dx
                lms[j]['y'] += dy
                placed.add(j)
        else:
            rightmost_x = max(lms[j]['x'] + lms[j]['w'] for j in placed)
            comp = remaining.pop(0)
            leftmost_x = min(lms[j]['x'] for j in comp)
            for j in comp:
                lms[j]['x'] += rightmost_x - leftmost_x
                lms[j]['y'] = 0
                placed.add(j)


def _to_dbus_structs(lms):
    result = []
    for lm in lms:
        mons = [monitor_struct(m[0], m[1]) for m in lm['monitors']]
        result.append(logical_monitor_struct(lm['x'], lm['y'], lm['scale'], lm['transform'], lm['primary'], mons))
    return result


def adjust_layout(new_logical_monitors, layout_mode):
    lms = _build_rects(new_logical_monitors, layout_mode)
    _normalize(lms)
    components = _find_components(lms)
    _place_components(lms, components)
    _normalize(lms)
    return _to_dbus_structs(lms)
