# OmniWall ⚔️

> **Универсальная 4K-утилита и `systemd` сервис для ежедневной и ручной ротации обоев на любом Linux-дистрибутиве (KDE Plasma, GNOME, XFCE, Cinnamon, MATE, Wayland/swww, X11/feh)**

Спроектирована для автоматической ротации потрясающих 4K-артов по **Warhammer 40,000**, но поддерживает любые кастомные теги (Dota 2, Cyberpunk, Anime, Nature), соотношения сторон, агрегацию из нескольких источников и настраиваемый **оффлайн-буфер**.

---

## 📦 Установка в одну команду

### Вариант 1: Универсальный скрипт (любой Linux-дистрибутив)
Не требует сборки или прав суперпользователя. Просто выполните:
```bash
curl -fsSL https://raw.githubusercontent.com/chelsea/omniwall/main/install.sh | bash
```

### Вариант 2: Готовый `.deb` пакет (Ubuntu, Debian, Linux Mint, Pop!_OS)
Скачайте `.deb` файл из вкладки Releases и установите стандартным менеджером пакетов:
```bash
sudo apt install ./omniwall_1.0.0_all.deb
```

### Вариант 3: Arch Linux (AUR / PKGBUILD)
```bash
yay -S omniwall
# или вручную:
makepkg -si
```

### Вариант 4: Через pipx / pip (Python)
```bash
pipx install git+https://github.com/chelsea/omniwall.git
```

---

## ✨ Возможности

- **Работает на любом Linux-дистрибутиве и окружении**:
  - **KDE Plasma** (нативный `plasma-apply-wallpaperimage`)
  - **GNOME / Ubuntu / Fedora / Pop!_OS** (`gsettings` с поддержкой light & dark режимов)
  - **Cinnamon & MATE** (Linux Mint)
  - **XFCE** (`xfconf-query`)
  - **Wayland тайлинг** (Hyprland, Sway через `swww`)
  - **X11 оконные менеджеры** (i3, bspwm, Openbox через `feh` или `nitrogen`)
- **Настройка расписания через одну команду**:
  - `omniwall schedule 15:30` — задать конкретное время суток
  - `omniwall schedule 6h` — задать интервал (каждые 6 часов)
- **Двуязычный поиск (RU / EN)**: Можно писать теги на русском (`--tag "вархаммер"`, `--tag "дота 2"`, `--tag "криг"`). Встроен словарь игровых терминов + авто-переводчик.
- **Мульти-источниковая агрегация**:
  - **Wallhaven REST API**: официальная база с точной фильтрацией по 4K и фракциям.
  - **Web 4K Engine (Bing HD)**: поиск оригиналов сверхвысокого разрешения по всей Сети (ArtStation, AlphaCoders, Reddit и др.).
- **Оффлайн-буфер (Запас на случай отключения сети)**:
  - Автоматически держит в локальной папке запас из `N` свежих обоев (по умолчанию: 5, настраивается через `--buffer 10`).
  - Если интернета не будет несколько дней, служба продолжит менять обои из буфера.
- **0 МБ RAM в фоне**: Не является демоном. Просыпается на 1.5 секунды через `systemd.timer` (`oneshot`), меняет обои и полностью выгружается из памяти.

---

## 🚀 Примеры использования

### Базовые команды:
```bash
# Вывести полную справку со всеми аргументами
omniwall --help

# Установить следующие случайные обои по умолчанию (Warhammer 40k в 4K)
omniwall next

# Вернуться к предыдущим обоям
omniwall prev

# Информация о текущих обоях и графическом окружении
omniwall current

# Список сохранённых артов в локальной библиотеке
omniwall list
```

### Настройка времени и расписания:
```bash
# Менять обои каждый день ровно в 15:30
omniwall schedule 15:30

# Менять обои каждый день в 09:00 утра
omniwall schedule 09:00

# Менять обои каждые 6 часов
omniwall schedule 6h

# Посмотреть текущее расписание
omniwall schedule
```

### Поиск по тегам (на русском и английском) и фильтры:
```bash
# Поиск по русскоязычным тегам
omniwall next --tag "дота 2"
omniwall next --tag "криг"
omniwall next --tag "космодесант"
omniwall next --tag "киберпанк"

# Поиск по англоязычным тегам
omniwall next --tag "Black Templars"
omniwall next --tag "nature"

# Фильтр соотношения сторон (16:9, 21:9, 32:9)
omniwall next --tag "вархаммер" --ratio 16x9
omniwall next --ratio 21x9

# Минимальное разрешение
omniwall next --res 3840x2160    # 4K UHD
omniwall next --res 2560x1440    # 2K QHD
```

### Управление оффлайн-буфером:
```bash
# Проверить статус буфера
omniwall buffer

# Пополнить буфер до 10 обоев на случай отключения интернета
omniwall buffer -b 10 --sync

# Заполнить буфер артами по конкретному тегу
omniwall buffer -b 7 --sync --tag "вархаммер"

# Использовать только локальный буфер/кэш без выхода в сеть
omniwall next --local
```

---

## 🛠️ Включение ежедневного автообновления

После установки включите встроенный таймер:
```bash
systemctl --user enable --now omniwall.timer
```

Проверить статус работы:
```bash
systemctl --user list-timers --all | grep omniwall
```

---

## 📜 Лицензия
MIT
