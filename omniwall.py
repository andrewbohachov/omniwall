#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OmniWall: Universal 4K Wallpaper Rotator for Linux
Supports KDE Plasma, GNOME, XFCE, Cinnamon, MATE, Wayland (swww), X11 (feh).
Supports English and Russian UI, multi-source 4K fetching, tag pinning, offline buffer,
and user-defined total storage limits with LRU cache retention.
"""

import os
import sys
import json
import time
import random
import shutil
import argparse
import subprocess
import urllib.request
import urllib.parse
import re
from pathlib import Path
from datetime import datetime

# ----------------- PATHS & CONFIG -----------------

CONFIG_DIR = Path.home() / ".config" / "omniwall"
CACHE_DIR = Path.home() / ".local" / "share" / "omniwall" / "wallpapers"
BUFFER_DIR = Path.home() / ".local" / "share" / "omniwall" / "buffer"
STATE_FILE = CONFIG_DIR / "state.json"
CONFIG_FILE = CONFIG_DIR / "config.json"
SYSTEMD_USER_DIR = Path.home() / ".config" / "systemd" / "user"
TIMER_FILE = SYSTEMD_USER_DIR / "omniwall.timer"

DEFAULT_CONFIG = {
    "language": "en",  # "en" or "ru"
    "min_resolution": "3840x2160",
    "ratios": "16x9",
    "purity": "100",  # SFW
    "buffer_size": 5,
    "max_storage_mb": 100,  # Total combined storage limit in MB
    "max_cached_files": 15,
    "max_file_size_mb": 15,
    "schedule": "12:00",
    "sources": ["wallhaven", "bing"],
    "default_queries": [
        "nature landscape",
        "mountains 4k",
        "deep space galaxy",
        "minimalist architecture",
        "sunset aesthetic"
    ],
    "desktop_notifications": True
}

LOCAL_DICTIONARY = {
    "горы": "mountains landscape",
    "природа": "nature landscape",
    "космос": "deep space galaxy",
    "архитектура": "minimalist architecture",
    "минимализм": "minimalism landscape",
    "закат": "sunset landscape",
    "лес": "forest landscape",
    "море": "ocean seascape",
    "океан": "ocean seascape",
    "машины": "supercars",
    "авто": "supercars",
    "город": "cityscape night",
    "ночной город": "cityscape night",
    "вархаммер": "Warhammer 40000",
    "ваха": "Warhammer 40000",
    "криг": "Death Korps of Krieg",
    "дота": "Dota 2",
    "дота 2": "Dota 2",
    "киберпанк": "Cyberpunk aesthetic",
    "ведьмак": "The Witcher 3"
}

# ----------------- LOCALIZATION (I18N) -----------------

STRINGS = {
    "en": {
        "prog_desc": "OmniWall: Universal 4K Wallpaper Rotator for any Linux desktop.\nSupports KDE Plasma, GNOME, XFCE, Cinnamon, MATE, Wayland (swww), X11 (feh).\nBilingual search, multi-source aggregation, offline buffer, and flexible scheduling.",
        "epilog": """Usage examples:
  omniwall next                           Set next 4K wallpaper (pinned tag or default)
  omniwall next --tag "mountains"         Pin tag "mountains" and apply wallpaper
  omniwall next --reset-tag               Reset pinned tag and return to default rotation
  omniwall limit 50MB                     Set total storage limit for all wallpapers (50 MB)
  omniwall limit 100MB                    Set total storage limit for all wallpapers (100 MB)
  omniwall limit                          Show current storage usage and limit
  omniwall cache --clean                  Purge old cached wallpapers (free disk space)
  omniwall tag "space"                    Pin tag without immediately changing wallpaper
  omniwall tag                            Show currently pinned tag
  omniwall lang ru                        Switch UI language to Russian
  omniwall lang en                        Switch UI language to English
  omniwall schedule 15:30                 Set daily rotation at 15:30
  omniwall schedule 6h                    Set rotation every 6 hours
  omniwall buffer                         Check offline buffer status
  omniwall buffer -b 10 --sync            Fill offline buffer up to 10 wallpapers
  omniwall prev                           Roll back to previous wallpaper
  omniwall current                        Display current wallpaper information
  omniwall list                           List saved local wallpapers""",
        "cmd_next_help": "Set next wallpaper (default action)",
        "cmd_limit_help": "View or configure total storage limit for all images",
        "cmd_tag_help": "View or pin main search tag",
        "cmd_cache_help": "Manage cache size and disk optimization",
        "cmd_schedule_help": "Configure wallpaper change schedule (systemd timer)",
        "cmd_buffer_help": "Manage offline wallpaper buffer",
        "cmd_prev_help": "Return to previous wallpaper from history",
        "cmd_current_help": "Show information about currently applied wallpaper",
        "cmd_list_help": "List local saved wallpapers",
        "cmd_lang_help": "Switch or display UI language (en / ru)",
        "tag_help": "Search tag (e.g. 'mountains', 'space', 'architecture')",
        "reset_tag_help": "Reset pinned tag and return to default topics",
        "ratio_help": "Aspect ratio (e.g. 16x9, 16x10, 21x9, 32x9)",
        "res_help": "Minimum resolution (e.g. 3840x2160, 2560x1440)",
        "buffer_help": "Offline buffer size (default: 5)",
        "local_help": "Use only local buffer/cache without internet",
        "silent_help": "Do not show desktop notifications",
        "limit_size_help": "Total storage limit (e.g. 50MB, 100MB, 1GB)",
        "tag_apply_help": "Immediately download and apply wallpaper for this tag",
        "tag_reset_help": "Reset pinned tag to default rotation",
        "cache_clean_help": "Purge all old wallpapers (keeps active and buffer)",
        "cache_limit_help": "Total storage limit across all pictures (e.g. 50MB, 100MB)",
        "cache_files_help": "Maximum number of files in cache",
        "schedule_time_help": "Time of day (15:30, 09:00) or interval (6h, 12h)",
        "buffer_sync_help": "Download missing wallpapers into buffer immediately",
        "lang_name_help": "Language code: 'en' (English) or 'ru' (Russian)",
        "lang_saved": "Language changed to English (en).",
        "lang_current": "Current language: English (en).",
        "lang_usage": "Usage: omniwall lang en | omniwall lang ru",
        "applied_success": "Wallpaper applied ({env}): {path}",
        "applied_failed": "Error: Failed to apply wallpaper for your desktop environment.",
        "search_tag": "Searching wallpapers for tag: '{raw}' (EN: '{en}')",
        "tag_pinned": "Tag '{tag}' pinned! Subsequent 'next' calls will use this tag.",
        "using_pinned_tag": "Using pinned tag: '{tag}' (EN: '{en}')",
        "tag_reset_msg": "Pinned tag reset. Returned to default rotation.",
        "tag_not_pinned": "No tag pinned (using default rotation).",
        "tag_info_pinned": "Current pinned tag: '{tag}' (EN: '{en}')",
        "tag_usage_title": "Usage:",
        "tag_usage_pin": "  omniwall tag \"nature\"         # Pin tag 'nature'",
        "tag_usage_apply": "  omniwall tag \"mountains\" -a   # Pin and apply immediately",
        "tag_usage_reset": "  omniwall tag --reset          # Reset to default rotation",
        "storage_title": "OMNIWALL: TOTAL STORAGE USAGE",
        "storage_cache": "  Cache & History: {count} files ({mb:.1f} MB)",
        "storage_buffer": "  Offline buffer : {count} files ({mb:.1f} MB / target {target} items)",
        "storage_total": "  TOTAL USED     : {count} files — {total_mb:.1f} MB of {max_mb} MB ({percent:.1f}%)",
        "storage_limit": "  Total limit    : {max_mb} MB (max {max_files} files in cache)",
        "storage_cmds": "Storage commands:\n  omniwall limit 50MB              # Set total limit to 50 MB\n  omniwall limit 100MB             # Set total limit to 100 MB\n  omniwall limit 1GB               # Set total limit to 1 GB\n  omniwall cache --clean           # Clean old wallpapers now",
        "limit_saved": "New total storage limit saved: {mb} MB",
        "limit_error": "Invalid size format: '{val}'. Examples: 50MB, 100, 200MB, 1GB.",
        "cleaned_count": "Cleaned: {count} old files ({mb:.1f} MB)",
        "cache_cleaned": "Cache cleanup finished: deleted {count} old wallpapers ({mb:.1f} MB).\n(Active wallpaper and offline buffer preserved).",
        "current_title": "OMNIWALL: CURRENT DESKTOP WALLPAPER",
        "current_name": "  Title       : {title}",
        "current_env": "  Environment : {env}",
        "current_tag_pinned": "  Active tag  : {tag} (pinned)",
        "current_tag_default": "  Active tag  : Default rotation",
        "current_file": "  File        : {path}",
        "current_applied": "  Applied at  : {time}",
        "current_none": "No wallpaper currently tracked.",
        "prev_empty": "Wallpaper history is empty.",
        "prev_not_found": "Previous file is no longer found on disk.",
        "list_empty": "Local wallpaper library is empty.",
        "list_found": "Found local wallpapers: {count}",
        "buffer_full": "Buffer is full: {count}/{target} wallpapers ready for offline use.",
        "buffer_downloading": "Filling buffer: downloading {needed} wallpapers (target: {target})...",
        "buffer_added": "  + [{added}/{needed}] Added to buffer: {title}",
        "buffer_done": "Done! Current offline buffer: {total} wallpapers.",
        "sched_current": "Current schedule: {sched}",
        "sched_help": "To change schedule, specify time. Examples:\n  omniwall schedule 15:30   (daily at 15:30)\n  omniwall schedule 08:00   (daily at 08:00)\n  omniwall schedule 6h      (every 6 hours)",
        "sched_error": "Invalid time format: '{time}'. Examples: 15:30, 09:00, 6h, 12h.",
        "sched_configured": "Schedule configured: {desc}",
        "sched_timer_restarted": "Active systemd timer restarted with new schedule.",
        "sched_timer_inactive": "(Timer is inactive. To start: systemctl --user enable --now omniwall.timer)",
        "no_local_or_network": "Error: No local wallpapers found and network fetch returned no results."
    },
    "ru": {
        "prog_desc": "OmniWall: Универсальная 4K-ротация обоев для любого Linux-дистрибутива.\nПоддерживает KDE Plasma, GNOME, XFCE, Cinnamon, MATE, Wayland (swww), X11 (feh).\nПоиск на русском и английском, мульти-источники, оффлайн-буфер и гибкое расписание.",
        "epilog": """Примеры использования:
  omniwall next                           Следующие 4K обои (по закреплённому тегу или по умолчанию)
  omniwall next --tag "горы"              Закрепить тег "горы" и сразу поставить обои
  omniwall next --reset-tag               Сбросить закрепление и вернуться к темам по умолчанию
  omniwall limit 50MB                     Задать суммарный лимит на ВСЕ картинки (50 МБ)
  omniwall limit 100MB                    Задать суммарный лимит на ВСЕ картинки (100 МБ)
  omniwall limit                          Показать текущий суммарный объем и лимит
  omniwall cache --clean                  Очистить старые файлы кэша (освободить диск)
  omniwall tag "космос"                   Закрепить тег без немедленной смены обоев
  omniwall tag                            Показать текущий активный закреплённый тег
  omniwall lang en                        Переключить язык интерфейса на английский
  omniwall lang ru                        Переключить язык интерфейса на русский
  omniwall schedule 15:30                 Настроить смену обоев на 15:30 ежедневно
  omniwall schedule 6h                    Настроить смену обоев каждые 6 часов
  omniwall buffer                         Проверить статус оффлайн-буфера
  omniwall buffer -b 10 --sync            Пополнить буфер до 10 обоев на случай оффлайна
  omniwall prev                           Откатить на предыдущие обои
  omniwall current                        Показать информацию о текущих обоях
  omniwall list                           Показать все сохранённые файлы в кэше""",
        "cmd_next_help": "Установить следующие обои (по умолчанию)",
        "cmd_limit_help": "Задать или просмотреть суммарный лимит размера на ВСЕ картинки",
        "cmd_tag_help": "Просмотреть или закрепить основной тег поиска",
        "cmd_cache_help": "Управление размером кэша и оптимизация дискового пространства",
        "cmd_schedule_help": "Настроить время смены обоев (systemd таймер)",
        "cmd_buffer_help": "Управление оффлайн-буфером обоев",
        "cmd_prev_help": "Вернуться к предыдущим обоям из истории",
        "cmd_current_help": "Показать информацию о текущих установленных обоях",
        "cmd_list_help": "Список локальных сохранённых обоев",
        "cmd_lang_help": "Переключить или показать язык интерфейса (en / ru)",
        "tag_help": "Тег на русском или английском (закрепляется для последующих вызовов next)",
        "reset_tag_help": "Сбросить закреплённый тег и вернуться к темам по умолчанию",
        "ratio_help": "Соотношение сторон (например: 16x9, 16x10, 21x9, 32x9)",
        "res_help": "Минимальное разрешение (например: 3840x2160, 2560x1440)",
        "buffer_help": "Размер оффлайн-буфера обоев (по умолчанию: 5)",
        "local_help": "Брать только из оффлайн-буфера/кэша, без интернета",
        "silent_help": "Не показывать всплывающее уведомление",
        "limit_size_help": "Лимит на сумму всех файлов (например: 50MB, 100MB, 200MB, 1GB)",
        "tag_apply_help": "Сразу скачать и применить новые обои по этому тегу",
        "tag_reset_help": "Сбросить закрепление и вернуться к темам по умолчанию",
        "cache_clean_help": "Принудительно удалить все старые обои (кроме текущих и буфера)",
        "cache_limit_help": "Суммарный лимит размера на ВСЕ картинки (например: 50MB, 100MB)",
        "cache_files_help": "Задать максимальное количество файлов в кэше (например: 10, 15)",
        "schedule_time_help": "Время суток (15:30, 09:00) или интервал (6h, 12h)",
        "buffer_sync_help": "Принудительно докачать недостающие обои в буфер",
        "lang_name_help": "Код языка: 'en' (английский) или 'ru' (русский)",
        "lang_saved": "Язык интерфейса изменён на русский (ru).",
        "lang_current": "Текущий язык интерфейса: русский (ru).",
        "lang_usage": "Использование: omniwall lang en | omniwall lang ru",
        "applied_success": "Обои успешно применены ({env}): {path}",
        "applied_failed": "Ошибка: не удалось установить обои автоматически для вашего окружения.",
        "search_tag": "Поиск обоев по тегу: '{raw}' (EN: '{en}')",
        "tag_pinned": "Тег '{tag}' закреплён! Последующие вызовы 'next' будут искать по нему.",
        "using_pinned_tag": "Используется закреплённый тег: '{tag}' (EN: '{en}')",
        "tag_reset_msg": "Закрепление тега сброшено. Возврат к темам по умолчанию.",
        "tag_not_pinned": "Тег не закреплен (ротация тем по умолчанию).",
        "tag_info_pinned": "Текущий закреплённый тег: '{tag}' (EN: '{en}')",
        "tag_usage_title": "Использование:",
        "tag_usage_pin": "  omniwall tag \"природа\"         # Закрепить тему 'природа'",
        "tag_usage_apply": "  omniwall tag \"горы\" --apply    # Закрепить и сразу применить новые обои",
        "tag_usage_reset": "  omniwall tag --reset          # Сбросить закрепление и вернуться к темам по умолчанию",
        "storage_title": "OMNIWALL: ОБЩИЙ ОБЪЁМ ХРАНИЛИЩА ВСЕХ ОБОЕВ",
        "storage_cache": "  Кэш и история  : {count} файлов ({mb:.1f} МБ)",
        "storage_buffer": "  Оффлайн-буфер  : {count} файлов ({mb:.1f} МБ / цель {target} шт.)",
        "storage_total": "  ИТОГО ЗАНЯТО   : {count} файлов — {total_mb:.1f} МБ из {max_mb} МБ ({percent:.1f}%)",
        "storage_limit": "  Суммарный лимит: {max_mb} МБ (макс. {max_files} файлов в кэше)",
        "storage_cmds": "Команды управления размером:\n  omniwall limit 50MB              # Задать суммарный лимит 50 МБ\n  omniwall limit 100MB             # Задать суммарный лимит 100 МБ\n  omniwall limit 1GB               # Задать суммарный лимит 1 ГБ\n  omniwall cache --clean           # Очистить старые обои прямо сейчас",
        "limit_saved": "Новый суммарный лимит на ВСЕ картинки сохранён: {mb} МБ",
        "limit_error": "Ошибка формата размера: '{val}'. Примеры: 50MB, 100, 200MB, 1GB.",
        "cleaned_count": "Автоматически освобождено: {count} старых файлов ({mb:.1f} МБ)",
        "cache_cleaned": "Очистка кэша завершена: удалено {count} старых обоев ({mb:.1f} МБ).\n(Текущие активные обои и оффлайн-буфер сохранены).",
        "current_title": "OMNIWALL: ТЕКУЩИЕ ОБОИ РАБОЧЕГО СТОЛА",
        "current_name": "  Название     : {title}",
        "current_env": "  Окружение    : {env}",
        "current_tag_pinned": "  Активный тег : {tag} (закреплён)",
        "current_tag_default": "  Активный тег : Ротация по умолчанию",
        "current_file": "  Файл         : {path}",
        "current_applied": "  Установлен   : {time}",
        "current_none": "Текущие обои не зафиксированы утилитой.",
        "prev_empty": "История предыдущих обоев пуста.",
        "prev_not_found": "Предыдущий файл больше не найден на диске.",
        "list_empty": "Локальная библиотека пуста.",
        "list_found": "Найдено локальных обоев: {count}",
        "buffer_full": "Буфер полон: {count}/{target} обоев готовы к оффлайн-работе.",
        "buffer_downloading": "Пополнение буфера: скачивание {needed} обоев (цель: {target})...",
        "buffer_added": "  + [{added}/{needed}] Добавлено в буфер: {title}",
        "buffer_done": "Готово! Текущий оффлайн-буфер: {total} обоев.",
        "sched_current": "Текущее расписание: {sched}",
        "sched_help": "Чтобы изменить расписание, укажите время. Например:\n  omniwall schedule 15:30   (каждый день в 15:30)\n  omniwall schedule 08:00   (каждый день в 08:00)\n  omniwall schedule 6h      (каждые 6 часов)",
        "sched_error": "Ошибка формата времени: '{time}'. Примеры правильного формата:\n  omniwall schedule 15:30\n  omniwall schedule 09:00\n  omniwall schedule 6h",
        "sched_configured": "Расписание успешно настроено: {desc}",
        "sched_timer_restarted": "Активный таймер systemd перезапущен с новым временем.",
        "sched_timer_inactive": "(Таймер пока не включен. Для старта выполните: systemctl --user enable --now omniwall.timer)",
        "no_local_or_network": "Ошибка: локальные обои не найдены и сетевой запрос не вернул результатов."
    }
}

def get_lang(config=None):
    if config and config.get("language") in ("ru", "en"):
        return config["language"]
    return "en"

def msg(key, config=None, **kwargs):
    lang = get_lang(config)
    tpl = STRINGS.get(lang, STRINGS["en"]).get(key, STRINGS["en"].get(key, key))
    if kwargs:
        try:
            return tpl.format(**kwargs)
        except Exception:
            return tpl
    return tpl

# ----------------- CONFIG & STATE HELPERS -----------------

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

# ----------------- STORAGE & CACHE MANAGEMENT -----------------

def parse_size_to_mb(val_str):
    if val_str is None:
        return None
    if isinstance(val_str, (int, float)):
        return max(5, int(val_str))
    s = str(val_str).strip().lower().replace(" ", "")
    m = re.match(r"^(\d+(?:\.\d+)?)\s*(gb|гб|g|mb|мб|m)?$", s)
    if not m:
        return None
    num = float(m.group(1))
    unit = m.group(2) or "mb"
    if unit in ("gb", "гб", "g"):
        return max(5, int(num * 1024))
    return max(5, int(num))

def get_directory_stats(dir_path):
    if not dir_path.exists():
        return 0, 0, []
    files = [f for f in dir_path.iterdir() if f.is_file() and f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}]
    total_bytes = sum(f.stat().st_size for f in files)
    return len(files), total_bytes, files

def get_storage_stats():
    c_count, c_bytes, c_files = get_directory_stats(CACHE_DIR)
    b_count, b_bytes, b_files = get_directory_stats(BUFFER_DIR)
    return {
        "cache_count": c_count,
        "cache_bytes": c_bytes,
        "cache_files": c_files,
        "buffer_count": b_count,
        "buffer_bytes": b_bytes,
        "buffer_files": b_files,
        "total_count": c_count + b_count,
        "total_bytes": c_bytes + b_bytes
    }

def cleanup_storage(config, force_clean=False):
    max_mb = config.get("max_storage_mb", config.get("max_cache_mb", 100))
    max_bytes = max_mb * 1024 * 1024
    max_files = config.get("max_cached_files", 15)

    state = load_state()
    protected_paths = set()

    if state.get("current") and state["current"].get("path"):
        try:
            curr_p = Path(state["current"]["path"]).resolve()
            if curr_p.exists():
                protected_paths.add(curr_p)
        except Exception:
            pass

    history = state.get("history", [])
    if history:
        try:
            prev_p = Path(history[-1]["path"]).resolve()
            if prev_p.exists():
                protected_paths.add(prev_p)
        except Exception:
            pass

    stats = get_storage_stats()
    total_bytes = stats["total_bytes"]
    cache_files = stats["cache_files"]
    buffer_files = stats["buffer_files"]

    cache_files.sort(key=lambda f: f.stat().st_mtime)

    deleted_count = 0
    deleted_bytes = 0

    if force_clean:
        for f in cache_files:
            if f.resolve() not in protected_paths:
                f_size = f.stat().st_size
                try:
                    f.unlink()
                    deleted_count += 1
                    deleted_bytes += f_size
                except Exception:
                    pass
    else:
        for f in cache_files:
            curr_total = total_bytes - deleted_bytes
            curr_cache_count = len(cache_files) - deleted_count
            if curr_total <= max_bytes and curr_cache_count <= max_files:
                break

            if f.resolve() in protected_paths:
                continue

            f_size = f.stat().st_size
            try:
                f.unlink()
                deleted_count += 1
                deleted_bytes += f_size
            except Exception:
                pass

        if (total_bytes - deleted_bytes) > max_bytes and len(buffer_files) > 2:
            buffer_files.sort(key=lambda f: f.stat().st_mtime)
            for f in buffer_files:
                if (total_bytes - deleted_bytes) <= max_bytes or (len(buffer_files) - deleted_count) <= 2:
                    break
                if f.resolve() in protected_paths:
                    continue
                f_size = f.stat().st_size
                try:
                    f.unlink()
                    deleted_count += 1
                    deleted_bytes += f_size
                except Exception:
                    pass

    if deleted_count > 0:
        new_hist = [h for h in history if Path(h["path"]).exists()]
        if len(new_hist) != len(history):
            state["history"] = new_hist
            save_state(state)

    return deleted_count, deleted_bytes

cleanup_cache = cleanup_storage

# ----------------- DESKTOP ENVIRONMENT DETECTION -----------------

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

    # 2. GNOME / Unity
    if "gnome" in de or "unity" in de or "pop" in de or "ubuntu" in de:
        try:
            subprocess.run(["gsettings", "set", "org.gnome.desktop.background", "picture-uri", file_uri], check=True)
            subprocess.run(["gsettings", "set", "org.gnome.desktop.background", "picture-uri-dark", file_uri], check=False)
            return True, "GNOME"
        except Exception:
            pass

    # 3. Cinnamon
    if "cinnamon" in de or "x-cinnamon" in de:
        try:
            subprocess.run(["gsettings", "set", "org.cinnamon.desktop.background", "picture-uri", file_uri], check=True)
            return True, "Cinnamon"
        except Exception:
            pass

    # 4. MATE
    if "mate" in de:
        try:
            subprocess.run(["gsettings", "set", "org.mate.background", "picture-filename", str(abs_path)], check=True)
            return True, "MATE"
        except Exception:
            pass

    # 5. XFCE
    if "xfce" in de and shutil.which("xfconf-query"):
        try:
            res = subprocess.run(["xfconf-query", "-c", "xfce4-desktop", "-l"], capture_output=True, text=True)
            for line in res.stdout.splitlines():
                if "last-image" in line or "image-path" in line:
                    prop = line.strip()
                    subprocess.run(["xfconf-query", "-c", "xfce4-desktop", "-p", prop, "-s", str(abs_path)], check=False)
            return True, "XFCE"
        except Exception:
            pass

    # 6. Wayland tiling (swww, hyprpaper, swaybg)
    if "wayland" in os.environ.get("XDG_SESSION_TYPE", "").lower() or "hyprland" in de or "sway" in de:
        if shutil.which("swww"):
            try:
                subprocess.run(["swww", "img", str(abs_path), "--transition-type", "fade", "--transition-fps", "60"], check=True)
                return True, "Wayland (swww)"
            except Exception:
                pass

    # 7. Generic X11 (feh, nitrogen)
    if shutil.which("feh"):
        try:
            subprocess.run(["feh", "--bg-fill", str(abs_path)], check=True)
            return True, "X11 (feh)"
        except Exception:
            pass

    if shutil.which("nitrogen"):
        try:
            subprocess.run(["nitrogen", "--set-zoom-fill", str(abs_path)], check=True)
            return True, "X11 (nitrogen)"
        except Exception:
            pass

    return False, "Unknown"

def apply_wallpaper(image_path, title=None, config=None, silent=False):
    success, env_name = detect_and_apply_wallpaper(image_path)
    if success:
        state = load_state()
        history = state.get("history", [])
        curr = state.get("current")
        if curr and curr.get("path") != str(image_path):
            history.append(curr)
            if len(history) > 30:
                history.pop(0)

        state["history"] = history
        state["current"] = {
            "path": str(Path(image_path).resolve()),
            "title": title or Path(image_path).name,
            "applied_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "environment": env_name
        }
        save_state(state)

        if not silent and config and config.get("desktop_notifications", True):
            notify("OmniWall", f"{title or Path(image_path).stem}\n[{env_name}]")
        print(msg("applied_success", config, env=env_name, path=image_path))
        return True
    else:
        print(msg("applied_failed", config), file=sys.stderr)
        return False

# ----------------- WALLPAPER PROVIDERS -----------------

def fetch_wallhaven(query, min_res, ratio, config, purity="100"):
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

    max_bytes = config.get("max_file_size_mb", 15) * 1024 * 1024
    valid_items = [it for it in items if it.get("file_size", 0) <= max_bytes]
    if not valid_items:
        valid_items = items

    choice = random.choice(valid_items)
    img_id = choice["id"]
    ext = choice["file_type"].split("/")[-1]
    if ext == "jpeg":
        ext = "jpg"
    target_file = CACHE_DIR / f"wallhaven_{img_id}.{ext}"

    if not target_file.exists():
        dl_req = urllib.request.Request(choice["path"], headers=headers)
        with urllib.request.urlopen(dl_req, timeout=25) as dl_resp:
            cl = dl_resp.headers.get("Content-Length")
            if cl and int(cl) > max_bytes:
                return None
            data = dl_resp.read()
            if len(data) > max_bytes:
                return None
            with open(target_file, "wb") as f:
                f.write(data)

    return target_file, f"{query} [Wallhaven {choice['resolution']}]"

def fetch_bing_hd(query, config, min_res=None):
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

    max_bytes = config.get("max_file_size_mb", 15) * 1024 * 1024
    random.shuffle(valid_links)
    for img_url in valid_links[:5]:
        try:
            filename = f"web_{abs(hash(img_url))}.jpg"
            target_file = CACHE_DIR / filename
            if not target_file.exists():
                dl_req = urllib.request.Request(img_url, headers=headers)
                with urllib.request.urlopen(dl_req, timeout=15) as dl_resp:
                    cl = dl_resp.headers.get("Content-Length")
                    if cl and int(cl) > max_bytes:
                        continue
                    data = dl_resp.read()
                    if len(data) > max_bytes:
                        continue
                    with open(target_file, "wb") as f:
                        f.write(data)
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
                res = fetch_wallhaven(query, min_res, ratio, config, purity=config.get("purity", "100"))
                if res:
                    return res
            elif src == "bing":
                res = fetch_bing_hd(query, config, min_res)
                if res:
                    return res
        except Exception:
            continue
    return None

# ----------------- BUFFER & LOCAL STORAGE -----------------

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
        print(msg("buffer_full", config, count=len(current_files), target=target_count))
        return

    print(msg("buffer_downloading", config, needed=needed, target=target_count))
    if custom_tag:
        queries = [custom_tag]
    elif config.get("active_tag"):
        queries = [config.get("active_tag")]
    else:
        queries = config.get("default_queries", ["nature landscape"])

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
                    print(msg("buffer_added", config, added=added, needed=needed, title=title))
        except Exception:
            pass

    total = len(get_buffer_files())
    print(msg("buffer_done", config, total=total))
    cleanup_cache(config)

def get_local_wallpapers(filter_query=None):
    exts = {".jpg", ".jpeg", ".png", ".webp"}
    dirs = [
        BUFFER_DIR,
        CACHE_DIR,
        Path.home() / "Pictures" / "Wallpapers" / "OmniWall",
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

# ----------------- SCHEDULE MANAGEMENT -----------------

def update_schedule(time_str, config):
    clean_time = time_str.strip().lower()
    interval_match = re.match(r"^(\d+)\s*(h|ч|hour|hours)$", clean_time)
    time_match = re.match(r"^([01]?\d|2[0-3]):([0-5]\d)$", clean_time)

    lang = get_lang(config)
    if interval_match:
        hours = interval_match.group(1)
        calendar_rule = f"*-*-* 00/{hours}:00:00"
        desc_text = f"every {hours} hours" if lang == "en" else f"каждые {hours} ч."
    elif time_match:
        hh = time_match.group(1).zfill(2)
        mm = time_match.group(2)
        calendar_rule = f"*-*-* {hh}:{mm}:00"
        desc_text = f"daily at {hh}:{mm}" if lang == "en" else f"каждый день в {hh}:{mm}"
    else:
        print(msg("sched_error", config, time=time_str), file=sys.stderr)
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

    print(msg("sched_configured", config, desc=desc_text))
    print(f"  File: {TIMER_FILE}")

    try:
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True, capture_output=True)
        check = subprocess.run(["systemctl", "--user", "is-active", "omniwall.timer"], capture_output=True, text=True)
        if "active" in check.stdout:
            subprocess.run(["systemctl", "--user", "restart", "omniwall.timer"], check=False)
            print(f"  ✓ {msg('sched_timer_restarted', config)}")
        else:
            print(f"  {msg('sched_timer_inactive', config)}")
    except Exception:
        pass

    return True

# ----------------- CLI COMMANDS -----------------

def cmd_next(args, config):
    if getattr(args, "reset_tag", False):
        if "active_tag" in config:
            del config["active_tag"]
            save_config(config)
            print(msg("tag_reset_msg", config))

    raw_query = getattr(args, "tag", None)
    if raw_query:
        config["active_tag"] = raw_query
        save_config(config)
        query = translate_tag(raw_query)
        print(msg("search_tag", config, raw=raw_query, en=query))
        print(msg("tag_pinned", config, tag=raw_query))
    else:
        pinned = config.get("active_tag")
        if pinned:
            raw_query = pinned
            query = translate_tag(pinned)
            print(msg("using_pinned_tag", config, tag=pinned, en=query))
        else:
            query = translate_tag(random.choice(config.get("default_queries", ["nature landscape"])))

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
            cleanup_cache(config)
            return

    local_files = get_local_wallpapers(filter_query=raw_query)
    if not local_files:
        local_files = get_local_wallpapers()
    if not local_files:
        print(msg("no_local_or_network", config), file=sys.stderr)
        return

    state = load_state()
    current_path = state.get("current", {}).get("path") if state.get("current") else None
    candidates = [f for f in local_files if str(f) != current_path]
    chosen = random.choice(candidates if candidates else local_files)
    apply_wallpaper(chosen, chosen.stem.replace("_", " "), config, silent=args.silent)
    cleanup_cache(config)

def cmd_prev(args, config):
    state = load_state()
    history = state.get("history", [])
    if not history:
        print(msg("prev_empty", config))
        return
    prev_entry = history.pop()
    save_state(state)
    if prev_entry and Path(prev_entry["path"]).exists():
        apply_wallpaper(prev_entry["path"], prev_entry.get("title"), config, silent=args.silent)
    else:
        print(msg("prev_not_found", config))

def cmd_tag(args, config):
    if getattr(args, "reset", False):
        if "active_tag" in config:
            del config["active_tag"]
            save_config(config)
        print(msg("tag_reset_msg", config))
        return

    if args.tag_name:
        tag_val = args.tag_name.strip()
        config["active_tag"] = tag_val
        save_config(config)
        en = translate_tag(tag_val)
        print(f"✓ {msg('tag_pinned', config, tag=tag_val)}")
        if getattr(args, "apply", False):
            setattr(args, "tag", tag_val)
            cmd_next(args, config)
    else:
        active = config.get("active_tag")
        if active:
            en = translate_tag(active)
            print(msg("tag_info_pinned", config, tag=active, en=en))
        else:
            print(msg("tag_not_pinned", config))
        print(f"\n{msg('tag_usage_title', config)}")
        print(msg("tag_usage_pin", config))
        print(msg("tag_usage_apply", config))
        print(msg("tag_usage_reset", config))

def cmd_current(args, config=None):
    state = load_state()
    curr = state.get("current")
    if not curr:
        print(msg("current_none", config))
        return
    if config is None:
        config = load_config()
    print("┌────────────────────────────────────────────────────────┐")
    print(f"│         {msg('current_title', config):<46} │")
    print("└────────────────────────────────────────────────────────┘")
    print(msg("current_name", config, title=curr.get('title')))
    print(msg("current_env", config, env=curr.get('environment', 'Desktop')))
    pinned = config.get("active_tag")
    if pinned:
        print(msg("current_tag_pinned", config, tag=pinned))
    else:
        print(msg("current_tag_default", config))
    print(msg("current_file", config, path=curr.get('path')))
    print(msg("current_applied", config, time=curr.get('applied_at')))

def cmd_buffer(args, config):
    files = get_buffer_files()
    target = args.buffer or config.get("buffer_size", 5)
    print(f"=== {msg('storage_buffer', config, count=len(files), mb=sum(f.stat().st_size for f in files)/(1024*1024), target=target)} ===")
    for idx, f in enumerate(files, 1):
        print(f"  [{idx}] {f.name}")
    if args.sync or len(files) < target:
        sync_buffer(target, config, custom_tag=args.tag)

def cmd_schedule(args, config):
    if not args.time:
        curr_sched = config.get("schedule", "12:00")
        print(msg("sched_current", config, sched=curr_sched))
        print(msg("sched_help", config))
        return
    update_schedule(args.time, config)

def cmd_list(args):
    config = load_config()
    files = get_local_wallpapers(filter_query=getattr(args, "tag", None))
    if not files:
        print(msg("list_empty", config))
        return
    print(msg("list_found", config, count=len(files)))
    for f in sorted(files):
        print(f"  • {f.name} ({f.parent.name})")

def print_storage_summary(config):
    stats = get_storage_stats()
    cache_count = stats["cache_count"]
    cache_mb = stats["cache_bytes"] / (1024 * 1024)
    buf_count = stats["buffer_count"]
    buf_mb = stats["buffer_bytes"] / (1024 * 1024)
    total_count = stats["total_count"]
    total_mb = stats["total_bytes"] / (1024 * 1024)

    max_mb = config.get("max_storage_mb", config.get("max_cache_mb", 100))
    max_files = config.get("max_cached_files", 15)
    percent = (total_mb / max_mb * 100) if max_mb > 0 else 0

    print("┌────────────────────────────────────────────────────────┐")
    print(f"│      {msg('storage_title', config):<49} │")
    print("└────────────────────────────────────────────────────────┘")
    print(msg("storage_cache", config, count=cache_count, mb=cache_mb))
    print(msg("storage_buffer", config, count=buf_count, mb=buf_mb, target=config.get('buffer_size', 5)))
    print("  ────────────────────────────────────────────────────────")
    print(msg("storage_total", config, count=total_count, total_mb=total_mb, max_mb=max_mb, percent=percent))
    print(msg("storage_limit", config, max_mb=max_mb, max_files=max_files))
    print(f"\n{msg('storage_cmds', config)}")

def cmd_limit(args, config):
    val_str = getattr(args, "size", None)
    if val_str:
        mb = parse_size_to_mb(val_str)
        if not mb:
            print(msg("limit_error", config, val=val_str), file=sys.stderr)
            return
        config["max_storage_mb"] = mb
        save_config(config)
        print(f"✓ {msg('limit_saved', config, mb=mb)}")
        del_count, del_bytes = cleanup_storage(config)
        if del_count > 0:
            print(f"  {msg('cleaned_count', config, count=del_count, mb=del_bytes / (1024*1024))}")
    print_storage_summary(config)

def cmd_cache(args, config):
    modified = False
    size_input = getattr(args, "size", None) or getattr(args, "limit", None) or getattr(args, "max_mb", None)
    if size_input is not None:
        mb = parse_size_to_mb(size_input)
        if mb:
            config["max_storage_mb"] = mb
            modified = True
            print(f"✓ {msg('limit_saved', config, mb=mb)}")

    if getattr(args, "max_files", None) is not None:
        config["max_cached_files"] = int(args.max_files)
        modified = True
        print(f"✓ {msg('cache_files_help', config)}: {args.max_files}")

    if modified:
        save_config(config)
        del_count, del_bytes = cleanup_storage(config)
        if del_count > 0:
            print(f"  {msg('cleaned_count', config, count=del_count, mb=del_bytes / (1024*1024))}")

    if getattr(args, "clean", False):
        del_count, del_bytes = cleanup_storage(config, force_clean=True)
        print(msg("cache_cleaned", config, count=del_count, mb=del_bytes / (1024*1024)))

    print_storage_summary(config)

def cmd_lang(args, config):
    lang_code = getattr(args, "lang_name", None)
    if lang_code:
        clean = lang_code.strip().lower()
        if clean in ("en", "eng", "english"):
            config["language"] = "en"
            save_config(config)
            print(msg("lang_saved", config))
        elif clean in ("ru", "rus", "russian"):
            config["language"] = "ru"
            save_config(config)
            print(msg("lang_saved", config))
        else:
            print("Supported languages: 'en' (English), 'ru' (Russian).", file=sys.stderr)
            print("Examples:\n  omniwall lang en\n  omniwall lang ru", file=sys.stderr)
    else:
        print(msg("lang_current", config))
        print(msg("lang_usage", config))

# ----------------- PARSER & ENTRYPOINT -----------------

def build_parser(config=None):
    lang = get_lang(config)
    parser = argparse.ArgumentParser(
        prog="omniwall",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=msg("prog_desc", config),
        epilog=msg("epilog", config)
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute" if lang == "en" else "Команда для выполнения")

    # Command: next
    parser_next = subparsers.add_parser("next", help=msg("cmd_next_help", config))
    parser_next.add_argument("-t", "--tag", "-q", "--query", type=str, help=msg("tag_help", config))
    parser_next.add_argument("--reset-tag", action="store_true", help=msg("reset_tag_help", config))
    parser_next.add_argument("-r", "--ratio", type=str, help=msg("ratio_help", config))
    parser_next.add_argument("--res", "--resolution", dest="resolution", type=str, help=msg("res_help", config))
    parser_next.add_argument("-b", "--buffer", type=int, help=msg("buffer_help", config))
    parser_next.add_argument("-l", "--local", action="store_true", help=msg("local_help", config))
    parser_next.add_argument("-s", "--silent", action="store_true", help=msg("silent_help", config))

    # Command: limit
    parser_limit = subparsers.add_parser("limit", help=msg("cmd_limit_help", config))
    parser_limit.add_argument("size", nargs="?", type=str, help=msg("limit_size_help", config))

    # Command: tag
    parser_tag = subparsers.add_parser("tag", help=msg("cmd_tag_help", config))
    parser_tag.add_argument("tag_name", nargs="?", type=str, help=msg("tag_help", config))
    parser_tag.add_argument("-a", "--apply", action="store_true", help=msg("tag_apply_help", config))
    parser_tag.add_argument("--reset", action="store_true", help=msg("tag_reset_help", config))

    # Command: cache
    parser_cache = subparsers.add_parser("cache", help=msg("cmd_cache_help", config))
    parser_cache.add_argument("size", nargs="?", type=str, help=msg("limit_size_help", config))
    parser_cache.add_argument("--clean", action="store_true", help=msg("cache_clean_help", config))
    parser_cache.add_argument("--limit", "--max-mb", dest="limit", type=str, help=msg("cache_limit_help", config))
    parser_cache.add_argument("--max-files", type=int, help=msg("cache_files_help", config))

    # Command: schedule
    parser_sched = subparsers.add_parser("schedule", help=msg("cmd_schedule_help", config))
    parser_sched.add_argument("time", nargs="?", type=str, help=msg("schedule_time_help", config))

    # Command: buffer
    parser_buf = subparsers.add_parser("buffer", help=msg("cmd_buffer_help", config))
    parser_buf.add_argument("-b", "--buffer", type=int, help=msg("buffer_help", config))
    parser_buf.add_argument("--sync", action="store_true", help=msg("buffer_sync_help", config))
    parser_buf.add_argument("-t", "--tag", type=str, help=msg("tag_help", config))

    # Command: prev
    parser_prev = subparsers.add_parser("prev", help=msg("cmd_prev_help", config))
    parser_prev.add_argument("-s", "--silent", action="store_true", help=msg("silent_help", config))

    # Command: current
    subparsers.add_parser("current", help=msg("cmd_current_help", config))

    # Command: list
    parser_list = subparsers.add_parser("list", help=msg("cmd_list_help", config))
    parser_list.add_argument("-t", "--tag", "-q", "--query", type=str, help=msg("tag_help", config))

    # Command: lang
    parser_lang = subparsers.add_parser("lang", help=msg("cmd_lang_help", config))
    parser_lang.add_argument("lang_name", nargs="?", type=str, help=msg("lang_name_help", config))

    return parser

def main():
    config = load_config()
    parser = build_parser(config)

    if len(sys.argv) == 1:
        args = parser.parse_args(["next"])
    else:
        if sys.argv[1].startswith("-") and sys.argv[1] not in ("-h", "--help"):
            args = parser.parse_args(["next"] + sys.argv[1:])
        else:
            args = parser.parse_args()

    if args.command in (None, "next"):
        cmd_next(args, config)
    elif args.command in ("limit", "max-size", "storage-limit"):
        cmd_limit(args, config)
    elif args.command in ("tag", "set-tag"):
        cmd_tag(args, config)
    elif args.command in ("lang", "language"):
        cmd_lang(args, config)
    elif args.command in ("cache", "clean"):
        cmd_cache(args, config)
    elif args.command in ("schedule", "time", "timer"):
        cmd_schedule(args, config)
    elif args.command in ("buffer", "sync"):
        cmd_buffer(args, config)
    elif args.command in ("prev", "previous"):
        cmd_prev(args, config)
    elif args.command in ("current", "status", "info"):
        cmd_current(args, config)
    elif args.command in ("list", "ls"):
        cmd_list(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
