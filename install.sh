#!/usr/bin/env bash
set -e

# ==============================================================================
# OmniWall One-Line Installer
# Supports local execution and remote curl execution:
#   curl -sSL https://raw.githubusercontent.com/<user>/omniwall/main/install.sh | bash
# ==============================================================================

REPO_RAW_URL="${OMNIWALL_RAW_URL:-https://raw.githubusercontent.com/chelsea/omniwall/main}"
BIN_DIR="$HOME/.local/bin"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
CONFIG_DIR="$HOME/.config/omniwall"

echo "=========================================================="
echo "          ⚔️  УСТАНОВКА OMNIWALL ROTATOR  ⚔️             "
echo "=========================================================="

mkdir -p "$BIN_DIR"
mkdir -p "$SYSTEMD_USER_DIR"
mkdir -p "$CONFIG_DIR"

# Проверяем, запускается ли скрипт из склонированной папки или через curl
if [ -f "$(dirname "${BASH_SOURCE[0]}")/omniwall.py" ]; then
    SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    echo "[1/4] Копирование исполняемых файлов..."
    cp "$SRC_DIR/omniwall.py" "$BIN_DIR/omniwall"
    cp "$SRC_DIR/systemd/omniwall.service" "$SYSTEMD_USER_DIR/"
    cp "$SRC_DIR/systemd/omniwall.timer" "$SYSTEMD_USER_DIR/"
    if [ ! -f "$CONFIG_DIR/config.json" ]; then
        cp "$SRC_DIR/config.default.json" "$CONFIG_DIR/config.json"
    fi
else
    echo "[1/4] Скачивание компонентов OmniWall из репозитория..."
    curl -fsSL "$REPO_RAW_URL/omniwall.py" -o "$BIN_DIR/omniwall"
    curl -fsSL "$REPO_RAW_URL/systemd/omniwall.service" -o "$SYSTEMD_USER_DIR/omniwall.service"
    curl -fsSL "$REPO_RAW_URL/systemd/omniwall.timer" -o "$SYSTEMD_USER_DIR/omniwall.timer"
    if [ ! -f "$CONFIG_DIR/config.json" ]; then
        curl -fsSL "$REPO_RAW_URL/config.default.json" -o "$CONFIG_DIR/config.json"
    fi
fi

# Делаем бинарник исполняемым и создаем удобные алиасы
chmod +x "$BIN_DIR/omniwall"
ln -sf "$BIN_DIR/omniwall" "$BIN_DIR/wallpapers"
ln -sf "$BIN_DIR/omniwall" "$BIN_DIR/w40k-wallpaper"
ln -sf "$BIN_DIR/omniwall" "$BIN_DIR/grimwall"
echo "[2/4] Зарегистрированы команды: omniwall, wallpapers, grimwall"

# Проверяем PATH
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo "⚠️  Внимание: $HOME/.local/bin отсутствует в вашем PATH."
    echo "    Добавьте следующую строку в ~/.bashrc или ~/.zshrc:"
    echo '    export PATH="$HOME/.local/bin:$PATH"'
fi

# Перезагружаем конфигурацию systemd --user
echo "[3/4] Регистрация системных таймеров systemd --user..."
if command -v systemctl &>/dev/null; then
    systemctl --user daemon-reload || true
fi

echo "[4/4] Готово!"
echo ""
echo "=========================================================="
echo "          🎉 OmniWall успешно установлен!                "
echo "=========================================================="
echo ""
echo "Примеры быстрых команд:"
echo "  omniwall --help                 # Полная справка по аргументам"
echo "  omniwall next                   # Поставить свежие 4K-обои (Ваха)"
echo "  omniwall next --tag \"дота 2\"    # Поставить обои по любому тегу"
echo "  omniwall schedule 15:30         # Настроить время ежедневной смены"
echo "  omniwall buffer                 # Проверить статус оффлайн-буфера"
echo ""
echo "Включение автоматической ежедневной смены обоев:"
echo "  systemctl --user enable --now omniwall.timer"
echo "=========================================================="
