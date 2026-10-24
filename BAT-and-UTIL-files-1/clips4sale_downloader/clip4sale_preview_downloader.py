#!/usr/bin/env python3
"""Download public Clips4Sale previews, with deliberate folder selection and pacing.

Python 3.10+. See README.md for installation, examples, and site limitations.
"""
from __future__ import annotations

import argparse
import ctypes
import html
import io
import json
import math
import os
from pathlib import Path
import random
import re
import shutil
import signal
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import unicodedata
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from html.parser import HTMLParser
from typing import Any
from urllib.parse import parse_qsl, unquote, urlencode, urljoin, urlsplit, urlunsplit

CLAIRE_PARENT = Path(r"C:\new\p")
DEFAULT_DESTINATION = CLAIRE_PARENT / "clips4sale_previews"
# Keep this table easy to edit between sessions. Keys are matched anywhere in
# the normalized category name; values are filename prefixes.
CATEGORY_PREFIXES = {
    "small penis humiliation": "sph",
    "cuckolding": "cuck",
    "chastity": "ch",
}
VERSION = "0.9.0"
TEMP_PROFILE_ROOT = Path(tempfile.gettempdir()) / "clips4sale_downloader"
DEFAULT_DATABASE_NAME = "clips4sale.db"
APP_DATA_ROOT = Path(os.environ.get("APPDATA") or (Path.home() / "AppData" / "Roaming")) / "Clips4SaleDownloader"
DEFAULT_PROFILE_DIR = APP_DATA_ROOT / "browser-profile"
LEGACY_DEFAULT_PROFILE_DIR = TEMP_PROFILE_ROOT / "browser-profile"
HISTORY_ROOT = APP_DATA_ROOT / "history"
PRIVATE_DATABASE_PATH = HISTORY_ROOT / "clips4sale-downloads.db"
PRIVATE_REPORT_ROOT = HISTORY_ROOT / "reports"
DATABASE_BACKUP_ROOT = HISTORY_ROOT / "backups"
# Import earlier shared ledgers once so moving history to AppData does not
# forget already-downloaded clips. The old databases are read only.
LEGACY_TEMP_DATABASE_PATH = TEMP_PROFILE_ROOT / "history" / "clips4sale-downloads.db"
LEGACY_PRIVATE_DATA_ROOT = (Path(r"C:\BAT\private") if Path(r"C:\BAT\private").is_dir()
                            else Path(os.environ.get("APPDATA") or (Path.home() / "AppData" / "Roaming"))
                            / "Clips4SaleDownloader") / "clips4sale_downloader"
LEGACY_PRIVATE_DATABASE_PATH = LEGACY_PRIVATE_DATA_ROOT / "clips4sale-downloads.db"
LOG_DIRECTORY = Path(r"C:\logs\c4sdl")
DEFAULT_MEDIA_RETRIES = 1
RESCAN_KNOWN_STREAK = 5
PROFILE_FALLBACK_ROOT = ".browser-profile-runs"
PROFILE_SNAPSHOT_ROOT = ".browser-profile-snapshots"
PROFILE_SNAPSHOT_MARKER = ".c4sdl-login-copy.json"
# Chromium/Chrome versions use Singleton* markers, while the older downloader
# used a plain lockfile. Treat every one of them as busy before attempting a
# persistent launch; a second launcher must clone the login-bearing profile.
PROFILE_LOCK_NAMES = ("SingletonLock", "SingletonSocket", "SingletonCookie", "lockfile", "LOCK")
BROWSER_LAUNCH_TIMEOUT_MS = 30_000
PROFILE_CLONE_TIMEOUT_SECONDS = 30.0
PROFILE_DATABASE_TIMEOUT_SECONDS = 5.0
VIDEO_PAUSE_RANGE = (0.40, 4.20)
REUSED_VIDEO_PAUSE_RANGE = (1.00, 5.00)
FIVE_VIDEO_PAUSE_RANGE = (1.20, 7.30)
LONG_VIDEO_PAUSE_RANGE = (3.30, 13.70)
PROFILE_COPY_IGNORES = {
    "SingletonCookie", "SingletonLock", "SingletonSocket", "DevToolsActivePort",
    "LOCK", "lockfile", "Cache", "Code Cache", "GPUCache", "GrShaderCache",
    "ShaderCache", "Crashpad", "BrowserMetrics",
}
PROFILE_SQLITE_SIDECARS = ("-wal", "-shm", "-journal")
# Only these per-profile paths carry the settings/cookies/origin storage used
# for login. History, metrics databases, extensions, and component caches are
# deliberately not part of a concurrent downloader's startup.
PROFILE_LOGIN_PATHS = ("Preferences", "Secure Preferences", "Network/Cookies", "Cookies",
                       "Local Storage", "Session Storage", "IndexedDB")
CLIP_PATH = re.compile(r"/(?:[a-z]{2}/)?studio/(\d+)/(\d+)(?:/|$)")
QUALITY_TOKEN = r"(?:8k|4k|uhd|fhd|full\s*hd|hd|sd|\d{3,4}p|\d{3,4}\s*[x×]\s*\d{3,4}|mp4|wmv|mov|avi|webm)"
QUALITY_SUFFIX = re.compile(rf"(?:\s*[-_–—|,:]\s*|\s+|\s*[\[(]){QUALITY_TOKEN}[\])]?$", re.I)
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".m4v", ".wmv", ".avi", ".ogv"}
IMAGE_EXTENSIONS = {".gif", ".jpg", ".jpeg", ".png", ".webp", ".avif"}
EMOJI_RE = re.compile(r"[🌈📁📍✨📦✏❌⚠↩✅🧭🏷🎬🧪📥⏳🗃🧹♻🛟🔐🌐🔒🖥💾⚡🔁]\ufe0f?")


def terminal_text(text: str, stream=None) -> str:
    """Keep emoji on capable terminals while avoiding cp1252 crashes on older consoles."""
    stream = stream or sys.stdout
    encoding = getattr(stream, "encoding", None) or "utf-8"
    try:
        text.encode(encoding)
    except (LookupError, UnicodeEncodeError):
        return EMOJI_RE.sub("", text)
    return text


class DownloadError(RuntimeError):
    pass


class SiteBlocked(DownloadError):
    pass


def clean_title(title: str) -> str:
    title = unicodedata.normalize("NFKC", html.unescape(title)).strip()
    while True:
        shorter = QUALITY_SUFFIX.sub("", title).strip(" -_–—|,:")
        if shorter == title or not shorter:
            return title
        title = shorter


def title_key(title: str) -> str:
    return re.sub(r"\s+", " ", clean_title(title)).casefold()


def category_prefix(category: str) -> str:
    normalized = re.sub(r"\s+", " ", str(category or "")).strip().casefold()
    for name, prefix in CATEGORY_PREFIXES.items():
        if str(name).strip().casefold() in normalized:
            return safe_filename(str(prefix).strip())
    return ""


def clip_category_name(listing_category: str, raw: dict) -> str:
    """Use the primary/first clip category for every form of full-studio URL."""
    listing_key = re.sub(r"[\s_-]+", "", str(listing_category or "")).casefold()
    if listing_key not in {"", "all", "allcategories"}:
        return str(listing_category or "").strip()

    def name(value):
        if isinstance(value, dict):
            value = (value.get("name") or value.get("title") or value.get("category_name")
                     or value.get("category"))
        if not isinstance(value, str) or value.strip().isdigit():
            return ""
        return re.sub(r"\s+", " ", html.unescape(value).replace("-", " ")).strip().title()

    # The site's canonical primary field is category_name. Its
    # related_category_links are secondary categories, not the studio catalog.
    for key in ("primary_category", "primaryCategory", "category_name", "categoryName", "category"):
        found = name(raw.get(key))
        if found:
            return found
    primary_id = str(raw.get("primary_category_id") or raw.get("primaryCategoryId")
                     or raw.get("categoryId") or raw.get("category_id") or "")
    for key in ("categories", "category", "related_category_links"):
        values = raw.get(key)
        if not isinstance(values, list):
            continue
        primary = [value for value in values if isinstance(value, dict) and
                   (value.get("primary") is True or value.get("is_primary") is True
                    or value.get("isPrimary") is True
                    or (primary_id and str(value.get("id")) == primary_id))]
        for value in [*primary, *values]:
            found = name(value)
            if found:
                return found
    category_link = re.search(r"/Cat([1-9]\d*)-([^/]+)", str(raw.get("category_link") or ""), re.I)
    return name(unquote(category_link[2])) if category_link else "Uncategorized"


def quality_score(raw: dict) -> tuple[int, int, float]:
    text = " ".join(str(raw.get(k) or "") for k in
                    ("screen_size", "resolution", "resolution_text"))
    if not re.search(r"\d{3,4}p|\d+\s*[x×]\s*\d+|\b(?:8k|4k|uhd|fhd|hd|sd)\b", text, re.I):
        text = str(raw.get("title") or "")
    heights, areas = [], []
    for width, height in re.findall(r"(\d{3,5})\s*[x×]\s*(\d{3,5})", text, re.I):
        w, h = int(width), int(height)
        heights.append(min(w, h))
        areas.append(w * h)
    heights.extend(int(n) for n in re.findall(r"(?<!\d)(\d{3,4})p\b", text, re.I))
    for pattern, height in ((r"\b8k\b", 4320), (r"\b(?:4k|uhd)\b", 2160),
                            (r"\b(?:fhd|full\s*hd)\b", 1080), (r"\bhd\b", 720),
                            (r"\bsd\b", 480)):
        if re.search(pattern, text, re.I):
            heights.append(height)
    try:
        size = float(raw.get("size_mb") or raw.get("size") or 0)
    except (ValueError, TypeError):
        size = 0
    return max(heights, default=0), max(areas, default=0), size


def safe_filename(text: str) -> str:
    text = unicodedata.normalize("NFKC", html.unescape(text))
    text = re.sub(r'[<>:"/\\|?*\x00-\x1f\x7f]', "_", text)
    text = re.sub(r"\s+", " ", text).strip(" .") or "Untitled"
    if re.match(r"^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)", text, re.I):
        text = "_" + text
    return text


def collision_path(path: Path) -> Path:
    """Preserve existing items; suffix goes immediately before the final extension."""
    candidate, n = path, 1
    while candidate.exists():
        candidate = path.with_name(f"{path.stem} ({n}){path.suffix}")
        n += 1
    return candidate


