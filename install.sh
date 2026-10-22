#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
CONFIG_DIR="$HOME/.config/w40k-wallpaper"

echo "=== Установка Wallpapers CLI (Warhammer 40,000 Rotator) ==="

# 1. Бинарники (создаем и wallpapers, и w40k-wallpaper для удобства)
mkdir -p "$BIN_DIR"
cp "$SCRIPT_DIR/w40k_wallpaper.py" "$BIN_DIR/wallpapers"
chmod +x "$BIN_DIR/wallpapers"
ln -sf "$BIN_DIR/wallpapers" "$BIN_DIR/w40k-wallpaper"
echo "✓ Установлены команды: $BIN_DIR/wallpapers и $BIN_DIR/w40k-wallpaper"

# 2. Конфигурация
mkdir -p "$CONFIG_DIR"
if [ ! -f "$CONFIG_DIR/config.json" ]; then
    cp "$SCRIPT_DIR/config.default.json" "$CONFIG_DIR/config.json"
    echo "✓ Создан конфигурационный файл в $CONFIG_DIR/config.json"
fi

# 3. Юниты systemd
mkdir -p "$SYSTEMD_USER_DIR"
cp "$SCRIPT_DIR/systemd/w40k-wallpaper.service" "$SYSTEMD_USER_DIR/"
cp "$SCRIPT_DIR/systemd/w40k-wallpaper.timer" "$SYSTEMD_USER_DIR/"
systemctl --user daemon-reload
echo "✓ Файлы службы и таймера скопированы в $SYSTEMD_USER_DIR"

echo ""
echo "=== Установка завершена! ==="
echo "Для просмотра справки выполните:"
echo "  wallpapers --help"
echo ""
echo "Примеры использования:"
echo "  wallpapers next"
echo "  wallpapers next --tag \"dota 2\""
echo "  wallpapers next --tag \"Krieg\" --ratio 16x9"
echo "  wallpapers current"
echo "  wallpapers prev"
echo ""
echo "Для включения ежедневного таймера (каждый день в 12:00) выполните:"
echo "  systemctl --user enable --now w40k-wallpaper.timer"
