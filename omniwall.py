#!/usr/bin/env python3
"""
OmniWall:
Cross-Desktop 4K Wallpaper Rotator for Linux (KDE Plasma, GNOME, XFCE, Cinnamon, MATE, Wayland/swww, X11/feh).

Features:
- Multi-DE auto-detection: KDE Plasma, GNOME (light/dark), XFCE, Cinnamon, MATE, Wayland (swww), i3/X11 (feh, nitrogen)
- Custom schedule CLI: easily set wallpaper rotation time (e.g. 'omniwall schedule 15:30' or 'every 6h')
- Multi-source image fetching (Wallhaven API + Bing HD Engine)
- Bilingual tag support (Russian & English with smart auto-translation)
- Configurable offline buffer (e.g., 5-10 pre-downloaded wallpapers)
- Zero background memory footprint (pure systemd --user oneshot architecture)
"""

import sys
import os
import json
import random
import re
import shutil
import argparse
import urllib.request
import urllib.parse
import subprocess
from pathlib import Path
from datetime import datetime

CONFIG_DIR = Path.home() / ".config" / "omniwall"
CACHE_DIR = Path.home() / ".local" / "share" / "omniwall" / "wallpapers"
BUFFER_DIR = Path.home() / ".local" / "share" / "omniwall" / "buffer"
STATE_FILE = CONFIG_DIR / "state.json"
CONFIG_FILE = CONFIG_DIR / "config.json"
SYSTEMD_USER_DIR = Path.home() / ".config" / "systemd" / "user"
TIMER_FILE = SYSTEMD_USER_DIR / "omniwall.timer"

DEFAULT_CONFIG = {
    "min_resolution": "3840x2160",
    "ratios": "16x9",
    "purity": "100",  # SFW
    "buffer_size": 5,  # количество оффлайн-обоев в буфере
    "schedule": "12:00",  # ежедневное время смены
    "sources": ["wallhaven", "bing"],
    "default_queries": [
        "id:2143",  # Warhammer 40,000 tag
        "Astra Militarum",
        "Death Korps of Krieg",
        "Iron Hands Space Marines",
        "Salamanders 40k",
        "Black Templars",
        "Dreadnought warhammer"
    ],
    "desktop_notifications": True
}

LOCAL_DICTIONARY = {
    "вархаммер": "Warhammer 40000",
    "ваха": "Warhammer 40000",
    "вархаммер 40к": "Warhammer 40000",
    "вархаммер 40000": "Warhammer 40000",
    "космодесант": "Space Marines Warhammer",
    "астартес": "Adeptus Astartes",
    "астра милитарум": "Astra Militarum",
    "имперская гвардия": "Imperial Guard Warhammer",
    "криг": "Death Korps of Krieg",
    "корпус смерти крига": "Death Korps of Krieg",
    "черные храмовники": "Black Templars",
    "железные руки": "Iron Hands Space Marines",
    "саламандры": "Salamanders Warhammer 40k",
    "темные ангелы": "Dark Angels Warhammer",
    "кровавые ангелы": "Blood Angels",
    "космические волки": "Space Wolves",
    "ультрамарины": "Ultramarines",
    "дредноут": "Dreadnought Warhammer",
    "титан": "Warlord Titan Warhammer",
    "город-улей": "Hive City Warhammer",
    "дота": "Dota 2",
    "дота 2": "Dota 2",
    "ведьмак": "The Witcher 3",
    "киберпанк": "Cyberpunk 2077",
    "природа": "nature landscape",
    "космос": "deep space galaxy",
    "машины": "supercars",
    "аниме": "anime scenery aesthetic"
}

def load_config():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    BUFFER_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4, ensure_ascii=False)
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            for k, v in DEFAULT_CONFIG.items():
                if k not in cfg:
                    cfg[k] = v
            return cfg
    except Exception:
        return DEFAULT_CONFIG

def save_config(config):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def load_state():
    if not STATE_FILE.exists():
        return {"current": None, "history": []}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"current": None, "history": []}

def save_state(state):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4, ensure_ascii=False)

