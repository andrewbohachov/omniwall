#!/usr/bin/env python3
"""
w40k-wallpaper / wallpapers:
Automated & On-Demand 4K Wallpaper Rotator for Linux (KDE Plasma & Freedesktop).
Supports arbitrary tags, aspect ratios, resolutions, and systemd daily automation.
"""

import sys
import os
import json
import random
import argparse
import urllib.request
import urllib.parse
import subprocess
from pathlib import Path
from datetime import datetime

CONFIG_DIR = Path.home() / ".config" / "w40k-wallpaper"
CACHE_DIR = Path.home() / ".local" / "share" / "w40k-wallpaper" / "wallpapers"
STATE_FILE = CONFIG_DIR / "state.json"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "min_resolution": "3840x2160",
    "ratios": "16x9",
    "purity": "100",  # SFW: 100 = sfw, 110 = sfw+sketchy
    "categories": "111",  # general/anime/people
    "default_queries": [
        "id:2143",  # Warhammer 40,000 on Wallhaven
        "Astra Militarum",
        "Death Korps of Krieg",
        "Iron Hands",
        "Salamanders 40k",
        "Black Templars",
        "Dreadnought warhammer"
    ],
    "desktop_notifications": True,
    "apply_command": "plasma-apply-wallpaperimage"
}

def load_config():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
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

def notify(title, message):
    try:
        subprocess.run(
            ["notify-send", "-a", "Wallpapers", "-i", "preferences-desktop-wallpaper", title, message],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception:
        pass

def apply_wallpaper(image_path, title=None, config=None, silent=False):
    cmd = config.get("apply_command", "plasma-apply-wallpaperimage") if config else "plasma-apply-wallpaperimage"
    try:
        subprocess.run([cmd, str(image_path)], capture_output=True, text=True, check=True)
        state = load_state()
        state["history"].append(state.get("current"))
        state["history"] = [h for h in state["history"] if h][-50:]
        state["current"] = {
            "path": str(image_path),
            "title": title or Path(image_path).name,
            "applied_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_state(state)

        if not silent and config and config.get("desktop_notifications", True):
            notify("Обои обновлены", f"{title or Path(image_path).stem}")
        print(f"✓ Обои успешно применены: {image_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при смене обоев: {e.stderr}", file=sys.stderr)
        return False
    except FileNotFoundError:
        print(f"Команда '{cmd}' не найдена в вашей графической среде.", file=sys.stderr)
        return False

def fetch_online_wallpaper(query, min_res, ratio, purity="100", categories="111"):
    """
    Query Wallhaven API with custom query, resolution, ratio and purity.
    """
    headers = {"User-Agent": "Mozilla/5.0 (Linux; x86_64) w40k-wallpaper/2.0"}
    encoded_q = urllib.parse.quote(query)
    url = (
        f"https://wallhaven.cc/api/v1/search?"
        f"q={encoded_q}&atleast={min_res}&ratios={ratio}&purity={purity}&categories={categories}&sorting=random"
    )

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        items = data.get("data", [])
        if not items:
            return None

        choice = random.choice(items)
        img_id = choice["id"]
        ext = choice["file_type"].split("/")[-1]
        if ext == "jpeg":
            ext = "jpg"
        target_file = CACHE_DIR / f"{img_id}.{ext}"

        if not target_file.exists():
            print(f"Загрузка арта [{choice['resolution']}] по запросу '{query}'...")
            dl_req = urllib.request.Request(choice["path"], headers=headers)
            with urllib.request.urlopen(dl_req, timeout=25) as resp, open(target_file, "wb") as f:
                f.write(resp.read())

        title = f"{query} ({choice['resolution']})"
        return target_file, title
    except Exception as e:
        print(f"Предупреждение сети ({e}). Переключение на локальную коллекцию...")
        return None

def get_local_wallpapers(filter_query=None):
    exts = {".jpg", ".jpeg", ".png", ".webp"}
    dirs = [
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

def cmd_next(args, config):
    query = args.tag or args.query
    if not query:
        query = random.choice(config.get("default_queries", ["id:2143"]))

    min_res = args.resolution or config.get("min_resolution", "3840x2160")
    ratio = args.ratio or config.get("ratios", "16x9")

    # If not forced local-only, try online
    if not args.local:
        fresh = fetch_online_wallpaper(query, min_res, ratio, purity=config.get("purity", "100"))
        if fresh:
            path, title = fresh
            apply_wallpaper(path, title, config, silent=args.silent)
            return

    # Fallback to local
    local_files = get_local_wallpapers(filter_query=args.tag or args.query)
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
    print("│                 ТЕКУЩИЕ ОБОИ РАБОЧЕГО СТОЛА            │")
    print("└────────────────────────────────────────────────────────┘")
    print(f"  Название   : {curr.get('title')}")
    print(f"  Файл       : {curr.get('path')}")
    print(f"  Установлен : {curr.get('applied_at')}")

def cmd_list(args):
    files = get_local_wallpapers(filter_query=args.tag or args.query)
    if not files:
        print("Локальная библиотека пуста.")
        return
    print(f"Найдено локальных обоев: {len(files)}")
    for f in sorted(files):
        print(f"  • {f.name} ({f.parent})")

def build_parser():
    parser = argparse.ArgumentParser(
        prog="wallpapers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""
⚔️  Wallpapers CLI: Умная ротация 4K-обоев для Linux (Warhammer 40,000 & кастомные теги).
Поддерживает работу по расписанию в systemd и ручную смену с фильтрами.
        """,
        epilog="""
Примеры использования:
  wallpapers next                           Установить следующие случайные обои по умолчанию (Ваха 4K)
  wallpapers next --tag "dota 2"            Установить обои по тегу 'dota 2' в 4K
  wallpapers next --tag "Krieg" --ratio 16x9 Обои с Death Korps of Krieg строго 16:9
  wallpapers next --res 2560x1440           Задать минимальное разрешение 2K
  wallpapers next --local                   Использовать только локальные сохранённые файлы
  wallpapers prev                           Откатить на предыдущие обои
  wallpapers current                        Показать информацию о текущих обоях
  wallpapers list                           Показать все сохранённые файлы в кэше
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Команда для выполнения")

    # Command: next
    parser_next = subparsers.add_parser("next", help="Установить следующие обои (по умолчанию)")
    parser_next.add_argument("-t", "--tag", "-q", "--query", type=str, help="Тег или поисковый запрос (например: warhammer, 'dota 2', krieg, astartes)")
    parser_next.add_argument("-r", "--ratio", type=str, help="Соотношение сторон (например: 16x9, 16x10, 21x9, 32x9)")
    parser_next.add_argument("--res", "--resolution", dest="resolution", type=str, help="Минимальное разрешение (например: 3840x2160, 2560x1440, 1920x1080)")
    parser_next.add_argument("-l", "--local", action="store_true", help="Брать только из локального кэша, без интернета")
    parser_next.add_argument("-s", "--silent", action="store_true", help="Не показывать всплывающее уведомление")

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

    # Default to 'next' if no positional command passed
    if len(sys.argv) == 1:
        args = parser.parse_args(["next"])
    else:
        # Check if first arg is a known flag rather than command (e.g. wallpapers --tag "dota 2")
        if sys.argv[1].startswith("-") and sys.argv[1] not in ("-h", "--help"):
            args = parser.parse_args(["next"] + sys.argv[1:])
        else:
            args = parser.parse_args()

    if args.command in (None, "next"):
        cmd_next(args, config)
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
