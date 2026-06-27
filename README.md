# GNOME Monitor Mirror (gmm)

`gmm` is a command-line tool for GNOME Wayland and X11 sessions. It mirrors, unmirrors, and configures displays by talking directly to the GNOME Mutter D-Bus interface — no GUI required.

---

## Requirements

- Linux with a running GNOME session (Wayland or X11)
- Python 3.7+
- `dbus-python` system library

### Install system dependencies

**Ubuntu / Debian:**
```bash
sudo apt update && sudo apt install python3-dbus libdbus-1-dev pkg-config
```

**Fedora / RHEL:**
```bash
sudo dnf install python3-dbus dbus-glib-devel
```

**Arch Linux:**
```bash
sudo pacman -S python-dbus
```

---

## Installation

### Method 1: `pipx` (Recommended)

```bash
pipx install git+https://github.com/Toxica20002/gmm.git
```

### Method 2: `pip`

```bash
pip install git+https://github.com/Toxica20002/gmm.git
```

> On modern distros you may hit PEP 668 errors. Use `pipx` or a virtualenv.

### Method 3: Local development

```bash
git clone https://github.com/Toxica20002/gmm.git
cd gmm
pip install -e .
```

---

## Usage

Running `gmm` with no arguments shows the current monitor status and help text.

### List monitors and layout

```bash
gmm list monitor
```

Shows connected physical monitors (vendor, product, active resolution) and the current logical layout groups (position, scale, mirrored groups).

### List supported resolutions

```bash
gmm list resolution <monitor>
# Aliases: list resolutions, list res
```

Lists every resolution and refresh rate the monitor supports, sorted by pixel count.

```
Supported resolutions for monitor 'DP-4':
  - 2560 x 1440 @ 144.0Hz, 60.0Hz
  - 1920 x 1080 @ 144.0Hz, 60.0Hz
  ...
```

### Mirror displays

Mirror one or more targets onto a source display. `gmm` automatically finds the best common resolution.

```bash
gmm <source> <target1> [target2 ...]
```

**Examples:**
```bash
gmm HDMI-5 DP-4              # Mirror DP-4 onto HDMI-5
gmm HDMI-5 DP-3 DP-4         # Mirror DP-3 and DP-4 onto HDMI-5
```

### Unmirror displays

Separates a mirrored monitor into an independent extended display (placed to the right of the existing layout).

```bash
gmm unmirror <monitor>        # Unmirror a specific display
gmm unmirror all              # Separate all mirrored displays
```

`--unmirror` and `-u` are accepted as aliases for `unmirror`.

### Set resolution

Sets the resolution (and optionally the refresh rate) of a display.

```bash
gmm set-resolution <monitor> <WxH>[@rate]
# Aliases: set-res, resolution, res
```

**Examples:**
```bash
gmm set-resolution DP-4 1920x1080        # Set resolution, keep current refresh rate
gmm set-resolution DP-4 1920x1080@144    # Set resolution and target 144 Hz
gmm res DP-4 2560x1440@60Hz              # Short alias, Hz suffix optional
```

---

## Architecture

The codebase follows a three-layer structure:

```
src/gmm/
├── cli.py                      # Entry point — arg parsing and dispatch
├── presentation/
│   ├── display.py              # Status and help output
│   └── list_command.py         # `list monitor` / `list resolution` handlers
├── application/
│   ├── mirror.py               # Build mirror D-Bus config
│   ├── unmirror.py             # Build unmirror D-Bus config
│   └── set_resolution.py       # Build set-resolution D-Bus config
├── domain/
│   ├── monitor.py              # Physical monitor model, mode selection
│   └── layout.py               # Layout normalization and connector logic
└── infrastructure/
    ├── dbus_client.py          # Mutter D-Bus connection
    └── dbus_builders.py        # D-Bus type construction helpers
```

---

## License

MIT — see [LICENSE](LICENSE).
