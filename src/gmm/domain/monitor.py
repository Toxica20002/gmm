def build_physical_map(physical_monitors):
    physical_map = {}
    for pm in physical_monitors:
        spec, modes, props = pm
        connector, vendor, product, serial_str = spec

        current_mode = None
        preferred_mode = None
        for mode in modes:
            mode_id, width, height, rate, scale_mult, flags, mode_props = mode
            if mode_props.get('is-current'):
                current_mode = (mode_id, width, height, rate)
            if mode_props.get('is-preferred'):
                preferred_mode = (mode_id, width, height, rate)

        physical_map[connector] = {
            'vendor': vendor,
            'product': product,
            'current': current_mode,
            'preferred': preferred_mode,
            'modes': modes
        }
    return physical_map


def find_best_mode(modes, width, height, target_rate=None):
    matching = [m for m in modes if m[1] == width and m[2] == height]
    if not matching:
        return None

    if target_rate is not None:
        matching_sorted = sorted(matching, key=lambda m: abs(m[3] - target_rate))
        if abs(matching_sorted[0][3] - target_rate) < 1.0:
            return matching_sorted[0][0]
        return None

    for m in matching:
        if m[6].get('is-current'):
            return m[0]

    for m in matching:
        if m[6].get('is-preferred'):
            return m[0]

    matching_sorted = sorted(matching, key=lambda m: abs(m[3] - 60.0))
    return matching_sorted[0][0]


def get_active_mode_id(conn, physical_map, fallback=None):
    info = physical_map.get(conn)
    if info:
        if info['current']:
            return info['current'][0]
        if info['preferred']:
            return info['preferred'][0]
    return fallback


def get_monitor_width(conn, physical_map):
    info = physical_map.get(conn)
    if info:
        if info['current']:
            return info['current'][1]
        if info['preferred']:
            return info['preferred'][1]
    return 0


def find_common_resolution_multi(source_conn, target_conns, physical_map):
    source_modes = physical_map[source_conn]['modes']
    common_res = {(m[1], m[2]) for m in source_modes}

    for target in target_conns:
        target_modes = physical_map[target]['modes']
        target_res = {(m[1], m[2]) for m in target_modes}
        common_res = common_res.intersection(target_res)

    if not common_res:
        return None

    sorted_common = sorted(list(common_res), key=lambda x: x[0] * x[1], reverse=True)
    best_res = sorted_common[0]

    source_mode_id = find_best_mode(source_modes, best_res[0], best_res[1])

    target_mode_ids = {}
    for target in target_conns:
        target_mode_ids[target] = find_best_mode(physical_map[target]['modes'], best_res[0], best_res[1])

    return source_mode_id, target_mode_ids, best_res
