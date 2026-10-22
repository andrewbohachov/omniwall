# Wallpapers CLI (w40k-wallpaper) ⚔️

> **Умная CLI-утилита и `systemd` сервис для ежедневной и ручной ротации 4K-обоев на Linux (KDE Plasma & Freedesktop)**

Изначально спроектирована для автоматической ротации 4K-артов по **Warhammer 40,000**, но поддерживает поиск по любым кастомным тегам (например: `Dota 2`, `Cyberpunk`, `Anime`, `Nature`), соотношениям сторон и разрешениям через официальный API Wallhaven.

---

## ✨ Возможности

- **Качество 4K UHD**: Автоматический фильтр по разрешению `3840×2160` (16:9), `2K`, `Ultrawide 21:9` и выше.
- **Поддержка кастомных тегов**: Возможность искать как по Вахе, так и по любым другим вселенным (`--tag "dota 2"`, `--tag "Krieg"`).
- **Фильтр соотношения сторон**: Поддержка флага `--ratio` (`16x9`, `16x10`, `21x9`, `32x9`).
- **Справка `help`**: Детальная встроенная справка со всеми аргументами и примерами.
- **Автоматизация по расписанию**: `systemd --user` таймер раз в 24 часа (в 12:00) без прав root.
- **Оффлайн-кэш**: Автоматический переход на локальные файлы при отсутствии сети.
- **История и откат**: Команда `wallpapers prev` возвращает предыдущий арт.
- **Всплывающие уведомления**: Нативное уведомление на рабочий стол с названием арта.

---

## 🚀 Примеры использования

### Базовые команды:
```bash
# Справка по всем командам и опциям
wallpapers --help

# Установить следующие случайные обои по умолчанию (Warhammer 40k в 4K)
wallpapers next

# Вернуться к предыдущим обоям
wallpapers prev

# Информация о текущих обоях
wallpapers current

# Список локально сохранённых артов в кэше
wallpapers list
```

### Поиск по тегам, разрешениям и соотношениям:
```bash
# Скачать и установить 4K-обои по тегу "dota 2"
wallpapers next --tag "dota 2"

# Скачать обои с Корпусом Смерти Крига строго в формате 16:9
wallpapers next --tag "Krieg" --ratio 16x9

# Обои по Черным Храмовникам в разрешении 2K
wallpapers next --tag "Black Templars" --res 2560x1440

# Использовать только локальную коллекцию без выхода в интернет
wallpapers next --local

# Тихий режим (без всплывающего системного уведомления)
wallpapers next --silent
```

---

## 🛠️ Установка

```bash
git clone https://github.com/yourusername/w40k-wallpaper.git
cd w40k-wallpaper
./install.sh
```

Установщик создаёт две команды в `~/.local/bin/`:
- `wallpapers`
- `w40k-wallpaper`

### Включение ежедневного таймера (каждый день в 12:00):
```bash
systemctl --user enable --now w40k-wallpaper.timer
```

### Проверка статуса таймера:
```bash
systemctl --user list-timers --all | grep w40k
```

---

## ⚙️ Конфигурация по умолчанию

Файл настроек создается в `~/.config/w40k-wallpaper/config.json`:

```json
{
    "min_resolution": "3840x2160",
    "ratios": "16x9",
    "purity": "100",
    "default_queries": [
        "id:2143",
        "Astra Militarum",
        "Death Korps of Krieg",
        "Iron Hands",
        "Salamanders 40k",
        "Black Templars",
        "Dreadnought warhammer"
    ],
    "desktop_notifications": true,
    "apply_command": "plasma-apply-wallpaperimage"
}
```

---

## 📜 Лицензия
MIT
