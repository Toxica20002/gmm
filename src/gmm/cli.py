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

def find_best_mode(modes, width, height):
    matching = [m for m in modes if m[1] == width and m[2] == height]
    if not matching:
        return None
    
    # 1. Prefer current mode
    for m in matching:
        if m[6].get('is-current'):
            return m[0]
            
    # 2. Prefer preferred mode
    for m in matching:
        if m[6].get('is-preferred'):
            return m[0]
            
    # 3. Prefer refresh rate closest to 60Hz
    matching_sorted = sorted(matching, key=lambda m: abs(m[3] - 60.0))
    return matching_sorted[0][0]

def find_common_resolution_multi(source_conn, target_conns, physical_map):
    source_modes = physical_map[source_conn]['modes']
    common_res = {(m[1], m[2]) for m in source_modes}
    
    for target in target_conns:
        target_modes = physical_map[target]['modes']
        target_res = {(m[1], m[2]) for m in target_modes}
        common_res = common_res.intersection(target_res)
        
    if not common_res:
        return None
        
    # Sort by area descending (highest resolution first)
    sorted_common = sorted(list(common_res), key=lambda x: x[0] * x[1], reverse=True)
    best_res = sorted_common[0]
    
    source_mode_id = find_best_mode(source_modes, best_res[0], best_res[1])
    
    target_mode_ids = {}
    for target in target_conns:
        target_mode_ids[target] = find_best_mode(physical_map[target]['modes'], best_res[0], best_res[1])
        
    return source_mode_id, target_mode_ids, best_res

def print_status(physical_map, logical_monitors):
    print("=== Connected Physical Monitors ===")
    for conn, info in physical_map.items():
        curr = info['current']
        status = f"Active: {curr[1]}x{curr[2]}@{curr[3]:.1f}Hz" if curr else "Disabled"
        print(f"  - {conn:<8} : {info['vendor']} {info['product']} ({status})")
        
    print("\n=== Logical Layout Groups ===")
    for i, lm in enumerate(logical_monitors):
        x, y, scale, transform, primary, monitors, lm_props = lm
        mon_names = [m[0] for m in monitors]
        primary_str = " [Primary]" if primary else ""
        mirror_str = " (Mirrored)" if len(mon_names) > 1 else ""
        print(f"  Group {i+1}: {', '.join(mon_names)}{primary_str}{mirror_str} at Pos: ({x}, {y}), Scale: {scale}")

def print_help():
    print("""
GNOME Wayland/X11 CLI tool to mirror or unmirror displays (gmm).

Usage:
  gmm list monitor                             # List connected displays and layout
  gmm <source> <target1> [target2 ... targetN] # Mirror one or more targets onto source
  gmm unmirror <monitor>                       # Make <monitor> an independent extended display
  gmm unmirror all                             # Separate all mirrored monitors
  gmm --unmirror <monitor>
  gmm --unmirror all

Examples:
  gmm HDMI-5 DP-4
  gmm HDMI-5 DP-3 DP-4
  gmm unmirror DP-4
  gmm unmirror all
""")

def get_mode_width(mode_id):
    try:
        return int(str(mode_id).split('x')[0])
    except Exception:
        return 1920

