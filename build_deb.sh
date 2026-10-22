#!/usr/bin/env bash
set -e

VERSION="1.0.0"
PACKAGE_NAME="omniwall"
BUILD_DIR="/tmp/${PACKAGE_NAME}_${VERSION}_all"

echo "=== Сборка .deb пакета для Debian / Ubuntu ==="

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$BUILD_DIR/usr/bin"
mkdir -p "$BUILD_DIR/usr/lib/systemd/user"
mkdir -p "$BUILD_DIR/etc/omniwall"

# Control файл
cat <<EOF > "$BUILD_DIR/DEBIAN/control"
Package: ${PACKAGE_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: all
Depends: python3
Maintainer: Chelsea <chelsea@local>
Description: OmniWall - Cross-Desktop 4K Wallpaper Rotator for Linux
 Automated multi-source 4K wallpaper rotation for KDE, GNOME, XFCE, and Wayland.
EOF

# Копирование исполняемых файлов
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "$SCRIPT_DIR/omniwall.py" "$BUILD_DIR/usr/bin/omniwall"
chmod +x "$BUILD_DIR/usr/bin/omniwall"
ln -sf omniwall "$BUILD_DIR/usr/bin/wallpapers"
ln -sf omniwall "$BUILD_DIR/usr/bin/grimwall"

# Копирование systemd юнитов
cp "$SCRIPT_DIR/systemd/omniwall.service" "$BUILD_DIR/usr/lib/systemd/user/"
cp "$SCRIPT_DIR/systemd/omniwall.timer" "$BUILD_DIR/usr/lib/systemd/user/"

# Дефолтный конфиг
cp "$SCRIPT_DIR/config.default.json" "$BUILD_DIR/etc/omniwall/config.json"

# Сборка пакета
OUTPUT_DEB="${SCRIPT_DIR}/${PACKAGE_NAME}_${VERSION}_all.deb"
dpkg-deb --build --root-owner-group "$BUILD_DIR" "$OUTPUT_DEB"
rm -rf "$BUILD_DIR"

echo "✓ Пакет успешно собран: $OUTPUT_DEB"
echo "  Установка на любой Ubuntu/Debian системе одной командой:"
echo "    sudo apt install ./${PACKAGE_NAME}_${VERSION}_all.deb"
