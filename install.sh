#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
CONFIG_DIR="$HOME/.config/w40k-wallpaper"

echo "=== Установка Grimwall / Wallpapers CLI ==="

# 1. Бинарники (создаем grimwall, wallpapers и w40k-wallpaper)
mkdir -p "$BIN_DIR"
cp "$SCRIPT_DIR/w40k_wallpaper.py" "$BIN_DIR/grimwall"
chmod +x "$BIN_DIR/grimwall"
ln -sf "$BIN_DIR/grimwall" "$BIN_DIR/wallpapers"
ln -sf "$BIN_DIR/grimwall" "$BIN_DIR/w40k-wallpaper"
echo "✓ Установлены команды: grimwall, wallpapers, w40k-wallpaper"

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
echo "Окружение: автоматически поддерживаются KDE, GNOME, XFCE, Cinnamon, MATE, i3, Wayland"
echo ""
echo "Полезные команды:"
echo "  grimwall --help"
echo "  grimwall next"
echo "  grimwall next --tag \"вархаммер\""
echo "  grimwall next --tag \"дота 2\" --ratio 16x9"
echo "  grimwall schedule 15:30          # изменить время смены обоев"
echo "  grimwall buffer                  # статус оффлайн-буфера"
echo ""
echo "Для включения автозапуска по расписанию выполните:"
echo "  systemctl --user enable --now w40k-wallpaper.timer"
