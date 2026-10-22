# OmniWall

**[English](README.md)** | [Русский](README_RU.md)

Universal 4K wallpaper rotator utility and `systemd` service for Linux desktops (KDE Plasma, GNOME, XFCE, Cinnamon, MATE, Wayland/swww, X11/feh).

OmniWall is a lightweight, cross-desktop tool designed to fetch, cache, and rotate ultra-high-definition wallpapers (4K UHD, UltraWide 21:9, 32:9). It features multi-source aggregation, bilingual search tag translation (English / Russian), an offline buffer reserve, strict user-defined total disk storage limits with LRU cache cleanup, and scheduled background rotation with zero RAM usage.

---

## Installation

### Method 1: Single-Command Shell Installer (Recommended)
Installs binaries and systemd units to user space without requiring root privileges:
```bash
curl -fsSL https://raw.githubusercontent.com/andrewbohachov/omniwall/main/install.sh | bash
```

### Method 2: Debian / Ubuntu Package (.deb)
Download the pre-compiled `.deb` package from [Releases](https://github.com/andrewbohachov/omniwall/releases) and install via APT:
```bash
sudo apt install ./omniwall_1.0.0_all.deb
```

### Method 3: Arch Linux (PKGBUILD / AUR)
```bash
yay -S omniwall
# or manually:
makepkg -si
```

### Method 4: Python pipx / pip
```bash
pipx install git+https://github.com/andrewbohachov/omniwall.git
```

---

## Features

- Cross-Desktop Compatibility:
  - KDE Plasma 5 & 6 (native `plasma-apply-wallpaperimage`)
  - GNOME (Ubuntu, Fedora, Pop!_OS via `gsettings` with dark and light mode sync)
  - Cinnamon and MATE (Linux Mint)
  - XFCE (`xfconf-query`)
  - Wayland tiling compositors (Hyprland, Sway via `swww`)
  - X11 window managers (i3, bspwm, Openbox via `feh` or `nitrogen`)
- Bilingual Search (EN / RU):
  - Search using English or Russian keywords ("mountains", "space", "nature", "architecture", "minimalism", etc.).
  - Built-in translation pipeline for querying international wallpaper repositories.
- Persistent Tag Pinning:
  - When a search tag is specified, it is automatically pinned. All subsequent manual switches and scheduled timer events will continue rotating wallpapers under that tag until updated.
- Zero Background RAM Footprint:
  - Not an active daemon. Executes for 1-2 seconds via a `systemd.timer` oneshot unit, updates the wallpaper, and immediately exits memory.
- Multi-Source Aggregation:
  - Wallhaven REST API: Official database with strict 4K and aspect ratio filters.
  - Web 4K Engine: Direct high-resolution image discovery without watermarks.
- Strict Total Storage Management:
  - Users can set a hard limit on the total disk size consumed by all images combined (cache, history, and offline buffer).
  - Automatically evicts oldest unused wallpapers using an LRU (Least Recently Used) cache strategy.
  - Active desktop wallpaper is always protected from deletion.
- Offline Buffer Reserve:
  - Automatically maintains a local reserve of fresh wallpapers so rotations continue smoothly during network outages.
- Flexible Scheduling:
  - Configure intervals (e.g. `6h`, `12h`) or specific times of day (e.g. `15:30`) with a single command.
- Multi-Language CLI:
  - Full support for English (`en`) and Russian (`ru`) user interfaces.

---

## Usage

### Basic Commands
```bash
# Display full command-line help
omniwall --help

# Set next 4K wallpaper
omniwall next

# Roll back to previous wallpaper from history
omniwall prev

# Display current wallpaper details and desktop environment
omniwall current

# List saved local wallpapers in cache
omniwall list
```

---

### Tag Search and Pinning
> Note: Specifying a tag with `--tag` or the `tag` command automatically pins it as the active category for future rotations.

```bash
# Pin a tag and apply a new wallpaper immediately
omniwall next --tag "mountains"
omniwall next --tag "space"
omniwall next --tag "nature"

# Pin a tag for future rotations without changing current wallpaper
omniwall tag "architecture"

# View currently pinned tag
omniwall tag

# Reset pinned tag back to default rotation
omniwall tag --reset
# (or omniwall next --reset-tag)

# Filter by aspect ratio (16:9, 16:10, 21:9, 32:9)
omniwall next --tag "nature" --ratio 16x9
omniwall next --ratio 21x9

# Filter by minimum resolution
omniwall next --res 3840x2160    # 4K UHD
omniwall next --res 2560x1440    # 2K QHD
```

---

### Storage Limits and Cache Management
> Note: The storage limit applies to the combined sum of all images (active, cache, history, and offline buffer).

```bash
# Set total disk limit for all images (e.g. 50MB, 100MB, 1GB):
omniwall limit 50MB
omniwall limit 100MB
omniwall limit 1GB

# View current storage usage breakdown and configured limits:
omniwall limit
# (or omniwall cache)

# Force-clean old cached images immediately (preserves active wallpaper and buffer):
omniwall cache --clean

# Limit maximum number of cached image files:
omniwall cache --max-files 10
```

---

### Language Settings
Switch the CLI language between English and Russian at any time:
```bash
# Switch interface to English
omniwall lang en

# Switch interface to Russian
omniwall lang ru

# View currently configured language
omniwall lang
```

---

### Offline Buffer Management
```bash
# Check current buffer status
omniwall buffer

# Expand and sync offline buffer up to 10 wallpapers
omniwall buffer -b 10 --sync

# Sync buffer using a specific tag
omniwall buffer -b 8 --sync --tag "space"

# Switch wallpaper strictly from local cache without accessing internet
omniwall next --local
```

---

### Rotation Scheduling
```bash
# Set daily rotation at 15:30
omniwall schedule 15:30

# Set daily rotation every morning at 09:00
omniwall schedule 09:00

# Rotate wallpapers every 6 hours
omniwall schedule 6h

# Rotate wallpapers every 12 hours
omniwall schedule 12h

# View currently configured schedule
omniwall schedule
```

---

## Background Automation (systemd)

To enable automatic background rotations according to your configured schedule, activate the user systemd timer:
```bash
systemctl --user enable --now omniwall.timer
```

Verify timer status:
```bash
systemctl --user status omniwall.timer
```

Check the next scheduled trigger time:
```bash
systemctl --user list-timers --all | grep omniwall
```

---

## License
Released under the [MIT License](LICENSE).
