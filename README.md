# Grimwall ⚔️

> **Кросс-десктопная CLI-утилита и `systemd` сервис для ежедневной и ручной ротации 4K-обоев на любом Linux-дистрибутиве (KDE Plasma, GNOME, XFCE, Cinnamon, MATE, Wayland/swww, X11/feh)**

Изначально спроектирована для автоматической ротации 4K-артов по **Warhammer 40,000**, но полностью открыта для любых кастомных тегов (Dota 2, Cyberpunk, Anime, Nature), соотношений сторон и поисковых систем.

---

## ✨ Возможности

- **Работает на любом Linux-дистрибутиве и окружении**:
  - **KDE Plasma** (нативный `plasma-apply-wallpaperimage`)
  - **GNOME / Ubuntu / Fedora / Pop!_OS** (`gsettings` с поддержкой light & dark режимов)
  - **Cinnamon & MATE** (Linux Mint)
  - **XFCE** (`xfconf-query`)
  - **Wayland тайлинг** (Hyprland, Sway через `swww`)
  - **X11 оконные менеджеры** (i3, bspwm, Openbox через `feh` или `nitrogen`)
- **Настройка времени смены обоев через CLI**:
  - `grimwall schedule 15:30` — задать конкретное время суток
  - `grimwall schedule 6h` — задать интервал (каждые 6 часов)
- **Двуязычный поиск (RU / EN)**: Можно писать теги на русском (`--tag "вархаммер"`, `--tag "дота 2"`, `--tag "криг"`). Встроен умный словарь игровых вселенных + автоматический переводчик.
- **Мульти-источниковая агрегация**:
  - **Wallhaven REST API**: официальная база артов с точной фильтрацией по 4K и фракциям.
  - **Web 4K Engine (Bing HD)**: поиск несжатых оригиналов по всей Сети (ArtStation, AlphaCoders, Reddit и др.).
- **Оффлайн-буфер (Запас на случай отключения сети)**:
  - Автоматически держит в локальной папке запас из `N` свежих обоев (по умолчанию: 5, настраивается через `--buffer 10`).
  - Если интернета не будет несколько дней, служба продолжит исправно менять обои из буфера.
- **0 МБ RAM в фоне**: Не является демоном. Просыпается на 1.5 секунды через `systemd.timer` (`oneshot`), меняет обои и полностью выгружается из памяти.

---

## 🚀 Примеры использования

### Базовые команды:
```bash
# Вывести полную справку со всеми аргументами
grimwall --help

# Установить следующие случайные обои по умолчанию (Warhammer 40k в 4K)
grimwall next

# Вернуться к предыдущим обоям
grimwall prev

# Информация о текущих обоях и графическом окружении
grimwall current

# Список сохранённых артов в локальной библиотеке
grimwall list
```

### Настройка времени и расписания:
```bash
# Менять обои каждый день ровно в 15:30
grimwall schedule 15:30

# Менять обои каждый день в 09:00 утра
grimwall schedule 09:00

# Менять обои каждые 6 часов
grimwall schedule 6h

# Посмотреть текущее расписание
grimwall schedule
```

### Поиск по тегам (на русском и английском) и фильтры:
```bash
# Поиск по русскоязычным тегам
grimwall next --tag "дота 2"
grimwall next --tag "криг"
grimwall next --tag "космодесант"
grimwall next --tag "киберпанк"

# Поиск по англоязычным тегам
grimwall next --tag "Black Templars"
grimwall next --tag "nature"

# Фильтр соотношения сторон (16:9, 21:9, 32:9)
grimwall next --tag "вархаммер" --ratio 16x9
grimwall next --ratio 21x9

# Минимальное разрешение
grimwall next --res 3840x2160    # 4K UHD
grimwall next --res 2560x1440    # 2K QHD
```

### Управление оффлайн-буфером:
```bash
# Проверить статус буфера
grimwall buffer

# Пополнить буфер до 10 обоев на случай отключения интернета
grimwall buffer -b 10 --sync

# Заполнить буфер артами по конкретному тегу
grimwall buffer -b 7 --sync --tag "вархаммер"

# Использовать только локальный буфер/кэш без выхода в сеть
grimwall next --local
```

---

## 🛠️ Установка

```bash
git clone https://github.com/yourusername/grimwall.git
cd grimwall
./install.sh
```

Установщик создаёт три эквивалентные команды в `~/.local/bin/`:
- `grimwall`
- `wallpapers`
- `w40k-wallpaper`

### Включение таймера автообновления:
```bash
systemctl --user enable --now w40k-wallpaper.timer
```

---

## 📜 Лицензия
MIT
