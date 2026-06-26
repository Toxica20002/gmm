import sys
import dbus

from gmm.infrastructure.dbus_client import get_dbus_interface
from gmm.domain.monitor import build_physical_map
from gmm.domain.layout import adjust_layout
from gmm.application.mirror import build_mirror_config
from gmm.application.unmirror import build_unmirror_all_config, build_unmirror_config
from gmm.application.set_resolution import build_set_resolution_config
from gmm.presentation.display import print_status, print_help
from gmm.presentation.list_command import handle_list_command


def _parse_resolution_arg(resolution_str):
    target_rate = None
    if '@' in resolution_str:
        res_part, rate_part = resolution_str.split('@', 1)
        rate_part = rate_part.lower().replace('hz', '').strip()
        try:
            target_rate = float(rate_part)
        except ValueError:
            print(f"Error: Invalid refresh rate format in '{resolution_str}'. Must be like @144 or @144.0Hz.", file=sys.stderr)
            sys.exit(1)
        resolution_str = res_part
    try:
        w, h = resolution_str.split('x')
        return int(w), int(h), target_rate
    except Exception:
        print(f"Error: Invalid resolution format '{resolution_str}'. Must be WxH (e.g. 1920x1080).", file=sys.stderr)
        sys.exit(1)


def _dispatch(args, physical_map, logical_monitors):
    if args[0] == 'list':
        handle_list_command(args, physical_map, logical_monitors)
        return None

    if args[0] in ('set-resolution', 'set-res', 'resolution', 'res'):
        if len(args) < 3:
            print("Error: Please specify the monitor and target resolution (e.g. 1920x1080).", file=sys.stderr)
            sys.exit(1)
        w, h, target_rate = _parse_resolution_arg(args[2])
        return build_set_resolution_config(args[1], w, h, target_rate, physical_map, logical_monitors)

    if args[0] in ('--unmirror', '-u', 'unmirror'):
        if len(args) < 2:
            print("Error: Please specify the monitor to unmirror or 'all'.", file=sys.stderr)
            sys.exit(1)
        if args[1] == 'all':
            return build_unmirror_all_config(physical_map, logical_monitors)
        return build_unmirror_config(args[1], physical_map, logical_monitors)

    if len(args) >= 2:
        return build_mirror_config(args[0], args[1:], physical_map, logical_monitors)

    print_help()
    sys.exit(1)


def main():
    interface = get_dbus_interface()
    serial, physical_monitors, logical_monitors, properties = interface.GetCurrentState()
    physical_map = build_physical_map(physical_monitors)
    layout_mode = int(properties.get('layout-mode', 1))

    args = sys.argv[1:]
    if not args:
        print_status(physical_map, logical_monitors)
        print_help()
        return

    new_config = _dispatch(args, physical_map, logical_monitors)
    if new_config is None:
        return

    try:
        interface.ApplyMonitorsConfig(
            dbus.UInt32(serial),
            dbus.UInt32(2),
            adjust_layout(new_config, layout_mode),
            dbus.Dictionary({}, signature='sv')
        )
        print("Success: Display configuration applied successfully!")
    except Exception as e:
        print(f"Error: Failed to apply configuration: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
