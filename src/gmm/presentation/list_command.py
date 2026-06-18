import sys

from gmm.presentation.display import print_status


def handle_list_command(args, physical_map, logical_monitors):
    if len(args) >= 2 and args[1] == 'monitor':
        print_status(physical_map, logical_monitors)
        return

    if len(args) >= 3 and args[1] in ('resolution', 'res', 'resolutions'):
        _print_resolutions(args[2], physical_map)
        return

    print("Error: Unknown subcommand. Did you mean 'gmm list monitor' or 'gmm list resolution <monitor>'?", file=sys.stderr)
    sys.exit(1)


def _print_resolutions(monitor_target, physical_map):
    if monitor_target not in physical_map:
        print(f"Error: Monitor '{monitor_target}' not found.", file=sys.stderr)
        sys.exit(1)

    res_dict = {}
    for mode in physical_map[monitor_target]['modes']:
        mode_id, w, h, rate, *_ = mode
        res_dict.setdefault((w, h), []).append(rate)

    print(f"Supported resolutions for monitor '{monitor_target}':")
    for w, h in sorted(res_dict, key=lambda r: r[0] * r[1], reverse=True):
        rates_str = ", ".join(f"{r:.1f}Hz" for r in sorted(set(res_dict[(w, h)]), reverse=True))
        print(f"  - {w:<4} x {h:<4} @ {rates_str}")
