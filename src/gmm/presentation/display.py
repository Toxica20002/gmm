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
  gmm list resolution <monitor>                # List all supported resolutions of <monitor> (aliases: list resolutions/res)
  gmm <source> <target1> [target2 ... targetN] # Mirror one or more targets onto source
  gmm unmirror <monitor>                       # Make <monitor> an independent extended display
  gmm unmirror all                             # Separate all mirrored monitors
  gmm --unmirror <monitor>
  gmm --unmirror all
  gmm set-resolution <monitor> <resolution>[@rate] # Set resolution and optionally refresh rate (e.g. 1920x1080 or 1920x1080@144)
  gmm set-res <monitor> <resolution>[@rate]
  gmm resolution <monitor> <resolution>[@rate]
  gmm res <monitor> <resolution>[@rate]

Examples:
  gmm HDMI-5 DP-4
  gmm HDMI-5 DP-3 DP-4
  gmm unmirror DP-4
  gmm unmirror all
  gmm set-resolution DP-4 1280x720
  gmm set-resolution DP-4 1920x1080@144

""")