def translate_tag(tag):
    clean_tag = tag.strip().lower()
    if clean_tag in LOCAL_DICTIONARY:
        return LOCAL_DICTIONARY[clean_tag]
    
    if re.search(r"[\u0400-\u04FF]", tag):
        try:
            url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(tag)}&langpair=ru|en"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                translated = data.get("responseData", {}).get("translatedText")
                if translated and not translated.startswith("MYMEMORY"):
                    return translated
        except Exception:
            pass
    return tag

def notify(title, message):
    try:
        subprocess.run(
            ["notify-send", "-a", "OmniWall", "-i", "preferences-desktop-wallpaper", title, message],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception:
        pass

# ----------------- КРОСС-ОКРУЖЕНИЕ (DE DETECTION) -----------------

def detect_and_apply_wallpaper(image_path):
    abs_path = Path(image_path).resolve()
    file_uri = f"file://{abs_path}"
    de = (os.environ.get("XDG_CURRENT_DESKTOP") or os.environ.get("DESKTOP_SESSION") or "").lower()

    # 1. KDE Plasma
    if "kde" in de or "plasma" in de or shutil.which("plasma-apply-wallpaperimage"):
        try:
            subprocess.run(["plasma-apply-wallpaperimage", str(abs_path)], capture_output=True, text=True, check=True)
            return True, "KDE Plasma"
        except Exception:
            pass

    # 2. GNOME / Ubuntu Desktop / Pop!_OS / Budgie
    if any(x in de for x in ["gnome", "ubuntu", "unity", "budgie", "pop"]) or shutil.which("gsettings"):
        try:
            subprocess.run(["gsettings", "set", "org.gnome.desktop.background", "picture-uri", file_uri], check=True, capture_output=True)
            subprocess.run(["gsettings", "set", "org.gnome.desktop.background", "picture-uri-dark", file_uri], check=True, capture_output=True)
            return True, "GNOME"
        except Exception:
            pass

    # 3. Cinnamon (Linux Mint)
    if "cinnamon" in de:
        try:
            subprocess.run(["gsettings", "set", "org.cinnamon.desktop.background", "picture-uri", file_uri], check=True, capture_output=True)
            return True, "Cinnamon"
        except Exception:
            pass

    # 4. MATE Desktop
    if "mate" in de:
        try:
            subprocess.run(["gsettings", "set", "org.mate.background", "picture-filename", str(abs_path)], check=True, capture_output=True)
            return True, "MATE"
        except Exception:
            pass

    # 5. XFCE Desktop
    if "xfce" in de and shutil.which("xfconf-query"):
        try:
            res = subprocess.run(["xfconf-query", "-c", "xfce4-desktop", "-l"], capture_output=True, text=True)
            applied = False
            for prop in res.stdout.splitlines():
                if "last-image" in prop or "image-path" in prop:
                    subprocess.run(["xfconf-query", "-c", "xfce4-desktop", "-p", prop, "-s", str(abs_path)], check=False)
                    applied = True
            if applied:
                return True, "XFCE"
        except Exception:
            pass

    # 6. Wayland тайлинговые оконные менеджеры (Hyprland, Sway via swww)
    if shutil.which("swww"):
        try:
            subprocess.run(["swww", "img", str(abs_path)], check=True, capture_output=True)
            return True, "swww (Wayland)"
        except Exception:
            pass

    # 7. X11 оконные менеджеры (i3, bspwm, Openbox, Awesome) via feh или nitrogen
    if shutil.which("feh"):
        try:
            subprocess.run(["feh", "--bg-fill", str(abs_path)], check=True, capture_output=True)
            return True, "feh (X11)"
        except Exception:
            pass
    if shutil.which("nitrogen"):
        try:
            subprocess.run(["nitrogen", "--set-zoom-fill", str(abs_path)], check=True, capture_output=True)
            return True, "nitrogen (X11)"
        except Exception:
            pass

    return False, "Неизвестное окружение"

def apply_wallpaper(image_path, title=None, config=None, silent=False):
    success, env_name = detect_and_apply_wallpaper(image_path)
    if success:
        state = load_state()
        state["history"].append(state.get("current"))
        state["history"] = [h for h in state["history"] if h][-50:]
        state["current"] = {
            "path": str(image_path),
            "title": title or Path(image_path).name,
            "applied_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "environment": env_name
        }
        save_state(state)

        if not silent and config and config.get("desktop_notifications", True):
            notify("OmniWall", f"{title or Path(image_path).stem}\n[{env_name}]")
        print(f"✓ Обои успешно применены ({env_name}): {image_path}")
        return True
    else:
        print(f"Ошибка: не удалось установить обои автоматически для вашего окружения.", file=sys.stderr)
        return False

# ----------------- ПРОВАЙДЕРЫ ОБОЕВ -----------------

def fetch_wallhaven(query, min_res, ratio, purity="100"):
    headers = {"User-Agent": "Mozilla/5.0 omniwall/1.0"}
    encoded_q = urllib.parse.quote(query)
    url = (
        f"https://wallhaven.cc/api/v1/search?"
        f"q={encoded_q}&atleast={min_res}&ratios={ratio}&purity={purity}&sorting=random"
    )
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    items = data.get("data", [])
    if not items:
        return None

    choice = random.choice(items)
    img_id = choice["id"]
    ext = choice["file_type"].split("/")[-1]
    if ext == "jpeg":
        ext = "jpg"
    target_file = CACHE_DIR / f"wallhaven_{img_id}.{ext}"

    if not target_file.exists():
        dl_req = urllib.request.Request(choice["path"], headers=headers)
        with urllib.request.urlopen(dl_req, timeout=25) as dl_resp, open(target_file, "wb") as f:
            f.write(dl_resp.read())

    return target_file, f"{query} [Wallhaven {choice['resolution']}]"

def fetch_bing_hd(query, min_res=None):
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0"}
    search_term = f"{query} 4k wallpaper 3840x2160 uhd"
    url = f"https://www.bing.com/images/search?q={urllib.parse.quote(search_term)}&form=HDRSC2&first=1"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=8) as resp:
        html = resp.read().decode("utf-8", errors="ignore")

    matches = re.findall(r'murl&quot;:&quot;(https?://[^\&]+)&quot;', html)
    valid_links = [m for m in matches if any(m.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp"])]
    if not valid_links:
        return None

    random.shuffle(valid_links)
    for img_url in valid_links[:5]:
        try:
            filename = f"web_{abs(hash(img_url))}.jpg"
            target_file = CACHE_DIR / filename
            if not target_file.exists():
                dl_req = urllib.request.Request(img_url, headers=headers)
                with urllib.request.urlopen(dl_req, timeout=15) as dl_resp, open(target_file, "wb") as f:
                    f.write(dl_resp.read())
            return target_file, f"{query} [Web 4K Engine]"
        except Exception:
            continue
    return None

def fetch_from_any_source(query, config, min_res=None, ratio=None):
    min_res = min_res or config.get("min_resolution", "3840x2160")
    ratio = ratio or config.get("ratios", "16x9")
    sources = config.get("sources", ["wallhaven", "bing"])
    random.shuffle(sources)

    for src in sources:
        try:
            if src == "wallhaven":
                res = fetch_wallhaven(query, min_res, ratio, purity=config.get("purity", "100"))
                if res:
                    return res
            elif src == "bing":
                res = fetch_bing_hd(query, min_res)
                if res:
                    return res
        except Exception:
            continue
    return None

# ----------------- БУФЕР И ОФФЛАЙН КЭШ -----------------

def get_buffer_files():
    exts = {".jpg", ".jpeg", ".png", ".webp"}
    if not BUFFER_DIR.exists():
        return []
    return [p for p in BUFFER_DIR.iterdir() if p.is_file() and p.suffix.lower() in exts]

def sync_buffer(target_count, config, custom_tag=None):
    BUFFER_DIR.mkdir(parents=True, exist_ok=True)
    current_files = get_buffer_files()
    needed = target_count - len(current_files)

    if needed <= 0:
        print(f"Буфер полон: {len(current_files)}/{target_count} обоев готовы к оффлайн-работе.")
        return

    print(f"Пополнение буфера: скачивание {needed} обоев (цель: {target_count})...")
    queries = [custom_tag] if custom_tag else config.get("default_queries", ["Warhammer 40000"])

    added = 0
    attempts = 0
    while added < needed and attempts < needed * 3:
        attempts += 1
        q = translate_tag(random.choice(queries))
        try:
            result = fetch_from_any_source(q, config)
            if result:
                src_path, title = result
                dest_file = BUFFER_DIR / f"buffer_{src_path.name}"
                if not dest_file.exists():
                    shutil.copy2(src_path, dest_file)
                    added += 1
                    print(f"  + [{added}/{needed}] Добавлено в буфер: {title}")
        except Exception:
            pass

    total = len(get_buffer_files())
    print(f"✓ Готово! Текущий оффлайн-буфер: {total} обоев.")

def get_local_wallpapers(filter_query=None):
    exts = {".jpg", ".jpeg", ".png", ".webp"}
    dirs = [
        BUFFER_DIR,
        CACHE_DIR,
        Path.home() / "Pictures" / "Wallpapers" / "Warhammer40k",
        Path.home() / "Pictures" / "Wallpapers",
        Path.home() / "Pictures"
    ]
    files = []
    for d in dirs:
        if d.exists():
            for p in d.iterdir():
                if p.is_file() and p.suffix.lower() in exts:
                    if filter_query:
                        if filter_query.lower() in p.name.lower():
                            files.append(p)
                    else:
                        files.append(p)
    return files

# ----------------- УПРАВЛЕНИЕ РАСПИСАНИЕМ (SCHEDULE) -----------------

def update_schedule(time_str, config):
    clean_time = time_str.strip().lower()
    interval_match = re.match(r"^(\d+)\s*(h|ч|hour|hours)$", clean_time)
    time_match = re.match(r"^([01]?\d|2[0-3]):([0-5]\d)$", clean_time)

    if interval_match:
        hours = interval_match.group(1)
        calendar_rule = f"*-*-* 00/{hours}:00:00"
        desc_text = f"каждые {hours} ч."
    elif time_match:
        hh = time_match.group(1).zfill(2)
        mm = time_match.group(2)
        calendar_rule = f"*-*-* {hh}:{mm}:00"
        desc_text = f"каждый день в {hh}:{mm}"
    else:
        print(f"Ошибка формата времени: '{time_str}'.", file=sys.stderr)
        print("Примеры правильного формата:", file=sys.stderr)
        print("  omniwall schedule 15:30    (каждый день в 15:30)", file=sys.stderr)
        print("  omniwall schedule 09:00    (каждый день в 09:00)", file=sys.stderr)
        print("  omniwall schedule 6h       (каждые 6 часов)", file=sys.stderr)
        return False

    config["schedule"] = clean_time
    save_config(config)

    SYSTEMD_USER_DIR.mkdir(parents=True, exist_ok=True)
    timer_content = f"""[Unit]
Description=Daily timer for OmniWall Wallpaper Rotator ({desc_text})

[Timer]
OnCalendar={calendar_rule}
Persistent=true

[Install]
WantedBy=timers.target
"""
    with open(TIMER_FILE, "w", encoding="utf-8") as f:
        f.write(timer_content)

    print(f"✓ Расписание успешно настроено: {desc_text}")
    print(f"  Файл таймера: {TIMER_FILE}")

    try:
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True, capture_output=True)
        check = subprocess.run(["systemctl", "--user", "is-active", "omniwall.timer"], capture_output=True, text=True)
        if "active" in check.stdout:
            subprocess.run(["systemctl", "--user", "restart", "omniwall.timer"], check=False)
            print("  ✓ Активный таймер systemd перезапущен с новым временем.")
        else:
            print("  (Таймер пока не включен. Для старта выполните: systemctl --user enable --now omniwall.timer)")
    except Exception:
        pass

    return True

# ----------------- КОМАНДЫ CLI -----------------

def cmd_next(args, config):
    raw_query = getattr(args, "tag", None)
    if raw_query:
        query = translate_tag(raw_query)
        print(f"Поиск обоев по тегу: '{raw_query}' (EN: '{query}')")
    else:
        query = translate_tag(random.choice(config.get("default_queries", ["Warhammer 40000"])))

    min_res = args.resolution or config.get("min_resolution", "3840x2160")
    ratio = args.ratio or config.get("ratios", "16x9")

    if not args.local:
        fresh = fetch_from_any_source(query, config, min_res=min_res, ratio=ratio)
        if fresh:
            path, title = fresh
            apply_wallpaper(path, title, config, silent=args.silent)
            target_buffer = args.buffer or config.get("buffer_size", 5)
            if len(get_buffer_files()) < target_buffer:
                sync_buffer(target_buffer, config)
            return

    local_files = get_local_wallpapers(filter_query=raw_query)
    if not local_files:
        local_files = get_local_wallpapers()
    if not local_files:
        print("Ошибка: локальные обои не найдены и сетевой запрос не вернул результатов.", file=sys.stderr)
        return

    state = load_state()
    current_path = state.get("current", {}).get("path") if state.get("current") else None
    candidates = [f for f in local_files if str(f) != current_path]
    chosen = random.choice(candidates if candidates else local_files)
    apply_wallpaper(chosen, chosen.stem.replace("_", " "), config, silent=args.silent)

def cmd_prev(args, config):
    state = load_state()
    history = state.get("history", [])
    if not history:
        print("История предыдущих обоев пуста.")
        return
    prev_entry = history.pop()
    save_state(state)
    if prev_entry and Path(prev_entry["path"]).exists():
        apply_wallpaper(prev_entry["path"], prev_entry.get("title"), config, silent=args.silent)
    else:
        print("Предыдущий файл больше не найден на диске.")

def cmd_current(args):
    state = load_state()
    curr = state.get("current")
    if not curr:
        print("Текущие обои не зафиксированы утилитой.")
        return
    print("┌────────────────────────────────────────────────────────┐")
    print("│             OMNIWALL: ТЕКУЩИЕ ОБОИ РАБОЧЕГО СТОЛА      │")
    print("└────────────────────────────────────────────────────────┘")
    print(f"  Название   : {curr.get('title')}")
    print(f"  Окружение  : {curr.get('environment', 'KDE/GNOME')}")
    print(f"  Файл       : {curr.get('path')}")
    print(f"  Установлен : {curr.get('applied_at')}")

def cmd_buffer(args, config):
    files = get_buffer_files()
    target = args.buffer or config.get("buffer_size", 5)
    print(f"=== Локальный оффлайн-буфер: {len(files)} / {target} обоев ===")
    for idx, f in enumerate(files, 1):
        print(f"  [{idx}] {f.name}")
    if args.sync or len(files) < target:
        sync_buffer(target, config, custom_tag=args.tag)

def cmd_schedule(args, config):
    if not args.time:
        curr_sched = config.get("schedule", "12:00")
        print(f"Текущее расписание: {curr_sched}")
        print("Чтобы изменить расписание, укажите время. Например:")
        print("  omniwall schedule 15:30   (каждый день в 15:30)")
        print("  omniwall schedule 08:00   (каждый день в 08:00)")
        print("  omniwall schedule 6h      (каждые 6 часов)")
        return
    update_schedule(args.time, config)

def cmd_list(args):
    files = get_local_wallpapers(filter_query=getattr(args, "tag", None))
    if not files:
        print("Локальная библиотека пуста.")
        return
    print(f"Найдено локальных обоев: {len(files)}")
    for f in sorted(files):
        print(f"  • {f.name} ({f.parent.name})")

def build_parser():
    parser = argparse.ArgumentParser(
        prog="omniwall",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""
⚔️  OmniWall: Универсальная 4K-ротация обоев для любого Linux-дистрибутива.
Поддерживает KDE Plasma, GNOME, XFCE, Cinnamon, MATE, Wayland (swww), X11 (feh).
Поиск на русском и английском, мульти-источники, оффлайн-буфер и гибкое расписание.
        """,
        epilog="""
Примеры использования:
  omniwall next                           Следующие 4K обои по умолчанию (Warhammer 40,000)
  omniwall next --tag "дота 2"            Поиск по русскому тегу (авто-перевод на EN)
  omniwall next --tag "криг" --ratio 16x9 Корпус Смерти Крига строго 16:9
  omniwall schedule 15:30                 Настроить смену обоев на 15:30 ежедневно
  omniwall schedule 6h                    Настроить смену обоев каждые 6 часов
  omniwall buffer                         Проверить статус оффлайн-буфера
  omniwall buffer -b 10 --sync            Пополнить буфер до 10 обоев на случай оффлайна
  omniwall prev                           Откатить на предыдущие обои
  omniwall current                        Показать информацию о текущих обоях
  omniwall list                           Показать все сохранённые файлы в кэше
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Команда для выполнения")

    # Command: next
    parser_next = subparsers.add_parser("next", help="Установить следующие обои (по умолчанию)")
    parser_next.add_argument("-t", "--tag", "-q", "--query", type=str, help="Тег на русском или английском (например: вархаммер, 'дота 2', криг, astartes)")
    parser_next.add_argument("-r", "--ratio", type=str, help="Соотношение сторон (например: 16x9, 16x10, 21x9, 32x9)")
    parser_next.add_argument("--res", "--resolution", dest="resolution", type=str, help="Минимальное разрешение (например: 3840x2160, 2560x1440)")
    parser_next.add_argument("-b", "--buffer", type=int, help="Размер оффлайн-буфера обоев (по умолчанию: 5)")
    parser_next.add_argument("-l", "--local", action="store_true", help="Брать только из оффлайн-буфера/кэша, без интернета")
    parser_next.add_argument("-s", "--silent", action="store_true", help="Не показывать всплывающее уведомление")

    # Command: schedule
    parser_sched = subparsers.add_parser("schedule", help="Настроить время смены обоев (systemd таймер)")
    parser_sched.add_argument("time", nargs="?", type=str, help="Время суток (15:30, 09:00) или интервал (6h, 12h)")

    # Command: buffer
    parser_buf = subparsers.add_parser("buffer", help="Управление оффлайн-буфером обоев")
    parser_buf.add_argument("-b", "--buffer", type=int, help="Задать целевое количество обоев в буфере")
    parser_buf.add_argument("--sync", action="store_true", help="Принудительно докачать недостающие обои в буфер")
    parser_buf.add_argument("-t", "--tag", type=str, help="Тег для пополнения буфера (RU или EN)")

    # Command: prev
    parser_prev = subparsers.add_parser("prev", help="Вернуться к предыдущим обоям из истории")
    parser_prev.add_argument("-s", "--silent", action="store_true", help="Не показывать всплывающее уведомление")

    # Command: current
    subparsers.add_parser("current", help="Показать информацию о текущих установленных обоях")

    # Command: list
    parser_list = subparsers.add_parser("list", help="Список локальных сохранённых обоев")
    parser_list.add_argument("-t", "--tag", "-q", "--query", type=str, help="Фильтровать список по ключевому слову")

    return parser

def main():
    config = load_config()
    parser = build_parser()

    if len(sys.argv) == 1:
        args = parser.parse_args(["next"])
    else:
        if sys.argv[1].startswith("-") and sys.argv[1] not in ("-h", "--help"):
            args = parser.parse_args(["next"] + sys.argv[1:])
        else:
            args = parser.parse_args()

    if args.command in (None, "next"):
        cmd_next(args, config)
    elif args.command in ("schedule", "time", "timer"):
        cmd_schedule(args, config)
    elif args.command in ("buffer", "sync"):
        cmd_buffer(args, config)
    elif args.command in ("prev", "previous"):
        cmd_prev(args, config)
    elif args.command in ("current", "status", "info"):
        cmd_current(args)
    elif args.command in ("list", "ls"):
        cmd_list(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
