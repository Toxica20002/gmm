# GNOME Monitor Mirror (gmm)

`gmm` is a command-line interface (CLI) tool designed for GNOME Wayland and X11 sessions. It allows you to easily mirror or unmirror displays directly from the terminal by interacting with the GNOME Mutter D-Bus interface.

---

## Requirements

- **Operating System:** Linux with a running GNOME Display Manager (GDM) session (Wayland or X11).
- **Python:** Python 3.7 or newer.
- **System Dependencies:**
  Since the tool relies on `dbus-python` to interact with Mutter, you must have the system D-Bus libraries.

  ### On Ubuntu / Debian:
  ```bash
  sudo apt update
  sudo apt install python3-dbus libdbus-1-dev pkg-config
  ```

  ### On Fedora / RHEL:
  ```bash
  sudo dnf install python3-dbus dbus-glib-devel
  ```

  ### On Arch Linux:
  ```bash
  sudo pacman -S python-dbus
  ```

---

## Installation

### Method 1: Using `pipx` (Recommended)
`pipx` installs python command-line applications in isolated environments while making them globally accessible.

```bash
pipx install git+https://github.com/YOUR_GITHUB_USERNAME/gnome-monitor-mirror.git
```

### Method 2: Using `pip`
You can install the package directly from GitHub:

```bash
pip install git+https://github.com/YOUR_GITHUB_USERNAME/gnome-monitor-mirror.git
```
*(Note: If you run into PEP 668 "externally-managed-environment" errors on modern distros, either use `pipx` above, or run inside a virtual environment).*

### Method 3: Local Development
Clone the repository and install it in editable mode:

```bash
git clone https://github.com/YOUR_GITHUB_USERNAME/gnome-monitor-mirror.git
cd gnome-monitor-mirror
pip install -e .
```

---

## Usage

Once installed, the `gmm` command will be available in your system path.

### 1. List Monitors and Current Layout
Get a list of all connected physical displays and the current logical configuration groups:
```bash
gmm list monitor
```
*Or run `gmm` with no arguments.*

### 2. Mirror Displays
Mirror one or more target displays onto a source display. The tool automatically attempts to find a compatible resolution.

**Syntax:**
```bash
gmm <source_monitor> <target_monitor1> [target_monitor2 ... target_monitorN]
```

**Examples:**
- Mirror `DP-4` onto `HDMI-5`:
  ```bash
  gmm HDMI-5 DP-4
  ```
- Mirror `DP-3` and `DP-4` onto `HDMI-5`:
  ```bash
  gmm HDMI-5 DP-3 DP-4
  ```

### 3. Unmirror Displays
Separate a mirrored monitor into an independent extended display. The tool places the separated monitor to the right of your existing layout.

- Unmirror a specific display:
  ```bash
  gmm unmirror DP-4
  ```
- Unmirror all mirrored displays (separate everything):
  ```bash
  gmm unmirror all
  ```

---

## License

This project is licensed under the [MIT License](LICENSE).