def main():
    interface = get_dbus_interface()
    serial, physical_monitors, logical_monitors, properties = interface.GetCurrentState()
    physical_map = build_physical_map(physical_monitors)
    
    args = sys.argv[1:]
    
    # 1. No arguments: print help and status
    if not args:
        print_status(physical_map, logical_monitors)
        print_help()
        return
        
    # 2. list monitor subcommand
    if len(args) >= 1 and args[0] == 'list':
        if len(args) >= 2 and args[1] == 'monitor':
            print_status(physical_map, logical_monitors)
            return
        else:
            print("Error: Unknown subcommand. Did you mean 'gmm list monitor'?", file=sys.stderr)
            sys.exit(1)
            
    # 3. Unmirror action
    if args[0] in ('--unmirror', '-u', 'unmirror'):
        if len(args) < 2:
            print("Error: Please specify the monitor to unmirror or 'all'.", file=sys.stderr)
            sys.exit(1)
        unmirror_target = args[1]
        
        # Unmirror all monitors
        if unmirror_target == 'all':
            print("Separating all mirrored monitors...")
            new_logical_monitors = []
            monitors_to_separate = []
            
            # Keep first monitor of each group, collect extra ones
            for lm in logical_monitors:
                x, y, scale, transform, primary, monitors, lm_props = lm
                if not monitors:
                    continue
                    
                first_mon = monitors[0]
                conn, vendor, product, serial_str = first_mon
                
                for extra_mon in monitors[1:]:
                    monitors_to_separate.append(extra_mon[0])
                    
                mode_id = None
                if conn in physical_map:
                    if physical_map[conn]['current']:
                        mode_id = physical_map[conn]['current'][0]
                    elif physical_map[conn]['preferred']:
                        mode_id = physical_map[conn]['preferred'][0]
                if not mode_id:
                    mode_id = first_mon[1]
                    
                dbus_monitors_list = [
                    dbus.Struct((dbus.String(conn), dbus.String(mode_id), dbus.Dictionary({}, signature='sv')), signature='(ssa{sv})')
                ]
                new_logical_monitors.append(
                    dbus.Struct((
                        dbus.Int32(x), dbus.Int32(y), dbus.Double(scale),
                        dbus.UInt32(transform), dbus.Boolean(primary),
                        dbus.Array(dbus_monitors_list, signature='(ssa{sv})')
                    ), signature='(iiduba(ssa{sv}))')
                )
                
            if not monitors_to_separate:
                print("No monitors are currently mirrored. Nothing to separate.")
                return
                
            # Place each separated monitor to the right
            for conn in monitors_to_separate:
                rightmost_x = 0
                for nlm in new_logical_monitors:
                    x = nlm[0]
                    monitors = nlm[5]
                    max_width = 0
                    for m in monitors:
                        max_width = max(max_width, get_mode_width(m[1]))
                    rightmost_x = max(rightmost_x, x + max_width)
                    
                print(f"Placing separated monitor '{conn}' at coordinate x={rightmost_x}...")
                pref_mode = physical_map[conn]['preferred']
                mode_id = pref_mode[0] if pref_mode else physical_map[conn]['modes'][0][0]
                dbus_monitors_list = [
                    dbus.Struct((dbus.String(conn), dbus.String(mode_id), dbus.Dictionary({}, signature='sv')), signature='(ssa{sv})')
                ]
                new_logical_monitors.append(
                    dbus.Struct((
                        dbus.Int32(rightmost_x), dbus.Int32(0), dbus.Double(1.0),
                        dbus.UInt32(0), dbus.Boolean(False),
                        dbus.Array(dbus_monitors_list, signature='(ssa{sv})')
                    ), signature='(iiduba(ssa{sv}))')
                )
                
        # Unmirror specific monitor
        else:
            if unmirror_target not in physical_map:
                print(f"Error: Monitor '{unmirror_target}' not found.", file=sys.stderr)
                sys.exit(1)
                
            is_mirrored = False
            for lm in logical_monitors:
                monitors = lm[5]
                if len(monitors) > 1 and any(m[0] == unmirror_target for m in monitors):
                    is_mirrored = True
                    break
                    
            if not is_mirrored:
                print(f"Monitor '{unmirror_target}' is not currently mirrored in any group.", file=sys.stderr)
                
            rightmost_x = 0
            for lm in logical_monitors:
                x, y, scale, transform, primary, monitors, lm_props = lm
                lm_width = 0
                for mon in monitors:
                    conn = mon[0]
                    if conn in physical_map:
                        curr = physical_map[conn]['current']
                        pref = physical_map[conn]['preferred']
                        if curr:
                            lm_width = max(lm_width, curr[1])
                        elif pref:
                            lm_width = max(lm_width, pref[1])
                rightmost_x = max(rightmost_x, x + lm_width)
                
            print(f"Separating '{unmirror_target}' and placing it at coordinate x={rightmost_x}...")
            
            new_logical_monitors = []
            for lm in logical_monitors:
                x, y, scale, transform, primary, monitors, lm_props = lm
                new_monitors = []
                for mon in monitors:
                    conn = mon[0]
                    if conn == unmirror_target:
                        continue
                    mode_id = None
                    if conn in physical_map:
                        if physical_map[conn]['current']:
                            mode_id = physical_map[conn]['current'][0]
                        elif physical_map[conn]['preferred']:
                            mode_id = physical_map[conn]['preferred'][0]
                    if not mode_id:
                        mode_id = mon[1]
                    new_monitors.append((conn, mode_id))
                    
                if not new_monitors:
                    continue
                    
                dbus_monitors_list = [
                    dbus.Struct((dbus.String(c), dbus.String(m), dbus.Dictionary({}, signature='sv')), signature='(ssa{sv})')
                    for c, m in new_monitors
                ]
                new_logical_monitors.append(
                    dbus.Struct((
                        dbus.Int32(x), dbus.Int32(y), dbus.Double(scale),
                        dbus.UInt32(transform), dbus.Boolean(primary),
                        dbus.Array(dbus_monitors_list, signature='(ssa{sv})')
                    ), signature='(iiduba(ssa{sv}))')
                )
                
            pref_mode = physical_map[unmirror_target]['preferred']
            mode_id = pref_mode[0] if pref_mode else physical_map[unmirror_target]['modes'][0][0]
            dbus_monitors_list = [
                dbus.Struct((dbus.String(unmirror_target), dbus.String(mode_id), dbus.Dictionary({}, signature='sv')), signature='(ssa{sv})')
            ]
            new_logical_monitors.append(
                dbus.Struct((
                    dbus.Int32(rightmost_x), dbus.Int32(0), dbus.Double(1.0),
                    dbus.UInt32(0), dbus.Boolean(False),
                    dbus.Array(dbus_monitors_list, signature='(ssa{sv})')
                ), signature='(iiduba(ssa{sv}))')
            )
            
    # 4. Mirror action (1 source to N targets)
    elif len(args) >= 2:
        source_conn = args[0]
        target_conns = args[1:]
        
        if source_conn not in physical_map:
            print(f"Error: Source monitor '{source_conn}' not found.", file=sys.stderr)
            sys.exit(1)
        for target_conn in target_conns:
            if target_conn not in physical_map:
                print(f"Error: Target monitor '{target_conn}' not found.", file=sys.stderr)
                sys.exit(1)
                
        source_mode_id = None
        target_mode_ids = {}
        
        # Check current resolution of source
        source_curr = physical_map[source_conn]['current']
        if source_curr:
            w, h = source_curr[1], source_curr[2]
            all_supported = True
            temp_ids = {}
            for target in target_conns:
                mode_id = find_best_mode(physical_map[target]['modes'], w, h)
                if mode_id:
                    temp_ids[target] = mode_id
                else:
                    all_supported = False
                    break
            if all_supported:
                source_mode_id = source_curr[0]
                target_mode_ids = temp_ids
                print(f"Mirroring at source resolution: {w}x{h}")
                
        # If target doesn't support source's current, try preferred
        if not source_mode_id:
            source_pref = physical_map[source_conn]['preferred']
            if source_pref:
                w, h = source_pref[1], source_pref[2]
                all_supported = True
                temp_ids = {}
                for target in target_conns:
                    mode_id = find_best_mode(physical_map[target]['modes'], w, h)
                    if mode_id:
                        temp_ids[target] = mode_id
                    else:
                        all_supported = False
                        break
                if all_supported:
                    source_mode_id = source_pref[0]
                    target_mode_ids = temp_ids
                    print(f"Mirroring at source preferred resolution: {w}x{h}")
                    
        # Fallback to any common resolution
        if not source_mode_id:
            common_info = find_common_resolution_multi(source_conn, target_conns, physical_map)
            if common_info:
                source_mode_id, target_mode_ids, res = common_info
                print(f"Mirroring at common resolution: {res[0]}x{res[1]}")
            else:
                print(f"Error: No common resolution found between '{source_conn}' and all targets: {', '.join(target_conns)}.", file=sys.stderr)
                sys.exit(1)
                
        print(f"Mirroring targets: {', '.join(target_conns)} onto source: '{source_conn}'...")
        
        # Ensure source is in the active layout
        source_in_layout = False
        for lm in logical_monitors:
            if any(m[0] == source_conn for m in lm[5]):
                source_in_layout = True
                break
                
        if not source_in_layout:
            rightmost_x = 0
            for lm in logical_monitors:
                x, y, scale, transform, primary, monitors, lm_props = lm
                lm_width = 0
                for mon in monitors:
                    c = mon[0]
                    if c in physical_map:
                        curr = physical_map[c]['current']
                        pref = physical_map[c]['preferred']
                        if curr:
                            lm_width = max(lm_width, curr[1])
                        elif pref:
                            lm_width = max(lm_width, pref[1])
                rightmost_x = max(rightmost_x, x + lm_width)
            
            print(f"Source monitor '{source_conn}' was not in the active layout. Enabling it at pos: ({rightmost_x}, 0)...")
            dummy_lm = (
                rightmost_x, 0, 1.0, 0, False,
                [(source_conn, '', '', '')],
                {}
            )
            logical_monitors.append(dummy_lm)
            
        new_logical_monitors = []
        for lm in logical_monitors:
            x, y, scale, transform, primary, monitors, lm_props = lm
            new_monitors = []
            for mon in monitors:
                conn = mon[0]
                if conn in target_conns:
                    continue
                    
                mode_id = None
                if conn == source_conn:
                    mode_id = source_mode_id
                elif conn in physical_map:
                    if physical_map[conn]['current']:
                        mode_id = physical_map[conn]['current'][0]
                    elif physical_map[conn]['preferred']:
                        mode_id = physical_map[conn]['preferred'][0]
                if not mode_id:
                    mode_id = mon[1]
                new_monitors.append((conn, mode_id))
                
                if conn == source_conn:
                    for target in target_conns:
                        new_monitors.append((target, target_mode_ids[target]))
                        
            if not new_monitors:
                continue
                
            dbus_monitors_list = [
                dbus.Struct((dbus.String(c), dbus.String(m), dbus.Dictionary({}, signature='sv')), signature='(ssa{sv})')
                for c, m in new_monitors
            ]
            new_logical_monitors.append(
                dbus.Struct((
                    dbus.Int32(x), dbus.Int32(y), dbus.Double(scale),
                    dbus.UInt32(transform), dbus.Boolean(primary),
                    dbus.Array(dbus_monitors_list, signature='(ssa{sv})')
                ), signature='(iiduba(ssa{sv}))')
            )
            
    else:
        print_help()
        sys.exit(1)
            
    # Apply the configuration (persistent method = 2)
    try:
        interface.ApplyMonitorsConfig(
            dbus.UInt32(serial),
            dbus.UInt32(2),
            new_logical_monitors,
            dbus.Dictionary({}, signature='sv')
        )
        print("Success: Display configuration applied successfully!")
    except Exception as e:
        print(f"Error: Failed to apply configuration: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