def write_new_json(path: Path, data: Any) -> Path:
    while True:
        target = collision_path(path)
        try:
            with target.open("x", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write("\n")
            return target
        except FileExistsError:
            continue


def select_destination(requested: Path | None, input_fn=input) -> Path:
    """Require an explicit destination, including an interactive custom path."""
    choices = [Path.cwd().resolve()]
    claire_default = (os.environ.get("USERNAME", "").strip().casefold() == "claire"
                      and CLAIRE_PARENT.is_dir())
    # Keep the current folder as the first numbered choice for compatibility,
    # but make Claire's destination the Enter/default action for Claire.
    for folder in (DEFAULT_DESTINATION if claire_default else None, requested):
        if folder is not None:
            folder = folder.expanduser().resolve()
            if folder not in choices:
                choices.append(folder)
    default_note = (f" (press Enter for {DEFAULT_DESTINATION})" if claire_default
                    else " (press Enter is not a selection)")
    print(terminal_text(f"\n📁 Choose where this run will save files{default_note}:"))
    for i, folder in enumerate(choices, 1):
        badge = " ✨ create after you choose it" if not folder.exists() else ""
        if i == 1:
            label = "📍 current folder"
        elif folder == DEFAULT_DESTINATION:
            label = "🌈 Claire default"
        else:
            label = "📦 requested folder"
        print(terminal_text(f"  {i}. {label}: {folder}{badge}"))
    custom_number = len(choices) + 1
    print(terminal_text(f"  {custom_number}. ✏️  Enter another location"))
    print(terminal_text("  0. ❌ Cancel"))
    while True:
        try:
            answer = input_fn("Destination number or custom option: ").strip()
        except EOFError as exc:
            raise DownloadError("An interactive destination choice is required.") from exc
        if answer == "0":
            raise KeyboardInterrupt
        if not answer and claire_default:
            folder = DEFAULT_DESTINATION.expanduser().resolve()
            folder.mkdir(parents=True, exist_ok=True)
            print(terminal_text(f"✅ Saving this run to the Claire default: {folder}\n"))
            return folder
        if answer.casefold() in {"n", "new", "e", "custom"} or answer == str(custom_number):
            try:
                entered = input_fn("Enter the full destination path: ").strip().strip('"')
            except EOFError as exc:
                raise DownloadError("A custom destination path is required.") from exc
            if not entered:
                print(terminal_text("⚠️  A destination path is required."))
                continue
            folder = Path(os.path.expandvars(os.path.expanduser(entered))).resolve()
            if folder.exists() and not folder.is_dir():
                print(terminal_text(f"⚠️  That path is a file, not a folder: {folder}"))
                continue
            try:
                confirmed = input_fn(f"Use {folder}? Type YES to confirm: ").strip()
            except EOFError as exc:
                raise DownloadError("The custom destination was not confirmed.") from exc
            if confirmed.casefold() != "yes":
                print(terminal_text("↩️  Custom destination cancelled; choose again."))
                continue
            folder.mkdir(parents=True, exist_ok=True)
            if not folder.is_dir():
                raise DownloadError(f"Destination is not a directory: {folder}")
            print(terminal_text(f"✅ Saving this run to: {folder}\n"))
            return folder
        if answer.isdigit() and 1 <= int(answer) <= len(choices):
            folder = choices[int(answer) - 1]
            folder.mkdir(parents=True, exist_ok=True)
            if not folder.is_dir():
                raise DownloadError(f"Destination is not a directory: {folder}")
            print(terminal_text(f"✅ Saving this run to: {folder}\n"))
            return folder
        print(terminal_text("⚠️  Enter one of the displayed choices; Enter alone does not select a folder."))


@dataclass
class Clip:
    id: str
    studio_id: str
    url: str
    title: str
    raw: dict = field(default_factory=dict)

    @classmethod
    def from_raw(cls, raw: dict, base: str) -> Clip | None:
        link = raw.get("link") or raw.get("bannerLink") or raw.get("url")
        if not isinstance(link, str):
            return None
        url = urljoin(base, link)
        match = CLIP_PATH.search(urlsplit(url).path)
        if not match or not raw.get("title"):
            return None
        return cls(match[2], match[1], url, str(raw["title"]), raw)


def deduplicate(clips: list[Clip]) -> tuple[list[Clip], list[dict]]:
    groups: dict[tuple[str, str], list[Clip]] = {}
    for clip in clips:
        groups.setdefault((clip.studio_id, title_key(clip.title)), []).append(clip)
    chosen, duplicates = [], []
    for group in groups.values():
        ranked = sorted(group, key=lambda c: quality_score(c.raw), reverse=True)
        chosen.append(ranked[0])
        for discarded in ranked[1:]:
            duplicates.append({"kept": ranked[0].url, "skipped": discarded.url,
                               "title": clean_title(ranked[0].title),
                               "kept_quality": quality_score(ranked[0].raw),
                               "skipped_quality": quality_score(discarded.raw)})
    return chosen, duplicates


def dicts(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from dicts(child)


def hydration_from_html(source: str) -> dict:
    """Read the site's JSON assignment without executing arbitrary page JavaScript."""
    match = re.search(r"window\.__remixContext\s*=\s*", source)
    if not match:
        return {}
    try:
        return json.JSONDecoder().raw_decode(source[match.end():])[0]
    except (json.JSONDecodeError, TypeError):
        return {}


def listing_data(payload: dict, studio_id: str) -> dict:
    for obj in dicts(payload):
        if str(obj.get("studioId")) == studio_id and isinstance(obj.get("clips"), list):
            return obj
    return {}


def detail_data(payload: dict, clip_id: str) -> dict:
    for obj in dicts(payload):
        if str(obj.get("clipId", obj.get("id"))) == clip_id and obj.get("title"):
            return obj
    return {}


@dataclass(frozen=True)
class Media:
    url: str
    role: str
    alternate_urls: tuple[str, ...] = ()


@dataclass(frozen=True)
class ListingScope:
    key: str
    kind: str
    studio_id: str
    category_id: str | None = None
    category_slug: str = ""

    @property
    def description(self) -> str:
        if self.kind == "studio":
            return f"whole studio {self.studio_id}"
        name = self.category_slug.replace("-", " ").strip() or self.category_id or "unknown"
        return f"studio {self.studio_id} + category {name}"


def listing_scope(url: str) -> ListingScope:
    """Return a stable history identity independent of page/sort/limit options."""
    path = unquote(urlsplit(url).path)
    studio_match = re.search(r"/(?:[a-z]{2}/)?studio/(\d+)(?:/|$)", path, re.I)
    if not studio_match:
        raise DownloadError(f"Could not identify a studio in listing URL: {url}")
    studio_id = studio_match[1]
    category_match = re.search(r"/Cat(\d+)(?:-([^/]+))?", path, re.I)
    if not category_match or category_match[1] == "0":
        return ListingScope(f"studio:{studio_id}", "studio", studio_id)
    category_id = category_match[1]
    return ListingScope(f"studio:{studio_id}:category:{category_id}", "studio-category",
                        studio_id, category_id, category_match[2] or "")


def ask_rescan(scope: ListingScope, completed_at: str, studio: str = "", category: str = "",
               *, headless: bool = False, input_fn=input) -> bool:
    """Ask whether a completely downloaded cached scope should be checked for new clips."""
    completed_date = str(completed_at or "an earlier date")[:10]
    if scope.kind == "studio":
        subject = "This studio"
        detail = studio or f"Studio {scope.studio_id}"
    else:
        subject = "This studio/category"
        detail = " - ".join(part for part in (studio, category) if part) or scope.description
    message = (f"{subject} was completely downloaded as of {completed_date}.\n\n"
               f"{detail}\n\nDo you want to re-scan for new clips?")
    if os.name == "nt" and not headless:
        try:
            # A topmost Yes/No dialog remains visible when the terminal is
            # behind another window. No is the safe default button.
            flags = 0x00000004 | 0x00000020 | 0x00000100 | 0x00010000 | 0x00040000
            return ctypes.windll.user32.MessageBoxW(
                None, message, f"Clips4Sale downloader v{VERSION}", flags
            ) == 6  # IDYES
        except (AttributeError, OSError):
            pass
    if not getattr(sys.stdin, "isatty", lambda: False)() and input_fn is input:
        print(terminal_text(message + "\nUsing the saved scan in this non-interactive session."),
              file=sys.stderr, flush=True)
        return False
    print(terminal_text("\n" + message))
    print("  [1] Use the saved scan")
    print("  [2] Re-scan for new clips")
    try:
        return input_fn("Choose 1 or 2 [1]: ").strip() == "2"
    except EOFError:
        return False


def random_delay(low: float, high: float) -> float:
    """Return a two-decimal random delay, including the requested endpoints."""
    return round(random.uniform(low, high), 2)


class DownloadPacer:
    """Share non-repeating scheduled delays across one job's browser/downloads."""

    def __init__(self, panel: ProgressPanel, pump=None):
        self.panel = panel
        self.pump = pump
        self.video_downloads = 0
        self.next_long_pause = random.randint(17, 27)
        self.last_wait_ticks: int | None = None

    def choose_wait(self, seconds: float, bounds: tuple[float, float] | None = None) -> float:
        """Exclude the last positive wait at hundredth-of-a-second precision.

        Bounded pauses stay within their requested range. Fixed/minimum waits
        round upward and, only on a collision, gain 0.01–1.00s. A zero wait
        remains a no-op and does not erase the previous actual wait.
        """
        if seconds <= 0:
            return 0.0
        ticks = math.ceil(round(seconds * 100, 8))
        if bounds is not None:
            low = math.ceil(round(bounds[0] * 100, 8))
            high = math.floor(round(bounds[1] * 100, 8))
            if low <= 0 or high < low or not low <= ticks <= high:
                raise ValueError("Wait must fit its positive hundredth-second range")
        if ticks == self.last_wait_ticks:
            if bounds is None:
                ticks += random.randint(1, 100)
            else:
                if high == low:
                    raise ValueError("Wait range has no alternative to the previous delay")
                # Select from the remaining ticks directly: repeated RNG
                # results cannot cause an unbounded re-roll loop.
                ticks = low + random.randrange(high - low)
                if ticks >= self.last_wait_ticks:
                    ticks += 1
        self.last_wait_ticks = ticks
        return ticks / 100

    def pause(self, seconds: float, bounds: tuple[float, float] | None = None, on_scheduled=None):
        seconds = self.choose_wait(seconds, bounds)
        if on_scheduled is not None:
            on_scheduled(seconds)
        if seconds <= 0:
            return seconds
        self.panel.wait(seconds, self.pump)
        return seconds

    def browser_pause(self, page, seconds: float):
        seconds = self.choose_wait(seconds)
        if seconds > 0:
            page.wait_for_timeout(seconds * 1000)
        return seconds

    def video_downloaded(self):
        self.video_downloads += 1
        # Every video gets its own small, two-decimal pause.
        self.pause(random_delay(*VIDEO_PAUSE_RANGE), VIDEO_PAUSE_RANGE)
        # The five-video pause is independent; if both milestones coincide,
        # both requested pauses are honored in sequence.
        if self.video_downloads % 5 == 0:
            self.pause(random_delay(*FIVE_VIDEO_PAUSE_RANGE), FIVE_VIDEO_PAUSE_RANGE)
        if self.video_downloads >= self.next_long_pause:
            self.pause(random_delay(*LONG_VIDEO_PAUSE_RANGE), LONG_VIDEO_PAUSE_RANGE)
            self.next_long_pause = self.video_downloads + random.randint(17, 27)


class DownloadDatabase:
    """Small WAL-backed job ledger shared by runs using one destination.

    The clip id is the durable identity.  That is intentional: the same clip
    can be returned by two category listings, but it must still have one set of
    files in the destination.  Media rows additionally remember the source
    URL, so a completed item can be skipped without re-downloading it.
    """

    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(path), timeout=60, isolation_level=None)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA busy_timeout=60000")
        for attempt in range(10):
            try:
                self.connection.execute("PRAGMA journal_mode=WAL")
                break
            except sqlite3.OperationalError as exc:
                if "locked" not in str(exc).casefold() or attempt == 9:
                    raise
                time.sleep(0.05 * (attempt + 1))
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS clips (
                studio_id TEXT NOT NULL,
                clip_id TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                category TEXT,
                filename_base TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                updated_at TEXT NOT NULL,
                PRIMARY KEY (studio_id, clip_id)
            );
            CREATE TABLE IF NOT EXISTS media (
                studio_id TEXT NOT NULL,
                clip_id TEXT NOT NULL,
                role TEXT NOT NULL,
                url TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                path TEXT,
                bytes INTEGER,
                duration REAL,
                width INTEGER,
                height INTEGER,
                attempts INTEGER NOT NULL DEFAULT 0,
                owner_pid INTEGER,
                error TEXT,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (studio_id, clip_id, role, url),
                FOREIGN KEY (studio_id, clip_id)
                    REFERENCES clips(studio_id, clip_id)
            );
            CREATE INDEX IF NOT EXISTS media_status_idx
                ON media(studio_id, clip_id, status);
            CREATE INDEX IF NOT EXISTS media_url_role_idx
                ON media(role, url, status);
            CREATE TABLE IF NOT EXISTS discovery_cache (
                listing_url TEXT PRIMARY KEY,
                studio_id TEXT NOT NULL,
                studio TEXT NOT NULL,
                category TEXT,
                clips_json TEXT NOT NULL,
                discovered INTEGER NOT NULL,
                completed_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS run_history (
                run_id TEXT PRIMARY KEY,
                scope_key TEXT NOT NULL,
                scope_kind TEXT NOT NULL,
                studio_id TEXT NOT NULL,
                category_id TEXT,
                listing_url TEXT NOT NULL,
                studio TEXT,
                category TEXT,
                destination TEXT NOT NULL,
                status TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                discovered INTEGER,
                selected INTEGER,
                files INTEGER,
                errors INTEGER
            );
            CREATE INDEX IF NOT EXISTS run_history_scope_idx
                ON run_history(scope_key, started_at DESC);
            """
        )

    @staticmethod
    def _now() -> str:
        return datetime.now().isoformat(timespec="seconds")

    @staticmethod
    def _pid_alive(pid: int | None) -> bool:
        if not pid or pid <= 0:
            return False
        if os.name == "nt":
            # os.kill(pid, 0) is NOT a liveness check on Windows: zero is
            # CTRL_C_EVENT and can interrupt this process and its browser
            # driver. Query a process handle without sending any signal.
            from ctypes import wintypes
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
            kernel.OpenProcess.restype = wintypes.HANDLE
            kernel.WaitForSingleObject.argtypes = (wintypes.HANDLE, wintypes.DWORD)
            kernel.WaitForSingleObject.restype = wintypes.DWORD
            kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
            kernel.CloseHandle.restype = wintypes.BOOL
            handle = kernel.OpenProcess(0x00100000, False, pid)  # SYNCHRONIZE only
            if not handle:
                # Only a missing PID proves the owner is gone. Access denied
                # or an unexpected query error must not steal a live claim.
                return ctypes.get_last_error() != 87  # ERROR_INVALID_PARAMETER
            try:
                return kernel.WaitForSingleObject(handle, 0) != 0  # WAIT_OBJECT_0 = exited
            finally:
                kernel.CloseHandle(handle)
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except OSError:
            # PermissionError still means a process may own the download.
            return True
        return True

    def set_metadata(self, **values: Any):
        for key, value in values.items():
            self.connection.execute(
                "INSERT INTO metadata(key, value) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, json.dumps(value, ensure_ascii=False)),
            )

    def metadata(self, key: str) -> Any:
        row = self.connection.execute("SELECT value FROM metadata WHERE key=?", (key,)).fetchone()
        if not row:
            return None
        try:
            return json.loads(row["value"])
        except json.JSONDecodeError:
            return row["value"]

    def previous_scope_activity(self, scope: ListingScope) -> dict | None:
        """Find the latest run, or an older listing cache from before run history existed."""
        row = self.connection.execute(
            "SELECT * FROM run_history WHERE scope_key=? ORDER BY started_at DESC LIMIT 1",
            (scope.key,),
        ).fetchone()
        if row:
            return dict(row)
        # Version 0.6 cached listings but did not append run records. Recover
        # that evidence so the first 0.7 run still gives a useful reminder.
        rows = self.connection.execute(
            "SELECT * FROM discovery_cache WHERE studio_id=? ORDER BY completed_at DESC",
            (scope.studio_id,),
        ).fetchall()
        for cached in rows:
            try:
                cached_scope = listing_scope(cached["listing_url"])
            except DownloadError:
                continue
            if cached_scope.key == scope.key:
                return {
                    "scope_key": scope.key,
                    "scope_kind": scope.kind,
                    "studio_id": scope.studio_id,
                    "category_id": scope.category_id,
                    "listing_url": cached["listing_url"],
                    "studio": cached["studio"],
                    "category": cached["category"],
                    "destination": None,
                    "status": "listing-cached",
                    "started_at": cached["completed_at"],
                    "finished_at": cached["completed_at"],
                    "discovered": cached["discovered"],
                    "selected": None,
                    "files": None,
                    "errors": None,
                }
        return None

    def completed_scope_activity(self, scope: ListingScope) -> dict | None:
        """Return the latest error-free completed run for the requested scope."""
        row = self.connection.execute(
            "SELECT * FROM run_history WHERE scope_key=? AND status='complete' "
            "ORDER BY finished_at DESC LIMIT 1",
            (scope.key,),
        ).fetchone()
        return dict(row) if row else None

    def successful_still_media(self) -> list[dict]:
        """Return saved still-image rows used to identify obsolete variants."""
        rows = self.connection.execute(
            """SELECT studio_id, clip_id, role, url, path, bytes, width, height, updated_at
               FROM media
               WHERE status='success' AND path IS NOT NULL
                 AND (role='thumbnail' OR role='image' OR role LIKE 'image-%')
               ORDER BY studio_id, clip_id, updated_at"""
        ).fetchall()
        return [dict(row) for row in rows]

    def mark_media_recycled(self, row: dict):
        """Record a user-approved Recycle Bin cleanup without erasing history."""
        self.connection.execute(
            """UPDATE media SET status='recycled-old-variant', owner_pid=NULL,
                      error='Recycled after higher-quality same-image variant was retained',
                      updated_at=?
               WHERE studio_id=? AND clip_id=? AND role=? AND url=?""",
            (self._now(), row["studio_id"], row["clip_id"], row["role"], row["url"]),
        )

    def start_scope_run(self, scope: ListingScope, listing_url: str, destination: Path) -> str:
        """Append a run record; prior history is never overwritten."""
        run_id = uuid.uuid4().hex
        self.connection.execute(
            """INSERT INTO run_history(
                   run_id, scope_key, scope_kind, studio_id, category_id,
                   listing_url, destination, status, started_at
               ) VALUES(?, ?, ?, ?, ?, ?, ?, 'running', ?)""",
            (run_id, scope.key, scope.kind, scope.studio_id, scope.category_id,
             listing_url, str(destination), self._now()),
        )
        return run_id

    def finish_scope_run(self, run_id: str, report: dict):
        """Complete the current append-only history row with its final summary."""
        clips = report.get("clips") or []
        files = sum(len(item.get("files") or []) for item in clips)
        errors = sum(len(item.get("errors") or []) for item in clips) + len(report.get("errors") or [])
        if report.get("dry_run") and report.get("completed"):
            status = "planned-with-errors" if errors else "planned"
        elif report.get("completed"):
            status = "complete-with-errors" if errors else "complete"
        else:
            status = "interrupted" if any("Interrupt" in str(error) for error in report.get("errors") or []) else "failed"
        self.connection.execute(
            """UPDATE run_history SET status=?, finished_at=?, studio=?, category=?,
                   discovered=?, selected=?, files=?, errors=? WHERE run_id=?""",
            (status, self._now(), report.get("studio"), report.get("category"),
             report.get("discovered"), report.get("selected"), files, errors, run_id),
        )

    def merge_legacy(self, source: Path):
        """Import an older destination ledger into the private shared ledger."""
        source = source.expanduser().resolve()
        if source == self.path.resolve() or not source.is_file():
            return 0
        try:
            stat = source.stat()
            signature = f"{stat.st_size}:{stat.st_mtime_ns}"
        except OSError:
            return 0
        marker_key = f"legacy-import::{source}"
        marker = self.metadata(marker_key)
        if marker == signature:
            return 0
        uri = source.as_uri() + "?mode=ro"
        imported = 0
        legacy = sqlite3.connect(uri, uri=True, timeout=5)
        legacy.row_factory = sqlite3.Row
        try:
            tables = {row[0] for row in legacy.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            if "metadata" in tables:
                for row in legacy.execute("SELECT key, value FROM metadata"):
                    self.connection.execute("INSERT OR IGNORE INTO metadata(key, value) VALUES(?, ?)",
                                            (row["key"], row["value"]))
                    imported += 1
            if "discovery_cache" in tables:
                columns = ("listing_url", "studio_id", "studio", "category", "clips_json",
                           "discovered", "completed_at")
                for row in legacy.execute(f"SELECT {', '.join(columns)} FROM discovery_cache"):
                    self.connection.execute(
                        f"INSERT OR IGNORE INTO discovery_cache({', '.join(columns)}) VALUES({', '.join('?' for _ in columns)})",
                        tuple(row[column] for column in columns))
                    imported += 1
            if "run_history" in tables:
                columns = ("run_id", "scope_key", "scope_kind", "studio_id", "category_id",
                           "listing_url", "studio", "category", "destination", "status",
                           "started_at", "finished_at", "discovered", "selected", "files", "errors")
                for row in legacy.execute(f"SELECT {', '.join(columns)} FROM run_history"):
                    self.connection.execute(
                        f"INSERT OR IGNORE INTO run_history({', '.join(columns)}) VALUES({', '.join('?' for _ in columns)})",
                        tuple(row[column] for column in columns))
                    imported += 1
            if "clips" in tables:
                columns = ("studio_id", "clip_id", "title", "url", "category", "filename_base",
                           "status", "updated_at")
                for row in legacy.execute(f"SELECT {', '.join(columns)} FROM clips"):
                    values = tuple(row[column] for column in columns)
                    self.connection.execute(
                        f"INSERT OR IGNORE INTO clips({', '.join(columns)}) VALUES({', '.join('?' for _ in columns)})",
                        values)
                    if row["status"] == "complete":
                        self.connection.execute(
                            "UPDATE clips SET status='complete', updated_at=? "
                            "WHERE studio_id=? AND clip_id=? AND status!='complete'",
                            (row["updated_at"], row["studio_id"], row["clip_id"]))
                    imported += 1
            if "media" in tables:
                columns = ("studio_id", "clip_id", "role", "url", "status", "path", "bytes",
                           "duration", "width", "height", "attempts", "owner_pid", "error", "updated_at")
                for row in legacy.execute(f"SELECT {', '.join(columns)} FROM media"):
                    values = tuple(row[column] for column in columns)
                    self.connection.execute(
                        f"INSERT OR IGNORE INTO media({', '.join(columns)}) VALUES({', '.join('?' for _ in columns)})",
                        values)
                    if row["status"] == "success":
                        self.connection.execute(
                            """UPDATE media SET status='success', path=?, bytes=?, duration=?, width=?, height=?,
                               attempts=?, owner_pid=NULL, error=NULL, updated_at=?
                               WHERE studio_id=? AND clip_id=? AND role=? AND url=? AND status!='success'""",
                            (row["path"], row["bytes"], row["duration"], row["width"], row["height"],
                             row["attempts"], row["updated_at"], row["studio_id"], row["clip_id"],
                             row["role"], row["url"]))
                    imported += 1
        finally:
            legacy.close()
        # A destination-local database can be very large.  Remember the exact
        # source revision after a successful import so subsequent starts do
        # not scan and merge the same rows again.
        self.connection.execute(
            "INSERT INTO metadata(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (marker_key, json.dumps(signature)),
        )
        return imported

    def store_discovery(self, listing_url: str, clips: list[Clip], studio: str, category: str,
                        scroll_steps: int | None = None):
        """Persist a stable listing and the depth needed to reach its boundary."""
        self.connection.execute(
            """INSERT INTO discovery_cache(listing_url, studio_id, studio, category,
                                             clips_json, discovered, completed_at)
               VALUES(?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(listing_url) DO UPDATE SET
                   studio_id=excluded.studio_id, studio=excluded.studio,
                   category=excluded.category, clips_json=excluded.clips_json,
                   discovered=excluded.discovered, completed_at=excluded.completed_at""",
            (listing_url, clips[0].studio_id if clips else "", studio, category or None,
             json.dumps([clip.raw for clip in clips], ensure_ascii=False), len(clips), self._now()),
        )
        if scroll_steps is not None:
            self.set_metadata(**{f"discovery-scroll-steps::{listing_url}": int(scroll_steps)})

    def discovery_cache_info(self, listing_url: str) -> dict | None:
        row = self.connection.execute(
            "SELECT studio_id, studio, category, discovered, completed_at "
            "FROM discovery_cache WHERE listing_url=?",
            (listing_url,),
        ).fetchone()
        if not row:
            return None
        info = dict(row)
        info["scroll_steps"] = self.metadata(f"discovery-scroll-steps::{listing_url}")
        return info

    def cached_discovery(self, listing_url: str) -> tuple[list[Clip], str, str] | None:
        row = self.connection.execute(
            "SELECT studio, category, clips_json FROM discovery_cache WHERE listing_url=?",
            (listing_url,),
        ).fetchone()
        if not row:
            return None
        try:
            raws = json.loads(row["clips_json"])
            clips = [clip for raw in raws if (clip := Clip.from_raw(raw, listing_url))]
        except (TypeError, json.JSONDecodeError):
            return None
        if not clips:
            return None
        return clips, str(row["studio"] or ""), str(row["category"] or "")

    def completed_media(self, clip: Clip) -> list[dict]:
        """Return a complete clip's saved rows, or empty if any file is absent."""
        clip_row = self.connection.execute(
            "SELECT status FROM clips WHERE studio_id=? AND clip_id=?",
            (clip.studio_id, clip.id),
        ).fetchone()
        if not clip_row or clip_row["status"] != "complete":
            return []
        rows = self.connection.execute(
            "SELECT * FROM media WHERE studio_id=? AND clip_id=? AND status='success' "
            "ORDER BY role, updated_at", (clip.studio_id, clip.id),
        ).fetchall()
        saved = []
        for row in rows:
            if not row["path"] or not Path(row["path"]).is_file():
                return []
            item = {"path": row["path"], "role": row["role"], "bytes": row["bytes"]}
            for key in ("duration", "width", "height"):
                if row[key] is not None:
                    item[key] = row[key]
            saved.append(item)
        return saved

    def upsert_clip(self, clip: Clip, category: str = "", filename_base: str = ""):
        now = self._now()
        self.connection.execute(
            """INSERT INTO clips(studio_id, clip_id, title, url, category, filename_base, status, updated_at)
               VALUES(?, ?, ?, ?, ?, ?, 'pending', ?)
               ON CONFLICT(studio_id, clip_id) DO UPDATE SET
                   title=excluded.title, url=excluded.url,
                   category=COALESCE(excluded.category, clips.category),
                   filename_base=COALESCE(excluded.filename_base, clips.filename_base),
                   updated_at=excluded.updated_at""",
            (clip.studio_id, clip.id, clip.title, clip.url, category or None,
             filename_base or None, now),
        )

    def claim_media(self, clip: Clip, media: Media, expected_path: Path) -> bool:
        """Atomically reserve a media item for this process.

        A second concurrent downloader sees ``processing`` and skips the item.
        The same URL is also shared across duplicate clip records, so a media
        file cannot be downloaded twice merely because the site exposed it
        under two clip identities. A crashed process can be reclaimed because
        its PID is no longer alive.
        """
        now = self._now()
        with self.connection:
            # Serialize the read-and-claim decision across processes. Without
            # an immediate write transaction, two runs could both observe a
            # missing URL owner before either inserts its processing row.
            self.connection.execute("BEGIN IMMEDIATE")
            rows = self.connection.execute(
                "SELECT * FROM media "
                "WHERE (studio_id=? AND clip_id=? AND role=?) OR url=? "
                "ORDER BY CASE status WHEN 'success' THEN 0 WHEN 'processing' THEN 1 ELSE 2 END, updated_at DESC",
                (clip.studio_id, clip.id, media.role, media.url),
            ).fetchall()

            def link_success(row):
                # Store an alias row for this clip so finish_clip() and future
                # resume runs can resolve the shared file through this clip's
                # own URL key without downloading it again.
                self.connection.execute(
                    """INSERT INTO media(studio_id, clip_id, role, url, status, path,
                                          bytes, duration, width, height, attempts,
                                          owner_pid, error, updated_at)
                       VALUES(?, ?, ?, ?, 'success', ?, ?, ?, ?, ?, ?, NULL, NULL, ?)
                       ON CONFLICT(studio_id, clip_id, role, url) DO UPDATE SET
                           status='success', path=excluded.path, bytes=excluded.bytes,
                           duration=excluded.duration, width=excluded.width,
                           height=excluded.height, owner_pid=NULL, error=NULL,
                           updated_at=excluded.updated_at""",
                    (clip.studio_id, clip.id, media.role, media.url, row["path"],
                     row["bytes"], row["duration"], row["width"], row["height"],
                     row["attempts"] or 0, now),
                )

            for row in rows:
                if row["status"] == "success" and row["path"]:
                    try:
                        valid = Path(row["path"]).is_file()
                    except OSError:
                        valid = False
                    if valid:
                        if (row["studio_id"], row["clip_id"], row["role"], row["url"]) != (
                                clip.studio_id, clip.id, media.role, media.url):
                            link_success(row)
                        return False
                if row["status"] == "processing" and self._pid_alive(row["owner_pid"]):
                    return False

            # A file from an earlier run may predate the database, or the
            # process may have published it just before its DB transaction.
            # Adopt that exact deterministic path instead of creating a
            # collision-suffixed duplicate.
            existing = expected_path if expected_path.is_file() else None
            if existing is None and expected_path.suffix == ".media":
                candidates = [path for path in expected_path.parent.glob(expected_path.stem + ".*")
                              if path.suffix not in {".media", ".part"} and path.is_file()]
                existing = candidates[0] if len(candidates) == 1 else None
            if existing is not None:
                self.connection.execute(
                    """INSERT INTO media(studio_id, clip_id, role, url, status, path,
                                          bytes, attempts, owner_pid, error, updated_at)
                       VALUES(?, ?, ?, ?, 'success', ?, ?, 0, NULL, NULL, ?)
                       ON CONFLICT(studio_id, clip_id, role, url) DO UPDATE SET
                           status='success', path=excluded.path, bytes=excluded.bytes,
                           owner_pid=NULL, error=NULL, updated_at=excluded.updated_at""",
                    (clip.studio_id, clip.id, media.role, media.url, str(existing),
                     existing.stat().st_size, now),
                )
                return False

            self.connection.execute(
                """INSERT INTO media(studio_id, clip_id, role, url, status, path, attempts,
                                      owner_pid, error, updated_at)
                   VALUES(?, ?, ?, ?, 'processing', ?, 1, ?, NULL, ?)
                   ON CONFLICT(studio_id, clip_id, role, url) DO UPDATE SET
                       status='processing', path=NULL, owner_pid=excluded.owner_pid,
                       attempts=media.attempts + 1, error=NULL, updated_at=excluded.updated_at""",
                (clip.studio_id, clip.id, media.role, media.url, str(expected_path), os.getpid(), now),
            )
        return True

    def record_success(self, clip: Clip, media: Media, saved: dict):
        self.connection.execute(
            """UPDATE media SET status='success', path=?, bytes=?, duration=?, width=?, height=?,
                               owner_pid=NULL, error=NULL, updated_at=?
               WHERE studio_id=? AND clip_id=? AND role=? AND url=?""",
            (saved["path"], saved.get("bytes"), saved.get("duration"), saved.get("width"),
             saved.get("height"), self._now(), clip.studio_id, clip.id, media.role, media.url),
        )

    def record_failure(self, clip: Clip, media: Media, error: str, *, retrying: bool = False):
        """Persist an error before logging; retain ownership throughout a retry."""
        with self.connection:
            self.connection.execute("BEGIN IMMEDIATE")
            self.connection.execute(
                """UPDATE media SET status=?, owner_pid=?, error=?, updated_at=?,
                                    attempts=attempts + ?
                   WHERE studio_id=? AND clip_id=? AND role=? AND url=?""",
                ("processing" if retrying else "failed", os.getpid() if retrying else None,
                 error, self._now(), int(retrying), clip.studio_id, clip.id, media.role, media.url),
            )
            # finish_clip() restores 'complete' if the retry recovers. Until
            # then even an interruption during console output retains failure
            # history and puts this clip behind unattempted clips next time.
            self.mark_clip_failed(clip, error)

    def successful_media(self, clip: Clip, media: Media) -> dict | None:
        row = self.connection.execute(
            "SELECT * FROM media WHERE studio_id=? AND clip_id=? AND role=? AND url=?",
            (clip.studio_id, clip.id, media.role, media.url),
        ).fetchone()
        if not row or row["status"] != "success" or not row["path"]:
            return None
        path = Path(row["path"])
        if not path.is_file():
            return None
        return {key: row[key] for key in row.keys() if row[key] is not None}

    def successful_media_for_role(self, clip: Clip, role: str) -> dict | None:
        row = self.connection.execute(
            "SELECT * FROM media WHERE studio_id=? AND clip_id=? AND role=? AND status='success' "
            "ORDER BY updated_at DESC LIMIT 1", (clip.studio_id, clip.id, role)
        ).fetchone()
        if not row or not row["path"] or not Path(row["path"]).is_file():
            return None
        return {key: row[key] for key in row.keys() if row[key] is not None}

    def mark_clip_failed(self, clip: Clip, error: str):
        self.connection.execute(
            "UPDATE clips SET status='failed', updated_at=? WHERE studio_id=? AND clip_id=?",
            (self._now(), clip.studio_id, clip.id),
        )

    def finish_clip(self, clip: Clip, assets: list[Media]) -> bool:
        if not assets:
            return False
        complete = all(self.successful_media_for_role(clip, media.role) for media in assets)
        self.connection.execute(
            "UPDATE clips SET status=?, updated_at=? WHERE studio_id=? AND clip_id=?",
            ("complete" if complete else "failed", self._now(), clip.studio_id, clip.id),
        )
        return complete

    def failed_clip_ids(self) -> set[tuple[str, str]]:
        rows = self.connection.execute(
            "SELECT studio_id, clip_id FROM clips WHERE status='failed' "
            "UNION SELECT m.studio_id, m.clip_id FROM media m "
            "LEFT JOIN clips c ON c.studio_id=m.studio_id AND c.clip_id=m.clip_id "
            "WHERE m.status='failed' AND COALESCE(c.status, 'failed') <> 'complete'"
        ).fetchall()
        failed = {(str(row["studio_id"]), str(row["clip_id"])) for row in rows}
        # Older releases could exit before recording a failure, leaving only
        # a processing row. Recover that history without touching live owners.
        interrupted = self.connection.execute(
            "SELECT m.studio_id, m.clip_id, m.owner_pid FROM media m "
            "LEFT JOIN clips c ON c.studio_id=m.studio_id AND c.clip_id=m.clip_id "
            "WHERE m.status='processing' AND COALESCE(c.status, 'pending') <> 'complete'"
        ).fetchall()
        owners = {}
        for row in interrupted:
            pid = row["owner_pid"]
            if pid not in owners:
                owners[pid] = self._pid_alive(pid)
            if not owners[pid]:
                failed.add((str(row["studio_id"]), str(row["clip_id"])))
        return failed

    def close(self):
        self.connection.close()


def media_from_raw(raw: dict, base: str) -> list[Media]:
    """Only inspect the selected clip record, never recommendation records."""
    found: list[Media] = []
    seen: set[str] = set()

    def add(value: Any, role: str):
        if not isinstance(value, str) or not value:
            return
        url = urljoin(base, html.unescape(value))
        parts = urlsplit(url)
        if parts.scheme not in ("http", "https") or url in seen:
            return
        ext = Path(unquote(parts.path)).suffix.lower()
        if ext not in VIDEO_EXTENSIONS | IMAGE_EXTENSIONS:
            return
        if role == "preview" and ext not in VIDEO_EXTENSIONS:
            role = "preview-gif" if ext == ".gif" else "image"
        seen.add(url)
        found.append(Media(url, role))

    for key in ("customPreviewUrl", "cdn_preview_link"):
        add(raw.get(key), "preview")
    for key in ("previewUrl", "gifPreviewUrl"):
        add(raw.get(key), "preview-gif")
    add(raw.get("cdn_previewlg_link"), "thumbnail")
    add(raw.get("previewLink"), "thumbnail" if not any(m.role == "thumbnail" for m in found) else "image")
    for obj in dicts(raw.get("thumbs", {})):
        for value in obj.values():
            add(value, "image")
    for key in ("srcSet", "responsiveSrcset"):
        value = raw.get(key)
        values = [value] if isinstance(value, str) else [v for obj in dicts(value) for v in obj.values()]
        for text in values:
            if isinstance(text, str):
                for entry in text.split(","):
                    add(entry.strip().split(" ")[0], "image")
    # Clip descriptions sometimes contain additional stills or animations.
    class Images(HTMLParser):
        def handle_starttag(self, tag, attrs):
            a = dict(attrs)
            if tag in ("img", "source", "video"):
                value = a.get("src", a.get("data-src", ""))
                ext = Path(urlsplit(value).path).suffix.lower()
                add(value, "preview-gif" if ext in VIDEO_EXTENSIONS | {".gif"} else "image")
    Images().feed(str(raw.get("description_sanitized") or raw.get("description") or ""))
    return found


def _media_extension(media: Media) -> str:
    return Path(unquote(urlsplit(media.url).path)).suffix.lower()


_STILL_VARIANT_PREFIX = re.compile(
    r"^(?:previewlg|thumb|square_(?:sm|md|lrg|ex_lrg)|rect_(?:sm|md|lrg|ex_lrg))_(.+)$",
    re.I,
)
_RESIZE_QUERY_KEYS = {
    "crop", "dpr", "fit", "h", "height", "q", "quality", "resize", "size", "w", "width",
}


def _still_image_family(media: Media) -> str:
    """Collapse C4S crop/size variants while retaining genuinely different images."""
    parts = urlsplit(media.url)
    path = unquote(parts.path)
    filename = Path(path).name
    known = _STILL_VARIANT_PREFIX.match(filename)
    if known:
        filename = known[1]
    else:
        stem, suffix = os.path.splitext(filename)
        # Common srcset/CDN forms for the same underlying image.
        # A bare numeric suffix can identify a different image, so only strip
        # explicit width/dimension markers here.
        stem = re.sub(r"(?:[-_.](?:w\d{2,5}|\d{2,5}x\d{2,5})|@\d+x)$", "", stem, flags=re.I)
        filename = stem + suffix
    normalized_path = str(Path(path).with_name(filename)).replace("\\", "/")
    query = urlencode([(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True)
                       if key.casefold() not in _RESIZE_QUERY_KEYS])
    return urlunsplit((parts.scheme.casefold(), parts.netloc.casefold(), normalized_path, query, ""))


def _image_quality(media: Media, position: int) -> tuple[int, int, int, int]:
    """Rank variants inside one still-image family without downloading all of them."""
    text = unquote(media.url).casefold()
    dimensions = [(int(w), int(h)) for w, h in re.findall(r"(\d{3,5})[x×](\d{3,5})", text)]
    area = max((w * h for w, h in dimensions), default=0)
    # Clips4Sale currently exposes these in descending useful resolution.
    # previewlg is the uncropped 720px image in observed listings; the rect
    # variants follow, while square variants are intentional crops.
    named_quality = 50
    for token, score in (
        ("original", 120), ("previewlg_", 110), ("full", 105),
        ("rect_ex_lrg_", 100), ("rect_lrg_", 90), ("rect_md_", 80),
        ("rect_sm_", 70), ("thumb_", 60), ("square_md_", 40), ("square_sm_", 30),
    ):
        if token in text:
            named_quality = score
            break
    if "@2x" in text or re.search(r"(?:^|[-_.])2x(?:[-_.]|$)", text):
        named_quality += 5
    # Explicit site variant, then measured/encoded area, then semantic role,
    # then discovery order keeps the result deterministic.
    return named_quality, area, int(media.role == "thumbnail"), -position


def _animation_family(media: Media) -> str:
    """Group alternate formats and explicit sizes of the same animation."""
    parts = urlsplit(media.url)
    path = unquote(parts.path)
    stem = os.path.splitext(Path(path).name)[0]
    stem = re.sub(
        r"(?:[-_.](?:w\d{2,5}|\d{2,5}x\d{2,5}|\d{3,4}p|sm|md|lg|lrg|xl|2x)|@\d+x)$",
        "", stem, flags=re.I,
    )
    normalized_path = str(Path(path).with_name(stem)).replace("\\", "/")
    query = urlencode([(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True)
                       if key.casefold() not in _RESIZE_QUERY_KEYS])
    return urlunsplit((parts.scheme.casefold(), parts.netloc.casefold(), normalized_path, query, ""))


def _animation_quality(media: Media, position: int) -> tuple[int, int, int, int]:
    text = unquote(media.url).casefold()
    dimensions = [(int(w), int(h)) for w, h in re.findall(r"(\d{3,5})[x×](\d{3,5})", text)]
    area = max((w * h for w, h in dimensions), default=0)
    vertical = max((int(value) for value in re.findall(r"(?:^|[-_.])(\d{3,4})p(?:[-_.]|$)", text)),
                   default=0)
    # Preserve the established GIF preference when no quality signal differs.
    format_preference = int(_media_extension(media) == ".gif")
    return area, vertical, format_preference, -position


def media_for_download(assets: list[Media]) -> list[Media]:
    """Keep each distinct still/animation, but only its best exposed variant."""
    videos = [m for m in assets if m.role == "preview" and _media_extension(m) in VIDEO_EXTENSIONS]
    gif_family = [m for m in assets if m.role == "preview-gif"
                  and _media_extension(m) in (VIDEO_EXTENSIONS | {".gif"})]
    stills = [m for m in assets if m.role in {"image", "thumbnail"}
              and _media_extension(m) in IMAGE_EXTENSIONS]
    selected: list[Media] = []
    if videos:
        # Preserve the site's primary preview preference while still being
        # deterministic if several player fields are exposed.
        selected.append(videos[0])
    if gif_family:
        animation_families: dict[str, list[tuple[int, Media]]] = {}
        for position, media in enumerate(gif_family):
            animation_families.setdefault(_animation_family(media), []).append((position, media))
        for number, family in enumerate(animation_families.values(), 1):
            ranked = sorted(family, key=lambda pair: _animation_quality(pair[1], pair[0]), reverse=True)
            best = ranked[0][1]
            alternates = tuple(item.url for _, item in ranked[1:] if item.url != best.url)
            role = "preview-gif" if number == 1 else f"preview-gif-{number}"
            selected.append(Media(best.url, role, alternates))
    if stills:
        families: dict[str, list[tuple[int, Media]]] = {}
        for position, media in enumerate(stills):
            families.setdefault(_still_image_family(media), []).append((position, media))
        image_number = 1
        thumbnail_used = False
        for family in families.values():
            ranked = sorted(family, key=lambda pair: _image_quality(pair[1], pair[0]), reverse=True)
            best = ranked[0][1]
            alternates = tuple(item.url for _, item in ranked[1:] if item.url != best.url)
            if not thumbnail_used and any(item.role == "thumbnail" for _, item in family):
                role = "thumbnail"
                thumbnail_used = True
            else:
                role = f"image-{image_number}"
                image_number += 1
            selected.append(Media(best.url, role, alternates))
    # URL-level de-duplication also covers a site that exposes the same file
    # once as a thumbnail and once through a responsive image field.
    unique: list[Media] = []
    seen: set[str] = set()
    for media in selected:
        if media.url not in seen:
            unique.append(media)
            seen.add(media.url)
    return unique


def old_variant_cleanup_plan(ledger: DownloadDatabase, output: Path) -> list[dict]:
    """Find lower-quality saved stills that belong to the same site image family.

    Separate source images remain separate groups. GIF/video animations are not
    queried, so the cleanup can never mistake an animation for a still variant.
    """
    output = output.expanduser().resolve()
    families: dict[tuple[str, str, str], dict[str, dict]] = {}
    for row in ledger.successful_still_media():
        path = Path(str(row.get("path") or "")).expanduser()
        try:
            resolved = path.resolve()
        except OSError:
            continue
        if not resolved.is_file() or resolved.parent != output:
            continue
        extension = resolved.suffix.casefold()
        if extension not in IMAGE_EXTENSIONS or extension == ".gif":
            continue
        media = Media(str(row.get("url") or ""), str(row.get("role") or "image"))
        family = _still_image_family(media)
        key = (str(row["studio_id"]), str(row["clip_id"]), family)
        candidate = dict(row)
        candidate["path"] = str(resolved)
        candidate["quality"] = (*_image_quality(media, 0), resolved.stat().st_size)
        # A legacy ledger can mention one physical file more than once. Treat
        # the file as one candidate so it can never be recycled as its own duplicate.
        existing = families.setdefault(key, {}).get(str(resolved).casefold())
        if not existing or candidate["quality"] > existing["quality"]:
            families[key][str(resolved).casefold()] = candidate

    plan = []
    for key, paths in families.items():
        candidates = list(paths.values())
        if len(candidates) < 2:
            continue
        ranked = sorted(candidates, key=lambda item: item["quality"], reverse=True)
        plan.append({
            "studio_id": key[0],
            "clip_id": key[1],
            "family": key[2],
            "keep": ranked[0],
            "recycle": ranked[1:],
        })
    return sorted(plan, key=lambda item: (item["studio_id"], item["clip_id"], item["family"]))


def clean_old_variants(ledger: DownloadDatabase, output: Path, *, input_fn=input) -> dict:
    """Preview and optionally recycle lower-resolution copies of the same still."""
    plan = old_variant_cleanup_plan(ledger, output)
    files = [row for group in plan for row in group["recycle"]]
    result = {"groups": len(plan), "candidates": len(files), "recycled": [], "errors": []}
    if not files:
        print(terminal_text("🧹 Old-image cleanup: no redundant saved variants were found."))
        return result

    print(terminal_text(f"\n🧹 Old-image cleanup preview: {len(files)} lower-quality files in "
                        f"{len(plan)} same-image groups:"))
    for group in plan:
        print(terminal_text(f"  🎬 Clip {group['clip_id']} — keep: {Path(group['keep']['path']).name}"))
        for row in group["recycle"]:
            print(terminal_text(f"     ♻️ recycle: {Path(row['path']).name}"))
    if not getattr(sys.stdin, "isatty", lambda: False)() and input_fn is input:
        print(terminal_text("Preview only: interactive confirmation is required to use the Recycle Bin."))
        result["preview_only"] = True
        return result
    print("  [1] Leave every file in place")
    print("  [2] Send only the listed lower-quality variants to the Recycle Bin")
    try:
        approved = input_fn("Choose 1 or 2 [1]: ").strip() == "2"
    except EOFError:
        approved = False
    if not approved:
        result["preview_only"] = True
        return result

    try:
        from send2trash import send2trash
    except ImportError as exc:
        raise DownloadError("Old-image cleanup requires send2trash so files are never permanently deleted. "
                            "Install it with: python -m pip install send2trash") from exc
    for group in plan:
        for row in group["recycle"]:
            path = Path(row["path"])
            try:
                send2trash(str(path))
                ledger.mark_media_recycled(row)
                result["recycled"].append(str(path))
                print(terminal_text(f"  ✅ Recycled: {path.name}"))
            except Exception as exc:
                message = f"{path}: {exc}"
                result["errors"].append(message)
                print(terminal_text(f"  ⚠️ Kept because recycling failed: {message}"), file=sys.stderr)
    return result


class CaptureWriter(io.TextIOBase):
    """Keep the latest tqdm frame so it can be positioned at the terminal bottom."""
    def write(self, text):
        self.latest = text
        return len(text)

    def __init__(self):
        self.latest = ""

    def flush(self):
        return None


def restore_default_sigint_handler():
    """Keep shared console helpers from turning Ctrl+C into exit status 0."""
    try:
        signal.signal(signal.SIGINT, signal.default_int_handler)
    except ValueError:
        # An embedding application may call this from a non-main thread.
        pass


class ProgressPanel:
    """Keep one global bar and one reusable per-transfer bar on fixed rows."""
    RESIZE_POLL_SECONDS = 0.2
    ANSI_SEQUENCE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")

    def __init__(self, log_file=None):
        try:
            from clairecjs_utils.claire_progressbar import RainbowTqdm, rainbow_hex
            from tqdm.utils import disp_len
        except ImportError as exc:
            raise DownloadError("Install/use clairecjs_utils in C:\\clairecjs_utils and install tqdm. "
                                "The shared rainbow bar is required.") from exc
        # The shared statusbar import may install its own SIGINT handler;
        # restore the downloader's resumable-run policy after that import.
        restore_default_sigint_handler()
        if RainbowTqdm is None:
            raise DownloadError("Install tqdm to use the shared rainbow progress bar.")
        self.rainbow_hex = rainbow_hex
        self._tqdm_width = disp_len
        stderr_tty = bool(getattr(sys.stderr, "isatty", lambda: False)())
        stdout_tty = bool(getattr(sys.stdout, "isatty", lambda: False)())
        # Some Windows launchers expose stdout as the console but pipe stderr.
        # Prefer the interactive stream so the fixed rows and colors are not
        # silently disabled just because diagnostics use stderr.
        self.stream = sys.stderr if stderr_tty else sys.stdout
        self.stderr_tty = stderr_tty
        self.stdout_tty = stdout_tty
        # Windows Terminal/ConPTY supports ANSI even when TERM is unset or
        # classic console-mode probing is unavailable. Only an explicit
        # C4SDL_NO_ANSI request disables the fixed-row renderer. C4SDL_FORCE_ANSI
        # is useful for terminal wrappers that report both streams as pipes.
        self.ansi = ((self.stream.isatty() or os.environ.get("C4SDL_FORCE_ANSI"))
                      and not os.environ.get("C4SDL_NO_ANSI")
                      and (os.name == "nt" or os.environ.get("TERM") != "dumb"))
        self.console_mode = None
        if self.ansi and os.name == "nt":
            # A ConPTY stream can be ANSI-capable without exposing a classic
            # console handle. Keep ANSI enabled when probing is unavailable.
            try:
                kernel = ctypes.windll.kernel32
                kernel.GetStdHandle.restype = ctypes.c_void_p
                handle = kernel.GetStdHandle(-12 if self.stream is sys.stderr else -11)
                mode = ctypes.c_ulong()
                if kernel.GetConsoleMode(ctypes.c_void_p(handle), ctypes.byref(mode)):
                    if kernel.SetConsoleMode(ctypes.c_void_p(handle), mode.value | 4):
                        self.console_mode = (handle, mode.value)
            except (AttributeError, OSError):
                pass
        self.total_writer = CaptureWriter()
        self.total = RainbowTqdm(total=None, desc="🌈 Discovering", file=self.total_writer,
                                 leave=False, disable=False, dynamic_ncols=False)
        self.transient: tuple[str, float, float] | None = None
        self.status = "Loading listing"
        self.columns = 0
        self.rows = 0
        self.scroll_bottom = 0
        self.log_file = log_file
        self.plain_width = 0
        self._lock = threading.RLock()
        self._closed = False
        self._stop_resize = threading.Event()
        self._resize_thread = None
        if self.ansi or self.stream.isatty():
            # The main thread may be waiting for a browser/HTTP request. Only
            # terminal sizing/rendering happens here, never browser or DB work.
            self._resize_thread = threading.Thread(target=self._watch_resize,
                                                   name="c4sdl-terminal-resize", daemon=True)
            self._resize_thread.start()

    def set_total(self, total: int, desc="Total previews"):
        with self._lock:
            self.total.reset(total=total)
            self.total.set_description_str(f"🌈 {desc}", refresh=False)
            self.draw()

    @classmethod
    def _display_width(cls, text: str) -> int:
        width = 0
        for char in cls.ANSI_SEQUENCE.sub("", text):
            if unicodedata.combining(char) or char in ("\ufe0e", "\ufe0f", "\u200d"):
                continue
            width += 2 if unicodedata.east_asian_width(char) in ("W", "F") else 1
        return width

    @classmethod
    def _clip_line(cls, text: str, columns: int) -> str:
        if columns <= 0:
            return ""
        text = cls.ANSI_SEQUENCE.sub("", str(text))
        text = terminal_text(re.sub(r"[\x00-\x1f\x7f]", " ", text), sys.stderr)
        if cls._display_width(text) <= columns:
            return text
        output, used = [], 0
        for char in text:
            char_width = 0 if unicodedata.combining(char) or char in ("\ufe0e", "\ufe0f", "\u200d") else (
                2 if unicodedata.east_asian_width(char) in ("W", "F") else 1
            )
            if used + char_width > max(0, columns - 1):
                break
            output.append(char)
            used += char_width
        return "".join(output) + "…"

    def _colour_line(self, text: str, category: str | None = None) -> str:
        if not self.ansi:
            return text
        message = category or text
        if message.startswith("❌") or any(token in message for token in ("Media error:", "Clip error:")):
            colour = "1;38;2;255;100;115"  # errors: red
        elif message.startswith(("⚠", "🔁", "⏳", "🔒")):
            colour = "38;2;255;205;90"  # warnings/retries/waits: amber
        elif message.startswith(("✅", "📥 Saved:", "💾")):
            colour = "38;2;100;240;155"  # saved/ready: green
        elif message.startswith("↩"):
            colour = "38;2;110;175;195"  # reused: muted cyan
        elif message.startswith(("🎬", "🌈", "🏷", "🗃")):
            colour = "1;38;2;220;150;255"  # clip headings/cache/global: violet
        else:
            colour = "38;2;105;210;255"  # browser/transfer/info: blue
        return f"\x1b[{colour}m{text}\x1b[0m"

    def _progress_line(self, label: str, current: float, total: float | None, columns: int) -> str:
        # Reserve one right-edge cell, as PAFPlayer does, to prevent terminal
        # autowrap from scrolling the bottom status row into the history.
        available = max(0, columns - 1)
        if not available:
            return ""
        if total and total > 0:
            fraction = min(1.0, max(0.0, current / total))
            percent = f"{fraction * 100:3.0f}%"
            count = f"{current / 1048576:.1f}/{total / 1048576:.1f} MB" if label.startswith("📥") else f"{current:,.0f}/{total:,.0f}"
        else:
            fraction = 0.0
            percent = "   "
            count = (f"{current / 1048576:.1f} MB downloaded" if label.startswith("📥")
                     else f"{current:,.0f} found")
        suffix = f" {count}"
        if available < 8:
            return self._clip_line(percent.strip() or "…", available).ljust(available)
        if available < self._display_width(suffix) + 14:
            suffix = ""
        # Bound long filenames rather than the bar. All remaining columns go
        # to Claire's shared tqdm renderer, with no fixed 40-cell bar limit.
        label_room = max(0, min(40, available // 3,
                                available - self._display_width(suffix) - 14))
        category = label
        label = self._clip_line(label, label_room)
        prefix = (label + " " if label else "") + percent + " "
        # tqdm versions that count combining marks/emoji selectors as cells
        # need this adjustment so Unicode labels still occupy the exact width.
        width_adjustment = self._tqdm_width(prefix + suffix) - self._display_width(prefix + suffix)
        return self.total.format_meter(
            n=fraction, total=1, elapsed=0, ncols=available + width_adjustment,
            prefix=self._colour_line(prefix, category), count=self._colour_line(suffix, category),
            bar_format="{desc}{bar}{count}", ascii="─━",
            colour=self.rainbow_hex(fraction) if self.ansi else None,
        )

    def transfer_progress(self, current: int, total: int, label: str):
        with self._lock:
            self.transient = (label, float(current), float(total) if total > 0 else 0.0)
            self.draw()

    def draw_status(self, text: str):
        """Update the reusable transient row without printing a new line."""
        with self._lock:
            self.status = text
            self.transient = None
            self.draw()

    def _terminal_size(self) -> tuple[int, int]:
        # Ask the output device first; inherited COLUMNS/LINES environment
        # variables may describe the window before it was resized.
        for stream in (self.stream, sys.__stdout__, sys.__stderr__):
            try:
                size = os.get_terminal_size(stream.fileno())
                if size.columns > 0 and size.lines > 0:
                    return size.columns, size.lines
            except (AttributeError, OSError, ValueError):
                pass
        cols, rows = shutil.get_terminal_size((100, 30))
        return max(1, cols), max(1, rows)

    def _watch_resize(self):
        while not self._stop_resize.wait(self.RESIZE_POLL_SECONDS):
            try:
                with self._lock:
                    if self._closed:
                        return
                    size = self._terminal_size()
                    if size != (self.columns, self.rows):
                        self._draw_locked(size)
            except (OSError, ValueError):
                # A closed output pipe must not keep a dead renderer running.
                return

    def _reflow_locked(self, cols: int, rows: int):
        if (cols, rows) == (self.columns, self.rows):
            return
        if self.ansi:
            # Like PAFPlayer, use today's viewport, clear the old/new bottom
            # footprints in place, and avoid LF/IL/DL during layout changes.
            old_footprint = {self.rows - 1, self.rows} if self.scroll_bottom else set()
            new_footprint = {rows - 1, rows} if rows >= 5 else set()
            clear = "".join(f"\x1b[{row};1H\x1b[2K"
                            for row in sorted(old_footprint | new_footprint) if 1 <= row <= rows)
            self.stream.write("\x1b[r" + clear)
            if rows >= 5:
                self.stream.write(f"\x1b[1;{rows - 2}r")
        self.columns, self.rows = cols, rows
        self.scroll_bottom = rows - 2 if self.ansi and rows >= 5 else 0
        self.plain_width = 0

    def draw(self):
        with self._lock:
            self._draw_locked(self._terminal_size())

    def _draw_locked(self, size: tuple[int, int]):
        if self._closed:
            return
        cols, rows = size
        self._reflow_locked(cols, rows)
        total_text = self._progress_line("🌈 Global", self.total.n, self.total.total, cols)
        if self.transient:
            label, current, total = self.transient
            transient_text = self._progress_line(label, current, total or None, cols)
        else:
            transient_text = self._colour_line(self._clip_line(self.status, cols - 1), self.status)
        if self.ansi and rows >= 5:
            # Absolute placement also avoids a stale saved cursor after reflow.
            # Always park the cursor inside the log region afterwards.
            self.stream.write(f"\x1b[{rows - 1};1H\x1b[2K{transient_text}"
                              f"\x1b[{rows};1H\x1b[2K{total_text}"
                              f"\x1b[{self.scroll_bottom};1H")
            self.stream.flush()
        elif self.stream.isatty():
            plain_total = re.sub(r"\x1b\[[0-9;]*m", "", total_text)
            plain_transient = re.sub(r"\x1b\[[0-9;]*m", "", transient_text)
            combined = self._clip_line(plain_total + " | " + plain_transient, max(1, cols - 1))
            self.stream.write("\r" + combined + " " * max(0, self.plain_width - self._display_width(combined)))
            self.plain_width = self._display_width(combined)
            self.stream.flush()

    def log(self, text: str):
        with self._lock:
            if self._closed:
                return
            plain = self.ANSI_SEQUENCE.sub("", str(text))
            if self.log_file:
                self.log_file.write(f"{datetime.now().isoformat(timespec='seconds')} {plain}\n")
                self.log_file.flush()
            cols, rows = self._terminal_size()
            self._reflow_locked(cols, rows)
            safe = self._clip_line(plain, cols - 1)
            if self.ansi and self.scroll_bottom:
                self.stream.write(f"\x1b[{self.scroll_bottom};1H\x1b[2K")
            elif self.stream.isatty():
                self.stream.write("\r" + " " * self.plain_width + "\r")
            print(self._colour_line(safe, plain), file=self.stream, flush=True)
            self._draw_locked((cols, rows))

    def wait(self, seconds: float, pump=None):
        start = time.monotonic()
        try:
            while True:
                elapsed = min(seconds, time.monotonic() - start)
                with self._lock:
                    self.transient = (f"⏳ Next clip in {math.ceil(seconds - elapsed)}s", elapsed, seconds)
                    self.draw()
                if elapsed >= seconds:
                    break
                pause = min(0.2, seconds - elapsed)
                pump(pause * 1000) if pump else time.sleep(pause)
        finally:
            with self._lock:
                self.transient = None
                self.draw()

    def close(self):
        self._stop_resize.set()
        if self._resize_thread is not None and threading.current_thread() is not self._resize_thread:
            self._resize_thread.join(timeout=1)
        with self._lock:
            if self._closed:
                return
            self._closed = True
            self.total.close()
            if self.ansi:
                cols, rows = self._terminal_size()
                self._reflow_locked(cols, rows)
                self.stream.write("\x1b[0m\x1b[r\x1b[?25h")
                if self.scroll_bottom:
                    self.stream.write(f"\x1b[{rows - 1};1H\x1b[2K\x1b[{rows};1H\x1b[2K"
                                      f"\x1b[{rows};1H\r\n")
                else:
                    self.stream.write(f"\x1b[{rows};1H\x1b[2K\r\n")
                self.stream.flush()
            if self.console_mode:
                ctypes.windll.kernel32.SetConsoleMode(ctypes.c_void_p(self.console_mode[0]), self.console_mode[1])
            elif self.stream.isatty() and not self.ansi:
                self.stream.write("\r" + " " * self.plain_width + "\r")
                self.stream.flush()


def open_run_log() -> tuple[Path | None, Any | None]:
    """Create one collision-safe text log in the shared C4SDL log folder."""
    LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)
    stem = LOG_DIRECTORY / f"clips4sale-{datetime.now():%Y%m%d-%H%M%S-%f}-{os.getpid()}.log"
    while True:
        target = collision_path(stem)
        try:
            return target, target.open("x", encoding="utf-8")
        except FileExistsError:
            continue


SNAPSHOT_JS = """() => ({
  hydration: window.__remixContext || {},
  title: document.querySelector('h1')?.textContent || '',
  links: Array.from(document.querySelectorAll('[data-testid^="storeClips_"][data-testid$="-clip-link"]')).map(a => ({
    url: a.href, title: a.textContent.trim(),
    resolution_text: a.closest('[data-testid$="-clip"]')?.textContent || ''
  })),
  height: document.documentElement.scrollHeight,
  bottom: window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 6,
  loading: Array.from(document.querySelectorAll('[data-testid="loader"], [aria-busy="true"]'))
    .some(e => e.getBoundingClientRect().height > 0 && getComputedStyle(e).visibility !== 'hidden')
})"""


def longest_consecutive_cached(clip_ids: list[str], cached_ids: set[str]) -> int:
    """Return the longest run of cached IDs in current listing order."""
    longest = current = 0
    for clip_id in clip_ids:
        if clip_id in cached_ids:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def goto(page, url: str, headless: bool, pause: bool = False, pacer: DownloadPacer | None = None):
    def navigate():
        try:
            page.bring_to_front()
        except Exception:
            pass
        response = page.goto(url, wait_until="domcontentloaded", timeout=60000)
        if page.url.casefold() == "about:blank":
            raise DownloadError(f"The browser stayed on about:blank instead of opening: {url}")
        if response and response.status == 429:
            raise SiteBlocked("The site returned HTTP 429 (rate limit). Stop and try again later.")
        if response and response.status >= 400:
            raise SiteBlocked(f"The page returned HTTP {response.status}: {url}")

    navigate()
    current_url = page.url.casefold()
    login_redirect = any(token in current_url for token in ("/login", "/signin", "sign-in", "verify-age"))
    if pause or (login_redirect and not headless):
        if login_redirect:
            prompt = ("The browser is showing a login/verification page. Complete it in the browser, "
                      "then press Enter; the original URL will be reopened: ")
        else:
            prompt = ("Complete any site prompts in the browser, then press Enter; "
                      "the original URL will be reopened: ")
        input(prompt)
        # Authentication commonly redirects away from the listing. Always
        # reactivate the URL the user supplied after the manual step.
        navigate()
    elif not headless:
        if pacer is not None:
            pacer.browser_pause(page, 1.0)
        else:
            page.wait_for_timeout(1000)


def discover(page, url: str, args, panel: ProgressPanel,
             pacer: DownloadPacer | None = None, *, previous_clips: list[Clip] | None = None,
             previous_scroll_steps: int | None = None) -> tuple[list[Clip], str, str]:
    pacer = pacer or DownloadPacer(panel)
    studio_id = re.search(r"/studio/(\d+)", urlsplit(url).path)[1]
    category_match = re.search(r"/Cat(\d+)-([^/]+)", urlsplit(url).path, re.I)
    category_id = category_match[1] if category_match else None
    known: dict[str, Clip] = {}
    records: dict[str, dict] = {}
    pending: set = set()
    network_error: list[str] = []
    studio = ""
    category = ("All Categories" if not category_match or category_match[1] == "0"
                else unquote(category_match[2]).replace("-", " ").title() if category_match else "")
    category_filter_enabled = bool(category_id and category_id != "0")
    prior_clips = list(previous_clips or [])
    prior_ids = {clip.id for clip in prior_clips}
    newest_first = bool(re.search(r"(?:display_order_desc|newest|latest)", url, re.I))
    listing_order: list[str] = []
    scroll_steps = 0
    incremental_reason = ""

    def receive(response):
        if response.request.resource_type not in ("xhr", "fetch"):
            return
        # Ads must not turn a complete listing into an error.
        host = urlsplit(response.url).hostname or ""
        if host != "clips4sale.com" and not host.endswith(".clips4sale.com"):
            return
        if response.status in (403, 429) or response.status >= 500:
            network_error.append(f"Listing request returned HTTP {response.status}.")
        if "json" in response.headers.get("content-type", ""):
            try:
                for obj in dicts(response.json()):
                    if (obj.get("clipId") or obj.get("id")) and obj.get("title"):
                        records[str(obj.get("clipId", obj.get("id")))] = obj
            except Exception:
                pass

    def started(request):
        host = urlsplit(request.url).hostname or ""
        if request.resource_type in ("xhr", "fetch") and (host == "clips4sale.com" or host.endswith(".clips4sale.com")):
            pending.add(request)

    def ended(request):
        pending.discard(request)

    page.on("response", receive)
    page.on("request", started)
    page.on("requestfinished", ended)
    page.on("requestfailed", ended)
    try:
        # Reused logins should begin scrolling without a hidden Enter gate.
        # goto still pauses on a real login redirect; explicit manual setup
        # remains available for same-URL overlays via --pause-before-scrape.
        goto(page, url, args.headless, pause=getattr(args, "pause_before_scrape", False), pacer=pacer)
        panel.status = "🧭 Discovering clips; starting the studio scan"
        panel.draw()
        stable = 0
        previous = None
        for step in range(args.max_scrolls):
            snapshot = page.evaluate(SNAPSHOT_JS)
            data = listing_data(snapshot["hydration"], studio_id)
            studio = data.get("title") or studio or snapshot["title"]
            for entry in data.get("categories", []):
                if str(entry.get("id")) == category_id:
                    category = str(entry.get("name") or category).title()
            for raw in data.get("clips", []):
                records[str(raw.get("clipId", raw.get("id")))] = raw
            visible = snapshot["links"]
            # Initial server data also supports rendering delays and virtualized grids.
            cycle_order = []
            for raw in [*data.get("clips", []), *visible]:
                clip = Clip.from_raw(raw, url)
                if clip and clip.studio_id == studio_id:
                    richer = records.get(clip.id, raw)
                    if (category_filter_enabled and richer.get("categoryId")
                            and str(richer["categoryId"]) != category_id):
                        continue
                    clip = Clip.from_raw(richer, url) or clip
                    known[clip.id] = clip
                    cycle_order.append(clip.id)
            for clip_id in cycle_order:
                if clip_id not in listing_order:
                    listing_order.append(clip_id)
            if network_error:
                raise SiteBlocked(network_error[0] + " Listing may be incomplete; no media were saved.")
            panel.status = f"🧭 Scrolling: {len(known)} clips found; quiet checks {stable}/{args.stable_rounds}"
            panel.total.n = len(known)
            panel.draw()
            if prior_clips and not snapshot["loading"] and not pending:
                cached_streak = longest_consecutive_cached(listing_order, prior_ids)
                required_streak = getattr(args, "rescan_known_streak", RESCAN_KNOWN_STREAK)
                if newest_first and cached_streak >= required_streak:
                    incremental_reason = (f"reached {required_streak} consecutive previously cached clips")
                elif not newest_first and len(known) >= len(prior_clips):
                    incremental_reason = "reached the previous cached clip count"
                elif previous_scroll_steps is not None and scroll_steps >= int(previous_scroll_steps):
                    incremental_reason = "reached the previous scan depth"
                if incremental_reason:
                    panel.log(f"🧭 New-clip scan stopped: {incremental_reason}; "
                              f"{len(known)} fresh listing records checked.")
                    break
            state = (len(known), snapshot["height"])
            if state == previous and snapshot["bottom"] and not pending:
                stable += 1
            else:
                stable = 0
            previous = state
            if stable >= args.stable_rounds:
                if snapshot["loading"]:
                    raise DownloadError("The listing stopped growing but still shows a loader. "
                                        "Retry or increase --stable-rounds/--scroll-delay; no media saved.")
                break
            # Move through the viewport to trigger lazy content, then observe the bottom.
            page.evaluate("window.scrollBy(0, Math.max(500, window.innerHeight * 0.85))")
            scroll_steps += 1
            pacer.browser_pause(page, args.scroll_delay)
        else:
            raise DownloadError("Reached --max-scrolls before the listing finished. No media saved.")
    finally:
        for event, handler in (("response", receive), ("request", started),
                               ("requestfinished", ended), ("requestfailed", ended)):
            page.remove_listener(event, handler)
    if not known:
        raise DownloadError("No clips found. Check the browser for a site prompt or changed page layout.")
    if not studio and not args.studio_name:
        raise DownloadError("Could not identify the studio. Supply --studio-name.")
    fresh_clips = list(known.values())
    new_clip_ids = set(known).difference(prior_ids) if prior_clips else set()
    if prior_clips:
        # Fresh records win so title/category/quality metadata can update;
        # cached records below the old boundary remain available for resume.
        merged = dict(known)
        for clip in prior_clips:
            merged.setdefault(clip.id, clip)
        clips = list(merged.values())
    else:
        clips = fresh_clips
    args._last_discovery_scroll_steps = scroll_steps
    args._last_discovery_incremental = bool(prior_clips)
    args._last_discovery_new_clips = len(new_clip_ids)
    args._last_discovery_stop_reason = incremental_reason
    return clips, args.studio_name or studio, args.category_name or category


def inspect_clip(page, clip: Clip, args, pacer: DownloadPacer | None = None) -> tuple[dict, list[Media]]:
    goto(page, clip.url, args.headless, pacer=pacer)
    if pacer is not None:
        pacer.browser_pause(page, args.page_delay)
    else:
        page.wait_for_timeout(args.page_delay * 1000)
    raw = detail_data(page.evaluate("window.__remixContext || {}"), clip.id)
    if not raw:
        raw = detail_data(hydration_from_html(page.content()), clip.id)
    if not raw:
        raise DownloadError(f"Clip {clip.id}: selected clip data is unavailable; check for a site prompt.")
    merged = {**clip.raw, **raw}
    media = media_from_raw(merged, clip.url)
    # Current clip's VideoObject is a fallback if the player fields change.
    for text in page.locator('script[type="application/ld+json"]').all_text_contents():
        try:
            for obj in dicts(json.loads(text)):
                if obj.get("@type") == "VideoObject" and obj.get("contentUrl"):
                    url = urljoin(clip.url, obj["contentUrl"])
                    if not any(m.url == url for m in media) and Path(urlsplit(url).path).suffix.lower() in VIDEO_EXTENSIONS:
                        media.append(Media(url, "preview"))
        except (json.JSONDecodeError, TypeError):
            continue
    if not media:
        raise DownloadError(f"No public preview or images exposed for clip {clip.id}.")
    return merged, media


def probe_video(path: Path, ffprobe: str) -> dict:
    result = subprocess.run([ffprobe, "-v", "error", "-show_entries",
                             "format=duration:stream=codec_type,width,height,duration", "-of", "json", str(path)],
                            capture_output=True, text=True, timeout=60, check=False)
    if result.returncode:
        raise DownloadError(f"ffprobe could not read {path.name}")
    info = json.loads(result.stdout)
    streams = [s for s in info.get("streams", []) if s.get("codec_type") == "video"]
    if not streams:
        raise DownloadError(f"No video stream in {path.name}")
    durations = []
    for item in [info.get("format", {}), *streams]:
        try:
            value = float(item.get("duration", 0))
            if math.isfinite(value) and value > 0:
                durations.append(value)
        except (ValueError, TypeError):
            pass
    if not durations:
        raise DownloadError(f"Cannot determine actual preview duration: {path.name}")
    return {"duration": max(durations), "width": max(s.get("width", 0) for s in streams),
            "height": max(s.get("height", 0) for s in streams)}


def file_extension(url: str, content_type: str) -> str:
    mime = content_type.split(";", 1)[0].strip().lower()
    types = {"video/mp4": ".mp4", "video/webm": ".webm", "video/quicktime": ".mov",
             "video/x-ms-wmv": ".wmv", "video/ogg": ".ogv", "image/jpeg": ".jpg",
             "image/gif": ".gif", "image/png": ".png", "image/webp": ".webp", "image/avif": ".avif"}
    if mime in types:
        return types[mime]
    ext = Path(unquote(urlsplit(url).path)).suffix.lower()
    if mime in ("application/octet-stream", "binary/octet-stream", "") and ext in VIDEO_EXTENSIONS | IMAGE_EXTENSIONS:
        return ".jpg" if ext == ".jpeg" else ext
    raise DownloadError(f"Expected media, received {mime or 'unknown content type'}")


def tag_video_partial(partial: Path, extension: str, category: str, ffmpeg: str, ffprobe: str) -> Path:
    """Stream-copy to a new staged file; never edit existing video bytes in place."""
    formats = {".mp4": "mp4", ".m4v": "mp4", ".mov": "mov", ".webm": "webm",
               ".wmv": "asf", ".avi": "avi", ".ogv": "ogg"}
    tagged = collision_path(partial.with_name(partial.name + f".tag-{uuid.uuid4().hex[:8]}.part"))
    command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-n",
               "-i", str(partial), "-map", "0", "-map_metadata", "0", "-c", "copy",
               "-metadata", f"genre={category}", "-metadata:s", f"genre={category}",
               "-f", formats[extension], str(tagged)]
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8",
                            errors="replace", timeout=120, check=False)
    if result.returncode:
        raise DownloadError(f"Category metadata could not be written; staging files preserved: {result.stderr.strip()}")
    check = subprocess.run([ffprobe, "-v", "error", "-show_entries",
                            "format_tags=genre:stream_tags=genre", "-of", "json", str(tagged)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=60, check=False)
    try:
        tags = json.loads(check.stdout)
        genres = [value for obj in dicts(tags) for key, value in obj.items() if key.casefold() == "genre"]
    except (json.JSONDecodeError, TypeError):
        genres = []
    if check.returncode or category not in genres:
        raise DownloadError("Category metadata verification failed; untagged and tagged staging files preserved.")
    return tagged


def download_media(session, media: Media, output: Path, stem: str, referer: str,
                   panel: ProgressPanel, *, video_category: str = "", ffmpeg: str = "ffmpeg",
                   ffprobe: str = "ffprobe") -> Path:
    """Try the best still first, falling back only when its URL is gone."""
    candidates = (media.url, *media.alternate_urls)
    for index, url in enumerate(candidates):
        candidate = Media(url, media.role)
        try:
            return _download_media_one(session, candidate, output, stem, referer, panel,
                                       video_category=video_category, ffmpeg=ffmpeg, ffprobe=ffprobe)
        except Exception as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status not in (404, 410) or index + 1 >= len(candidates):
                raise
            panel.log(f"↪️ {media.role} candidate returned HTTP {status}; trying fallback URL "
                      f"({index + 2}/{len(candidates)}): {candidates[index + 1]}")
    raise DownloadError(f"No available media candidate for {stem}")


def _download_media_one(session, media: Media, output: Path, stem: str, referer: str,
                        panel: ProgressPanel, *, video_category: str = "", ffmpeg: str = "ffmpeg",
                        ffprobe: str = "ffprobe") -> Path:
    # Stream in bounded chunks. Exclusive file creation prevents overwrite races.
    hinted_ext = Path(unquote(urlsplit(media.url).path)).suffix.lower()
    if hinted_ext == ".jpeg":
        hinted_ext = ".jpg"
    hinted_partial = (output / (stem + hinted_ext)).with_name(
        (output / (stem + hinted_ext)).name + ".part"
    ) if hinted_ext else None
    resume_from = hinted_partial.stat().st_size if hinted_partial and hinted_partial.is_file() else 0
    headers = {"Referer": referer}
    if resume_from:
        headers["Range"] = f"bytes={resume_from}-"
    with session.get(media.url, headers=headers, stream=True, timeout=(20, 60)) as response:
        if response.status_code in (401, 403, 429):
            raise SiteBlocked(f"Media returned HTTP {response.status_code}; stopping this run.")
        response.raise_for_status()
        if response.status_code == 206 and not resume_from:
            raise DownloadError("Server returned partial media to a full-file request.")
        ext = file_extension(response.url, response.headers.get("Content-Type", ""))
        target = collision_path(output / (stem + ext))
        partial = target.with_name(target.name + ".part")
        if response.status_code == 206:
            content_range = response.headers.get("Content-Range", "")
            match = re.match(r"bytes\s+(\d+)-\d+/(\d+|\*)", content_range, re.I)
            if match and int(match.group(1)) != resume_from:
                raise DownloadError("Server resumed the media at an unexpected byte offset.")
        elif resume_from:
            # The server ignored Range. Preserve the old partial and start a
            # new one rather than overwriting evidence from the interruption.
            partial = collision_path(partial)
            resume_from = 0
        content_range = response.headers.get("Content-Range", "")
        range_match = re.match(r"bytes\s+\d+-\d+/(\d+)", content_range, re.I)
        total = int(response.headers.get("Content-Length") or 0)
        expected_total = (int(range_match.group(1)) if range_match else resume_from + total
                          if response.status_code == 206 else total)
        written = resume_from
        if hasattr(panel, "transfer_progress"):
            panel.transfer_progress(written, expected_total, f"📥 {stem + ext}")
        else:
            panel.status = f"Downloading {written / 1048576:.1f} MB"
            panel.draw()
        try:
            with partial.open("ab" if resume_from else "xb") as stream:
                for chunk in response.iter_content(256 * 1024):
                    if chunk:
                        stream.write(chunk)
                        written += len(chunk)
                        if hasattr(panel, "transfer_progress"):
                            panel.transfer_progress(written, expected_total, f"📥 {stem + ext}")
                        else:
                            panel.status = f"Downloading {written / 1048576:.1f} MB"
                            panel.draw()
                stream.flush()
                os.fsync(stream.fileno())
            if written == 0 or (expected_total and not response.headers.get("Content-Encoding") and written != expected_total):
                raise DownloadError("Incomplete media response; partial file preserved.")
            publish = partial
            if video_category and ext in VIDEO_EXTENSIONS:
                panel.log(f"🏷️ Embedding primary category: {video_category}")
                publish = tag_video_partial(partial, ext, video_category, ffmpeg, ffprobe)
            # Windows rename does not replace existing files; hard-link publication is
            # atomic and refuses collisions on other platforms. No existing file is removed.
            while True:
                target = collision_path(output / (stem + ext))
                try:
                    if os.name == "nt":
                        publish.rename(target)
                    else:
                        os.link(publish, target)
                        from send2trash import send2trash
                        send2trash(str(publish))
                    break
                except FileExistsError:
                    continue
            if publish != partial:
                try:
                    from send2trash import send2trash
                    send2trash(str(partial))
                except Exception as exc:
                    # A successful tagged download remains successful if the
                    # Recycle Bin is unavailable. Never permanently delete.
                    panel.log(f"⚠️ Kept untagged staging file (could not recycle): {partial}: {exc}")
                else:
                    panel.log(f"♻️ Recycled untagged staging file: {partial}; recoverable from Recycle Bin.")
            return target
        except BaseException:
            if partial.exists():
                panel.log(f"Preserved incomplete file: {partial}")
            raise


def base_name(output: Path, studio: str, category: str, clip: Clip,
              *, include_category_prefix: bool = False) -> str:
    category_tag = category_prefix(category) if include_category_prefix else ""
    prefix = " - ".join(x for x in (category_tag, studio, category, clean_title(clip.title)) if x)
    stem = safe_filename(prefix)
    # Leave room for suffixes and .part on Windows systems without long paths enabled.
    room = min(190, 240 - len(str(output)) - 40)
    if room < 30:
        raise DownloadError("Destination path is too long; choose a shorter folder.")
    if len(stem) > room:
        stem = stem[:room - len(clip.id) - 3].rstrip(" .") + f" [{clip.id}]"
    return stem


def media_stem(stem: str, role: str) -> str:
    """Use singular, predictable names for the reduced media set."""
    return stem if role == "preview" else f"{stem}-{role}"


def clone_browser_profile(source: Path, destination: Path, status=None):
    """Copy only login state, with bounded SQLite snapshots and visible progress.

    The destination must be new. Failed snapshots stay as uniquely named
    partials, never as a seemingly complete Cookies database. No login values
    are logged, and the source browser can remain open throughout the copy.
    """
    source = source.resolve()
    destination = destination.resolve()
    if not source.is_dir():
        raise DownloadError(
            f"Could not clone browser profile: source profile is not available at {source}. "
            "The first run must finish creating its logged-in profile before another run can share it."
        )
    if destination == source or source in destination.parents:
        raise DownloadError("The concurrent profile must be outside the source profile.")
    destination.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    copied = 0
    last_update = 0.0

    def update(path: Path, detail: str = "", force: bool = False):
        nonlocal last_update
        now = time.monotonic()
        relative = path.relative_to(source)
        if now - started >= PROFILE_CLONE_TIMEOUT_SECONDS:
            raise DownloadError(f"Login-state copy exceeded {PROFILE_CLONE_TIMEOUT_SECONDS:g}s at {relative}. "
                                f"Source: {source}. Incomplete copy preserved at {destination}.")
        if force or now - last_update >= 0.5:
            message = (f"🔐 Copying login state: {relative} | {copied} files, {now - started:.1f}s"
                       + (f" | {detail}" if detail else ""))
            if status:
                status(message)
            else:
                print(terminal_text(message), file=sys.stderr, flush=True)
            last_update = now

    def is_sqlite_database(path: Path) -> bool:
        try:
            with path.open("rb") as stream:
                return stream.read(16) == b"SQLite format 3\x00"
        except OSError:
            return False

    def snapshot_sqlite(src: Path, dst: Path):
        # SQLite's backup API captures a transactionally consistent image even
        # while Chrome has the source database open. Copying DB/WAL separately
        # can otherwise miss the newest login-cookie updates.
        source_uri = src.resolve().as_uri() + "?mode=ro"
        source_db = target_db = None
        snapshot_started = time.monotonic()

        def progress(code, remaining, total):
            update(src, "database busy; waiting" if code in (5, 6) else f"{total - remaining}/{total} pages")
            if time.monotonic() - snapshot_started >= PROFILE_DATABASE_TIMEOUT_SECONDS:
                raise TimeoutError(f"SQLite login snapshot remained busy for {PROFILE_DATABASE_TIMEOUT_SECONDS:g}s")

        try:
            # busy_timeout does not bound Python's backup retry loop. Its
            # progress callback must enforce a deadline even on SQLITE_BUSY.
            source_db = sqlite3.connect(source_uri, uri=True, timeout=0)
            source_db.execute("PRAGMA busy_timeout=0")
            target_db = sqlite3.connect(str(dst), timeout=0)
            source_db.backup(target_db, pages=128, progress=progress, sleep=0.05)
        finally:
            if target_db is not None:
                target_db.close()
            if source_db is not None:
                source_db.close()

    def ignore(_directory: str, names: list[str]) -> set[str]:
        ignored = set()
        for name in names:
            folded = name.casefold()
            if (name in PROFILE_COPY_IGNORES or "singleton" in folded
                    or folded.endswith(PROFILE_SQLITE_SIDECARS)
                    or folded.endswith(".lock")):
                ignored.add(name)
        return ignored

    def copy_file(src: Path, dst: Path):
        nonlocal copied
        update(src, force=True)
        dst.parent.mkdir(parents=True, exist_ok=True)
        last_error = None
        for attempt in range(3):
            partial = dst.with_name(dst.name + f".copy-{uuid.uuid4().hex}.part")
            try:
                if is_sqlite_database(src):
                    snapshot_sqlite(src, partial)
                else:
                    with src.open("rb") as reader, partial.open("xb") as writer:
                        while chunk := reader.read(1024 * 1024):
                            writer.write(chunk)
                            update(src)
                # Publish only a completed snapshot/copy. Preserve every old
                # file if an unexpected destination collision occurs.
                if dst.exists():
                    raise DownloadError(f"Profile copy refuses to replace existing file: {dst}")
                partial.rename(dst)
                copied += 1
                return
            except TimeoutError as exc:
                last_error = exc
                break
            except (OSError, sqlite3.Error) as exc:
                last_error = exc
                if attempt < 2:
                    update(src, f"retry {attempt + 1}/2: {exc}", force=True)
                    time.sleep(0.15 * (attempt + 1))
        raise DownloadError(f"Could not copy login state {src.relative_to(source)}: {last_error}. "
                            f"Source: {source}. Incomplete copy preserved at {destination}. "
                            "Close the source browser briefly if this login file remains locked.") from last_error

    def copy_directory(src: Path, dst: Path):
        update(src)
        dst.mkdir(parents=True, exist_ok=True)
        with os.scandir(src) as scan:
            entries = sorted(scan, key=lambda entry: entry.name)
        ignored = ignore(str(src), [entry.name for entry in entries])
        for entry in entries:
            if entry.name in ignored:
                continue
            child_src, child_dst = Path(entry.path), dst / entry.name
            if entry.is_dir(follow_symlinks=False):
                copy_directory(child_src, child_dst)
            elif entry.is_file(follow_symlinks=False):
                copy_file(child_src, child_dst)

    def copy_selected(src: Path):
        relative = src.relative_to(source)
        if any((source / Path(*relative.parts[:index])).is_symlink()
               for index in range(1, len(relative.parts) + 1)):
            raise DownloadError(f"Login-state copy will not follow a profile symlink: {relative}")
        dst = destination / relative
        if src.is_dir():
            copy_directory(src, dst)
        elif src.is_file():
            copy_file(src, dst)

    copy_selected(source / "Local State")
    with os.scandir(source) as scan:
        profiles = sorted(entry.name for entry in scan if entry.is_dir(follow_symlinks=False)
                          and (entry.name == "Default" or re.fullmatch(r"Profile \d+", entry.name)))
    for profile in profiles:
        for relative in PROFILE_LOGIN_PATHS:
            copy_selected(source / profile / relative)
    write_new_json(destination / PROFILE_SNAPSHOT_MARKER,
                   {"source": str(source), "completed": datetime.now().isoformat(), "files": copied})
    message = f"✅ Login-state copy ready: {copied} files in {time.monotonic() - started:.1f}s"
    if status:
        status(message)
    else:
        print(terminal_text(message), file=sys.stderr, flush=True)


def has_login_profile(profile: Path) -> bool:
    """Recognize a saved login candidate without inspecting cookie values."""
    try:
        if not (profile / "Local State").is_file():
            return False
        return any(cookie.is_file() and cookie.stat().st_size > 0
                   for directory in profile.iterdir()
                   if directory.is_dir() and (directory.name == "Default"
                                               or re.fullmatch(r"Profile \d+", directory.name))
                   for cookie in (directory / "Network" / "Cookies", directory / "Cookies"))
    except OSError:
        return False


def migrate_legacy_login_profile(profile: Path, status) -> bool:
    """Move a usable temporary-profile login into AppData on first v0.9 use."""
    try:
        if profile.resolve() != DEFAULT_PROFILE_DIR.resolve() or profile.exists() \
                or not has_login_profile(LEGACY_DEFAULT_PROFILE_DIR):
            return False
        profile.parent.mkdir(parents=True, exist_ok=True)
        staging = profile.parent / f".{profile.name}-migration-{uuid.uuid4().hex[:10]}"
        status(f"🔐 Moving the saved login from temporary storage into AppData: {profile}")
        clone_browser_profile(LEGACY_DEFAULT_PROFILE_DIR, staging, status=status)
        try:
            staging.rename(profile)
        except FileExistsError:
            # A concurrent process won the migration race. Preserve this valid
            # copy as an idle snapshot rather than deleting or overwriting it.
            snapshot_root = profile.parent / PROFILE_SNAPSHOT_ROOT
            snapshot_root.mkdir(parents=True, exist_ok=True)
            staging.rename(collision_path(snapshot_root / staging.name))
        status(f"✅ Persistent AppData login is ready: {profile}")
        return True
    except (DownloadError, OSError) as exc:
        status(f"⚠️ The old temporary login could not be migrated: {exc}")
        return False


def saved_login_candidates(profile: Path) -> list[Path]:
    """Prefer completed, never-opened snapshots; allow old idle run profiles."""
    candidates = []
    for folder in (PROFILE_SNAPSHOT_ROOT, PROFILE_FALLBACK_ROOT):
        root = profile.parent / folder
        if not root.is_dir():
            continue
        directories = sorted((item for item in root.iterdir() if item.is_dir()),
                             key=lambda item: item.stat().st_mtime, reverse=True)
        for item in directories:
            if folder == PROFILE_SNAPSHOT_ROOT and not (item / PROFILE_SNAPSHOT_MARKER).is_file():
                continue
            owner = re.match(r"run-(\d+)-", item.name)
            if owner and DownloadDatabase._pid_alive(int(owner[1])):
                continue
            if has_login_profile(item):
                candidates.append(item)
    return candidates[:3]


def clone_concurrent_profile(profile: Path, destination: Path, status) -> Path:
    """Use a saved login when the retained browser exclusively locks Cookies."""
    errors = []
    candidates = [profile, *saved_login_candidates(profile)]
    for index, source in enumerate(candidates):
        target = collision_path(destination)
        if index:
            status(f"🔐 Trying saved login from {source.name}; the shared profile is busy")
        try:
            clone_browser_profile(source, target, status=status)
            return target
        except (DownloadError, OSError) as exc:
            errors.append(f"{source}: {exc}")
            status(f"⚠️ Login copy unavailable: {exc}")
    raise DownloadError("No readable login profile was available. " + " | ".join(errors)
                        + " Close the retained downloader browser once, then retry; "
                        "future runs keep an idle login snapshot for concurrent startup.")


def preserve_login_snapshot(profile: Path, source: Path, status):
    """Keep an encrypted on-disk cookie snapshot that Chrome never opens."""
    if not has_login_profile(source):
        return
    root = profile.parent / PROFILE_SNAPSHOT_ROOT
    snapshot = root / f"login-{datetime.now():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:10]}"
    try:
        status("🔐 Saving an idle login snapshot for concurrent runs")
        clone_browser_profile(source, snapshot, status=status)
    except (DownloadError, OSError) as exc:
        # An available run profile may still be used; retaining older complete
        # snapshots is preferable to aborting a job over snapshot maintenance.
        status(f"⚠️ Could not refresh the idle login snapshot: {exc}")


def acquire_profile_lease(profile_dir: Path):
    """Atomically decide which process may launch the reusable profile.

    Chromium's own singleton lock can appear slightly after Playwright starts
    Chrome. This small OS-backed lease closes that startup race; the OS releases
    it automatically if a downloader is terminated.
    """
    lease_path = profile_dir.parent / f".{profile_dir.name}.clips4sale.lock"
    try:
        lease_path.parent.mkdir(parents=True, exist_ok=True)
        stream = lease_path.open("a+b")
    except OSError:
        return None
    try:
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            stream.write(b"\0")
            stream.flush()
        stream.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return stream
    except (OSError, ImportError):
        stream.close()
        return None


def release_profile_lease(lease):
    if lease is None:
        return
    try:
        lease.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(lease.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(lease.fileno(), fcntl.LOCK_UN)
    except (OSError, ImportError):
        pass
    finally:
        lease.close()


def close_browser_resources(context, browser, report: dict):
    """Close browser handles without masking the saved run report on shutdown."""
    resources = [context]
    if browser is not None and browser is not context:
        resources.append(browser)
    for resource in resources:
        if resource is None:
            continue
        try:
            resource.close()
        except Exception as exc:
            message = str(exc)
            normalized = message.casefold()
            if "connection closed while reading from the driver" not in normalized:
                report.setdefault("errors", []).append(f"Browser cleanup warning: {message}")


def browser_executable_for(args) -> Path | None:
    """Find the visible browser matching Playwright's selected channel."""
    program_files = [os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMFILES(X86)"),
                     os.environ.get("LOCALAPPDATA")]
    candidates: list[Path] = []
    if args.browser == "chrome":
        candidates.extend(Path(root) / "Google" / "Chrome" / "Application" / "chrome.exe"
                          for root in program_files if root)
    elif args.browser == "msedge":
        candidates.extend(Path(root) / "Microsoft" / "Edge" / "Application" / "msedge.exe"
                          for root in program_files if root)
    else:
        playwright_executable = getattr(args, "_playwright_chromium_executable", None)
        if playwright_executable:
            candidates.append(Path(playwright_executable))
    candidates.extend(Path(path) for path in (
        shutil.which("chrome.exe"), shutil.which("chrome"),
        shutil.which("msedge.exe"), shutil.which("msedge"),
    ) if path)
    return next((candidate for candidate in candidates if candidate.is_file()), None)


def leave_browser_open(args, last_url: str, report: dict, panel) -> None:
    """Hand a headed persistent profile back to an ordinary visible browser.

    Playwright owns the browser it starts and necessarily closes it as its
    context shuts down.  Start a normal browser only after that cleanup has
    released the profile lock, so the user keeps a usable, logged-in window.
    """
    if args.close_browser_on_exit:
        report["browser_left_open"] = {"left_open": False, "reason": "disabled by --close-browser-on-exit"}
        return
    if args.headless:
        report["browser_left_open"] = {"left_open": False, "reason": "headless run"}
        return
    if args.no_persistent_login:
        report["browser_left_open"] = {"left_open": False, "reason": "isolated non-persistent session"}
        return
    profile = getattr(args, "_profile_actual", None)
    if not profile:
        report.setdefault("errors", []).append("Browser hand-off warning: no persistent profile was available.")
        return
    executable = browser_executable_for(args)
    if executable is None:
        report.setdefault("errors", []).append("Browser hand-off warning: could not locate Chrome, Edge, or Chromium.")
        return
    target_url = last_url if str(last_url).startswith(("http://", "https://")) else args.url
    command = [str(executable), "--no-first-run", f"--user-data-dir={Path(profile)}", target_url]
    creationflags = 0
    if os.name == "nt":
        creationflags = 0x00000008 | 0x00000200  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
    try:
        # Closing a Playwright persistent context returns Chrome's singleton
        # lock asynchronously.  A short hand-off delay avoids a second window
        # briefly starting on about:blank and immediately exiting on the lock.
        time.sleep(0.5)
        subprocess.Popen(command, close_fds=True, creationflags=creationflags)
    except OSError as exc:
        report.setdefault("errors", []).append(f"Browser hand-off warning: {exc}")
        panel.log(f"⚠️ Could not leave the browser open: {exc}")
        return
    report["browser_left_open"] = {
        "left_open": True, "profile": str(profile), "url": target_url,
        "executable": str(executable),
    }
    panel.log(f"🌐 Browser left open at: {target_url}")


def retryable_media_error(exc: Exception) -> bool:
    """Media failures remain retryable unless the user lowers ``--media-retries``."""
    return True


def session_for(context, page):
    import requests
    session = requests.Session()
    session.headers.update({"User-Agent": page.evaluate("navigator.userAgent"), "Accept-Encoding": "identity"})
    for cookie in context.cookies():
        session.cookies.set(cookie["name"], cookie["value"], domain=cookie["domain"],
                            path=cookie["path"], secure=cookie["secure"])
    return session


def open_browser_context(playwright, args, status=None):
    """Open Chrome, automatically isolating concurrent persistent profiles.

    Chrome deliberately refuses two persistent contexts using one user-data
    directory.  The old implementation surfaced that lock as a fatal error.
    We first try the familiar reusable profile; if it is busy, this run gets a
    unique sibling profile instead of failing the whole job.  An explicit
    ``--profile-dir`` is still honored as the preferred profile, but it also
    receives the same automatic fallback so parallel jobs remain possible.
    """
    launch = {"headless": args.headless, "timeout": BROWSER_LAUNCH_TIMEOUT_MS}
    if args.browser != "chromium":
        launch["channel"] = args.browser
    try:
        args._playwright_chromium_executable = playwright.chromium.executable_path
    except Exception:
        pass

    def report_status(message: str):
        if status:
            status(message)
        else:
            print(terminal_text(message), file=sys.stderr, flush=True)

    viewport = {"width": 1280, "height": 900}
    if args.no_persistent_login:
        report_status("🌐 Starting an isolated browser session...")
        browser = playwright.chromium.launch(**launch)
        return browser, browser.new_context(viewport=viewport)

    profile_dir = (Path(args.profile_dir).expanduser().resolve()
                   if args.profile_dir else DEFAULT_PROFILE_DIR)
    if not args.profile_dir:
        migrate_legacy_login_profile(profile_dir, report_status)
    profile_dir.mkdir(parents=True, exist_ok=True)
    report_status(f"🔐 Checking reusable browser profile: {profile_dir}")
    lease = acquire_profile_lease(profile_dir)
    profile_busy = lease is None or any(os.path.lexists(str(profile_dir / name)) for name in PROFILE_LOCK_NAMES)
    first_error = None
    if not profile_busy:
        # Capture an idle profile before Chrome can exclusively lock Cookies.
        preserve_login_snapshot(profile_dir, profile_dir, report_status)
        report_status("🌐 Starting the reusable browser session...")
        try:
            context = playwright.chromium.launch_persistent_context(
                str(profile_dir), viewport=viewport, **launch
            )
            args._profile_actual = profile_dir
        except Exception as exc:
            first_error = exc
    else:
        first_error = DownloadError(
            f"The reusable browser profile is already in use: {profile_dir}"
        )
    if first_error is not None:
        release_profile_lease(lease)
        lease = None
        # Clone the login-bearing profile before launching the isolated copy.
        # Chromium's lock is per user-data directory, so each concurrent run
        # gets its own lock while retaining the same cookies/site storage.
        report_status("🔒 Shared browser profile is busy; copying the logged-in profile for this run...")
        fallback_root = profile_dir.parent / PROFILE_FALLBACK_ROOT
        fallback_root.mkdir(parents=True, exist_ok=True)
        fallback = fallback_root / f"run-{os.getpid()}-{uuid.uuid4().hex[:10]}"
        fallback = clone_concurrent_profile(profile_dir, fallback, report_status)
        preserve_login_snapshot(profile_dir, fallback, report_status)
        report_status("🌐 Starting the isolated concurrent browser session...")
        try:
            context = playwright.chromium.launch_persistent_context(
                str(fallback), viewport=viewport, **launch
            )
        except Exception as second_error:
            raise DownloadError(
                f"Could not open a browser profile at {profile_dir}, and the isolated "
                f"concurrent-run profile {fallback} also failed. The first error was: {first_error}"
            ) from second_error
        args._profile_actual = fallback
        report_status(f"✅ Isolated browser session ready; login copied from the shared profile.")
    args._profile_lease = lease
    # launch_persistent_context returns the context itself; it owns its browser.
    return context, context


def run_page(context):
    """Use Chromium's initial page when a persistent context already created one."""
    pages = list(getattr(context, "pages", ()) or ())
    for page in pages:
        try:
            if not page.is_closed():
                page.bring_to_front()
                return page
        except Exception:
            continue
    page = context.new_page()
    try:
        page.bring_to_front()
    except Exception:
        pass
    return page


def failed_last(clips: list[Clip], failed_ids: set[tuple[str, str]]) -> list[Clip]:
    """Keep the original listing order while moving failed clips to the end."""
    return sorted(clips, key=lambda clip: (clip.studio_id, clip.id) in failed_ids)


def prepare_selection(ledger: DownloadDatabase, args, clips: list[Clip]):
    """Apply retry, failed-last, and max-clip policy to a cached listing."""
    selected, duplicates = deduplicate(clips)
    retry_ids = getattr(args, "_retry_clip_keys", None)
    if retry_ids is not None:
        selected = [clip for clip in selected if (clip.studio_id, clip.id) in retry_ids]
    failed_ids = ledger.failed_clip_ids()
    selected = failed_last(selected, failed_ids)
    if args.max_clips:
        selected = selected[:args.max_clips]
    return selected, duplicates, failed_ids


def inter_clip_wait(video_already_available: bool, deferred_by_other_run: bool,
                    durations: list[float], unknown_duration: bool, args,
                    clip_had_error: bool = False) -> float:
    """Choose the pause after a clip, keeping failures from looking hung."""
    if args.dry_run:
        seconds = args.page_delay
    elif video_already_available:
        seconds = 0.0
    elif deferred_by_other_run:
        # Another process still owns the media claim; it has not completed for
        # this run yet, so use the short coordination pause rather than the
        # duration-based delay.
        seconds = random_delay(*REUSED_VIDEO_PAUSE_RANGE)
    elif clip_had_error:
        # A missing/failed preview has no trustworthy duration. Do not make a
        # failed clip impose the full 30-second unknown-duration fallback;
        # continue through the queue and leave it for a later failure-only run.
        seconds = random_delay(*REUSED_VIDEO_PAUSE_RANGE)
    else:
        seconds = max(durations) if durations else args.fallback_wait
        if unknown_duration:
            seconds = max(seconds, args.fallback_wait)
    return seconds


def retry_ids_from_source(source: Path) -> tuple[set[tuple[str, str]], str | None, Path | None]:
    """Read failed clip identities from either a JSON report or the DB."""
    source = source.expanduser().resolve()
    if not source.is_file():
        raise DownloadError(f"Retry source does not exist: {source}")
    if source.suffix.casefold() in {".db", ".sqlite", ".sqlite3"}:
        ledger = DownloadDatabase(source)
        try:
            return ledger.failed_clip_ids(), ledger.metadata("listing"), None
        finally:
            ledger.close()
    try:
        report = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DownloadError(f"Could not read retry report: {source}") from exc
    failed: set[tuple[str, str]] = set()
    for entry in report.get("clips", []):
        saved_roles = {item.get("role") for item in entry.get("files", [])}
        unresolved_attempts = any(item.get("role") not in saved_roles
                                  for item in entry.get("media_attempt_errors", []))
        if entry.get("errors") or unresolved_attempts:
            studio = str(report.get("studio_id") or report.get("studio") or "")
            clip_id = str(entry.get("clip_id") or "")
            if studio and clip_id:
                failed.add((studio, clip_id))
    destination = report.get("destination")
    return failed, report.get("listing"), Path(destination) if destination else None


def private_database_path() -> Path:
    """Return the shared cache/history ledger under the user's AppData folder."""
    HISTORY_ROOT.mkdir(parents=True, exist_ok=True)
    return PRIVATE_DATABASE_PATH


def private_report_path(dry_run: bool) -> Path:
    PRIVATE_REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    return PRIVATE_REPORT_ROOT / ("clips4sale-plan.json" if dry_run else "clips4sale-run.json")


def automatic_database_backup(source: Path) -> Path | None:
    """Create and verify a transactionally consistent, collision-safe DB backup."""
    source = source.expanduser().resolve()
    if not source.is_file():
        return None
    try:
        private = source == PRIVATE_DATABASE_PATH.resolve()
    except OSError:
        private = False
    root = DATABASE_BACKUP_ROOT if private else source.parent / "backups"
    root.mkdir(parents=True, exist_ok=True)
    target = collision_path(root / f"{source.stem}.{datetime.now():%Y%m%d-%H%M%S}.{os.getpid()}.db")
    partial = target.with_name(target.name + f".{uuid.uuid4().hex}.part")
    source_db = target_db = None
    try:
        source_db = sqlite3.connect(source.as_uri() + "?mode=ro", uri=True, timeout=60)
        target_db = sqlite3.connect(str(partial), timeout=60)
        source_db.backup(target_db, pages=256, sleep=0.05)
        target_db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        check = target_db.execute("PRAGMA quick_check").fetchone()
        if not check or str(check[0]).casefold() != "ok":
            raise DownloadError(f"SQLite backup verification failed: {check}")
        target_db.close()
        target_db = None
        source_db.close()
        source_db = None
        partial.rename(target)
        return target
    except Exception as exc:
        # Keep a partial backup for diagnosis. It must never be silently or
        # permanently deleted under Claire's replacement/recycling rules.
        raise DownloadError(f"Could not create automatic database backup; partial preserved at "
                            f"{partial}: {exc}") from exc
    finally:
        if target_db is not None:
            target_db.close()
        if source_db is not None:
            source_db.close()


def recent_history(database: Path, limit: int = 20) -> list[dict]:
    """Read run history without creating or modifying the database."""
    database = database.expanduser().resolve()
    if not database.is_file():
        return []
    connection = sqlite3.connect(database.as_uri() + "?mode=ro", uri=True, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        table = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='run_history'"
        ).fetchone()
        if not table:
            return []
        rows = connection.execute(
            """SELECT started_at, finished_at, status, scope_kind, studio_id, category_id,
                      studio, category, discovered, selected, files, errors, destination, listing_url
               FROM run_history ORDER BY started_at DESC LIMIT ?""",
            (int(limit),),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def print_history(limit: int = 20, database: Path | None = None):
    """Print a compact recent-run view for the standalone --history action."""
    database = database or PRIVATE_DATABASE_PATH
    rows = recent_history(database, limit)
    print(terminal_text(f"🗃️ Download history: {database}"))
    if not rows:
        print("No recorded runs yet.")
        return
    for row in rows:
        when = str(row.get("finished_at") or row.get("started_at") or "unknown")[:19].replace("T", " ")
        studio = str(row.get("studio") or f"Studio {row.get('studio_id') or '?'}")
        category = str(row.get("category") or ("All Categories" if row.get("scope_kind") == "studio" else ""))
        scope_name = " - ".join(part for part in (studio, category) if part)
        counts = (f"found {row.get('discovered') if row.get('discovered') is not None else '?'}; "
                  f"selected {row.get('selected') if row.get('selected') is not None else '?'}; "
                  f"files {row.get('files') if row.get('files') is not None else '?'}; "
                  f"errors {row.get('errors') if row.get('errors') is not None else '?'}")
        print(terminal_text(f"🌈 {when}  {row.get('status') or 'unknown':<20}  {scope_name}"))
        print(f"   {counts}")
        print(f"   {row.get('destination') or '(no destination recorded)'}")


def notify_completion(output: Path, status: int) -> bool:
    """Show a topmost Windows completion window so background runs are visible."""
    if os.name != "nt":
        return False
    title = f"Clips4Sale downloader v{VERSION}"
    if status == 0:
        message = f"Download run complete.\n\nSaved in:\n{output}"
        icon = 0x00000040  # MB_ICONINFORMATION
    else:
        message = f"Download run finished with errors.\n\nCheck the report for:\n{output}"
        icon = 0x00000030  # MB_ICONWARNING
    try:
        ctypes.windll.user32.MessageBoxW(
            None, message, title, 0x00000000 | icon | 0x00010000 | 0x00040000
        )
        return True
    except (AttributeError, OSError):
        return False


def run(args, output: Path, ffprobe: str) -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise DownloadError("Install dependencies: python -m pip install -r requirements.txt") from exc
    ffmpeg = shutil.which(getattr(args, "ffmpeg", "ffmpeg"))
    if not ffmpeg and not args.dry_run:
        raise DownloadError("ffmpeg is required to embed video categories. Install FFmpeg or use --ffmpeg PATH.")
    database_started = time.monotonic()
    print(terminal_text("⏳ Opening the resume database..."), file=sys.stderr, flush=True)
    database_path = private_database_path()
    database_backup = None
    database_backup_error = None
    if database_path.is_file():
        try:
            database_backup = automatic_database_backup(database_path)
            if database_backup:
                print(terminal_text(f"🛟 Database backup: {database_backup}"), file=sys.stderr, flush=True)
        except DownloadError as exc:
            database_backup_error = str(exc)
            print(terminal_text(f"⚠️ {exc}"), file=sys.stderr, flush=True)
    ledger = DownloadDatabase(database_path)
    print(terminal_text(f"✅ Resume database ready in {time.monotonic() - database_started:.1f}s"),
          file=sys.stderr, flush=True)
    legacy_databases = [output / DEFAULT_DATABASE_NAME]
    if ledger.path.resolve() == PRIVATE_DATABASE_PATH.resolve():
        legacy_databases[0:0] = [LEGACY_TEMP_DATABASE_PATH, LEGACY_PRIVATE_DATABASE_PATH]
    imported_legacy: list[str] = []
    for legacy_database in dict.fromkeys(path.expanduser() for path in legacy_databases):
        if not legacy_database.is_file() or legacy_database.resolve() == ledger.path.resolve():
            continue
        print(terminal_text(f"🔄 Checking legacy history: {legacy_database}"),
              file=sys.stderr, flush=True)
        legacy_started = time.monotonic()
        if ledger.merge_legacy(legacy_database):
            imported_legacy.append(str(legacy_database))
        print(terminal_text(f"✅ Legacy history check finished in {time.monotonic() - legacy_started:.1f}s"),
              file=sys.stderr, flush=True)
    retry_ids = getattr(args, "_retry_clip_keys", None)
    retry_source = getattr(args, "retry_failures", None)
    if retry_ids is None and retry_source:
        retry_ids, _, _ = retry_ids_from_source(Path(retry_source))
    report: dict = {
        "listing": args.url, "destination": str(output), "database": str(ledger.path),
        "version": VERSION, "pid": os.getpid(),
        "started": datetime.now().isoformat(), "dry_run": args.dry_run,
        "resumed": not getattr(args, "fresh", False),
        "retry_failures_only": bool(retry_source), "clips": [], "errors": [],
    }
    if database_backup:
        report["database_backup"] = str(database_backup)
    if database_backup_error:
        report["database_backup_error"] = database_backup_error

    def ensure_database_backup():
        nonlocal database_backup, database_backup_error
        if database_backup is not None or database_backup_error is not None:
            return
        try:
            database_backup = automatic_database_backup(database_path)
            if database_backup:
                report["database_backup"] = str(database_backup)
        except DownloadError as exc:
            database_backup_error = str(exc)
            report["database_backup_error"] = database_backup_error
            print(terminal_text(f"⚠️ {exc}"), file=sys.stderr, flush=True)

    if imported_legacy:
        report["legacy_databases_imported"] = imported_legacy
    if getattr(args, "clean_old_variants", False):
        report["old_variant_cleanup"] = clean_old_variants(ledger, output)
    ledger.set_metadata(listing=args.url, destination=str(output))
    scope = listing_scope(args.url)
    prior_scope = ledger.previous_scope_activity(scope)
    run_history_id = ledger.start_scope_run(scope, args.url, output)
    report["history_scope"] = {"key": scope.key, "kind": scope.kind,
                               "studio_id": scope.studio_id, "category_id": scope.category_id}
    report["history_run_id"] = run_history_id
    if prior_scope:
        report["prior_scope_activity"] = prior_scope
    # Resolve the durable filelist before importing Playwright or touching a
    # browser profile.  A completed cached listing is enough to resume a run
    # whose files are already present, so that common case should not launch
    # Chrome at all.
    cache_started = time.monotonic()
    existing_listing = ledger.cached_discovery(args.url)
    cache_info = ledger.discovery_cache_info(args.url)
    cached_listing = None if args.refresh_listing else existing_listing
    rescan_previous: list[Clip] | None = (existing_listing[0] if args.refresh_listing and existing_listing else None)
    if existing_listing and not args.dry_run:
        prior_clips, prior_studio, prior_category = existing_listing
        complete_scope_clips, _ = deduplicate(prior_clips)
        cache_is_complete = bool(complete_scope_clips) and all(
            ledger.completed_media(clip) for clip in complete_scope_clips
        )
        if cache_is_complete and not args.refresh_listing:
            completion = ledger.completed_scope_activity(scope) or prior_scope or cache_info or {}
            completed_at = completion.get("finished_at") or completion.get("completed_at") \
                or completion.get("started_at") or "an earlier date"
            if ask_rescan(scope, completed_at, prior_studio, prior_category, headless=args.headless):
                cached_listing = None
                rescan_previous = prior_clips
                report["rescan_requested"] = True
            else:
                report["rescan_requested"] = False
        elif args.refresh_listing:
            report["rescan_requested"] = True
    if prior_scope and not existing_listing:
        when = prior_scope.get("finished_at") or prior_scope.get("started_at") or "an earlier date"
        print(terminal_text(f"⚠️ History reminder: {scope.description} has earlier history from {when}."),
              file=sys.stderr, flush=True)
    print(terminal_text(f"🗃️ Listing cache lookup finished in {time.monotonic() - cache_started:.1f}s"),
          file=sys.stderr, flush=True)
    log_path = None
    log_file = None
    try:
        log_path, log_file = open_run_log()
        report["logfile"] = str(log_path)
    except OSError as exc:
        report["errors"].append(f"Could not create logfile in {LOG_DIRECTORY}: {exc}")
        print(f"Warning: could not create logfile in {LOG_DIRECTORY}: {exc}", file=sys.stderr)
    panel = ProgressPanel(log_file)
    startup_draw = getattr(panel, "draw_status", None)

    def startup_status(text):
        # Startup has no clip/transfer log yet. Record every phase and clone
        # progress update so a stall can be tied to a specific file/operation.
        if log_file:
            log_file.write(f"{datetime.now().isoformat(timespec='seconds')} {text}\n")
            log_file.flush()
        if callable(startup_draw):
            startup_draw(text)
        else:
            panel.status = text
            panel.draw()
    renderer = "ANSI fixed rows" if getattr(panel, "ansi", False) else "plain log mode"
    panel.log(f"🖥️ Status renderer: {renderer}; stdout_tty={getattr(panel, 'stdout_tty', False)}; "
              f"stderr_tty={getattr(panel, 'stderr_tty', False)}")
    startup_status("⏳ Preparing the browser session")
    if cached_listing and not args.dry_run:
        cached_clips, cached_studio, cached_category = cached_listing
        selected, duplicates, failed_ids = prepare_selection(ledger, args, cached_clips)
        pending = [clip for clip in selected if not ledger.completed_media(clip)]
        if not pending:
            report.update(
                discovery_source="database-cache",
                browser_started=False,
                cached_filelist_fast_path=True,
                studio=cached_studio,
                category=cached_category,
                discovered=len(cached_clips),
                studio_id=(selected[0].studio_id if selected else cached_clips[0].studio_id),
                duplicate_editions=duplicates,
                selected=len(selected),
                failed_queued_last=sum((clip.studio_id, clip.id) in failed_ids for clip in selected),
            )
            panel.log(f"🗃️ Reusing {len(cached_clips)} clips from the completed listing cache; no listing rescan.")
            panel.log(f"⚡ Cached filelist is complete; no browser startup required ({len(selected)} clips already downloaded).")
            panel.set_total(len(selected))
            for index, clip in enumerate(selected):
                completed = ledger.completed_media(clip)
                entry = {"clip_id": clip.id, "url": clip.url, "title": clip.title,
                         "quality": quality_score(clip.raw), "files": completed,
                         "errors": [], "resumed": True, "skipped": "already-complete"}
                report["clips"].append(entry)
                panel.log(f"↩️ [{index + 1}/{len(selected)}] Already complete: {clip.title}")
                panel.total.update(1)
                panel.draw()
            report["completed"] = True
            panel.close()
            report["finished"] = datetime.now().isoformat()
            ledger.finish_scope_run(run_history_id, report)
            ensure_database_backup()
            report_path = write_new_json(private_report_path(args.dry_run), report)
            if log_file:
                log_file.write(f"{datetime.now().isoformat(timespec='seconds')} Run report: {report_path}\n")
                log_file.flush()
                log_file.close()
            ledger.close()
            print(f"Run report: {report_path}")
            print(f"Finished: {len(report['clips'])} clips processed; 0 clips with errors.")
            return 0
    browser = None
    context = None
    page = None
    last_browser_url = args.url
    try:
        with sync_playwright() as playwright:
            browser, context = open_browser_context(playwright, args, startup_status)
            try:
                # Persistent contexts normally start with a visible about:blank
                # page. Reusing it keeps the foreground browser tab synchronized
                # with the page that receives the requested listing URL.
                page = run_page(context)
                # One delay history covers browser settling, discovery, and
                # download pacing. Each run starts with its own history.
                pacer = DownloadPacer(panel)
                # Pacing is deliberately independent of the browser driver.
                # A closed/unstable page must not abort an otherwise resumable
                # download merely because the next delay is being displayed.
                cached = cached_listing
                if cached:
                    clips, studio, category = cached
                    report["discovery_source"] = "database-cache"
                    panel.log(f"🗃️ Reusing {len(clips)} clips from the completed listing cache; no listing rescan.")
                else:
                    if not args.headless:
                        startup_status("🌐 Opening the requested listing in the browser")
                        goto(page, args.url, args.headless, pacer=pacer)
                        last_browser_url = page.url
                    clips, studio, category = discover(
                        page, args.url, args, panel, pacer=pacer,
                        previous_clips=rescan_previous,
                        previous_scroll_steps=(cache_info or {}).get("scroll_steps"),
                    )
                    ledger.store_discovery(
                        args.url, clips, studio, category,
                        scroll_steps=getattr(args, "_last_discovery_scroll_steps", None),
                    )
                    if rescan_previous:
                        new_count = getattr(args, "_last_discovery_new_clips", 0)
                        report.update(discovery_source="incremental-rescan", new_clips=new_count,
                                      rescan_stop_reason=getattr(args, "_last_discovery_stop_reason", ""),
                                      rescan_scroll_steps=getattr(args, "_last_discovery_scroll_steps", None))
                        panel.log(f"💾 New-clip scan found {new_count} new clips; merged them with "
                                  f"the {len(rescan_previous)} cached clips.")
                    else:
                        report["discovery_source"] = "browser-scrape"
                        panel.log(f"💾 Stored the complete {len(clips)}-clip listing for future resume attempts.")
                selected, duplicates, failed_ids = prepare_selection(ledger, args, clips)
                report.update(studio=studio, category=category, discovered=len(clips),
                              studio_id=(selected[0].studio_id if selected else (clips[0].studio_id if clips else "")),
                              duplicate_editions=duplicates, selected=len(selected),
                              failed_queued_last=sum((clip.studio_id, clip.id) in failed_ids for clip in selected))
                mode = "; retrying failures only" if retry_ids is not None else "; resuming from the job database"
                panel.log(f"🌈 Found {len(clips)} listings; skipped {len(duplicates)} duplicate editions; "
                          f"{len(selected)} selected{mode}.")
                panel.log(f"🏷️ Filename prefix: {studio}" + (f" - {category}" if category else ""))
                panel.set_total(len(selected))
                for index, clip in enumerate(selected):
                    entry = {"clip_id": clip.id, "url": clip.url, "title": clip.title,
                             "quality": quality_score(clip.raw), "files": [], "errors": []}
                    report["clips"].append(entry)
                    panel.log(f"🎬 [{index + 1}/{len(selected)}] {clip.title}")
                    durations = []
                    unknown_duration = False
                    deferred_by_other_run = False
                    video_already_available = False
                    clip_had_error = False
                    ledger.upsert_clip(clip)
                    completed = ledger.completed_media(clip)
                    if completed:
                        entry["files"] = completed
                        entry["resumed"] = True
                        entry["skipped"] = "already-complete"
                        entry["assets"] = [{"role": item["role"], "path": item["path"]}
                                            for item in completed]
                        panel.log(f"↩️ Already complete; skipped detail/media discovery for {clip.id}.")
                        panel.total.update(1)
                        panel.draw()
                        continue
                    try:
                        inspect_error = None
                        for inspect_attempt in range(args.media_retries + 1):
                            try:
                                raw, assets = inspect_clip(page, clip, args, pacer=pacer)
                                inspect_error = None
                                break
                            except SiteBlocked:
                                raise
                            except Exception as exc:
                                inspect_error = str(exc)
                                if inspect_attempt < args.media_retries:
                                    panel.log(f"🔁 Retry {inspect_attempt + 1}/{args.media_retries} inspecting {clip.id}: {exc}")
                                    continue
                        if inspect_error:
                            raise DownloadError(inspect_error)
                        assets = media_for_download(assets)
                        entry["assets"] = [{"url": m.url, "role": m.role} for m in assets]
                        entry["quality"] = quality_score(raw)
                        file_category = clip_category_name(category, raw)
                        entry["category"] = file_category
                        stem = base_name(output, studio, file_category, clip,
                                         include_category_prefix=getattr(args, "category_prefixes", False))
                        entry["filename_base"] = stem
                        ledger.upsert_clip(clip, file_category, stem)
                        if args.dry_run:
                            panel.log(f"🧪 Would save {len(assets)} media files with base: {stem}")
                        else:
                            with session_for(context, page) as session:
                                for media in assets:
                                    output_stem = media_stem(stem, media.role)
                                    expected = output / (output_stem + (_media_extension(media) or ".media"))
                                    if not ledger.claim_media(clip, media, expected):
                                        old = (ledger.successful_media(clip, media)
                                               or ledger.successful_media_for_role(clip, media.role))
                                        if old:
                                            saved = {"path": old["path"], "role": media.role,
                                                     "bytes": old.get("bytes") or Path(old["path"]).stat().st_size}
                                            for key in ("duration", "width", "height"):
                                                if old.get(key) is not None:
                                                    saved[key] = old[key]
                                            entry["files"].append(saved)
                                            if (media.role == "preview" or media.role.startswith("preview-gif")) \
                                                    and _media_extension(media) in VIDEO_EXTENSIONS:
                                                video_already_available = True
                                                if old.get("duration"):
                                                    durations.append(float(old["duration"]))
                                            panel.log(f"↩️ Already complete: {Path(saved['path']).name}")
                                        else:
                                            deferred_by_other_run = True
                                            entry.setdefault("deferred", []).append({"url": media.url, "role": media.role})
                                            panel.log(f"⏳ Another run owns: {Path(output_stem).name}")
                                        continue
                                    last_error = None
                                    for attempt in range(args.media_retries + 1):
                                        # Keep the original reservation across retries.
                                        # Re-claiming here mistook our own live claim for
                                        # another worker and used to send Windows Ctrl+C.
                                        try:
                                            panel.log(f"📥 Media attempt {attempt + 1}/{args.media_retries + 1} "
                                                      f"({media.role}, clip {clip.id}): {media.url}")
                                            path = download_media(session, media, output, output_stem, clip.url, panel,
                                                                  video_category=file_category,
                                                                  ffmpeg=ffmpeg, ffprobe=ffprobe)
                                            saved = {"path": str(path), "role": media.role, "bytes": path.stat().st_size}
                                            if path.suffix.lower() in VIDEO_EXTENSIONS:
                                                saved["category"] = file_category
                                                saved["category_tag"] = "genre"
                                                try:
                                                    info = probe_video(path, ffprobe)
                                                except Exception:
                                                    unknown_duration = True
                                                    raise
                                                saved.update(info)
                                                durations.append(info["duration"])
                                            ledger.record_success(clip, media, saved)
                                            entry["files"].append(saved)
                                            panel.log(f"📥 Saved: {path.name}")
                                            if path.suffix.lower() in VIDEO_EXTENSIONS:
                                                pacer.video_downloaded()
                                            last_error = None
                                            break
                                        except SiteBlocked as exc:
                                            ledger.record_failure(clip, media, str(exc))
                                            raise
                                        except Exception as exc:
                                            last_error = str(exc)
                                            retrying = attempt < args.media_retries and retryable_media_error(exc)
                                            ledger.record_failure(clip, media, last_error, retrying=retrying)
                                            status = getattr(getattr(exc, "response", None), "status_code", None)
                                            status_text = f"HTTP {status}" if status else type(exc).__name__
                                            entry.setdefault("media_attempt_errors", []).append({
                                                "role": media.role, "url": media.url, "attempt": attempt + 1,
                                                "http_status": status, "error": last_error, "retrying": retrying,
                                            })
                                            panel.log(f"⚠️ Media attempt {attempt + 1}/{args.media_retries + 1} failed "
                                                      f"({media.role}, {status_text}): {media.url}")
                                            if retrying:
                                                panel.log(f"🔁 Retry {attempt + 1}/{args.media_retries} for {output_stem}: {exc}")
                                                continue
                                            break
                                    if last_error:
                                        clip_had_error = True
                                        entry["errors"].append(f"{media.role} {media.url}: {last_error}")
                                        panel.log(f"⚠️ Media error: {last_error}; continuing with remaining media/queue.")
                            if not any(m.role == "preview" or m.role.startswith("preview-gif") for m in assets):
                                entry["errors"].append("No preview video or GIF was exposed for this clip.")
                            if not deferred_by_other_run:
                                ledger.finish_clip(clip, assets)
                    except SiteBlocked:
                        raise
                    except Exception as exc:
                        clip_had_error = True
                        entry["errors"].append(str(exc))
                        ledger.mark_clip_failed(clip, str(exc))
                        panel.log(f"⚠️ Clip error: {exc}")
                    finally:
                        panel.total.update(1)
                        panel.draw()
                    if index + 1 < len(selected):
                        # Probe the actual saved preview, never the paid clip's advertised duration.
                        seconds = inter_clip_wait(video_already_available, deferred_by_other_run,
                                                  durations, unknown_duration, args, clip_had_error)
                        entry["wait_seconds"] = seconds
                        if seconds > 0:
                            if clip_had_error:
                                reason = "failed media; continuing queue"
                            elif deferred_by_other_run:
                                reason = "media owned by another active run"
                            elif durations:
                                reason = "measured preview duration"
                            else:
                                reason = "unknown preview duration"
                            def record_wait(actual_seconds):
                                entry["wait_seconds"] = actual_seconds
                                panel.log(f"⏳ Waiting {actual_seconds:.2f}s before the next clip ({reason}).")

                            bounds = (REUSED_VIDEO_PAUSE_RANGE if not args.dry_run
                                      and (clip_had_error or deferred_by_other_run) else None)
                            pacer.pause(seconds, bounds=bounds, on_scheduled=record_wait)
                report["completed"] = True
            except (KeyboardInterrupt, EOFError):
                # Release the terminal immediately, before browser/profile
                # cleanup can wait. The outer finally can safely close again.
                panel.close()
                raise
            finally:
                if page is not None:
                    try:
                        current_url = page.url
                        if str(current_url).startswith(("http://", "https://")):
                            last_browser_url = current_url
                    except Exception:
                        pass
                close_browser_resources(context, browser, report)
                if not args.no_persistent_login and getattr(args, "_profile_actual", None):
                    preferred = (Path(args.profile_dir).expanduser().resolve()
                                 if args.profile_dir else DEFAULT_PROFILE_DIR)
                    preserve_login_snapshot(preferred, Path(args._profile_actual), startup_status)
                release_profile_lease(getattr(args, "_profile_lease", None))
                leave_browser_open(args, last_browser_url, report, panel)
    except BaseException as exc:
        report["completed"] = False
        if isinstance(exc, KeyboardInterrupt):
            interruption = "Interrupted by SIGINT/Ctrl+C (signal source is not known)"
        elif isinstance(exc, SystemExit):
            interruption = f"Downloader exited during the run with status {exc.code!r}"
        else:
            interruption = str(exc) or type(exc).__name__
        trace = traceback.format_exc()
        report["errors"].append(interruption)
        report["exception_traceback"] = trace
        if log_file:
            log_file.write(f"{datetime.now().isoformat(timespec='seconds')} ❌ {interruption}\n")
            log_file.write(trace)
            if not trace.endswith("\n"):
                log_file.write("\n")
            log_file.flush()
        raise
    finally:
        panel.close()
        report["finished"] = datetime.now().isoformat()
        ledger.finish_scope_run(run_history_id, report)
        ensure_database_backup()
        report_path = write_new_json(private_report_path(args.dry_run), report)
        if log_file:
            log_file.write(f"{datetime.now().isoformat(timespec='seconds')} Run report: {report_path}\n")
            log_file.flush()
            log_file.close()
        ledger.close()
        print(f"Run report: {report_path}")
    failures = sum(bool(c["errors"]) for c in report["clips"])
    print(f"Finished: {len(report['clips'])} clips processed; {failures} clips with errors.")
    return 1 if failures else 0


def positive_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("must be a finite number greater than zero")
    return number


def positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return number


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    p.add_argument("--history", nargs="?", const=20, type=positive_int, metavar="N",
                   help="Show the most recent N runs and exit (default: 20)")
    p.add_argument("url", nargs="?", help="Clips4Sale studio/category listing URL (read from retry report when omitted)")
    p.add_argument("--output", type=Path, help="Add this destination to the mandatory numbered menu")
    p.add_argument("--retry-failures", "--rerun-failures", type=Path, metavar="REPORT_OR_DB",
                   help="Re-run only clips recorded as failed in a prior JSON report or clips4sale.db")
    p.add_argument("--studio-name", help="Override the studio filename prefix")
    p.add_argument("--category-name", help="Override the category filename prefix")
    p.add_argument("--category-prefixes", action="store_true",
                   help="Opt in to sortable abbreviations such as 'sph -' in filenames (off by default)")
    p.add_argument("--browser", choices=("chrome", "msedge", "chromium"), default="chrome")
    p.add_argument("--profile-dir", type=Path,
                   help=r"Reusable browser profile directory (default: %%APPDATA%%\Clips4SaleDownloader\browser-profile)")
    p.add_argument("--no-persistent-login", action="store_true",
                   help="Use an isolated browser session; login will not be retained")
    p.add_argument("--headless", action="store_true", help="Hide browser; cannot interact with site prompts")
    p.add_argument("--pause-before-scrape", action="store_true",
                   help="Wait for Enter before scanning (optional manual login/site-overlay setup)")
    p.add_argument("--close-browser-on-exit", action="store_true",
                   help="Close the headed browser when the job ends instead of leaving it open at its last page")
    p.add_argument("--dry-run", action="store_true", help="Discover clips/media and write a plan; save no media")
    p.add_argument("--max-clips", type=positive_int, help="Limit selected downloads AFTER full discovery/deduplication")
    p.add_argument("--scroll-delay", type=positive_float, default=2.0, help="Seconds between scrolls (default: 2)")
    p.add_argument("--stable-rounds", type=positive_int, default=8, help="Quiet bottom checks before completion (default: 8)")
    p.add_argument("--max-scrolls", type=positive_int, default=2000, help="Abort if discovery exceeds this limit")
    p.add_argument("--page-delay", type=positive_float, default=2.0, help="Seconds to settle each clip page")
    p.add_argument("--fallback-wait", type=positive_float, default=30.0, help="Wait when preview duration is unavailable")
    p.add_argument("--media-retries", "--retries", type=positive_int, default=DEFAULT_MEDIA_RETRIES,
                   help="Additional attempts for each failed media item (default: 1)")
    p.add_argument("--clean-old-variants", action="store_true",
                   help="Preview old lower-resolution still variants and offer to recycle only redundant copies")
    p.add_argument("--refresh-listing", action="store_true",
                   help="Check for new clips using the cached listing's previous boundary")
    p.add_argument("--rescan-known-streak", type=positive_int, default=RESCAN_KNOWN_STREAK,
                   help=f"Consecutive cached clips needed to end a newest-first rescan (default: {RESCAN_KNOWN_STREAK})")
    p.add_argument("--fresh", action="store_true",
                   help="Do not describe this invocation as a resume; existing successful DB items are still protected")
    p.add_argument("--no-completion-notification", action="store_true",
                   help="Do not show the topmost Windows completion window")
    p.add_argument("--ffprobe", default="ffprobe", help="ffprobe command or absolute executable path")
    p.add_argument("--ffmpeg", default="ffmpeg", help="ffmpeg command or absolute path for lossless category tagging")
    return p


def main(argv=None) -> int:
    p = parser()
    args = p.parse_args(argv)
    # clairecjs_utils.claire_console installs a SIGINT handler that calls
    # sys.exit(0). Restore Python's normal handler so Ctrl+C is reported as a
    # real KeyboardInterrupt and the resumable-run report is unambiguous.
    restore_default_sigint_handler()
    print(terminal_text(f"🌈 Clips4Sale preview downloader v{VERSION}"))
    if args.history is not None:
        try:
            print_history(args.history)
            return 0
        except Exception as exc:
            print(f"Error reading history: {exc}", file=sys.stderr)
            return 1
    retry_destination = None
    if args.retry_failures:
        try:
            retry_ids, retry_url, retry_destination = retry_ids_from_source(args.retry_failures)
            args._retry_clip_keys = retry_ids
            if not args.url:
                args.url = retry_url
            if args.output is None and retry_destination:
                args.output = retry_destination
        except DownloadError as exc:
            p.error(str(exc))
    if not args.url:
        p.error("Provide a listing URL, or use --retry-failures with a report/database that contains one.")
    parsed = urlsplit(args.url)
    if (parsed.scheme != "https" or parsed.hostname not in ("clips4sale.com", "www.clips4sale.com")
            or not re.search(r"/studio/\d+", parsed.path) or CLIP_PATH.search(parsed.path)):
        p.error("Provide an HTTPS Clips4Sale studio/category LISTING URL.")
    try:
        ffprobe = shutil.which(args.ffprobe)
        if not ffprobe and not args.dry_run:
            raise DownloadError("ffprobe is required to measure the downloaded previews. Install FFmpeg or use --ffprobe PATH.")
        output = select_destination(args.output)
        status = run(args, output, ffprobe or args.ffprobe)
        if not args.headless and not args.no_completion_notification:
            notify_completion(output, status)
        return status
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled. Completed and partial files have been preserved.", file=sys.stderr)
        return 130
    except SystemExit as exc:
        if exc.code in (None, 0, 130):
            print("\nCancelled. Completed and partial files have been preserved.", file=sys.stderr)
            return 130
        raise
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
