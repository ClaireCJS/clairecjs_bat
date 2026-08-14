#!/usr/bin/env python3
"""
Audit an incoming music-processing batch and produce a proposal report.

The audit itself is read-only. Interactive approvals and explicit opt-in flags
can apply narrowly defined repairs, with backups, Recycle Bin safety, narrated
network artwork lookup, and post-write re-auditing.
"""

from __future__ import annotations

import argparse
import colorsys
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime
from difflib import SequenceMatcher
import html
import hashlib
import io
import json
import math
import os
import random
import re
import shutil
import ssl
import sqlite3
import stat
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from collections import Counter, defaultdict
from contextlib import ExitStack, contextmanager, nullcontext
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Callable, NoReturn

# USER CONFIGURATION ---------------------------------------------------------
# Published releases are deliberately separate from the timestamped safety
# backups that the auditor makes before replacements. Update both values only
# when publishing a new named release.
AUDIT_MUSIC_BATCH_VERSION = "v146"
AUDIT_MUSIC_BATCH_RELEASE_NAME = "direct-chafa-terminal-waveforms"
AUDIT_MUSIC_BATCH_RELEASE_DATE = "2026-08-14"

# Set this to a full executable path only when automatic discovery cannot find
# your preferred image viewer. The V key first honors openimage.bat, then this
# value, then IrfanView found on PATH or in established portable paths.
IMAGE_VIEWER_EXECUTABLE: str | None = None

# Set this to a full executable path only when waveform review cannot discover
# Adobe Audition, Cool Edit, Sound Forge, Audacity, or another audio editor.
AUDIO_EDITOR_EXECUTABLE: str | None = None

# Artwork previews consume the terminal while retaining these rows for status,
# the approval prompt, and a possible IrfanView-open message.
ART_PREVIEW_RESERVED_TEXT_ROWS = 14
ART_PREVIEW_INDENT_COLUMNS = 12
ART_PREVIEW_RIGHT_MARGIN_COLUMNS = 2
# Scale artwork previews relative to the live geometry calculated by the shared
# claire_terminal_geometry helper.  1.00 uses its full fitted size; 0.90 leaves
# a little breathing room around artwork without changing waveform previews.
# The viewer is intentionally compact: 0.23 is 30% smaller than the previous
# 0.33 setting while retaining enough detail for artwork approval.
ART_PREVIEW_SCALE = 0.23
# Artwork review previews keep the current height but are intentionally wider.
# Width is doubled after the normal scale calculation, but never allowed to
# exceed three times the chosen preview height.
ART_PREVIEW_WIDTH_MULTIPLIER = 2.0
ART_PREVIEW_MAX_WIDTH_TO_HEIGHT = 3.0

# Built-in behavior defaults apply when no adjacent configuration file exists.
# Use --configure-defaults to create/update that file interactively.
BEHAVIOR_CONFIG_FILENAME = "audit_music_batch.config.json"
BUILTIN_DEFAULT_EMBED_LYRICS = True
BUILTIN_DEFAULT_FIND_COVER = False
BUILTIN_DEFAULT_CHECK_SILENCE = True
BUILTIN_DEFAULT_SILENCE_THRESHOLD_SECONDS = 10.0
# ReplayGain adjustments inside this ±dB window are effectively neutral and
# are not offered for destructive sample-data baking. Change this one value to
# make both the folder-wide workflow and the per-file B option more/less strict.
REPLAYGAIN_BAKE_THRESHOLD_DB = 0.05
SILENCE_DETECT_NOISE_DB = -50
SILENCE_ANALYSIS_WORKERS = max(2, min(8, os.cpu_count() or 4))
# Restore v113's known-good width-driven renderer at exactly half its original
# values: ordinary 0.60 -> 0.30; comparison 0.80 -> 0.40.  Raster height is not
# independently scaled or forced; it follows the 2000x700 JPEG aspect ratio.
WAVEFORM_REVIEW_WIDTH_SCALE = 0.80
# A genuine comparison is one 80%-wide composite containing two side-by-side
# panels, so each before/after waveform occupies approximately 40%.
WAVEFORM_COMPARISON_WIDTH_SCALE = 0.80
WAVEFORM_REVIEW_HEIGHT_SCALE = 0.80
WAVEFORM_COMPARISON_HEIGHT_SCALE = 0.40
# Compatibility aliases retained for older call sites/tests. Normal waveform
# review keeps horizontal and vertical scales identical.
WAVEFORM_REVIEW_SCALE = WAVEFORM_REVIEW_WIDTH_SCALE
WAVEFORM_COMPARISON_SCALE = WAVEFORM_COMPARISON_WIDTH_SCALE
WAVEFORM_REVIEW_WIDTH_FRACTION = WAVEFORM_REVIEW_WIDTH_SCALE
WAVEFORM_COMPARISON_WIDTH_FRACTION = WAVEFORM_COMPARISON_WIDTH_SCALE
# Legacy constants retained for compatibility with older tests/helpers. Runtime
# sizing no longer starts from a fixed waveform-row height and no multiplier is
# applied after the classic geometry is scaled.
WAVEFORM_PREVIEW_HEIGHT_ROWS = 6
WAVEFORM_FINAL_HEIGHT_MULTIPLIER = 1
WAVEFORM_REVIEW_MIN_GRAPH_ROWS = 2
# Compatibility constants retained for historical tests/calibration reports.
WAVEFORM_TERMINAL_CELL_ASPECT = 0.50
WAVEFORM_SIXEL_SAFETY_ROWS = 1
WAVEFORM_SIXEL_CURSOR_ROW_FACTOR = 1
WAVEFORM_SIXEL_COLORS = 64
_WAVEFORM_SIXEL_CURSOR_CELL_HEIGHT_PIXELS: int | None = None
WAVEFORM_COMPARISON_GAP_SOURCE_PIXELS = 60
WAVEFORM_COMPARISON_PROMPT_PAD_SOURCE_PIXELS = 120
# Requested v139 diagnostic exaggeration: every currently-rendered waveform
# is 25% wider and 4x taller.  The width increase itself adds 1.25x height to
# aspect-preserving images, so normal plots need a 3.2x vertical stretch and
# the contact-sheet source needs its panel scale raised by 3.2x.
WAVEFORM_REVIEW_VERTICAL_STRETCH = 1.0
WAVEFORM_COMPARISON_PANEL_HEIGHT_SCALE = 1.0
NO_ARGUMENT_MUSIC_SCAN_MAX_DEPTH = 5
WAVEFORM_JPEG_WIDTH = 2000
WAVEFORM_JPEG_HEIGHT = 700
WAVEFORM_METRICS_GUTTER_WIDTH = 260
WAVEFORM_PLOT_WIDTH = WAVEFORM_JPEG_WIDTH - WAVEFORM_METRICS_GUTTER_WIDTH
WAVEFORM_SILENCE_MIN_SECONDS = 0.1
WAVEFORM_APPROVAL_DATABASE_MAX_BYTES = 50 * 1024 * 1024
WAVEFORM_APPROVAL_DATABASE_FILENAME = "waveform_reviews.sqlite3"
AUDIT_CACHE_FILENAME = "audit_music_batch.sqlite3"
REPLAYGAIN_TIMING_DATABASE_FILENAME = "replaygain_timings.sqlite3"
WAVEFORM_CHANNEL_COLORS = (
    "0x55dcff",  # cyan: left/first channel
    "0xb68cff",  # violet: right/second channel
    "0x78e6a3",  # mint: additional channels
    "0xffb45c",  # amber: additional channels
    "0xff779f",  # rose: additional channels
    "0x79b9ff",  # blue: additional channels
)
LRC2SRT_GENERATED_MARKER = "claire-sawyer-lrc2srt-converter-marker"


def audit_cache_path() -> Path:
    """Return the per-user persistent cache location for successful audits."""
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
    if base:
        return Path(base) / "ClaireCJS" / AUDIT_CACHE_FILENAME
    return Path.home() / ".clairecjs" / AUDIT_CACHE_FILENAME




def replaygain_timing_database_path() -> Path:
    """Return the write-only timing telemetry database used for later modeling."""
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
    if base:
        return Path(base) / "ClaireCJS" / REPLAYGAIN_TIMING_DATABASE_FILENAME
    return Path.home() / ".clairecjs" / REPLAYGAIN_TIMING_DATABASE_FILENAME


def record_replaygain_timing(
    path: Path,
    *,
    tool: str,
    elapsed_seconds: float,
    succeeded: bool,
) -> None:
    """Append one timing sample without ever reading historical samples."""
    try:
        size_bytes = path.stat().st_size
    except OSError:
        size_bytes = 0
    try:
        db_path = replaygain_timing_database_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(db_path) as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS replaygain_timings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recorded_at TEXT NOT NULL,
                    tool TEXT NOT NULL,
                    extension TEXT NOT NULL,
                    path TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    elapsed_seconds REAL NOT NULL,
                    succeeded INTEGER NOT NULL
                )
                """
            )
            db.execute(
                """
                INSERT INTO replaygain_timings(
                    recorded_at, tool, extension, path, size_bytes,
                    elapsed_seconds, succeeded
                ) VALUES(?,?,?,?,?,?,?)
                """,
                (
                    datetime.now().isoformat(timespec="seconds"),
                    tool,
                    path.suffix.casefold(),
                    str(path),
                    int(size_bytes),
                    float(elapsed_seconds),
                    1 if succeeded else 0,
                ),
            )
    except Exception:
        # Telemetry must never interfere with the music operation.
        pass


def compact_elapsed(seconds: float) -> str:
    """Render a short HH:MM:SS/MM:SS duration for progress and summaries."""
    total = max(0, int(round(float(seconds))))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:d}:{minutes:02d}:{secs:02d}" if hours else f"{minutes:02d}:{secs:02d}"


def cached_silence_intervals(
    path: Path, threshold: float, ffmpeg_executable: str
) -> list[dict[str, Any]] | None:
    """Return a prior successful silence result when the file is unchanged."""
    try:
        stat = path.stat()
        key = (str(path.resolve()), stat.st_size, stat.st_mtime_ns, float(threshold), SILENCE_DETECT_NOISE_DB)
        db_path = audit_cache_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(db_path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS silence_cache (path TEXT, size INTEGER, mtime_ns INTEGER, threshold REAL, noise REAL, intervals TEXT, PRIMARY KEY(path,size,mtime_ns,threshold,noise))")
            row = db.execute("SELECT intervals FROM silence_cache WHERE path=? AND size=? AND mtime_ns=? AND threshold=? AND noise=?", key).fetchone()
            if row:
                return json.loads(row[0])
    except Exception:
        row = None
    intervals = detect_silence_intervals(path, threshold, ffmpeg_executable=ffmpeg_executable)
    try:
        with sqlite3.connect(audit_cache_path()) as db:
            db.execute("INSERT OR REPLACE INTO silence_cache(path,size,mtime_ns,threshold,noise,intervals) VALUES(?,?,?,?,?,?)", (*key, json.dumps(intervals)))
            db.execute("DELETE FROM silence_cache WHERE path NOT IN (SELECT DISTINCT path FROM silence_cache)")
    except Exception:
        pass
    return intervals

# Load the leaf module directly.  The legacy clairecjs_utils package initializer
# imports optional console dependencies that an otherwise read-only audit should
# not require merely to display a progress bar.
_SCRIPT_DIR = Path(__file__).resolve().parent
_PROGRESS_LIBRARY_SEARCH_DIRS = (
    _SCRIPT_DIR,
    _SCRIPT_DIR / "clairecjs_util",
    _SCRIPT_DIR / "clairecjs_utils",
)
for _progress_dir in _PROGRESS_LIBRARY_SEARCH_DIRS:
    if (_progress_dir / "claire_progressbar.py").is_file():
        sys.path.insert(0, str(_progress_dir))
        break
try:
    from claire_progressbar import progress_bar, rainbow_hex, spaced_unit
    _PROGRESS_IMPORT_ERROR: str | None = None
except Exception as _progress_exc:
    _PROGRESS_IMPORT_ERROR = (
        f"{type(_progress_exc).__name__}: {_progress_exc}"
    )

    def progress_bar(**_kwargs):
        """Fallback context when the optional shared progress library is absent."""
        return nullcontext(None)

    def spaced_unit(unit: str) -> str:
        """Preserve tqdm's expected leading-space unit convention."""
        cleaned = str(unit).strip()
        return f" {cleaned}" if cleaned else ""

    def rainbow_hex(position: float) -> str:
        """Small stdlib fallback retained for diagnostics and unit-test output."""
        red, green, blue = colorsys.hsv_to_rgb(float(position) % 1.0, 1.0, 1.0)
        return f"#{round(red * 255):02x}{round(green * 255):02x}{round(blue * 255):02x}"

# The geometry helper may travel alongside the script, inside either spelling
# of the shared utilities folder, or in the canonical library location.
# Import its leaf module directly; the package initializer is intentionally
# avoided because this utility must still run in minimal copied installations.
_TERMINAL_GEOMETRY_SEARCH_DIRS = (
    Path.cwd(),
    Path.cwd() / "clairecjs_util",
    Path.cwd() / "clairecjs_utils",
    _SCRIPT_DIR,
    _SCRIPT_DIR / "clairecjs_util",
    _SCRIPT_DIR / "clairecjs_utils",
    Path(r"C:\clairecjs_utils"),
    Path(r"C:\BAT\clairecjs_utils"),
)
for _geometry_dir in _TERMINAL_GEOMETRY_SEARCH_DIRS:
    if (_geometry_dir / "claire_terminal_geometry.py").is_file():
        sys.path.insert(0, str(_geometry_dir))
        break
try:
    from claire_terminal_geometry import query_terminal_geometry
except Exception:
    query_terminal_geometry = None


AUDIO_EXTS = {".mp3", ".flac"}
ALLOWED_AUDIO_EXTS = {".mp3", ".flac", ".wav"}
KNOWN_AUDIO_EXTS = {
    ".aac",
    ".aiff",
    ".ape",
    ".au",
    ".flac",
    ".m4a",
    ".mid",
    ".midi",
    ".mod",
    ".mp2",
    ".mp3",
    ".mp4",
    ".ogg",
    ".opus",
    ".ra",
    ".s3m",
    ".shn",
    ".stm",
    ".wav",
    ".wma",
    ".wv",
    ".xm",
}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
FRONT_ART_STEMS = ("cover", "folder")
FRONT_ART_EXTENSION_PRIORITY = (".jpg", ".jpeg", ".png", ".webp", ".gif")
NON_FRONT_ART_STEMS = {
    "artist",
    "back",
    "band",
    "booklet",
    "cd",
    "disc",
    "inlay",
    "inside",
    "liner",
    "logo",
    "matrix",
    "medium",
    "obi",
    "proof",
    "spine",
    "tray",
    "vinyl",
}
LYRIC_EXTS = {".txt", ".lrc", ".srt"}
SIDECAR_EXTS = IMAGE_EXTS | LYRIC_EXTS | {".log", ".json", ".bak"}
CANONICAL_FILENAME_MARKERS = {
    "(instrumental)": "[instrumental]",
    "(semi-instrumental)": "[semi-instrumental]",
    "(semi-music)": "[semi-music]",
    "(semimusic)": "[semi-music]",
    "(non-music)": "[non-music]",
    "(nonmusic)": "[non-music]",
    "[nonmusic]": "[non-music]",
    "(bonus track)": "[bonus track]",
    "(vinyl rip)": "[vinyl rip]",
    "(denoised)": "[denoised]",
    "(hissy)": "[hissy]",
    "(sl hissy)": "[sl hissy]",
    "(v sl hissy)": "[v sl hissy]",
    "(lq)": "[LQ]",
    "(mq)": "[MQ]",
    "(mlq)": "[MLQ]",
    "(pops!)": "[pops!]",
}
CANONICAL_RENAME_EXTS = AUDIO_EXTS | LYRIC_EXTS | IMAGE_EXTS | {
    ".bak",
    ".json",
    ".log",
}
PLAYLIST_EXTS = {".m3u", ".m3u8"}
GENERIC_ARTIST_FOLDER_NAMES = {
    "albums",
    "downloads",
    "incoming",
    "misc",
    "music",
    "new",
    "ready-for-tagging",
    "ready-for-tagging-and-transcribed",
    "singles",
    "soulseek",
    "unknown",
    "various artists",
}
SPECIAL_ARTIST_CHILD_FOLDERS = {
    "misc", "covers", "tributes", "collaborations", "collabs",
    "singles", "demos", "live", "remixes", "soundtracks",
}
ARCHIVE_HINTS = (
    "archival",
    "archive",
    "original-unmerged",
    "unmerged",
    "original-unprocessed",
    "unprocessed",
    "not-for-play",
    "deprecated",
)
DO_NOT_PLAY_LINE = (
    ":do not play,--changer,--changerrecent,--changerrecent to learn,--party,"
    "--preferred,--tolerable,--pretty good,--concert,--concertnext,--concertold,"
    "--concertrecent,--CRTL,--1980's party,--Christmas"
)
APPROVAL_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
MUSICBRAINZ_API_ROOT = "https://musicbrainz.org/ws/2"
COVER_ART_ARCHIVE_ROOT = "https://coverartarchive.org"
BANDCAMP_SEARCH_ROOT = "https://bandcamp.com/search"
DISCOGS_API_ROOT = "https://api.discogs.com"
ITUNES_SEARCH_ROOT = "https://itunes.apple.com/search"
COVER_HTTP_TIMEOUT_SECONDS = 30
COVER_MAX_DOWNLOAD_BYTES = 100 * 1024 * 1024
COVER_USER_AGENT = (
    "audit_music_batch.py/1.0 (ClioCJS@gmail.com)"
)
_LAST_MUSICBRAINZ_REQUEST_AT = 0.0
EXECUTABLE_CATEGORIES = {
    "adobe_xmp",
    "archive_incomplete_attrib",
    "archive_missing_attrib",
    "archive_missing_marker",
    "all_caps_album_title",
    "bare_marker",
    "embedded_art_without_sidecar",
    "embedded_lyrics_outdated",
    "excessive_silence",
    "karaoke_not_embedded",
    "missing_srt_from_lrc_txt",
    "newer_lrc_needs_srt_backfill",
    "missing_embedded_art",
    "corrupted_legacy_id3_frames",
    "missing_replaygain",
    "missing_album",
    "multiple_embedded_artworks",
    "plain_lyrics_not_embedded",
    "read_only_audio",
    "simplify_punk_genre",
    "redundant_album_artist_filename_group",
    "filename_title_capitalization_group",
    "filename_marker_style",
    "smaller_numbered_image_duplicate",
    "stale_transcription_marker",
    "tagrename_m3u8",
    "temporary_batch_file",
    "vad_scratch_srt",
    "wav_remaining",
}
GROUPED_RENAME_CATEGORIES = {
    "redundant_album_artist_filename_group",
    "filename_title_capitalization_group",
}
ROOT_WIDE_ACTION_CATEGORIES = {
    "missing_srt_from_lrc_txt",
    "missing_replaygain",
}
ACTION_PROMPT_QUESTIONS = {
    "all_caps_album_title": (
        "Rename this all-caps album title with normal title capitalization now?"
    ),
    "adobe_xmp": "Send this Adobe XMP sidecar to the Recycle Bin now?",
    "archive_incomplete_attrib": (
        "Add the standard do-not-play line to attrib.lst now?"
    ),
    "archive_missing_attrib": (
        "Create attrib.lst with the standard do-not-play line now?"
    ),
    "archive_missing_marker": "Create the standard archive marker file now?",
    "bare_marker": "Send this bare marker file to the Recycle Bin now?",
    "embedded_art_without_sidecar": (
        "Extract the embedded artwork to an image sidecar now?"
    ),
    "embedded_lyrics_outdated": (
        "Refresh the embedded lyrics and timed karaoke from the regenerated "
        "sidecar files now?"
    ),
    "excessive_silence": (
        "Open this audio file in the configured editor to fix the excessive "
        "silence now?"
    ),
    "karaoke_not_embedded": (
        "Embed the timed karaoke lyrics into this audio file now?"
    ),
    "newer_lrc_needs_srt_backfill": (
        "Regenerate this older SRT from the newer MiniLyrics LRC now?"
    ),
    "missing_embedded_art": (
        "Use the available sidecar—or search for a verified release artwork "
        "set—and embed only its Front image now?"
    ),
    "corrupted_legacy_id3_frames": (
        "Remove the clearly corrupted legacy ID3 frames from this audio file now?"
    ),
    "missing_replaygain": "Run ReplayGain on this folder now?",
    "missing_srt_from_lrc_txt": "Run Lyric/Karaoke Fix for this folder now?",
    "multiple_embedded_artworks": (
        "Export all artwork to sidecars and keep only the front cover embedded now?"
    ),
    "plain_lyrics_not_embedded": (
        "Embed the plain lyrics into this audio file now?"
    ),
    "read_only_audio": "Clear this audio file's read-only attribute now?",
    "simplify_punk_genre": (
        "Choose a cleaner punk-family genre for this audio file now?"
    ),
    "redundant_album_artist_filename_group": (
        "Rename this album file group to remove the redundant artist name now?"
    ),
    "filename_title_capitalization_group": (
        "Rename this album file group to normalize track separators and "
        "song-title capitalization now?"
    ),
    "filename_marker_style": (
        "Rename this file to the proposed canonical marker spelling now?"
    ),
    "smaller_numbered_image_duplicate": (
        "Send this smaller artwork duplicate to the Recycle Bin now?"
    ),
    "stale_transcription_marker": (
        "Send this stale transcription marker to the Recycle Bin now?"
    ),
    "tagrename_m3u8": (
        "Send this Tag&Rename preview sidecar to the Recycle Bin now?"
    ),
    "temporary_batch_file": (
        "Send this temporary batch file to the Recycle Bin now?"
    ),
    "vad_scratch_srt": (
        "Send this VAD scratch SRT sidecar to the Recycle Bin now?"
    ),
    "wav_remaining": (
        "Convert this WAV to FLAC, carry forward available metadata, lyrics, "
        "and approved artwork, then audit the new FLAC now?"
    ),
}
PROMPT_NOUN_PHRASES = (
    "all-caps album title",
    "regenerated sidecar files",
    "configured editor",
    "excessive silence",
    "MiniLyricsFix",
    "batch root",
    "embedded lyrics",
    "proposed canonical marker spelling",
    "standard archive marker file",
    "standard do-not-play line",
    "ARGT ReplayGain workflow",
    "Tag&Rename preview sidecar",
    "available front-cover sidecar",
    "release artwork",
    "downloaded artwork image",
    "Front artwork image",
    "supplied image part",
    "approved image part",
    "VAD scratch SRT sidecar",
    "smaller artwork duplicate",
    "stale transcription marker",
    "multiple embedded artworks",
    "timed karaoke lyrics",
    "WAV",
    "FLAC",
    "available metadata",
    "approved artwork",
    "ReplayGain",
    "newer MiniLyrics LRC",
    "older SRT",
    "temporary batch file",
    "Adobe XMP sidecar",
    "read-only attribute",
    "embedded artwork",
    "bare marker file",
    "all artwork",
    "front cover",
    "image sidecar",
    "plain lyrics",
    "audio file",
    "album files",
    "artist name",
    "attrib.lst",
    "Recycle Bin",
    "sidecars",
    "folder",
    "Album value",
    "ENTER",
)
ANSI = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "cyan": "\033[36m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "white": "\033[37m",
    "dim": "\033[2m",
    "faint": "\033[2m",
    "italic": "\033[3m",
    "blink": "\033[5m",
    "erase_line": "\033[2K",
    "erase_to_eol": "\033[K",
}
ANSI_DOUBLE_HEIGHT_TOP = "\033#3"
ANSI_DOUBLE_HEIGHT_BOTTOM = "\033#4"

ENUMERATION_PROGRESS_FORMAT = (
    "{desc:<24.24}: {n:>7,.0f} files found"
    " • {elapsed} elapsed • {rate_fmt}"
)
ENUMERATION_PROGRESS_FORMAT = "{desc:<24.24}: {n:>7,.0f} files found • {elapsed:>8} elapsed • ETA --:--:-- • {rate_fmt:>12}"
AUDIT_PROGRESS_FORMAT = (
    "{desc}: {percentage:3.0f}%|{bar}| "
    "{n:>7,.0f}/{total:>7,.0f}"
    " • {elapsed}{postfix}"
)
AUDIT_PROGRESS_FORMAT = "{desc:<24.24}: {percentage:3.0f}%|{bar}| {n:>7,.0f}/{total:>7,.0f} • {elapsed:>8} • ETA {remaining:>8} • {rate_fmt:>12}{postfix}"
FILE_PROGRESS_FORMAT = "{desc:<24.24}: {percentage:3.0f}%|{bar}| {n:>7,.0f}/{total:>7,.0f} files • {elapsed:>8} • ETA {remaining:>8} • {rate_fmt:>12}"
ITEM_PROGRESS_FORMAT = "{desc:<24.24}: {percentage:3.0f}%|{bar}| {n:>7,.0f}/{total:>7,.0f} • {elapsed:>8} • ETA {remaining:>8} • {rate_fmt:>12}"
REPLAYGAIN_PROGRESS_FORMAT = "{desc:<24.24}: {percentage:3.0f}%|{bar}| • {elapsed:>8}{postfix}"
def collision_safe_path(
    desired: Path, reserved: set[Path] | None = None
) -> Path:
    """Return an unused path, adding `` (1)``, `` (2)``, and so on."""
    occupied = reserved or set()
    if not desired.exists() and desired not in occupied:
        return desired
    suffix = desired.suffix
    stem = desired.name[: -len(suffix)] if suffix else desired.name
    index = 1
    while True:
        candidate = desired.with_name(f"{stem} ({index}){suffix}")
        if not candidate.exists() and candidate not in occupied:
            return candidate
        index += 1


def replacement_backup_path(
    path: Path, timestamp: str | None = None
) -> Path:
    """Choose the required timestamped sibling backup path for ``path``."""
    stamp = timestamp or datetime.now().strftime("%Y%m%d%H%M")
    desired = path.with_name(
        f"{path.name}.bak.{stamp}.replaced-by-chatgpt.bak"
    )
    return collision_safe_path(desired)


def backup_before_inline_replacement(
    path: Path, timestamp: str | None = None
) -> Path:
    """Copy and verify ``path`` before any in-place content/tag replacement."""
    if not path.is_file():
        raise FileNotFoundError(f"Cannot back up missing file: {path}")
    backup = replacement_backup_path(path, timestamp)
    shutil.copy2(path, backup)
    if not backup.is_file() or backup.stat().st_size != path.stat().st_size:
        raise RuntimeError(f"Replacement backup verification failed: {backup}")
    return backup


def recycle_path(path: Path) -> Path:
    """Send ``path`` to the OS Recycle Bin; never fall back to unlink/rmtree."""
    if not path.exists():
        raise FileNotFoundError(f"Cannot recycle missing path: {path}")
    if send2trash is not None:
        send2trash(str(path))
    elif os.name == "nt":
        import ctypes
        from ctypes import wintypes

        class SHFILEOPSTRUCTW(ctypes.Structure):
            _fields_ = [
                ("hwnd", wintypes.HWND),
                ("wFunc", wintypes.UINT),
                ("pFrom", wintypes.LPCWSTR),
                ("pTo", wintypes.LPCWSTR),
                ("fFlags", wintypes.WORD),
                ("fAnyOperationsAborted", wintypes.BOOL),
                ("hNameMappings", ctypes.c_void_p),
                ("lpszProgressTitle", wintypes.LPCWSTR),
            ]

        operation = SHFILEOPSTRUCTW()
        operation.wFunc = 3  # FO_DELETE
        operation.pFrom = str(path.resolve()) + "\0\0"
        operation.fFlags = (
            0x0004  # FOF_SILENT
            | 0x0010  # FOF_NOCONFIRMATION
            | 0x0040  # FOF_ALLOWUNDO: send to the Recycle Bin
            | 0x0400  # FOF_NOERRORUI
        )
        result = ctypes.windll.shell32.SHFileOperationW(
            ctypes.byref(operation)
        )
        if result or operation.fAnyOperationsAborted:
            raise RuntimeError(
                "Windows Recycle Bin operation failed "
                f"(result={result}, aborted={operation.fAnyOperationsAborted}): "
                f"{path}"
            )
    else:
        raise RuntimeError(
            "send2trash is unavailable; refusing permanent deletion"
        )
    if path.exists():
        raise RuntimeError(f"Recycle Bin operation did not remove: {path}")
    return path


_LAST_RANDOM_CONSOLE_PAIR: tuple[int, int] | None = None


def ansi_16_foreground(index: int) -> int:
    """Return the ANSI foreground code for a Windows-style color index."""
    return 30 + index if index < 8 else 90 + (index - 8)


def ansi_16_background(index: int) -> int:
    """Return the ANSI background code for a Windows-style color index."""
    return 40 + index if index < 8 else 100 + (index - 8)


def emit_argt_random_color(
    *,
    foreground_only: bool,
    use_color: bool,
    random_source: random.Random | Any = random,
) -> str:
    """Emit the random foreground/background behavior used by ARGT's BATs."""
    global _LAST_RANDOM_CONSOLE_PAIR
    if not use_color:
        return ""
    if foreground_only:
        foreground = random_source.randint(8, 15)
        sequence = f"\033[{ansi_16_foreground(foreground)}m"
    else:
        while True:
            foreground = random_source.randint(0, 15)
            background = random_source.randint(0, 15)
            pair = (foreground, background)
            if foreground != background and pair != _LAST_RANDOM_CONSOLE_PAIR:
                _LAST_RANDOM_CONSOLE_PAIR = pair
                break
        sequence = (
            f"\033[{ansi_16_foreground(foreground)};"
            f"{ansi_16_background(background)}m"
        )
    print(sequence, end="", flush=True)
    return sequence


def require_replaygain_program(name: str) -> str:
    """Resolve one ARGT dependency or fail before changing any audio."""
    executable = shutil.which(name)
    if executable is None:
        raise RuntimeError(
            f"ARGT-compatible ReplayGain requires {name} in PATH"
        )
    return executable


def run_live_command(
    command: list[str],
    *,
    cwd: Path,
    stream_output: bool,
) -> None:
    """Run a command visibly in the current console and enforce its exit code."""
    if stream_output:
        print(
            console_safe_text(
            f"        ▶ {subprocess.list2cmdline(command)}"
            ),
            flush=True,
        )
    options: dict[str, Any] = {
        "cwd": str(cwd),
        "check": False,
    }
    if not stream_output:
        options.update(
            {
                "stdout": subprocess.PIPE,
                "stderr": subprocess.STDOUT,
                "text": True,
                "errors": "replace",
            }
        )
    result = subprocess.run(command, **options)
    if result.returncode:
        captured = str(getattr(result, "stdout", "") or "").strip()
        detail = f"\n{captured}" if captured else ""
        raise RuntimeError(
            f"ReplayGain command failed with exit code {result.returncode}: "
            f"{subprocess.list2cmdline(command)}{detail}"
        )


def move_sequestered_files_back(sequester: Path, folder: Path) -> list[Path]:
    """Move every MP3-workaround artifact back with collision-safe names."""
    restored: list[Path] = []
    if not sequester.exists():
        return restored
    for staged in sorted(sequester.iterdir(), key=lambda item: item.name.lower()):
        destination = collision_safe_path(folder / staged.name)
        shutil.move(str(staged), str(destination))
        restored.append(destination)
    return restored


def run_silent_polled_command(
    command: list[str],
    *,
    cwd: Path,
    on_tick: Callable[[float], None] | None = None,
    poll_seconds: float = 0.10,
) -> float:
    """Run a child silently, polling often enough for a live progress display."""
    started = time.perf_counter()
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace") as output:
        process = subprocess.Popen(
            command,
            cwd=str(cwd),
            stdout=output,
            stderr=subprocess.STDOUT,
        )
        while True:
            returncode = process.poll()
            elapsed = time.perf_counter() - started
            if on_tick is not None:
                on_tick(elapsed)
            if returncode is not None:
                break
            time.sleep(max(0.02, float(poll_seconds)))
        output.flush()
        output.seek(0)
        captured = output.read().strip()
    if returncode:
        detail = f"\n{captured}" if captured else ""
        raise RuntimeError(
            f"ReplayGain command failed with exit code {returncode}: "
            f"{subprocess.list2cmdline(command)}{detail}"
        )
    return time.perf_counter() - started


def apply_argt_replaygain_folder(
    folder: Path,
    *,
    use_color: bool,
    stream_output: bool = False,
) -> list[str]:
    """Run the ARGT-equivalent workflow with one quiet, predictive progress UI."""
    immediate_audio = [
        path
        for path in folder.iterdir()
        if path.is_file() and path.suffix.lower() in {".mp3", ".flac"}
    ]
    mp3_files = sorted(
        (path for path in immediate_audio if path.suffix.lower() == ".mp3"),
        key=lambda path: path.name.lower(),
    )
    flac_files = sorted(
        (path for path in immediate_audio if path.suffix.lower() == ".flac"),
        key=lambda path: path.name.lower(),
    )
    actions: list[str] = []
    operation_started = time.perf_counter()
    try:
        if mp3_files:
            metamp3 = require_replaygain_program("metamp3")
            print(
                console_safe_text(
                    f"        🔢 Adding ReplayGain tags to {len(mp3_files)} MP3 "
                    f"file{'s' if len(mp3_files) != 1 else ''}..."
                ),
                flush=True,
            )
            for path in mp3_files:
                backup = backup_before_inline_replacement(path)
                actions.append(f"backup:{backup}")

            sequester = collision_safe_path(folder / "ohhhh")
            sequester.mkdir()
            try:
                for path in mp3_files:
                    shutil.move(str(path), str(sequester / path.name))
                run_silent_polled_command(
                    [metamp3, "--replay-gain", "*.*"],
                    cwd=sequester,
                )
            finally:
                restored = move_sequestered_files_back(sequester, folder)
                if sequester.exists() and not any(sequester.iterdir()):
                    recycle_path(sequester)
                    actions.append(f"recycled:{sequester}")
            for path in restored:
                actions.append(f"replaygain:{path}")

        if flac_files:
            metaflac = require_replaygain_program("metaflac")
            print(
                console_safe_text(
                    f"        🎚️ Adding ReplayGain tags to {len(flac_files)} FLAC "
                    f"file{'s' if len(flac_files) != 1 else ''}..."
                ),
                flush=True,
            )
            sizes: dict[Path, int] = {}
            for path in flac_files:
                try:
                    sizes[path] = max(1, path.stat().st_size)
                except OSError:
                    sizes[path] = 1
            total_bytes = max(1, sum(sizes.values()))
            completed_bytes = 0
            completed_seconds = 0.0
            progress_enabled = bool(getattr(sys.stderr, "isatty", lambda: False)())
            with progress_bar(
                total=1.0,
                description="🎚️ ReplayGain FLACs",
                unit="",
                enabled=progress_enabled,
                bar_format=REPLAYGAIN_PROGRESS_FORMAT,
            ) as progress:
                for index, path in enumerate(flac_files, start=1):
                    size_bytes = sizes[path]
                    remaining_after_bytes = max(
                        0, total_bytes - completed_bytes - size_bytes
                    )
                    model_seconds_per_byte = (
                        completed_seconds / completed_bytes
                        if completed_bytes > 0 and completed_seconds > 0
                        else None
                    )
                    backup = backup_before_inline_replacement(path)
                    actions.append(f"backup:{backup}")
                    command = [metaflac, "--add-replay-gain", str(path)]
                    command_started = time.perf_counter()

                    def update_progress(elapsed: float) -> None:
                        if progress is None:
                            return
                        if model_seconds_per_byte is None:
                            target = completed_bytes / total_bytes
                            eta_text = "calibrating"
                        else:
                            estimated = max(0.05, model_seconds_per_byte * size_bytes)
                            fraction = min(0.97, max(0.0, elapsed / estimated))
                            target = (
                                completed_bytes + size_bytes * fraction
                            ) / total_bytes
                            effective_model = max(
                                model_seconds_per_byte,
                                elapsed / max(1.0, size_bytes * 0.97),
                            )
                            eta_seconds = max(0.0, estimated - elapsed) + (
                                effective_model * remaining_after_bytes
                            )
                            eta_text = compact_elapsed(eta_seconds)
                        progress.n = min(0.999999, max(float(progress.n), target))
                        progress.set_postfix_str(
                            f" • {index}/{len(flac_files)} • ETA {eta_text} • "
                            f"{compact_progress_filename(path)}",
                            refresh=False,
                        )
                        progress.refresh()

                    succeeded = False
                    try:
                        elapsed = run_silent_polled_command(
                            command,
                            cwd=folder,
                            on_tick=update_progress,
                        )
                        succeeded = True
                    except Exception:
                        elapsed = time.perf_counter() - command_started
                        record_replaygain_timing(
                            path,
                            tool="metaflac",
                            elapsed_seconds=elapsed,
                            succeeded=False,
                        )
                        raise
                    else:
                        record_replaygain_timing(
                            path,
                            tool="metaflac",
                            elapsed_seconds=elapsed,
                            succeeded=True,
                        )
                    finally:
                        if succeeded:
                            completed_bytes += size_bytes
                            completed_seconds += elapsed
                            if progress is not None:
                                progress.n = min(1.0, completed_bytes / total_bytes)
                                learned_model = (
                                    completed_seconds / completed_bytes
                                    if completed_bytes else 0.0
                                )
                                eta = learned_model * max(
                                    0, total_bytes - completed_bytes
                                )
                                progress.set_postfix_str(
                                    f" • {index}/{len(flac_files)} • ETA "
                                    f"{compact_elapsed(eta)} • "
                                    f"{compact_progress_filename(path)}",
                                    refresh=False,
                                )
                                progress.refresh()
                    actions.append(f"replaygain:{path}")
                if progress is not None:
                    progress.n = 1.0
                    progress.set_postfix_str(
                        f" • {len(flac_files)}/{len(flac_files)} • ETA 00:00",
                        refresh=False,
                    )
                    progress.refresh()

        total_elapsed = time.perf_counter() - operation_started
        total_files = len(mp3_files) + len(flac_files)
        actions.append(
            f"replaygain_summary:{total_files}|{len(mp3_files)}|"
            f"{len(flac_files)}|{total_elapsed:.6f}"
        )
    finally:
        if use_color:
            print(ANSI["reset"], end="", flush=True)
    return actions


def apply_replaygain_file(
    audio_path: Path,
    *,
    use_color: bool,
    stream_output: bool = True,
) -> list[str]:
    """Recalculate ReplayGain for exactly one edited MP3 or FLAC file."""
    suffix = audio_path.suffix.casefold()
    if suffix not in {".mp3", ".flac"}:
        raise RuntimeError(
            f"ReplayGain tagging is supported here for MP3 and FLAC, not "
            f"{suffix or 'extensionless'} audio"
        )
    if not audio_path.is_file():
        raise FileNotFoundError(audio_path)

    backup = backup_before_inline_replacement(audio_path)
    if suffix == ".mp3":
        executable = require_replaygain_program("metamp3")
        command = [executable, "--replay-gain", audio_path.name]
    else:
        executable = require_replaygain_program("metaflac")
        command = [executable, "--add-replay-gain", str(audio_path)]

    emit_argt_random_color(
        foreground_only=(suffix == ".mp3"),
        use_color=use_color,
    )
    print(
        console_safe_text(
            f"        🔢 Recalculating ReplayGain for edited file: "
            f"{audio_path.name}"
        ),
        flush=True,
    )
    try:
        run_live_command(
            command,
            cwd=audio_path.parent,
            stream_output=stream_output,
        )
    finally:
        if use_color:
            print("\033[91;40m", end="", flush=True)
    return [f"backup:{backup}", f"replaygain:{audio_path}"]


def canonicalized_filename(name: str) -> str:
    """Return a filename with established parenthesized markers normalized."""
    result = name
    for old, new in CANONICAL_FILENAME_MARKERS.items():
        result = re.sub(re.escape(old), lambda _match, value=new: value, result, flags=re.I)
    return result


def is_windows_read_only(path: Path) -> bool:
    """Return whether the Windows read-only file attribute is set."""
    attributes = getattr(path.stat(), "st_file_attributes", 0)
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_READONLY", 1))


def add_local_dependency_paths() -> None:
    """Let the installed C:\\BAT copy find the sandbox's Python helper libs."""
    candidates: list[Path] = []
    env_path = os.environ.get("AUDIT_MUSIC_BATCH_PYTHONPATH")
    if env_path:
        candidates.extend(Path(part) for part in env_path.split(os.pathsep) if part)

    userprofile = Path(os.environ.get("USERPROFILE", ""))
    candidates.extend(
        [
            Path(__file__).resolve().parent / ".codex_tools" / "python",
            Path.cwd() / ".codex_tools" / "python",
            userprofile / "Documents" / "Music Processing" / ".codex_tools" / "python",
            userprofile / "OneDrive" / "Documents" / "Music Processing" / ".codex_tools" / "python",
        ]
    )

    for candidate in candidates:
        if candidate.exists():
            text = str(candidate)
            if text not in sys.path:
                sys.path.insert(0, text)


add_local_dependency_paths()


try:
    from mutagen import File as mutagen_file
    from mutagen.flac import FLAC, Picture
    from mutagen.id3 import APIC, ID3, SYLT, TALB, TCON, TXXX, USLT
    from mutagen.mp3 import MP3
except Exception:  # pragma: no cover - exercised when mutagen is absent.
    mutagen_file = None
    FLAC = Picture = APIC = ID3 = SYLT = TALB = TCON = TXXX = USLT = MP3 = None


try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
except Exception:  # pragma: no cover - optional dependency.
    Image = ImageDraw = ImageFilter = ImageFont = None


try:
    from send2trash import send2trash
except Exception:  # pragma: no cover - required only for approved deletions.
    send2trash = None


try:
    import certifi
except Exception:  # pragma: no cover - verified default context remains.
    certifi = None


@dataclass(frozen=True)
class ToolRequirement:
    name: str
    available: bool
    capability: str
    importance: str


@dataclass(frozen=True)
class BehaviorDefaults:
    """Persistent automatic behaviors, overridable by each command line."""

    embed_lyrics: bool = BUILTIN_DEFAULT_EMBED_LYRICS
    find_cover: bool = BUILTIN_DEFAULT_FIND_COVER
    check_silence: bool = BUILTIN_DEFAULT_CHECK_SILENCE
    silence_threshold_seconds: float = (
        BUILTIN_DEFAULT_SILENCE_THRESHOLD_SECONDS
    )


@dataclass(frozen=True)
class CoverArtwork:
    """One distinct remote artwork image belonging to a selected release."""

    image_id: str
    url: str
    types: tuple[str, ...]
    comment: str
    front: bool
    approved: bool


@dataclass(frozen=True)
class ArtworkPreviewGeometry:
    """Live console dimensions available to one artwork preview."""

    terminal_columns: int
    terminal_rows: int
    indent_columns: int
    columns: int
    rows: int
    pixel_width: int
    pixel_height: int


@dataclass(frozen=True)
class ConsoleViewportState:
    """Visible console-window geometry plus cursor location in that window."""

    columns: int
    rows: int
    cursor_column: int
    cursor_row: int
    window_top: int = 0
    window_bottom: int = 0

    @property
    def rows_available_from_cursor(self) -> int:
        return max(1, self.rows - self.cursor_row)


@dataclass(frozen=True)
class WaveformReviewLayout:
    """One inline waveform-review block's vertical budget."""

    graph_rows: int
    graph_count: int
    fixed_text_rows: int
    required_rows: int
    rows_available_from_cursor: int
    scroll_rows: int
    terminal_columns: int
    terminal_rows: int


@dataclass(frozen=True)
class PreparedArtworkPreview:
    """Display-ready preview produced without writing to the terminal."""

    mode: str
    geometry: ArtworkPreviewGeometry
    sixel_payload: bytes | None = None
    text_payload: str | None = None
    renderer_options: tuple[str, ...] = ()
    direct_command: tuple[str, ...] = ()


@dataclass(frozen=True)
class CoverMatch:
    """A release match plus its complete selected artwork inventory."""

    source: str
    release_id: str
    release_group_id: str
    artist: str
    album: str
    date: str
    country: str
    formats: tuple[str, ...]
    confidence: int
    exact_id: bool
    ambiguous: bool
    artworks: tuple[CoverArtwork, ...]


def dependency_requirements(
    *,
    unit_tests: bool = False,
    find_cover: bool = False,
    check_silence: bool = True,
    availability: dict[str, bool] | None = None,
) -> list[ToolRequirement]:
    """Inventory every Python/executable dependency used by this script."""
    overrides = availability or {}

    def detected(name: str, actual: bool) -> bool:
        return bool(overrides.get(name, actual))

    requirements = [
        ToolRequirement(
            "mutagen",
            detected("mutagen", mutagen_file is not None),
            "audio/tag inspection plus metadata, lyrics, and artwork writes",
            "core audit",
        ),
        ToolRequirement(
            "Pillow",
            detected("Pillow", Image is not None),
            (
                "decoding, validating, and normalizing downloaded cover artwork"
                if find_cover
                else "image-dimension checks used when evaluating artwork duplicates"
            ),
            "cover search" if find_cover else "audit enhancement",
        ),
        ToolRequirement(
            "Recycle Bin support",
            detected(
                "send2trash",
                send2trash is not None or os.name == "nt",
            ),
            "safe Recycle Bin cleanup; permanent deletion is never substituted",
            "approved cleanup",
        ),
        ToolRequirement(
            "claire_progressbar",
            detected(
                "claire_progressbar",
                _PROGRESS_IMPORT_ERROR is None,
            ),
            "rainbow progress display for long enumeration and audit passes",
            "console status",
        ),
        ToolRequirement(
            "metamp3",
            detected("metamp3", shutil.which("metamp3") is not None),
            "ARGT-equivalent ReplayGain writes for MP3 folders",
            "approved repair",
        ),
        ToolRequirement(
            "metaflac",
            detected("metaflac", shutil.which("metaflac") is not None),
            "ARGT-equivalent ReplayGain writes for FLAC files",
            "approved repair",
        ),
        ToolRequirement(
            "ffplay",
            detected("ffplay", shutil.which("ffplay") is not None),
            "P=Preview audio during interactive waveform review",
            "waveform audio preview",
        ),
        ToolRequirement(
            "play_audio_file.py",
            detected(
                "play_audio_file.py",
                audio_preview_player_script() is not None,
            ),
            (
                "keyboard-controlled waveform audio preview with seeking "
                "and immediate stop keys"
            ),
            "waveform audio preview",
        ),
    ]
    if check_silence:
        requirements.append(
            ToolRequirement(
                "ffmpeg",
                detected("ffmpeg", shutil.which("ffmpeg") is not None),
                "automatic detection of leading, internal, and trailing silence",
                "silence audit",
            )
        )
    if find_cover:
        requirements.append(
            ToolRequirement(
                "IrfanView",
                detected(
                    "IrfanView",
                    irfanview_executable() is not None,
                ),
                (
                    "the V key for full-size downloaded-artwork review; "
                    "set IMAGE_VIEWER_EXECUTABLE in the script's top "
                    "USER CONFIGURATION section"
                ),
                "cover review",
            )
        )
    if unit_tests:
        requirements.extend(
            [
                ToolRequirement(
                    "flac",
                    detected("flac", shutil.which("flac") is not None),
                    "generation of disposable FLAC fixtures",
                    "unit tests",
                ),
                *(
                    []
                    if check_silence
                    else [
                        ToolRequirement(
                            "ffmpeg",
                            detected(
                                "ffmpeg",
                                shutil.which("ffmpeg") is not None,
                            ),
                            "generation of disposable MP3 fixtures",
                            "unit tests",
                        )
                    ]
                ),
            ]
        )
    return requirements


def render_dependency_warnings(
    missing: list[ToolRequirement],
    use_color: bool,
) -> str:
    """Explain each unavailable tool and the exact capability it disables."""
    lines = [
        "",
        report_section("Dependency preflight — warnings", use_color, "yellow"),
        "",
    ]
    for requirement in missing:
        name = rgb_text(
            requirement.name,
            255,
            240,
            70,
            use_color,
        )
        impact = rgb_text(
            f"{requirement.importance}: {requirement.capability}",
            205,
            155,
            45,
            use_color,
        )
        lines.append(f"        ⚠️ {name} is unavailable — {impact}.")
    lines.extend(
        [
            "",
            "        Missing tools disable only the capabilities named above;",
            "        choosing No cancels before any music files are scanned.",
            "",
        ]
    )
    return "\n".join(lines)


def run_dependency_preflight(
    *,
    unit_tests: bool,
    find_cover: bool = False,
    check_silence: bool = True,
    interactive: bool,
    use_color: bool,
    key_reader=None,
    availability: dict[str, bool] | None = None,
) -> bool:
    """Warn about missing tools and obtain permission before continuing."""
    missing = [
        requirement
        for requirement in dependency_requirements(
            unit_tests=unit_tests,
            find_cover=find_cover,
            check_silence=check_silence,
            availability=availability,
        )
        if not requirement.available
    ]
    if not missing:
        return True
    print(
        console_safe_text(render_dependency_warnings(missing, use_color)),
        end="",
    )
    if not interactive:
        print(
            colorize(
                "        ⚠️ --no-interactive suppresses the prompt; "
                "continuing with the listed capabilities unavailable.",
                "yellow",
                use_color,
            )
        )
        return True
    subject = "unit tests" if unit_tests else "audit"
    return prompt_for_approval(
        f"Proceed with the {subject} despite these missing tools?",
        default_yes=False,
        use_color=use_color,
        key_reader=key_reader,
        indent="        ",
    )


def recognized_album_artist(folder: Path) -> str | None:
    """Infer an album artist from ``Artist\\YYYY - Album`` structure."""
    is_album = bool(re.match(r"^\s*(?:19|20)\d{2}\b", folder.name))
    is_special_child = folder.name.strip().casefold() in SPECIAL_ARTIST_CHILD_FOLDERS
    if not is_album and not is_special_child:
        inferred = inferred_album_filename_identity(folder)
        return inferred[0] if inferred else None
    artist = folder.parent.name.strip()
    if (
        not artist
        or artist.lower() in GENERIC_ARTIST_FOLDER_NAMES
        or len(re.sub(r"[^A-Za-z0-9]", "", artist)) < 3
    ):
        return None
    return artist


def inferred_album_filename_identity(folder: Path) -> tuple[str, str] | None:
    """Infer ``Artist, Album`` from repeated ``Artist - Album - NN Title`` names."""
    candidates: Counter[tuple[str, str]] = Counter()
    try:
        files = folder.iterdir()
    except OSError:
        return None
    for candidate in files:
        if not candidate.is_file() or candidate.suffix.casefold() not in AUDIO_EXTS:
            continue
        match = re.match(
            r"^\s*(?P<artist>.+?)\s+-\s+(?P<album>.+?)\s+-\s+"
            r"(?P<track>\d{1,2})[ _.\-]+.+$",
            candidate.stem,
        )
        if not match:
            continue
        artist = match.group("artist").strip()
        album = match.group("album").strip()
        if artist and album:
            candidates[(artist, album)] += 1
    if not candidates:
        return None
    identity, count = candidates.most_common(1)[0]
    return identity if count >= 2 else None


def redundant_artist_filename_proposal(
    filename: str,
    artist: str,
    album_track_count: int,
) -> str | None:
    """Normalize one redundant-artist album filename.

    The resulting convention is ``N_Title words.ext`` for albums with fewer
    than ten distinct tracks and ``NN_Title words.ext`` for larger albums.
    Separator underscores inside the title become spaces, and ``feat.`` is
    normalized to the more common filename spelling ``feat``.
    """
    path = Path(filename)
    if path.suffix.lower() not in CANONICAL_RENAME_EXTS:
        return None
    words = re.findall(r"[A-Za-z0-9]+", artist)
    if not words:
        return None
    artist_pattern = r"[-_. ]+".join(re.escape(word) for word in words)
    match = re.match(
        rf"^(?P<track>\d{{1,3}})[-_. ]+"
        rf"{artist_pattern}[-_. ]+(?P<rest>.+)$",
        path.stem,
        flags=re.I,
    )
    if not match:
        return None
    track_number = int(match.group("track"))
    track = (
        f"{track_number:02d}"
        if album_track_count >= 10
        else str(track_number)
    )
    title_source, suffix = rename_title_and_suffix(
        path,
        match.group("rest"),
    )
    title = canonical_song_title_text(title_source)
    proposed = f"{track}_{title}{suffix}"
    return proposed if proposed != path.name else None


def album_prefixed_filename_proposal(
    filename: str,
    artist: str,
    album: str,
    album_track_count: int,
) -> str | None:
    """Strip repeated artist/album prefixes from an album track and its sidecars."""
    path = Path(filename)
    if path.suffix.lower() not in CANONICAL_RENAME_EXTS:
        return None
    def phrase_pattern(value: str) -> str:
        return r"[-_. ]+".join(
            re.escape(word) for word in re.findall(r"[A-Za-z0-9]+", value)
        )
    artist_pattern = phrase_pattern(artist)
    album_pattern = phrase_pattern(album)
    if not artist_pattern or not album_pattern:
        return None
    match = re.match(
        rf"^{artist_pattern}[-_. ]+{album_pattern}[-_. ]+"
        rf"(?P<track>\d{{1,3}})[-_. ]+(?P<rest>.+)$",
        path.stem,
        flags=re.I,
    )
    if not match:
        return None
    track_number = int(match.group("track"))
    track = f"{track_number:02d}" if album_track_count >= 10 else str(track_number)
    title_source, suffix = rename_title_and_suffix(path, match.group("rest"))
    title_source = title_source.translate(str.maketrans({
        "‘": "'", "’": "'", "“": '"', "”": '"',
    }))
    title = canonical_song_title_text(title_source)
    proposed = f"{track}_{title}{suffix}"
    return proposed if proposed != path.name else None


TITLE_STRUCTURAL_LOWERCASE = {"aka", "feat", "ft", "vs"}
TITLE_CONTRACTION_SUFFIXES = {
    "d",
    "ll",
    "m",
    "n",
    "re",
    "s",
    "t",
    "ve",
}


def canonical_title_word(word: str) -> str:
    """Title-case a word while preserving accepted acronyms and stylization."""
    if not word:
        return word
    letters = "".join(character for character in word if character.isalpha())
    if len(letters) > 1 and letters.isupper():
        return word
    if any(character.isupper() for character in word[1:]) and any(
        character.islower() for character in word
    ):
        return word
    pieces = re.split(r"(['’])", word)
    first = pieces[0]
    lowered = first.casefold()
    if lowered in TITLE_STRUCTURAL_LOWERCASE:
        pieces[0] = lowered
    elif first:
        pieces[0] = first[0].upper() + first[1:].lower()
    for index in range(2, len(pieces), 2):
        piece = pieces[index]
        if not piece:
            continue
        lowered = piece.casefold()
        if lowered in TITLE_CONTRACTION_SUFFIXES:
            pieces[index] = lowered
        else:
            pieces[index] = piece[0].upper() + piece[1:].lower()
    return "".join(pieces)


def strip_trailing_tracking_identifier(text: str) -> str:
    """Remove a final eight-character download/tracking token.

    Accepted tokens contain only hexadecimal characters/underscores and at
    least two decimal digits, which catches values such as ``E75E4EC6``,
    ``35876105``, and ``F45_CC0D`` without treating an ordinary final word as
    disposable.
    """
    value = str(text).rstrip()
    match = re.search(
        r"(?i)(?P<separator>[-_ ]+)(?P<token>[0-9a-f_]{8})$",
        value,
    )
    if match is None:
        return value
    token = match.group("token")
    if sum(character.isdigit() for character in token) < 2:
        return value
    return value[: match.start("separator")].rstrip(" -_")


def canonical_song_title_text(text: str) -> str:
    """Normalize separators/feat and capitalize ordinary filename title words."""
    normalized = str(text).translate(str.maketrans({
        "‘": "'", "’": "'", "“": '"', "”": '"',
    }))
    normalized = re.sub(
        r"_+",
        " ",
        strip_trailing_tracking_identifier(str(text)),
    )
    normalized = re.sub(r"\bfeat\.(?=\s|\))", "feat", normalized, flags=re.I)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    normalized = re.sub(r"\(\s+", "(", normalized)
    normalized = re.sub(r"\s+\)", ")", normalized)
    normalized = re.sub(r"\bYoull\b", "You'll", normalized, flags=re.I)
    marker_values = {
        value.casefold(): value
        for value in CANONICAL_FILENAME_MARKERS.values()
    }
    pieces = re.split(r"(\[[^\]]+\])", normalized)
    word_pattern = re.compile(
        r"[^\W\d_]+(?:['’][^\W\d_]+)*",
        flags=re.UNICODE,
    )
    for index, piece in enumerate(pieces):
        canonical_marker = marker_values.get(piece.casefold())
        if canonical_marker is not None:
            pieces[index] = canonical_marker
            continue
        pieces[index] = word_pattern.sub(
            lambda match: canonical_title_word(match.group(0)),
            piece,
        )
    return "".join(pieces)


def rename_title_and_suffix(path: Path, rest: str) -> tuple[str, str]:
    """Separate a title from its real extension and timestamped backup tail."""
    if path.suffix.casefold() != ".bak":
        return rest, path.suffix
    known_extensions = sorted(
        {
            extension.lstrip(".")
            for extension in (
                AUDIO_EXTS
                | LYRIC_EXTS
                | IMAGE_EXTS
                | {".json", ".log"}
            )
        },
        key=len,
        reverse=True,
    )
    match = re.match(
        r"^(?P<title>.*?)"
        r"(?P<tail>\.(?:"
        + "|".join(re.escape(item) for item in known_extensions)
        + r")\.bak\..+)$",
        rest,
        flags=re.I,
    )
    if match is None:
        return rest, path.suffix
    return match.group("title"), match.group("tail") + path.suffix


def album_uses_disc_track_prefix(files: list[Path]) -> bool:
    """Detect a repeated DISC_TRACK_TITLE convention from the audio files."""
    audio = [path for path in files if path.suffix.casefold() in AUDIO_EXTS]
    if len(audio) < 2:
        return False
    matches = [
        re.match(
            r"^(?P<disc>\d{1,2})_(?P<track>\d{1,2})_(?P<title>.+)$",
            path.stem,
        )
        for path in audio
    ]
    if any(match is None for match in matches):
        return False
    discs = {str(match.group("disc")) for match in matches if match is not None}
    # Requiring more than one disc/side prevents a title beginning with a number
    # from being mistaken for compound numbering in an ordinary one-disc album.
    return len(discs) >= 2


def album_title_source_and_suffix(
    path: Path, rest: str, *, compound_track_prefix: bool
) -> tuple[str, str]:
    """Split title text from structural sidecar/backup tails."""
    if compound_track_prefix and path.suffix.casefold() == ".srt":
        match = re.match(
            r"^(?P<title>.*?)(?P<tail>\.(?:mp3|flac)\._vad_ten)$",
            rest,
            flags=re.I,
        )
        if match is not None:
            return match.group("title"), match.group("tail") + path.suffix
    return rename_title_and_suffix(path, rest)


def capitalized_album_filename_proposal(
    filename: str,
    album_track_count: int,
    *,
    compound_track_prefix: bool = False,
) -> str | None:
    """Normalize track prefix/title case while preserving compound disc numbering."""
    path = Path(filename)
    if path.suffix.casefold() not in CANONICAL_RENAME_EXTS:
        return None
    if compound_track_prefix:
        match = re.match(
            r"^(?P<disc>\d{1,2})_(?P<track>\d{1,2})_(?P<rest>.+)$",
            path.stem,
        )
        if match is None:
            return None
        prefix = f"{match.group('disc')}_{match.group('track')}_"
        title_source, suffix = album_title_source_and_suffix(
            path,
            match.group("rest"),
            compound_track_prefix=True,
        )
        title = canonical_song_title_text(title_source)
        proposed = f"{prefix}{title}{suffix}"
        return proposed if proposed != path.name else None

    match = re.match(
        r"^(?P<track>\d{1,3})[-_. ]+(?P<rest>.+)$",
        path.stem,
    )
    if match is None:
        return None
    track_number = int(match.group("track"))
    track = (
        f"{track_number:02d}"
        if album_track_count >= 10
        else str(track_number)
    )
    title_source, suffix = album_title_source_and_suffix(
        path,
        match.group("rest"),
        compound_track_prefix=False,
    )
    title = canonical_song_title_text(title_source)
    proposed = f"{track}_{title}{suffix}"
    return proposed if proposed != path.name else None


def all_caps_album_title_proposal(
    filename: str,
    album_track_count: int,
    *,
    compound_track_prefix: bool = False,
) -> str | None:
    """Suggest conservative title case while preserving disc/track prefixes."""
    path = Path(filename)
    if path.suffix.casefold() not in CANONICAL_RENAME_EXTS:
        return None
    if compound_track_prefix:
        match = re.match(
            r"^(?P<disc>\d{1,2})_(?P<track>\d{1,2})_(?P<rest>.+)$",
            path.stem,
        )
        if match is None:
            return None
        prefix = f"{match.group('disc')}_{match.group('track')}_"
    else:
        match = re.match(
            r"^(?P<track>\d{1,3})[-_. ]+(?P<rest>.+)$",
            path.stem,
        )
        if match is None:
            return None
        track_number = int(match.group("track"))
        track = f"{track_number:02d}" if album_track_count >= 10 else str(track_number)
        prefix = f"{track}_"
    title_source, suffix = album_title_source_and_suffix(
        path,
        match.group("rest"),
        compound_track_prefix=compound_track_prefix,
    )
    title_source = title_source.translate(str.maketrans({
        "‘": "'", "’": "'", "“": '"', "”": '"',
    }))
    letters = "".join(character for character in title_source if character.isalpha())
    if not letters or letters != letters.upper():
        return None
    title = re.sub(
        r"[A-Za-zÀ-ÖØ-öø-ÿ]+(?:['’][A-Za-zÀ-ÖØ-öø-ÿ]+)?",
        lambda word: word.group(0).capitalize(),
        title_source,
    )
    proposed = f"{prefix}{title}{suffix}"
    return proposed if proposed != path.name else None


def audio_duration_seconds(path: Path) -> float | None:
    """Read duration without decoding the full stream."""
    if mutagen_file is None:
        return None
    try:
        audio = mutagen_file(path)
        duration = getattr(getattr(audio, "info", None), "length", None)
        return float(duration) if duration is not None else None
    except Exception:
        return None


def detect_silence_intervals(
    path: Path,
    threshold_seconds: float,
    *,
    ffmpeg_executable: str | None = None,
) -> list[dict[str, Any]]:
    """Decode one file with ffmpeg and return silence strictly over threshold."""
    ffmpeg = ffmpeg_executable or shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is unavailable for silence detection")
    command = [
        str(ffmpeg),
        "-hide_banner",
        "-nostats",
        "-i",
        str(path),
        "-af",
        (
            f"silencedetect=noise={SILENCE_DETECT_NOISE_DB}dB:"
            f"d={float(threshold_seconds):g}"
        ),
        "-f",
        "null",
        "-",
    ]
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="replace",
        check=False,
    )
    if result.returncode:
        tail = "\n".join(str(result.stdout or "").splitlines()[-5:])
        raise RuntimeError(
            f"ffmpeg silence detection failed for {path.name}"
            + (f": {tail}" if tail else "")
        )
    starts = [
        float(value)
        for value in re.findall(
            r"silence_start:\s*(-?\d+(?:\.\d+)?)",
            str(result.stdout or ""),
        )
    ]
    endings = [
        (float(end), float(duration))
        for end, duration in re.findall(
            r"silence_end:\s*(-?\d+(?:\.\d+)?)"
            r"\s*\|\s*silence_duration:\s*(\d+(?:\.\d+)?)",
            str(result.stdout or ""),
        )
    ]
    track_duration = audio_duration_seconds(path)
    intervals: list[dict[str, Any]] = []
    for index, (end, duration) in enumerate(endings):
        start = (
            starts[index]
            if index < len(starts)
            else max(0.0, end - duration)
        )
        if duration <= float(threshold_seconds):
            continue
        leading = start <= 0.15
        trailing = (
            track_duration is not None
            and end >= track_duration - 0.25
        )
        if leading and trailing:
            position = "entire-track"
        elif leading:
            position = "leading"
        elif trailing:
            position = "trailing"
        else:
            position = "internal"
        intervals.append(
            {
                "start": round(max(0.0, start), 3),
                "end": round(max(0.0, end), 3),
                "duration": round(duration, 3),
                "position": position,
            }
        )
    return intervals


def compact_progress_filename(path: Path, limit: int = 16) -> str:
    """Return a recognizable filename preview no wider than ``limit`` cells."""
    name = path.name
    width = max(3, int(limit))
    if len(name) <= width:
        return name
    left = (width - 1) // 2
    right = width - 1 - left
    return f"{name[:left]}…{name[-right:]}"


@dataclass
class Finding:
    severity: str
    category: str
    path: str
    message: str
    suggestion: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    code: str | None = None

    def as_dict(self) -> dict[str, Any]:
        out = {
            "severity": self.severity,
            "category": self.category,
            "path": self.path,
            "message": self.message,
        }
        if self.suggestion:
            out["suggestion"] = self.suggestion
        if self.details:
            out["details"] = self.details
        if self.code:
            out["code"] = self.code
        return out


def split_genre_components(genres: list[str]) -> list[str]:
    """Split multi-value/semicolon genre tags into stable, unique components."""
    components: list[str] = []
    seen: set[str] = set()
    for raw in genres:
        for piece in re.split(r"\s*(?:;|/|\|)\s*", str(raw).strip()):
            value = piece.strip()
            if not value:
                continue
            key = value.casefold()
            if key in seen:
                continue
            seen.add(key)
            components.append(value)
    return components


class BatchAudit:
    def __init__(
        self,
        root: Path,
        include_archives: bool = False,
        *,
        check_silence: bool = False,
        silence_threshold_seconds: float = (
            BUILTIN_DEFAULT_SILENCE_THRESHOLD_SECONDS
        ),
    ) -> None:
        self.display_root = Path(root)
        self.root = root.resolve()
        self.include_archives = include_archives
        self.check_silence = check_silence
        self.silence_threshold_seconds = float(silence_threshold_seconds)
        self.findings: list[Finding] = []
        self.files: list[Path] = []
        self.audio_files: list[Path] = []
        self.extension_counts: Counter[str] = Counter()
        self.mutagen_available = mutagen_file is not None
        self.pillow_available = Image is not None
        self.progress = None
        self._progress_audio_preview = ""

    def refresh_progress_postfix(self, *, refresh: bool) -> None:
        """Show compact rate/filename text without consuming the bar width."""
        if self.progress is None:
            return
        details = getattr(self.progress, "format_dict", {}) or {}
        elapsed = float(details.get("elapsed") or 0.0)
        current = float(details.get("n") or 0.0)
        initial = float(getattr(self.progress, "initial", 0.0) or 0.0)
        rate = (current - initial) / elapsed if elapsed > 0 else 0.0
        unit = str(getattr(self.progress, "unit", "") or "").strip()
        postfix = (f"{rate:6.2f} {unit}/s" if rate > 0 else f"{'--':>6} {unit}/s")
        postfix = f"{postfix:<16}"
        if self._progress_audio_preview:
            postfix += f" • {self._progress_audio_preview}"
        self.progress.set_postfix_str(postfix, refresh=refresh)

    def progress_update(self) -> None:
        if self.progress is not None:
            self.progress.update(1)
            self.refresh_progress_postfix(refresh=False)

    def progress_show_audio(self, path: Path) -> None:
        """Refresh immediately with the audio file currently being opened."""
        if self.progress is not None:
            self._progress_audio_preview = compact_progress_filename(path)
            self.refresh_progress_postfix(refresh=True)

    def progress_phase(self, description: str) -> None:
        """Show a new audit phase immediately without changing progress."""
        if self.progress is not None:
            self._progress_audio_preview = ""
            self.progress.set_description(description, refresh=False)
            self.refresh_progress_postfix(refresh=True)

    def rel(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(self.root))
        except ValueError:
            return str(path)

    def add(
        self,
        severity: str,
        category: str,
        path: Path | str,
        message: str,
        suggestion: str = "",
        **details: Any,
    ) -> None:
        path_text = self.rel(path) if isinstance(path, Path) else path
        self.findings.append(
            Finding(
                severity=severity,
                category=category,
                path=path_text,
                message=message,
                suggestion=suggestion,
                details={k: v for k, v in details.items() if v is not None},
            )
        )

    def is_archive_path(self, path: Path) -> bool:
        parts = [p.lower() for p in path.relative_to(self.root).parts[:-1]]
        name = path.name.lower()
        return any(any(hint in part for hint in ARCHIVE_HINTS) for part in parts) or ".deprecated" in name

    def is_instrumental_or_no_lyrics(self, path: Path) -> bool:
        haystack = " ".join(path.relative_to(self.root).parts).lower()
        # Do not add partial-song hints like [semi-instr] or [no-lyr] here.
        # They describe one section, not the whole merged audio file.
        return any(
            token in haystack
            for token in (
                "[instrumental]",
                "(instrumental)",
                "[instrumentals]",
                "(instrumentals)",
                "[no lyrics]",
                "(no lyrics)",
                "[no vocals]",
                "(no vocals)",
                "[sound effect]",
                "(sound effect)",
                "[sound clip]",
                "(sound clip)",
                "[chiptune]",
                "(chiptune)",
                "audiobook",
            )
        )

    def collect_files(
        self,
        on_file: Callable[[int], None] | None = None,
        on_audio_file: Callable[[Path], None] | None = None,
    ) -> None:
        if not self.root.exists():
            raise SystemExit(f"Batch root does not exist: {self.root}")
        discovered: list[Path] = []
        for path in self.root.rglob("*"):
            if path.is_file():
                discovered.append(path)
                if on_file is not None:
                    on_file(len(discovered))
                if (
                    on_audio_file is not None
                    and path.suffix.lower() in AUDIO_EXTS
                    and (
                        self.include_archives
                        or not self.is_archive_path(path)
                    )
                ):
                    on_audio_file(path)
        self.files = sorted(discovered, key=lambda p: str(p).lower())
        self.extension_counts = Counter(p.suffix.lower() or "[no extension]" for p in self.files)
        self.audio_files = [
            p
            for p in self.files
            if p.suffix.lower() in AUDIO_EXTS and (self.include_archives or not self.is_archive_path(p))
        ]

    def image_dimensions(self, path: Path) -> tuple[int, int] | None:
        if Image is None:
            return None
        try:
            with Image.open(path) as img:
                return (int(img.width), int(img.height))
        except Exception:
            return None

    def sidecar(self, audio_path: Path, ext: str) -> Path | None:
        candidate = audio_path.with_suffix(ext)
        return candidate if candidate.exists() and candidate.is_file() and candidate.stat().st_size > 0 else None

    def same_stem_sidecars(self, audio_path: Path, exts: set[str]) -> list[Path]:
        out = []
        for ext in sorted(exts):
            candidate = audio_path.with_suffix(ext)
            if candidate.exists() and candidate.is_file() and candidate.stat().st_size > 0:
                out.append(candidate)
        return out

    def folder_art_candidates(self, folder: Path) -> list[Path]:
        return folder_front_art_candidates(folder)

    def artwork_sidecars_for_audio(self, audio_path: Path) -> list[Path]:
        """Recognize album Front art and MISC's same-basename extracted art."""
        candidates = self.folder_art_candidates(audio_path.parent)
        if not is_album_track_filename(audio_path):
            candidates.extend(
                self.same_stem_sidecars(audio_path, IMAGE_EXTS)
            )
        return list(dict.fromkeys(candidates))

    def tag_snapshot(self, path: Path) -> dict[str, Any]:
        if mutagen_file is None:
            return {"error": "mutagen is not available"}
        try:
            audio = mutagen_file(path)
        except Exception as exc:
            return {"error": f"{type(exc).__name__}: {exc}"}
        if audio is None:
            return {"error": "mutagen returned no audio object"}

        info = getattr(audio, "info", None)
        duration = getattr(info, "length", None)
        out: dict[str, Any] = {
            "duration": float(duration) if duration is not None else None,
            "channels": int(getattr(info, "channels", 0) or 0),
            "title": [],
            "artist": [],
            "album": [],
            "genre": [],
            "comments": [],
            "urls": [],
            "replaygain": {},
            "art_count": 0,
            "lyrics": {
                "unsynced": 0,
                "synced": 0,
                "compat_synced": 0,
                "unsynced_text": "",
                "synced_text": "",
            },
        }

        tags = getattr(audio, "tags", None)
        suffix = path.suffix.lower()
        if suffix == ".flac":
            tagmap = {str(k).upper(): v for k, v in (tags or {}).items()}
            out["title"] = list_values(tagmap.get("TITLE"))
            out["artist"] = list_values(tagmap.get("ARTIST"))
            out["album"] = list_values(tagmap.get("ALBUM"))
            out["genre"] = list_values(tagmap.get("GENRE"))
            out["comments"] = list_values(tagmap.get("COMMENT"))
            out["urls"] = list_values(tagmap.get("URL")) + list_values(tagmap.get("WEBSITE"))
            out["art_count"] = len(getattr(audio, "pictures", []) or [])
            out["art_types"] = [int(picture.type) for picture in (getattr(audio, "pictures", []) or [])]
            unsynced_values = list_values(
                tagmap.get("LYRICS") or tagmap.get("UNSYNCEDLYRICS")
            )
            synced_values = list_values(tagmap.get("SYNCEDLYRICS"))
            out["lyrics"]["unsynced"] = int(bool(unsynced_values))
            out["lyrics"]["synced"] = int(bool(synced_values))
            out["lyrics"]["unsynced_text"] = (
                unsynced_values[0] if unsynced_values else ""
            )
            out["lyrics"]["synced_text"] = (
                synced_values[0] if synced_values else ""
            )
            for key, value in tagmap.items():
                if key.startswith("REPLAYGAIN"):
                    out["replaygain"][key.lower()] = list_values(value)
        else:
            if tags:
                out["title"] = frame_text(tags, "TIT2")
                out["artist"] = frame_text(tags, "TPE1")
                out["album"] = frame_text(tags, "TALB")
                out["genre"] = frame_text(tags, "TCON")
                out["art_count"] = len(tags.getall("APIC"))
                out["art_types"] = [int(picture.type) for picture in tags.getall("APIC")]
                unsynced_frames = tags.getall("USLT")
                out["lyrics"]["unsynced"] = len(unsynced_frames)
                out["lyrics"]["synced"] = len(tags.getall("SYLT"))
                if unsynced_frames:
                    out["lyrics"]["unsynced_text"] = str(
                        getattr(unsynced_frames[0], "text", "")
                    )
                out["comments"] = [str(t) for frame in tags.getall("COMM") for t in getattr(frame, "text", [])]
                out["urls"] = [str(t) for frame in tags.getall("WXXX") for t in getattr(frame, "url", [])]
                for frame in tags.getall("TXXX"):
                    desc = getattr(frame, "desc", "")
                    text = [str(x) for x in getattr(frame, "text", [])]
                    if desc.upper() == "SYNCEDLYRICS":
                        out["lyrics"]["compat_synced"] += 1
                        if not out["lyrics"]["synced_text"] and text:
                            out["lyrics"]["synced_text"] = text[0]
                    if desc.lower().startswith("replaygain"):
                        out["replaygain"][desc.lower()] = text
        return out

    def has_track_replaygain(self, path: Path, snapshot: dict[str, Any]) -> bool:
        replaygain = {str(k).lower(): v for k, v in snapshot.get("replaygain", {}).items()}
        required = {
            ".flac": ("replaygain_track_gain", "replaygain_track_peak"),
            ".mp3": ("replaygain_track_gain", "replaygain_track_peak"),
        }.get(path.suffix.lower(), ())
        if not all(
            replaygain.get(key)
            and any(str(value).strip() for value in replaygain[key])
            for key in required
        ):
            return False
        gain = str(replaygain["replaygain_track_gain"][0]).strip()
        peak = str(replaygain["replaygain_track_peak"][0]).strip()
        return bool(
            re.fullmatch(
                r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:\s*dB)?", gain, re.I
            )
            and re.fullmatch(r"[+]?(?:\d+(?:\.\d*)?|\.\d+)", peak)
        )

    def lrc_is_timestamped(self, path: Path) -> bool:
        try:
            text = read_text(path)
        except Exception:
            return False
        return bool(re.search(r"^\[[0-9]{1,2}:[0-9]{2}(?:\.[0-9]{1,3})?\]", text, flags=re.M))

    def audit_filesystem(self) -> None:
        for path in self.files:
            try:
                stat_result = path.stat()
            except FileNotFoundError:
                # Temporary marker/work files may legitimately disappear after
                # enumeration; a filesystem audit must tolerate that race.
                self.progress_update()
                continue
            suffix = path.suffix.lower()
            name_lower = path.name.lower()
            size = stat_result.st_size
            archived = self.is_archive_path(path)

            if size == 0:
                if suffix in AUDIO_EXTS or suffix in LYRIC_EXTS or suffix in IMAGE_EXTS:
                    self.add("problem", "zero_byte_media_or_sidecar", path, "Zero-byte media/lyric/art file.")
                elif path.name == "__":
                    self.add("safe_cleanup", "bare_marker", path, "Bare __ marker file.", "Send the bare __ marker to the Recycle Bin.")
                elif suffix == "" and re.fullmatch(r"__ .+ __", path.name):
                    self.add("info", "kept_user_marker", path, "Zero-byte __ something __ marker/comment file; keep by default.")
                elif suffix == "":
                    self.add("safe_cleanup", "zero_byte_token", path, "Zero-byte no-extension token file.", "Recycle it if it is not a deliberate marker.")

            if suffix in AUDIO_EXTS and 0 < size < 8192 and not archived:
                self.add(
                    "problem",
                    "suspiciously_tiny_audio",
                    path,
                    f"Audio file is suspiciously tiny ({size:,} bytes).",
                    "Verify that it is a real, playable audio file; do not treat it as merely an empty placeholder.",
                    size=size,
                )

            try:
                read_only_audio = (
                    suffix in AUDIO_EXTS
                    and is_windows_read_only(path)
                    and not archived
                )
            except FileNotFoundError:
                self.progress_update()
                continue
            if read_only_audio:
                self.add(
                    "safe_fix",
                    "read_only_audio",
                    path,
                    "Audio file has the Windows read-only attribute.",
                    "Clear read-only before approving metadata, lyric, artwork, or ReplayGain writes.",
                )

            if suffix in CANONICAL_RENAME_EXTS:
                proposed_name = canonicalized_filename(path.name)
                if proposed_name != path.name:
                    proposed_path = path.with_name(proposed_name)
                    if proposed_path.exists():
                        self.add(
                            "problem",
                            "filename_marker_collision",
                            path,
                            f"Canonical marker spelling would collide with existing {proposed_name}.",
                            "Resolve the two files manually.",
                            proposed_name=proposed_name,
                        )
                    else:
                        self.add(
                            "safe_fix",
                            "filename_marker_style",
                            path,
                            f"Filename marker should be normalized to {proposed_name}.",
                            "Approve the exact filename normalization.",
                            proposed_name=proposed_name,
                        )

            if path.name.lower() == "completed-todos.log":
                self.progress_update()
                continue

            if suffix == ".bak" or ".bak." in name_lower:
                self.add("never_default", "backup_file", path, "Backup file.", "Keep by default; recycling requires explicit approval.")
            elif suffix == ".log":
                self.add("ask_first", "log_sidecar", path, "Log sidecar.", "Keep by default; ask before cleanup.")
            elif suffix == ".json":
                self.add("ask_first", "json_sidecar", path, "JSON sidecar.", "Ask before cleanup; may contain transcription/search details.")

            if name_lower.endswith("._vad_ten.srt"):
                normal_base = re.sub(r"\.(mp3|flac)\._vad_ten\.srt$", "", path.name, flags=re.I)
                has_finished = any((path.parent / f"{normal_base}{ext}").exists() for ext in (".srt", ".lrc", ".txt"))
                if has_finished:
                    self.add("safe_cleanup", "vad_scratch_srt", path, "VAD scratch SRT with finished sidecars present.", "Send the scratch sidecar to the Recycle Bin.")
                else:
                    self.add("ask_first", "vad_scratch_srt", path, "VAD scratch SRT without obvious finished sidecar.", "Review before recycling.")

            if suffix == ".bat" and re.search(r"(temp|temporary|create-the-missing-karaokes|get-the-missing-lyrics)", name_lower):
                self.add("safe_cleanup", "temporary_batch_file", path, "Generated temporary batch file.", "Recycle after confirming the workflow step is complete.")
            if suffix in {".currentlydoingtranscriptionshere", ".lastinvalidaitranscriptioncheck"}:
                self.add("safe_cleanup", "stale_transcription_marker", path, "AI transcription marker file.", "Recycle when no transcription is currently running.")
            if suffix == ".m3u8":
                self.add("safe_cleanup", "tagrename_m3u8", path, "Tag&Rename preview playlist sidecar.", "Send to the Recycle Bin.")
            if suffix == ".xmp":
                self.add("safe_cleanup", "adobe_xmp", path, "Adobe/Audition XMP sidecar.", "Recycle after audio editing is complete.")

            if suffix in KNOWN_AUDIO_EXTS and suffix not in ALLOWED_AUDIO_EXTS and not archived:
                self.add("problem", "unsupported_audio_format", path, f"Audio format {suffix} is not MP3/FLAC/WAV.", "Convert or archive original.")
            if suffix == ".wav" and not archived:
                self.add(
                    "ask_first",
                    "wav_remaining",
                    path,
                    "WAV remains in active batch.",
                    "Approve conversion to FLAC; the WAV itself is kept for "
                    "now, while available metadata, lyrics, and approved "
                    "artwork are carried to the new FLAC.",
                )

            if "todo" in name_lower and path.name.lower() != "completed-todos.log" and not archived:
                self.add("problem", "active_todo_filename", path, "Active TODO remains in filename.", "Resolve the TODO, then remove it from active filenames and log it.")
            if re.search(r"[;%^]", path.name):
                self.add("ask_first", "forbidden_filename_char", path, "Filename contains one of ; % ^.", "Rename using the preferred safe equivalent.")
            if re.search(r"(?:Â|Ã|â€|�)", path.name):
                self.add("ask_first", "mojibake_filename", path, "Filename looks mojibaked.", "Review and rename if needed.")

            if suffix in IMAGE_EXTS and re.search(r" \([0-9]+\)$", path.stem):
                base_stem = re.sub(r" \([0-9]+\)$", "", path.stem)
                sibling = path.with_name(base_stem + path.suffix)
                try:
                    sibling_size = sibling.stat().st_size
                except FileNotFoundError:
                    sibling_size = None
                if sibling_size is not None and size <= sibling_size:
                    self.add("safe_cleanup", "smaller_numbered_image_duplicate", path, "Numbered image duplicate with larger/same unnumbered sibling.", "Send the smaller numbered duplicate to the Recycle Bin.", sibling=self.rel(sibling))
            self.progress_update()

    def audit_duplicates_and_archives(self) -> None:
        by_folder_stem: dict[tuple[Path, str], set[str]] = defaultdict(set)
        for path in self.files:
            if path.suffix.lower() in AUDIO_EXTS and not self.is_archive_path(path):
                by_folder_stem[(path.parent, path.stem.lower())].add(path.suffix.lower())
        for (folder, stem), exts in by_folder_stem.items():
            if ".mp3" in exts and ".flac" in exts:
                mp3 = folder / f"{stem}.mp3"
                self.add(
                    "safe_cleanup",
                    "same_stem_mp3_flac",
                    mp3 if mp3.exists() else folder,
                    "Matching MP3 and FLAC versions exist in the same folder.",
                    "Deprecate the MP3 after copying any MP3-only sidecars to the FLAC.",
                )

        self.audit_redundant_album_artist_filenames()

        archive_dirs = set()
        for path in self.files:
            if path.suffix.lower() in AUDIO_EXTS and self.is_archive_path(path):
                for parent in [path.parent, *path.parents]:
                    if parent == self.root:
                        break
                    if any(hint in parent.name.lower() for hint in ARCHIVE_HINTS):
                        archive_dirs.add(parent)
                        break
        for folder in sorted(archive_dirs, key=lambda p: str(p).lower()):
            attrib = folder / "attrib.lst"
            marker = folder / "__ this folder is for archival purposes, and has been flagged for exclusion from common playlists __"
            if not attrib.exists():
                self.add("safe_fix", "archive_missing_attrib", folder, "Archive/do-not-play folder has audio but no attrib.lst.", "Create attrib.lst with do-not-play exclusions.")
            else:
                try:
                    text = read_text(attrib)
                except Exception:
                    text = ""
                if DO_NOT_PLAY_LINE not in text:
                    self.add("safe_fix", "archive_incomplete_attrib", attrib, "Archive attrib.lst does not contain the standard do-not-play line.", "Add standard do-not-play line.")
            if not marker.exists():
                self.add("safe_fix", "archive_missing_marker", folder, "Archive/do-not-play folder has no zero-byte explanatory marker.", "Create the standard archival marker file.")

    def audit_redundant_album_artist_filenames(self) -> None:
        """Group redundant artist-prefix renames into one finding per album."""
        by_folder: dict[Path, list[Path]] = defaultdict(list)
        for path in self.files:
            by_folder[path.parent].append(path)

        for folder, files in sorted(
            by_folder.items(),
            key=lambda item: str(item[0]).lower(),
        ):
            artist = recognized_album_artist(folder)
            if artist is None or self.is_archive_path(folder):
                continue
            inferred_identity = inferred_album_filename_identity(folder)
            inferred_album = (
                inferred_identity[1]
                if inferred_identity and inferred_identity[0].casefold()
                == artist.casefold()
                else None
            )
            compound_track_prefix = album_uses_disc_track_prefix(files)
            if compound_track_prefix:
                track_identities = {
                    (match.group("disc"), match.group("track"))
                    for path in files
                    if path.suffix.lower() in AUDIO_EXTS
                    and (
                        match := re.match(
                            r"^(?P<disc>\d{1,2})_(?P<track>\d{1,2})_",
                            path.name,
                        )
                    )
                }
                album_track_count = len(track_identities)
            else:
                track_numbers = {
                    int(match.group("track"))
                    for path in files
                    if path.suffix.lower() in AUDIO_EXTS
                    and (
                        match := re.search(
                            r"(?:^|[-_. ])(?P<track>\d{1,2})[-_. ]+",
                            path.name,
                        )
                    )
                }
                album_track_count = len(track_numbers)
            renames: list[dict[str, str]] = []
            audio_renames: list[tuple[Path, str]] = []
            for path in sorted(files, key=lambda item: item.name.lower()):
                proposed_name = redundant_artist_filename_proposal(
                    path.name,
                    artist,
                    album_track_count,
                )
                if proposed_name is None and inferred_album:
                    proposed_name = album_prefixed_filename_proposal(
                        path.name,
                        artist,
                        inferred_album,
                        album_track_count,
                    )
                if proposed_name is None:
                    continue
                before = self.rel(path)
                after = self.rel(path.with_name(proposed_name))
                if before == after:
                    continue
                renames.append({"before": before, "after": after})
                if path.suffix.lower() in AUDIO_EXTS:
                    audio_renames.append((path, proposed_name))

            redundant_group = len(audio_renames) >= 2
            redundant_before = (
                {item["before"] for item in renames}
                if redundant_group
                else set()
            )
            if redundant_group:
                audio_names = {
                    path.name: proposed_name
                    for path, proposed_name in audio_renames
                }
                playlists: list[str] = []
                for playlist in files:
                    if playlist.suffix.lower() not in PLAYLIST_EXTS:
                        continue
                    try:
                        text = read_text(playlist)
                    except Exception:
                        continue
                    if any(
                        re.search(re.escape(old_name), text, flags=re.I)
                        for old_name in audio_names
                    ):
                        playlists.append(self.rel(playlist))

                self.add(
                    "ask_first",
                    "redundant_album_artist_filename_group",
                    folder,
                    (
                        f'Artist name "{artist}" and album name '
                        f'"{inferred_album}" prefix {len(renames)} album filenames.'
                        if inferred_album else
                        f'Artist name "{artist}" is repeated after the track number '
                        f"in {len(renames)} album filenames."
                    ),
                    "Approve one grouped rename for the audio and matching "
                    "sidecars/backups; local playlist references will be "
                    "backed up and updated.",
                    artist=artist,
                    renames=renames,
                    audio_count=len(audio_renames),
                    track_count=album_track_count,
                    playlists=playlists,
                )

            # All-caps titles are intentionally handled one audio family at a
            # time: the proposed capitalization is useful, but the user gets
            # an rn.bat-style editable filename before anything is renamed.
            all_caps_audio_paths: set[Path] = set()
            for path in sorted(files, key=lambda item: item.name.lower()):
                if path.suffix.casefold() not in AUDIO_EXTS:
                    continue
                proposed_name = all_caps_album_title_proposal(
                    path.name,
                    album_track_count,
                    compound_track_prefix=compound_track_prefix,
                )
                if proposed_name is None:
                    continue
                all_caps_audio_paths.add(path)
                self.add(
                    "ask_first",
                    "all_caps_album_title",
                    path,
                    "Album-track title is written entirely in capital letters.",
                    "Use the suggested capitalization or edit the filename "
                    "yourself before the audio, sidecars, backups, and local "
                    "playlist references are renamed together.",
                    proposed_name=proposed_name,
                    track_count=album_track_count,
                )

            case_renames: list[dict[str, str]] = []
            case_audio_renames: list[tuple[Path, str]] = []
            for path in sorted(files, key=lambda item: item.name.lower()):
                if self.rel(path) in redundant_before:
                    continue
                if path in all_caps_audio_paths:
                    continue
                # Do not reinterpret a lone artist-prefixed title as ordinary
                # title text; the repeated pattern is the safety signal.
                prefix_proposal = redundant_artist_filename_proposal(
                    path.name,
                    artist,
                    album_track_count,
                )
                if prefix_proposal is None and inferred_album:
                    prefix_proposal = album_prefixed_filename_proposal(
                        path.name,
                        artist,
                        inferred_album,
                        album_track_count,
                    )
                if prefix_proposal is not None:
                    continue
                proposed_name = capitalized_album_filename_proposal(
                    path.name,
                    album_track_count,
                    compound_track_prefix=compound_track_prefix,
                )
                if proposed_name is None:
                    continue
                before = self.rel(path)
                after = self.rel(path.with_name(proposed_name))
                if before == after:
                    continue
                case_renames.append({"before": before, "after": after})
                if path.suffix.casefold() in AUDIO_EXTS:
                    case_audio_renames.append((path, proposed_name))
            if not case_audio_renames:
                continue
            case_audio_names = {
                path.name: proposed_name
                for path, proposed_name in case_audio_renames
            }
            case_playlists: list[str] = []
            for playlist in files:
                if playlist.suffix.casefold() not in PLAYLIST_EXTS:
                    continue
                try:
                    text = read_text(playlist)
                except Exception:
                    continue
                if any(
                    re.search(re.escape(old_name), text, flags=re.I)
                    for old_name in case_audio_names
                ):
                    case_playlists.append(self.rel(playlist))
            self.add(
                "ask_first",
                "filename_title_capitalization_group",
                folder,
                f"{len(case_renames)} album filenames need normalized "
                "track separators or song-title capitalization.",
                "Approve one grouped rename for the audio and matching "
                "sidecars/backups; local playlist references will be backed "
                "up and updated.",
                renames=case_renames,
                audio_count=len(case_audio_renames),
                track_count=album_track_count,
                playlists=case_playlists,
            )

    def audit_audio_tags(self) -> None:
        if mutagen_file is None:
            self.add("problem", "dependency_missing", str(self.root), "mutagen is not available; tag checks were skipped.", "Install mutagen for full tag audit.")
            for _path in self.audio_files:
                self.progress_update()
            return

        replaygain_by_folder: dict[Path, dict[str, Any]] = defaultdict(
            lambda: {"total": 0, "missing": []}
        )
        missing_srt_by_folder: dict[Path, list[Path]] = defaultdict(list)

        for path in self.audio_files:
            self.progress_show_audio(path)
            snapshot = self.tag_snapshot(path)
            if "error" in snapshot:
                self.add("problem", "unreadable_audio", path, f"Could not read tags/audio: {snapshot['error']}", "Open/check/repair file.")
                self.progress_update()
                continue

            corrupt_id3 = corrupted_legacy_id3_frames(path)
            if corrupt_id3:
                self.add(
                    "safe_fix",
                    "corrupted_legacy_id3_frames",
                    path,
                    "Corrupted legacy ID3 frames detected: "
                    + ", ".join(sorted(corrupt_id3))
                    + ". The values contain broken UTF-8/BOM mojibake and may be reordered.",
                    "Back up this MP3 and remove only the corrupted non-core "
                    "ID3 frames; clean title, artist, album, and ReplayGain "
                    "frames are kept unchanged.",
                    frames=sorted(corrupt_id3),
                )

            channels = int(snapshot.get("channels") or 0)
            if channels > 2:
                self.add(
                    "ask_first",
                    "multichannel_audio",
                    path,
                    f"Multichannel audio detected ({channels} channels).",
                    "Keep the channel layout. ReplayGain 2.0 via rsgain/libebur128 can analyze 5.1 and 7.1 audio accurately.",
                    channels=channels,
                )

            genres = [str(x).strip() for x in snapshot.get("genre", [])]
            if not genres:
                self.add("problem", "missing_genre", path, "Missing genre tag.", "Set a real genre, or intentionally remove only if this batch allows no genre.")
            elif any(not g for g in genres):
                self.add("problem", "empty_genre", path, "Empty genre value.", "Remove empty genre entries or set a real genre.")
            else:
                components = split_genre_components(genres)
                # This is specifically a simplification finding: a single genre
                # such as "Punk Rock" is already simple and should not be nagged.
                # Multi-value / semicolon tags containing a punk-family component
                # get an interactive chooser instead.
                if (
                    len(components) > 1
                    and any("punk" in component.casefold() for component in components)
                ):
                    self.add(
                        "safe_fix",
                        "simplify_punk_genre",
                        path,
                        f"Punk-family genre is {genres}.",
                        "Choose Punk (default), one existing genre component, or keep the whole existing tag.",
                        genres=genres,
                        genre_components=components,
                    )

            if not snapshot.get("title"):
                self.add("problem", "missing_title", path, "Missing title tag.")
            if not snapshot.get("artist"):
                self.add("problem", "missing_artist", path, "Missing artist tag.")
            if not snapshot.get("album"):
                self.add(
                    "ask_first",
                    "missing_album",
                    path,
                    "Missing album tag.",
                    "Enter an album value when prompted, or press Enter to leave it unchanged.",
                )

            for comment in snapshot.get("comments", []):
                text = str(comment).strip()
                url = extract_url_only_comment(text)
                if url:
                    self.add("safe_fix", "url_comment", path, f"Comment only points to URL: {text}", "Move URL into URL tag and clear the fake comment.", url=url)
                elif text:
                    self.add("info", "comment_present", path, "Non-empty comment tag is present.", comment=text)

            replaygain_status = replaygain_by_folder[path.parent]
            replaygain_status["total"] += 1
            if not self.has_track_replaygain(path, snapshot):
                replaygain_status["missing"].append(path)

            front_sidecars = embeddable_front_art_candidates(path)
            image_sidecars = self.artwork_sidecars_for_audio(path)
            if int(snapshot.get("art_count") or 0) == 0:
                severity = "safe_fix" if front_sidecars else "ask_first"
                suggestion = (
                    "Embed existing sidecar artwork."
                    if front_sidecars
                    else "Search MusicBrainz/Cover Art Archive first, fall back "
                    "to Discogs when configured, review every supplied artwork "
                    "part, and embed only one approved Front image."
                )
                self.add(
                    severity,
                    "missing_embedded_art",
                    path,
                    "No embedded front cover art.",
                    suggestion,
                    sidecars=[self.rel(p) for p in front_sidecars],
                    action_available=True,
                )
            elif int(snapshot.get("art_count") or 0) > 1:
                self.add(
                    "safe_fix",
                    "multiple_embedded_artworks",
                    path,
                    "More than one image is embedded; only one front cover should remain in the audio file.",
                    "Export every embedded image to the folder, then retain only one front-cover image in the audio.",
                    art_count=int(snapshot.get("art_count") or 0),
                    art_types=snapshot.get("art_types", []),
                )
            elif not image_sidecars:
                self.add(
                    "ask_first",
                    "embedded_art_without_sidecar",
                    path,
                    "Audio has embedded art but no obvious image sidecar.",
                    "For numbered album tracks, extract cover.jpg; for "
                    "MISC/loose tracks, extract a same-basename JPG sidecar.",
                )

            lyrics = snapshot.get("lyrics", {})
            has_unsynced = int(lyrics.get("unsynced") or 0) > 0
            has_synced = int(lyrics.get("synced") or 0) > 0 or int(lyrics.get("compat_synced") or 0) > 0
            lrc = self.sidecar(path, ".lrc")
            txt = self.sidecar(path, ".txt")
            srt = self.sidecar(path, ".srt")
            if not self.is_instrumental_or_no_lyrics(path):
                if lrc and txt and not srt:
                    if self.lrc_is_timestamped(lrc):
                        missing_srt_by_folder[path.parent].append(path)
                    else:
                        self.add(
                            "ask_first",
                            "lrc_txt_missing_srt_but_lrc_untimed",
                            path,
                            "LRC and TXT sidecars exist, but SRT is missing and the LRC does not look timestamped.",
                            "Review the LRC before trying to create an SRT.",
                        )
                elif (
                    lrc
                    and srt
                    and self.lrc_is_timestamped(lrc)
                    and lrc.stat().st_mtime > srt.stat().st_mtime
                    and not lrc_is_derived_from_srt(lrc, srt)
                ):
                    self.add(
                        "safe_fix",
                        "newer_lrc_needs_srt_backfill",
                        path,
                        "Timestamped LRC sidecar is newer than its SRT and "
                        "contains edits not derived from that SRT.",
                        "Run lrc2srt.py for this LRC to backfill the matching "
                        "SRT, then re-audit.",
                        lrc_sidecar=self.rel(lrc),
                        srt_sidecar=self.rel(srt),
                    )
                plain_candidates = [
                    candidate for candidate in (txt, lrc, srt) if candidate
                ]
                timed_candidates = [
                    candidate for candidate in (lrc, srt) if candidate
                ]
                plain_source, plain_line_count = first_usable_plain_sidecar(
                    plain_candidates
                )
                timed_source, timed_line_count = first_usable_timed_sidecar(
                    timed_candidates
                )
                outdated_components: list[dict[str, Any]] = []
                if has_unsynced and plain_source:
                    expected_plain = usable_plain_sidecar_content(plain_source)
                    plain_reasons = lyric_refresh_reasons(
                        path,
                        plain_source,
                        expected_plain,
                        str(lyrics.get("unsynced_text") or ""),
                    )
                    if plain_reasons:
                        outdated_components.append(
                            {
                                "kind": "plain lyrics",
                                "sidecar": self.rel(plain_source),
                                "reasons": plain_reasons,
                            }
                        )
                if has_synced and timed_source:
                    expected_timed = timed_sidecar_content(timed_source)
                    timed_reasons = lyric_refresh_reasons(
                        path,
                        timed_source,
                        expected_timed,
                        str(lyrics.get("synced_text") or ""),
                        timed=True,
                    )
                    if timed_reasons:
                        outdated_components.append(
                            {
                                "kind": "timed karaoke",
                                "sidecar": self.rel(timed_source),
                                "reasons": timed_reasons,
                            }
                        )
                if not has_unsynced:
                    if plain_source:
                        self.add(
                            "safe_fix",
                            "plain_lyrics_not_embedded",
                            path,
                            "Plain lyrics are not embedded; "
                            f"a usable {plain_source.suffix.upper()} sidecar exists "
                            f"with {plain_line_count} lyric "
                            f"line{'s' if plain_line_count != 1 else ''}.",
                            "Approve the Y/n prompt below, or run with --embed-lyrics, to embed plain lyrics (USLT for MP3; LYRICS/UNSYNCEDLYRICS for FLAC).",
                            sidecar=self.rel(plain_source),
                            usable_lines=plain_line_count,
                        )
                    elif plain_candidates:
                        self.add(
                            "ask_first",
                            "unusable_plain_lyric_sidecar",
                            path,
                            "Plain lyrics are not embedded; lyric sidecar "
                            "file(s) exist, but none contains usable lyric text.",
                            "Repair or replace the listed lyric sidecar, then re-audit.",
                            sidecars=[
                                self.rel(candidate)
                                for candidate in plain_candidates
                            ],
                        )
                    else:
                        self.add(
                            "ask_first",
                            "missing_plain_lyrics",
                            path,
                            "No embedded plain lyrics and no lyric sidecar were found.",
                            "Find/create lyrics, or mark the track instrumental/no lyrics.",
                        )
                if not has_synced:
                    if timed_source:
                        self.add(
                            "safe_fix",
                            "karaoke_not_embedded",
                            path,
                            "Timed karaoke lyrics are not embedded; "
                            f"a usable {timed_source.suffix.upper()} sidecar exists "
                            f"with {timed_line_count} timestamped lyric "
                            f"line{'s' if timed_line_count != 1 else ''}.",
                            "Approve the Y/n prompt below, or run with --embed-lyrics, to embed timed karaoke (SYLT plus compatibility LRC for MP3; SYNCEDLYRICS for FLAC).",
                            sidecar=self.rel(timed_source),
                            usable_lines=timed_line_count,
                        )
                    elif timed_candidates:
                        self.add(
                            "ask_first",
                            "unusable_karaoke_sidecar",
                            path,
                            "Timed karaoke lyrics are not embedded; LRC/SRT "
                            "sidecar file(s) exist, but none contains usable "
                            "timestamped lyric lines.",
                            "Repair or replace the listed timed sidecar, then re-audit.",
                            sidecars=[
                                self.rel(candidate)
                                for candidate in timed_candidates
                            ],
                        )
                    else:
                        self.add(
                            "ask_first",
                            "missing_karaoke",
                            path,
                            "No embedded timed karaoke lyrics and no timestamped LRC/SRT sidecar were found.",
                            "Find/create timed karaoke, or mark the track instrumental/no lyrics.",
                        )
                if outdated_components:
                    kinds = " and ".join(
                        component["kind"] for component in outdated_components
                    )
                    sidecars = list(
                        dict.fromkeys(
                            component["sidecar"]
                            for component in outdated_components
                        )
                    )
                    self.add(
                        "safe_fix",
                        "embedded_lyrics_outdated",
                        path,
                        f"Embedded {kinds} are older than or different from "
                        "the current sidecar files.",
                        "Approve the prompt below, or run with --embed-lyrics, "
                        "to refresh the embedded lyrics from the regenerated "
                        "sidecars and re-audit the audio file.",
                        sidecars=sidecars,
                        components=outdated_components,
                    )
            self.progress_update()

        for folder, status in sorted(
            replaygain_by_folder.items(), key=lambda item: str(item[0]).casefold()
        ):
            missing_paths = list(status["missing"])
            total_count = int(status["total"])
            missing_count = len(missing_paths)
            if not missing_count:
                continue
            if missing_count == total_count:
                message = (
                    f"ReplayGain track gain/peak is missing or invalid for all "
                    f"{total_count} audio file{'s' if total_count != 1 else ''} "
                    "in this folder."
                )
            else:
                message = (
                    f"ReplayGain track gain/peak is missing or invalid for "
                    f"{missing_count} of {total_count} audio files in this folder."
                )
            self.add(
                "safe_fix",
                "missing_replaygain",
                folder,
                message,
                "Run the full ARGT-equivalent workflow once for this folder: "
                "process MP3s first, then FLACs with a quiet predictive progress "
                "bar, and re-audit.",
                folder_level=True,
                affected_files=[self.rel(path) for path in missing_paths],
                missing_count=missing_count,
                total_count=total_count,
            )

        for folder, paths in sorted(
            missing_srt_by_folder.items(), key=lambda item: str(item[0]).casefold()
        ):
            count = len(paths)
            self.add(
                "safe_fix",
                "missing_srt_from_lrc_txt",
                folder,
                (
                    f"{count} track{'s' if count != 1 else ''} in this folder "
                    "have timestamped LRC and TXT sidecars but no matching SRT."
                ),
                "Run Lyric/Karaoke Fix once for this folder, then re-audit.",
                folder_level=True,
                affected_files=[self.rel(path) for path in paths],
                missing_count=count,
            )

    def audit_excessive_silence(
        self,
        futures: dict[Path, Future] | None = None,
        *,
        ffmpeg_executable: str | None = None,
    ) -> None:
        """Harvest concurrent excessive-silence analysis in file order."""
        if not self.check_silence:
            return
        ffmpeg = ffmpeg_executable or shutil.which("ffmpeg")
        if ffmpeg is None:
            self.add(
                "problem",
                "silence_check_unavailable",
                self.root,
                "Excessive-silence analysis was requested, but ffmpeg is unavailable.",
                "Install ffmpeg or run with --no-silence-check.",
            )
            for _path in self.audio_files:
                self.progress_update()
            return
        threshold = self.silence_threshold_seconds
        owned_executor: ThreadPoolExecutor | None = None
        if futures is None:
            owned_executor = ThreadPoolExecutor(
                max_workers=SILENCE_ANALYSIS_WORKERS,
                thread_name_prefix="audit-silence",
            )
            futures = {
                path: owned_executor.submit(
                    cached_silence_intervals,
                    path,
                    threshold,
                    ffmpeg_executable=ffmpeg,
                )
                for path in self.audio_files
            }
        for path in self.audio_files:
            self.progress_show_audio(path)
            try:
                future = futures.get(path)
                intervals = (
                    future.result()
                    if future is not None
                    else cached_silence_intervals(
                        path,
                        threshold,
                        ffmpeg_executable=ffmpeg,
                    )
                )
                if intervals:
                    descriptions = [
                        (
                            f"{item['position']} {item['duration']:g}s "
                            f"({item['start']:g}–{item['end']:g}s)"
                        )
                        for item in intervals
                    ]
                    self.add(
                        "ask_first",
                        "excessive_silence",
                        path,
                        (
                            f"{len(intervals)} silence interval"
                            f"{'s' if len(intervals) != 1 else ''} exceed"
                            f"{'s' if len(intervals) == 1 else ''} "
                            f"{threshold:g} seconds: "
                            + "; ".join(descriptions)
                            + "."
                        ),
                        "Approve the default-Yes editor prompt to inspect and "
                        "trim this file now, or run --review-waveforms to "
                        "inspect the full-screen waveform first.",
                        threshold_seconds=threshold,
                        intervals=intervals,
                    )
            except Exception as exc:
                self.add(
                    "problem",
                    "silence_analysis_failed",
                    path,
                    f"Excessive-silence analysis failed: {type(exc).__name__}: {exc}",
                    "Verify the audio with ffmpeg, then re-run the audit.",
                )
            finally:
                self.progress_update()
        if owned_executor is not None:
            owned_executor.shutdown(wait=True)

    def audit(
        self,
        embed_lyrics_first: bool = False,
        refresh_embedded_lyrics: bool = False,
    ) -> dict[str, Any]:
        progress = None
        embedded: list[dict[str, Any]] = []
        with ExitStack() as stack:
            silence_ffmpeg = (
                shutil.which("ffmpeg")
                if self.check_silence
                else None
            )
            silence_executor: ThreadPoolExecutor | None = None
            silence_futures: dict[Path, Future] = {}
            if silence_ffmpeg is not None:
                silence_executor = stack.enter_context(
                    ThreadPoolExecutor(
                        max_workers=SILENCE_ANALYSIS_WORKERS,
                        thread_name_prefix="audit-silence",
                    )
                )
            if sys.stderr.isatty():
                progress = stack.enter_context(
                    progress_bar(
                        total=None,
                        description="🔎 Finding files",
                        unit="files",
                        enabled=True,
                        bar_format=ENUMERATION_PROGRESS_FORMAT,
                    )
                )

            def on_file(discovered_count: int) -> None:
                if progress is not None:
                    progress.update(1)

            def on_audio_file(path: Path) -> None:
                if silence_executor is None:
                    return
                silence_futures[path] = silence_executor.submit(
                    cached_silence_intervals,
                    path,
                    self.silence_threshold_seconds,
                    ffmpeg_executable=silence_ffmpeg,
                )

            self.collect_files(
                on_file=on_file,
                on_audio_file=on_audio_file,
            )
            total_checks = (
                len(self.files) * 2
                + len(self.audio_files)
                + (len(self.audio_files) if embed_lyrics_first else 0)
                + (len(self.audio_files) if self.check_silence else 0)
            )
            if progress is None:
                progress = stack.enter_context(
                    progress_bar(
                        total=total_checks,
                        description="👀 Auditing music batch",
                        unit="checks",
                        enabled=sys.stderr.isatty(),
                        bar_format=AUDIT_PROGRESS_FORMAT,
                    )
                )
                if progress is not None:
                    progress.update(len(self.files))
            else:
                progress.total = total_checks
                progress.unit = spaced_unit("checks")
                progress.bar_format = AUDIT_PROGRESS_FORMAT
                progress.set_description("👀 Auditing music batch", refresh=False)
                progress.refresh()
            self.progress = progress
            if embed_lyrics_first:
                self.progress_phase("🎤 Embedding available lyrics")
                for path in self.audio_files:
                    self.progress_show_audio(path)
                    try:
                        if not self.is_instrumental_or_no_lyrics(path):
                            actions = embed_lyrics(
                                path,
                                write=True,
                                force_refresh=refresh_embedded_lyrics,
                            )
                            if actions:
                                embedded.append(
                                    {"path": self.rel(path), "actions": actions}
                                )
                    finally:
                        self.progress_update()
            self.progress_phase("📂 Checking files and sidecars")
            self.audit_filesystem()
            self.progress_phase("🔁 Checking duplicates and archives")
            self.audit_duplicates_and_archives()
            self.progress_phase("🎵 Reading audio tags")
            self.audit_audio_tags()
            if self.check_silence:
                self.progress_phase("🔇 Silence detect")
                self.audit_excessive_silence(
                    silence_futures if silence_executor is not None else None,
                    ffmpeg_executable=silence_ffmpeg,
                )
            if self.progress is not None:
                self.progress.set_postfix_str("", refresh=False)
            self.progress = None
        self.assign_codes()
        report = self.report_data()
        if embed_lyrics_first:
            report["embedded_lyrics"] = embedded
            report["embedded_lyrics_mode"] = (
                "refresh"
                if refresh_embedded_lyrics
                else "automatic"
            )
        return report

    def assign_codes(self) -> None:
        severity_order = {"safe_fix": 0, "safe_cleanup": 1, "ask_first": 2}
        codeable = sorted(
            [
                f
                for f in self.findings
                if (
                    f.severity in severity_order
                    and f.category in EXECUTABLE_CATEGORIES
                    and f.details.get("action_available", True)
                )
            ],
            key=lambda f: (severity_order[f.severity], f.category, f.path.lower()),
        )
        for code, finding in zip(APPROVAL_CHARS, codeable):
            finding.code = code

    def report_data(self) -> dict[str, Any]:
        counts = Counter(f.severity for f in self.findings)
        categories = Counter(f.category for f in self.findings)
        return {
            "root": str(self.display_root),
            "resolved_root": str(self.root),
            "include_archives": self.include_archives,
            "check_silence": self.check_silence,
            "silence_threshold_seconds": self.silence_threshold_seconds,
            "mutagen_available": self.mutagen_available,
            "pillow_available": self.pillow_available,
            "counts": {
                "files": len(self.files),
                "active_audio": len(self.audio_files),
                "by_extension": dict(sorted(self.extension_counts.items())),
                "by_severity": dict(sorted(counts.items())),
                "by_category": dict(sorted(categories.items())),
            },
            "findings": [f.as_dict() for f in self.findings],
        }


def list_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(v) for v in value]
    return [str(value)]


def frame_text(tags: Any, frame_id: str) -> list[str]:
    out = []
    for frame in tags.getall(frame_id):
        out.extend(str(x) for x in getattr(frame, "text", []))
    return out


CORRUPTED_LEGACY_ID3_FRAME_IDS = (
    "TPOS",  # disc number
    "TLEN",  # duration
    "TBPM",  # tempo
    "TKEY",  # musical key
    "TSRC",  # ISRC
    "TSSE",  # encoder
    "TPUB",  # publisher
    "TCOP",  # copyright
    "TEXT",  # lyricist/text writer
)


def corrupted_legacy_id3_frames(path: Path) -> dict[str, list[str]]:
    """Return known non-core ID3 frames bearing the broken UTF-8/BOM pattern.

    This intentionally does not attempt to guess at a reconstruction: the
    affected serialisation can both prepend mojibake and reorder characters.
    Clean core frames such as title/artist/album and ReplayGain are excluded.
    """
    if path.suffix.casefold() != ".mp3" or MP3 is None or ID3 is None:
        return {}
    try:
        tags = MP3(path, ID3=ID3).tags
    except Exception:
        return {}
    if not tags:
        return {}
    corrupt: dict[str, list[str]] = {}
    for frame_id in CORRUPTED_LEGACY_ID3_FRAME_IDS:
        values = frame_text(tags, frame_id)
        if any(
            "├" in value
            or "╛" in value
            or "ï»¿" in value
            or re.match(r"^\?{2,}", value)
            for value in values
        ):
            corrupt[frame_id] = values
    return corrupt


def repair_corrupted_legacy_id3_frames(path: Path) -> list[str]:
    """Back up and remove only proven-corrupt legacy ID3 frame types."""
    corrupt = corrupted_legacy_id3_frames(path)
    if not corrupt:
        raise RuntimeError("No recognized corrupted legacy ID3 frames remain")
    backup = backup_before_inline_replacement(path)
    tagged = MP3(path, ID3=ID3)
    if not tagged.tags:
        raise RuntimeError("MP3 does not contain ID3 tags")
    for frame_id in corrupt:
        tagged.tags.delall(frame_id)
    tagged.save(v2_version=3)
    remaining = corrupted_legacy_id3_frames(path)
    if remaining:
        raise RuntimeError(
            "Corrupted legacy ID3 frame verification failed: "
            + ", ".join(sorted(remaining))
        )
    return [f"backup:{backup}", "removed_corrupt_id3:" + ",".join(sorted(corrupt))]


def extract_url_only_comment(text: str) -> str | None:
    match = re.fullmatch(r"(?:visit\s+)?(https?://\S+)\s*", text, flags=re.I)
    return match.group(1) if match else None


def read_text(path: Path) -> str:
    def decoded_text(raw_bytes: bytes, encoding: str, **kwargs) -> str:
        """Decode text while preserving Path.read_text's newline semantics."""
        return (
            raw_bytes.decode(encoding, **kwargs)
            .replace("\r\n", "\n")
            .replace("\r", "\n")
        )

    raw = path.read_bytes()
    bom_encodings = (
        (b"\x00\x00\xfe\xff", "utf-32"),
        (b"\xff\xfe\x00\x00", "utf-32"),
        (b"\xff\xfe", "utf-16"),
        (b"\xfe\xff", "utf-16"),
        (b"\xef\xbb\xbf", "utf-8-sig"),
    )
    for signature, encoding in bom_encodings:
        if raw.startswith(signature):
            return decoded_text(raw, encoding)

    # MiniLyrics and subtitle tools also produce BOM-less UTF-16 files. A
    # strong alternating-NUL pattern is safe to distinguish from ordinary
    # single-byte lyric text before falling back to UTF-8/Windows-1252.
    if len(raw) >= 8:
        even_null_ratio = raw[0::2].count(0) / len(raw[0::2])
        odd_null_ratio = raw[1::2].count(0) / len(raw[1::2])
        if odd_null_ratio >= 0.30 and even_null_ratio <= 0.05:
            return decoded_text(raw, "utf-16-le")
        if even_null_ratio >= 0.30 and odd_null_ratio <= 0.05:
            return decoded_text(raw, "utf-16-be")

    for encoding in ("utf-8", "cp1252"):
        try:
            return decoded_text(raw, encoding)
        except UnicodeDecodeError:
            continue
    return decoded_text(raw, sys.getdefaultencoding(), errors="replace")


def ensure_id3(path: Path):
    audio = MP3(path, ID3=ID3)
    if audio.tags is None:
        audio.add_tags()
    return audio


def set_flac_value(audio, key: str, value: str) -> None:
    for existing in list(audio.tags.keys()):
        if existing.lower() == key.lower():
            del audio.tags[existing]
    if value.strip():
        audio[key] = [value]


def find_lyric_sidecar(path: Path, extensions: tuple[str, ...]) -> Path | None:
    for extension in extensions:
        # Replace the audio extension exactly once. Creating an extensionless
        # intermediate Path and calling with_suffix() again breaks filenames
        # containing dots, such as "(feat._Artist).flac".
        candidate = path.with_suffix(extension)
        if candidate.is_file() and candidate.stat().st_size > 0:
            return candidate
    scratch = Path(str(path) + "._vad_ten.srt")
    if ".srt" in extensions and scratch.is_file() and scratch.stat().st_size > 0:
        return scratch
    return None


def strip_lrc_timestamps(line: str) -> str:
    return re.sub(r"(\[[0-9]{1,2}:[0-9]{2}(?:\.[0-9]{1,3})?\])+", "", line).strip()


def is_sidecar_comment_line(line: str) -> bool:
    """Treat hash-prefixed transcription notes as metadata, never lyrics."""
    return strip_lrc_timestamps(str(line)).lstrip().startswith("#")


def filtered_plain_lyric_text(text: str) -> str:
    """Remove transcription comments while preserving lyric stanza spacing."""
    lines = [
        raw.rstrip()
        for raw in str(text).replace("\r\n", "\n").replace("\r", "\n").split("\n")
        if not is_sidecar_comment_line(raw)
    ]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def normalized_lyric_payload(text: str) -> str:
    """Normalize line endings and outer whitespace without hiding comment text."""
    lines = [
        line.rstrip()
        for line in str(text).replace("\r\n", "\n").replace("\r", "\n").split("\n")
    ]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def plain_from_lrc(text: str) -> str:
    lines = [
        body
        for line in text.splitlines()
        if not is_sidecar_comment_line(line)
        and (body := strip_lrc_timestamps(line))
    ]
    return "\n".join(lines).strip() + ("\n" if lines else "")


def plain_from_srt(text: str) -> str:
    lines = [
        line
        for raw in text.splitlines()
        if (line := raw.strip())
        and not is_sidecar_comment_line(line)
        and not line.isdigit()
        and "-->" not in line
    ]
    return "\n".join(lines).strip() + ("\n" if lines else "")


def usable_plain_sidecar_content(path: Path) -> str:
    """Return normalized plain lyrics from a sidecar, or an empty string."""
    try:
        text = read_text(path)
    except Exception:
        return ""
    suffix = path.suffix.lower()
    if suffix == ".lrc":
        return plain_from_lrc(text).strip()
    if suffix == ".srt":
        return plain_from_srt(text).strip()
    return filtered_plain_lyric_text(text)


def first_usable_plain_sidecar(
    candidates: list[Path],
) -> tuple[Path | None, int]:
    """Choose the first sidecar containing actual plain lyric lines."""
    for candidate in candidates:
        content = usable_plain_sidecar_content(candidate)
        lines = [line for line in content.splitlines() if line.strip()]
        if lines:
            return candidate, len(lines)
    return None, 0


def srt_time_to_lrc(time_text: str) -> str:
    hours, minutes, rest = time_text.split(":")
    seconds, milliseconds = rest.split(",")
    total_minutes = int(hours) * 60 + int(minutes)
    hundredths = int(round(int(milliseconds) / 10.0))
    if hundredths == 100:
        seconds = str(int(seconds) + 1)
        hundredths = 0
    return f"[{total_minutes:02d}:{int(seconds):02d}.{hundredths:02d}]"


def lrc_from_srt(text: str) -> str:
    output = []
    for block in re.split(r"\r?\n\r?\n+", text.strip()):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        timing_index = next((index for index, line in enumerate(lines) if "-->" in line), None)
        if timing_index is None:
            continue
        try:
            timestamp = srt_time_to_lrc(lines[timing_index].split("-->", 1)[0].strip())
        except Exception:
            continue
        lyric = " ".join(
            line
            for line in lines[timing_index + 1 :]
            if not is_sidecar_comment_line(line)
        ).strip()
        if lyric:
            output.append(f"{timestamp}{lyric}")
    return "\n".join(output).strip() + ("\n" if output else "")


def parse_lrc_for_sylt(text: str) -> list[tuple[str, int]]:
    entries: list[tuple[str, int]] = []
    for line in text.splitlines():
        timestamps = re.findall(
            r"\[([0-9]{1,2}):([0-9]{2})(?:\.([0-9]{1,3}))?\]", line
        )
        body = strip_lrc_timestamps(line)
        if not body or is_sidecar_comment_line(body):
            continue
        for minutes, seconds, fraction in timestamps:
            fraction = fraction or "0"
            milliseconds = int(minutes) * 60000 + int(seconds) * 1000
            milliseconds += int(fraction.ljust(3, "0")[:3])
            entries.append((body, milliseconds))
    return entries


def normalized_timed_lyric_text(text: str) -> str:
    """Retain only timestamped lyric lines, excluding sidecar commentary."""
    lines: list[str] = []
    for raw in str(text).replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw.strip()
        if (
            line
            and re.search(
                r"\[[0-9]{1,2}:[0-9]{2}(?:\.[0-9]{1,3})?\]",
                line,
            )
            and strip_lrc_timestamps(line)
            and not is_sidecar_comment_line(line)
        ):
            lines.append(line)
    return "\n".join(lines)


def timed_sidecar_content(path: Path) -> str:
    """Return canonical embeddable LRC text from a usable LRC or SRT sidecar."""
    text = read_text(path)
    if path.suffix.lower() == ".srt":
        text = lrc_from_srt(text)
    return normalized_timed_lyric_text(text)


def lrc_is_derived_from_srt(lrc: Path, srt: Path) -> bool:
    """Recognize an LRC generated from this SRT, not manually edited in MiniLyrics.

    ``srt2lrc.py`` does not leave a persistent marker.  Compare its meaningful
    timestamp/text entries instead, ignoring harmless end-blank cues and
    sidecar comments.  A marked lrc2srt output is also categorically treated
    as LRC-authored, so a newer LRC should refresh it.
    """
    try:
        srt_text = read_text(srt)
        if LRC2SRT_GENERATED_MARKER.casefold() in srt_text.casefold():
            return False
        lrc_entries = parse_lrc_for_sylt(timed_sidecar_content(lrc))
        srt_entries = parse_lrc_for_sylt(
            normalized_timed_lyric_text(lrc_from_srt(srt_text))
        )
    except Exception:
        return False
    return bool(lrc_entries) and lrc_entries == srt_entries


def lrc2srt_executable() -> Path | None:
    """Locate the user's lrc2srt tool beside this auditor or in C:\\BAT."""
    candidates = (
        _SCRIPT_DIR / "lrc2srt.py",
        Path(r"C:\BAT\lrc2srt.py"),
    )
    return next((candidate for candidate in candidates if candidate.is_file()), None)


def generate_missing_srt_sidecars(
    root: Path,
    audio_or_folder: Path,
    *,
    expected_audio_paths: list[Path] | None = None,
) -> list[str]:
    """Run the folder-scoped Lyric/Karaoke Fix and verify every expected SRT."""
    target_folder = (
        audio_or_folder
        if audio_or_folder.is_dir()
        else audio_or_folder.parent
    )
    expected_audio = list(expected_audio_paths or [])
    if not expected_audio and audio_or_folder.is_file():
        expected_audio = [audio_or_folder]
    if not expected_audio:
        expected_audio = [
            path
            for path in target_folder.iterdir()
            if path.is_file()
            and path.suffix.casefold() in AUDIO_EXTS
            and find_lyric_sidecar(path, (".lrc",)) is not None
            and find_lyric_sidecar(path, (".txt",)) is not None
            and find_lyric_sidecar(path, (".srt",)) is None
        ]
    if not expected_audio:
        return [f"lyric_karaoke_fix_summary:0|0|{target_folder}"]

    for audio_path in expected_audio:
        lrc = find_lyric_sidecar(audio_path, (".lrc",))
        if lrc is None:
            raise RuntimeError(
                f"The matching timestamped LRC sidecar is unavailable: {audio_path.name}"
            )

    # A precomputed finding can become stale before we reach it. Also, the
    # auditor deliberately treats a zero-byte SRT as missing while lrc2srt.py
    # treats any existing filename as "already had SRT". Resolve both cases
    # before invoking the tool so a harmless stale/empty file cannot turn into
    # a confusing command failure.
    already_valid: list[Path] = []
    recycled_empty: list[Path] = []
    for audio_path in expected_audio:
        srt = audio_path.with_suffix(".srt")
        if srt.is_file():
            try:
                size = srt.stat().st_size
            except FileNotFoundError:
                size = 0
            if size > 0:
                already_valid.append(srt)
            else:
                recycle_path(srt)
                recycled_empty.append(srt)

    pending_audio = [
        audio_path
        for audio_path in expected_audio
        if not audio_path.with_suffix(".srt").is_file()
    ]
    if not pending_audio:
        print(
            console_safe_text(
                f"            ✅ Lyric/Karaoke Fix: all {len(expected_audio)} "
                f"expected SRT sidecar{'s are' if len(expected_audio) != 1 else ' is'} "
                "already present; nothing to do."
            ),
            flush=True,
        )
        return [
            f"lyric_karaoke_fix_summary:0|{len(expected_audio)}|{target_folder}",
            *[f"confirmed_srt:{path}" for path in already_valid],
        ]

    tool = lrc2srt_executable()
    if tool is None:
        raise RuntimeError(
            "lrc2srt.py was not found beside the auditor or in C:\\BAT"
        )
    command = [
        sys.executable,
        str(tool),
        "MiniLyricsFix",  # internal lrc2srt.py mode name; never shown to user
        "--recursive",
        "--automatic-overwrites",
    ]
    print(
        console_safe_text(
            "            🎤 Lyric/Karaoke Fix: generating missing SRT sidecars "
            f"for {target_folder}..."
        ),
        flush=True,
    )
    result = subprocess.run(
        command,
        cwd=str(target_folder),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="replace",
    )
    captured = str(getattr(result, "stdout", "") or "").strip()
    # Keep the implementation detail out of user-visible diagnostics.
    captured = captured.replace("MiniLyricsFix", "Lyric/Karaoke Fix")

    missing_after = [
        audio_path.with_suffix(".srt")
        for audio_path in expected_audio
        if not audio_path.with_suffix(".srt").is_file()
        or audio_path.with_suffix(".srt").stat().st_size <= 0
    ]
    if missing_after:
        names = ", ".join(path.name for path in missing_after[:5])
        if len(missing_after) > 5:
            names += f", … (+{len(missing_after) - 5} more)"
        detail = f"\n{captured}" if captured else ""
        raise RuntimeError(
            f"Lyric/Karaoke Fix did not create {len(missing_after)} expected SRT "
            f"sidecar{'s' if len(missing_after) != 1 else ''}: {names}{detail}"
        )

    # Some lrc2srt.py builds use a nonzero exit status for "nothing to do".
    # Verification above is authoritative: if every expected SRT now exists and
    # is nonempty, the folder action succeeded regardless of that status code.
    generated_count = len(pending_audio)
    print(
        console_safe_text(
            f"            ✅ Lyric/Karaoke Fix: verified {len(expected_audio)} SRT "
            f"sidecar{'s' if len(expected_audio) != 1 else ''} "
            f"({generated_count} generated)."
        ),
        flush=True,
    )
    return [
        f"lyric_karaoke_fix_summary:{generated_count}|{len(expected_audio)}|{target_folder}",
        *[f"recycled_empty_srt:{path}" for path in recycled_empty],
        *[
            f"confirmed_srt:{audio_path.with_suffix('.srt')}"
            for audio_path in expected_audio
        ],
    ]


def backfill_srt_from_lrc(audio_path: Path) -> list[str]:
    """Run the existing lrc2srt workflow for exactly one updated LRC sidecar."""
    lrc = find_lyric_sidecar(audio_path, (".lrc",))
    srt = find_lyric_sidecar(audio_path, (".srt",))
    tool = lrc2srt_executable()
    if lrc is None or srt is None:
        raise RuntimeError("Matching LRC and SRT sidecars are required")
    if tool is None:
        raise RuntimeError("lrc2srt.py was not found beside the auditor or in C:\\BAT")
    before_mtime = srt.stat().st_mtime_ns
    print(
        console_safe_text(
            f"            🎤 Running {tool.name} to backfill {srt.name} from {lrc.name}:"
        ),
        flush=True,
    )
    result = subprocess.run(
        [sys.executable, str(tool), str(lrc), "--automatic-overwrites"],
        cwd=str(lrc.parent),
        check=False,
    )
    if result.returncode:
        raise RuntimeError(f"lrc2srt.py exited with code {result.returncode}")
    if not srt.is_file() or srt.stat().st_mtime_ns <= before_mtime:
        raise RuntimeError("lrc2srt.py did not rewrite the matching SRT")
    return [f"backfilled_srt:{srt}"]


def lyric_refresh_reasons(
    audio_path: Path,
    sidecar_path: Path,
    expected: str,
    embedded: str,
    *,
    timed: bool = False,
) -> list[str]:
    """Explain why a sidecar must replace its prior embedded lyric payload."""
    normalize = normalized_timed_lyric_text if timed else normalized_lyric_payload
    reasons: list[str] = []
    if normalize(expected) != normalize(embedded):
        reasons.append("content differs from the embedded copy")
    try:
        if sidecar_path.stat().st_mtime_ns > audio_path.stat().st_mtime_ns:
            reasons.append("sidecar was regenerated after the last audio write")
    except OSError:
        pass
    return reasons


def usable_timed_sidecar_entries(path: Path) -> list[tuple[str, int]]:
    """Return validated timed lyric entries from LRC or SRT content."""
    try:
        text = timed_sidecar_content(path)
    except Exception:
        return []
    return parse_lrc_for_sylt(text)


def first_usable_timed_sidecar(
    candidates: list[Path],
) -> tuple[Path | None, int]:
    """Choose the first sidecar with at least one timed lyric entry."""
    for candidate in candidates:
        entries = usable_timed_sidecar_entries(candidate)
        if entries:
            return candidate, len(entries)
    return None, 0


def ensure_lyric_sidecars(path: Path, write: bool) -> tuple[Path | None, Path | None]:
    txt = find_lyric_sidecar(path, (".txt",))
    lrc = find_lyric_sidecar(path, (".lrc",))
    srt = find_lyric_sidecar(path, (".srt",))
    if txt is None and (lrc or srt):
        txt = path.with_suffix(".txt")
        plain_source, _line_count = first_usable_plain_sidecar(
            [
                candidate
                for candidate in (lrc, srt)
                if candidate and candidate.exists()
            ]
        )
        plain = (
            usable_plain_sidecar_content(plain_source)
            if plain_source
            else ""
        )
        if plain and write:
            txt.write_text(plain, encoding="utf-8")
        if not plain:
            txt = None
    if lrc is None and srt and "[instrumental]" not in path.name.lower():
        lrc = path.with_suffix(".lrc")
        timed = lrc_from_srt(read_text(srt))
        if timed and write:
            lrc.write_text(timed, encoding="utf-8")
        if not timed:
            lrc = None
    return txt, lrc


def embed_lyrics(
    path: Path,
    write: bool = True,
    *,
    force_refresh: bool = False,
) -> list[str]:
    txt, lrc = ensure_lyric_sidecars(path, write)
    srt = find_lyric_sidecar(path, (".srt",))
    plain_source, _plain_line_count = first_usable_plain_sidecar(
        [
            candidate
            for candidate in (txt, lrc, srt)
            if candidate and candidate.exists()
        ]
    )
    plain = (
        usable_plain_sidecar_content(plain_source)
        if plain_source
        else ""
    )
    timed_source, _timed_line_count = first_usable_timed_sidecar(
        [
            candidate
            for candidate in (lrc, srt)
            if candidate and candidate.exists()
        ]
    )
    synced = (
        timed_sidecar_content(timed_source)
        if timed_source
        else ""
    )
    synced_entries = parse_lrc_for_sylt(synced) if synced else []
    if not synced_entries:
        synced = ""
    actions: list[str] = []
    if path.suffix.lower() == ".flac":
        audio = FLAC(path)
        current_plain_values = list_values(
            audio.get("LYRICS") or audio.get("UNSYNCEDLYRICS")
        )
        current_synced_values = list_values(audio.get("SYNCEDLYRICS"))
        current_plain = (
            current_plain_values[0] if current_plain_values else ""
        )
        current_synced = (
            current_synced_values[0] if current_synced_values else ""
        )
        plain_needs_refresh = bool(
            plain
            and plain_source
            and (
                force_refresh
                or lyric_refresh_reasons(
                    path,
                    plain_source,
                    plain,
                    current_plain,
                )
            )
        )
        synced_needs_refresh = bool(
            synced
            and timed_source
            and (
                force_refresh
                or lyric_refresh_reasons(
                    path,
                    timed_source,
                    synced,
                    current_synced,
                    timed=True,
                )
            )
        )
        if not write:
            return [
                action
                for needed, action in (
                    (plain_needs_refresh, "embed_plain_lyrics"),
                    (synced_needs_refresh, "embed_synced_lyrics"),
                )
                if needed
            ]
        if plain_needs_refresh:
            set_flac_value(audio, "LYRICS", plain)
            set_flac_value(audio, "UNSYNCEDLYRICS", plain)
            actions.append("plain_lyrics")
        if synced_needs_refresh:
            set_flac_value(audio, "SYNCEDLYRICS", synced)
            actions.append("synced_lyrics")
        if actions:
            backup = backup_before_inline_replacement(path)
            audio.save()
            actions.insert(0, f"backup:{backup}")
        return actions

    audio = ensure_id3(path)
    tags = audio.tags
    unsynced_frames = tags.getall("USLT")
    current_plain = (
        str(getattr(unsynced_frames[0], "text", ""))
        if unsynced_frames
        else ""
    )
    current_synced = ""
    for frame in tags.getall("TXXX"):
        if getattr(frame, "desc", "").upper() == "SYNCEDLYRICS":
            values = [str(value) for value in getattr(frame, "text", [])]
            if values:
                current_synced = values[0]
                break
    plain_needs_refresh = bool(
        plain
        and plain_source
        and (
            force_refresh
            or lyric_refresh_reasons(
                path,
                plain_source,
                plain,
                current_plain,
            )
        )
    )
    synced_needs_refresh = bool(
        synced
        and timed_source
        and (
            force_refresh
            or lyric_refresh_reasons(
                path,
                timed_source,
                synced,
                current_synced,
                timed=True,
            )
        )
    )
    if not write:
        return [
            action
            for needed, action in (
                (plain_needs_refresh, "embed_plain_lyrics"),
                (synced_needs_refresh, "embed_synced_lyrics"),
            )
            if needed
        ]
    if plain_needs_refresh:
        tags.delall("USLT")
        tags.add(USLT(encoding=3, lang="eng", desc="", text=plain))
        actions.append("plain_lyrics")
    if synced_needs_refresh:
        tags.delall("SYLT")
        for key in list(tags.keys()):
            if key.startswith("TXXX") and getattr(tags[key], "desc", "").upper() == "SYNCEDLYRICS":
                del tags[key]
        tags.add(
            SYLT(
                encoding=3,
                lang="eng",
                format=2,
                type=1,
                desc="",
                text=synced_entries,
            )
        )
        tags.add(TXXX(encoding=3, desc="SYNCEDLYRICS", text=[synced]))
        actions.append("synced_lyrics")
    if actions:
        backup = backup_before_inline_replacement(path)
        audio.save(v2_version=3)
        actions.insert(0, f"backup:{backup}")
    return actions


def first_text(values: Any) -> str:
    """Return the first nonblank scalar from a tag/API value."""
    for value in list_values(values):
        if str(value).strip():
            return str(value).strip()
    return ""


def cover_lookup_metadata(path: Path) -> dict[str, Any]:
    """Read conservative release-identification fields from one audio file."""
    if mutagen_file is None:
        raise RuntimeError("mutagen is required to read cover-search metadata")
    audio = mutagen_file(path)
    if audio is None:
        raise RuntimeError(f"Could not read audio metadata: {path}")
    tags = getattr(audio, "tags", None)
    metadata: dict[str, Any] = {
        "title": "",
        "artist": "",
        "album_artist": "",
        "album": "",
        "date": "",
        "track_count": 0,
        "release_id": "",
        "release_group_id": "",
    }
    if path.suffix.lower() == ".flac":
        tagmap = {
            str(key).upper(): list_values(value)
            for key, value in (tags or {}).items()
        }
        metadata.update(
            title=first_text(tagmap.get("TITLE")),
            artist=first_text(tagmap.get("ARTIST")),
            album_artist=first_text(tagmap.get("ALBUMARTIST")),
            album=first_text(tagmap.get("ALBUM")),
            date=first_text(tagmap.get("DATE"))
            or first_text(tagmap.get("ORIGINALDATE")),
            release_id=first_text(tagmap.get("MUSICBRAINZ_ALBUMID"))
            or first_text(tagmap.get("MUSICBRAINZ_RELEASEID")),
            release_group_id=first_text(
                tagmap.get("MUSICBRAINZ_RELEASEGROUPID")
            ),
        )
        track_text = first_text(tagmap.get("TRACKNUMBER"))
        total_text = (
            first_text(tagmap.get("TOTALTRACKS"))
            or first_text(tagmap.get("TRACKTOTAL"))
        )
    else:
        metadata.update(
            title=first_text(frame_text(tags, "TIT2")) if tags else "",
            artist=first_text(frame_text(tags, "TPE1")) if tags else "",
            album_artist=first_text(frame_text(tags, "TPE2")) if tags else "",
            album=first_text(frame_text(tags, "TALB")) if tags else "",
            date=first_text(frame_text(tags, "TDRC")) if tags else "",
        )
        track_text = first_text(frame_text(tags, "TRCK")) if tags else ""
        total_text = ""
        for frame in tags.getall("TXXX") if tags else []:
            description = str(getattr(frame, "desc", "")).strip().casefold()
            value = first_text(getattr(frame, "text", []))
            if description in {
                "musicbrainz album id",
                "musicbrainz release id",
            }:
                metadata["release_id"] = value
            elif description == "musicbrainz release group id":
                metadata["release_group_id"] = value
            elif description in {"totaltracks", "tracktotal"}:
                total_text = value
    total_match = re.search(r"(?:/|\b)(\d{1,3})\s*$", track_text)
    if total_text.isdigit():
        metadata["track_count"] = int(total_text)
    elif total_match and "/" in track_text:
        metadata["track_count"] = int(total_match.group(1))

    folder_artist = recognized_album_artist(path.parent)
    folder_album = re.sub(
        r"^\s*(?:19|20)\d{2}\s*[-–—]\s*",
        "",
        path.parent.name,
    ).strip()
    special_child = path.parent.name.strip().casefold() in SPECIAL_ARTIST_CHILD_FOLDERS
    if not metadata["album"] and folder_artist and not special_child:
        metadata["album"] = folder_album
    if not metadata["album_artist"] and folder_artist:
        metadata["album_artist"] = folder_artist
    if not metadata["artist"]:
        metadata["artist"] = metadata["album_artist"]
    if not metadata["album_artist"]:
        metadata["album_artist"] = metadata["artist"]
    if not metadata["album"] and special_child and metadata["title"]:
        # A loose track has no honest album to invent.  The release search can
        # still use its title as a conservative single/release-title fallback.
        metadata["album"] = metadata["title"]
    if not metadata["date"]:
        year_match = re.match(r"^\s*((?:19|20)\d{2})\b", path.parent.name)
        if year_match:
            metadata["date"] = year_match.group(1)
    if not metadata["track_count"] and metadata["album"]:
        track_numbers = {
            int(match.group(1))
            for sibling in path.parent.iterdir()
            if sibling.is_file()
            and sibling.suffix.lower() in AUDIO_EXTS
            and (match := re.match(r"^(\d{1,3})[-_. ]+", sibling.name))
        }
        metadata["track_count"] = len(track_numbers)
    return metadata


def _musicbrainz_wait() -> None:
    """Honor MusicBrainz's average one-request-per-second limit."""
    global _LAST_MUSICBRAINZ_REQUEST_AT
    elapsed = time.monotonic() - _LAST_MUSICBRAINZ_REQUEST_AT
    if _LAST_MUSICBRAINZ_REQUEST_AT and elapsed < 1.05:
        time.sleep(1.05 - elapsed)
    _LAST_MUSICBRAINZ_REQUEST_AT = time.monotonic()


def verified_https_context() -> ssl.SSLContext:
    """Build a verified context, preferring certifi when Python has no CA file."""
    if certifi is not None:
        try:
            return ssl.create_default_context(cafile=certifi.where())
        except Exception:
            pass
    return ssl.create_default_context()


def certificate_failure(reason: Any) -> bool:
    """Recognize direct or urllib-wrapped certificate verification failures."""
    return isinstance(reason, ssl.SSLCertVerificationError) or (
        "certificate verify failed" in str(reason).casefold()
    )


def cover_archive_json_fallback_url(url: str) -> str | None:
    """Map one CAA release JSON endpoint to its verified Internet Archive copy."""
    match = re.fullmatch(
        r"https?://coverartarchive\.org/release/"
        r"([0-9a-fA-F-]{36})/?",
        url,
    )
    if not match:
        return None
    release_id = match.group(1)
    return (
        f"https://archive.org/download/mbid-{release_id}/index.json"
    )


def cover_archive_image_fallback_url(url: str) -> str | None:
    """Map a CAA release image URL directly to its Internet Archive object."""
    match = re.match(
        r"https?://coverartarchive\.org/release/"
        r"(?P<release>[0-9a-fA-F-]{36})/"
        r"(?P<image>\d+)(?:-\d+)?(?:\.[A-Za-z0-9]+)?(?:\?.*)?$",
        url,
    )
    if not match:
        return None
    release_id = match.group("release")
    image_id = match.group("image")
    return (
        f"https://archive.org/download/mbid-{release_id}/"
        f"mbid-{release_id}-{image_id}.jpg"
    )


def cover_http_get_json(
    url: str,
    *,
    musicbrainz: bool = False,
) -> dict[str, Any] | None:
    """Fetch JSON with bounded timeouts, identification, and useful failures."""
    if musicbrainz:
        _musicbrainz_wait()
    request = Request(
        url,
        headers={
            "User-Agent": COVER_USER_AGENT,
            "Accept": "application/json",
        },
    )
    try:
        with urlopen(
            request,
            timeout=COVER_HTTP_TIMEOUT_SECONDS,
            context=verified_https_context(),
        ) as response:
            payload = response.read(COVER_MAX_DOWNLOAD_BYTES + 1)
    except HTTPError as exc:
        if exc.code == 404:
            return None
        raise RuntimeError(f"HTTP {exc.code} while requesting {url}") from exc
    except URLError as exc:
        fallback = (
            cover_archive_json_fallback_url(url)
            if certificate_failure(exc.reason)
            else None
        )
        if fallback is not None:
            return cover_http_get_json(fallback)
        if certificate_failure(exc.reason):
            raise RuntimeError(
                "TLS certificate validation failed while requesting "
                f"{url}; certifi/default CA verification and the verified "
                "Internet Archive fallback could not complete"
            ) from exc
        raise RuntimeError(f"Network error while requesting {url}: {exc.reason}") from exc
    if len(payload) > COVER_MAX_DOWNLOAD_BYTES:
        raise RuntimeError(f"JSON response exceeded safety limit: {url}")
    try:
        decoded = json.loads(payload.decode("utf-8"))
    except Exception as exc:
        raise RuntimeError(f"Server returned invalid JSON: {url}") from exc
    return decoded if isinstance(decoded, dict) else None


def cover_http_get_bytes(url: str) -> tuple[bytes, str, str]:
    """Download exactly one bounded image response and return its final URL."""
    request = Request(
        url,
        headers={
            "User-Agent": COVER_USER_AGENT,
            "Accept": "image/*",
        },
    )
    try:
        with urlopen(
            request,
            timeout=COVER_HTTP_TIMEOUT_SECONDS,
            context=verified_https_context(),
        ) as response:
            content_type = response.headers.get_content_type()
            final_url = response.geturl()
            payload = response.read(COVER_MAX_DOWNLOAD_BYTES + 1)
    except HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} while downloading artwork") from exc
    except URLError as exc:
        fallback = (
            cover_archive_image_fallback_url(url)
            if certificate_failure(exc.reason)
            else None
        )
        if fallback is not None:
            return cover_http_get_bytes(fallback)
        if certificate_failure(exc.reason):
            raise RuntimeError(
                "Artwork TLS certificate validation failed after the "
                "certifi/default CA and Internet Archive fallback attempts"
            ) from exc
        raise RuntimeError(f"Artwork download failed: {exc.reason}") from exc
    if len(payload) > COVER_MAX_DOWNLOAD_BYTES:
        raise RuntimeError("Artwork exceeded the 100 MiB download safety limit")
    return payload, content_type, final_url


def cover_http_get_text(url: str) -> str:
    """Fetch one bounded UTF-8 HTML page used for artwork-source discovery."""
    request = Request(
        url,
        headers={
            "User-Agent": COVER_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    try:
        with urlopen(
            request,
            timeout=COVER_HTTP_TIMEOUT_SECONDS,
            context=verified_https_context(),
        ) as response:
            payload = response.read(COVER_MAX_DOWNLOAD_BYTES + 1)
            charset = response.headers.get_content_charset() or "utf-8"
    except HTTPError as exc:
        if exc.code == 404:
            return ""
        raise RuntimeError(f"HTTP {exc.code} while searching Bandcamp") from exc
    except URLError as exc:
        raise RuntimeError(
            f"Bandcamp artwork search failed: {exc.reason}"
        ) from exc
    if len(payload) > COVER_MAX_DOWNLOAD_BYTES:
        raise RuntimeError("Bandcamp page exceeded the response safety limit")
    return payload.decode(charset, errors="replace")


def normalized_match_text(text: str) -> str:
    """Normalize release text for conservative similarity comparisons."""
    normalized = unicodedata.normalize("NFKD", str(text))
    ascii_text = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )
    return " ".join(re.findall(r"[a-z0-9]+", ascii_text.casefold()))


def release_artist_text(release: dict[str, Any]) -> str:
    """Flatten a MusicBrainz artist-credit array into its credited text."""
    credits = release.get("artist-credit", [])
    if not isinstance(credits, list):
        return ""
    parts: list[str] = []
    for credit in credits:
        if isinstance(credit, str):
            parts.append(credit)
        elif isinstance(credit, dict):
            parts.append(
                str(
                    credit.get("name")
                    or credit.get("artist", {}).get("name")
                    or ""
                )
            )
            parts.append(str(credit.get("joinphrase") or ""))
    return "".join(parts).strip()


def release_track_count(release: dict[str, Any]) -> int:
    """Return a MusicBrainz release's total track count."""
    media = release.get("media", [])
    if not isinstance(media, list):
        return 0
    return sum(
        int(medium.get("track-count") or medium.get("track_count") or 0)
        for medium in media
        if isinstance(medium, dict)
    )


def release_formats(release: dict[str, Any]) -> tuple[str, ...]:
    """Return the nonblank medium formats attached to a release."""
    return tuple(
        str(medium.get("format")).strip()
        for medium in release.get("media", [])
        if isinstance(medium, dict) and str(medium.get("format") or "").strip()
    )


def caa_artworks(payload: dict[str, Any] | None) -> tuple[CoverArtwork, ...]:
    """Parse approved Cover Art Archive entries and keep one primary Front."""
    if not payload:
        return ()
    parsed: list[CoverArtwork] = []
    seen: set[str] = set()
    front_seen = False
    for index, image in enumerate(payload.get("images", []), start=1):
        if not isinstance(image, dict) or not image.get("approved", True):
            continue
        url = str(image.get("image") or "").strip()
        if not url or url in seen:
            continue
        front = bool(image.get("front"))
        if front and front_seen:
            continue
        if front:
            front_seen = True
        seen.add(url)
        parsed.append(
            CoverArtwork(
                image_id=str(image.get("id") or index),
                url=url,
                types=tuple(
                    str(value)
                    for value in image.get("types", [])
                    if str(value).strip()
                ),
                comment=str(image.get("comment") or "").strip(),
                front=front,
                approved=bool(image.get("approved", True)),
            )
        )
    return tuple(parsed)


def merge_release_group_front(
    artworks: tuple[CoverArtwork, ...],
    release_group_id: str,
    json_fetcher: Callable[..., dict[str, Any] | None],
) -> tuple[CoverArtwork, ...]:
    """Use a release-group Front only when the exact release has none."""
    if any(artwork.front for artwork in artworks) or not release_group_id:
        return artworks
    payload = json_fetcher(
        f"{COVER_ART_ARCHIVE_ROOT}/release-group/{release_group_id}",
        musicbrainz=False,
    )
    group_front = next(
        (artwork for artwork in caa_artworks(payload) if artwork.front),
        None,
    )
    return ((group_front,) + artworks) if group_front else artworks


def cover_release_score(
    release: dict[str, Any],
    metadata: dict[str, Any],
) -> int:
    """Combine MusicBrainz's score with explicit album/artist/date/track checks."""
    album = str(metadata.get("album") or "")
    artist = str(metadata.get("album_artist") or metadata.get("artist") or "")
    release_album = str(release.get("title") or "")
    release_artist = release_artist_text(release)
    album_ratio = SequenceMatcher(
        None,
        normalized_match_text(album),
        normalized_match_text(release_album),
    ).ratio()
    artist_ratio = SequenceMatcher(
        None,
        normalized_match_text(artist),
        normalized_match_text(release_artist),
    ).ratio()
    api_score = int(release.get("score") or 0) / 100.0
    score = 45 * album_ratio + 30 * artist_ratio + 20 * api_score
    wanted_year = re.search(r"(?:19|20)\d{2}", str(metadata.get("date") or ""))
    result_year = re.search(r"(?:19|20)\d{2}", str(release.get("date") or ""))
    if wanted_year and result_year:
        score += 5 if wanted_year.group() == result_year.group() else 0
    else:
        score += 3
    wanted_tracks = int(metadata.get("track_count") or 0)
    result_tracks = release_track_count(release)
    if wanted_tracks and result_tracks and wanted_tracks != result_tracks:
        score -= 8
    elif wanted_tracks and result_tracks:
        score += 5
    return max(0, min(100, round(score)))


def _release_group_id(release: dict[str, Any]) -> str:
    group = release.get("release-group", {})
    return str(group.get("id") or "") if isinstance(group, dict) else ""


def musicbrainz_search_url(metadata: dict[str, Any]) -> str:
    """Build a fielded MusicBrainz release search URL."""
    album = str(metadata.get("album") or "").replace('"', "")
    artist = str(
        metadata.get("album_artist") or metadata.get("artist") or ""
    ).replace('"', "")
    terms = [f'release:"{album}"', f'artist:"{artist}"']
    year_match = re.search(r"(?:19|20)\d{2}", str(metadata.get("date") or ""))
    if year_match:
        terms.append(f"date:{year_match.group()}")
    track_count = int(metadata.get("track_count") or 0)
    if track_count:
        terms.append(f"tracks:{track_count}")
    return (
        f"{MUSICBRAINZ_API_ROOT}/release/?"
        + urlencode(
            {
                "query": " AND ".join(terms),
                "fmt": "json",
                "limit": 8,
            }
        )
    )


def bandcamp_search_url(metadata: dict[str, Any]) -> str:
    """Build Bandcamp's artist-plus-release search query."""
    artist = str(
        metadata.get("album_artist") or metadata.get("artist") or ""
    ).strip()
    release = str(metadata.get("album") or metadata.get("title") or "").strip()
    return f"{BANDCAMP_SEARCH_ROOT}?{urlencode({'q': f'{artist} {release}'})}"


def itunes_search_url(metadata: dict[str, Any]) -> str:
    """Build a conservative Apple Music/iTunes album-catalog search URL."""
    artist = str(
        metadata.get("album_artist") or metadata.get("artist") or ""
    ).strip()
    album = str(metadata.get("album") or metadata.get("title") or "").strip()
    params = {
        'term': f'{artist} {album}',
        'entity': 'album',
        'limit': 25,
        'country': 'US',
    }
    return f"{ITUNES_SEARCH_ROOT}?{urlencode(params)}"


def _html_plain_text(value: str) -> str:
    """Reduce a small HTML result fragment to normalized visible text."""
    return " ".join(
        html.unescape(re.sub(r"<[^>]+>", " ", value)).split()
    )


def _html_meta_content(page: str, key: str) -> str:
    """Read a meta property/name regardless of attribute order."""
    for tag in re.findall(r"<meta\b[^>]*>", page, flags=re.IGNORECASE):
        attributes = {
            name.casefold(): html.unescape(value)
            for name, _quote, value in re.findall(
                r"""([:\w-]+)\s*=\s*(["'])(.*?)\2""",
                tag,
                flags=re.IGNORECASE | re.DOTALL,
            )
        }
        if (
            attributes.get("property", "").casefold() == key.casefold()
            or attributes.get("name", "").casefold() == key.casefold()
        ):
            return attributes.get("content", "").strip()
    return ""


def _bandcamp_original_art_url(url: str) -> str:
    """Ask Bandcamp's image CDN for its original artwork rendition."""
    return re.sub(
        r"(?i)(https://[^/?#]*bcbits\.com/img/a\d+)_\d+"
        r"(\.[a-z0-9]+)(?=$|[?#])",
        r"\1_0\2",
        url,
    )


def bandcamp_cover_match(
    metadata: dict[str, Any],
    text_fetcher: Callable[[str], str],
) -> CoverMatch | None:
    """Return a conservatively scored Bandcamp release with original Front art."""
    try:
        search_page = text_fetcher(bandcamp_search_url(metadata))
    except RuntimeError:
        return None
    if not search_page:
        return None
    blocks = re.findall(
        r"<li\b[^>]*\bclass=[\"'][^\"']*\bsearchresult\b[^\"']*[\"']"
        r"[^>]*>(.*?)</li>",
        search_page,
        flags=re.IGNORECASE | re.DOTALL,
    )
    wanted_album = normalized_match_text(
        str(metadata.get("album") or metadata.get("title") or "")
    )
    wanted_artist = normalized_match_text(
        str(metadata.get("album_artist") or metadata.get("artist") or "")
    )
    candidates: list[tuple[int, str]] = []
    for block in blocks:
        href_match = re.search(
            r"""href=["'](https?://[^"']+\.bandcamp\.com/"""
            r"""(?:album|track)/[^"'?#]+)""",
            block,
            flags=re.IGNORECASE,
        )
        if not href_match:
            continue
        visible = normalized_match_text(_html_plain_text(block))
        album_ratio = SequenceMatcher(None, wanted_album, visible).ratio()
        artist_ratio = SequenceMatcher(None, wanted_artist, visible).ratio()
        confidence = round(60 * album_ratio + 40 * artist_ratio)
        if wanted_album and wanted_album in visible:
            confidence += 20
        if wanted_artist and wanted_artist in visible:
            confidence += 15
        if (
            wanted_album
            and wanted_artist
            and wanted_album in visible
            and wanted_artist in visible
        ):
            confidence = max(confidence, 96)
        candidates.append(
            (min(100, confidence), html.unescape(href_match.group(1)))
        )
    if not candidates:
        return None
    confidence, release_url = max(candidates, key=lambda item: item[0])
    if confidence < 82:
        return None
    try:
        release_page = text_fetcher(release_url)
    except RuntimeError:
        return None
    image_url = _html_meta_content(release_page, "og:image")
    if not image_url:
        return None
    page_title = _html_meta_content(release_page, "title")
    if ", by " in page_title:
        album, artist = page_title.rsplit(", by ", 1)
    else:
        album = (
            _html_meta_content(release_page, "og:title")
            or str(metadata.get("album") or "")
        )
        artist = str(
            metadata.get("album_artist") or metadata.get("artist") or ""
        )
    release_id = release_url.rstrip("/").rsplit("/", 1)[-1]
    return CoverMatch(
        source="Bandcamp",
        release_id=release_id,
        release_group_id="",
        artist=artist.strip(),
        album=album.strip(),
        date=str(metadata.get("date") or ""),
        country="",
        formats=("Digital",),
        confidence=confidence,
        exact_id=False,
        ambiguous=confidence < 94,
        artworks=(
            CoverArtwork(
                image_id=release_id,
                url=_bandcamp_original_art_url(image_url),
                types=("Front",),
                comment="Bandcamp original release artwork",
                front=True,
                approved=True,
            ),
        ),
    )


def _itunes_original_art_url(url: str) -> str:
    """Request the largest standard iTunes artwork rendition from its CDN."""
    return re.sub(r"/\d+x\d+(?:bb)?(?=[.-])", "/3000x3000bb", url)


def itunes_cover_match(
    metadata: dict[str, Any],
    json_fetcher: Callable[..., dict[str, Any] | None],
) -> CoverMatch | None:
    """Return a conservatively matched Apple Music/iTunes Front artwork image."""
    payload = json_fetcher(itunes_search_url(metadata), musicbrainz=False) or {}
    results = payload.get("results", [])
    if not isinstance(results, list):
        return None
    wanted_album = normalized_match_text(
        str(metadata.get("album") or metadata.get("title") or "")
    )
    wanted_artist = normalized_match_text(
        str(metadata.get("album_artist") or metadata.get("artist") or "")
    )
    candidates: list[tuple[int, dict[str, Any]]] = []
    for result in results:
        if not isinstance(result, dict):
            continue
        artwork_url = str(result.get("artworkUrl100") or "").strip()
        album = normalized_match_text(str(result.get("collectionName") or ""))
        artist = normalized_match_text(str(result.get("artistName") or ""))
        if not artwork_url or not album or not artist:
            continue
        confidence = round(
            60 * SequenceMatcher(None, wanted_album, album).ratio()
            + 40 * SequenceMatcher(None, wanted_artist, artist).ratio()
        )
        if wanted_album and wanted_album == album:
            confidence += 20
        if wanted_artist and wanted_artist == artist:
            confidence += 15
        candidates.append((min(100, confidence), result))
    if not candidates:
        return None
    confidence, result = max(candidates, key=lambda item: item[0])
    if confidence < 86:
        return None
    artwork_url = str(result["artworkUrl100"])
    release_id = str(result.get("collectionId") or artwork_url)
    return CoverMatch(
        source="Apple Music / iTunes",
        release_id=release_id,
        release_group_id="",
        artist=str(result.get("artistName") or "").strip(),
        album=str(result.get("collectionName") or "").strip(),
        date=str(result.get("releaseDate") or metadata.get("date") or "")[:10],
        country=str(result.get("country") or ""),
        formats=("Digital",),
        confidence=confidence,
        exact_id=False,
        ambiguous=confidence < 96,
        artworks=(
            CoverArtwork(
                image_id=release_id,
                url=_itunes_original_art_url(artwork_url),
                types=("Front",),
                comment="Apple Music/iTunes catalog artwork",
                front=True,
                approved=True,
            ),
        ),
    )


def discogs_cover_match(
    metadata: dict[str, Any],
    json_fetcher: Callable[..., dict[str, Any] | None],
) -> CoverMatch | None:
    """Return a confirmation-required Discogs fallback when a token exists."""
    token = os.environ.get("DISCOGS_TOKEN", "").strip()
    if not token:
        return None
    params = {
        "type": "release",
        "artist": metadata.get("album_artist") or metadata.get("artist") or "",
        "release_title": metadata.get("album") or "",
        "per_page": 10,
        "token": token,
    }
    year_match = re.search(r"(?:19|20)\d{2}", str(metadata.get("date") or ""))
    if year_match:
        params["year"] = year_match.group()
    payload = json_fetcher(
        f"{DISCOGS_API_ROOT}/database/search?{urlencode(params)}",
        musicbrainz=False,
    )
    results = payload.get("results", []) if payload else []
    if not results:
        return None
    wanted_album = normalized_match_text(str(metadata.get("album") or ""))
    wanted_artist = normalized_match_text(
        str(metadata.get("album_artist") or metadata.get("artist") or "")
    )
    scored: list[tuple[int, dict[str, Any]]] = []
    for result in results:
        title_text = str(result.get("title") or "")
        result_artist, _, result_album = title_text.partition(" - ")
        album_ratio = SequenceMatcher(
            None, wanted_album, normalized_match_text(result_album)
        ).ratio()
        artist_ratio = SequenceMatcher(
            None, wanted_artist, normalized_match_text(result_artist)
        ).ratio()
        scored.append((round(60 * album_ratio + 40 * artist_ratio), result))
    confidence, best = max(scored, key=lambda item: item[0])
    resource_url = str(best.get("resource_url") or "")
    if not resource_url:
        return None
    release = json_fetcher(resource_url, musicbrainz=False) or {}
    images = release.get("images", [])
    artworks: list[CoverArtwork] = []
    for index, image in enumerate(images, start=1):
        url = str(image.get("uri") or image.get("resource_url") or "")
        if not url:
            continue
        primary = str(image.get("type") or "").casefold() == "primary"
        artworks.append(
            CoverArtwork(
                image_id=str(index),
                url=url,
                types=("Front",) if primary else ("Other",),
                comment="Discogs secondary image" if not primary else "",
                front=primary,
                approved=True,
            )
        )
    if not any(artwork.front for artwork in artworks):
        return None
    return CoverMatch(
        source="Discogs",
        release_id=str(best.get("id") or ""),
        release_group_id="",
        artist=str(metadata.get("album_artist") or metadata.get("artist") or ""),
        album=str(metadata.get("album") or ""),
        date=str(best.get("year") or metadata.get("date") or ""),
        country=str(best.get("country") or ""),
        formats=tuple(str(value) for value in best.get("format", []) if value),
        confidence=confidence,
        exact_id=False,
        ambiguous=True,
        artworks=tuple(artworks),
    )


def resolve_cover_match(
    path: Path,
    *,
    json_fetcher: Callable[..., dict[str, Any] | None] | None = None,
    text_fetcher: Callable[[str], str] | None = None,
) -> CoverMatch:
    """Resolve one release, preferring an exact tagged MusicBrainz release ID."""
    fetch_json = json_fetcher or cover_http_get_json
    metadata = cover_lookup_metadata(path)
    album = str(metadata.get("album") or "")
    artist = str(metadata.get("album_artist") or metadata.get("artist") or "")

    release_id = str(metadata.get("release_id") or "")
    release_group_id = str(metadata.get("release_group_id") or "")
    if release_id:
        lookup: dict[str, Any] | None = None
        if not album or not artist:
            lookup = fetch_json(
                f"{MUSICBRAINZ_API_ROOT}/release/{release_id}?"
                + urlencode(
                    {
                        "inc": "artist-credits+release-groups+media",
                        "fmt": "json",
                    }
                ),
                musicbrainz=True,
            )
            if lookup:
                release_group_id = release_group_id or _release_group_id(lookup)
                album = str(lookup.get("title") or album)
                artist = release_artist_text(lookup) or artist
        release_payload = fetch_json(
            f"{COVER_ART_ARCHIVE_ROOT}/release/{release_id}",
            musicbrainz=False,
        )
        artworks = caa_artworks(release_payload)
        if not any(artwork.front for artwork in artworks):
            lookup = lookup or fetch_json(
                f"{MUSICBRAINZ_API_ROOT}/release/{release_id}?"
                + urlencode(
                    {
                        "inc": "artist-credits+release-groups+media",
                        "fmt": "json",
                    }
                ),
                musicbrainz=True,
            )
            if lookup:
                release_group_id = release_group_id or _release_group_id(lookup)
                album = str(lookup.get("title") or album)
                artist = release_artist_text(lookup) or artist
                formats = release_formats(lookup)
                date = str(lookup.get("date") or metadata.get("date") or "")
                country = str(lookup.get("country") or "")
            else:
                formats = ()
                date = str(metadata.get("date") or "")
                country = ""
            artworks = merge_release_group_front(
                artworks,
                release_group_id,
                fetch_json,
            )
        else:
            formats = ()
            date = str(metadata.get("date") or "")
            country = ""
        if any(artwork.front for artwork in artworks):
            return CoverMatch(
                source="MusicBrainz / Cover Art Archive",
                release_id=release_id,
                release_group_id=release_group_id,
                artist=artist,
                album=album,
                date=date,
                country=country,
                formats=formats,
                confidence=100,
                exact_id=True,
                ambiguous=False,
                artworks=artworks,
            )

    if not album or not artist:
        raise RuntimeError(
            "Cover search needs both album and album-artist/artist metadata "
            "when no usable exact MusicBrainz Release ID is tagged"
        )

    search_payload = fetch_json(
        musicbrainz_search_url(metadata),
        musicbrainz=True,
    )
    releases = search_payload.get("releases", []) if search_payload else []
    scored = sorted(
        (
            (cover_release_score(release, metadata), release)
            for release in releases
            if isinstance(release, dict) and release.get("id")
        ),
        key=lambda item: item[0],
        reverse=True,
    )
    # Archive-backed releases come first because they can include the complete
    # approved set (back, inlay, disc, booklet, etc.), not merely a Front.
    for index, (confidence, release) in enumerate(scored[:5]):
        candidate_release_id = str(release["id"])
        candidate_group_id = _release_group_id(release)
        artworks = caa_artworks(
            fetch_json(
                f"{COVER_ART_ARCHIVE_ROOT}/release/{candidate_release_id}",
                musicbrainz=False,
            )
        )
        artworks = merge_release_group_front(
            artworks,
            candidate_group_id,
            fetch_json,
        )
        if not any(artwork.front for artwork in artworks):
            continue
        next_score = scored[index + 1][0] if index + 1 < len(scored) else 0
        ambiguous = confidence < 94 or confidence - next_score < 6
        return CoverMatch(
            source="MusicBrainz / Cover Art Archive",
            release_id=candidate_release_id,
            release_group_id=candidate_group_id,
            artist=release_artist_text(release),
            album=str(release.get("title") or ""),
            date=str(release.get("date") or ""),
            country=str(release.get("country") or ""),
            formats=release_formats(release),
            confidence=confidence,
            exact_id=False,
            ambiguous=ambiguous,
            artworks=artworks,
        )

    discogs = discogs_cover_match(metadata, fetch_json)
    if discogs:
        return discogs
    bandcamp = bandcamp_cover_match(
        metadata,
        text_fetcher or cover_http_get_text,
    )
    if bandcamp:
        return bandcamp
    itunes = itunes_cover_match(metadata, fetch_json)
    if itunes:
        return itunes
    raise RuntimeError(
        "No release with an approved Front image was found on "
        "MusicBrainz/Cover Art Archive, Discogs, Bandcamp, or Apple Music/iTunes"
        + (
            "; Discogs was checked"
            if os.environ.get("DISCOGS_TOKEN")
            else "; set DISCOGS_TOKEN to enable the Discogs artwork-set fallback"
        )
    )


def artwork_stem(artwork: CoverArtwork, match: CoverMatch) -> str:
    """Map artwork metadata to stable folder-sidecar names."""
    if artwork.front:
        return "cover"
    types = {value.casefold() for value in artwork.types}
    comment = artwork.comment.casefold()
    if "matrix/runout" in types or "matrix" in comment or "runout" in comment:
        return "matrix"
    if "lyrics" in comment:
        return "lyrics"
    if "inlay" in comment or "liner" in types:
        return "inlay"
    if "back" in types:
        return "back"
    if "booklet" in types:
        return "booklet"
    if "medium" in types:
        joined_formats = " ".join(match.formats).casefold()
        if "vinyl" in joined_formats:
            return "vinyl"
        if any(
            token in joined_formats
            for token in ("cd", "sacd", "dvd", "blu-ray", "minidisc")
        ):
            return "disc"
        if "cassette" in joined_formats:
            return "cassette"
        return "disc"
    for cover_type, stem in (
        ("tray", "tray"),
        ("spine", "spine"),
        ("obi", "obi"),
        ("track", "track"),
        ("poster", "poster"),
        ("sticker", "sticker"),
        ("panel", "panel"),
    ):
        if cover_type in types:
            return stem
    return "artwork"


def artwork_name_plan(
    match: CoverMatch,
    audio_path: Path,
    *,
    album_scope: bool,
) -> list[tuple[CoverArtwork, str]]:
    """Assign stable, non-overwriting JPG names to every distinct image."""
    counts: Counter[str] = Counter()
    plan: list[tuple[CoverArtwork, str]] = []
    for artwork in match.artworks:
        stem = artwork_stem(artwork, match)
        counts[stem] += 1
        if counts[stem] > 1:
            stem = f"{stem}-{counts[stem]}"
        if artwork.front:
            name = f"{stem}.jpg"
        elif album_scope:
            name = f"{stem}.jpg"
        else:
            name = f"{audio_path.stem}.{stem}.jpg"
        plan.append((artwork, name))
    return plan


def validated_jpeg(
    payload: bytes,
    content_type: str,
    *,
    front: bool,
) -> tuple[bytes, int, int, str]:
    """Decode one remote image and normalize it to a verified high-quality JPG."""
    if Image is None:
        raise RuntimeError("Pillow is required to validate downloaded artwork")
    if not payload:
        raise RuntimeError("Artwork download was empty")
    if content_type and not (
        content_type.casefold().startswith("image/")
        or content_type.casefold() == "application/octet-stream"
    ):
        raise RuntimeError(
            f"Artwork server returned non-image content type {content_type}"
        )
    try:
        with Image.open(io.BytesIO(payload)) as probe:
            probe.verify()
        with Image.open(io.BytesIO(payload)) as image:
            image.load()
            width, height = int(image.width), int(image.height)
            source_format = str(image.format or "unknown")
            minimum = 300 if front else 200
            if width < minimum or height < minimum:
                raise RuntimeError(
                    f"Artwork is too small ({width}x{height}); "
                    f"minimum is {minimum}x{minimum}"
                )
            if front:
                ratio = width / height
                if not 0.60 <= ratio <= 1.70:
                    raise RuntimeError(
                        f"Front artwork has an implausible aspect ratio "
                        f"({width}x{height})"
                    )
            converted = image.convert("RGB")
            output = io.BytesIO()
            converted.save(
                output,
                format="JPEG",
                quality=95,
                subsampling=0,
                optimize=True,
            )
            return output.getvalue(), width, height, source_format
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError("Downloaded artwork is not a decodable image") from exc


def cover_narration(
    emoji: str,
    text: str,
    *,
    use_color: bool,
    color: tuple[int, int, int] = (120, 200, 235),
    dim: bool = False,
    italic: bool = False,
) -> None:
    """Print cover narration with every message body on the same cell stop."""
    # Most emoji occupy two terminal cells while the music note occupies one.
    # Pad dynamically so every message body starts at the same column.
    emoji_padding = " " * max(1, 3 - visible_cell_width(emoji))
    styled_text = rgb_text(
        text,
        *color,
        use_color,
        dim=dim,
    )
    if italic and use_color:
        styled_text = f"{ANSI['italic']}{styled_text}"
    print(f"            {emoji}{emoji_padding}{styled_text}")


def inline_italic(text: str, use_color: bool) -> str:
    """Italicize one phrase without resetting its surrounding ANSI color."""
    if not use_color:
        return text
    return f"{ANSI['italic']}{text}\033[23m"


def chafa_executable() -> Path | None:
    """Find Chafa, preferring PATH and then the established local install."""
    discovered = shutil.which("chafa")
    candidates = [
        Path(discovered) if discovered else None,
        Path(r"C:\util\Chafa.exe") if os.name == "nt" else None,
    ]
    return next(
        (
            candidate
            for candidate in candidates
            if candidate is not None and candidate.is_file()
        ),
        None,
    )


def openimage_launcher() -> Path | None:
    """Find the canonical openimage.bat launcher."""
    discovered = shutil.which("openimage.bat")
    candidates = [
        Path(discovered) if discovered else None,
        _SCRIPT_DIR / "openimage.bat",
        Path(r"C:\BAT\openimage.bat") if os.name == "nt" else None,
    ]
    return next(
        (
            candidate
            for candidate in candidates
            if candidate is not None and candidate.is_file()
        ),
        None,
    )


def irfanview_executable() -> Path | None:
    """Find IrfanView using PATH, its environment override, or known installs."""
    candidates: list[Path | None] = []
    if IMAGE_VIEWER_EXECUTABLE:
        candidates.append(Path(IMAGE_VIEWER_EXECUTABLE).expanduser())
    configured = os.environ.get("IRFANVIEW", "").strip().strip('"')
    if configured:
        candidates.append(Path(configured))
    for name in ("i_view32.exe", "i_view64.exe", "i_view32", "i_view64"):
        discovered = shutil.which(name)
        if discovered:
            candidates.append(Path(discovered))
    if os.name == "nt":
        candidates.extend(
            (
                Path(
                    r"C:\util2\IrfanViewPortable\App"
                    r"\IrfanView\i_view32.exe"
                ),
                Path(
                    r"C:\util2\IrfanViewPortable\App"
                    r"\IrfanView64\i_view64.exe"
                ),
            )
        )
    return next((path for path in candidates if path and path.is_file()), None)


def launch_default_image_viewer(path: Path) -> Path:
    """Open an image with the operating system's default image association."""
    if os.name == "nt":
        os.startfile(str(path))  # type: ignore[attr-defined]
        return path
    opener = shutil.which("xdg-open") or shutil.which("open")
    if not opener:
        raise RuntimeError("No default image viewer launcher was found")
    subprocess.Popen([opener, str(path)])
    return path


def image_resolution(path: Path) -> str:
    """Return an image's pixel dimensions for preview narration."""
    if Image is None:
        return "unknown resolution"
    try:
        with Image.open(path) as image:
            return f"{int(image.width)}x{int(image.height)}"
    except Exception:
        return "unknown resolution"


def terminal_supports_sixel() -> bool:
    """Honor explicit preview selection or a terminal's Sixel advertisement."""
    preference = os.environ.get(
        "AUDIT_MUSIC_ART_PREVIEW", "auto"
    ).casefold()
    if preference in {"sixel", "sixels"}:
        return True
    if preference in {"ansi", "symbols", "text", "none", "off"}:
        return False
    advertised = " ".join(
        os.environ.get(name, "")
        for name in (
            "TERM",
            "TERM_FEATURES",
            "TERMINAL_FEATURES",
            "DEC_TERMINAL_ID",
        )
    ).casefold()
    return "sixel" in advertised


def windows_visible_console_size() -> os.terminal_size | None:
    """Read the visible Win32 console viewport, never the scrollback buffer."""
    if os.name != "nt":
        return None
    try:
        import ctypes
        import msvcrt

        class Coord(ctypes.Structure):
            _fields_ = (("x", ctypes.c_short), ("y", ctypes.c_short))

        class SmallRect(ctypes.Structure):
            _fields_ = (
                ("left", ctypes.c_short),
                ("top", ctypes.c_short),
                ("right", ctypes.c_short),
                ("bottom", ctypes.c_short),
            )

        class ConsoleScreenBufferInfo(ctypes.Structure):
            _fields_ = (
                ("size", Coord),
                ("cursor_position", Coord),
                ("attributes", ctypes.c_ushort),
                ("window", SmallRect),
                ("maximum_window_size", Coord),
            )

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        get_info = kernel32.GetConsoleScreenBufferInfo
        get_info.argtypes = (
            ctypes.c_void_p,
            ctypes.POINTER(ConsoleScreenBufferInfo),
        )
        get_info.restype = ctypes.c_int
        for stream in (sys.stdout, sys.stderr, sys.stdin):
            try:
                handle = msvcrt.get_osfhandle(stream.fileno())
            except (AttributeError, OSError, ValueError):
                continue
            info = ConsoleScreenBufferInfo()
            if get_info(handle, ctypes.byref(info)):
                columns = int(info.window.right - info.window.left + 1)
                rows = int(info.window.bottom - info.window.top + 1)
                if columns > 0 and rows > 0:
                    return os.terminal_size((columns, rows))
    except Exception:
        return None
    return None


def windows_console_viewport_state() -> ConsoleViewportState | None:
    """Return visible Win32 viewport and cursor position without touching Chafa geometry.

    This is deliberately waveform-specific state.  Artwork/Chafa previews continue
    to use the project's existing ``claire_terminal_geometry`` integration.
    """
    if os.name != "nt":
        return None
    try:
        import ctypes
        import msvcrt

        class Coord(ctypes.Structure):
            _fields_ = (("x", ctypes.c_short), ("y", ctypes.c_short))

        class SmallRect(ctypes.Structure):
            _fields_ = (
                ("left", ctypes.c_short),
                ("top", ctypes.c_short),
                ("right", ctypes.c_short),
                ("bottom", ctypes.c_short),
            )

        class ConsoleScreenBufferInfo(ctypes.Structure):
            _fields_ = (
                ("size", Coord),
                ("cursor_position", Coord),
                ("attributes", ctypes.c_ushort),
                ("window", SmallRect),
                ("maximum_window_size", Coord),
            )

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        get_info = kernel32.GetConsoleScreenBufferInfo
        get_info.argtypes = (
            ctypes.c_void_p,
            ctypes.POINTER(ConsoleScreenBufferInfo),
        )
        get_info.restype = ctypes.c_int
        for stream in (sys.stdout, sys.stderr, sys.stdin):
            try:
                handle = msvcrt.get_osfhandle(stream.fileno())
            except (AttributeError, OSError, ValueError):
                continue
            info = ConsoleScreenBufferInfo()
            if not get_info(handle, ctypes.byref(info)):
                continue
            columns = int(info.window.right - info.window.left + 1)
            rows = int(info.window.bottom - info.window.top + 1)
            if columns <= 0 or rows <= 0:
                continue
            cursor_column = max(0, min(columns - 1, int(info.cursor_position.x - info.window.left)))
            cursor_row = max(0, min(rows - 1, int(info.cursor_position.y - info.window.top)))
            return ConsoleViewportState(
                columns=columns,
                rows=rows,
                cursor_column=cursor_column,
                cursor_row=cursor_row,
                window_top=int(info.window.top),
                window_bottom=int(info.window.bottom),
            )
    except Exception:
        return None
    return None


def windows_console_font_cell_size() -> tuple[int, int] | None:
    """Return the active Win32 console font cell size in physical pixels."""
    if os.name != "nt":
        return None
    try:
        import ctypes
        import msvcrt

        class Coord(ctypes.Structure):
            _fields_ = (("x", ctypes.c_short), ("y", ctypes.c_short))

        class ConsoleFontInfoEx(ctypes.Structure):
            _fields_ = (
                ("cbSize", ctypes.c_ulong),
                ("nFont", ctypes.c_ulong),
                ("dwFontSize", Coord),
                ("FontFamily", ctypes.c_uint),
                ("FontWeight", ctypes.c_uint),
                ("FaceName", ctypes.c_wchar * 32),
            )

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        get_font = kernel32.GetCurrentConsoleFontEx
        get_font.argtypes = (
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.POINTER(ConsoleFontInfoEx),
        )
        get_font.restype = ctypes.c_int
        for stream in (sys.stdout, sys.stderr, sys.stdin):
            try:
                handle = msvcrt.get_osfhandle(stream.fileno())
            except (AttributeError, OSError, ValueError):
                continue
            info = ConsoleFontInfoEx()
            info.cbSize = ctypes.sizeof(ConsoleFontInfoEx)
            if get_font(handle, False, ctypes.byref(info)):
                width = int(info.dwFontSize.x)
                height = int(info.dwFontSize.y)
                if width > 0 and height > 0:
                    return width, height
    except Exception:
        return None
    return None


def windows_console_pixel_scale_factor() -> float:
    """Return Windows display-DPI scaling for terminal pixel geometry.

    GetCurrentConsoleFontEx can report the unscaled logical font cell under
    Windows Terminal/ConPTY. Sixel, however, is painted in display pixels.
    Compensating by the active window/system DPI keeps an 80% waveform near
    80% of the *visible* terminal instead of roughly half that size on a 200%
    display. Non-Windows terminals deliberately stay at 1.0.
    """
    if os.name != "nt":
        return 1.0
    try:
        import ctypes

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        dpi_candidates: list[int] = []
        get_console_window = getattr(kernel32, "GetConsoleWindow", None)
        get_dpi_for_window = getattr(user32, "GetDpiForWindow", None)
        if get_console_window is not None and get_dpi_for_window is not None:
            get_console_window.restype = ctypes.c_void_p
            get_dpi_for_window.argtypes = (ctypes.c_void_p,)
            get_dpi_for_window.restype = ctypes.c_uint
            hwnd = get_console_window()
            if hwnd:
                dpi_candidates.append(int(get_dpi_for_window(hwnd) or 0))
        get_dpi_for_system = getattr(user32, "GetDpiForSystem", None)
        if get_dpi_for_system is not None:
            get_dpi_for_system.restype = ctypes.c_uint
            dpi_candidates.append(int(get_dpi_for_system() or 0))
        # GetConsoleWindow() is only a message-queue pseudo-window under
        # Windows Terminal and can misleadingly report 96 DPI. Prefer the
        # highest sane signal so a 150%/200% desktop is not collapsed to 100%.
        dpi = max((value for value in dpi_candidates if value), default=0)
        if 72 <= dpi <= 768:
            return max(0.75, min(4.0, dpi / 96.0))
    except Exception:
        pass
    return 1.0


def visible_console_size() -> os.terminal_size:
    """Return visible cells while ignoring stale COLUMNS/LINES environment data."""
    windows_size = windows_visible_console_size()
    if windows_size is not None:
        return windows_size
    for stream in (sys.stdout, sys.stderr, sys.stdin):
        try:
            size = os.get_terminal_size(stream.fileno())
        except (AttributeError, OSError, ValueError):
            continue
        if size.columns > 0 and size.lines > 0:
            return size
    return os.terminal_size((100, 35))


ANSI_CONTROL_RE = re.compile(
    r"\x1b(?:\[[0-?]*[ -/]*[@-~]|#[34])"
)


def visible_cell_width(text: str) -> int:
    """Approximate terminal cells after removing this script's ANSI controls."""
    plain = ANSI_CONTROL_RE.sub("", text)
    width = 0
    for character in plain:
        codepoint = ord(character)
        if character in {"\r", "\n"} or unicodedata.combining(character):
            continue
        if 0xFE00 <= codepoint <= 0xFE0F:
            continue
        if character in {"♩", "♪", "♫", "♬"}:
            # Windows Terminal renders these text-style music notes as one
            # cell even though their Unicode block overlaps emoji symbols.
            width += 1
            continue
        if (
            unicodedata.east_asian_width(character) in {"W", "F"}
            or 0x1F000 <= codepoint <= 0x1FAFF
            or 0x2600 <= codepoint <= 0x27BF
        ):
            width += 2
        else:
            width += 1
    return width


def rendered_console_rows(text: str, columns: int | None = None) -> int:
    """Count the terminal rows occupied by one possibly wrapped prompt."""
    width = max(1, int(columns or visible_console_size().columns))
    logical_lines = str(text).split("\n")
    return sum(
        max(1, (visible_cell_width(line) + width - 1) // width)
        for line in logical_lines
    )


def prompt_with_option_legend(
    prompt: str,
    options: str,
    *,
    indent: str = "",
    terminal_columns: int | None = None,
) -> str:
    """Keep a prompt's option explanation intact on an aligned second line.

    The inline form is retained when it fits. Otherwise, the option legend
    starts on the next line beneath the first character after the ``❓ ``
    marker, rather than being split arbitrarily by terminal word wrapping.
    """
    first_line = f"{indent}{prompt}"
    inline = f"{first_line} {options} "
    columns = max(
        1,
        int(terminal_columns or visible_console_size().columns),
    )
    if visible_cell_width(inline) <= columns:
        return inline
    question_text_column = (
        visible_cell_width(indent) + visible_cell_width("❓ ")
    )
    continuation = " " * question_text_column
    return f"{first_line}\n{continuation}{options} "


def waveform_rendering_status(
    filename: str,
    use_color: bool,
    *,
    frame: str = "⏳",
    terminal_columns: int | None = None,
) -> str:
    """Render the one-line animated status shown while a waveform is generated."""
    prefix = f"            {frame} Rendering: "
    columns = max(1, int(terminal_columns or visible_console_size().columns))
    available = max(4, columns - visible_cell_width(prefix))
    shown = middle_ellipsize(str(filename), available)
    return (
        rgb_text(prefix, 190, 185, 150, use_color, dim=True)
        + varied_path(shown, use_color)
    )


def waveform_rendered_status(
    filename: str,
    use_color: bool,
    *,
    terminal_columns: int | None = None,
) -> str:
    """Render the stable replacement for the animated waveform wait line."""
    prefix = "            ✅ Rendered: "
    columns = max(1, int(terminal_columns or visible_console_size().columns))
    available = max(4, columns - visible_cell_width(prefix))
    shown = middle_ellipsize(str(filename), available)
    return (
        rgb_text(prefix, 115, 225, 150, use_color)
        + varied_path(shown, use_color)
    )


def wait_for_waveform_render(
    future: Future,
    filename: str,
    *,
    use_color: bool,
    refresh_seconds: float = 0.32,
    leave_final_status: bool = True,
):
    """Wait for one render future while animating an hourglass in place.

    Waveform review can clear the temporary wait line when the render finishes,
    then print the stable ``Rendered:`` status *inside* its measured review block.
    Other callers retain the historical final-status behavior by default.
    """
    interactive_terminal = bool(
        getattr(sys.stdout, "isatty", lambda: False)()
    )
    frames = ("⏳", "⌛")
    if interactive_terminal and not future.done():
        frame_index = 0
        while not future.done():
            status = waveform_rendering_status(
                filename,
                use_color,
                frame=frames[frame_index % len(frames)],
            )
            print(
                "\r" + status + ANSI["erase_to_eol"],
                end="",
                flush=True,
            )
            frame_index += 1
            time.sleep(max(0.05, float(refresh_seconds)))
        result = future.result()
        if leave_final_status:
            print(
                "\r"
                + waveform_rendered_status(filename, use_color)
                + ANSI["erase_to_eol"]
            )
        else:
            print("\r" + ANSI["erase_line"], end="\r", flush=True)
        return result
    if not future.done() and leave_final_status:
        print(waveform_rendering_status(filename, use_color))
    result = future.result()
    if leave_final_status:
        print(waveform_rendered_status(filename, use_color))
    return result


def erase_wrapped_console_text(text: str) -> None:
    """Erase every terminal row occupied by text whose cursor is at its end."""
    rows = rendered_console_rows(text)
    sequence = f"\r{ANSI['erase_line']}"
    for _ in range(rows - 1):
        sequence += f"\033[1A\r{ANSI['erase_line']}"
    sequence += "\r"
    print(sequence, end="", flush=True)


class ConsolePager:
    """A transparent stdout wrapper that pauses before one viewport scrolls."""

    def __init__(self, stream: Any, key_reader=None) -> None:
        self.stream = stream
        self.key_reader = key_reader or read_single_key
        self.rows_used = 0
        self.line_width = 0
        self.line_rows = 0

    @property
    def encoding(self):
        return getattr(self.stream, "encoding", None)

    def isatty(self) -> bool:
        return bool(getattr(self.stream, "isatty", lambda: False)())

    def fileno(self) -> int:
        return self.stream.fileno()

    def flush(self) -> None:
        self.stream.flush()

    def _capacity(self) -> int:
        return max(1, int(visible_console_size().lines) - 3)

    def _pause(self) -> None:
        prompt = (
            f"{ANSI['bold']}\033[38;2;255;225;80m"
            "── More ── press any key to continue "
            f"{ANSI['reset']}"
        )
        self.stream.write(prompt)
        self.stream.flush()
        key = self.key_reader()
        if key == "\x03":
            self.stream.write(ANSI["reset"])
            self.stream.flush()
            raise KeyboardInterrupt
        self.stream.write(
            f"\r{ANSI['erase_line']}{ANSI['erase_to_eol']}"
        )
        self.stream.flush()
        self.rows_used = 0
        self.line_rows = 0
        self.line_width = 0

    def reset_after_user_pause(self) -> None:
        """Treat another interactive prompt as the page's natural pause."""
        self.rows_used = 0
        self.line_rows = 0
        self.line_width = 0

    def _reserve_rows(self, desired_line_width: int) -> None:
        columns = max(1, int(visible_console_size().columns))
        desired_rows = max(
            1,
            (max(1, desired_line_width) + columns - 1) // columns,
        )
        extra_rows = max(0, desired_rows - self.line_rows)
        if extra_rows and self.rows_used + extra_rows > self._capacity():
            self._pause()
            extra_rows = desired_rows
        self.rows_used += extra_rows
        self.line_rows = desired_rows

    def write(self, text: str) -> int:
        """Write incrementally so multiline strings pause between screenfuls."""
        value = str(text)
        pieces = re.split(r"(\n)", value)
        for piece in pieces:
            if not piece:
                continue
            if piece == "\n":
                if self.line_rows == 0:
                    self._reserve_rows(0)
                self.stream.write(piece)
                self.line_width = 0
                self.line_rows = 0
                continue
            if "\r" in piece:
                after_carriage = piece.rsplit("\r", 1)[-1]
                self.line_width = visible_cell_width(after_carriage)
                self.line_rows = 0
                self._reserve_rows(self.line_width)
            else:
                desired_width = self.line_width + visible_cell_width(piece)
                self._reserve_rows(desired_width)
                self.line_width = desired_width
            self.stream.write(piece)
        return len(value)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.stream, name)


@contextmanager
def paged_console_output(enabled: bool = True):
    """Page real interactive stdout; never page redirected/machine output."""
    original = sys.stdout
    interactive = (
        enabled
        and bool(getattr(original, "isatty", lambda: False)())
        and bool(getattr(sys.stdin, "isatty", lambda: False)())
    )
    if not interactive:
        yield None
        return
    pager = ConsolePager(original)
    sys.stdout = pager
    try:
        yield pager
    finally:
        sys.stdout = original


def reset_console_pager_after_user_input() -> None:
    """Reset page accounting when another prompt already paused the user."""
    reset = getattr(sys.stdout, "reset_after_user_pause", None)
    if callable(reset):
        reset()


def artwork_preview_geometry(
    terminal_size: os.terminal_size | None = None,
    *,
    indent_columns: int = ART_PREVIEW_INDENT_COLUMNS,
    right_margin_columns: int = ART_PREVIEW_RIGHT_MARGIN_COLUMNS,
    reserved_text_rows: int = ART_PREVIEW_RESERVED_TEXT_ROWS,
    cell_pixel_size: tuple[int, int] | None = None,
) -> ArtworkPreviewGeometry:
    """Use the full live console minus indent, margin, and prompt/status rows."""
    live_console = terminal_size is None
    terminal = terminal_size or visible_console_size()
    terminal_columns = max(1, int(terminal.columns))
    terminal_rows = max(1, int(terminal.lines))
    actual_indent_columns = min(
        max(0, int(indent_columns)),
        max(0, terminal_columns - 10),
    )
    columns = max(
        4,
        terminal_columns
        - actual_indent_columns
        - max(0, int(right_margin_columns)),
    )
    reserved_rows = min(
        max(0, int(reserved_text_rows)),
        max(0, terminal_rows - 4),
    )
    rows = max(2, terminal_rows - reserved_rows)
    cell_width, cell_height = (
        cell_pixel_size
        or (windows_console_font_cell_size() if live_console else None)
        or (7, 14)
    )
    return ArtworkPreviewGeometry(
        terminal_columns=terminal_columns,
        terminal_rows=terminal_rows,
        indent_columns=actual_indent_columns,
        columns=columns,
        rows=rows,
        pixel_width=max(1, columns * cell_width),
        pixel_height=max(1, rows * cell_height),
    )


def waveform_review_prompt_text(
    audio_name: str,
    *,
    terminal_columns: int,
    excessive_silence: bool,
    allow_bake_gain: bool,
) -> str:
    """Build the plain review prompt exactly as it will wrap on screen."""
    question = urgent_prompt_text(
        f"Does this waveform show a problem in {audio_name}?",
        False,
        faint_italic_spans=(audio_name,),
    )
    return prompt_with_option_legend(
        question,
        waveform_review_choices(
            False,
            default_edit=excessive_silence,
            allow_bake_gain=allow_bake_gain,
        ),
        indent="            ",
        terminal_columns=terminal_columns,
    )


def waveform_review_fixed_text_rows(
    audio_name: str,
    *,
    index: int,
    total: int,
    comparison_active: bool,
    terminal_columns: int,
    excessive_silence: bool = False,
    allow_bake_gain: bool = False,
) -> int:
    """Count every non-Sixel row belonging to the current review block."""
    columns = max(1, int(terminal_columns))
    rows = 1  # leading blank line separating this review from prior output
    rows += rendered_console_rows(
        waveform_review_header(
            index, total, comparison_active=comparison_active, use_color=False
        ),
        columns,
    )
    rows += rendered_console_rows(
        waveform_rendered_status(
            audio_name, False, terminal_columns=columns
        ),
        columns,
    )
    if excessive_silence:
        # Use the longest normal narration shape.  Exact seconds do not change
        # wrapping materially, but keeping this row in the budget prevents the
        # warning from pushing the prompt offscreen.
        silence_text = (
            "            🔴 Longest silence exceeds the configured limit; "
            "ENTER defaults to opening this file in the audio editor."
        )
        rows += rendered_console_rows(silence_text, columns)
    rows += rendered_console_rows(
        waveform_review_prompt_text(
            audio_name,
            terminal_columns=columns,
            excessive_silence=excessive_silence,
            allow_bake_gain=allow_bake_gain,
        ),
        columns,
    )
    return rows


def waveform_review_graph_rows(
    comparison_active: bool,
    terminal_size: os.terminal_size | None = None,
    *,
    rows_available_from_cursor: int | None = None,
    fixed_text_rows: int | None = None,
) -> int:
    """Choose equal graph heights using the live rows below the cursor.

    Prefer shrinking the graphs over scrolling prior audit output.  Only when
    even the configured minimum graph height cannot fit do we later scroll the
    viewport by the exact number of rows required.
    """
    terminal = terminal_size or visible_console_size()
    lines = max(1, int(terminal.lines))
    graph_count = 2 if comparison_active else 1
    fixed = max(0, int(fixed_text_rows if fixed_text_rows is not None else (5 if comparison_active else 4)))
    available = max(1, int(rows_available_from_cursor if rows_available_from_cursor is not None else lines))
    usable = available - fixed - graph_count * WAVEFORM_SIXEL_SAFETY_ROWS
    no_scroll_rows = usable // graph_count
    if no_scroll_rows >= WAVEFORM_REVIEW_MIN_GRAPH_ROWS:
        return min(int(WAVEFORM_PREVIEW_HEIGHT_ROWS), int(no_scroll_rows))

    full_usable = lines - fixed - graph_count * WAVEFORM_SIXEL_SAFETY_ROWS
    full_rows = full_usable // graph_count
    if full_rows >= WAVEFORM_REVIEW_MIN_GRAPH_ROWS:
        # The cursor is already too low for even the minimum graph height.
        # Use the minimum useful height and scroll only the exact remaining
        # deficit; do not scroll old audit output merely to preserve 6-row art.
        return int(WAVEFORM_REVIEW_MIN_GRAPH_ROWS)
    return max(1, min(int(WAVEFORM_PREVIEW_HEIGHT_ROWS), int(full_rows)))


def waveform_review_layout_plan(
    audio_name: str,
    *,
    index: int,
    total: int,
    comparison_active: bool,
    excessive_silence: bool,
    allow_bake_gain: bool,
    viewport_state: ConsoleViewportState | None = None,
    terminal_size: os.terminal_size | None = None,
) -> WaveformReviewLayout:
    """Plan one inline review using uniform classic waveform geometry.

    The waveform starts from the original pre-experiment preview (nearly the
    full live terminal), then scales uniformly to 75% for a single graph or
    50% for each before/after graph.  A comparison therefore occupies roughly
    one screen in total instead of one screen per graph.

    If the complete current review block cannot physically fit in the visible
    viewport, clamp only the vertical dimension as a last-resort safety measure;
    horizontal width remains at the configured scale so the metric gutter stays
    on-screen.
    """
    terminal = terminal_size or visible_console_size()
    state = viewport_state
    columns = int(state.columns if state is not None else terminal.columns)
    rows = int(state.rows if state is not None else terminal.lines)
    rows_available = state.rows_available_from_cursor if state is not None else rows
    fixed = waveform_review_fixed_text_rows(
        audio_name,
        index=index,
        total=total,
        comparison_active=comparison_active,
        terminal_columns=columns,
        excessive_silence=excessive_silence,
        allow_bake_gain=allow_bake_gain,
    )
    graph_count = 2 if comparison_active else 1
    width_scale = (
        WAVEFORM_COMPARISON_WIDTH_SCALE
        if comparison_active
        else WAVEFORM_REVIEW_WIDTH_SCALE
    )
    height_scale = (
        WAVEFORM_COMPARISON_HEIGHT_SCALE
        if comparison_active
        else WAVEFORM_REVIEW_HEIGHT_SCALE
    )
    desired = waveform_preview_geometry(
        width_scale,
        height_scale=height_scale,
    )
    graph_rows = max(1, int(desired.rows))

    # Exact scaled classic geometry should normally fit.  Only clamp if the
    # complete current review block is literally taller than the whole visible
    # viewport; this prevents impossible cursor math on very small terminals.
    max_graph_rows = max(
        1,
        (rows - fixed - graph_count * WAVEFORM_SIXEL_SAFETY_ROWS) // graph_count,
    )
    graph_rows = min(graph_rows, max_graph_rows)
    required = fixed + graph_count * (graph_rows + WAVEFORM_SIXEL_SAFETY_ROWS)
    scroll_rows = max(0, required - rows_available)
    return WaveformReviewLayout(
        graph_rows=graph_rows,
        graph_count=graph_count,
        fixed_text_rows=fixed,
        required_rows=required,
        rows_available_from_cursor=rows_available,
        scroll_rows=scroll_rows,
        terminal_columns=columns,
        terminal_rows=rows,
    )


def waveform_preview_height_scale(width_fraction: float) -> float:
    """Return the configured vertical stretch for a known waveform width."""
    width = float(width_fraction)
    if math.isclose(
        width, WAVEFORM_COMPARISON_WIDTH_FRACTION, rel_tol=0.0, abs_tol=1e-9
    ):
        return float(WAVEFORM_COMPARISON_HEIGHT_SCALE)
    if math.isclose(
        width, WAVEFORM_REVIEW_WIDTH_FRACTION, rel_tol=0.0, abs_tol=1e-9
    ):
        return float(WAVEFORM_REVIEW_HEIGHT_SCALE)
    # Unknown/custom callers retain the historical uniform scaling behavior.
    return max(0.10, float(width_fraction))


def capture_waveform_sixel_cursor_cell_height() -> int | None:
    """Capture only VT's real cell height for post-Sixel cursor advancement.

    Raster sizing intentionally remains on v131's known-good path. The probe
    established that CSI 16 t reports the real 20-pixel terminal row while the
    Win32/ConPTY font API can report 40. Mixing the shared helper into raster
    geometry caused v132's wide, shallow regression; this value is therefore
    used solely by ``sixel_display_rows``.
    """
    global _WAVEFORM_SIXEL_CURSOR_CELL_HEIGHT_PIXELS
    captured = None
    if callable(query_terminal_geometry):
        try:
            terminal_geometry = query_terminal_geometry()
            viewport_height = int(
                getattr(terminal_geometry, "viewport_height", 0)
            )
            text_rows = int(getattr(terminal_geometry, "rows", 0))
            # The viewport/text-grid ratio is the measurement that matters for
            # cursor advancement.  CSI 6t's standalone cell response has proved
            # vulnerable to unrelated terminal input being parsed as its height.
            height = (
                round(viewport_height / text_rows)
                if viewport_height > 0 and text_rows > 0
                else int(getattr(terminal_geometry, "cell_height", 0))
            )
            if height > 0:
                captured = height
        except Exception:
            captured = None
    _WAVEFORM_SIXEL_CURSOR_CELL_HEIGHT_PIXELS = captured
    return captured


def waveform_preview_geometry(
    width_fraction: float = WAVEFORM_REVIEW_WIDTH_FRACTION,
    *,
    height_rows: int | None = None,
    height_scale: float | None = None,
) -> ArtworkPreviewGeometry:
    """Return the exact terminal viewport offered to direct waveform Chafa."""
    base = artwork_preview_geometry(
        indent_columns=12,
        right_margin_columns=1,
        reserved_text_rows=9,
    )
    fraction = max(0.10, min(1.0, float(width_fraction)))
    requested_columns = max(8, round(base.terminal_columns * fraction))
    columns = min(base.columns, requested_columns)
    cell_width = base.pixel_width / max(1, base.columns)
    cell_height = base.pixel_height / max(1, base.rows)
    if height_rows is not None:
        requested_rows = max(2, int(height_rows))
    else:
        vertical_fraction = max(
            0.10,
            min(
                1.0,
                float(
                    WAVEFORM_REVIEW_HEIGHT_SCALE
                    if height_scale is None
                    else height_scale
                ),
            ),
        )
        requested_rows = max(2, round(base.terminal_rows * vertical_fraction))
    rows = min(base.terminal_rows, requested_rows)
    return replace(
        base,
        columns=columns,
        rows=rows,
        pixel_width=max(1, round(columns * cell_width)),
        pixel_height=max(1, round(rows * cell_height)),
    )


def chafa_sixel_geometry_options(geometry: ArtworkPreviewGeometry) -> list[str]:
    """Return the exact shared-library Chafa options used by echo-image.bat."""
    if callable(query_terminal_geometry):
        try:
            live = query_terminal_geometry()
            # This is intentionally the same public API echo-image.bat calls:
            # ``python -m clairecjs_utils.claire_terminal_geometry --format
            # chafa --reserve-rows N``.  Do not duplicate its pixel math here.
            options = [
                *live.chafa_options_for(
                    reserved_rows=ART_PREVIEW_RESERVED_TEXT_ROWS
                ).split(),
                "--scale=max",
            ]
            return scale_chafa_view_size(options, ART_PREVIEW_SCALE)
        except Exception:
            pass
    return scale_chafa_view_size([
        "--view-size="
        # This is the deliberately *smaller* no-helper fallback.  It is only
        # used by copied installations that genuinely lack the shared helper.
        f"{geometry.columns:.1f}x"
        f"{geometry.rows:.1f}",
        "--scale=max",
    ], ART_PREVIEW_SCALE)


def scale_chafa_view_size(
    options: list[str],
    scale: float,
    *,
    width_multiplier: float = ART_PREVIEW_WIDTH_MULTIPLIER,
    max_width_to_height: float = ART_PREVIEW_MAX_WIDTH_TO_HEIGHT,
) -> list[str]:
    """Scale Chafa's viewport, then widen it with a physical 3:1 aspect cap."""
    factor = max(0.10, float(scale))
    width_factor = max(0.10, float(width_multiplier))
    aspect_cap = max(1.0, float(max_width_to_height))

    # Chafa view-size is measured in terminal cells, not square pixels. A
    # 10x20 font means two columns occupy the same physical width as one row
    # occupies height. Use the advertised ratio when present; otherwise the
    # project's established 7x14 fallback is the same 0.5 ratio.
    cell_width_to_height = 0.5
    for option in options:
        ratio = re.fullmatch(r"--font-ratio=([0-9.]+)/([0-9.]+)", option)
        if ratio and float(ratio.group(2)) > 0:
            cell_width_to_height = (
                float(ratio.group(1)) / float(ratio.group(2))
            )
            break

    scaled: list[str] = []
    for option in options:
        match = re.fullmatch(r"--view-size=([0-9.]+)x([0-9.]+)", option)
        if match:
            height = max(1.0, float(match.group(2)) * factor)
            ordinary_width = max(1.0, float(match.group(1)) * factor)
            max_width_cells = (
                height * aspect_cap / max(0.05, cell_width_to_height)
            )
            width = min(ordinary_width * width_factor, max_width_cells)
            scaled.append(f"--view-size={width:.1f}x{height:.1f}")
        else:
            scaled.append(option)
    return scaled


def scaled_artwork_geometry(
    geometry: ArtworkPreviewGeometry,
    scale: float = ART_PREVIEW_SCALE,
    *,
    width_multiplier: float = ART_PREVIEW_WIDTH_MULTIPLIER,
    max_width_to_height: float = ART_PREVIEW_MAX_WIDTH_TO_HEIGHT,
) -> ArtworkPreviewGeometry:
    """Keep the current preview height, double width, cap physical width at 3x height."""
    factor = max(0.10, float(scale))
    rows = max(2, round(geometry.rows * factor))
    ordinary_columns = max(4, round(geometry.columns * factor))
    cell_width = geometry.pixel_width / max(1, geometry.columns)
    cell_height = geometry.pixel_height / max(1, geometry.rows)
    max_columns_by_physical_aspect = round(
        rows
        * cell_height
        * max(1.0, float(max_width_to_height))
        / max(0.1, cell_width)
    )
    columns = max(4, min(
        round(ordinary_columns * max(0.10, float(width_multiplier))),
        max_columns_by_physical_aspect,
    ))
    return ArtworkPreviewGeometry(
        terminal_columns=geometry.terminal_columns,
        terminal_rows=geometry.terminal_rows,
        indent_columns=geometry.indent_columns,
        columns=columns,
        rows=rows,
        pixel_width=max(1, round(columns * cell_width)),
        pixel_height=max(1, round(rows * cell_height)),
    )


def fitted_preview_image(
    image,
    width: int,
    height: int,
):
    """Resize up or down to the largest undistorted image inside the box."""
    source_width, source_height = image.size
    if source_width < 1 or source_height < 1:
        raise RuntimeError("Artwork preview source has invalid dimensions")
    scale = min(width / source_width, height / source_height)
    target = (
        max(1, round(source_width * scale)),
        max(1, round(source_height * scale)),
    )
    if target == image.size:
        return image
    return image.resize(target, Image.Resampling.LANCZOS)


def width_filling_preview_image(
    image,
    width: int,
    height: int,
):
    """Fill the requested width while preserving the source aspect ratio.

    ``height`` is intentionally *not* a hard cap.  Pixel-graphics protocols
    such as Sixel paint in pixels, and Windows Terminal/ConPTY can report a
    wildly incorrect font-cell height.  Capping to that value used to squash a
    2000x700 waveform into a very wide, ~one-text-row strip.  Width is the
    reviewer's requested constraint; the terminal can scroll vertically.
    """
    source_width, source_height = image.size
    if source_width < 1 or source_height < 1:
        raise RuntimeError("Preview source has invalid dimensions")
    target_width = max(1, int(width))
    target_height = max(1, round(source_height * target_width / source_width))
    target = (target_width, target_height)
    if target == image.size:
        return image
    return image.resize(target, Image.Resampling.LANCZOS)


def exact_preview_image(image, width: int, height: int):
    """Resize to an exact diagnostic viewport, intentionally allowing stretch."""
    target = (max(1, int(width)), max(1, int(height)))
    if image.size == target:
        return image
    return image.resize(target, Image.Resampling.BOX)


def ansi_half_block_preview(
    path: Path,
    *,
    use_color: bool,
    geometry: ArtworkPreviewGeometry | None = None,
    stretch_to_width: bool = False,
    height_multiplier: float = 1.0,
) -> str:
    """Fill the available console area with a portable half-block preview."""
    if Image is None:
        raise RuntimeError("Pillow is unavailable for the ANSI artwork preview")
    geometry = geometry or artwork_preview_geometry()
    with Image.open(path) as source:
        image = (
            width_filling_preview_image(
                source.convert("RGB"),
                geometry.columns,
                geometry.rows * 2,
            )
            if stretch_to_width
            else fitted_preview_image(
                source.convert("RGB"),
                geometry.columns,
                geometry.rows * 2,
            )
        )
        height_factor = max(0.10, float(height_multiplier))
        if not math.isclose(height_factor, 1.0):
            image = image.resize(
                (image.width, max(1, round(image.height * height_factor))),
                Image.Resampling.LANCZOS,
            )
        canvas_height = image.height + (image.height % 2)
        canvas = Image.new("RGB", (image.width, canvas_height), (0, 0, 0))
        canvas.paste(image, (0, 0))
        pixels = canvas.load()
        lines: list[str] = []
        grayscale = " .:-=+*#%@"
        for y in range(0, canvas.height, 2):
            pieces = [" " * geometry.indent_columns]
            for x in range(canvas.width):
                upper = pixels[x, y]
                lower = pixels[x, y + 1]
                if use_color:
                    pieces.append(
                        f"\033[38;2;{upper[0]};{upper[1]};{upper[2]}m"
                        f"\033[48;2;{lower[0]};{lower[1]};{lower[2]}m▀"
                    )
                else:
                    luminance = sum(upper) / 3
                    pieces.append(
                        grayscale[
                            min(
                                len(grayscale) - 1,
                                round(
                                    luminance
                                    * (len(grayscale) - 1)
                                    / 255
                                ),
                            )
                        ]
                    )
            if use_color:
                pieces.append(ANSI["reset"])
            lines.append("".join(pieces))
        return "\n".join(lines)


def _sixel_run(character: str, count: int) -> str:
    """Compress one repeated Sixel character when doing so is worthwhile."""
    if count >= 4:
        return f"!{count}{character}"
    return character * count


def sixel_preview_bytes(
    path: Path,
    *,
    geometry: ArtworkPreviewGeometry | None = None,
    stretch_to_width: bool = False,
    exact_size: bool = False,
    colors: int = 64,
    dither: bool = True,
    transparent_black: bool = False,
    pixel_aspect_selector: int = 0,
    height_multiplier: float = 1.0,
) -> bytes:
    """Encode a compact indexed-color Sixel using Pillow and stdlib.

    Waveform previews use ``exact_size`` plus a 32-color/no-dither palette.
    Their background is intentionally transparent after the reserved terminal
    area has been cleared, which avoids spending most of the payload encoding
    black pixels. Artwork retains the older, higher-quality defaults.
    """
    if Image is None:
        raise RuntimeError("Pillow is unavailable for the Sixel preview")
    geometry = geometry or artwork_preview_geometry()
    with Image.open(path) as source:
        rgb = source.convert("RGB")
        if exact_size:
            image = exact_preview_image(
                rgb,
                geometry.pixel_width,
                geometry.pixel_height,
            )
        elif stretch_to_width:
            image = width_filling_preview_image(
                rgb,
                geometry.pixel_width,
                geometry.pixel_height,
            )
        else:
            image = fitted_preview_image(
                rgb,
                geometry.pixel_width,
                geometry.pixel_height,
            )
        height_factor = max(0.10, float(height_multiplier))
        if not math.isclose(height_factor, 1.0):
            image = image.resize(
                (image.width, max(1, round(image.height * height_factor))),
                Image.Resampling.LANCZOS,
            )

        palette_size = max(2, min(256, int(colors)))
        quantized = image.quantize(
            colors=palette_size,
            method=Image.Quantize.MEDIANCUT,
            dither=(Image.Dither.FLOYDSTEINBERG if dither else Image.Dither.NONE),
        )
        width, height = quantized.size
        palette = quantized.getpalette() or []
        pixel_data = quantized.load()
        used_colors = sorted(set(quantized.getdata()))

        transparent_color: int | None = None
        if transparent_black and used_colors:
            # JPEG backgrounds are not always mathematically #000000. Select
            # the darkest palette entry as transparent only when it is safely
            # near black; the reserved screen area is cleared before drawing.
            darkest = min(
                used_colors,
                key=lambda c: sum(palette[c * 3 : c * 3 + 3]),
            )
            dark_rgb = palette[darkest * 3 : darkest * 3 + 3]
            if dark_rgb and max(dark_rgb) <= 28:
                transparent_color = darkest

        visible_colors = [
            color for color in used_colors if color != transparent_color
        ]
        p1 = max(0, min(9, int(pixel_aspect_selector)))
        pieces = [f"\033P{p1};1;0q", f'"1;1;{width};{height}']
        for color in visible_colors:
            red = round((palette[color * 3] / 255) * 100)
            green = round((palette[color * 3 + 1] / 255) * 100)
            blue = round((palette[color * 3 + 2] / 255) * 100)
            pieces.append(f"#{color};2;{red};{green};{blue}")

        for band_y in range(0, height, 6):
            masks: dict[int, bytearray] = {}
            for offset, y in enumerate(range(band_y, min(band_y + 6, height))):
                bit = 1 << offset
                for x in range(width):
                    color = pixel_data[x, y]
                    if color == transparent_color:
                        continue
                    mask = masks.get(color)
                    if mask is None:
                        mask = bytearray(width)
                        masks[color] = mask
                    mask[x] |= bit
            band_colors = sorted(masks)
            for color_index, color in enumerate(band_colors):
                pieces.append(f"#{color}")
                previous: str | None = None
                run_count = 0
                for bits in masks[color]:
                    character = chr(63 + bits)
                    if character == previous:
                        run_count += 1
                    else:
                        if previous is not None:
                            pieces.append(_sixel_run(previous, run_count))
                        previous = character
                        run_count = 1
                if previous is not None:
                    pieces.append(_sixel_run(previous, run_count))
                if color_index != len(band_colors) - 1:
                    pieces.append("$")
            if band_y + 6 < height:
                pieces.append("-")
        pieces.append("\033\\")
        return "".join(pieces).encode("ascii")


def sixel_payload_pixel_size(payload: bytes) -> tuple[int, int] | None:
    """Return the declared Sixel raster width/height when the payload has it."""
    match = re.search(br'"1;1;(\d+);(\d+)', payload)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def sixel_display_rows(
    payload: bytes,
    geometry: ArtworkPreviewGeometry,
) -> int:
    """Translate the actual rendered Sixel height into terminal rows (v113)."""
    declared = sixel_payload_pixel_size(payload)
    if declared is None:
        return max(1, geometry.rows)
    _pixel_width, pixel_height = declared
    if pixel_height <= 0:
        return max(1, geometry.rows)
    geometry_cell_height = geometry.pixel_height / max(1, geometry.rows)
    # The earlier placement probe measured this terminal at 20 physical pixels
    # per text row. Never use a larger divisor for cursor reservation: doing so
    # under-reserves rows and lets the prompt overwrite the lower Sixel bands.
    # A smaller measured value remains valid and simply reserves more room.
    cell_height = min(
        20.0,
        geometry_cell_height,
        float(_WAVEFORM_SIXEL_CURSOR_CELL_HEIGHT_PIXELS or 20),
    )
    return max(1, math.ceil(pixel_height / max(1.0, cell_height)))


def sixel_terminal_frame(
    payload: bytes,
    *,
    geometry: ArtworkPreviewGeometry,
    cursor_row: int | None = None,
) -> tuple[bytes, int]:
    """Reserve real rows first, paint in them, then return below the raster.

    Windows Terminal can leave Sixel pixels fixed to the viewport while later
    text scrolling occurs.  Advancing rows after painting therefore leaves a
    tall raster clipped to its first visible band.  Materialize the rows before
    the DCS, move back into that block with relative cursor motion (which TCC
    passes through reliably), paint, and finally move below the whole block.
    """
    image_rows = sixel_display_rows(payload, geometry)
    terminal_rows = max(2, int(geometry.terminal_rows))
    reserved_rows = min(
        terminal_rows - 1,
        max(2, image_rows + WAVEFORM_SIXEL_SAFETY_ROWS),
    )
    cursor_up = f"\x1b[{reserved_rows}A".encode("ascii")
    cursor_down = f"\x1b[{reserved_rows}B".encode("ascii")
    frame = (
        (b"\r\n" * reserved_rows)
        + cursor_up
        + b"\x1b7\r"
        + (" " * geometry.indent_columns).encode("ascii")
        + payload
        + b"\x1b8"
        + cursor_down
        + b"\r"
    )
    return frame, reserved_rows


def emit_sixel_preview(
    payload: bytes,
    *,
    geometry: ArtworkPreviewGeometry | None = None,
) -> None:
    """Emit one pre-reserved Sixel frame without post-image scrolling."""
    geometry = geometry or artwork_preview_geometry()
    try:
        sys.stdout.flush()
    except Exception:
        pass
    try:
        sys.stderr.flush()
    except Exception:
        pass
    viewport = windows_console_viewport_state()
    frame, _reserved_rows = sixel_terminal_frame(
        payload,
        geometry=geometry,
        cursor_row=(viewport.cursor_row if viewport is not None else None),
    )
    try:
        descriptor = sys.stdout.fileno()
    except (AttributeError, OSError, io.UnsupportedOperation):
        descriptor = None
    if descriptor is not None:
        try:
            os.write(descriptor, frame)
            return
        except OSError:
            pass
    stream = getattr(sys.stdout, "buffer", None)
    if stream is not None:
        stream.write(frame)
        stream.flush()
    else:
        sys.stdout.write(frame.decode("ascii", errors="replace"))
        sys.stdout.flush()


def prepare_artwork_preview(
    path: Path,
    *,
    use_color: bool,
    prefer_sixel: bool = False,
    geometry: ArtworkPreviewGeometry | None = None,
    stretch_to_width: bool = False,
) -> PreparedArtworkPreview:
    """Prepare Chafa, Sixel, or ANSI output without touching the terminal."""
    geometry = geometry or artwork_preview_geometry()
    chafa = chafa_executable()
    sixel = use_color and (
        prefer_sixel or terminal_supports_sixel()
    )
    if sixel and not stretch_to_width:
        # echo-image starts its sixel image at the left edge and lets the
        # shared geometry helper own the complete viewport calculation.  The
        # former indentation was an extra, incompatible width constraint.
        geometry = artwork_preview_geometry(
            indent_columns=0,
            right_margin_columns=0,
            reserved_text_rows=ART_PREVIEW_RESERVED_TEXT_ROWS,
        )
    if chafa is None and sixel:
        geometry = scaled_artwork_geometry(geometry)
        return PreparedArtworkPreview(
            mode="built-in Sixel",
            geometry=geometry,
            sixel_payload=sixel_preview_bytes(
                path,
                geometry=geometry,
                stretch_to_width=stretch_to_width,
            ),
        )
    if chafa is None:
        if not stretch_to_width:
            geometry = scaled_artwork_geometry(geometry)
        return PreparedArtworkPreview(
            mode="built-in ANSI half-blocks",
            geometry=geometry,
            text_payload=ansi_half_block_preview(
                path,
                use_color=use_color,
                geometry=geometry,
                stretch_to_width=stretch_to_width,
            ),
        )
    output_format = "sixels" if sixel else "symbols"
    if sixel and not stretch_to_width:
        # Keep this in lockstep with echo-image.bat: its geometry helper uses
        # live cell pixels plus --font-ratio, rather than guessing from cells.
        scaled_geometry = scaled_artwork_geometry(geometry)
        command = [
            str(chafa),
            "--format=sixels",
            "--fit-width",
            "--colors=full",
            f"--size={scaled_geometry.columns}x{scaled_geometry.rows}",
            *chafa_sixel_geometry_options(geometry),
            "--optimize=9",
            "--work=9",
            "--color-space=din99d",
        ]
    else:
        command = [
            str(chafa),
            f"--format={output_format}",
            f"--size={geometry.columns}x{geometry.rows}",
            f"--view-size={geometry.columns}x{geometry.rows}",
            "--scale=max",
            "--animate=off",
            "--relative=off",
            "--margin-right=0",
            "--work=9",
        ]
    if stretch_to_width:
        # Waveforms are diagnostic plots, so consuming the exact requested
        # viewport is more useful than preserving their JPEG aspect ratio.
        # Chafa's --stretch is the documented exact-dimensions mode.
        command.append("--stretch")
    if not sixel:
        command.extend(
            (
                f"--colors={'full' if use_color else 'none'}",
                "--dither=ordered",
            )
        )
    command.append(str(path))
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0 or not result.stdout:
        if sixel:
            return PreparedArtworkPreview(
                mode="built-in Sixel",
                geometry=geometry,
                sixel_payload=sixel_preview_bytes(
                    path,
                    geometry=geometry,
                    stretch_to_width=stretch_to_width,
                ),
            )
        return PreparedArtworkPreview(
            mode="built-in ANSI half-blocks",
            geometry=geometry,
            text_payload=ansi_half_block_preview(
                path,
                use_color=use_color,
                geometry=geometry,
                stretch_to_width=stretch_to_width,
            ),
        )
    if sixel:
        return PreparedArtworkPreview(
            mode="Chafa Sixel",
            geometry=geometry,
            sixel_payload=result.stdout,
            renderer_options=tuple(command[1:-1]),
        )
    rendered = result.stdout.decode(
        sys.stdout.encoding or "utf-8",
        errors="replace",
    )
    return PreparedArtworkPreview(
        mode="Chafa ANSI symbols",
        geometry=geometry,
        text_payload="\n".join(
            f"{' ' * geometry.indent_columns}{line}" if line else ""
            for line in rendered.rstrip().splitlines()
        ),
    )


def emit_prepared_artwork_preview(
    prepared: PreparedArtworkPreview,
) -> str:
    """Write a previously prepared preview and return its renderer label."""
    if prepared.direct_command:
        try:
            sys.stdout.flush()
        except Exception:
            pass
        try:
            sys.stderr.flush()
        except Exception:
            pass
        result = subprocess.run(
            list(prepared.direct_command),
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Direct Chafa waveform renderer exited with "
                f"status {result.returncode}"
            )
    elif prepared.sixel_payload is not None:
        if prepared.mode == "Chafa Sixel" and prepared.renderer_options:
            compact_options = " ".join(
                option.replace("--format=sixels", "fmt=sixels")
                .replace("--fit-width", "fit-width")
                .replace("--colors=full", "colors=full")
                .replace("--view-size=", "view=")
                .replace("--font-ratio=", "ratio=")
                .replace("--scale=max", "scale=max")
                .replace("--optimize=", "opt=")
                .replace("--work=", "work=")
                .replace("--color-space=", "space=")
                for option in prepared.renderer_options
            )
            print(
                rgb_text(
                    "            Chafa opts: " + compact_options,
                    135, 135, 150, True, dim=True,
                )
            )
        emit_sixel_preview(
            prepared.sixel_payload,
            geometry=prepared.geometry,
        )
    else:
        print(prepared.text_payload or "")
    return prepared.mode


def render_artwork_preview(
    path: Path,
    *,
    use_color: bool,
    prefer_sixel: bool = True,
    geometry: ArtworkPreviewGeometry | None = None,
    stretch_to_width: bool = False,
) -> str:
    """Fit artwork to the live console through Chafa or built-in renderers."""
    prepared = prepare_artwork_preview(
        path,
        use_color=use_color,
        prefer_sixel=prefer_sixel,
        geometry=geometry,
        stretch_to_width=stretch_to_width,
    )
    return emit_prepared_artwork_preview(prepared)


def _raw_console_stream(stream=None):
    """Return the underlying terminal stream when stdout is wrapped by the pager."""
    candidate = stream or sys.stdout
    return getattr(candidate, "stream", candidate)


def _write_terminal_control(sequence: str, stream=None) -> None:
    target = _raw_console_stream(stream)
    try:
        target.write(sequence)
        target.flush()
    except Exception:
        pass


def ensure_waveform_review_vertical_room(
    layout: WaveformReviewLayout,
    *,
    stream=None,
) -> int:
    """Leave viewport movement to normal output so scrollback is preserved.

    The Sixel frame advances by ordinary CRLFs after painting. An explicit
    ``CSI S`` scroll made the review look like it cleared the screen and could
    detach the cursor from the logical end of output.
    """
    del layout, stream
    return 0


def create_waveform_comparison_contact_sheet(
    before_path: Path,
    after_path: Path,
    destination: Path,
) -> Path:
    """Build one side-by-side before/after raster for native Sixel display."""
    if Image is None:
        raise RuntimeError("Pillow is required for waveform comparisons")
    ensure_waveform_jpeg_ready(before_path)
    ensure_waveform_jpeg_ready(after_path)
    with Image.open(before_path) as before_source, Image.open(after_path) as after_source:
        before = before_source.convert("RGB")
        after = after_source.convert("RGB")
        height = max(before.height, after.height)

        def normalize_height(image):
            if image.height == height:
                return image
            width = max(1, round(image.width * height / image.height))
            return image.resize((width, height), Image.Resampling.LANCZOS)

        before = normalize_height(before)
        after = normalize_height(after)
        panel_scale = max(0.1, float(WAVEFORM_COMPARISON_PANEL_HEIGHT_SCALE))

        def compact_panel(image):
            return image.resize(
                (image.width, max(1, round(image.height * panel_scale))),
                Image.Resampling.LANCZOS,
            )

        before = compact_panel(before)
        after = compact_panel(after)
        gap = max(1, round(WAVEFORM_COMPARISON_GAP_SOURCE_PIXELS * panel_scale))
        canvas = Image.new(
            "RGB",
            (before.width + gap + after.width, max(before.height, after.height)),
            "black",
        )
        canvas.paste(before, (0, 0))
        canvas.paste(after, (before.width + gap, 0))
        destination.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(
            destination,
            format="JPEG",
            quality=100,
            subsampling=0,
            optimize=True,
        )
    ensure_waveform_jpeg_ready(destination)
    return destination



def prepare_waveform_preview(
    path: Path,
    *,
    use_color: bool,
    width_fraction: float = WAVEFORM_REVIEW_WIDTH_FRACTION,
    height_rows: int | None = None,
    height_scale: float | None = None,
    prefer_direct_chafa: bool = True,
) -> PreparedArtworkPreview:
    """Prepare a waveform using echo-image's proven direct Chafa contract."""
    ensure_waveform_jpeg_ready(path)
    geometry = waveform_preview_geometry(
        width_fraction,
        height_rows=height_rows,
        height_scale=height_scale,
    )
    if use_color and prefer_direct_chafa:
        exact_chafa = (
            shutil.which("chafa-1.18.2.exe")
            or shutil.which("chafa-1.18.2")
            or (
                r"C:\util\chafa-1.18.2.exe"
                if Path(r"C:\util\chafa-1.18.2.exe").is_file()
                else None
            )
            or shutil.which("chafa")
        )
        if exact_chafa:
            command = (
                str(exact_chafa),
                "--format=sixels",
                "--colors=full",
                f"--view-size={geometry.columns}x{geometry.rows}",
                "--scale=max",
                "--optimize=9",
                "--work=9",
                "--color-space=din99d",
                str(path),
                "--margin-bottom=4",
                "--margin-right=0",
            )
            return PreparedArtworkPreview(
                mode="direct Chafa 1.18.2 Sixel",
                geometry=geometry,
                renderer_options=command[1:-1],
                direct_command=command,
            )
    return PreparedArtworkPreview(
        mode="native Pillow Sixel" if use_color else "ANSI grayscale",
        geometry=geometry,
        sixel_payload=(
            sixel_preview_bytes(
                path,
                geometry=geometry,
                stretch_to_width=True,
                height_multiplier=1.0,
            )
            if use_color
            else None
        ),
        text_payload=(
            ansi_half_block_preview(
                path,
                use_color=False,
                geometry=geometry,
                stretch_to_width=True,
                height_multiplier=1.0,
            )
            if not use_color
            else None
        ),
    )


def render_waveform_preview(path: Path, *, use_color: bool) -> str:
    """Render an ordinary waveform at the configured review width."""
    return emit_prepared_artwork_preview(
        prepare_waveform_preview(
            path,
            use_color=use_color,
            width_fraction=WAVEFORM_REVIEW_WIDTH_FRACTION,
            height_scale=WAVEFORM_REVIEW_HEIGHT_SCALE,
        )
    )


def render_waveform_comparison_preview(path: Path, *, use_color: bool) -> str:
    """Render pre/post ReplayGain comparison waves at the configured wide width."""
    return emit_prepared_artwork_preview(
        prepare_waveform_preview(
            path,
            use_color=use_color,
            width_fraction=WAVEFORM_COMPARISON_WIDTH_FRACTION,
            height_scale=WAVEFORM_COMPARISON_HEIGHT_SCALE,
        )
    )



CALIBRATION_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
CALIBRATION_CHAFA_TIMEOUT_SECONDS = 15.0
CALIBRATION_SIXEL_CHUNK_BYTES = 16 * 1024
CALIBRATION_PATTERN_RASTER = (100, 100)


def _calibration_scalar_snapshot(value: Any) -> dict[str, Any]:
    """Extract simple public geometry fields without assuming helper internals."""
    snapshot: dict[str, Any] = {}
    for name in sorted(set(dir(value))):
        if name.startswith("_") or name in {"chafa_options_for"}:
            continue
        try:
            item = getattr(value, name)
        except Exception:
            continue
        if callable(item):
            continue
        if isinstance(item, (str, int, float, bool, type(None))):
            snapshot[name] = item
        elif isinstance(item, (tuple, list)) and all(
            isinstance(part, (str, int, float, bool, type(None))) for part in item
        ):
            snapshot[name] = list(item)
    return snapshot


def shared_terminal_geometry_snapshot() -> dict[str, Any]:
    """Capture the established claire_terminal_geometry result used by Chafa."""
    if not callable(query_terminal_geometry):
        return {
            "available": False,
            "module": None,
            "values": {},
            "chafa_options": None,
            "error": "claire_terminal_geometry could not be imported",
        }
    try:
        live = query_terminal_geometry()
        module = sys.modules.get(getattr(query_terminal_geometry, "__module__", ""))
        module_path = str(getattr(module, "__file__", "") or "") or None
        try:
            options = live.chafa_options_for(
                reserved_rows=ART_PREVIEW_RESERVED_TEXT_ROWS
            )
        except Exception as exc:
            options = f"<error: {type(exc).__name__}: {exc}>"
        return {
            "available": True,
            "module": module_path,
            "values": _calibration_scalar_snapshot(live),
            "chafa_options": options,
            "error": None,
        }
    except Exception as exc:
        return {
            "available": False,
            "module": None,
            "values": {},
            "chafa_options": None,
            "error": f"{type(exc).__name__}: {exc}",
        }


def query_terminal_pixel_geometry_windows(
    parameter: int,
    *,
    expected_result_code: int,
    timeout_seconds: float = 0.35,
) -> dict[str, Any]:
    """Ask the terminal for pixel geometry using xterm-compatible CSI ... t.

    CSI 14 t returns ``CSI 4 ; height ; width t`` for the text area in pixels.
    CSI 16 t returns ``CSI 6 ; height ; width t`` for one character cell.
    Windows Terminal versions that do not support the query simply time out.
    """
    result: dict[str, Any] = {
        "parameter": int(parameter),
        "supported": False,
        "width": None,
        "height": None,
        "raw": "",
        "error": None,
    }
    if os.name != "nt":
        result["error"] = "not Windows"
        return result
    try:
        import msvcrt

        target = _raw_console_stream(sys.stdout)
        target.write(f"\x1b[{int(parameter)}t")
        target.flush()
        deadline = time.perf_counter() + max(0.05, float(timeout_seconds))
        chars: list[str] = []
        while time.perf_counter() < deadline:
            if msvcrt.kbhit():
                chars.append(msvcrt.getwch())
                if chars[-1] == "t":
                    break
            else:
                time.sleep(0.005)
        raw = "".join(chars)
        result["raw"] = raw.encode("unicode_escape").decode("ascii")
        match = re.search(r"\x1b\[(\d+);(\d+);(\d+)t", raw)
        if match and int(match.group(1)) == int(expected_result_code):
            result["height"] = int(match.group(2))
            result["width"] = int(match.group(3))
            result["supported"] = True
        elif raw:
            result["error"] = "unexpected terminal response"
        else:
            result["error"] = "no response before timeout"
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def terminal_calibration_measurements() -> dict[str, Any]:
    """Collect every independent geometry signal we can compare on Windows."""
    visible = visible_console_size()
    viewport = windows_console_viewport_state()
    font_cell = windows_console_font_cell_size()
    shared = shared_terminal_geometry_snapshot()
    csi14 = query_terminal_pixel_geometry_windows(14, expected_result_code=4)
    csi16 = query_terminal_pixel_geometry_windows(16, expected_result_code=6)
    measurements = {
        "visible_cells": [int(visible.columns), int(visible.lines)],
        "win32_viewport": (
            {
                "columns": viewport.columns,
                "rows": viewport.rows,
                "cursor_column": viewport.cursor_column,
                "cursor_row": viewport.cursor_row,
                "window_top": viewport.window_top,
                "window_bottom": viewport.window_bottom,
            }
            if viewport is not None
            else None
        ),
        "win32_font_cell_pixels": list(font_cell) if font_cell else None,
        "windows_dpi_scale": windows_console_pixel_scale_factor(),
        "csi_14_text_area_pixels": csi14,
        "csi_16_cell_pixels": csi16,
        "shared_geometry": shared,
    }
    measurements.update(calibration_geometry_analysis(measurements))
    return measurements


def _calibration_pixel_pair(width: Any, height: Any) -> list[float] | None:
    """Normalize one width/height signal without treating it as authoritative."""
    try:
        pair = [float(width), float(height)]
    except (TypeError, ValueError):
        return None
    if not all(math.isfinite(value) and value > 0 for value in pair):
        return None
    return [round(value, 4) for value in pair]


def calibration_geometry_analysis(measurements: dict[str, Any]) -> dict[str, Any]:
    """Compare independent cell-pixel signals and leave every raw value intact.

    This intentionally does not select a winner.  The controlled Sixel raster
    later in the calibration is the empirical check against these reports.
    """
    signals: dict[str, list[float]] = {}
    csi16 = measurements.get("csi_16_cell_pixels") or {}
    pair = _calibration_pixel_pair(csi16.get("width"), csi16.get("height"))
    if csi16.get("supported") and pair:
        signals["csi_16t"] = pair

    visible = measurements.get("visible_cells") or []
    csi14 = measurements.get("csi_14_text_area_pixels") or {}
    if (
        csi14.get("supported")
        and len(visible) == 2
        and int(visible[0]) > 0
        and int(visible[1]) > 0
    ):
        pair = _calibration_pixel_pair(
            float(csi14.get("width")) / int(visible[0]),
            float(csi14.get("height")) / int(visible[1]),
        )
        if pair:
            signals["csi_14t_div_visible_cells"] = pair

    shared_values = (
        (measurements.get("shared_geometry") or {}).get("values") or {}
    )
    pair = _calibration_pixel_pair(
        shared_values.get("cell_width"), shared_values.get("cell_height")
    )
    if pair:
        signals["claire_terminal_geometry"] = pair

    font_cell = measurements.get("win32_font_cell_pixels") or []
    if len(font_cell) == 2:
        pair = _calibration_pixel_pair(font_cell[0], font_cell[1])
        if pair:
            signals["win32_console_font"] = pair
            dpi_scale = float(measurements.get("windows_dpi_scale") or 1.0)
            scaled_pair = _calibration_pixel_pair(
                pair[0] * dpi_scale, pair[1] * dpi_scale
            )
            if scaled_pair:
                signals["win32_console_font_times_dpi"] = scaled_pair

    disagreements: list[dict[str, Any]] = []
    names = sorted(signals)
    for left_index, left_name in enumerate(names):
        for right_name in names[left_index + 1 :]:
            left = signals[left_name]
            right = signals[right_name]
            delta = [round(left[0] - right[0], 4), round(left[1] - right[1], 4)]
            if abs(delta[0]) > 0.25 or abs(delta[1]) > 0.25:
                disagreements.append(
                    {
                        "left": left_name,
                        "left_pixels": left,
                        "right": right_name,
                        "right_pixels": right,
                        "delta_pixels": delta,
                    }
                )

    cell_count_disagreements: list[dict[str, Any]] = []
    viewport = measurements.get("win32_viewport") or {}
    if len(visible) == 2 and viewport:
        win32_cells = [viewport.get("columns"), viewport.get("rows")]
        if list(visible) != win32_cells:
            cell_count_disagreements.append(
                {
                    "visible_console_size": list(visible),
                    "win32_viewport": win32_cells,
                }
            )

    derived = signals.get("csi_14t_div_visible_cells")
    return {
        "derived_cell_pixels_from_csi14_visible_cells": derived,
        "independent_cell_pixel_signals": signals,
        "cell_pixel_disagreements": disagreements,
        "visible_cell_disagreements": cell_count_disagreements,
        "reconciled_cell_pixels": None,
    }


def _calibration_source_image_size(path: Path) -> tuple[int, int] | None:
    if Image is None:
        return None
    try:
        with Image.open(path) as image:
            return int(image.width), int(image.height)
    except Exception:
        return None


def find_calibration_audio(root: Path, max_depth: int = 5) -> Path | None:
    """Choose one deterministic audio file from a bounded calibration tree."""
    start = Path(root).resolve(strict=False)
    stack: list[tuple[Path, int]] = [(start, 0)]
    visited: set[str] = set()
    candidates: list[Path] = []
    while stack:
        folder, depth = stack.pop()
        key = os.path.normcase(str(folder.resolve(strict=False)))
        if key in visited:
            continue
        visited.add(key)
        try:
            entries = sorted(folder.iterdir(), key=lambda item: item.name.casefold())
        except OSError:
            continue
        for entry in entries:
            try:
                if entry.is_file() and entry.suffix.casefold() in ALLOWED_AUDIO_EXTS:
                    candidates.append(entry)
                elif depth < max_depth and entry.is_dir():
                    stack.append((entry, depth + 1))
            except OSError:
                continue
        if candidates:
            return sorted(candidates, key=lambda item: str(item).casefold())[0]
    return None


def build_direct_chafa_calibration_command(
    source: Path,
) -> tuple[list[str], ArtworkPreviewGeometry]:
    """Build the normal shared-geometry Chafa Sixel command without running it."""
    chafa = chafa_executable()
    if chafa is None:
        raise RuntimeError("Chafa was not found; Renderer A cannot run directly")
    geometry = artwork_preview_geometry(
        indent_columns=0,
        right_margin_columns=0,
        reserved_text_rows=ART_PREVIEW_RESERVED_TEXT_ROWS,
    )
    scaled_geometry = scaled_artwork_geometry(geometry)
    command = [
        str(chafa),
        "--format=sixels",
        "--fit-width",
        "--colors=full",
        f"--size={scaled_geometry.columns}x{scaled_geometry.rows}",
        *chafa_sixel_geometry_options(geometry),
        "--optimize=9",
        "--work=9",
        "--color-space=din99d",
        str(Path(source)),
    ]
    return command, geometry


def run_direct_chafa_calibration(
    command: list[str],
    *,
    timeout_seconds: float = CALIBRATION_CHAFA_TIMEOUT_SECONDS,
    popen_factory=None,
    clock=None,
) -> dict[str, Any]:
    """Run Chafa with inherited stdio and a hard watchdog deadline.

    Inherited stdout/stderr is the point of Renderer A: Python never captures,
    wraps, counts, or re-emits Chafa's Sixel payload.  A blocked terminal write
    therefore cannot strand calibration forever.
    """
    factory = popen_factory or subprocess.Popen
    timer = clock or time.perf_counter
    started = timer()
    process = factory(
        list(command),
        stdin=None,
        stdout=None,
        stderr=None,
    )
    timed_out = False
    terminated = False
    killed = False
    try:
        return_code = process.wait(timeout=max(0.05, float(timeout_seconds)))
    except subprocess.TimeoutExpired:
        timed_out = True
        terminated = True
        process.terminate()
        try:
            return_code = process.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            killed = True
            process.kill()
            return_code = process.wait()
    elapsed = max(0.0, timer() - started)
    return {
        "return_code": int(return_code),
        "timed_out": timed_out,
        "watchdog_seconds": float(timeout_seconds),
        "terminated": terminated,
        "killed": killed,
        "terminal_emission_seconds": round(elapsed, 6),
        "timing_scope": (
            "whole Chafa process (render plus inherited terminal emission); "
            "these cannot be separated without capturing the payload"
        ),
        "stdio": "inherited directly by Chafa",
    }


def emit_terminal_bytes_chunked(
    payload: bytes,
    *,
    chunk_size: int = CALIBRATION_SIXEL_CHUNK_BYTES,
    writer=None,
    clock=None,
) -> dict[str, Any]:
    """Write terminal bytes in bounded chunks and time actual emission."""
    size = max(256, int(chunk_size))
    timer = clock or time.perf_counter
    binary_stream = getattr(_raw_console_stream(sys.stdout), "buffer", None)
    descriptor: int | None = None
    if writer is None:
        try:
            descriptor = _raw_console_stream(sys.stdout).fileno()
        except (AttributeError, OSError, ValueError, io.UnsupportedOperation):
            descriptor = None

    chunks = 0
    written = 0
    started = timer()
    for offset in range(0, len(payload), size):
        block = payload[offset : offset + size]
        chunks += 1
        if writer is not None:
            result = writer(block)
            written += len(block) if result is None else int(result)
        elif descriptor is not None:
            view = memoryview(block)
            while view:
                count = os.write(descriptor, view)
                if count <= 0:
                    raise OSError("terminal write made no progress")
                written += count
                view = view[count:]
        elif binary_stream is not None:
            result = binary_stream.write(block)
            written += len(block) if result is None else int(result)
        else:
            text_block = block.decode("ascii", errors="replace")
            _raw_console_stream(sys.stdout).write(text_block)
            written += len(block)
    target = _raw_console_stream(sys.stdout)
    try:
        target.flush()
    except Exception:
        if binary_stream is not None:
            binary_stream.flush()
    elapsed = max(0.0, timer() - started)
    return {
        "chunk_size_bytes": size,
        "chunks": chunks,
        "bytes_written": written,
        "terminal_emission_seconds": round(elapsed, 6),
    }


def emit_sixel_preview_chunked(
    payload: bytes,
    *,
    geometry: ArtworkPreviewGeometry,
    chunk_size: int = CALIBRATION_SIXEL_CHUNK_BYTES,
    writer=None,
    clock=None,
) -> dict[str, Any]:
    """Emit a calibration Sixel frame without one giant blocking write."""
    frame, reserved_rows = sixel_terminal_frame(payload, geometry=geometry)
    result = emit_terminal_bytes_chunked(
        frame,
        chunk_size=chunk_size,
        writer=writer,
        clock=clock,
    )
    result.update(
        {
            "payload_bytes": len(payload),
            "framed_bytes": len(frame),
            "reserved_terminal_rows": reserved_rows,
        }
    )
    return result


def controlled_sixel_test_pattern(
    width: int = CALIBRATION_PATTERN_RASTER[0],
    height: int = CALIBRATION_PATTERN_RASTER[1],
) -> bytes:
    """Create a dependency-free, known-size checker/border Sixel raster."""
    width = max(1, int(width))
    height = max(1, int(height))
    pieces = [
        '\033P9;1;0q',
        f'"1;1;{width};{height}',
        "#0;2;100;100;100",
        "#1;2;100;0;70",
        "#2;2;0;75;100",
    ]
    for band_y in range(0, height, 6):
        masks = {0: bytearray(width), 1: bytearray(width), 2: bytearray(width)}
        for offset, y in enumerate(range(band_y, min(band_y + 6, height))):
            bit = 1 << offset
            for x in range(width):
                border = x in {0, width - 1} or y in {0, height - 1}
                center = x in {width // 2 - 1, width // 2} or y in {
                    height // 2 - 1,
                    height // 2,
                }
                color = 0 if border or center else 1 + ((x // 10 + y // 10) % 2)
                masks[color][x] |= bit
        for index, color in enumerate((0, 1, 2)):
            pieces.append(f"#{color}")
            previous: str | None = None
            count = 0
            for bits in masks[color]:
                character = chr(63 + bits)
                if character == previous:
                    count += 1
                else:
                    if previous is not None:
                        pieces.append(_sixel_run(previous, count))
                    previous = character
                    count = 1
            if previous is not None:
                pieces.append(_sixel_run(previous, count))
            if index != 2:
                pieces.append("$")
        if band_y + 6 < height:
            pieces.append("-")
    pieces.append("\033\\")
    return "".join(pieces).encode("ascii")


def controlled_pattern_expected_cells(
    raster: tuple[int, int],
    measurements: dict[str, Any],
) -> dict[str, list[float]]:
    """Show each geometry signal's prediction without choosing a winner."""
    width, height = raster
    predictions: dict[str, list[float]] = {}
    for name, pair in (
        measurements.get("independent_cell_pixel_signals") or {}
    ).items():
        if len(pair) == 2 and float(pair[0]) > 0 and float(pair[1]) > 0:
            predictions[name] = [
                round(width / float(pair[0]), 4),
                round(height / float(pair[1]), 4),
            ]
    return predictions


def _optional_observed_cells(prompt: str, *, line_reader=None) -> float | None:
    """Read an observed physical cell count; blank or ? means unknown."""
    reader = line_reader or input
    while True:
        raw = str(reader(prompt)).strip()
        if not raw or raw in {"?", "-"}:
            reset_console_pager_after_user_input()
            return None
        try:
            value = float(raw)
        except ValueError:
            print("        Enter a positive number, or leave it blank if unsure.")
            continue
        if value > 0 and math.isfinite(value):
            reset_console_pager_after_user_input()
            return round(value, 4)
        print("        Enter a positive number, or leave it blank if unsure.")


def observe_controlled_sixel_pattern(
    measurements: dict[str, Any],
    *,
    line_reader=None,
) -> dict[str, Any]:
    """Display a 100x100 raster and collect its real Windows Terminal footprint."""
    raster = CALIBRATION_PATTERN_RASTER
    payload = controlled_sixel_test_pattern(*raster)
    visible = measurements.get("visible_cells") or [80, 24]
    geometry = ArtworkPreviewGeometry(
        terminal_columns=int(visible[0]),
        terminal_rows=int(visible[1]),
        indent_columns=0,
        columns=10,
        rows=5,
        pixel_width=raster[0],
        pixel_height=raster[1],
    )
    print()
    print("        -- Controlled built-in Sixel: exact 100x100-pixel raster --")
    print("        Measure the outer white border in terminal cells; decimals are OK.")
    emission = emit_sixel_preview_chunked(payload, geometry=geometry)
    observed_width = _optional_observed_cells(
        "        Observed physical width in cells (blank if unsure): ",
        line_reader=line_reader,
    )
    observed_height = _optional_observed_cells(
        "        Observed physical height in cells (blank if unsure): ",
        line_reader=line_reader,
    )
    return {
        "declared_sixel_raster": list(raster),
        "payload_bytes": len(payload),
        "emission": emission,
        "predicted_cells_by_independent_signal": controlled_pattern_expected_cells(
            raster, measurements
        ),
        "observed_physical_cells": [observed_width, observed_height],
    }


def build_waveform_calibration_previews(
    source: Path,
    *,
    use_color: bool,
) -> tuple[PreparedArtworkPreview, PreparedArtworkPreview]:
    """Prepare the exact same image through shared Chafa and waveform Sixel."""
    source = Path(source)
    chafa_preview = prepare_artwork_preview(
        source,
        use_color=use_color,
        prefer_sixel=True,
        geometry=artwork_preview_geometry(),
        stretch_to_width=False,
    )
    builtin_preview = prepare_waveform_preview(
        source,
        use_color=use_color,
        width_fraction=WAVEFORM_COMPARISON_WIDTH_FRACTION,
        height_scale=WAVEFORM_COMPARISON_HEIGHT_SCALE,
        prefer_direct_chafa=False,
    )
    return chafa_preview, builtin_preview


def waveform_calibration_rating(
    renderer_name: str,
    *,
    key_reader=None,
) -> dict[str, str]:
    """Collect simple physical-display judgments from the real terminal user."""
    reader = key_reader or read_single_key

    def ask(question: str, choices: dict[str, str]) -> str:
        legend = " / ".join(f"{key.upper()}={label}" for key, label in choices.items())
        while True:
            print(f"        ❓ {question} [{legend}] ", end="", flush=True)
            key = reader()
            if key == "\x03":
                print()
                raise KeyboardInterrupt
            answer = choices.get(key.casefold())
            if answer is not None:
                print(answer)
                reset_console_pager_after_user_input()
                return answer
            invalid_key_beep()

    print(f"        Rate {renderer_name} on THIS Windows Terminal:")
    return {
        "width": ask(
            "Width?",
            {"g": "good", "n": "too narrow", "w": "too wide", "c": "cropped"},
        ),
        "height": ask(
            "Height?",
            {"g": "good", "s": "too short", "t": "too tall", "c": "cropped"},
        ),
        "metrics": ask(
            "Right-side summary metrics?",
            {"r": "readable", "u": "present but unreadable", "m": "missing", "c": "cropped"},
        ),
    }


def calibration_preview_record(
    prepared: PreparedArtworkPreview,
    *,
    preparation_seconds: float | None = None,
    emission: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Describe the prepared output before Windows Terminal interprets it."""
    raster = (
        sixel_payload_pixel_size(prepared.sixel_payload)
        if prepared.sixel_payload is not None
        else None
    )
    return {
        "renderer": prepared.mode,
        "preparation_seconds": (
            round(float(preparation_seconds), 6)
            if preparation_seconds is not None
            else None
        ),
        "geometry_cells": [prepared.geometry.columns, prepared.geometry.rows],
        "geometry_pixels": [prepared.geometry.pixel_width, prepared.geometry.pixel_height],
        "declared_sixel_raster": list(raster) if raster else None,
        "renderer_options": list(prepared.renderer_options),
        "payload_bytes": len(prepared.sixel_payload or b""),
        "terminal_emission_seconds": (
            emission.get("terminal_emission_seconds") if emission else None
        ),
        "emission": emission,
    }


def render_waveform_calibration_report(data: dict[str, Any]) -> str:
    """Render one stable copy/paste report for the next calibration iteration."""
    return (
        "===== WAVEFORM TERMINAL CALIBRATION REPORT =====\n"
        + json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True)
        + "\n===== END WAVEFORM TERMINAL CALIBRATION REPORT ====="
    )


def _run_waveform_terminal_calibration_v124(
    target: Path,
    *,
    use_color: bool,
    key_reader=None,
) -> int:
    """Compare real Chafa geometry with built-in Sixel on the user's terminal."""
    requested = Path(target).expanduser().resolve(strict=False)
    source_audio: Path | None = None
    source_image: Path | None = None
    generated_temp: tempfile.TemporaryDirectory[str] | None = None
    try:
        if requested.is_dir():
            source_audio = find_calibration_audio(requested)
            if source_audio is None:
                raise RuntimeError(
                    f"No supported audio file was found within 5 levels of {requested}"
                )
        elif requested.is_file() and requested.suffix.casefold() in CALIBRATION_IMAGE_EXTS:
            source_image = requested
        elif requested.is_file() and requested.suffix.casefold() in ALLOWED_AUDIO_EXTS:
            source_audio = requested
        else:
            raise RuntimeError(
                "Calibration target must be an audio file, waveform image, or folder: "
                f"{requested}"
            )

        if source_image is None:
            if source_audio is None:
                raise RuntimeError("Calibration could not resolve an audio source")
            if shutil.which("ffmpeg") is None:
                raise RuntimeError("Waveform calibration from audio requires ffmpeg in PATH")
            generated_temp = tempfile.TemporaryDirectory(prefix="audit-waveform-calibration-")
            destination = Path(generated_temp.name) / "calibration-waveform.jpg"
            source_image, _backup, _metrics = generate_waveform_jpeg(
                source_audio,
                narrate=False,
                destination=destination,
            )
        elif source_image.suffix.casefold() not in {".jpg", ".jpeg"}:
            if Image is None:
                raise RuntimeError("Pillow is required to calibrate from a non-JPEG image")
            generated_temp = tempfile.TemporaryDirectory(prefix="audit-waveform-calibration-")
            converted = Path(generated_temp.name) / "calibration-waveform.jpg"
            with Image.open(source_image) as original:
                original.convert("RGB").save(converted, format="JPEG", quality=96)
            source_image = converted

        ensure_waveform_jpeg_ready(source_image)
        image_size = _calibration_source_image_size(source_image)
        chafa_path = chafa_executable()

        print()
        print("        🧪 Waveform terminal calibration")
        print("        ⏱️ Do not type for about one second while CSI 14t/16t geometry queries run...")
        measurements = terminal_calibration_measurements()
        print(f"        📄 Source image: {source_image}")
        if source_audio is not None:
            print(f"        🎵 Source audio: {source_audio}")
        print(f"        🖼️ Source raster: {image_size[0]}×{image_size[1]}" if image_size else "        🖼️ Source raster: unknown")
        print(f"        🖥️ Chafa executable: {chafa_path or 'NOT FOUND'}")
        print("        📐 Geometry measurements:")
        for line in json.dumps(measurements, indent=2, ensure_ascii=False, sort_keys=True).splitlines():
            print("            " + line)

        print()
        print("        ── Renderer A: shared claire_terminal_geometry + Chafa ──")
        chafa_preview, builtin_preview = build_waveform_calibration_previews(
            source_image,
            use_color=use_color,
        )
        chafa_record = calibration_preview_record(chafa_preview)
        print("        Prepared output:")
        for line in json.dumps(chafa_record, indent=2, ensure_ascii=False, sort_keys=True).splitlines():
            print("            " + line)
        if chafa_preview.mode != "Chafa Sixel":
            print(
                "        ⚠️ Renderer A did NOT actually reach Chafa Sixel; "
                f"the runtime fell back to {chafa_preview.mode}."
            )
        emit_prepared_artwork_preview(chafa_preview)
        chafa_rating = waveform_calibration_rating(
            "Renderer A",
            key_reader=key_reader,
        )

        print()
        print("        ── Renderer B: built-in waveform Sixel ──")
        builtin_record = calibration_preview_record(builtin_preview)
        print("        Prepared output:")
        for line in json.dumps(builtin_record, indent=2, ensure_ascii=False, sort_keys=True).splitlines():
            print("            " + line)
        emit_prepared_artwork_preview(builtin_preview)
        builtin_rating = waveform_calibration_rating(
            "Renderer B",
            key_reader=key_reader,
        )

        report = {
            "audit_music_batch_version": AUDIT_MUSIC_BATCH_VERSION,
            "release_date": AUDIT_MUSIC_BATCH_RELEASE_DATE,
            "requested_target": str(requested),
            "source_audio": str(source_audio) if source_audio else None,
            "source_image": str(source_image),
            "source_raster": list(image_size) if image_size else None,
            "measurements": measurements,
            "renderer_A_shared_chafa": {
                **chafa_record,
                "rating": chafa_rating,
            },
            "renderer_B_builtin_sixel": {
                **builtin_record,
                "rating": builtin_rating,
            },
        }
        print()
        print(render_waveform_calibration_report(report))
        print()
        print("        📋 Copy/paste the report above back into ChatGPT with a screenshot of both renderers.")
        return 0
    finally:
        if generated_temp is not None:
            generated_temp.cleanup()


def run_waveform_terminal_calibration(
    target: Path,
    *,
    use_color: bool,
    key_reader=None,
    line_reader=None,
) -> int:
    """Compare direct Chafa, controlled pixels, and chunked built-in Sixel."""
    del use_color  # Calibration explicitly exercises Sixel even with --no-color.
    requested = Path(target).expanduser().resolve(strict=False)
    source_audio: Path | None = None
    source_image: Path | None = None
    generated_temp: tempfile.TemporaryDirectory[str] | None = None
    try:
        if requested.is_dir():
            source_audio = find_calibration_audio(requested)
            if source_audio is None:
                raise RuntimeError(
                    f"No supported audio file was found within 5 levels of {requested}"
                )
        elif requested.is_file() and requested.suffix.casefold() in CALIBRATION_IMAGE_EXTS:
            source_image = requested
        elif requested.is_file() and requested.suffix.casefold() in ALLOWED_AUDIO_EXTS:
            source_audio = requested
        else:
            raise RuntimeError(
                "Calibration target must be an audio file, waveform image, or folder: "
                f"{requested}"
            )

        if source_image is None:
            if source_audio is None:
                raise RuntimeError("Calibration could not resolve an audio source")
            if shutil.which("ffmpeg") is None:
                raise RuntimeError("Waveform calibration from audio requires ffmpeg in PATH")
            generated_temp = tempfile.TemporaryDirectory(
                prefix="audit-waveform-calibration-"
            )
            destination = Path(generated_temp.name) / "calibration-waveform.jpg"
            source_image, _backup, _metrics = generate_waveform_jpeg(
                source_audio,
                narrate=False,
                destination=destination,
            )
        elif source_image.suffix.casefold() not in {".jpg", ".jpeg"}:
            if Image is None:
                raise RuntimeError(
                    "Pillow is required to calibrate from a non-JPEG image"
                )
            generated_temp = tempfile.TemporaryDirectory(
                prefix="audit-waveform-calibration-"
            )
            converted = Path(generated_temp.name) / "calibration-waveform.jpg"
            with Image.open(source_image) as original:
                original.convert("RGB").save(converted, format="JPEG", quality=96)
            source_image = converted

        ensure_waveform_jpeg_ready(source_image)
        image_size = _calibration_source_image_size(source_image)
        chafa_path = chafa_executable()
        if chafa_path is None:
            raise RuntimeError("Waveform terminal calibration requires Chafa")

        print()
        print("        Waveform terminal calibration")
        print("        Do not type while the CSI 14t/16t geometry queries run...")
        measurements = terminal_calibration_measurements()
        print(f"        Source image: {source_image}")
        if source_audio is not None:
            print(f"        Source audio: {source_audio}")
        print(
            f"        Source raster: {image_size[0]}x{image_size[1]}"
            if image_size
            else "        Source raster: unknown"
        )
        print(f"        Chafa executable: {chafa_path}")
        print("        Independent geometry measurements (no value is forced):")
        for line in json.dumps(
            measurements, indent=2, ensure_ascii=False, sort_keys=True
        ).splitlines():
            print("            " + line)

        controlled_pattern = observe_controlled_sixel_pattern(
            measurements,
            line_reader=line_reader,
        )

        print()
        print("        -- Renderer A: direct shared-geometry Chafa --")
        prepare_started = time.perf_counter()
        chafa_command, chafa_geometry = build_direct_chafa_calibration_command(
            source_image
        )
        chafa_prepare_seconds = time.perf_counter() - prepare_started
        chafa_record: dict[str, Any] = {
            "renderer": "Chafa Sixel (direct inherited stdio)",
            "preparation_seconds": round(chafa_prepare_seconds, 6),
            "geometry_cells": [chafa_geometry.columns, chafa_geometry.rows],
            "geometry_pixels": [
                chafa_geometry.pixel_width,
                chafa_geometry.pixel_height,
            ],
            "declared_sixel_raster": None,
            "payload_bytes": None,
            "unavailable_metrics_reason": (
                "Direct inherited stdout deliberately prevents Python from "
                "capturing/counting/parsing Chafa's Sixel payload."
            ),
            "renderer_options": chafa_command[1:-1],
        }
        print("        Prepared direct command:")
        for line in json.dumps(
            chafa_record, indent=2, ensure_ascii=False, sort_keys=True
        ).splitlines():
            print("            " + line)
        print(
            f"        Chafa now owns the terminal directly; watchdog: "
            f"{CALIBRATION_CHAFA_TIMEOUT_SECONDS:g}s."
        )
        chafa_execution = run_direct_chafa_calibration(chafa_command)
        chafa_record["terminal_emission_seconds"] = chafa_execution[
            "terminal_emission_seconds"
        ]
        chafa_record["execution"] = chafa_execution
        print()
        if chafa_execution["timed_out"]:
            print("        WARNING: Chafa exceeded the watchdog and was stopped.")
        elif chafa_execution["return_code"] != 0:
            print(
                "        WARNING: Direct Chafa exited with code "
                f"{chafa_execution['return_code']}."
            )
        chafa_rating = waveform_calibration_rating(
            "Renderer A",
            key_reader=key_reader,
        )

        print()
        print("        -- Renderer B: built-in waveform Sixel, chunked --")
        builtin_prepare_started = time.perf_counter()
        builtin_preview = prepare_waveform_preview(
            source_image,
            use_color=True,
            width_fraction=WAVEFORM_COMPARISON_WIDTH_FRACTION,
            height_scale=WAVEFORM_COMPARISON_HEIGHT_SCALE,
            prefer_direct_chafa=False,
        )
        builtin_prepare_seconds = time.perf_counter() - builtin_prepare_started
        if builtin_preview.sixel_payload is None:
            raise RuntimeError("Renderer B did not produce a Sixel payload")
        builtin_record = calibration_preview_record(
            builtin_preview,
            preparation_seconds=builtin_prepare_seconds,
        )
        print("        Prepared output:")
        for line in json.dumps(
            builtin_record, indent=2, ensure_ascii=False, sort_keys=True
        ).splitlines():
            print("            " + line)
        builtin_emission = emit_sixel_preview_chunked(
            builtin_preview.sixel_payload,
            geometry=builtin_preview.geometry,
        )
        builtin_record["terminal_emission_seconds"] = builtin_emission[
            "terminal_emission_seconds"
        ]
        builtin_record["emission"] = builtin_emission
        builtin_rating = waveform_calibration_rating(
            "Renderer B",
            key_reader=key_reader,
        )

        report = {
            "audit_music_batch_version": AUDIT_MUSIC_BATCH_VERSION,
            "release_date": AUDIT_MUSIC_BATCH_RELEASE_DATE,
            "requested_target": str(requested),
            "source_audio": str(source_audio) if source_audio else None,
            "source_image": str(source_image),
            "source_raster": list(image_size) if image_size else None,
            "measurements": measurements,
            "controlled_builtin_sixel_pattern": controlled_pattern,
            "renderer_A_direct_chafa": {
                **chafa_record,
                "rating": chafa_rating,
            },
            "renderer_B_builtin_sixel": {
                **builtin_record,
                "rating": builtin_rating,
            },
        }
        print()
        print(render_waveform_calibration_report(report))
        print()
        print("        Copy/paste the report above with a screenshot of both renderers.")
        return 0
    finally:
        if generated_temp is not None:
            generated_temp.cleanup()


def launch_irfanview(path: Path) -> Path:
    """Open one image through openimage.bat or its standalone equivalent."""
    launcher = openimage_launcher()
    executable = irfanview_executable()
    if launcher is not None:
        # openimage.bat uses TCC-specific syntax. Use it when TCC is callable;
        # otherwise reproduce its effective action directly below.
        tcc = shutil.which("tcc.exe") or shutil.which("tcc")
        if tcc:
            subprocess.Popen(
                [tcc, "/c", "call", str(launcher), str(path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return launcher
    if executable is None:
        raise RuntimeError(
            "openimage.bat/IrfanView could not be launched; set "
            "IMAGE_VIEWER_EXECUTABLE in the USER CONFIGURATION section "
            "near the top of audit_music_batch.py"
        )
    subprocess.Popen(
        [str(executable), str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return executable


def audio_editor_executable() -> Path | None:
    """Find a configured or installed audio editor for waveform review."""
    configured = (
        AUDIO_EDITOR_EXECUTABLE
        or os.environ.get("AUDIT_MUSIC_AUDIO_EDITOR")
    )
    if configured:
        candidate = Path(os.path.expandvars(configured))
        if candidate.is_file():
            return candidate

    discovered_names = (
        "Adobe Audition.exe",
        "Adobe Audition CC.exe",
        "audition.exe",
        "coolpro2.exe",
        "coolpro.exe",
        "ocenaudio.exe",
        "audacity.exe",
        "forge32.exe",
    )
    for name in discovered_names:
        discovered = shutil.which(name)
        if discovered:
            return Path(discovered)

    program_roots = [
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")),
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")),
    ]
    for program_root in program_roots:
        adobe_root = program_root / "Adobe"
        if adobe_root.is_dir():
            auditions = sorted(
                adobe_root.glob("Adobe Audition*/Adobe Audition*.exe"),
                key=lambda item: item.name.casefold(),
                reverse=True,
            )
            if auditions:
                return auditions[0]

    fixed_candidates = (
        Path(r"C:\coolpro2\coolpro2.exe"),
        Path(r"C:\coolpro\coolpro.exe"),
        Path(r"C:\audio\soundforge\FORGE32.EXE"),
        Path(r"C:\BAT\cooledit2.bat"),
        Path(r"C:\BAT\soundforge.bat"),
    )
    return next(
        (candidate for candidate in fixed_candidates if candidate.is_file()),
        None,
    )


def launch_audio_editor(audio_path: Path) -> Path:
    """Open one audio file in the best available editor without blocking."""
    editor = audio_editor_executable()
    if editor is None:
        raise RuntimeError(
            "No audio editor was found; set AUDIO_EDITOR_EXECUTABLE in the "
            "USER CONFIGURATION section near the top of audit_music_batch.py"
        )
    if editor.suffix.casefold() in {".bat", ".cmd"}:
        command_processor = os.environ.get("COMSPEC", "cmd.exe")
        subprocess.Popen(
            [
                command_processor,
                "/d",
                "/c",
                "call",
                str(editor),
                str(audio_path),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        subprocess.Popen(
            [str(editor), str(audio_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    return editor


def audio_preview_player_script() -> Path | None:
    """Find the format-neutral interactive FFplay controller."""
    script_folder = Path(__file__).resolve().parent
    candidates = (
        script_folder / "play_audio_file.py",
        Path(r"C:\BAT\play_audio_file.py"),
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    discovered = shutil.which("play_audio_file.py")
    if discovered:
        return Path(discovered)
    return None


def launch_audio_preview(audio_path: Path) -> Path:
    """Synchronously preview audio with the keyboard-controlled local player."""
    player = audio_preview_player_script()
    if player is None:
        raise RuntimeError(
            "play_audio_file.py was not found beside audit_music_batch.py, "
            "under C:\\BAT, or in PATH"
        )
    result = subprocess.run(
        [sys.executable, str(player), str(audio_path)],
        check=False,
    )
    if result.returncode:
        raise RuntimeError(
            f"{player.name} exited with status {result.returncode}"
        )
    return player


def read_artwork_review_key(
    key_reader,
    rendered_size: os.terminal_size,
) -> str:
    """Read a review key, reporting a live Windows viewport resize as a key."""
    if key_reader is not None:
        return key_reader()
    if (
        os.name != "nt"
        or not bool(getattr(sys.stdin, "isatty", lambda: False)())
        or not bool(getattr(sys.stdout, "isatty", lambda: False)())
    ):
        return read_single_key()

    import msvcrt

    while True:
        if visible_console_size() != rendered_size:
            return "__resize__"
        if msvcrt.kbhit():
            key = msvcrt.getwch()
            if key in {"\x00", "\xe0"}:
                msvcrt.getwch()
                return ""
            return key
        time.sleep(0.08)


def artwork_review_choices(use_color: bool) -> str:
    """Spell out every artwork-review key instead of using cryptic letters."""
    plain = "Y=Yes | N=No | A=Yes for folder | S=No for folder | O=Open default | Shift+O=IrfanView | R=Refresh | V=View original"
    if not use_color:
        return f"[{plain}]"
    return (
        f"{rgb_text('[', 255, 205, 55, True)}"
        f"{ANSI['bold']}\033[38;2;95;245;135mY{ANSI['reset']}"
        f"{rgb_text('=Yes/Enter | ', 255, 190, 95, True)}"
        f"{ANSI['bold']}\033[38;2;255;105;105mN{ANSI['reset']}"
        f"{rgb_text('=No | ', 255, 190, 95, True)}"
        f"{ANSI['bold']}\033[38;2;255;215;80mR{ANSI['reset']}"
        f"{rgb_text('=Refresh | ', 255, 190, 95, True)}"
        f"{ANSI['bold']}\033[38;2;185;145;255mV{ANSI['reset']}"
        f"{rgb_text('=View original]', 255, 190, 95, True)}"
    )


def artwork_review_choice(
    path: Path,
    *,
    label: str,
    use_color: bool,
    key_reader=None,
    preview_renderer=None,
    image_viewer=None,
    question_text: str | None = None,
) -> bool:
    """Preview one download and wait for Yes, No, Refresh, or View."""
    renderer = preview_renderer or render_artwork_preview
    viewer = image_viewer or launch_irfanview
    question = (
        question_text
        or f"Approve this downloaded artwork image as {label}?"
    )
    while True:
        rendered_size = visible_console_size()
        reset_console_pager_after_user_input()
        mode = renderer(path, use_color=use_color)
        resolution = image_resolution(path)
        cover_narration(
            "👁️",
            f"Preview rendered with {mode}.",
            use_color=use_color,
            color=(105, 95, 145),
            dim=True,
        )
        cover_narration(
            "🖼️",
            f"Image resolution: {resolution}.",
            use_color=use_color,
            color=(125, 150, 175),
            dim=True,
        )
        prompt_visible = False
        while True:
            prompt = urgent_prompt_text(question, use_color)
            steady = prompt_with_option_legend(
                prompt,
                artwork_review_choices(use_color),
                indent="            ",
            )
            interactive_terminal = bool(
                getattr(sys.stdout, "isatty", lambda: False)()
            )
            if not prompt_visible:
                print(
                    blinking_approval_prompt(
                        steady,
                        use_color and interactive_terminal,
                    ),
                    end="",
                    flush=True,
                )
                prompt_visible = True
            key = read_artwork_review_key(key_reader, rendered_size)
            if key == "\x03":
                raise KeyboardInterrupt
            lowered = key.casefold()
            if key == "__resize__" or lowered == "r":
                if interactive_terminal:
                    erase_wrapped_console_text(steady)
                else:
                    print()
                cover_narration(
                    "🔄",
                    "Console viewport changed; re-rendering at the live size.",
                    use_color=use_color,
                    color=(105, 145, 180),
                    dim=True,
                )
                break
            if lowered == "v":
                if interactive_terminal:
                    erase_wrapped_console_text(steady)
                else:
                    print()
                prompt_visible = False
                try:
                    opened_with = viewer(path)
                    cover_narration(
                        "🔎",
                        f"Opened {path.name} in {Path(opened_with).name}; "
                        "return here to choose Yes, No, or Refresh.",
                        use_color=use_color,
                        color=(150, 120, 205),
                        dim=True,
                    )
                except Exception as exc:
                    cover_narration(
                        "❌",
                        f"Could not open the original image: {exc}.",
                        use_color=use_color,
                        color=(255, 90, 100),
                    )
                continue
            if key == "o":
                if interactive_terminal:
                    erase_wrapped_console_text(steady)
                else:
                    print()
                try:
                    opened_with = launch_default_image_viewer(path)
                    cover_narration("🖼️", f"Opened {path.name} in the default image viewer.", use_color=use_color, color=(150, 120, 205), dim=True)
                except Exception as exc:
                    cover_narration("❌", f"Could not open the image: {exc}.", use_color=use_color, color=(255, 90, 100))
                continue
            if key == "O":
                if interactive_terminal:
                    erase_wrapped_console_text(steady)
                else:
                    print()
                try:
                    opened_with = launch_irfanview(path)
                    cover_narration("🖼️", f"Opened {path.name} in IrfanView.", use_color=use_color, color=(150, 120, 205), dim=True)
                except Exception as exc:
                    cover_narration("❌", f"Could not open IrfanView: {exc}.", use_color=use_color, color=(255, 90, 100))
                continue
            if key in {"\r", "\n"} or lowered == "y":
                accepted = True
            elif lowered == "n":
                accepted = False
            else:
                invalid_key_beep()
                continue
            settled = (
                f"            {prompt} "
                f"{approval_answer(accepted, use_color)}"
            )
            if interactive_terminal:
                erase_wrapped_console_text(steady)
                print(
                    f"{settled}{ANSI['erase_to_eol']}"
                )
            else:
                print("Yes!" if accepted else "No!")
            reset_console_pager_after_user_input()
            return accepted


def waveform_review_choices(
    use_color: bool,
    *,
    default_edit: bool = False,
    allow_bake_gain: bool = False,
) -> str:
    """Render explicit diagnostic waveform-review controls."""
    edit_label = "ENTER/E=Edit audio | " if default_edit else "E=Edit audio | "
    plain = (
        "N=It’s fine | Y=There is a problem | "
        f"P=Preview audio | {edit_label}"
        + ("B=Bake ReplayGain | " if allow_bake_gain else "")
        + "V=View fullscreen"
    )
    if not use_color:
        return f"[{plain}]"
    parts = (
        ("N", "=It’s fine | ", (95, 245, 135)),
        ("Y", "=There is a problem | ", (255, 105, 105)),
        ("P", "=Preview audio | ", (95, 205, 255)),
        (
            "ENTER/E" if default_edit else "E",
            "=Edit audio | ",
            (255, 185, 75),
        ),
        *(
            (("B", "=Bake ReplayGain | ", (90, 225, 150)),)
            if allow_bake_gain
            else ()
        ),
        ("V", "=View fullscreen", (185, 145, 255)),
    )
    rendered = [rgb_text("[", 255, 205, 55, True)]
    for key, label, color in parts:
        rendered.append(
            f"{ANSI['bold']}\033[38;2;{color[0]};{color[1]};"
            f"{color[2]}m{key}{ANSI['reset']}"
        )
        rendered.append(rgb_text(label, 255, 190, 95, True))
    rendered.append(rgb_text("]", 255, 205, 55, True))
    return "".join(rendered)


def waveform_decision_answer(decision: str, use_color: bool) -> str:
    """Render a stable non-blinking waveform diagnostic decision."""
    if decision == "fine":
        text, color = "No — it’s fine; next file.", (95, 245, 135)
    else:
        text, color = "Yes — there is a problem.", (255, 120, 80)
    if not use_color:
        return text
    return (
        f"{ANSI['bold']}\033[38;2;{color[0]};{color[1]};"
        f"{color[2]}m{text}{ANSI['reset']}"
    )


def rename_waveform_problem_family(
    audio_path: Path,
    new_filename: str,
) -> tuple[Path, list[Path], list[Path]]:
    """Rename audio plus same-stem sidecars/backups and local playlists."""
    source = audio_path.resolve()
    requested = new_filename.strip().strip('"')
    if not requested:
        return source, [], []
    if Path(requested).name != requested or any(
        character in requested for character in '<>:"/\\|?*'
    ):
        raise ValueError(
            "Enter a filename only; folders and reserved characters "
            "are not allowed"
        )
    if requested.endswith((" ", ".")):
        raise ValueError(
            "A Windows filename cannot end with a space or period"
        )
    destination_audio = source.with_name(requested)
    if destination_audio.suffix.casefold() != source.suffix.casefold():
        raise ValueError(
            f"Keep the original {source.suffix} audio extension when renaming"
        )
    if requested == source.name:
        return source, [], []

    old_stem = source.stem
    new_stem = destination_audio.stem
    family = [
        candidate
        for candidate in source.parent.iterdir()
        if candidate.is_file()
        and (
            candidate.name.casefold() == source.name.casefold()
            or candidate.name.casefold().startswith(
                f"{old_stem}.".casefold()
            )
        )
    ]
    if source not in family:
        raise FileNotFoundError(
            f"Audio file disappeared before rename: {source}"
        )
    mappings = [
        (
            candidate,
            (
                destination_audio
                if candidate == source
                else candidate.with_name(
                    new_stem + candidate.name[len(old_stem) :]
                )
            ),
        )
        for candidate in family
    ]
    destination_keys = [
        str(destination).casefold() for _source, destination in mappings
    ]
    if len(destination_keys) != len(set(destination_keys)):
        raise FileExistsError(
            "The interactive rename creates duplicate filenames"
        )
    sources = {candidate.resolve() for candidate, _destination in mappings}
    for _candidate, destination in mappings:
        if destination.exists() and destination.resolve() not in sources:
            raise FileExistsError(
                f"Refusing rename collision: {destination.name}"
            )

    playlist_updates: list[tuple[Path, str, str, str]] = []
    for playlist in source.parent.iterdir():
        if (
            not playlist.is_file()
            or playlist.suffix.casefold() not in PLAYLIST_EXTS
        ):
            continue
        original, encoding = read_text_and_encoding(playlist)
        updated = re.sub(
            re.escape(source.name),
            lambda _match: destination_audio.name,
            original,
            flags=re.I,
        )
        if updated != original:
            playlist_updates.append(
                (playlist, original, updated, encoding)
            )

    backups = [
        backup_before_inline_replacement(playlist)
        for playlist, _original, _updated, _encoding in playlist_updates
    ]
    staged: list[tuple[Path, Path, Path]] = []
    finalized: list[tuple[Path, Path, Path]] = []
    try:
        for index, (candidate, destination) in enumerate(
            mappings,
            start=1,
        ):
            temporary = collision_safe_path(
                source.parent
                / f".audit_music_batch-waveform-rename-{index:04d}.tmp"
            )
            candidate.rename(temporary)
            staged.append((candidate, temporary, destination))
        for candidate, temporary, destination in staged:
            temporary.rename(destination)
            finalized.append((candidate, temporary, destination))
        for playlist, _original, updated, encoding in playlist_updates:
            playlist.write_bytes(updated.encode(encoding))
    except Exception:
        for playlist, original, _updated, encoding in playlist_updates:
            try:
                playlist.write_bytes(original.encode(encoding))
            except Exception:
                pass
        for candidate, _temporary, destination in reversed(finalized):
            try:
                if destination.exists() and not candidate.exists():
                    destination.rename(candidate)
            except Exception:
                pass
        finalized_temporaries = {
            temporary for _candidate, temporary, _destination in finalized
        }
        for candidate, temporary, _destination in reversed(staged):
            if temporary in finalized_temporaries:
                continue
            try:
                if temporary.exists() and not candidate.exists():
                    temporary.rename(candidate)
            except Exception:
                pass
        raise

    renamed = [destination for _candidate, destination in mappings]
    if not destination_audio.is_file() or any(
        not destination.is_file() for destination in renamed
    ):
        raise RuntimeError(
            "Interactive waveform-problem rename did not verify"
        )
    return destination_audio, renamed, backups


def read_interactive_filename_edit(
    prompt: str,
    initial_filename: str,
    input_reader=None,
) -> str:
    """Read an editable, prefilled filename on Windows with safe fallbacks."""
    if input_reader is not None:
        return input_reader(prompt)
    if (
        os.name == "nt"
        and bool(getattr(sys.stdin, "isatty", lambda: False)())
        and bool(getattr(sys.stdout, "isatty", lambda: False)())
    ):
        try:
            import ctypes
            import msvcrt

            class ConsoleReadControl(ctypes.Structure):
                _fields_ = (
                    ("nLength", ctypes.c_ulong),
                    ("nInitialChars", ctypes.c_ulong),
                    ("dwCtrlWakeupMask", ctypes.c_ulong),
                    ("dwControlKeyState", ctypes.c_ulong),
                )

            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            read_console = kernel32.ReadConsoleW
            read_console.argtypes = (
                ctypes.c_void_p,
                ctypes.c_void_p,
                ctypes.c_ulong,
                ctypes.POINTER(ctypes.c_ulong),
                ctypes.POINTER(ConsoleReadControl),
            )
            read_console.restype = ctypes.c_int
            handle = msvcrt.get_osfhandle(sys.stdin.fileno())
            capacity = 32768
            buffer = ctypes.create_unicode_buffer(capacity)
            buffer.value = initial_filename
            characters_read = ctypes.c_ulong()
            control = ConsoleReadControl()
            control.nLength = ctypes.sizeof(ConsoleReadControl)
            control.nInitialChars = len(initial_filename)
            print(prompt, end="", flush=True)
            if read_console(
                handle,
                buffer,
                capacity - 1,
                ctypes.byref(characters_read),
                ctypes.byref(control),
            ):
                return buffer[: characters_read.value].rstrip("\r\n")
        except Exception:
            pass
    return input(prompt)


def prompt_for_waveform_problem_rename(
    audio_path: Path,
    *,
    use_color: bool,
    input_reader=None,
) -> Path:
    """Offer an rn.bat-style filename edit and rename its complete family."""
    print(f"            {music_filename(audio_path.name, use_color)}")
    prompt = (
        "            "
        + urgent_prompt_text(
            "New filename (press ENTER to leave unchanged):",
            use_color,
        )
        + " "
    )
    try:
        entered = read_interactive_filename_edit(
            prompt,
            audio_path.name,
            input_reader=input_reader,
        ).strip()
    except EOFError:
        entered = ""
    reset_console_pager_after_user_input()
    if not entered or entered.strip('"') == audio_path.name:
        print(
            rgb_text(
                "            ❌ Unchanged — the problem remains flagged only "
                "in this review’s results.",
                175,
                155,
                145,
                use_color,
                dim=True,
            )
        )
        return audio_path
    renamed_audio, renamed, backups = rename_waveform_problem_family(
        audio_path,
        entered,
    )
    print(
        colorize(
            f"            ✅ Renamed and verified {len(renamed)} matching "
            f"file{'s' if len(renamed) != 1 else ''}.",
            "green",
            use_color,
        )
    )
    if backups:
        print(
            rgb_text(
                f"            💾 Kept {len(backups)} playlist backup"
                f"{'s' if len(backups) != 1 else ''}.",
                170,
                170,
                175,
                use_color,
                dim=True,
            )
        )
    return renamed_audio


def prompt_for_all_caps_album_title_rename(
    audio_path: Path,
    suggested_filename: str,
    *,
    use_color: bool,
    input_reader=None,
) -> tuple[Path, list[str]]:
    """Offer the suggested title case, then an rn.bat-style editable rename."""
    print(f"            {music_filename(audio_path.name, use_color)}")
    print(
        "            "
        + rgb_text("💡 Suggested: ", 105, 175, 205, use_color, dim=True)
        + music_filename(suggested_filename, use_color)
    )
    prompt = (
        "            "
        + urgent_prompt_text(
            "New filename (press ENTER to use the suggested capitalization):",
            use_color,
        )
        + " "
    )
    try:
        entered = read_interactive_filename_edit(
            prompt,
            suggested_filename,
            input_reader=input_reader,
        ).strip()
    except EOFError:
        entered = ""
    reset_console_pager_after_user_input()
    if not entered:
        entered = suggested_filename
    if entered.strip('"') == audio_path.name:
        return audio_path, ["unchanged:filename"]
    renamed_audio, renamed, backups = rename_waveform_problem_family(
        audio_path,
        entered,
    )
    actions = [f"renamed:{renamed_audio}", f"renamed_family:{len(renamed)}"]
    actions.extend(f"backup:{backup}" for backup in backups)
    return renamed_audio, actions


def replaygain_decibels_from_factor(factor: float | None) -> float | None:
    """Convert a positive ReplayGain multiplier back to its tagged dB value."""
    if factor is None or not math.isfinite(float(factor)) or factor <= 0:
        return None
    return 20.0 * math.log10(float(factor))


def replaygain_needs_baking(
    metrics: WaveformMetrics | None,
    audio_path: Path,
    *,
    threshold_db: float = REPLAYGAIN_BAKE_THRESHOLD_DB,
) -> bool:
    """Return whether a supported file's tagged gain is outside ±threshold."""
    if metrics is None or audio_path.suffix.casefold() not in {".flac", ".mp3"}:
        return False
    tagged_db = replaygain_decibels_from_factor(metrics.replaygain_factor)
    return (
        tagged_db is not None
        and abs(tagged_db) > abs(float(threshold_db)) + 1e-9
    )


def safely_baked_replaygain_db(
    metrics: WaveformMetrics,
) -> tuple[float, float]:
    """Return requested and peak-protected ReplayGain adjustments in dB."""
    requested = replaygain_decibels_from_factor(metrics.replaygain_factor)
    if requested is None:
        raise RuntimeError("This audio file has no usable ReplayGain track gain")
    applied = requested
    peak_ratio = max(0.0, metrics.peak_volume_percentage / 100.0)
    if requested > 0 and peak_ratio > 0:
        # Retain 0.1% numerical headroom for codec/sample-format rounding.
        maximum_safe = 20.0 * math.log10(0.999 / peak_ratio)
        applied = min(requested, maximum_safe)
    return requested, applied


def _remove_flac_replaygain_tags(path: Path) -> None:
    """Remove now-stale FLAC ReplayGain fields before fresh analysis."""
    tagged = FLAC(path)
    for key in list(tagged.keys()):
        if str(key).casefold().startswith("replaygain_"):
            del tagged[key]
    tagged.save()


def file_sha256(path: Path) -> str:
    """Hash a potentially large media file without loading it all at once."""
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def replace_staged_media(
    staged: Path,
    destination: Path,
    *,
    use_color: bool,
) -> str:
    """Install staged media, falling back when Windows denies rename/delete.

    ``os.replace`` is preferred because it is atomic. Some Windows volumes
    permit writing a file but deny the delete/rename permission required by
    ``os.replace``. In that specific case, copy the already validated staged
    bytes over the destination, flush them, verify SHA-256, and recycle the
    staging file.
    """
    denied_error: OSError | None = None
    try:
        os.replace(staged, destination)
        return "atomic-replace"
    except OSError as atomic_error:
        access_denied = (
            isinstance(atomic_error, PermissionError)
            or getattr(atomic_error, "winerror", None) in {5, 32}
            or getattr(atomic_error, "errno", None) in {1, 13}
        )
        if not access_denied:
            raise
        denied_error = atomic_error

    try:
        with staged.open("rb") as source, destination.open("wb") as target:
            shutil.copyfileobj(source, target, length=1024 * 1024)
            target.flush()
            os.fsync(target.fileno())
    except Exception as copy_error:
        raise RuntimeError(
            "Windows denied atomic replacement, and the verified in-place "
            f"copy fallback also failed: {copy_error}"
        ) from denied_error

    if (
        destination.stat().st_size != staged.stat().st_size
        or file_sha256(destination) != file_sha256(staged)
    ):
        raise RuntimeError(
            "Windows denied atomic replacement, and SHA-256 verification of "
            "the in-place copy fallback failed"
        ) from denied_error

    try:
        recycle_path(staged)
        staging_note = "the staging file was sent to the Recycle Bin."
    except Exception as recycle_error:
        staging_note = (
            "the verified staging file was kept because Recycle Bin cleanup "
            f"failed ({type(recycle_error).__name__}: {recycle_error})."
        )
    cover_narration(
        "🛡️",
        "Windows denied atomic replacement; used a flushed, SHA-256-verified "
        f"in-place media write instead, and {staging_note}",
        use_color=use_color,
        color=(165, 185, 205),
        dim=True,
    )
    return "verified-copy-fallback"


def bake_replaygain_into_audio(
    audio_path: Path,
    metrics: WaveformMetrics,
    *,
    use_color: bool = True,
    stream_output: bool = True,
    ffmpeg_executable: str | None = None,
    metaflac_executable: str | None = None,
    metamp3_executable: str | None = None,
) -> tuple[Path, float]:
    """Bake track gain into FLAC/MP3 audio, then calculate fresh tags."""
    source = audio_path.resolve()
    requested_db, applied_db = safely_baked_replaygain_db(metrics)
    suffix = source.suffix.casefold()
    if suffix not in {".flac", ".mp3"}:
        raise RuntimeError(
            "Baked ReplayGain currently supports FLAC and MP3 audio"
        )
    limited = applied_db < requested_db - 0.01
    if stream_output:
        cover_narration(
            "🎚️",
            f"Tagged track gain requests {requested_db:+.2f} dB; applying "
            f"{applied_db:+.2f} dB"
            + (" after peak protection." if limited else "."),
            use_color=use_color,
            color=(105, 220, 155),
        )
    backup: Path | None = None
    if suffix == ".flac":
        ffmpeg = ffmpeg_executable or shutil.which("ffmpeg")
        metaflac = metaflac_executable or shutil.which("metaflac")
        if not ffmpeg or not metaflac:
            raise RuntimeError(
                "Baking FLAC ReplayGain requires ffmpeg and metaflac in PATH"
            )
        temporary = collision_safe_path(
            source.with_name(f".{source.name}.baking-replaygain.flac")
        )
        original = FLAC(source)
        bits_per_sample = int(
            getattr(
                getattr(original, "info", None),
                "bits_per_sample",
                16,
            )
            or 16
        )
        command = [
            str(ffmpeg),
            "-hide_banner",
            "-y",
            "-i",
            str(source),
            "-map",
            "0",
            "-map_metadata",
            "0",
            "-c",
            "copy",
            "-c:a",
            "flac",
            "-sample_fmt",
            "s16" if bits_per_sample <= 16 else "s32",
            "-filter:a",
            f"volume={applied_db:+.8f}dB",
            str(temporary),
        ]
        if stream_output:
            print(
            console_safe_text(
                f"        ▶ {subprocess.list2cmdline(command)}"
            ),
                flush=True,
            )
        options: dict[str, Any] = {"check": False}
        if not stream_output:
            options.update(
                {
                    "stdout": subprocess.PIPE,
                    "stderr": subprocess.STDOUT,
                    "text": True,
                    "errors": "replace",
                }
            )
        result = subprocess.run(command, **options)
        if result.returncode or not temporary.is_file():
            if temporary.exists():
                recycle_path(temporary)
            detail = str(getattr(result, "stdout", "") or "").strip()
            raise RuntimeError(
                "FFmpeg could not bake ReplayGain into this FLAC"
                + (f": {detail}" if detail else "")
            )
        try:
            normalized = FLAC(temporary)
            if not normalized.info or normalized.info.length <= 0:
                raise RuntimeError("Baked FLAC has no valid audio stream")
            _remove_flac_replaygain_tags(temporary)
            backup = backup_before_inline_replacement(source)
            replace_staged_media(
                temporary,
                source,
                use_color=use_color,
            )
            run_live_command(
                [str(metaflac), "--add-replay-gain", str(source)],
                cwd=source.parent,
                stream_output=stream_output,
            )
        except Exception:
            if temporary.exists():
                recycle_path(temporary)
            if backup is not None and backup.is_file():
                shutil.copy2(backup, source)
            raise
    else:
        ffmpeg = ffmpeg_executable or shutil.which("ffmpeg")
        metamp3 = metamp3_executable or shutil.which("metamp3")
        if not ffmpeg or not metamp3:
            raise RuntimeError(
                "Baking MP3 ReplayGain requires ffmpeg and metamp3 in PATH"
            )
        temporary = collision_safe_path(
            source.with_name(f".{source.name}.baking-replaygain.mp3")
        )
        command = [
            str(ffmpeg),
            "-hide_banner",
            "-y",
            "-i",
            str(source),
            "-map",
            "0",
            "-map_metadata",
            "0",
            "-c",
            "copy",
            "-c:a",
            "libmp3lame",
            "-q:a",
            "0",
            "-filter:a",
            f"volume={applied_db:+.8f}dB",
            "-id3v2_version",
            "3",
            str(temporary),
        ]
        if stream_output:
            print(
            console_safe_text(
                f"        ▶ {subprocess.list2cmdline(command)}"
            ),
            flush=True,
        )
        options = {"check": False}
        if not stream_output:
            options.update(
                {
                    "stdout": subprocess.PIPE,
                    "stderr": subprocess.STDOUT,
                    "text": True,
                    "errors": "replace",
                }
            )
        result = subprocess.run(command, **options)
        if result.returncode or not temporary.is_file():
            if temporary.exists():
                recycle_path(temporary)
            detail = str(getattr(result, "stdout", "") or "").strip()
            raise RuntimeError(
                "FFmpeg could not re-encode this MP3 with baked ReplayGain"
                + (f": {detail}" if detail else "")
            )
        try:
            encoded = MP3(temporary)
            if not encoded.info or encoded.info.length <= 0:
                raise RuntimeError("Re-encoded MP3 has no valid audio stream")
            if encoded.tags is not None:
                for frame in list(encoded.tags.getall("TXXX")):
                    if frame.desc.casefold().startswith("replaygain_"):
                        encoded.tags.delall(f"TXXX:{frame.desc}")
                encoded.save(v2_version=3)
            backup = backup_before_inline_replacement(source)
            replace_staged_media(
                temporary,
                source,
                use_color=use_color,
            )
            run_live_command(
                [str(metamp3), "--replay-gain", str(source)],
                cwd=source.parent,
                stream_output=stream_output,
            )
        except Exception:
            if temporary.exists():
                recycle_path(temporary)
            if backup is not None and backup.is_file():
                shutil.copy2(backup, source)
            raise
    if backup is None or not backup.is_file():
        raise RuntimeError("Baked ReplayGain backup verification failed")
    if waveform_replaygain_factor(source) is None:
        shutil.copy2(backup, source)
        raise RuntimeError(
            "Fresh ReplayGain tags were not verified; original was restored"
        )
    return backup, applied_db


def replaygain_bake_waveform_cache_paths(audio_path: Path) -> tuple[Path, Path]:
    """Return persistent-in-Recycle-Bin comparison paths for one audio file."""
    identity = hashlib.sha256(
        str(audio_path.resolve()).encode("utf-8", errors="replace")
    ).hexdigest()[:16]
    folder = waveform_staging_root() / "audit_music_batch-replaygain-bake-waveforms"
    return (
        folder / f"{identity}.before-replaygain-bake.jpg",
        folder / f"{identity}.after-replaygain-bake.jpg",
    )


def replaygain_waveform_pair_is_displayable(
    before_path: Path,
    after_path: Path,
) -> bool:
    """Require two distinct, verified JPEGs before advertising a pair."""
    if before_path == after_path:
        return False
    try:
        ensure_waveform_jpeg_ready(before_path)
        ensure_waveform_jpeg_ready(after_path)
    except Exception:
        return False
    return True


def replaygain_bake_candidates(audio_files: Iterable[Path]) -> list[Path]:
    """Find MP3/FLAC files whose tagged adjustment merits sample-data baking."""
    return [
        path
        for path in audio_files
        if (
            (tagged_db := replaygain_decibels_from_factor(
                waveform_replaygain_factor(path)
            ))
            is not None
            and abs(tagged_db) > REPLAYGAIN_BAKE_THRESHOLD_DB + 1e-9
            and path.suffix.casefold() in {".flac", ".mp3"}
        )
    ]


def status_bar_filename(path: Path, *, columns: int | None = None) -> str:
    """Return a one-line status filename using two dots, never an ellipsis."""
    name = path.name
    width = columns or visible_console_size().columns
    available = max(20, width - visible_cell_width("Processing file: ") - 2)
    if visible_cell_width(name) <= available:
        return name
    if available <= 2:
        return "." * available
    left_count = max(1, (available - 2) * 3 // 5)
    right_count = max(1, available - 2 - left_count)
    left = name[:left_count]
    right = name[-right_count:]
    while visible_cell_width(left + ".." + right) > available and right:
        right = right[1:]
    while visible_cell_width(left + ".." + right) > available and left:
        left = left[:-1]
    return left + ".." + right


def update_stable_bake_status(progress: Any | None, audio_path: Path) -> None:
    """Keep the current filename on the line directly above a tqdm bar."""
    if progress is None or not getattr(sys.stderr, "isatty", lambda: False)():
        return
    progress.clear()
    sys.stderr.write(
        f"\033[1A\rProcessing file: {status_bar_filename(audio_path)}\033[K\n"
    )
    sys.stderr.flush()
    progress.refresh()


def bake_replaygain_for_batch(
    audio_files: Iterable[Path],
    *,
    use_color: bool,
    key_reader=None,
    acceptable_silence_seconds: float = (
        BUILTIN_DEFAULT_SILENCE_THRESHOLD_SECONDS
    ),
) -> list[Path]:
    """Offer normal-audit ReplayGain baking and retain before/after gradients."""
    candidates = replaygain_bake_candidates(audio_files)
    if not candidates:
        return []
    threshold_text = f"±{REPLAYGAIN_BAKE_THRESHOLD_DB:g} dB"
    if not prompt_for_approval(
        f"Bake ReplayGain into the audio data for all {len(candidates)} file"
        f"{'s' if len(candidates) != 1 else ''} outside {threshold_text} now? "
        "Red-to-purple before and cyan-to-green after waveforms will be saved for a later "
        "waveform review.",
        False,
        use_color,
        key_reader=key_reader,
        indent="        ",
    ):
        return []

    baked: list[Path] = []
    cover_narration(
        "🔴",
        "Rendering and keeping red-to-purple before-waveforms before changing audio data.",
        use_color=use_color,
        color=(85, 190, 245),
        dim=True,
    )
    if getattr(sys.stderr, "isatty", lambda: False)():
        print("Processing file: preparing..", file=sys.stderr, flush=True)
    bake_progress_context = progress_bar(
        total=len(candidates),
        description="🎚 Baking ReplayGain",
        unit="files",
        bar_format=FILE_PROGRESS_FORMAT,
        enabled=bool(getattr(sys.stderr, "isatty", lambda: False)()),
    )
    bake_progress = bake_progress_context.__enter__()
    for audio_path in candidates:
        update_stable_bake_status(bake_progress, audio_path)
        before_path, after_path = replaygain_bake_waveform_cache_paths(audio_path)
        before_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            _before, _backup, before_metrics = generate_waveform_jpeg(
                audio_path,
                narrate=False,
                destination=before_path,
                acceptable_silence_seconds=acceptable_silence_seconds,
            )
            recolor_before_baked_waveform(before_path)
            backup, applied_db = bake_replaygain_into_audio(
                audio_path,
                before_metrics,
                use_color=use_color,
                stream_output=False,
            )
            _after, _backup, _after_metrics = generate_waveform_jpeg(
                audio_path,
                narrate=False,
                destination=after_path,
                acceptable_silence_seconds=acceptable_silence_seconds,
            )
            recolor_newly_baked_waveform(after_path)
            baked.append(audio_path)
        except Exception as exc:
            print_formatted_error(
                f"Could not bake ReplayGain into {audio_path.name}: {exc}",
                use_color,
            )
        finally:
            if bake_progress is not None:
                bake_progress.update(1)
    bake_progress_context.__exit__(None, None, None)
    return baked


def recolor_waveform_vertical_gradient(
    waveform_path: Path,
    center_color: tuple[int, int, int],
    outer_color: tuple[int, int, int],
    *,
    channels: int = 2,
) -> None:
    """Color each channel symmetrically from its center toward loud edges."""
    if Image is None:
        raise RuntimeError("Pillow is required to recolor waveform previews")
    with Image.open(waveform_path) as source:
        image = source.convert("RGB")
    plot_width = max(1, min(image.width, WAVEFORM_PLOT_WIDTH))
    plot = image.crop((0, 0, plot_width, image.height))
    mask = waveform_colored_mask(plot)
    channel_count = max(1, int(channels))
    rows = bytearray()
    for y in range(plot.height):
        local = ((y + 0.5) * channel_count / max(1, plot.height)) % 1.0
        distance = min(1.0, abs(local - 0.5) * 2.0)
        color = tuple(
            round(center + (outer - center) * distance)
            for center, outer in zip(center_color, outer_color)
        )
        rows.extend(bytes(color) * plot.width)
    gradient = Image.frombytes("RGB", plot.size, bytes(rows))
    plot.paste(gradient, mask=mask)
    image.paste(plot, (0, 0))
    image.save(waveform_path, format="JPEG", quality=94)


def recolor_before_baked_waveform(waveform_path: Path) -> None:
    """Use red centers and purple extremes for the original comparison."""
    recolor_waveform_vertical_gradient(
        waveform_path,
        (255, 65, 75),
        (175, 85, 255),
    )


def recolor_newly_baked_waveform(waveform_path: Path) -> None:
    """Use cyan-green centers and true-green extremes for baked audio."""
    recolor_waveform_vertical_gradient(
        waveform_path,
        (55, 235, 205),
        (70, 255, 105),
    )


def waveform_review_choice(
    waveform_path: Path,
    audio_path: Path,
    *,
    use_color: bool,
    key_reader=None,
    preview_renderer=None,
    comparison_preview_renderer=None,
    image_viewer=None,
    audio_editor=None,
    audio_previewer=None,
    problem_renamer=None,
    rename_input_reader=None,
    waveform_metrics: WaveformMetrics | None = None,
    comparison_active: bool = False,
    gain_baker=None,
    waveform_generator=None,
    waveform_recolorer=None,
    audio_retreater=None,
    excessive_silence: bool = False,
    longest_silence_seconds: float = 0.0,
    acceptable_silence_seconds: float = (
        BUILTIN_DEFAULT_SILENCE_THRESHOLD_SECONDS
    ),
) -> tuple[str, int, Path]:
    """Review one disposable waveform for problems, editing, or navigation."""
    renderer = preview_renderer or render_waveform_preview
    comparison_renderer = (
        comparison_preview_renderer
        or preview_renderer
        or render_waveform_comparison_preview
    )
    viewer = image_viewer or launch_irfanview
    editor = audio_editor or launch_audio_editor
    previewer = audio_previewer or launch_audio_preview
    renamer = problem_renamer or prompt_for_waveform_problem_rename
    baker = gain_baker or bake_replaygain_into_audio
    generator = waveform_generator or generate_waveform_jpeg
    recolorer = waveform_recolorer or recolor_newly_baked_waveform
    retreater = audio_retreater or retreat_edited_audio
    question = f"Does this waveform show a problem in {audio_path.name}?"
    edits_opened = 0
    current_metrics = waveform_metrics
    gain_baked = False
    while True:
        rendered_size = visible_console_size()
        reset_console_pager_after_user_input()
        active_renderer = comparison_renderer if comparison_active else renderer
        # Emit the preview without a trailing renderer-status line.  Sixel occupies
        # terminal pixel rows rather than normal text rows, so narration immediately
        # after it can visually overwrite the bottom of the waveform in Windows
        # Terminal.  The review header already communicates before/after context.
        active_renderer(waveform_path, use_color=use_color)
        if excessive_silence:
            cover_narration(
                "🔴",
                f"Longest silence is "
                f"{math.floor(max(0.0, longest_silence_seconds))}s, "
                f"exceeding the {acceptable_silence_seconds:g}s limit; "
                "ENTER defaults to opening this file in the audio editor.",
                use_color=use_color,
                color=(255, 75, 85),
            )
        requested_gain_db = (
            replaygain_decibels_from_factor(
                current_metrics.replaygain_factor
            )
            if current_metrics is not None
            else None
        )
        allow_bake_gain = replaygain_needs_baking(
            current_metrics,
            audio_path,
        ) and not gain_baked
        prompt_visible = False
        while True:
            prompt = urgent_prompt_text(
                question,
                use_color,
                faint_italic_spans=(audio_path.name,),
            )
            steady = prompt_with_option_legend(
                prompt,
                waveform_review_choices(
                    use_color,
                    default_edit=excessive_silence,
                    allow_bake_gain=allow_bake_gain,
                ),
                indent="            ",
            )
            interactive_terminal = bool(
                getattr(sys.stdout, "isatty", lambda: False)()
            )
            if not prompt_visible:
                print(
                    blinking_approval_prompt(
                        steady,
                        use_color and interactive_terminal,
                    ),
                    end="",
                    flush=True,
                )
                prompt_visible = True
            key = read_artwork_review_key(key_reader, rendered_size)
            if key == "\x03":
                raise KeyboardInterrupt
            lowered = key.casefold()
            if excessive_silence and key in {"", "\r", "\n"}:
                lowered = "e"
            if key == "__resize__":
                if interactive_terminal:
                    erase_wrapped_console_text(steady)
                else:
                    print()
                cover_narration(
                    "🔄",
                    "Console viewport changed; re-rendering at the live size.",
                    use_color=use_color,
                    color=(105, 145, 180),
                    dim=True,
                )
                break
            if lowered == "v":
                if interactive_terminal:
                    erase_wrapped_console_text(steady)
                else:
                    print()
                prompt_visible = False
                try:
                    opened_with = viewer(waveform_path)
                    cover_narration(
                        "🔎",
                        f"Opened the waveform image in "
                        f"{Path(opened_with).name}; return here to continue.",
                        use_color=use_color,
                        color=(150, 120, 205),
                        dim=True,
                    )
                except Exception as exc:
                    print_formatted_error(
                        f"Could not open the waveform image: {exc}",
                        use_color,
                    )
                continue
            if lowered == "p":
                if interactive_terminal:
                    erase_wrapped_console_text(steady)
                else:
                    print()
                prompt_visible = False
                try:
                    previewed_with = previewer(audio_path)
                    cover_narration(
                        "🔊",
                        f"Audio preview ended in {Path(previewed_with).name}; "
                        "returning to waveform review.",
                        use_color=use_color,
                        color=(95, 185, 225),
                        dim=True,
                    )
                except Exception as exc:
                    print_formatted_error(
                        f"Could not preview this audio file: {exc}",
                        use_color,
                    )
                continue
            if lowered == "e":
                if interactive_terminal:
                    erase_wrapped_console_text(steady)
                else:
                    print()
                prompt_visible = False
                try:
                    opened_with = editor(audio_path)
                    edits_opened += 1
                    cover_narration(
                        "🎛️",
                        f"Opened the audio in {Path(opened_with).name}.",
                        use_color=use_color,
                        color=(210, 155, 85),
                        dim=True,
                    )
                    retreater(
                        audio_path,
                        use_color=use_color,
                        key_reader=key_reader,
                    )
                    (
                        regenerated_waveform,
                        _regenerated_backup,
                        regenerated_metrics,
                    ) = generator(
                        audio_path,
                        narrate=True,
                        destination=waveform_path,
                        acceptable_silence_seconds=(
                            acceptable_silence_seconds
                        ),
                    )
                    waveform_path = regenerated_waveform
                    current_metrics = regenerated_metrics
                    excessive_silence = (
                        regenerated_metrics.longest_silence_seconds
                        > acceptable_silence_seconds
                    )
                    longest_silence_seconds = (
                        regenerated_metrics.longest_silence_seconds
                    )
                    cover_narration(
                        "🔄",
                        "Fresh waveform generated from the saved edit.",
                        use_color=use_color,
                        color=(95, 185, 225),
                        dim=True,
                    )
                except Exception as exc:
                    print_formatted_error(
                        f"Could not open an audio editor: {exc}",
                        use_color,
                    )
                break
            if lowered == "b" and allow_bake_gain and current_metrics is not None:
                if interactive_terminal:
                    erase_wrapped_console_text(steady)
                else:
                    print()
                prompt_visible = False
                requested_db, applied_db = safely_baked_replaygain_db(
                    current_metrics
                )
                protection = (
                    f"; peak protection limits the applied change to "
                    f"{applied_db:+.2f} dB"
                    if applied_db < requested_db - 0.01
                    else ""
                )
                method = (
                    "FLAC PCM amplitudes will change and be losslessly "
                    "re-encoded"
                    if audio_path.suffix.casefold() == ".flac"
                    else "the MP3 will be decoded and lossily re-encoded at "
                    "the highest LAME VBR quality"
                )
                if not prompt_for_approval(
                    f"Bake the tagged ReplayGain adjustment "
                    f"({requested_db:+.2f} dB{protection}) into this audio "
                    f"now? {method}; the original will be kept as a verified "
                    "backup and ReplayGain tags will then be recalculated.",
                    False,
                    use_color,
                    key_reader=key_reader,
                    indent="            ",
                ):
                    continue
                try:
                    before_bake_waveform = collision_safe_path(
                        waveform_path.with_name(
                            f"{waveform_path.stem}"
                            ".before-replaygain-bake"
                            f"{waveform_path.suffix}"
                        )
                    )
                    shutil.copy2(waveform_path, before_bake_waveform)
                    recolor_before_baked_waveform(before_bake_waveform)
                    backup, applied_db = baker(
                        audio_path,
                        current_metrics,
                        use_color=use_color,
                    )
                    (
                        regenerated_waveform,
                        _regenerated_backup,
                        regenerated_metrics,
                    ) = generator(
                        audio_path,
                        narrate=True,
                        destination=waveform_path,
                        acceptable_silence_seconds=(
                            acceptable_silence_seconds
                        ),
                    )
                    recolorer(regenerated_waveform)
                    current_metrics = regenerated_metrics
                    gain_baked = True
                    comparison_active = True
                    excessive_silence = (
                        regenerated_metrics.longest_silence_seconds
                        > acceptable_silence_seconds
                    )
                    longest_silence_seconds = (
                        regenerated_metrics.longest_silence_seconds
                    )
                    refreshed_db = replaygain_decibels_from_factor(
                        regenerated_metrics.replaygain_factor
                    )
                    cover_narration(
                        "💾",
                        f"Original kept as {backup.name}.",
                        use_color=use_color,
                        color=(145, 150, 155),
                        dim=True,
                    )
                    cover_narration(
                        "🔵",
                        "Before: original red-to-purple waveform; a ReplayGain-aware "
                        f"player applies {requested_db:+.2f} dB from its tag. "
                        "Comparison only — no response is needed.",
                        use_color=use_color,
                        color=(85, 190, 245),
                    )
                    reset_console_pager_after_user_input()
                    comparison_renderer(
                        before_bake_waveform,
                        use_color=use_color,
                    )
                    refreshed_text = (
                        f"{refreshed_db:+.2f} dB"
                        if refreshed_db is not None
                        else "unavailable"
                    )
                    cover_narration(
                        "🌱",
                        f"New waveform rendered in green after baking "
                        f"{applied_db:+.2f} dB into the samples; its fresh "
                        f"ReplayGain correction is {refreshed_text}.",
                        use_color=use_color,
                        color=(80, 255, 130),
                    )
                    cover_narration(
                        "✔️",
                        "Re-audit: changed audio, fresh ReplayGain tags, and "
                        "new waveform verified.",
                        use_color=use_color,
                        color=(95, 225, 130),
                    )
                except Exception as exc:
                    print_formatted_error(
                        f"Could not bake ReplayGain into this audio: {exc}",
                        use_color,
                    )
                break
            if lowered not in {"n", "y"}:
                invalid_key_beep()
                continue
            decision = "fine" if lowered == "n" else "problem"
            settled = (
                f"            {prompt} "
                f"{waveform_decision_answer(decision, use_color)}"
            )
            if interactive_terminal:
                erase_wrapped_console_text(steady)
                print(f"{settled}{ANSI['erase_to_eol']}")
            else:
                print(waveform_decision_answer(decision, use_color))
            reset_console_pager_after_user_input()
            if decision == "fine":
                return decision, edits_opened, audio_path
            if prompt_for_approval(
                "Want to edit this audio file now?",
                False,
                use_color,
                key_reader=key_reader,
                indent="            ",
            ):
                try:
                    opened_with = editor(audio_path)
                    edits_opened += 1
                    cover_narration(
                        "🎛️",
                        f"Opened the audio in {Path(opened_with).name}.",
                        use_color=use_color,
                        color=(210, 155, 85),
                        dim=True,
                    )
                    retreater(
                        audio_path,
                        use_color=use_color,
                        key_reader=key_reader,
                    )
                except Exception as exc:
                    print_formatted_error(
                        f"Could not open an audio editor: {exc}",
                        use_color,
                    )
            final_audio_path = audio_path
            if prompt_for_approval(
                "Want to rename this audio file to flag the problem?",
                False,
                use_color,
                key_reader=key_reader,
                indent="            ",
            ):
                try:
                    final_audio_path = renamer(
                        audio_path,
                        use_color=use_color,
                        input_reader=rename_input_reader,
                    )
                except Exception as exc:
                    print_formatted_error(
                        f"Could not rename the problem audio file: {exc}",
                        use_color,
                    )
            return decision, edits_opened, final_audio_path


def rejected_artwork_path(path: Path) -> Path:
    """Name a rejected download before sending it to the Recycle Bin."""
    return collision_safe_path(
        path.with_name(
            f"{path.stem}.rejected-by-username{path.suffix}"
        )
    )


def waveform_staging_root() -> Path:
    """Prefer C:\recycled for staging, then fall back to Windows %TEMP%."""
    recycled = Path(r"C:\recycled")
    if recycled.is_dir() and os.access(recycled, os.W_OK):
        return recycled
    return Path(tempfile.gettempdir())


def waveform_channel_count(audio_path: Path) -> int:
    """Read the channel count needed to draw every waveform separator."""
    if mutagen_file is None:
        return 1
    try:
        audio = mutagen_file(audio_path)
        channels = int(
            getattr(getattr(audio, "info", None), "channels", 0) or 0
        )
    except Exception:
        return 1
    return max(1, min(32, channels))


def waveform_frame_filters(
    audio_path: Path,
    plot_width: int = WAVEFORM_PLOT_WIDTH,
) -> str:
    """Frame only the waveform plot and divide its stacked channels."""
    line = "color=0x777777@0.60:t=fill"
    filters = [
        f"drawbox=x=0:y=0:w={int(plot_width)}:h=ih:"
        "color=0x777777@0.60:t=4"
    ]
    channels = waveform_channel_count(audio_path)
    filters.extend(
        f"drawbox=x=0:y=ih*{index}/{channels}-2:"
        f"w={int(plot_width)}:h=4:{line}"
        for index in range(1, channels)
    )
    return ",".join(filters)


def parse_waveform_peak_percentages(
    ffmpeg_output: str,
    channels: int,
) -> tuple[float, ...]:
    """Convert FFmpeg ``astats`` channel peaks from dBFS to percentages."""
    requested = max(1, int(channels))
    peaks_db: dict[int, float] = {}
    overall_db: float | None = None
    current_channel: int | None = None
    in_overall = False
    for raw_line in str(ffmpeg_output or "").splitlines():
        channel_match = re.search(r"\bChannel:\s*(\d+)\s*$", raw_line)
        if channel_match:
            current_channel = int(channel_match.group(1))
            in_overall = False
            continue
        if re.search(r"\bOverall\s*$", raw_line):
            current_channel = None
            in_overall = True
            continue
        peak_match = re.search(
            r"\bPeak level dB:\s*(-?inf|[-+]?\d+(?:\.\d+)?)\s*$",
            raw_line,
            flags=re.IGNORECASE,
        )
        if not peak_match:
            continue
        value_text = peak_match.group(1)
        value = (
            float("-inf")
            if value_text.casefold() == "-inf"
            else float(value_text)
        )
        if in_overall:
            overall_db = value
        elif current_channel is not None:
            peaks_db[current_channel] = value

    fallback = overall_db if overall_db is not None else float("-inf")
    percentages: list[float] = []
    for channel in range(1, requested + 1):
        decibels = peaks_db.get(channel, fallback)
        if not math.isfinite(decibels):
            percentage = 0.0
        else:
            percentage = 100.0 * math.pow(10.0, decibels / 20.0)
        percentages.append(max(0.0, min(100.0, percentage)))
    return tuple(percentages)


def dbfs_to_percentage(decibels: float | None) -> float:
    """Convert a finite dBFS amplitude into a clamped linear percentage."""
    if decibels is None or not math.isfinite(float(decibels)):
        return 0.0
    return max(
        0.0,
        min(100.0, 100.0 * math.pow(10.0, float(decibels) / 20.0)),
    )


def parse_waveform_average_volume_percentage(ffmpeg_output: str) -> float:
    """Read overall RMS level from FFmpeg astats as an average-volume percent."""
    in_overall = False
    overall_rms_db: float | None = None
    for raw_line in str(ffmpeg_output or "").splitlines():
        if re.search(r"\bOverall\s*$", raw_line):
            in_overall = True
            continue
        if re.search(r"\bChannel:\s*\d+\s*$", raw_line):
            in_overall = False
            continue
        if not in_overall:
            continue
        match = re.search(
            r"\bRMS level dB:\s*(-?inf|[-+]?\d+(?:\.\d+)?)\s*$",
            raw_line,
            flags=re.IGNORECASE,
        )
        if match:
            overall_rms_db = (
                float("-inf")
                if match.group(1).casefold() == "-inf"
                else float(match.group(1))
            )
    return dbfs_to_percentage(overall_rms_db)


def parse_waveform_silence_durations(
    ffmpeg_output: str,
) -> tuple[float, float]:
    """Return longest and total silence durations reported by silencedetect."""
    durations = [
        max(0.0, float(value))
        for value in re.findall(
            r"silence_duration:\s*(\d+(?:\.\d+)?)",
            str(ffmpeg_output or ""),
            flags=re.IGNORECASE,
        )
    ]
    if not durations:
        return 0.0, 0.0
    return max(durations), sum(durations)


def waveform_replaygain_factor(audio_path: Path) -> float | None:
    """Return the ReplayGain track-gain tag as a linear amplitude multiplier."""
    snapshot = BatchAudit(audio_path.parent).tag_snapshot(audio_path)
    values = snapshot.get("replaygain", {}).get("replaygain_track_gain", [])
    if not values:
        return None
    match = re.search(
        r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)",
        str(values[0]),
    )
    if not match:
        return None
    return math.pow(10.0, float(match.group(0)) / 20.0)


@dataclass(frozen=True)
class WaveformMetrics:
    """Audio measurements displayed in the unboxed right-side summary."""

    channel_peak_percentages: tuple[float, ...]
    peak_volume_percentage: float
    average_volume_percentage: float
    replaygain_factor: float | None
    longest_silence_seconds: float
    total_silence_seconds: float


def parse_waveform_metrics(
    ffmpeg_output: str,
    audio_path: Path,
    channels: int,
) -> WaveformMetrics:
    """Build all waveform summary measurements from one FFmpeg decode."""
    channel_peaks = parse_waveform_peak_percentages(
        ffmpeg_output,
        channels,
    )
    longest_silence, total_silence = parse_waveform_silence_durations(
        ffmpeg_output
    )
    return WaveformMetrics(
        channel_peak_percentages=channel_peaks,
        peak_volume_percentage=max(channel_peaks, default=0.0),
        average_volume_percentage=parse_waveform_average_volume_percentage(
            ffmpeg_output
        ),
        replaygain_factor=waveform_replaygain_factor(audio_path),
        longest_silence_seconds=longest_silence,
        total_silence_seconds=total_silence,
    )


def waveform_metric_lines(metrics: WaveformMetrics) -> tuple[str, ...]:
    """Format the compact center-right waveform and ReplayGain summary."""
    gain = (
        f"{metrics.replaygain_factor:.5f}"
        if metrics.replaygain_factor is not None
        else "n/a"
    )
    replaygain_db = replaygain_decibels_from_factor(
        metrics.replaygain_factor
    )
    replaygain = (
        f"{replaygain_db:+.2f} dB"
        if replaygain_db is not None
        else "n/a"
    )
    return (
        f"peak vol: {round(metrics.peak_volume_percentage)}%",
        f"avg vol: {round(metrics.average_volume_percentage)}%",
        f"ReplayGain: {replaygain}",
        f"gain: {gain}",
        f"silence: {math.floor(max(0.0, metrics.longest_silence_seconds))}s "
        "(longest)",
    )


def waveform_metric_value_colors(
    metrics: WaveformMetrics,
    acceptable_silence_seconds: float,
) -> tuple[tuple[int, int, int], ...]:
    """Color numeric values, reserving red for excessive continuous silence."""
    return (
        (205, 155, 255),
        (100, 220, 255),
        (115, 235, 165),
        (255, 165, 90),
        (
            (255, 75, 85)
            if metrics.longest_silence_seconds
            > float(acceptable_silence_seconds)
            else (255, 210, 90)
        ),
    )


def waveform_peak_label_font(channel_height: int):
    """Load a readable compact font for outer peak labels."""
    if ImageFont is None:
        raise RuntimeError("Pillow is required for waveform peak labels")
    size = max(12, min(26, int(channel_height) // 4))
    candidates = (
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\consola.ttf",
        "DejaVuSansMono.ttf",
    )
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except (OSError, ValueError):
            continue
    return ImageFont.load_default()


def waveform_metrics_font(lines: tuple[str, ...], max_width: int):
    """Choose the largest installed font that keeps every metric in the gutter."""
    if ImageFont is None:
        raise RuntimeError("Pillow is required for waveform metric labels")
    candidates = (
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\consola.ttf",
        "DejaVuSansMono.ttf",
    )
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1))) if ImageDraw and Image else None
    for size in range(26, 10, -1):
        for candidate in candidates:
            try:
                font = ImageFont.truetype(candidate, size)
            except (OSError, ValueError):
                continue
            if probe is None or all(
                probe.textbbox((0, 0), line, font=font)[2] <= max_width
                for line in lines
            ):
                return font
    return ImageFont.load_default()


def waveform_cyan_mask(region):
    """Return a strict mask containing only cyan waveform pixels."""
    if Image is None:
        raise RuntimeError("Pillow is required for waveform rendering")
    red, green, blue = region.split()
    return Image.frombytes(
        "L",
        region.size,
        bytes(
            (
                255
                if (
                    b >= 150
                    and g >= 120
                    and r <= 140
                    and g - r >= 50
                    and b - r >= 80
                )
                else 0
            )
            for r, g, b in zip(
                red.tobytes(),
                green.tobytes(),
                blue.tobytes(),
            )
        ),
    )


def waveform_colored_mask(region):
    """Return a mask for any saturated configured waveform-channel color."""
    if Image is None:
        raise RuntimeError("Pillow is required for waveform rendering")
    red, green, blue = region.split()
    return Image.frombytes(
        "L",
        region.size,
        bytes(
            (
                255
                if (
                    max(r, g, b) >= 110
                    and max(r, g, b) - min(r, g, b) >= 35
                )
                else 0
            )
            for r, g, b in zip(
                red.tobytes(),
                green.tobytes(),
                blue.tobytes(),
            )
        ),
    )


def waveform_channel_rgb(channel_index: int) -> tuple[int, int, int]:
    """Return the configured RGB plotting color for one channel."""
    encoded = WAVEFORM_CHANNEL_COLORS[
        channel_index % len(WAVEFORM_CHANNEL_COLORS)
    ]
    value = int(encoded.removeprefix("0x"), 16)
    return ((value >> 16) & 255, (value >> 8) & 255, value & 255)


def waveform_channel_mask(region, channel_index: int):
    """Mask one configured channel color, accepting old FFmpeg cyan fallback."""
    if Image is None:
        raise RuntimeError("Pillow is required for waveform rendering")
    expected = waveform_channel_rgb(channel_index)
    red, green, blue = region.split()
    mask = Image.frombytes(
        "L",
        region.size,
        bytes(
            (
                255
                if (
                    max(r, g, b) - min(r, g, b) >= 35
                    and sum(
                        abs(component - target)
                        for component, target in zip(
                            (r, g, b),
                            expected,
                        )
                    )
                    <= 220
                )
                else 0
            )
            for r, g, b in zip(
                red.tobytes(),
                green.tobytes(),
                blue.tobytes(),
            )
        ),
    )
    if mask.getbbox() is None and channel_index:
        # Some older FFmpeg builds reject the multicolor palette and the
        # generator deliberately retries every channel in cyan.
        return waveform_cyan_mask(region)
    return mask


def waveform_vertical_rainbow(size: tuple[int, int]):
    """Create one ROYGBIV fill, repeated identically for every channel."""
    if Image is None:
        raise RuntimeError("Pillow is required for waveform rendering")
    width, height = size
    height = max(1, int(height))
    rows = bytearray()
    for y in range(height):
        # HSV hue 0.00→0.78 gives red, orange, yellow, green, blue, indigo,
        # and violet without assigning separate colors to left/right channels.
        red, green, blue = colorsys.hsv_to_rgb(
            0.78 * y / max(1, height - 1),
            0.72,
            1.0,
        )
        rows.extend(bytes((round(red * 255), round(green * 255), round(blue * 255))) * width)
    return Image.frombytes("RGB", (width, height), bytes(rows))


def waveform_axis_ceiling_percent(metrics: WaveformMetrics) -> float:
    """Choose a truthful 5% axis ceiling with a small visible headroom."""
    peak = max(
        [float(metrics.peak_volume_percentage)]
        + [float(value) for value in metrics.channel_peak_percentages]
    )
    peak = max(0.0, min(100.0, peak))
    if peak >= 100.0:
        return 100.0
    headroom = max(2.0, peak * 0.05)
    return float(
        max(5, min(100, math.ceil((peak + headroom) / 5.0) * 5))
    )


def scale_waveform_to_absolute_peaks(
    image,
    channel_peak_percentages: tuple[float, ...],
    *,
    plot_width: int = WAVEFORM_PLOT_WIDTH,
    axis_ceiling_percent: float = 100.0,
) -> None:
    """Scale normalized waves against the explicitly labeled amplitude axis."""
    if Image is None:
        raise RuntimeError("Pillow is required for waveform rendering")
    channels = max(1, len(channel_peak_percentages))
    width = max(1, min(image.width, int(plot_width)) - 8)
    ceiling = max(0.1, min(100.0, float(axis_ceiling_percent)))
    for channel, peak in enumerate(channel_peak_percentages):
        top = round(image.height * channel / channels) + 4
        bottom = round(image.height * (channel + 1) / channels) - 4
        height = max(1, bottom - top)
        region = image.crop((4, top, 4 + width, bottom))
        mask = waveform_channel_mask(region, channel)
        region.paste((0, 0, 0), mask=mask)
        occupied_bounds = mask.getbbox()
        if occupied_bounds is None:
            image.paste(region, (4, top))
            continue
        target_height = max(
            1,
            min(
                height,
                round(height * max(0.0, min(ceiling, peak)) / ceiling),
            ),
        )
        # FFmpeg normalizes showwavespic independently and can leave a large
        # amount of black space above/below its actual envelope. Resizing that
        # whole channel canvas merely scales the empty space and leaves the
        # waveform visibly much shorter than its measured peak. Crop to the
        # occupied envelope first, then map that envelope to the truthful
        # peak-to-peak height represented by the labeled axis.
        occupied_mask = mask.crop(
            (0, occupied_bounds[1], width, occupied_bounds[3])
        )
        resized = occupied_mask.resize(
            (width, target_height),
            resample=getattr(Image, "Resampling", Image).LANCZOS,
        )
        absolute_mask = Image.new("L", (width, height), 0)
        absolute_mask.paste(resized, (0, (height - target_height) // 2))
        region.paste(
            waveform_vertical_rainbow(region.size),
            mask=absolute_mask,
        )
        image.paste(region, (4, top))


def emphasize_waveform_peak_visibility(
    image,
    *,
    plot_width: int = WAVEFORM_PLOT_WIDTH,
    channel_count: int = 1,
) -> None:
    """Make isolated true peaks visible without changing their amplitude.

    FFmpeg can legitimately draw a one-column peak in a several-thousand-pixel
    waveform.  That peak nearly disappears when the JPEG is scaled to a
    terminal cell grid, so expand only the cyan waveform mask by two pixels in
    each direction.  This preserves the peak's vertical position while making
    it survive JPEG and Sixel/ANSI downscaling.
    """
    if Image is None or ImageFilter is None:
        raise RuntimeError("Pillow is required for waveform peak emphasis")
    channels = max(1, int(channel_count))
    interior_width = max(1, min(image.width, int(plot_width)) - 4)
    # Work on each occupied channel band separately so its own configured
    # color is preserved; stop when a band contains no waveform pixels.
    for channel in range(channels):
        top = round(image.height * channel / channels) + 2
        bottom = round(image.height * (channel + 1) / channels) - 2
        if bottom <= top:
            continue
        region = image.crop((2, top, 2 + interior_width, bottom))
        channel_mask = waveform_colored_mask(region)
        if channel_mask.getbbox() is None:
            continue
        expanded = channel_mask.filter(ImageFilter.MaxFilter(5))
        color = waveform_vertical_rainbow(region.size)
        region.paste(color, mask=expanded)
        image.paste(region, (2, top))


def annotate_waveform_peak_guides(
    waveform_path: Path,
    metrics: WaveformMetrics,
    *,
    plot_width: int = WAVEFORM_PLOT_WIDTH,
    acceptable_silence_seconds: float = (
        BUILTIN_DEFAULT_SILENCE_THRESHOLD_SECONDS
    ),
) -> None:
    """Draw outer peak ticks plus an unboxed center-right metric summary."""
    if Image is None or ImageDraw is None:
        raise RuntimeError("Pillow is required for waveform peak labels")
    channels = max(1, len(metrics.channel_peak_percentages))
    with Image.open(waveform_path) as source:
        image = source.convert("RGB")
    if image.width <= plot_width + 20:
        raise RuntimeError(
            "Waveform preview has no room for its peak-label gutter"
        )
    axis_ceiling = waveform_axis_ceiling_percent(metrics)
    draw = ImageDraw.Draw(image)
    scale_waveform_to_absolute_peaks(
        image,
        metrics.channel_peak_percentages,
        plot_width=plot_width,
        axis_ceiling_percent=axis_ceiling,
    )
    emphasize_waveform_peak_visibility(
        image,
        plot_width=plot_width,
        channel_count=channels,
    )
    draw = ImageDraw.Draw(image)
    axis_x = max(4, min(image.width - 20, int(plot_width) - 1))
    channel_height = image.height / channels
    font = waveform_peak_label_font(round(channel_height))
    axis_color = (125, 125, 130)
    guide_color = (150, 150, 155)
    text_color = (205, 210, 215)
    draw.line(
        (axis_x, 3, axis_x, image.height - 4),
        fill=axis_color,
        width=3,
    )

    rounded = int(round(axis_ceiling))
    channel_height = image.height / channels
    usable_half_height = max(1, round(channel_height / 2) - 8)
    upper_y = round(channel_height / 2) - usable_half_height
    lower_y = round(image.height - channel_height / 2) + usable_half_height
    tick_start = max(0, axis_x - 36)
    tick_end = min(image.width - 1, axis_x + 14)
    text_x = min(image.width - 1, axis_x + 20)

    for y, label in (
        (upper_y, f"+{rounded}%"),
        (lower_y, f"-{rounded}%"),
    ):
        draw.line(
            (tick_start, y, tick_end, y),
            fill=guide_color,
            width=3,
        )
        box = draw.textbbox((0, 0), label, font=font)
        text_height = box[3] - box[1]
        label_y = max(
            2,
            min(image.height - text_height - 2, y - text_height // 2),
        )
        draw.text(
            (text_x, label_y),
            label,
            font=font,
            fill=text_color,
        )

    metric_lines = waveform_metric_lines(metrics)
    metric_x = axis_x + 20
    max_metric_width = max(20, image.width - metric_x - 8)
    metric_font = waveform_metrics_font(metric_lines, max_metric_width)
    boxes = [
        draw.textbbox((0, 0), line, font=metric_font)
        for line in metric_lines
    ]
    line_height = max(box[3] - box[1] for box in boxes) + 7
    block_height = line_height * len(metric_lines)
    metric_y = max(5, (image.height - block_height) // 2)
    draw.rectangle(
        (
            axis_x + 5,
            metric_y - 5,
            image.width - 1,
            metric_y + block_height + 5,
        ),
        fill=(0, 0, 0),
    )
    metric_value_colors = waveform_metric_value_colors(
        metrics,
        acceptable_silence_seconds,
    )
    for index, (line, value_color) in enumerate(
        zip(metric_lines, metric_value_colors)
    ):
        label, value = line.split(": ", 1)
        label_text = f"{label}: "
        y = metric_y + index * line_height
        draw.text(
            (metric_x, y),
            label_text,
            font=metric_font,
            fill=text_color,
        )
        label_width = draw.textlength(label_text, font=metric_font)
        draw.text(
            (metric_x + label_width, y),
            value,
            font=metric_font,
            fill=value_color,
        )
    image.save(waveform_path, format="JPEG", quality=94)


def ensure_waveform_jpeg_ready(path: Path) -> tuple[int, int]:
    """Verify a waveform JPEG is closed, decodable, and ready for Chafa/Sixel.

    This deliberately uses successful decode/verify rather than an arbitrary
    sleep.  Returning only after two independent Pillow opens also guarantees
    that no producer-side image handle is required by the preview renderer.
    """
    target = Path(path)
    if not target.is_file():
        raise FileNotFoundError(target)
    stat_result = target.stat()
    if stat_result.st_size <= 0 or image_mime(target) != "image/jpeg":
        raise RuntimeError(f"Waveform JPEG is not display-ready: {target}")
    if Image is not None:
        with Image.open(target) as probe:
            probe.verify()
        with Image.open(target) as probe:
            probe.load()
            if probe.width <= 0 or probe.height <= 0:
                raise RuntimeError(
                    f"Waveform JPEG has invalid dimensions: {target}"
                )
    confirmed = target.stat()
    if confirmed.st_size != stat_result.st_size:
        raise RuntimeError(
            f"Waveform JPEG changed during readiness verification: {target}"
        )
    return confirmed.st_size, confirmed.st_mtime_ns


def generate_waveform_jpeg(
    audio_path: Path,
    *,
    ffmpeg_executable: str | None = None,
    narrate: bool = True,
    destination: Path | None = None,
    acceptable_silence_seconds: float = (
        BUILTIN_DEFAULT_SILENCE_THRESHOLD_SECONDS
    ),
    cancel_event: threading.Event | None = None,
) -> tuple[Path, Path | None, WaveformMetrics]:
    """Generate and verify one disposable high-resolution waveform JPEG."""
    ffmpeg = ffmpeg_executable or shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError(
            "--review-waveforms requires ffmpeg in PATH"
        )
    target = destination or collision_safe_path(
        waveform_staging_root()
        / (
            "audit_music_batch-waveform-"
            f"{hashlib.sha256(str(audio_path).encode()).hexdigest()[:12]}"
            ".jpg"
        )
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = collision_safe_path(
        target.with_name(f".{target.name}.generating.jpg")
    )
    channels = waveform_channel_count(audio_path)
    waveform_colors = "|".join(
        WAVEFORM_CHANNEL_COLORS[index % len(WAVEFORM_CHANNEL_COLORS)]
        for index in range(channels)
    )
    waveform_filters = (
        "[0:a]asplit=3[waveform_audio][peak_audio][silence_audio];"
        "[waveform_audio]"
        f"showwavespic=s={WAVEFORM_PLOT_WIDTH}x{WAVEFORM_JPEG_HEIGHT}:"
        f"split_channels=1:colors={waveform_colors}:"
        "draw=full:scale=lin,"
        f"pad={WAVEFORM_JPEG_WIDTH}:{WAVEFORM_JPEG_HEIGHT}:0:0:black,"
        f"{waveform_frame_filters(audio_path)}[waveform_picture];"
        "[peak_audio]astats=metadata=0:reset=0,anullsink;"
        "[silence_audio]"
        f"silencedetect=noise={SILENCE_DETECT_NOISE_DB}dB:"
        f"d={WAVEFORM_SILENCE_MIN_SECONDS:g},anullsink"
    )
    command = [
        str(ffmpeg),
        "-hide_banner",
        "-nostats",
        "-loglevel",
        "info",
        "-y",
        "-i",
        str(audio_path),
        "-filter_complex",
        waveform_filters,
        "-map",
        "[waveform_picture]",
        "-frames:v",
        "1",
        "-q:v",
        "2",
        str(temporary),
    ]
    if narrate:
        print(
            console_safe_text(
                f"            ▶ Generating {WAVEFORM_JPEG_WIDTH}×"
                f"{WAVEFORM_JPEG_HEIGHT} waveform JPEG with ffmpeg."
            ),
            flush=True,
        )
    def run_waveform_command(arguments: list[str]):
        if cancel_event is None:
            return subprocess.run(
                arguments,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                errors="replace",
                check=False,
            )
        process = subprocess.Popen(
            arguments,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            errors="replace",
        )
        while True:
            try:
                stdout, _stderr = process.communicate(timeout=0.10)
                return subprocess.CompletedProcess(
                    arguments, process.returncode, stdout=stdout, stderr=None
                )
            except subprocess.TimeoutExpired:
                if not cancel_event.is_set():
                    continue
                process.terminate()
                try:
                    stdout, _stderr = process.communicate(timeout=1.0)
                except subprocess.TimeoutExpired:
                    process.kill()
                    stdout, _stderr = process.communicate()
                if temporary.exists():
                    recycle_path(temporary)
                raise RuntimeError("waveform rendering cancelled")

    result = run_waveform_command(command)
    if (
        (result.returncode or not temporary.is_file())
        and waveform_colors != WAVEFORM_CHANNEL_COLORS[0]
    ):
        # Older FFmpeg builds occasionally reject a multi-colour showwavespic
        # palette for particular MP3 layouts.  Preserve waveform review by
        # retrying the established single-cyan filter rather than failing the
        # whole background queue.
        if temporary.exists():
            recycle_path(temporary)
        fallback_filters = waveform_filters.replace(
            f"colors={waveform_colors}",
            f"colors={WAVEFORM_CHANNEL_COLORS[0]}",
            1,
        )
        fallback_command = list(command)
        fallback_command[
            fallback_command.index("-filter_complex") + 1
        ] = fallback_filters
        if narrate:
            print(
                console_safe_text(
                    "            ⚠️ Retrying waveform render with the "
                    "compatible single-colour filter."
                ),
                flush=True,
            )
        result = run_waveform_command(fallback_command)
    if result.returncode or not temporary.is_file():
        if temporary.exists():
            recycle_path(temporary)
        output_lines = [
            line.strip()
            for line in str(result.stdout or "").splitlines()
            if line.strip()
        ]
        # FFmpeg emits all container metadata (including full lyric tags) at
        # info level before the actual failure.  Only its short final tail is
        # useful in an interactive terminal.
        detail = "\n".join(output_lines[-12:])
        raise RuntimeError(
            f"ffmpeg waveform generation failed"
            + (f": {detail}" if detail else "")
        )
    if image_mime(temporary) != "image/jpeg":
        recycle_path(temporary)
        raise RuntimeError("ffmpeg did not generate a valid JPEG waveform")
    metrics = parse_waveform_metrics(
        result.stdout,
        audio_path,
        channels,
    )
    annotate_waveform_peak_guides(
        temporary,
        metrics,
        acceptable_silence_seconds=acceptable_silence_seconds,
    )
    if target.exists():
        os.replace(temporary, target)
    else:
        temporary.rename(target)
    try:
        ensure_waveform_jpeg_ready(target)
    except Exception as exc:
        raise RuntimeError(
            f"Waveform JPEG verification failed after staging: {target}: {exc}"
        ) from exc
    return target, None, metrics


def waveform_approval_database_path() -> Path:
    """Return the persistent per-user waveform-review database location."""
    local_app_data = os.environ.get("LOCALAPPDATA", "").strip()
    base = (
        Path(local_app_data)
        if local_app_data
        else Path.home() / "AppData" / "Local"
    )
    return (
        base
        / "audit_music_batch"
        / WAVEFORM_APPROVAL_DATABASE_FILENAME
    )


class WaveformApprovalStore:
    """Persist unchanged audio files that a user has visually marked fine."""

    def __init__(self, database_path: Path | None = None) -> None:
        self.path = Path(
            database_path or waveform_approval_database_path()
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS waveform_approvals (
                    path TEXT PRIMARY KEY,
                    size_bytes INTEGER NOT NULL,
                    modified_ns INTEGER NOT NULL,
                    approved_at TEXT NOT NULL
                )
                """
            )

    @staticmethod
    def _key(path: Path) -> str:
        return os.path.normcase(str(path.resolve(strict=False)))

    @staticmethod
    def _signature(path: Path) -> tuple[int, int]:
        status = path.stat()
        return int(status.st_size), int(status.st_mtime_ns)

    def is_approved(self, path: Path) -> bool:
        """Return true only when the stored file still has the same identity."""
        try:
            size_bytes, modified_ns = self._signature(path)
        except OSError:
            return False
        key = self._key(path)
        with sqlite3.connect(self.path) as connection:
            row = connection.execute(
                """
                SELECT size_bytes, modified_ns
                FROM waveform_approvals
                WHERE path = ?
                """,
                (key,),
            ).fetchone()
            if row and tuple(map(int, row)) == (size_bytes, modified_ns):
                return True
            if row:
                connection.execute(
                    "DELETE FROM waveform_approvals WHERE path = ?",
                    (key,),
                )
        return False

    def approve(self, path: Path) -> None:
        """Record a successful fine decision after all possible edits."""
        size_bytes, modified_ns = self._signature(path)
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """
                INSERT INTO waveform_approvals
                    (path, size_bytes, modified_ns, approved_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    size_bytes = excluded.size_bytes,
                    modified_ns = excluded.modified_ns,
                    approved_at = excluded.approved_at
                """,
                (
                    self._key(path),
                    size_bytes,
                    modified_ns,
                    datetime.now().astimezone().isoformat(timespec="seconds"),
                ),
            )

    def prune_if_oversized(
        self,
        max_bytes: int = WAVEFORM_APPROVAL_DATABASE_MAX_BYTES,
    ) -> int:
        """When oversized, remove vanished paths and compact the database."""
        try:
            if self.path.stat().st_size <= int(max_bytes):
                return 0
        except OSError:
            return 0
        with sqlite3.connect(self.path) as connection:
            rows = connection.execute(
                "SELECT path FROM waveform_approvals"
            ).fetchall()
            vanished = [
                str(stored_path)
                for (stored_path,) in rows
                if not Path(str(stored_path)).exists()
            ]
            connection.executemany(
                "DELETE FROM waveform_approvals WHERE path = ?",
                ((stored_path,) for stored_path in vanished),
            )
        with sqlite3.connect(self.path) as connection:
            connection.execute("VACUUM")
        return len(vanished)


def prioritized_waveform_render_futures(
    audio_files: list[Path],
    executor: ThreadPoolExecutor,
    staging_folder: Path,
    *,
    acceptable_silence_seconds: float,
    first_ready_callback: Callable[[
        Path, tuple[Path, Path | None, WaveformMetrics]
    ], None] | None = None,
    prestarted_first: tuple[Path, Future] | None = None,
) -> tuple[dict[Path, Future], dict[Path, tuple[Path, Path | None, WaveformMetrics]]]:
    """Render #1 to completion before the remaining background jobs start."""
    futures: dict[Path, Future] = {}
    rendered_results: dict[Path, tuple[Path, Path | None, WaveformMetrics]] = {}

    def submit(item_index: int, upcoming: Path) -> Future:
        staged_name = (
            f"{item_index:06d}-"
            f"{hashlib.sha256(str(upcoming).encode()).hexdigest()[:12]}"
            ".waveform.jpg"
        )
        future = executor.submit(
            generate_waveform_jpeg,
            upcoming,
            narrate=False,
            destination=staging_folder / staged_name,
            acceptable_silence_seconds=acceptable_silence_seconds,
        )
        futures[upcoming] = future
        return future

    if audio_files:
        first_audio = audio_files[0]
        if prestarted_first is not None and prestarted_first[0] == first_audio:
            first_future = prestarted_first[1]
            futures[first_audio] = first_future
        else:
            first_future = submit(1, first_audio)
        # This blocking result is deliberate: no second ffmpeg render is even
        # submitted until the first visible waveform is complete.
        rendered_results[first_audio] = first_future.result()
        if first_ready_callback is not None:
            # Finish the first *displayable* preview before background ffmpeg
            # jobs are allowed to compete for CPU/disk.
            first_ready_callback(first_audio, rendered_results[first_audio])
        for item_index, upcoming in enumerate(audio_files[1:], start=2):
            submit(item_index, upcoming)
    return futures, rendered_results


def review_waveforms(
    root: Path,
    *,
    include_archives: bool = False,
    use_color: bool = True,
    interactive: bool = True,
    key_reader=None,
    preview_renderer=None,
    image_viewer=None,
    audio_editor=None,
    audio_previewer=None,
    workers: int = 8,
    silence_threshold_seconds: float | None = None,
    approval_database_path: Path | None = None,
    force_all: bool = False,
    prestarted_waveform: tuple[Path, Future] | None = None,
) -> dict[str, Any]:
    """Review disposable waveform previews for audible-file warning signs."""
    if not interactive:
        raise RuntimeError(
            "--review-waveforms requires interactive review; "
            "remove --no-interactive"
        )
    audit = BatchAudit(root, include_archives=include_archives)
    audit.collect_files()
    all_audio_files = audit.audio_files
    approval_store = WaveformApprovalStore(approval_database_path)
    pruned_approvals = approval_store.prune_if_oversized()
    previously_approved = [
        path for path in all_audio_files if approval_store.is_approved(path)
    ]
    approved_keys = {
        WaveformApprovalStore._key(path) for path in previously_approved
    }
    audio_files = (
        list(all_audio_files)
        if force_all
        else [
            path
            for path in all_audio_files
            if WaveformApprovalStore._key(path) not in approved_keys
        ]
    )
    if force_all:
        previously_approved = []
    elif not audio_files and all_audio_files:
        # Direct --review-waveforms should offer the same escape hatch as the
        # post-audit offer when the approval database would otherwise queue 0.
        if prompt_force_all_waveform_review(
            len(all_audio_files),
            use_color=use_color,
            key_reader=key_reader,
        ):
            force_all = True
            audio_files = list(all_audio_files)
            previously_approved = []
    acceptable_silence_seconds = (
        float(silence_threshold_seconds)
        if silence_threshold_seconds is not None
        else load_behavior_defaults().silence_threshold_seconds
    )
    # Give the large review heading breathing room from the audit summary.
    for _ in range(3):
        print()
    print(
        "\n".join(
            double_height_gradient_section(
                "Waveform review",
                use_color,
                ((95, 220, 255), (255, 105, 210)),
            )
        )
    )
    print()
    print(
        f"        🎚️ {len(audio_files)} audio "
        f"file{'s' if len(audio_files) != 1 else ''} queued for waveform review."
    )
    if previously_approved:
        print(
            rgb_text(
                f"        ✅ {len(previously_approved)} unchanged, previously "
                "approved "
                f"file{'s' if len(previously_approved) != 1 else ''} skipped.",
                105,
                185,
                135,
                use_color,
                dim=True,
            )
        )
    if pruned_approvals:
        print(
            rgb_text(
                f"        🧹 Pruned {pruned_approvals} vanished file "
                f"reference{'s' if pruned_approvals != 1 else ''} from the "
                "oversized waveform approval database.",
                145,
                155,
                170,
                use_color,
                dim=True,
            )
        )
    print(
        rgb_text(
            "        🔍 Inspect for long silence, clipped/flat peaks, "
            "dropouts, channel imbalance, or other suspicious shapes.",
            155,
            170,
            185,
            use_color,
            dim=True,
        )
    )
    discovered_editor = audio_editor or (
        launch_audio_editor if audio_editor_executable() is not None else None
    )
    if discovered_editor is None:
        print(
            rgb_text(
                "        ⚠️ E=Edit audio is unavailable; set "
                "AUDIO_EDITOR_EXECUTABLE in the script's USER CONFIGURATION.",
                225,
                170,
                75,
                use_color,
                dim=True,
            )
        )
    fine: list[str] = []
    problems: list[dict[str, str]] = []
    edited: list[str] = []
    failed: list[dict[str, str]] = []
    worker_count = max(1, min(int(workers), 8))
    preview_lookahead = max(4, worker_count * 2)
    staging_folder = collision_safe_path(
        waveform_staging_root()
        / (
            "audit_music_batch-waveform-prerenders-"
            f"{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )
    )
    staging_folder.mkdir(parents=True)
    executor = ThreadPoolExecutor(
        max_workers=worker_count,
        thread_name_prefix="waveform",
    )
    before_bake_waveforms: dict[Path, Path] = {}
    folder_baked_audio: set[Path] = set()
    preview_executor: ThreadPoolExecutor | None = None
    prepared_futures: dict[Path, Future] = {}
    prepared_previews: dict[Path, PreparedArtworkPreview] = {}
    prepared_comparison_previews: dict[Path, PreparedArtworkPreview] = {}
    try:
        # Discover any persisted before/after comparison first so waveform #1
        # can have *both* display payloads ready before the worker fan-out.
        for path in audio_files:
            before_path, after_path = replaygain_bake_waveform_cache_paths(path)
            if replaygain_waveform_pair_is_displayable(
                before_path, after_path
            ):
                before_bake_waveforms[path] = before_path

        def prepare_first_waveform_before_fanout(
            first_audio: Path,
            first_result: tuple[Path, Path | None, WaveformMetrics],
        ) -> None:
            if preview_renderer is not None:
                return
            staged_path = first_result[0]
            ensure_waveform_jpeg_ready(staged_path)
            comparison_path = before_bake_waveforms.get(first_audio)
            comparison_active = comparison_path is not None
            prepared_previews[first_audio] = prepare_waveform_preview(
                staged_path,
                use_color=use_color,
                width_fraction=(
                    WAVEFORM_COMPARISON_WIDTH_FRACTION
                    if comparison_active
                    else WAVEFORM_REVIEW_WIDTH_FRACTION
                ),
                height_scale=(
                    WAVEFORM_COMPARISON_HEIGHT_SCALE
                    if comparison_active
                    else WAVEFORM_REVIEW_HEIGHT_SCALE
                ),
            )
            if comparison_path is not None:
                ensure_waveform_jpeg_ready(comparison_path)
                prepared_comparison_previews[first_audio] = prepare_waveform_preview(
                    comparison_path,
                    use_color=use_color,
                    width_fraction=WAVEFORM_COMPARISON_WIDTH_FRACTION,
                    height_scale=WAVEFORM_COMPARISON_HEIGHT_SCALE,
                )

        futures, rendered_results = prioritized_waveform_render_futures(
            audio_files,
            executor,
            staging_folder,
            acceptable_silence_seconds=acceptable_silence_seconds,
            first_ready_callback=prepare_first_waveform_before_fanout,
            prestarted_first=prestarted_waveform,
        )
        tagged_bake_candidates = replaygain_bake_candidates(audio_files)
        if tagged_bake_candidates:
            print()
            threshold_text = f"±{REPLAYGAIN_BAKE_THRESHOLD_DB:g} dB"
            if prompt_for_approval(
                f"Bake ReplayGain into the audio data for all "
                f"{len(tagged_bake_candidates)} file"
                f"{'s' if len(tagged_bake_candidates) != 1 else ''} outside "
                f"{threshold_text} before waveform review? Red-to-purple originals "
                "will be preserved for comparison; newly baked waveforms "
                "will be cyan-to-green.",
                False,
                use_color,
                key_reader=key_reader,
                indent="        ",
            ):
                cover_narration(
                    "🔴",
                    "Finishing and preserving the original red-to-purple waveform "
                    "previews before changing any audio data.",
                    use_color=use_color,
                    color=(85, 190, 245),
                    dim=True,
                )
                if getattr(sys.stderr, "isatty", lambda: False)():
                    print("Processing file: preparing..", file=sys.stderr, flush=True)
                bake_progress_context = progress_bar(
                    total=len(tagged_bake_candidates),
                    description="🎚️ Baking ReplayGain",
                    unit="files",
                    bar_format=FILE_PROGRESS_FORMAT,
                    enabled=bool(getattr(sys.stderr, "isatty", lambda: False)()),
                )
                bake_progress = bake_progress_context.__enter__()
                for candidate in tagged_bake_candidates:
                    update_stable_bake_status(bake_progress, candidate)
                    try:
                        old_result = futures[candidate].result()
                        rendered_results[candidate] = old_result
                        old_waveform, _old_backup, old_metrics = old_result
                        comparison = collision_safe_path(
                            old_waveform.with_name(
                                f"{old_waveform.stem}"
                                ".before-replaygain-bake"
                                f"{old_waveform.suffix}"
                            )
                        )
                        shutil.copy2(old_waveform, comparison)
                        recolor_before_baked_waveform(comparison)
                        backup, applied_db = bake_replaygain_into_audio(
                            candidate,
                            old_metrics,
                            use_color=use_color,
                            stream_output=False,
                        )
                        new_result = generate_waveform_jpeg(
                            candidate,
                            narrate=False,
                            destination=old_waveform,
                            acceptable_silence_seconds=(
                                acceptable_silence_seconds
                            ),
                        )
                        recolor_newly_baked_waveform(new_result[0])
                        rendered_results[candidate] = new_result
                        before_bake_waveforms[candidate] = comparison
                        folder_baked_audio.add(candidate)
                    except Exception as exc:
                        print_formatted_error(
                            f"Could not bake ReplayGain into "
                            f"{candidate.name}: {exc}",
                            use_color,
                        )
                    finally:
                        if bake_progress is not None:
                            bake_progress.update(1)
                bake_progress_context.__exit__(None, None, None)
        if preview_renderer is None and audio_files:
            # Do the first *display* preparation synchronously too. The first JPEG
            # was already rendered before the rest were submitted; encoding its
            # Sixel now prevents the background preview workers from delaying the
            # first thing the user can actually inspect.
            first_audio = audio_files[0]
            first_result = rendered_results.get(first_audio) or futures[first_audio].result()
            rendered_results[first_audio] = first_result
            ensure_waveform_jpeg_ready(first_result[0])
            first_comparison = before_bake_waveforms.get(first_audio)
            first_comparison_active = first_comparison is not None
            if first_audio not in prepared_previews:
                prepared_previews[first_audio] = prepare_waveform_preview(
                    first_result[0],
                    use_color=use_color,
                    width_fraction=(
                        WAVEFORM_COMPARISON_WIDTH_FRACTION
                        if first_comparison_active
                        else WAVEFORM_REVIEW_WIDTH_FRACTION
                    ),
                    height_scale=(
                        WAVEFORM_COMPARISON_HEIGHT_SCALE
                        if first_comparison_active
                        else WAVEFORM_REVIEW_HEIGHT_SCALE
                    ),
                )
            if first_comparison is not None:
                ensure_waveform_jpeg_ready(first_comparison)
                if first_audio not in prepared_comparison_previews:
                    prepared_comparison_previews[first_audio] = prepare_waveform_preview(
                        first_comparison,
                        use_color=use_color,
                        width_fraction=WAVEFORM_COMPARISON_WIDTH_FRACTION,
                        height_scale=WAVEFORM_COMPARISON_HEIGHT_SCALE,
                    )

            preview_executor = ThreadPoolExecutor(
                max_workers=max(1, min(4, worker_count)),
                thread_name_prefix="waveform-preview",
            )

            def prepare_after_render(
                audio_path: Path,
                render_future: Future,
            ) -> PreparedArtworkPreview:
                staged_path, _backup, _metrics = render_future.result()
                comparison_active = audio_path in before_bake_waveforms
                return prepare_waveform_preview(
                    staged_path,
                    use_color=use_color,
                    width_fraction=(
                        WAVEFORM_COMPARISON_WIDTH_FRACTION
                        if comparison_active
                        else WAVEFORM_REVIEW_WIDTH_FRACTION
                    ),
                    height_scale=(
                        WAVEFORM_COMPARISON_HEIGHT_SCALE
                        if comparison_active
                        else WAVEFORM_REVIEW_HEIGHT_SCALE
                    ),
                )

            def prepare_rendered_path(
                audio_path: Path, path: Path
            ) -> PreparedArtworkPreview:
                comparison_active = audio_path in before_bake_waveforms
                return prepare_waveform_preview(
                    path,
                    use_color=use_color,
                    width_fraction=(
                        WAVEFORM_COMPARISON_WIDTH_FRACTION
                        if comparison_active
                        else WAVEFORM_REVIEW_WIDTH_FRACTION
                    ),
                    height_scale=(
                        WAVEFORM_COMPARISON_HEIGHT_SCALE
                        if comparison_active
                        else WAVEFORM_REVIEW_HEIGHT_SCALE
                    ),
                )

            def schedule_preview(index_to_schedule: int) -> None:
                if (
                    preview_executor is None
                    or index_to_schedule >= len(audio_files)
                ):
                    return
                upcoming = audio_files[index_to_schedule]
                if upcoming in prepared_previews or upcoming in prepared_futures:
                    return
                if upcoming not in prepared_futures:
                    if upcoming in rendered_results:
                        prepared_futures[upcoming] = preview_executor.submit(
                            prepare_rendered_path,
                            upcoming,
                            rendered_results[upcoming][0],
                        )
                    else:
                        prepared_futures[upcoming] = preview_executor.submit(
                            prepare_after_render,
                            upcoming,
                            futures[upcoming],
                        )

            # Waveform #1 is intentionally prepared synchronously on the main
            # thread after JPEG readiness verification.  This avoids a Windows
            # Terminal/TCC first-frame race that could expose raw Sixel bytes.
            for lookahead_index in range(
                1, min(len(audio_files), preview_lookahead)
            ):
                schedule_preview(lookahead_index)
            print(
                rgb_text(
                    f"        ⚡ Waveform #1 rendered first with priority; "
                    f"pre-rendering the remainder with {worker_count} workers and "
                    f"keeping up to {preview_lookahead} display-ready previews ahead.",
                    105,
                    175,
                    220,
                    use_color,
                    dim=True,
                )
            )
        for index, audio_path in enumerate(audio_files, start=1):
            if preview_executor is not None:
                schedule_preview(index - 1 + preview_lookahead)
            comparison_waveform = before_bake_waveforms.get(audio_path)
            future = futures[audio_path]
            try:
                if audio_path in rendered_results:
                    (
                        staged_waveform,
                        _staging_backup,
                        waveform_metrics,
                    ) = rendered_results[audio_path]
                else:
                    (
                        staged_waveform,
                        _staging_backup,
                        waveform_metrics,
                    ) = wait_for_waveform_render(
                        future,
                        audio_path.name,
                        use_color=use_color,
                        leave_final_status=False,
                    )
                ensure_waveform_jpeg_ready(staged_waveform)
                comparison_active = comparison_waveform is not None
                excessive_silence_now = (
                    waveform_metrics.longest_silence_seconds
                    > acceptable_silence_seconds
                )
                allow_bake_gain_now = replaygain_needs_baking(
                    waveform_metrics, audio_path
                )
                viewport_state = windows_console_viewport_state()
                layout = waveform_review_layout_plan(
                    audio_path.name,
                    index=index,
                    total=len(audio_files),
                    comparison_active=comparison_active,
                    excessive_silence=excessive_silence_now,
                    allow_bake_gain=allow_bake_gain_now,
                    viewport_state=viewport_state,
                )
                ensure_waveform_review_vertical_room(layout)
                print()
                print(
                    waveform_review_header(
                        index,
                        len(audio_files),
                        comparison_active=comparison_active,
                        use_color=use_color,
                    )
                )
                print(
                    waveform_rendered_status(
                        audio_path.name,
                        use_color,
                        terminal_columns=layout.terminal_columns,
                    )
                )
                prepared_preview = prepared_previews.pop(audio_path, None)
                if prepared_preview is None:
                    prepared_future = prepared_futures.pop(
                        audio_path,
                        None,
                    )
                    prepared_preview = (
                        prepared_future.result()
                        if prepared_future is not None
                        else None
                    )
                prepared_used = False

                def queued_preview_renderer(
                    path: Path,
                    *,
                    use_color: bool,
                ) -> str:
                    nonlocal prepared_used
                    if (
                        not prepared_used
                        and prepared_preview is not None
                        and prepared_preview.geometry
                        == waveform_preview_geometry(
                            WAVEFORM_COMPARISON_WIDTH_FRACTION
                            if comparison_waveform is not None
                            else WAVEFORM_REVIEW_WIDTH_FRACTION,
                            height_rows=layout.graph_rows,
                        )
                    ):
                        prepared_used = True
                        return emit_prepared_artwork_preview(
                            prepared_preview
                        )
                    prepared_used = True
                    return emit_prepared_artwork_preview(
                        prepare_waveform_preview(
                            path,
                            use_color=use_color,
                            width_fraction=(
                                WAVEFORM_COMPARISON_WIDTH_FRACTION
                                if comparison_waveform is not None
                                else WAVEFORM_REVIEW_WIDTH_FRACTION
                            ),
                            height_rows=layout.graph_rows,
                        )
                    )

                prepared_comparison_sheet: PreparedArtworkPreview | None = None
                prepared_comparison_sheet_key: tuple[int, int, int, int] | None = None

                def queued_comparison_after_renderer(
                    path: Path,
                    *,
                    use_color: bool,
                ) -> str:
                    nonlocal prepared_comparison_sheet
                    nonlocal prepared_comparison_sheet_key
                    if comparison_waveform is None:
                        return queued_preview_renderer(path, use_color=use_color)
                    before_stat = comparison_waveform.stat()
                    after_stat = path.stat()
                    key = (
                        before_stat.st_size,
                        before_stat.st_mtime_ns,
                        after_stat.st_size,
                        after_stat.st_mtime_ns,
                    )
                    if prepared_comparison_sheet is None or key != prepared_comparison_sheet_key:
                        sheet_path = collision_safe_path(
                            staged_waveform.with_name(
                                f"{staged_waveform.stem}.before-after-contact-sheet.jpg"
                            )
                        )
                        create_waveform_comparison_contact_sheet(
                            comparison_waveform,
                            path,
                            sheet_path,
                        )
                        prepared_comparison_sheet = prepare_waveform_preview(
                            sheet_path,
                            use_color=use_color,
                            width_fraction=WAVEFORM_COMPARISON_WIDTH_FRACTION,
                            height_scale=WAVEFORM_COMPARISON_HEIGHT_SCALE,
                        )
                        prepared_comparison_sheet_key = key
                    return emit_prepared_artwork_preview(prepared_comparison_sheet)

                if comparison_waveform is not None:
                    reset_console_pager_after_user_input()
                    # Discard the obsolete separately prepared "before" frame.
                    # Built-in rendering now emits one physical contact sheet;
                    # custom renderers retain their historical two-call behavior.
                    prepared_comparison_previews.pop(audio_path, None)
                    if preview_renderer is not None:
                        preview_renderer(
                            comparison_waveform,
                            use_color=use_color,
                        )

                decision, edit_count, reviewed_audio_path = waveform_review_choice(
                    staged_waveform,
                    audio_path,
                    use_color=use_color,
                    key_reader=key_reader,
                    preview_renderer=(
                        preview_renderer or queued_preview_renderer
                    ),
                    comparison_preview_renderer=(
                        preview_renderer or queued_comparison_after_renderer
                    ),
                    comparison_active=(comparison_waveform is not None),
                    image_viewer=image_viewer,
                    audio_editor=discovered_editor,
                    audio_previewer=audio_previewer,
                    waveform_metrics=waveform_metrics,
                    excessive_silence=excessive_silence_now,
                    longest_silence_seconds=(
                        waveform_metrics.longest_silence_seconds
                    ),
                    acceptable_silence_seconds=acceptable_silence_seconds,
                )
                if edit_count:
                    edited.append(str(reviewed_audio_path))
                if decision == "fine":
                    fine.append(str(reviewed_audio_path))
                    approval_store.approve(reviewed_audio_path)
                    print(
                        colorize(
                            "            ✔️ Marked fine; continuing to the "
                            "next audio file.",
                            "green",
                            use_color,
                        )
                    )
                else:
                    problems.append(
                        {
                            "path": str(reviewed_audio_path),
                            "waveform": str(staged_waveform),
                            **(
                                {"renamed_from": str(audio_path)}
                                if reviewed_audio_path != audio_path
                                else {}
                            ),
                        }
                    )
                    print(
                        rgb_text(
                            "            ⚠️ Problem recorded in the waveform "
                            "review results.",
                            255,
                            180,
                            65,
                            use_color,
                        )
                    )
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
                failed.append({"path": str(audio_path), "error": error})
                print_formatted_error(
                    f"Waveform review failed for {audio_path.name}: {error}",
                    use_color,
                )
    finally:
        if preview_executor is not None:
            preview_executor.shutdown(
                wait=True,
                cancel_futures=True,
            )
        executor.shutdown(wait=True, cancel_futures=True)
    print()
    print(
        "\n".join(
            double_height_gradient_section(
                "Waveform review results",
                use_color,
                ((95, 220, 255), (255, 105, 210)),
            )
        )
    )
    print()
    print(
        f"        {len(fine)} newly approved, "
        f"{len(previously_approved)} previously approved, "
        f"{len(problems)} problem"
        f"{'s' if len(problems) != 1 else ''}, "
        f"{len(edited)} opened in an editor, {len(failed)} failed."
    )
    print(
        rgb_text(
            f"        🗂️ Disposable waveform previews remain in: "
            f"{staging_folder}",
            150,
            155,
            165,
            use_color,
            dim=True,
        )
    )
    return {
        "audio_files": len(all_audio_files),
        "queued": len(audio_files),
        "previously_approved": [
            str(path) for path in previously_approved
        ],
        "fine": fine,
        "problems": problems,
        "edited": edited,
        "failed": failed,
        "staging_folder": str(staging_folder),
        "approval_database": str(approval_store.path),
        "pruned_approvals": pruned_approvals,
    }


def waveform_review_header(
    index: int,
    total: int,
    *,
    comparison_active: bool,
    use_color: bool,
) -> str:
    """Render the per-item heading, including color-keyed before/after context."""
    base = f"        🎛️ Waveform {index}/{total}"
    if not comparison_active:
        return base + ":"
    if not use_color:
        return base + " (before, after):"
    white = (238, 238, 242)
    before = gradient_text(
        "before",
        True,
        ((255, 65, 75), (175, 85, 255)),
    )
    after = gradient_text(
        "after",
        True,
        ((55, 235, 205), (70, 255, 105)),
    )
    return (
        base
        + rgb_text(" (", *white, True)
        + before
        + rgb_text(", ", *white, True)
        + after
        + rgb_text("):", *white, True)
    )


def waveform_review_candidate_counts(
    root: Path,
    *,
    include_archives: bool = False,
    approval_database_path: Path | None = None,
) -> tuple[int, int, int]:
    """Return total, queued, and previously-approved waveform-review counts."""
    audit = BatchAudit(root, include_archives=include_archives)
    audit.collect_files()
    all_audio_files = audit.audio_files
    approval_store = WaveformApprovalStore(approval_database_path)
    approved = sum(
        1 for path in all_audio_files if approval_store.is_approved(path)
    )
    return len(all_audio_files), len(all_audio_files) - approved, approved


def waveform_review_candidates(
    root: Path,
    *,
    include_archives: bool = False,
    approval_database_path: Path | None = None,
) -> tuple[list[Path], list[Path]]:
    """Return all and unapproved audio paths for prompt-time pre-rendering."""
    audit = BatchAudit(root, include_archives=include_archives)
    audit.collect_files()
    all_audio_files = list(audit.audio_files)
    approval_store = WaveformApprovalStore(approval_database_path)
    queued = [
        path for path in all_audio_files if not approval_store.is_approved(path)
    ]
    return all_audio_files, queued


def prompt_force_all_waveform_review(
    total_audio: int,
    *,
    use_color: bool,
    key_reader=None,
    indent: str = "        ",
) -> bool:
    """Offer F=Force All when every eligible waveform is already approved."""
    reader = key_reader or read_single_key
    question = (
        f"Interactive waveform review has 0 files queued; all {total_audio} "
        f"eligible audio file{'s are' if total_audio != 1 else ' is'} already approved."
    )
    legend = "[F=Force All / N=No]"
    prompt = (
        f"{indent}{urgent_prompt_text(question, use_color)} "
        f"{rgb_text(legend, 255, 205, 70, use_color)}"
    )
    interactive_terminal = bool(
        getattr(sys.stdout, "isatty", lambda: False)()
    )
    print(
        blinking_approval_prompt(
            prompt, use_color and interactive_terminal
        ),
        end="",
        flush=True,
    )
    while True:
        key = reader()
        if key == "\x03":
            print()
            raise KeyboardInterrupt
        lowered = key.casefold()
        if lowered == "f":
            answer = True
            label = "Force All!"
            break
        if lowered == "n" or key in {"", "\r", "\n"}:
            answer = False
            label = "No!"
            break
        invalid_key_beep()
    if interactive_terminal:
        erase_wrapped_console_text(prompt)
    else:
        print()
    print(
        f"{indent}{urgent_prompt_text(question, use_color)} "
        + rgb_text(
            label,
            *( (120, 225, 255) if answer else (255, 105, 105) ),
            use_color,
        )
    )
    reset_console_pager_after_user_input()
    return answer


def prompt_post_audit_waveform_review(
    total_audio: int,
    queued: int,
    approved: int,
    *,
    use_color: bool,
    key_reader=None,
    indent: str = "        ",
) -> str:
    """Choose unreviewed-only, Force All, or skip; ENTER defaults to unreviewed."""
    reader = key_reader or read_single_key
    interactive_terminal = bool(
        getattr(sys.stdout, "isatty", lambda: False)()
    )

    if use_color and interactive_terminal:
        queued_display = (
            f"{ANSI['blink']}{ANSI['bold']}"
            f"\033[38;2;255;225;80m{queued}{ANSI['reset']}"
        )
    else:
        queued_display = str(queued)

    print(
        f"{indent}{total_audio} total waveforms ➜ "
        f"{queued_display} to review / {approved} already reviewed"
    )
    print(
        f'{indent}Press “Y” to review the {queued} un-reviewed '
        f"waveform{'s' if queued != 1 else ''}."
    )
    print(
        f'{indent}Press “F” to review all {total_audio} '
        f"waveform{'s' if total_audio != 1 else ''}."
    )

    question = "Run the interactive waveform review now?"
    legend = "[Y/n/f]"
    steady_prompt = (
        f"{indent}{urgent_prompt_text(question, use_color)} "
        f"{rgb_text(legend, 255, 205, 70, use_color)} "
    )
    print(steady_prompt, end="", flush=True)
    while True:
        key = reader()
        if key == "\x03":
            print()
            raise KeyboardInterrupt
        if key in {"", "\r", "\n"}:
            choice = "queued"
            break
        lowered = key.casefold()
        if lowered == "y":
            choice = "queued"
            break
        if lowered == "f":
            choice = "force_all"
            break
        if lowered == "n":
            choice = "no"
            break
        invalid_key_beep()

    if interactive_terminal:
        erase_wrapped_console_text(steady_prompt)
    else:
        print()
    settled = {
        "queued": (
            f"Yes — review {queued} un-reviewed "
            f"waveform{'s' if queued != 1 else ''}.",
            (95, 245, 135),
        ),
        "force_all": (
            f"Force All — review all {total_audio} "
            f"waveform{'s' if total_audio != 1 else ''}.",
            (120, 225, 255),
        ),
        "no": ("No.", (255, 105, 105)),
    }
    label, color = settled[choice]
    print(
        f"{indent}{urgent_prompt_text(question, use_color)} "
        + rgb_text(label, *color, use_color)
    )
    reset_console_pager_after_user_input()
    return choice


def offer_post_audit_waveform_review(
    root: Path,
    *,
    interactive: bool,
    suppressed: bool,
    include_archives: bool,
    use_color: bool,
    workers: int,
    silence_threshold_seconds: float | None = None,
    key_reader=None,
    reviewer=None,
) -> dict[str, Any] | None:
    """Offer a default-Yes three-way handoff to interactive waveform review."""
    if not interactive or suppressed:
        return None
    all_candidates, queued_candidates = waveform_review_candidates(
        root, include_archives=include_archives
    )
    total_audio = len(all_candidates)
    queued = len(queued_candidates)
    approved = total_audio - queued
    if total_audio == 0:
        print(
            rgb_text(
                "        🎚️ Interactive waveform review: 0 eligible audio files.",
                155, 170, 185, use_color, dim=True,
            )
        )
        return None

    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "Waveform review cannot start because ffmpeg is not in PATH"
        )
    speculative_executor: ThreadPoolExecutor | None = None
    speculative_cancel: threading.Event | None = None
    speculative: tuple[Path, Future] | None = None
    # Begin the first useful JPEG while the user is reading/answering the
    # review offer.  Keep this single-worker and cancellable: N terminates its
    # ffmpeg child instead of leaving invisible work running.
    speculative_candidates = queued_candidates or all_candidates
    if reviewer is None and speculative_candidates:
        speculative_cancel = threading.Event()
        speculative_executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="waveform-prompt"
        )
        speculative_audio = speculative_candidates[0]
        speculative_folder = collision_safe_path(
            waveform_staging_root()
            / (
                "audit_music_batch-waveform-prompt-"
                f"{datetime.now().strftime('%Y%m%d%H%M%S')}"
            )
        )
        speculative_folder.mkdir(parents=True)
        speculative_destination = speculative_folder / (
            "000001-"
            f"{hashlib.sha256(str(speculative_audio).encode()).hexdigest()[:12]}"
            ".waveform.jpg"
        )
        speculative = (
            speculative_audio,
            speculative_executor.submit(
                generate_waveform_jpeg,
                speculative_audio,
                narrate=False,
                destination=speculative_destination,
                acceptable_silence_seconds=(
                    float(silence_threshold_seconds)
                    if silence_threshold_seconds is not None
                    else load_behavior_defaults().silence_threshold_seconds
                ),
                cancel_event=speculative_cancel,
            ),
        )
    choice = prompt_post_audit_waveform_review(
        total_audio,
        queued,
        approved,
        use_color=use_color,
        key_reader=key_reader,
    )
    if choice == "no":
        if speculative_cancel is not None:
            speculative_cancel.set()
        if speculative_executor is not None:
            speculative_executor.shutdown(wait=True, cancel_futures=True)
        return None
    force_all = choice == "force_all"

    selected_candidates = all_candidates if force_all else queued_candidates
    if speculative is not None and (
        not selected_candidates or speculative[0] != selected_candidates[0]
    ):
        assert speculative_cancel is not None
        speculative_cancel.set()
        assert speculative_executor is not None
        speculative_executor.shutdown(wait=True, cancel_futures=True)
        speculative = None
        speculative_executor = None
    review = reviewer or review_waveforms
    try:
        review_kwargs = dict(
            include_archives=include_archives,
            use_color=use_color,
            interactive=True,
            key_reader=key_reader,
            workers=workers,
            silence_threshold_seconds=silence_threshold_seconds,
            force_all=force_all,
        )
        if reviewer is None:
            review_kwargs["prestarted_waveform"] = speculative
        return review(root, **review_kwargs)
    finally:
        if speculative_executor is not None:
            speculative_executor.shutdown(wait=True, cancel_futures=True)


def find_cover_and_embed(
    path: Path,
    *,
    audio_targets: list[Path] | None = None,
    album_scope: bool | None = None,
    use_color: bool = True,
    interactive: bool = True,
    key_reader=None,
    json_fetcher: Callable[..., dict[str, Any] | None] | None = None,
    text_fetcher: Callable[[str], str] | None = None,
    image_fetcher: Callable[[str], tuple[bytes, str, str]] | None = None,
    preview_renderer=None,
    image_viewer=None,
) -> list[str]:
    """Find one release, save its complete art set, embed only its Front."""
    targets = audio_targets or [path]
    album_scope = (
        bool(album_scope)
        if album_scope is not None
        else bool(recognized_album_artist(path.parent) or len(targets) > 1)
    )
    metadata = cover_lookup_metadata(path)
    identity = (
        f"{metadata.get('album_artist') or metadata.get('artist')} — "
        f"{metadata.get('album')}"
    ).strip(" —") or path.name
    cover_narration(
        "🏷️",
        f"Search metadata: {identity}.",
        use_color=use_color,
        color=(145, 125, 75),
        dim=True,
    )
    cover_narration(
        "🌐",
        "Searching exact "
        f"{inline_italic('MusicBrainz', use_color)} tags first, then "
        f"{inline_italic('Cover Art Archive', use_color)}, "
        f"{inline_italic('Discogs', use_color)} when configured, "
        f"{inline_italic('Bandcamp', use_color)}, and "
        f"{inline_italic('Apple Music/iTunes', use_color)}.",
        use_color=use_color,
        color=(85, 135, 165),
        dim=True,
    )
    with progress_bar(
        total=1,
        description="🎨 Finding cover art",
        unit="release",
        bar_format=ITEM_PROGRESS_FORMAT,
        enabled=bool(getattr(sys.stderr, "isatty", lambda: False)()),
    ) as lookup_progress:
        match = resolve_cover_match(
            path,
            json_fetcher=json_fetcher,
            text_fetcher=text_fetcher,
        )
        if lookup_progress is not None:
            lookup_progress.update(1)
    confidence_text = (
        "exact tagged release ID"
        if match.exact_id
        else f"{match.confidence}% metadata confidence"
    )
    cover_narration(
        "🎯",
        f"Matched cover art: {match.artist} — {match.album} "
        f"({match.date or 'date unknown'}; {confidence_text}).",
        use_color=use_color,
        color=(105, 200, 135),
    )
    plan = artwork_name_plan(
        match,
        path,
        album_scope=album_scope,
    )
    front_items = [(artwork, name) for artwork, name in plan if artwork.front]
    if len(front_items) != 1:
        raise RuntimeError(
            "Selected release did not provide exactly one primary Front image"
        )
    names = ", ".join(name for _artwork, name in plan)
    count_label = (
        f"{len(plan)} distinct image{'s' if len(plan) != 1 else ''}"
    )
    cover_narration(
        "🖼️",
        "Selected artwork set contains "
        f"{inline_italic(count_label, use_color)}: "
        f"{inline_italic(names, use_color)}.",
        use_color=use_color,
        color=(255, 190, 80),
    )
    if not match.exact_id:
        if not interactive:
            raise RuntimeError(
                "A metadata-based cover candidate needs interactive confirmation"
            )
        if not prompt_for_approval(
            f"Download and review this {len(plan)}-image artwork set "
            f"({names}), then embed only cover.jpg as its Front image?",
            default_yes=False,
            use_color=use_color,
            key_reader=key_reader,
            indent="            ",
        ):
            raise RuntimeError("Cover candidate was declined")

    fetch_image = image_fetcher or cover_http_get_bytes
    actions = [f"cover_source:{match.source} release {match.release_id}"]
    downloaded: list[
        tuple[CoverArtwork, str, bytes, int, int, str]
    ] = []
    with progress_bar(
        total=len(plan),
        description="⬇️ Downloading cover artwork",
        unit="images",
        bar_format=ITEM_PROGRESS_FORMAT,
        enabled=bool(getattr(sys.stderr, "isatty", lambda: False)()),
    ) as download_progress:
        for artwork, filename in plan:
            cover_narration(
                "⬇️",
                f"Downloading one {', '.join(artwork.types) or 'Other'} "
                f"image for {inline_italic(filename, use_color)}…",
                use_color=use_color,
                color=(85, 155, 205),
                dim=True,
            )
            try:
                payload, content_type, _final_url = fetch_image(artwork.url)
                jpeg, width, height, source_format = validated_jpeg(
                    payload,
                    content_type,
                    front=artwork.front,
                )
                downloaded.append(
                    (
                        artwork,
                        filename,
                        jpeg,
                        width,
                        height,
                        source_format,
                    )
                )
            except Exception as exc:
                cover_narration(
                    "❌",
                    f"Rejected {filename}: {exc}.",
                    use_color=use_color,
                    color=(255, 90, 100),
                )
                if artwork.front:
                    raise
                actions.append(f"artwork_rejected:{filename}")
            finally:
                if download_progress is not None:
                    download_progress.update(1)

    saved_by_id: dict[str, Path] = {}
    for artwork, filename, jpeg, width, height, source_format in downloaded:
        desired = path.parent / filename
        identical_existing = (
            desired.exists()
            and hashlib.sha256(desired.read_bytes()).digest()
            == hashlib.sha256(jpeg).digest()
        )
        if identical_existing:
            target = desired
            newly_written = False
        else:
            target = collision_safe_path(desired)
            target.write_bytes(jpeg)
            newly_written = True
        cover_narration(
            "🔬",
            f"Verified {source_format} artwork at {width}x{height}; "
            f"reviewing {target.name}.",
            use_color=use_color,
            color=(150, 215, 185),
        )
        if interactive and not artwork_review_choice(
            target,
            label=filename,
            use_color=use_color,
            key_reader=key_reader,
            preview_renderer=preview_renderer,
            image_viewer=image_viewer,
        ):
            rejected = rejected_artwork_path(target)
            if newly_written:
                target.replace(rejected)
            else:
                rejected.write_bytes(jpeg)
            recycle_path(rejected)
            actions.append(f"recycled_rejected_art:{rejected.name}")
            cover_narration(
                "♻️",
                f"Rejected {filename}; renamed it to {rejected.name} "
                "and sent it to the Recycle Bin.",
                use_color=use_color,
                color=(235, 175, 80),
            )
            if artwork.front:
                raise RuntimeError("Front artwork was rejected by username")
            continue
        if identical_existing:
            actions.append(f"kept_identical_art:{target}")
        else:
            actions.append(f"saved_art:{target}")
        saved_by_id[artwork.image_id] = target
        cover_narration(
            "✅",
            (
                f"Approved and saved {target.name}."
                if interactive
                else f"Saved {target.name} under explicit unattended "
                "--find-cover authorization."
            ),
            use_color=use_color,
            color=(150, 215, 185),
        )

    front_artwork = front_items[0][0]
    cover_path = saved_by_id.get(front_artwork.image_id)
    if cover_path is None or not cover_path.is_file():
        raise RuntimeError("The verified Front image was not saved")
    for target_audio in targets:
        if embedded_pictures(target_audio):
            continue
        cover_narration(
            "🎵",
            f"Embedding only {cover_path.name} into {target_audio.name}.",
            use_color=use_color,
            color=(130, 230, 165),
        )
        backup = embed_front_art(target_audio, cover_path, force=False)
        if backup is None:
            raise RuntimeError(
                f"Front cover was not embedded into {target_audio}"
            )
        actions.append(f"backup:{backup}")
        actions.append(f"embedded_art:{target_audio}")
    return actions


def image_mime(path: Path) -> str:
    data = path.read_bytes()[:16]
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"GIF8"):
        return "image/gif"
    if data.startswith(b"RIFF") and b"WEBP" in data:
        return "image/webp"
    return "image/jpeg"


def picture_extension(mime: str) -> str:
    return {
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
    }.get(mime, ".jpg")


def embedded_pictures(path: Path) -> list[tuple[bytes, str, int, str]]:
    audio = mutagen_file(path)
    if path.suffix.lower() == ".flac":
        return [
            (picture.data, picture.mime, int(picture.type), picture.desc or "")
            for picture in audio.pictures
        ]
    if not audio.tags:
        return []
    return [
        (picture.data, picture.mime, int(picture.type), picture.desc or "")
        for picture in audio.tags.getall("APIC")
    ]


def art_sidecar_stem(picture_type: int) -> str:
    return {
        3: "cover",
        4: "back",
        5: "booklet",
        6: "disc",
        7: "artist",
        8: "artist",
        9: "artist",
        10: "artist",
        11: "artist",
        12: "artist",
    }.get(picture_type, f"artwork-{picture_type:02d}")


def is_album_track_filename(path: Path) -> bool:
    """Recognize leading or artist/album-prefixed two-digit album track numbers."""
    return bool(
        re.search(r"(?:^|[-_. ])\d{1,2}(?:[ _.-]+)", path.stem)
    )


def exported_art_sidecar_stem(path: Path, picture_type: int) -> str:
    """Name album art collectively, but keep loose/MISC art track-specific."""
    standard = art_sidecar_stem(picture_type)
    if is_album_track_filename(path):
        return standard
    if picture_type == 3:
        return path.stem
    return f"{path.stem} - {standard}"


def export_art_sidecars(path: Path, write: bool = True) -> list[str]:
    existing_hashes = {
        hashlib.sha256(candidate.read_bytes()).hexdigest()
        for candidate in path.parent.iterdir()
        if candidate.is_file() and candidate.suffix.lower() in IMAGE_EXTS
    }
    exports: list[str] = []
    reserved: set[Path] = set()
    for data, mime, picture_type, _description in embedded_pictures(path):
        digest = hashlib.sha256(data).hexdigest()
        if digest in existing_hashes:
            continue
        stem = exported_art_sidecar_stem(path, picture_type)
        extension = picture_extension(mime)
        target = collision_safe_path(
            path.parent / f"{stem}{extension}", reserved
        )
        if write:
            target.write_bytes(data)
        existing_hashes.add(digest)
        reserved.add(target)
        exports.append(str(target))
    return exports


def same_basename_front_art_candidates(audio_path: Path) -> list[Path]:
    """Return track-specific Front art only for an unnumbered/MISC audio file."""
    if is_album_track_filename(audio_path):
        return []
    candidates: list[Path] = []
    for extension in FRONT_ART_EXTENSION_PRIORITY:
        candidate = audio_path.with_suffix(extension)
        if candidate.is_file() and candidate.stat().st_size > 0:
            candidates.append(candidate)
    return candidates


def embeddable_front_art_candidates(audio_path: Path) -> list[Path]:
    """Prefer folder Front art, then an exact MISC-track basename image."""
    candidates = folder_front_art_candidates(audio_path.parent)
    candidates.extend(same_basename_front_art_candidates(audio_path))
    return list(dict.fromkeys(candidates))


def front_art_candidate(path: Path) -> Path | None:
    candidates = embeddable_front_art_candidates(path)
    return candidates[0] if candidates else None


def is_allowed_front_art_name(
    path: Path,
    *,
    audio_path: Path | None = None,
) -> bool:
    """Accept folder Front names or the exact basename of one MISC track."""
    if re.fullmatch(
        r"(?:cover|folder)(?: \(\d+\))?",
        path.stem,
        flags=re.IGNORECASE,
    ):
        return True
    if audio_path is None or is_album_track_filename(audio_path):
        return False
    return (
        path.parent.resolve() == audio_path.parent.resolve()
        and path.stem.casefold() == audio_path.stem.casefold()
        and path.suffix.casefold() in IMAGE_EXTS
    )


def folder_front_art_candidates(folder: Path) -> list[Path]:
    """Return only explicit ``cover.*``/``folder.*`` Front sidecars.

    Same-stem images, sole images, ``front.*``, and especially ``proof.*`` are
    never inferred to be the cover.
    """
    candidates: list[Path] = []
    for stem in FRONT_ART_STEMS:
        for extension in FRONT_ART_EXTENSION_PRIORITY:
            candidate = folder / f"{stem}{extension}"
            if (
                candidate.is_file()
                and candidate.stat().st_size > 0
            ):
                candidates.append(candidate)
    return candidates


def normalized_local_front_jpeg(
    image: Path,
    *,
    audio_path: Path | None = None,
    write: bool = True,
) -> tuple[Path, bool]:
    """Return a JPEG Front sidecar, creating a collision-safe copy if needed."""
    if not is_allowed_front_art_name(image, audio_path=audio_path):
        raise RuntimeError(
            f"Refusing non-cover artwork sidecar: {image.name}"
        )
    if image.suffix.casefold() == ".jpg" and image_mime(image) == "image/jpeg":
        return image, False
    if Image is None:
        raise RuntimeError(
            "Pillow is required to convert non-JPEG Front artwork"
        )
    try:
        with Image.open(image) as source:
            converted = source.convert("RGB")
            output = io.BytesIO()
            converted.save(
                output,
                format="JPEG",
                quality=95,
                subsampling=0,
                optimize=True,
            )
            payload = output.getvalue()
    except Exception as exc:
        raise RuntimeError(
            f"Could not convert {image.name} to JPEG"
        ) from exc
    desired = image.with_name(f"{image.stem}.jpg")
    if (
        desired.is_file()
        and hashlib.sha256(desired.read_bytes()).digest()
        == hashlib.sha256(payload).digest()
    ):
        return desired, False
    target = collision_safe_path(desired)
    if not write:
        return target, True
    target.write_bytes(payload)
    if image_mime(target) != "image/jpeg":
        raise RuntimeError(f"JPEG conversion verification failed: {target}")
    return target, True


def embed_front_art(path: Path, image: Path, force: bool) -> Path | None:
    if not is_allowed_front_art_name(image, audio_path=path):
        raise RuntimeError(
            "Only cover.*, folder.*, or an exact unnumbered-track basename "
            f"may be embedded; refusing {image.name}"
        )
    pictures = embedded_pictures(path)
    if pictures and not force:
        return None
    data = image.read_bytes()
    mime = image_mime(image)
    backup = backup_before_inline_replacement(path)
    if path.suffix.lower() == ".flac":
        audio = FLAC(path)
        audio.clear_pictures()
        picture = Picture()
        picture.type = 3
        picture.mime = mime
        picture.desc = "Cover"
        picture.data = data
        audio.add_picture(picture)
        audio.save()
    else:
        audio = ensure_id3(path)
        audio.tags.delall("APIC")
        audio.tags.add(APIC(encoding=3, mime=mime, type=3, desc="Cover", data=data))
        audio.save(v2_version=3)
    return backup


def apply_art(path: Path, write: bool = True) -> list[str]:
    actions = [
        f"exported_art:{exported}"
        for exported in export_art_sidecars(path, write)
    ]
    picture_count = len(embedded_pictures(path))
    candidate = front_art_candidate(path)
    if candidate and picture_count != 1:
        jpeg_candidate, created_jpeg = normalized_local_front_jpeg(
            candidate,
            audio_path=path,
            write=write,
        )
        if created_jpeg:
            actions.append(
                f"{'saved_art' if write else 'would_save_art'}:"
                f"{jpeg_candidate}"
            )
        if write:
            backup = embed_front_art(
                path,
                jpeg_candidate,
                force=picture_count > 0,
            )
            if backup is not None:
                actions.append(f"backup:{backup}")
                actions.append(f"embedded_art:{jpeg_candidate}")
        else:
            actions.append(f"would_embed_art:{jpeg_candidate}")
    return actions


def copy_discernible_metadata_to_flac(source: Path, destination: Path) -> list[str]:
    """Copy readable tags and conservative folder-derived identity to FLAC."""
    metadata = cover_lookup_metadata(source)
    flac = FLAC(destination)
    tag_names = {
        "title": "TITLE",
        "artist": "ARTIST",
        "album_artist": "ALBUMARTIST",
        "album": "ALBUM",
        "date": "DATE",
        "track": "TRACKNUMBER",
    }
    written: list[str] = []
    for source_name, tag_name in tag_names.items():
        value = str(metadata.get(source_name) or "").strip()
        if value:
            flac[tag_name] = [value]
            written.append(tag_name.lower())
    flac.save()
    return written


def convert_wav_to_flac(
    wav_path: Path,
    *,
    use_color: bool,
    key_reader=None,
) -> list[str]:
    """Create a FLAC from one WAV, enrich it conservatively, and verify it."""
    if wav_path.suffix.lower() != ".wav":
        raise RuntimeError("WAV conversion was requested for a non-WAV file")
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("WAV-to-FLAC conversion requires ffmpeg in PATH")
    destination = wav_path.with_suffix(".flac")
    if destination.exists():
        raise FileExistsError(
            f"Refusing to overwrite existing FLAC: {destination.name}"
        )
    print(
        console_safe_text(
            f"            🎚️ Converting {wav_path.name} to {destination.name}:"
        ),
        flush=True,
    )
    result = subprocess.run(
        [
            str(ffmpeg), "-hide_banner", "-y", "-i", str(wav_path),
            "-map_metadata", "0", "-c:a", "flac", str(destination),
        ],
        check=False,
    )
    if result.returncode or not destination.is_file() or destination.stat().st_size == 0:
        raise RuntimeError("ffmpeg did not create a valid FLAC conversion")
    actions = [f"converted_flac:{destination}"]
    metadata = copy_discernible_metadata_to_flac(wav_path, destination)
    if metadata:
        actions.append("metadata:" + ",".join(metadata))
    lyric_actions = embed_lyrics(destination, write=True)
    actions.extend(lyric_actions)
    front = front_art_candidate(destination)
    if front is not None:
        actions.extend(apply_art(destination, write=True))
    else:
        actions.extend(
            find_cover_and_embed(
                destination,
                use_color=use_color,
                interactive=True,
                key_reader=key_reader,
            )
        )
    if not FLAC(destination):
        raise RuntimeError("Converted FLAC could not be re-opened for verification")
    wav_backup = replacement_backup_path(wav_path)
    wav_path.rename(wav_backup)
    if wav_path.exists() or not wav_backup.is_file():
        raise RuntimeError("Converted WAV could not be moved to its backup name")
    actions.append(f"backup:{wav_backup}")
    actions.append("re-audit:new_flac_passed")
    return actions


def review_extracted_art_sidecars(
    actions: list[str],
    *,
    use_color: bool,
    key_reader=None,
    preview_renderer=None,
    image_viewer=None,
) -> bool:
    """Preview each newly exported embedded-art sidecar before keeping it.

    An export is not treated as a trustworthy folder asset merely because its
    audio container called it Front/Back/etc.  The user sees the exact
    extracted pixels and can keep or reject each newly written image.  A
    rejection is renamed with the standard username suffix and recycled.
    """
    exported = [
        Path(action.removeprefix("exported_art:"))
        for action in actions
        if action.startswith("exported_art:")
    ]
    all_approved = True
    for sidecar in exported:
        if not sidecar.is_file():
            continue
        cover_narration(
            "🖼️",
            f"Extracted embedded artwork sidecar: {sidecar.name}.",
            use_color=use_color,
            color=(95, 190, 225),
        )
        accepted = artwork_review_choice(
            sidecar,
            label=sidecar.name,
            use_color=use_color,
            key_reader=key_reader,
            preview_renderer=preview_renderer,
            image_viewer=image_viewer,
            question_text=(
                "Is this extracted embedded artwork sidecar "
                f"({sidecar.name}) fine to keep?"
            ),
        )
        if accepted:
            actions.append(f"approved_extracted_art:{sidecar.name}")
            cover_narration(
                "✅",
                f"Approved extracted artwork sidecar: {sidecar.name}.",
                use_color=use_color,
                color=(95, 245, 135),
            )
            continue
        all_approved = False
        rejected = rejected_artwork_path(sidecar)
        sidecar.replace(rejected)
        recycle_path(rejected)
        actions.append(f"recycled_rejected_art:{rejected.name}")
        cover_narration(
            "♻️",
            f"Rejected extracted artwork recycled: {rejected.name}.",
            use_color=use_color,
            color=(165, 165, 175),
            dim=True,
        )
    return all_approved


def render_text(data: dict[str, Any], max_examples: int) -> str:
    return render_console_report(data, max_examples, use_color=False)


SUMMARY_CATEGORIES = {
    "backup_file": ("💾", "Backup files kept", "backup"),
    "json_sidecar": ("🧾", "JSON sidecars kept", "JSON"),
    "log_sidecar": ("📜", "Log sidecars kept", "log"),
    "kept_user_marker": ("📌", "User marker/comment files kept", "marker"),
}


def rgb_text(text: str, red: int, green: int, blue: int, enabled: bool, dim: bool = False) -> str:
    if not enabled:
        return text
    faint = ANSI["dim"] if dim else ""
    return f"{faint}\033[38;2;{red};{green};{blue}m{text}{ANSI['reset']}"


def varied_path(path: str, use_color: bool) -> str:
    if not use_color:
        return path
    digest = hashlib.sha256(path.encode("utf-8", errors="replace")).digest()
    offsets = tuple((byte % 41) - 20 for byte in digest[:3])
    base = (105, 190, 225)
    color = tuple(max(60, min(245, value + offset)) for value, offset in zip(base, offsets))
    return (
        f"{ANSI['dim']}{ANSI['italic']}"
        f"\033[38;2;{color[0]};{color[1]};{color[2]}m"
        f"{path}{ANSI['reset']}"
    )


def bright_cyan_path(path: str, use_color: bool) -> str:
    """Render a prominent audio target, distinct from dim suggestion text."""
    if not use_color:
        return path
    digest = hashlib.sha256(path.encode("utf-8", errors="replace")).digest()
    offsets = tuple((byte % 19) - 9 for byte in digest[:3])
    base = (65, 245, 255)
    color = tuple(
        max(80, min(255, value + offset))
        for value, offset in zip(base, offsets)
    )
    return (
        f"{ANSI['italic']}"
        f"\033[38;2;{color[0]};{color[1]};{color[2]}m"
        f"{path}{ANSI['reset']}"
    )


def varied_filename_chunk(
    chunk: str,
    identity: str,
    line_index: int,
    use_color: bool,
) -> str:
    """Style one wrapped filename line with a small, stable RGB variation."""
    if not use_color:
        return chunk
    digest = hashlib.sha256(
        f"{identity}\0{line_index}".encode("utf-8", errors="replace")
    ).digest()
    base = (110, 188, 220)
    offsets = tuple((byte % 19) - 9 for byte in digest[:3])
    color = tuple(
        max(75, min(240, value + offset))
        for value, offset in zip(base, offsets)
    )
    return (
        f"{ANSI['dim']}{ANSI['italic']}"
        f"\033[38;2;{color[0]};{color[1]};{color[2]}m"
        f"{chunk}{ANSI['reset']}"
    )


def music_filename(
    path: str,
    use_color: bool,
    *,
    prominent: bool = False,
) -> str:
    """Render a filename with a one-cell note aligned under two-cell emoji."""
    renderer = bright_cyan_path if prominent else varied_path
    return f" ♪ {renderer(path, use_color)}"


def middle_ellipsize(text: str, max_cells: int) -> str:
    """Shorten a long one-line value in its middle while preserving both ends."""
    value = str(text)
    if max_cells <= 0:
        return ""
    if visible_cell_width(value) <= max_cells:
        return value
    if max_cells <= 3:
        return "." * max_cells
    available = max_cells - 1
    left_cells = max(1, available * 2 // 5)
    right_cells = max(1, available - left_cells)
    left = value[:left_cells]
    right = value[-right_cells:]
    while visible_cell_width(left + "…" + right) > max_cells and right:
        right = right[1:]
    while visible_cell_width(left + "…" + right) > max_cells and left:
        left = left[:-1]
    return left + "…" + right


def warning_finding_message(finding: dict[str, Any]) -> str:
    """Mark a displayed actionable/review finding as a warning."""
    message = str(finding["message"])
    return message if message.startswith("⚠️") else f"⚠️ {message}"


def suggestion_emoji(category: str) -> str:
    """Choose a compact visual cue for the kind of suggested next step."""
    if category in {
        "embedded_lyrics_outdated",
        "karaoke_not_embedded",
        "missing_karaoke",
        "missing_plain_lyrics",
        "missing_srt_from_lrc_txt",
        "plain_lyrics_not_embedded",
        "unusable_karaoke_sidecar",
        "unusable_plain_lyric_sidecar",
    }:
        return "🎤"
    if category in {
        "embedded_art_without_sidecar",
        "missing_embedded_art",
        "multiple_embedded_artworks",
        "smaller_numbered_image_duplicate",
    }:
        return "🖼️"
    if category == "missing_replaygain":
        return "🎚️"
    if category in GROUPED_RENAME_CATEGORIES:
        return "✂️"
    if category.startswith("archive_"):
        return "📁"
    if category in {
        "adobe_xmp",
        "bare_marker",
        "stale_transcription_marker",
        "tagrename_m3u8",
        "temporary_batch_file",
        "vad_scratch_srt",
    }:
        return "🗑️"
    if category in {
        "empty_genre",
        "filename_marker_style",
        "missing_album",
        "missing_artist",
        "missing_genre",
        "missing_title",
    }:
        return "🏷️"
    return "💡"


def suggested_text(finding: dict[str, Any], use_color: bool) -> str:
    """Render a deliberately subdued suggestion with a semantic emoji."""
    text = (
        f"{suggestion_emoji(str(finding['category']))} "
        f"Suggested: {finding['suggestion']}"
    )
    return rgb_text(text, 75, 155, 190, use_color, dim=True)


def finding_sidecar_lines(
    finding: dict[str, Any],
    use_color: bool,
) -> list[str]:
    """Render exact lyric sidecars confirmed or rejected by validation."""
    details = finding.get("details", {})
    sidecars: list[str] = []
    if details.get("sidecar"):
        sidecars.append(str(details["sidecar"]))
    sidecars.extend(str(path) for path in details.get("sidecars", []))
    if not sidecars:
        return []
    needs_repair = finding["category"] in {
        "unusable_karaoke_sidecar",
        "unusable_plain_lyric_sidecar",
    }
    label = "Sidecar needs repair" if needs_repair else "Confirmed sidecar"
    return [
        f"📄 {label}: {varied_path(path, use_color)}"
        for path in dict.fromkeys(sidecars)
    ]


def rename_preview_table(
    finding: dict[str, Any],
    use_color: bool,
    terminal_columns: int | None = None,
) -> list[str]:
    """Render a compact Before/After table that never targets viewport width."""
    renames = [
        item
        for item in finding.get("details", {}).get("renames", [])
        if str(item.get("before", "")) != str(item.get("after", ""))
    ]
    pairs = [
        (
            f" ♪ {Path(item['before']).name}",
            f" ♪ {Path(item['after']).name}",
        )
        for item in renames
    ]
    if not pairs:
        return []
    before_heading = "Before filename"
    after_heading = "After filename"
    columns = terminal_columns or visible_console_size().columns
    outside_indent = 12
    column_gap = 5
    available = max(4, columns - outside_indent)
    if available < 41:
        lines: list[str] = []
        label_width = len(after_heading) + 2
        content_width = max(4, available - label_width)
        for before, after in pairs:
            for heading_text, value, color in (
                (before_heading, before, (255, 245, 70)),
                (after_heading, after, (255, 205, 55)),
            ):
                wrapped = textwrap.wrap(
                    value,
                    width=content_width,
                    subsequent_indent="  ",
                    break_long_words=True,
                    break_on_hyphens=True,
                ) or [""]
                for line_index, chunk in enumerate(wrapped):
                    label = (
                        f"{heading_text}:".ljust(label_width)
                        if line_index == 0
                        else " " * label_width
                    )
                    styled_label = (
                        rgb_text(label, *color, use_color)
                        if line_index == 0
                        else label
                    )
                    lines.append(
                        styled_label
                        + varied_filename_chunk(
                            chunk,
                            value,
                            line_index,
                            use_color,
                        )
                    )
        return lines
    natural_before_width = max(
        len(before_heading),
        *(len(before) for before, _after in pairs),
    )
    natural_after_width = max(
        len(after_heading),
        *(len(after) for _before, after in pairs),
    )
    natural_table_width = (
        natural_before_width + column_gap + natural_after_width
    )
    if natural_table_width <= available:
        before_width = natural_before_width
        after_width = natural_after_width
    else:
        usable_width = max(36, available - column_gap)
        minimum_width = min(18, usable_width // 2)
        combined_natural = natural_before_width + natural_after_width
        before_width = round(
            usable_width * natural_before_width / combined_natural
        )
        before_width = max(
            minimum_width,
            min(natural_before_width, before_width),
        )
        after_width = min(
            natural_after_width,
            usable_width - before_width,
        )
        if after_width < minimum_width:
            after_width = minimum_width
            before_width = usable_width - after_width
        unused = usable_width - before_width - after_width
        while unused > 0:
            before_need = natural_before_width - before_width
            after_need = natural_after_width - after_width
            if before_need <= 0 and after_need <= 0:
                break
            if before_need >= after_need and before_need > 0:
                before_width += 1
            elif after_need > 0:
                after_width += 1
            unused -= 1
    heading = (
        rgb_text(before_heading, 255, 245, 70, use_color)
        + " " * (before_width - len(before_heading))
        + " " * column_gap
        + rgb_text(after_heading, 255, 205, 55, use_color)
    )
    rule = rgb_text(
        "─" * before_width
        + " " * column_gap
        + "─" * after_width,
        155,
        125,
        55,
        use_color,
        dim=True,
    )
    lines = [heading, rule]
    for before, after in pairs:
        wrapped_before = textwrap.wrap(
            before,
            width=before_width,
            subsequent_indent="  ",
            break_long_words=True,
            break_on_hyphens=False,
        ) or [""]
        wrapped_after = textwrap.wrap(
            after,
            width=after_width,
            subsequent_indent="  ",
            break_long_words=True,
            break_on_hyphens=False,
        ) or [""]
        row_height = max(len(wrapped_before), len(wrapped_after))
        for line_index in range(row_height):
            before_chunk = (
                wrapped_before[line_index]
                if line_index < len(wrapped_before)
                else ""
            )
            after_chunk = (
                wrapped_after[line_index]
                if line_index < len(wrapped_after)
                else ""
            )
            styled_before = varied_filename_chunk(
                before_chunk,
                before,
                line_index,
                use_color,
            )
            styled_after = varied_filename_chunk(
                after_chunk,
                after,
                line_index,
                use_color,
            )
            lines.append(
                styled_before
                + " " * (before_width - len(before_chunk))
                + " " * column_gap
                + styled_after
            )
    return lines


def humanized_action(action: str) -> str:
    """Convert an internal action token into compact user-facing prose."""
    if action == "plain_lyrics":
        return "plain lyrics"
    if action == "synced_lyrics":
        return "timed karaoke"
    if action.startswith("renamed_group:"):
        return f"renamed {action.partition(':')[2]}"
    if action.startswith("updated_playlists:"):
        count_text = action.partition(":")[2]
        try:
            count = int(count_text)
        except ValueError:
            return f"updated playlists: {count_text}"
        noun = "playlist" if count == 1 else "playlists"
        return f"updated {count} {noun}"
    prefix, separator, value = action.partition(":")
    label = prefix.replace("_", " ").replace("-", " ")
    return f"{label}: {value}" if separator else label


def action_result_lines(
    actions: list[str],
    use_color: bool,
    indent: str = "            ",
) -> list[str]:
    """Split backups, applied changes, and re-audit status into clear lines."""
    lines: list[str] = []
    replaygain_summary = next(
        (action for action in actions if action.startswith("replaygain_summary:")),
        None,
    )
    srt_summary = next(
        (
            action
            for action in actions
            if action.startswith("lyric_karaoke_fix_summary:")
            or action.startswith("generated_srt_summary:")
        ),
        None,
    )
    backups = [
        action.removeprefix("backup:")
        for action in actions
        if action.startswith("backup:")
    ]
    if replaygain_summary and backups:
        lines.append(
            rgb_text(
                f"{indent}💾 Backups: {len(backups)} audio "
                f"file{'s' if len(backups) != 1 else ''}",
                145,
                150,
                160,
                use_color,
                dim=True,
            )
        )
    else:
        for backup in backups:
            backup_name = Path(backup).name
            lines.append(
                rgb_text(
                    f"{indent}💾 Backup: {backup_name}",
                    145,
                    150,
                    160,
                    use_color,
                    dim=True,
                )
            )
    saved_art = [
        action.removeprefix("saved_art:")
        for action in actions
        if action.startswith("saved_art:")
    ]
    for artwork in saved_art:
        lines.append(
            rgb_text(
                f"{indent}🖼️ Saved artwork: {artwork}",
                175,
                205,
                220,
                use_color,
                dim=True,
            )
        )
    embedded_art = [
        action.removeprefix("embedded_art:")
        for action in actions
        if action.startswith("embedded_art:")
    ]
    for audio_path in embedded_art:
        lines.append(
            colorize(
                f"{indent}🎵 Embedded Front cover: {audio_path}",
                "green",
                use_color,
            )
        )
    rejected_art = [
        action.removeprefix("recycled_rejected_art:")
        for action in actions
        if action.startswith("recycled_rejected_art:")
    ]
    for artwork in rejected_art:
        lines.append(
            rgb_text(
                f"{indent}♻️ Rejected artwork recycled: {artwork}",
                195,
                185,
                165,
                use_color,
                dim=True,
            )
        )
    if replaygain_summary:
        payload = replaygain_summary.partition(":")[2].split("|")
        if len(payload) == 4:
            total_count, mp3_count, flac_count, elapsed_text = payload
            elapsed = compact_elapsed(float(elapsed_text))
            lines.append(
                colorize(
                    f"{indent}✅ ReplayGain applied to {total_count} audio files "
                    f"({mp3_count} MP3, {flac_count} FLAC) in {elapsed}.",
                    "green",
                    use_color,
                )
            )
    if srt_summary:
        payload = srt_summary.partition(":")[2].split("|", 2)
        if srt_summary.startswith("lyric_karaoke_fix_summary:") and len(payload) >= 2:
            generated_count, verified_count = payload[:2]
            lines.append(
                colorize(
                    f"{indent}🎤 Lyric/Karaoke Fix: verified {verified_count} SRT "
                    f"sidecar{'s' if verified_count != '1' else ''}; "
                    f"{generated_count} generated.",
                    "green",
                    use_color,
                )
            )
        elif payload:
            count = payload[0]
            lines.append(
                colorize(
                    f"{indent}🎤 Generated {count} SRT sidecar"
                    f"{'s' if count != '1' else ''} for this folder.",
                    "green",
                    use_color,
                )
            )
    recycled_empty_srts = [
        action for action in actions if action.startswith("recycled_empty_srt:")
    ]
    if recycled_empty_srts:
        count = len(recycled_empty_srts)
        lines.append(
            rgb_text(
                f"{indent}♻️ Recycled {count} empty SRT placeholder"
                f"{'s' if count != 1 else ''} before regeneration.",
                195, 185, 165, use_color, dim=True,
            )
        )
    applied = [
        humanized_action(action)
        for action in actions
        if not action.startswith("backup:")
        and not action.startswith("saved_art:")
        and not action.startswith("embedded_art:")
        and not action.startswith("recycled_rejected_art:")
        and not action.startswith("replaygain:")
        and not action.startswith("replaygain_summary:")
        and not action.startswith("generated_srt_summary:")
        and not action.startswith("lyric_karaoke_fix_summary:")
        and not action.startswith("recycled_empty_srt:")
        and not action.startswith("confirmed_srt:")
        and not (replaygain_summary and action.startswith("recycled:"))
        and action != "re-audit:passed"
    ]
    if applied:
        lines.append(
            colorize(
                f"{indent}🔧 Applied: {', '.join(applied)}",
                "green",
                use_color,
            )
        )
    if "re-audit:passed" in actions:
        lines.append(
            rgb_text(
                f"{indent}✔️ Re-audit: passed",
                110,
                225,
                150,
                use_color,
            )
        )
    return lines


def embedded_lyrics_console_lines(
    data: dict[str, Any],
    use_color: bool,
) -> list[str]:
    """List every track changed by the noninteractive ``--embed-lyrics`` pass."""
    embedded = data.get("embedded_lyrics", [])
    if not embedded:
        return []
    title = "Lyric/karaoke embedding"
    lines: list[str] = []
    lines.extend(
        double_height_gradient_section(
            title,
            use_color,
            ((255, 125, 215), (100, 205, 255)),
        )
    )
    lines.append("")
    for item in embedded:
        changed = [
            humanized_action(action)
            for action in item.get("actions", [])
            if not str(action).startswith("backup:")
        ]
        description = ", ".join(changed) or "available lyrics"
        lines.append("        🎤 Embedding lyrics & karaoke into file:")
        lines.append(
            f"            {music_filename(str(item['path']), use_color)}"
        )
        lines.append(
            colorize(
                f"            🔧 Applied: {description}",
                "green",
                use_color,
            )
        )
        for action in item.get("actions", []):
            if str(action).startswith("backup:"):
                backup = Path(
                    str(action).removeprefix("backup:")
                ).name
                lines.append(
                    rgb_text(
                        f"            💾 Backup: {backup}",
                        145,
                        150,
                        160,
                        use_color,
                        dim=True,
                    )
                )
        lines.append(
            rgb_text(
                "            ✔️ Re-audited in this audit pass.",
                135,
                195,
                170,
                use_color,
                dim=True,
            )
        )
    return lines


def found_cover_art_console_lines(
    data: dict[str, Any],
    use_color: bool,
) -> list[str]:
    """Summarize every release attempted by the ``--find-cover`` pre-pass."""
    results = data.get("found_cover_art", [])
    if not results:
        return []
    lines: list[str] = []
    lines.extend(
        double_height_gradient_section(
            "Artwork handled by --find-cover",
            use_color,
            ((255, 225, 80), (90, 200, 250)),
        )
    )
    lines.append("")
    for result in results:
        paths = result.get("paths", [])
        if result.get("error"):
            lines.append(
                rgb_text(
                    f"        ❌ Cover search failed: {result['error']}",
                    255,
                    95,
                    105,
                    use_color,
                )
            )
        else:
            lines.append(
                rgb_text(
                    f"        ✅ Release artwork applied to "
                    f"{len(paths)} audio file{'s' if len(paths) != 1 else ''}.",
                    110,
                    225,
                    150,
                    use_color,
                )
            )
        for path in paths:
            lines.append(f"            {music_filename(path, use_color)}")
        lines.extend(
            action_result_lines(
                list(result.get("actions", [])),
                use_color,
                indent="            ",
            )
        )
    return lines


def double_height_finding_folder_line(
    folder: str,
    use_color: bool,
    terminal_columns: int | None = None,
) -> list[str]:
    """Render an artwork-action folder as a compact DEC double-height pair."""
    prefix = "📁 Folder: "
    if not use_color:
        columns = terminal_columns or visible_console_size().columns
        width = max(12, columns - 12 - visible_cell_width(prefix))
        return [f"{prefix}{middle_ellipsize(folder, width)}"]
    columns = terminal_columns or visible_console_size().columns
    # The caller adds 12 normal-width indent columns. DEC double-height also
    # implies double-width glyphs, so budget the remaining row at half width.
    capacity = max(18, (max(20, columns - 12) - 8) // 2)
    path_width = max(6, capacity - visible_cell_width(prefix))
    display_folder = middle_ellipsize(folder, path_width)
    styled = (
        rgb_text(prefix, 245, 215, 95, True)
        + varied_path(display_folder, True)
    )
    return [
        f"{ANSI_DOUBLE_HEIGHT_TOP}{ANSI['bold']}{styled}",
        f"{ANSI_DOUBLE_HEIGHT_BOTTOM}{ANSI['bold']}{styled}",
    ]


def finding_target_lines(
    finding: dict[str, Any],
    use_color: bool,
    root: Path | None = None,
    terminal_columns: int | None = None,
) -> list[str]:
    """Render an audio target or a folder-level/grouped target."""
    if finding.get("details", {}).get("folder_level"):
        raw_folder = str(finding["path"])
        if raw_folder == "." and root is not None:
            raw_folder = str(root.resolve())
        columns = terminal_columns or visible_console_size().columns
        prefix = "📁 Folder: "
        folder_width = max(12, columns - 12 - visible_cell_width(prefix))
        return [
            f"{prefix}{varied_path(middle_ellipsize(raw_folder, folder_width), use_color)}"
        ]
    if finding["category"] in GROUPED_RENAME_CATEGORIES:
        raw_folder = str(finding["path"])
        if raw_folder == "." and root is not None:
            raw_folder = str(root.resolve())
        columns = terminal_columns or visible_console_size().columns
        prefix = "📁 Album folder: "
        folder_width = max(
            12,
            columns - 12 - visible_cell_width(prefix),
        )
        display_folder = middle_ellipsize(raw_folder, folder_width)
        return [
            f"{prefix}{varied_path(display_folder, use_color)}",
            *rename_preview_table(finding, use_color),
        ]
    raw_path = Path(str(finding["path"]))
    lines: list[str] = []
    if raw_path.parent != Path("."):
        folder_text = str(raw_path.parent)
        if finding.get("category") == "embedded_art_without_sidecar":
            lines.extend(
                double_height_finding_folder_line(
                    folder_text,
                    use_color,
                    terminal_columns=terminal_columns,
                )
            )
        else:
            columns = terminal_columns or visible_console_size().columns
            prefix = "📁 Folder: "
            folder_width = max(12, columns - 12 - visible_cell_width(prefix))
            lines.append(
                f"{prefix}{varied_path(middle_ellipsize(folder_text, folder_width), use_color)}"
            )
    lines.append(music_filename(raw_path.name, use_color, prominent=True))
    return lines


def finding_filename_columns(
    findings: list[dict[str, Any]], use_color: bool
) -> list[str]:
    """Render unique finding filenames in compact, console-width columns."""
    raw_names = list(dict.fromkeys(str(item["path"]) for item in findings))
    names: list[str] = []
    for raw_name in raw_names:
        raw_path = Path(raw_name)
        basename = raw_path.name
        # These grids identify tracks, not formats. Remove stacked audio
        # suffixes such as .mp3.flac as well as the ordinary final extension.
        while Path(basename).suffix.casefold() in AUDIO_EXTS:
            basename = Path(basename).stem
        # Album downloads commonly repeat "Artist - Album - " on every row.
        # The surrounding finding already supplies that context, so begin at
        # the track number and spend the saved width on the actual song title.
        match = re.search(r"(?i)(?:^| - )(\d{1,3}(?:[_. -]).*)$", basename)
        if match:
            basename = match.group(1)
        parent = "" if raw_path.parent == Path(".") else str(raw_path.parent)
        names.append(f"{parent}\\{basename}" if parent else basename)
    if not names:
        return []
    console_columns = max(40, visible_console_size().columns)
    available_width = max(20, console_columns - 12)
    longest = max(visible_cell_width(name) for name in names)
    preferred_width = min(52, max(22, longest + 2))
    column_count = max(
        1,
        min(len(names), (available_width + 3) // (preferred_width + 3)),
    )
    cell_width = max(12, (available_width - 3 * (column_count - 1)) // column_count)
    rendered: list[str] = []
    # Newspaper order: fill downward in the first column before beginning the
    # next (1/4, 2/5, 3/6), not ordinary row-major 1/2, 3/4, 5/6.
    row_count = math.ceil(len(names) / column_count)
    for row_index in range(row_count):
        cells = []
        for column_index in range(column_count):
            index = row_index + column_index * row_count
            if index >= len(names):
                continue
            name = names[index]
            display = middle_ellipsize(name, cell_width)
            cells.append(
                music_filename(display, use_color, prominent=False)
                + " " * max(0, cell_width - visible_cell_width(display))
            )
        rendered.append("            " + "   ".join(cells).rstrip())
    return rendered


def report_section(title: str, use_color: bool, color: str = "cyan") -> str:
    gradients = {
        "cyan": ((90, 245, 255), (80, 190, 250)),
        "green": ((130, 245, 160), (70, 195, 135)),
        "magenta": ((245, 155, 255), (195, 105, 235)),
        "yellow": ((255, 245, 95), (245, 185, 45)),
    }
    return decorated_gradient_header(
        title,
        use_color,
        gradients.get(color, ((235, 235, 245), (175, 185, 210))),
        add_colon=True,
    )


def gradient_text(
    text: str,
    use_color: bool,
    stops: tuple[tuple[int, int, int], ...],
) -> str:
    """Color each character by interpolating across one or more RGB stops."""
    if not use_color or not text:
        return text
    if len(stops) < 2:
        return rgb_text(text, *stops[0], use_color)
    visible_length = max(1, len(text) - 1)
    rendered: list[str] = []
    segment_count = len(stops) - 1
    for index, character in enumerate(text):
        overall = index / visible_length
        scaled = min(overall * segment_count, float(segment_count))
        segment = min(int(scaled), segment_count - 1)
        ratio = scaled - segment
        start, end = stops[segment], stops[segment + 1]
        color = tuple(
            round(start[channel] + (end[channel] - start[channel]) * ratio)
            for channel in range(3)
        )
        rendered.append(
            f"\033[38;2;{color[0]};{color[1]};{color[2]}m{character}"
        )
    return "".join(rendered) + ANSI["reset"]


def decorated_gradient_header(
    title: str,
    use_color: bool,
    stops: tuple[tuple[int, int, int], ...],
    *,
    add_colon: bool,
) -> str:
    """Render symmetric ornaments around independently gradient-colored text."""
    suffix = ":" if add_colon else ""
    if not use_color:
        return f"✨✱✨ {title}{suffix} ✨✱✨"
    ornament = gradient_text("✨✱✨", True, stops)
    styled_title = gradient_text(f"{title}{suffix}", True, stops)
    return f"{ornament} {styled_title} {ornament}"


def interactive_results_summary(
    applied: int,
    skipped: int,
    failed: int,
    use_color: bool,
) -> str:
    """Render aligned action totals with color applied only to each number."""
    applied_number = rgb_text(str(applied), 90, 225, 125, use_color)
    skipped_number = rgb_text(str(skipped), 255, 215, 70, use_color)
    failed_number = rgb_text(str(failed), 255, 95, 100, use_color)
    return (
        f"        {applied_number} applied, "
        f"{skipped_number} skipped, "
        f"{failed_number} failed."
    )


def print_interactive_results(
    result: dict[str, Any],
    use_color: bool,
) -> None:
    """Print the main audit's interactive totals in the standard section style."""
    if not result.get("decisions"):
        return
    results_header = "\n".join(
        double_height_gradient_section(
            "Interactive results",
            use_color,
            ((255, 135, 245), (175, 95, 240)),
        )
    )
    print(
        "\n"
        + results_header
        + "\n\n"
        + interactive_results_summary(
            len(result["applied_codes"]),
            len(result["skipped_codes"]),
            len(result["failed_codes"]),
            use_color,
        )
        + "\n"
    )


def double_height_report_line(text: str, use_color: bool, red: int, green: int, blue: int) -> list[str]:
    if not text.startswith(("✨", "✱", "*")):
        text = f"✨✱✨ {text}"
    if not use_color:
        return [text]
    if ":" in text:
        label, remainder = text.split(":", 1)
        end = (
            max(0, red - 25),
            max(0, green - 25),
            max(0, blue - 15),
        )
        styled = (
            gradient_text(f"{label}:", True, ((red, green, blue), end))
            + rgb_text(remainder, red, green, blue, True)
        )
    else:
        styled = gradient_text(
            text,
            True,
            (
                (red, green, blue),
                (max(0, red - 25), max(0, green - 25), max(0, blue - 15)),
            ),
        )
    return [
        f"{ANSI_DOUBLE_HEIGHT_TOP}{ANSI['bold']}{styled}",
        f"{ANSI_DOUBLE_HEIGHT_BOTTOM}{ANSI['bold']}{styled}",
    ]


def double_height_plain_status(
    text: str,
    use_color: bool,
    stops: tuple[tuple[int, int, int], ...],
) -> list[str]:
    """Render an undecorated double-height status line starting at column zero."""
    if not use_color:
        return [text]
    styled = f"{ANSI['bold']}{gradient_text(text, True, stops)}"
    return [
        f"{ANSI_DOUBLE_HEIGHT_TOP}{styled}",
        f"{ANSI_DOUBLE_HEIGHT_BOTTOM}{styled}",
    ]


def double_height_labeled_path(
    label: str,
    path: str,
    use_color: bool,
    red: int,
    green: int,
    blue: int,
    terminal_columns: int | None = None,
) -> list[str]:
    """Wrap a long path before emitting matched DEC double-height line pairs.

    This follows ``bigecho.bat``'s sizing rule: double-width glyphs have half
    the terminal's normal character capacity, with ten columns reserved as a
    safety margin for emoji and Windows Terminal width discrepancies.
    """
    decorated_label = f"✨✱✨ {label}"
    if not use_color:
        return [f"{decorated_label} {path}"]
    columns = terminal_columns or visible_console_size().columns
    double_height_capacity = max(20, (columns - 10) // 2)
    first_prefix = f"{decorated_label} "
    continuation_prefix = " " * visible_cell_width(first_prefix)
    chunks: list[tuple[str, str]] = []
    remaining = path
    prefix = first_prefix
    while remaining:
        available = max(
            1,
            double_height_capacity - visible_cell_width(prefix),
        )
        chunks.append((prefix, remaining[:available]))
        remaining = remaining[available:].lstrip()
        prefix = continuation_prefix
    if not chunks:
        chunks.append((first_prefix, ""))

    label_end = (
        max(0, red - 25),
        max(0, green - 25),
        max(0, blue - 15),
    )
    output: list[str] = []
    for prefix, path_chunk in chunks:
        if prefix == first_prefix:
            styled_prefix = gradient_text(
                prefix, True, ((red, green, blue), label_end)
            )
        else:
            styled_prefix = prefix
        styled = styled_prefix + varied_path(path_chunk, True)
        output.extend(
            [
                f"{ANSI_DOUBLE_HEIGHT_TOP}{ANSI['bold']}{styled}",
                f"{ANSI_DOUBLE_HEIGHT_BOTTOM}{ANSI['bold']}{styled}",
            ]
        )
    return output


def double_height_section(
    title: str, use_color: bool, red: int, green: int, blue: int
) -> list[str]:
    end = (
        max(0, red - 35),
        max(0, green - 35),
        max(0, blue - 20),
    )
    return double_height_gradient_section(
        title, use_color, ((red, green, blue), end)
    )


def double_height_gradient_section(
    title: str,
    use_color: bool,
    stops: tuple[tuple[int, int, int], ...],
) -> list[str]:
    """Render a decorated double-height header with a per-character gradient."""
    text = f"✨✱✨ {title}: ✨✱✨"
    if not use_color:
        return [text]
    styled = (
        f"{ANSI['bold']}"
        f"{decorated_gradient_header(title, True, stops, add_colon=True)}"
    )
    return [
        f"{ANSI_DOUBLE_HEIGHT_TOP}{styled}",
        f"{ANSI_DOUBLE_HEIGHT_BOTTOM}{styled}",
    ]


def traffic_gradient_text(text: str, use_color: bool) -> str:
    return gradient_text(
        text,
        use_color,
        ((75, 230, 105), (255, 225, 45), (255, 75, 80)),
    )


def double_height_traffic_section(title: str, use_color: bool) -> list[str]:
    text = f"✨✱✨ {title}: ✨✱✨"
    if not use_color:
        return [text]
    decorated = decorated_gradient_header(
        title,
        True,
        ((75, 230, 105), (255, 225, 45), (255, 75, 80)),
        add_colon=True,
    )
    styled = f"{ANSI['bold']}{decorated}"
    return [
        f"{ANSI_DOUBLE_HEIGHT_TOP}{styled}",
        f"{ANSI_DOUBLE_HEIGHT_BOTTOM}{styled}",
    ]


def friendly_category(category: str) -> str:
    names = {
        "missing_album": "Missing album tag",
        "embedded_lyrics_outdated": "Embedded lyrics need refreshing",
        "excessive_silence": "Excessive silence detected",
        "lrc_txt_missing_srt_but_lrc_untimed": "Untimed LRC cannot create karaoke",
        "missing_plain_lyrics": "Plain lyrics missing",
        "missing_karaoke": "Timed karaoke missing",
        "unusable_karaoke_sidecar": "Timed sidecar needs repair",
        "unusable_plain_lyric_sidecar": "Plain-lyrics sidecar needs repair",
        "missing_embedded_art": "Embedded cover missing",
        "corrupted_legacy_id3_frames": "Corrupted legacy ID3 frames",
        "missing_replaygain": "ReplayGain missing",
        "missing_srt_from_lrc_txt": "SRT sidecars ready to generate",
        "karaoke_not_embedded": "Timed karaoke ready to embed",
        "plain_lyrics_not_embedded": "Plain lyrics ready to embed",
        "redundant_album_artist_filename_group": (
            "Redundant artist in album filenames"
        ),
        "filename_title_capitalization_group": (
            "Album filename capitalization"
        ),
        "all_caps_album_title": "All-caps album title",
        "same_stem_mp3_flac": "Matching MP3/FLAC pair",
    }
    return names.get(category, category.replace("_", " ").capitalize())


def finding_category_emoji(category: str) -> str:
    """Return the category-specific icon used before a finding heading."""
    if category in {
        "embedded_art_without_sidecar",
        "missing_embedded_art",
        "multiple_embedded_artworks",
        "smaller_numbered_image_duplicate",
    }:
        return "🎨"
    if category in {
        "embedded_lyrics_outdated",
        "karaoke_not_embedded",
        "lrc_txt_missing_srt_but_lrc_untimed",
        "missing_karaoke",
        "missing_plain_lyrics",
        "missing_srt_from_lrc_txt",
        "plain_lyrics_not_embedded",
        "unusable_karaoke_sidecar",
        "unusable_plain_lyric_sidecar",
    }:
        return "🎤"
    if category == "missing_replaygain":
        return "🎚️"
    if category == "excessive_silence":
        return "🔇"
    if category in GROUPED_RENAME_CATEGORIES or category == "all_caps_album_title":
        return "✂️"
    if category in {
        "empty_genre",
        "missing_album",
        "missing_artist",
        "missing_genre",
        "missing_title",
        "simplify_punk_genre",
        "url_comment",
    }:
        return "🏷️"
    if category.startswith("archive_"):
        return "📁"
    if category in {
        "adobe_xmp",
        "bare_marker",
        "stale_transcription_marker",
        "tagrename_m3u8",
        "temporary_batch_file",
        "vad_scratch_srt",
    }:
        return "🗑️"
    if category in {
        "same_stem_mp3_flac",
        "duplicate_audio",
    }:
        return "👯"
    if category in {
        "filename_marker_style",
        "forbidden_filename_char",
        "read_only_audio",
        "tiny_audio",
        "unreadable_audio",
        "zero_byte_audio",
    }:
        return "🛠️"
    return "⚠️"


def finding_category_label(category: str) -> str:
    """Prefix a human-readable finding category with its semantic emoji."""
    return f"{finding_category_emoji(category)} {friendly_category(category)}"


def approval_action_line(
    finding: dict[str, Any],
    use_color: bool,
) -> str:
    """Render an action label bright yellow and its warning darker yellow."""
    label = rgb_text(
        finding_category_label(str(finding["category"])),
        255,
        245,
        70,
        use_color,
    )
    divider = rgb_text("—", 235, 190, 45, use_color)
    message = rgb_text(
        warning_finding_message(finding),
        205,
        155,
        45,
        use_color,
    )
    return f"{label} {divider} {message}"


def approval_question(finding: dict[str, Any]) -> str:
    """Return the exact operation that an interactive approval will perform."""
    category = str(finding["category"])
    if category == "missing_embedded_art":
        sidecars = finding.get("details", {}).get("sidecars", [])
        if sidecars:
            sidecar_name = Path(str(sidecars[0])).name
            return (
                "Embed the available front-cover sidecar "
                f"({sidecar_name}) into this audio file now?"
            )
        return (
            "Search for the release artwork, download and preview every supplied "
            "image part, and embed only an approved Front cover now?"
        )
    if category == "redundant_album_artist_filename_group":
        count = len(
            [
                item
                for item in finding.get("details", {}).get("renames", [])
                if str(item.get("before", ""))
                != str(item.get("after", ""))
            ]
        )
        return (
            f"Rename these {count} album files to remove the redundant "
            "artist name now?"
        )
    if category == "filename_title_capitalization_group":
        count = len(
            [
                item
                for item in finding.get("details", {}).get("renames", [])
                if str(item.get("before", ""))
                != str(item.get("after", ""))
            ]
        )
        return (
            f"Rename these {count} album files to normalize track separators "
            "and song-title capitalization now?"
        )
    try:
        return ACTION_PROMPT_QUESTIONS[category]
    except KeyError as exc:
        raise ValueError(
            f"No concrete interactive question is defined for {category}"
        ) from exc


def refresh_missing_art_sidecars(
    root: Path,
    finding: dict[str, Any],
) -> list[Path]:
    """Refresh local Front candidates immediately before prompting.

    The filesystem is authoritative here: a cover may have appeared after the
    initial audit, and a stale finding must never offer a network search while
    a usable local ``cover.*`` or ``folder.*`` already exists.
    """
    if finding.get("category") != "missing_embedded_art":
        return []
    target = safe_finding_path(root, finding)
    candidates = embeddable_front_art_candidates(target)
    details = finding.setdefault("details", {})
    details["sidecars"] = [
        str(candidate.resolve().relative_to(root.resolve()))
        for candidate in candidates
    ]
    if candidates:
        finding["severity"] = "safe_fix"
        finding["suggestion"] = (
            "Preview the existing local Front sidecar, approve it, embed it, "
            "and re-audit; no artwork download is needed."
        )
    else:
        finding["severity"] = "ask_first"
        finding["suggestion"] = (
            "Search MusicBrainz/Cover Art Archive and Bandcamp first, fall "
            "back to Discogs when configured, review every supplied artwork "
            "part, and embed only one approved Front image."
        )
    return candidates


def artwork_finding_still_needs_action(
    root: Path,
    finding: dict[str, Any],
) -> bool:
    """Re-survey live artwork state before acting on a stale initial finding."""
    category = str(finding.get("category") or "")
    if category == "missing_embedded_art":
        # A newly extracted cover still needs embedding into this particular
        # file, but its details must be refreshed before the prompt.
        refresh_missing_art_sidecars(root, finding)
        return True
    if category not in {
        "embedded_art_without_sidecar",
        "multiple_embedded_artworks",
    }:
        return True
    target = safe_finding_path(root, finding)
    # If this particular track has no local Front candidate yet, it must get
    # the first extraction prompt. Once that prompt writes cover.jpg/a
    # same-basename sidecar, later identical findings are safely skipped.
    if front_art_candidate(target) is None:
        return True
    # ``write=False`` then reports only artwork payloads genuinely absent from
    # the folder, so redundant later prompts remain suppressed.
    return bool(export_art_sidecars(target, write=False))


def preview_existing_front_sidecar(
    root: Path,
    finding: dict[str, Any],
    *,
    use_color: bool,
    preview_renderer=None,
) -> Path | None:
    """Render a confirmed local Front sidecar immediately before its prompt."""
    if finding.get("category") != "missing_embedded_art":
        return None
    sidecars = finding.get("details", {}).get("sidecars", [])
    if not sidecars:
        return None
    candidate = safe_finding_path(root, {"path": str(sidecars[0])})
    if not candidate.is_file():
        return None
    renderer = preview_renderer or render_artwork_preview
    try:
        mode = renderer(candidate, use_color=use_color)
        cover_narration(
            "👁️",
            f"Existing front-cover sidecar preview rendered with {mode}: "
            f"{candidate.name}.",
            use_color=use_color,
            color=(115, 105, 155),
            dim=True,
        )
    except Exception as exc:
        print_formatted_error(
            f"Could not preview {candidate.name}: "
            f"{type(exc).__name__}: {exc}",
            use_color,
        )
    return candidate


def render_console_report(
    data: dict[str, Any],
    max_examples: int,
    use_color: bool,
    interactive: bool = False,
) -> str:
    lines: list[str] = [""]
    counts = data["counts"]
    resolved_root = data.get("resolved_root") or data["root"]
    label_width = max(len("Audit root:"), len("Active audio:"))
    lines.extend(
        double_height_labeled_path(
            "Audit root:".ljust(label_width),
            str(resolved_root),
            use_color,
            120,
            225,
            170,
        )
    )
    lines.append("")
    lines.extend(
        double_height_report_line(
            f"{'Active audio:'.ljust(label_width)} {counts['active_audio']}"
            f"    📄 Files examined: {counts['files']}",
            use_color,
            105,
            195,
            245,
        )
    )
    lines.append("")
    file_count = rgb_text(str(counts["files"]), 255, 210, 80, use_color)
    audio_count = rgb_text(str(counts["active_audio"]), 90, 220, 245, use_color)
    lines.append(
        f"{file_count} files processed; {audio_count} audio files checked for metadata, "
        "ReplayGain, embedded plain lyrics, timed karaoke, artwork, duplicates, "
        "formats, filenames, and cleanup safety."
    )
    lines.append("")
    embedded_lines = embedded_lyrics_console_lines(data, use_color)
    if embedded_lines:
        lines.extend(embedded_lines)
        lines.append("")
    cover_lines = found_cover_art_console_lines(data, use_color)
    if cover_lines:
        lines.extend(cover_lines)
        lines.append("")

    findings = data["findings"]
    summarized = [finding for finding in findings if finding["category"] in SUMMARY_CATEGORIES]
    visible = [finding for finding in findings if finding["category"] not in SUMMARY_CATEGORIES]
    visible_counts = Counter(finding["severity"] for finding in visible)
    kept_count = len(summarized)
    severity_rows = [
        ("🚨", "Problems", visible_counts.get("problem", 0), "Must be fixed or investigated.", (255, 100, 105)),
        ("🔧", "Fixes ready", visible_counts.get("safe_fix", 0), "Concrete repairs that can be applied.", (120, 225, 140)),
        ("🧹", "Cleanup candidates", visible_counts.get("safe_cleanup", 0), "Removable items, applied only after approval.", (255, 195, 90)),
        ("⚠️", "Review needed", visible_counts.get("ask_first", 0), "Needs information or human judgment.", (230, 145, 245)),
        ("💾", "Kept files", kept_count, "Recognized support/history files being kept.", (120, 190, 245)),
        ("ℹ️", "Information", visible_counts.get("info", 0), "Context only; no action normally required.", (155, 175, 195)),
    ]
    lines.extend(double_height_traffic_section("Findings by severity", use_color))
    lines.append("")
    severity_label_width = max(len(row[1]) for row in severity_rows)
    severity_count_width = max(len(str(row[2])) for row in severity_rows)
    for emoji, label, number, explanation, color in severity_rows:
        colored_number = rgb_text(
            str(number).rjust(severity_count_width),
            *color,
            use_color,
        )
        colored_label = rgb_text(label, *color, use_color)
        label_padding = " " * (severity_label_width - len(label))
        lines.append(
            f"        {emoji} {label_padding}{colored_label}: "
            f"{colored_number} — {explanation}"
        )

    summary_counts = Counter(finding["category"] for finding in summarized)
    if summary_counts:
        lines.append("")
        lines.extend(
            double_height_gradient_section(
                "Other files detected",
                use_color,
                ((100, 255, 255), (0, 215, 235), (80, 155, 255)),
            )
        )
        lines.append("")
        count_width = max(
            len(str(number)) for number in summary_counts.values() if number
        )
        for category, (emoji, label, _noun) in SUMMARY_CATEGORIES.items():
            number = summary_counts.get(category, 0)
            if number:
                colored_number = rgb_text(
                    str(number).rjust(count_width), 120, 205, 245, use_color
                )
                if category == "json_sidecar":
                    label = (
                        f"{ANSI['italic']}JSON{ANSI['reset']} sidecars kept"
                        if use_color
                        else "JSON sidecars kept"
                    )
                elif category == "log_sidecar":
                    label = (
                        f"{ANSI['italic']}Log{ANSI['reset']} sidecars kept"
                        if use_color
                        else "Log sidecars kept"
                    )
                lines.append(f"        {emoji} {colored_number} {label}.")

    coded = [
        finding
        for finding in data["findings"]
        if finding.get("code") and finding["category"] != "missing_album"
    ]
    if coded:
        lines.append("")
        lines.extend(
            double_height_gradient_section(
                "Actions available for your approval",
                use_color,
                ((255, 250, 80), (210, 145, 0)),
            )
        )
        lines.append("")
        action_groups: list[list[dict[str, Any]]] = []
        action_lookup: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
        for candidate in coded:
            key = (
                str(candidate["category"]),
                str(candidate.get("message", "")),
                str(candidate.get("suggestion", "")),
            )
            group = action_lookup.get(key)
            if group is None:
                group = []
                action_lookup[key] = group
                action_groups.append(group)
            group.append(candidate)
        for group in action_groups[: max_examples or None]:
            finding = group[0]
            lines.append(f"        {approval_action_line(finding, use_color)}")
            lines.extend(finding_filename_columns(group, use_color))
            lines.extend(
                f"            {line}"
                for line in finding_sidecar_lines(finding, use_color)
            )
            if finding.get("suggestion"):
                lines.append(
                    f"            {suggested_text(finding, use_color)}"
                )
        if max_examples and len(coded) > max_examples:
            lines.append(f"        … {len(coded) - max_examples} more actions omitted.")

    review = [
        finding
        for finding in visible
        if (
            not finding.get("code") or finding["category"] == "missing_album"
        )
        and finding["severity"] in {"problem", "ask_first", "safe_fix", "safe_cleanup"}
    ]
    if review:
        lines.append("")
        lines.extend(
            double_height_gradient_section(
                "Detected Problems",
                use_color,
                ((255, 255, 80), (255, 175, 0)),
            )
        )
        lines.append("")
        album_findings = [
            finding for finding in review if finding["category"] == "missing_album"
        ]
        other_review = [
            finding for finding in review if finding["category"] != "missing_album"
        ]
        if album_findings:
            warning = rgb_text(
                "🏷️ ⚠️ Missing album tag detected:", 255, 255, 0, use_color
            )
            lines.append(f"        {warning}")
            if interactive:
                count = len(album_findings)
                lines.append(
                    f"            {count} file{'s' if count != 1 else ''}; "
                    "album values will be requested below."
                )
            else:
                for finding in album_findings:
                    lines.append(
                        f"            {music_filename(finding['path'], use_color)}"
                    )
        grouped_review: list[list[dict[str, Any]]] = []
        grouped_lookup: dict[tuple[str, str, str], list[dict[str, Any]]] = {}
        for candidate in other_review:
            # A category/message/suggestion triple is one repeated problem;
            # list all affected tracks underneath it instead of repeating the
            # same paragraph for every song in an album.
            key = (
                str(candidate["category"]),
                str(candidate.get("message", "")),
                str(candidate.get("suggestion", "")),
            )
            group = grouped_lookup.get(key)
            if group is None:
                group = []
                grouped_lookup[key] = group
                grouped_review.append(group)
            group.append(candidate)
        same_file_set_groups: dict[tuple[str, ...], list[list[dict[str, Any]]]] = {}
        same_file_set_order: list[tuple[str, ...]] = []
        for group in grouped_review[: max_examples or None]:
            file_set = tuple(sorted(str(item["path"]) for item in group))
            if file_set not in same_file_set_groups:
                same_file_set_groups[file_set] = []
                same_file_set_order.append(file_set)
            same_file_set_groups[file_set].append(group)
        for file_set in same_file_set_order:
            related_groups = same_file_set_groups[file_set]
            # Two diagnoses sharing exactly the same tracks belong together:
            # show both labels first, then one shared newspaper-style file list.
            for group in related_groups:
                finding = group[0]
                label_color = (
                    (255, 255, 0)
                    if finding["category"] == "missing_album"
                    else (245, 190, 105)
                )
                label = rgb_text(
                    finding_category_label(finding["category"]),
                    *label_color,
                    use_color,
                )
                lines.append(
                    f"        {label} — {warning_finding_message(finding)}:"
                )
            lines.extend(finding_filename_columns(related_groups[0], use_color))
            for group in related_groups:
                finding = group[0]
                if finding.get("suggestion"):
                    lines.append(
                        f"            {suggested_text(finding, use_color)}"
                    )
        if max_examples and len(review) > max_examples:
            lines.append(f"        … {len(review) - max_examples} more findings omitted.")

    if not coded and not review:
        lines.append("")
        lines.extend(
            double_height_plain_status(
                "✓ No fixes or manual review items found.",
                use_color,
                ((130, 245, 160), (70, 195, 135)),
            )
        )
    lines.append("")
    return "\n".join(lines) + "\n"


def colorize(text: str, color: str, enabled: bool) -> str:
    if not enabled:
        return text
    return f"{ANSI.get(color, '')}{text}{ANSI['reset']}"


def formatted_error(message: str, use_color: bool) -> str:
    """Wrap an error in three bang emoji and blink only the ERROR label."""
    detail = re.sub(r"^\s*ERROR:\s*", "", str(message), flags=re.I)
    bangs = "💥💥💥"
    if not use_color:
        return f"{bangs} ERROR: {detail} {bangs}"
    label = (
        f"{ANSI['blink']}{ANSI['bold']}\033[38;2;255;55;65m"
        f"ERROR:{ANSI['reset']}"
    )
    body = rgb_text(detail, 255, 95, 105, True)
    return f"{bangs} {label} {body} {bangs}"


def usage_header(text: str, use_color: bool) -> list[str]:
    if not use_color:
        return [text]
    ornament = "✨✱✨"
    if text.startswith(ornament) and text.endswith(ornament):
        title = text[len(ornament) : -len(ornament)].strip()
        colored_text = decorated_gradient_header(
            title,
            True,
            ((125, 245, 155), (65, 195, 135)),
            add_colon=False,
        )
    else:
        colored_text = gradient_text(
            text, True, ((125, 245, 155), (65, 195, 135))
        )
    styled = (
        f"{ANSI['bold']}"
        f"{colored_text}"
    )
    return [
        f"{ANSI_DOUBLE_HEIGHT_TOP}{styled}",
        f"{ANSI_DOUBLE_HEIGHT_BOTTOM}{styled}",
    ]


def render_usage(use_color: bool = True) -> str:
    command = lambda text: colorize(text, "bold", use_color)
    example = lambda text: colorize(text, "cyan", use_color)
    note = lambda text: colorize(text, "dim", use_color)
    try:
        configured_defaults = load_behavior_defaults()
    except Exception:
        configured_defaults = BehaviorDefaults()

    def default_badge(enabled: bool) -> str:
        answer = "Yes" if enabled else "No"
        label = f"[default = {answer}]"
        if not use_color:
            return label
        answer_color = (95, 245, 135) if enabled else (255, 105, 105)
        neutral = (255, 190, 95)
        return (
            f"{ANSI['dim']}"
            f"\033[38;2;{neutral[0]};{neutral[1]};{neutral[2]}m"
            "[default = "
            f"{ANSI['reset']}{ANSI['dim']}"
            f"\033[38;2;{answer_color[0]};{answer_color[1]};"
            f"{answer_color[2]}m{answer}"
            f"{ANSI['reset']}{ANSI['dim']}"
            f"\033[38;2;{neutral[0]};{neutral[1]};{neutral[2]}m"
            f"]{ANSI['reset']}"
        )

    def default_value_badge(value: str) -> str:
        label = f"[default = {value}]"
        if not use_color:
            return label
        return (
            f"{ANSI['dim']}\033[38;2;255;210;80m"
            f"{label}{ANSI['reset']}"
        )

    lines = [
        "",
        *usage_header("✨✱✨ audit_music_batch.py ✨✱✨", use_color),
        "",
        f"  Release {AUDIT_MUSIC_BATCH_VERSION} — {AUDIT_MUSIC_BATCH_RELEASE_DATE} — "
        f"{AUDIT_MUSIC_BATCH_RELEASE_NAME.replace('-', ' ')}",
        "",
        "Audit an incoming music folder for:",
        "",
        "  * missing or questionable title, artist, album, genre, comment, and URL tags",
        "  * missing ReplayGain track gain/peak tags",
        "  * multichannel audio and ARGT-equivalent ReplayGain repair",
        "  * missing, multiple, or sidecar-less embedded cover artwork",
        "  * missing or stale embedded plain lyrics/timed karaoke on vocal tracks",
        "  * unsupported audio formats and matching MP3/FLAC duplicates",
        "  * redundant album-artist prefixes in grouped audio/sidecar filenames",
        "  * read-only or suspiciously tiny audio and noncanonical filename markers",
        "  * active TODOs, suspicious filenames, and zero-byte files",
        "  * disposable sidecars, transcription leftovers, logs, and kept backups",
        "  * archive/do-not-play folders missing their marker or attrib.lst rules",
        "",
        "Every finding is explained. Validated lyric/karaoke embedding follows its",
        "configured automatic default; other concrete writes require your approval.",
        "Judgment calls remain visible without pretending they are executable.",
        "",
        *usage_header(
            "✨✱✨ Interactive workflow features ✨✱✨",
            use_color,
        ),
        "",
        "  * MusicBrainz/Cover Art Archive, Discogs, Bandcamp, and Apple Music/iTunes",
        "    artwork discovery; archive-backed sets retain back/inlay/disc/etc., while",
        "    every supplied part is saved but only one approved Front image is embedded",
        "  * full-console Chafa, Sixel, or ANSI artwork previews that automatically",
        "    re-render after a live window/font-size change; V opens the original",
        "  * diagnostic waveform review at 60% terminal width (80% for pre/post-bake",
        "    comparisons), with parallel background pre-rendering,",
        "    persistent approvals, keyboard-controlled audio preview, editing,",
        "    and optional problem-file renaming",
        "  * B=Bake ReplayGain changes audio for players that ignore its tags:",
        "    FLAC is losslessly re-encoded; MP3 is decoded and LAME-re-encoded",
        "    at highest VBR quality; red-to-purple before and cyan-to-green after",
        "    shown, originals are backed up, and tags are recalculated",
        "  * a default-Yes end-of-audit waveform offer: Y reviews only new waveforms, F forces all",
        "  * default detection of excessive leading, internal, or trailing silence",
        "  * comment-filtered plain/timed lyric embedding plus newer-sidecar refresh",
        "  * timestamped backups, immediate repairs, and post-write re-auditing",
        "  * rainbow progress bars and More-style single-key paging",
        "",
        *usage_header("✨✱✨ Usage ✨✱✨", use_color),
        "",
        f"  {command('audit_music_batch.py')} {example('[foldername]')} {command('[flags]')}",
        note(
            "  ^ With no arguments, a music-containing current tree (up to 5 levels) offers a run/usage menu; otherwise usage is shown. "
            "--review-waveforms alone uses the current folder."
        ),
        "",
        *usage_header("✨✱✨ Flags ✨✱✨", use_color),
        "",
        f"  {command('--interactive')}  {command('--no-interactive')}  "
        f"{default_badge(True)}",
        note("  ^ Prompt for supported actions, or suppress all action prompts."),
        "",
        f"  {command('--write-reports')}  {command('--output-dir')} "
        f"{example('FOLDER')}  {default_badge(False)}",
        note("  ^ Write JSON, Markdown, and text reports, optionally somewhere else."),
        "",
        f"  {command('--format')} {example('text|json|markdown')}  "
        f"{command('--max-examples')} {example('NUMBER')}  "
        f"{default_value_badge('text; 80 examples')}",
        note("  ^ Choose the output format and limit findings printed per section; 0 prints all."),
        "",
        f"  {command('--include-archives')}  {default_badge(False)}",
        note("  ^ Include archived/deprecated audio in active tag checks."),
        "",
        f"  {command('--embed-lyrics')}  {command('--no-embed-lyrics')}  "
        f"{default_badge(configured_defaults.embed_lyrics)}",
        note(
            "  ^ Enable or suppress comment-filtered plain-lyrics AND "
            "timed-karaoke embedding together."
        ),
        "",
        f"  {command('--refresh-embedded-lyrics')}  "
        f"{default_badge(False)}",
        note(
            "  ^ Force-refresh both plain lyrics and timed karaoke from "
            "validated sidecars, then re-audit."
        ),
        "",
        f"  {command('--find-cover')}  {command('--no-find-cover')}  "
        f"{default_badge(configured_defaults.find_cover)}",
        note(
            "  ^ Enable or suppress missing-cover lookup. Existing cover.*, "
            "folder.*, or exact unnumbered-track sidecar is previewed first; "
            "otherwise every found part is reviewed and only Front is embedded."
        ),
        "",
        f"  {command('--check-silence')}  {command('--no-silence-check')}  "
        f"{default_badge(configured_defaults.check_silence)}",
        note("  ^ Enable or suppress automatic excessive-silence analysis."),
        "",
        f"  {command('--silence-threshold')} {example('SECONDS')}  "
        f"{default_value_badge(f'{configured_defaults.silence_threshold_seconds:g} seconds')}",
        note("  ^ Flag silence strictly longer than this duration."),
        "",
        f"  {command('--review-waveforms')}  "
        f"{command('--no-review-waveforms')}  "
        f"{command('--waveform-workers')} {example('NUMBER')}  "
        f"{default_badge(False)}  {default_value_badge('8 workers')}",
        note(
            "  ^ Run waveform review directly, suppress its normal end-of-audit "
            "offer, or choose 1-8 pre-render workers; display-ready previews "
            "are prepared ahead in a bounded cache."
        ),
        note(
            "    P=Preview audio uses play_audio_file.py: arrows seek 5 seconds, "
            "Shift+arrows seek 15, and Esc/X/Q/Ctrl+W/Alt+F4/Ctrl+C/"
            "Ctrl+Break stop playback."
        ),
        note(
            "    During review, B=Bake ReplayGain applies the tagged loudness "
            "correction to the samples, keeps the original, recalculates "
            "ReplayGain, re-shows the red-to-purple original without a prompt, "
            "then displays the cyan-to-green replacement waveform."
        ),
        "",
        f"  {command('--calibrate-waveform-terminal')} {example('[AUDIO_OR_WAVEFORM]')}  "
        f"{default_badge(False)}",
        note(
            "  ^ Controlled terminal calibration: compare independent geometry signals, "
            "measure a known 100x100 Sixel raster, stream Chafa directly with a watchdog, "
            "then emit the built-in waveform Sixel in timed bounded chunks."
        ),
        "",
        f"  {command('--configure-defaults')}  {command('--show-defaults')}  "
        f"{default_badge(False)}",
        note(
            "  ^ Change persistent automatic behaviors, or display the "
            "effective values."
        ),
        "",
        f"  {command('--no-color')}  {default_badge(False)}",
        note("  ^ Disable ANSI styling."),
        "",
        f"  {command('--no-pager')}  {default_badge(False)}",
        note("  ^ Disable automatic More-style paging in an interactive console."),
        "",
        f"  {command('--unit-tests')}  {default_badge(False)}",
        note("  ^ Run disposable generated-audio tests without auditing a folder."),
        "",
        f"  {command('-h  --help')}",
        note("  ^ Show this screen."),
        "",
        *usage_header("✨✱✨ Examples ✨✱✨", use_color),
        "",
        f"  {command('audit_music_batch.py')} {example('.')}",
        note("  ^ Audit the current folder and interactively apply approved actions."),
        "",
        "  "
        + command("audit_music_batch.py")
        + " "
        + example(r"C:\soulseek\READY-FOR-TAGGING-AND-TRANSCRIBED"),
        note("  ^ Audit a specifically named folder."),
        "",
        f"  {command('audit_music_batch.py')} {example('.')} {command('--no-interactive')}",
        note("  ^ Strictly read-only: show findings without prompts or changes."),
        "",
        f"  {command('audit_music_batch.py')} {example('.')} {command('--find-cover')}",
        note(
            "  ^ Resolve missing covers by release, review all supplied art, "
            "embed only approved Front, and re-audit."
        ),
        "",
        f"  {command('audit_music_batch.py')} {example('.')} "
        f"{command('--refresh-embedded-lyrics')}",
        note(
            "  ^ Force-refresh both embedded plain lyrics and timed karaoke "
            "from their current sidecars."
        ),
        "",
        f"  {command('audit_music_batch.py --review-waveforms')}",
        note(
            "  ^ Diagnose waveforms in the current folder; previews stay "
            "in temporary staging."
        ),
        "",
        f"  {command('audit_music_batch.py --calibrate-waveform-terminal .')}",
        note(
            "  ^ Calibrate Chafa vs built-in Sixel against one real waveform in the current tree."
        ),
        "",
        f"  {command('audit_music_batch.py --unit-tests')}",
        note("  ^ Run disposable generated-audio tests; never scan a music folder."),
        "",
        note("Bare invocation shows this screen and does not audit anything."),
        "",
    ]
    return "\n".join(lines)


def console_safe_text(text: str, stream: Any | None = None) -> str:
    encoding = getattr(stream or sys.stdout, "encoding", None) or "utf-8"
    try:
        text.encode(encoding)
    except UnicodeEncodeError:
        text = text.replace("✨", "*").replace("✱", "*")
        return text.encode(encoding, errors="replace").decode(encoding, errors="replace")
    return text


def print_formatted_error(message: str, use_color: bool) -> None:
    """Print an error safely even when redirected output uses a legacy code page."""
    print(console_safe_text(formatted_error(message, use_color)))


def print_usage(use_color: bool) -> None:
    print(console_safe_text(render_usage(use_color)), end="")


def approval_prompt(
    question_text: str,
    default_yes: bool,
    use_color: bool,
    indent: str = "",
) -> str:
    question = urgent_prompt_text(question_text, use_color)
    punctuation = rgb_text("[", 255, 205, 55, use_color)
    separator = rgb_text("/", 255, 165, 45, use_color)
    closing = rgb_text("]", 255, 205, 55, use_color)
    if use_color:
        yes_style = ANSI["bold"] if default_yes else ANSI["dim"]
        no_style = ANSI["dim"] if default_yes else ANSI["bold"]
        yes = (
            f"{yes_style}\033[38;2;95;245;135m"
            f"{'Y' if default_yes else 'y'}{ANSI['reset']}"
        )
        no = (
            f"{no_style}\033[38;2;255;105;105m"
            f"{'n' if default_yes else 'N'}{ANSI['reset']}"
        )
    else:
        yes = "Y" if default_yes else "y"
        no = "n" if default_yes else "N"
    return (
        f"{indent}{question} {punctuation}{yes}{separator}{no}{closing} "
    )


def urgent_prompt_text(
    text: str,
    use_color: bool,
    *,
    faint_italic_spans: tuple[str, ...] = (),
) -> str:
    """Style a question-led prompt urgently while italicizing its key nouns."""
    if not use_color:
        return f"❓ {text}"
    base = f"{ANSI['bold']}\033[38;2;255;105;45m"
    noun_style = f"{base}{ANSI['italic']}"
    noun_alternatives = [
        re.escape(phrase)
        for phrase in sorted(PROMPT_NOUN_PHRASES, key=len, reverse=True)
    ]
    faint_alternatives = [
        re.escape(span)
        for span in sorted(
            (span for span in faint_italic_spans if span),
            key=len,
            reverse=True,
        )
    ]
    pattern = re.compile(
        "("
        + "|".join(
            faint_alternatives
            + noun_alternatives
            + [r"\([^()]+\.(?:jpe?g|png|webp|gif)\)"]
        )
        + ")",
        flags=re.IGNORECASE,
    )
    pieces = pattern.split(text)
    styled: list[str] = [base, "❓ "]
    for piece in pieces:
        if any(
            piece.casefold() == span.casefold()
            for span in faint_italic_spans
        ):
            styled.extend((varied_path(piece, use_color), base))
        elif re.fullmatch(
            r"\([^()]+\.(?:jpe?g|png|webp|gif)\)",
            piece,
            flags=re.IGNORECASE,
        ):
            styled.extend(
                (
                    f"{ANSI['dim']}{ANSI['italic']}\033[38;2;200;175;135m",
                    piece,
                    ANSI["reset"],
                    base,
                )
            )
        elif any(
            piece.casefold() == phrase.casefold()
            for phrase in PROMPT_NOUN_PHRASES
        ):
            styled.extend((noun_style, piece, ANSI["reset"], base))
        else:
            styled.append(piece)
    styled.append(ANSI["reset"])
    return "".join(styled)


def blinking_approval_prompt(prompt: str, use_color: bool) -> str:
    """Make every styled segment blink without leaving blinking enabled."""
    if not use_color:
        return prompt
    blink = ANSI["blink"]
    return blink + prompt.replace(
        ANSI["reset"], ANSI["reset"] + blink
    ) + ANSI["reset"]


def approval_answer(answer_yes: bool, use_color: bool) -> str:
    """Render the chosen answer in a stable, non-blinking success/reject color."""
    color = (95, 245, 135) if answer_yes else (255, 105, 105)
    answer = "Yes!" if answer_yes else "No!"
    if not use_color:
        return answer
    return (
        f"{ANSI['bold']}\033[38;2;{color[0]};{color[1]};{color[2]}m"
        f"{answer}{ANSI['reset']}"
    )


def settled_approval_prompt(
    question: str,
    answer_yes: bool,
    use_color: bool,
    indent: str = "",
) -> str:
    """Render a completed prompt with Yes!/No! instead of its choice block."""
    return (
        f"{indent}{urgent_prompt_text(question, use_color)} "
        f"{approval_answer(answer_yes, use_color)}"
    )


def read_single_key() -> str:
    """Read one console key without waiting for Enter."""
    if os.name == "nt":
        import msvcrt

        key = msvcrt.getwch()
        if key in {"\x00", "\xe0"}:
            scan_code = msvcrt.getwch()
            # Delete is deliberately available as a hidden equivalent of D
            # for the artwork-delete prompt. Other extended keys remain inert.
            if scan_code == "S":
                return "\x7f"
            return ""
        return key

    if sys.stdin.isatty():
        import termios
        import tty

        descriptor = sys.stdin.fileno()
        previous = termios.tcgetattr(descriptor)
        try:
            tty.setraw(descriptor)
            return sys.stdin.read(1)
        finally:
            termios.tcsetattr(descriptor, termios.TCSADRAIN, previous)

    line = sys.stdin.readline()
    return line[:1] if line else "\r"


def invalid_key_beep(
    frequency_hz: int = 100,
    duration_seconds: float = 0.2,
) -> None:
    """Reject an unsupported prompt key audibly without changing the screen."""
    if os.name == "nt":
        try:
            import winsound

            winsound.Beep(
                max(37, min(32767, int(frequency_hz))),
                max(1, round(float(duration_seconds) * 1000)),
            )
            return
        except Exception:
            pass
    try:
        sys.stderr.write("\a")
        sys.stderr.flush()
    except Exception:
        pass


def wait_for_audio_editor_space(
    *,
    use_color: bool,
    key_reader=None,
) -> None:
    """Wait for a literal Space after editing; Enter is deliberately invalid."""
    reader = key_reader or read_single_key
    question = "Finish and save the audio edit, then press SPACE to continue."
    prompt = (
        f"            {urgent_prompt_text(question, use_color)} "
        f"{rgb_text('[SPACE only — ENTER will not work]', 255, 185, 70, use_color)}"
    )
    interactive_terminal = bool(
        getattr(sys.stdout, "isatty", lambda: False)()
    )
    print(
        blinking_approval_prompt(
            prompt,
            use_color and interactive_terminal,
        ),
        end="",
        flush=True,
    )
    while True:
        key = reader()
        if key == "\x03":
            raise KeyboardInterrupt
        if key == " ":
            if interactive_terminal:
                erase_wrapped_console_text(prompt)
            else:
                print()
            cover_narration(
                "⏯️",
                "SPACE received; re-treating the edited audio file.",
                use_color=use_color,
                color=(105, 210, 170),
            )
            reset_console_pager_after_user_input()
            return
        invalid_key_beep()


def prompt_for_approval(
    question: str,
    default_yes: bool,
    use_color: bool,
    key_reader=None,
    indent: str = "",
    erase_on_no: bool = False,
    erase_on_yes: bool = False,
) -> bool:
    reader = key_reader or read_single_key
    steady_prompt = approval_prompt(question, default_yes, use_color, indent)
    interactive_terminal = bool(
        getattr(sys.stdout, "isatty", lambda: False)()
    )
    waiting_prompt = blinking_approval_prompt(
        steady_prompt, use_color and interactive_terminal
    )
    print(console_safe_text(waiting_prompt), end="", flush=True)
    while True:
        key = reader()
        if key == "\x03":
            if interactive_terminal:
                print(ANSI["reset"], end="", flush=True)
            raise KeyboardInterrupt
        if key in {"\r", "\n"}:
            if interactive_terminal:
                erase_wrapped_console_text(steady_prompt)
                if not (
                    (default_yes and erase_on_yes)
                    or (not default_yes and erase_on_no)
                ):
                    print(
                        console_safe_text(
                            f"{settled_approval_prompt(question, default_yes, use_color, indent)}"
                            f"{ANSI['erase_to_eol']}"
                        )
                    )
            else:
                print(console_safe_text(approval_answer(default_yes, use_color)))
            reset_console_pager_after_user_input()
            return default_yes
        lowered = key.lower()
        if lowered in {"y", "n"}:
            answer_yes = lowered == "y"
            if interactive_terminal:
                erase_wrapped_console_text(steady_prompt)
                if not (
                    (answer_yes and erase_on_yes)
                    or (not answer_yes and erase_on_no)
                ):
                    print(
                        console_safe_text(
                            f"{settled_approval_prompt(question, answer_yes, use_color, indent)}"
                            f"{ANSI['erase_to_eol']}"
                        )
                    )
            else:
                print(console_safe_text(approval_answer(answer_yes, use_color)))
            reset_console_pager_after_user_input()
            return answer_yes
        invalid_key_beep()


def behavior_config_path(path: Path | None = None) -> Path:
    """Return the explicit path or the configuration beside this script."""
    return Path(path) if path is not None else _SCRIPT_DIR / BEHAVIOR_CONFIG_FILENAME


def load_behavior_defaults(path: Path | None = None) -> BehaviorDefaults:
    """Load strict booleans, using built-ins when no config has been created."""
    config = behavior_config_path(path)
    if not config.is_file():
        return BehaviorDefaults()
    try:
        payload = json.loads(config.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"Could not read behavior defaults: {config}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"Behavior defaults must be a JSON object: {config}")
    values: dict[str, Any] = {}
    for key, fallback in (
        ("embed_lyrics", BUILTIN_DEFAULT_EMBED_LYRICS),
        ("find_cover", BUILTIN_DEFAULT_FIND_COVER),
        ("check_silence", BUILTIN_DEFAULT_CHECK_SILENCE),
    ):
        value = payload.get(key, fallback)
        if not isinstance(value, bool):
            raise RuntimeError(
                f"Behavior default {key!r} must be true or false: {config}"
            )
        values[key] = value
    threshold = payload.get(
        "silence_threshold_seconds",
        BUILTIN_DEFAULT_SILENCE_THRESHOLD_SECONDS,
    )
    if (
        isinstance(threshold, bool)
        or not isinstance(threshold, (int, float))
        or not 0.1 <= float(threshold) <= 3600.0
    ):
        raise RuntimeError(
            "Behavior default 'silence_threshold_seconds' must be a number "
            f"from 0.1 through 3600: {config}"
        )
    values["silence_threshold_seconds"] = float(threshold)
    return BehaviorDefaults(**values)


def configure_behavior_defaults(
    *,
    use_color: bool,
    key_reader=None,
    input_reader=None,
    path: Path | None = None,
) -> tuple[BehaviorDefaults, Path, Path | None]:
    """Prompt for, persist, back up, and verify automatic behaviors."""
    config = behavior_config_path(path)
    current = load_behavior_defaults(config)
    print(
        "\n".join(
            double_height_gradient_section(
                "Configure automatic behavior defaults",
                use_color,
                ((255, 225, 80), (95, 200, 255)),
            )
        )
    )
    print()
    embed_lyrics = prompt_for_approval(
        "Automatically embed available validated plain-lyric and timed-karaoke "
        "sidecars before each audit?",
        current.embed_lyrics,
        use_color,
        key_reader=key_reader,
        indent="        ",
    )
    find_cover = prompt_for_approval(
        "Automatically find, preview, and approve missing release artwork?",
        current.find_cover,
        use_color,
        key_reader=key_reader,
        indent="        ",
    )
    check_silence = prompt_for_approval(
        "Automatically detect excessive silence during the normal audit?",
        current.check_silence,
        use_color,
        key_reader=key_reader,
        indent="        ",
    )
    threshold_prompt = (
        "        "
        + urgent_prompt_text(
            "Excessive-silence threshold in seconds "
            f"(press ENTER to keep {current.silence_threshold_seconds:g}):",
            use_color,
        )
        + " "
    )
    text_reader = input_reader or input
    try:
        entered_threshold = text_reader(threshold_prompt).strip()
    except EOFError:
        entered_threshold = ""
    reset_console_pager_after_user_input()
    silence_threshold_seconds = current.silence_threshold_seconds
    if entered_threshold:
        try:
            silence_threshold_seconds = float(entered_threshold)
        except ValueError as exc:
            raise ValueError(
                "Silence threshold must be a number of seconds"
            ) from exc
        if not 0.1 <= silence_threshold_seconds <= 3600.0:
            raise ValueError(
                "Silence threshold must be from 0.1 through 3600 seconds"
            )
    updated = BehaviorDefaults(
        embed_lyrics=embed_lyrics,
        find_cover=find_cover,
        check_silence=check_silence,
        silence_threshold_seconds=silence_threshold_seconds,
    )
    backup = (
        backup_before_inline_replacement(config)
        if config.is_file()
        else None
    )
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        json.dumps(
            {
                "embed_lyrics": updated.embed_lyrics,
                "find_cover": updated.find_cover,
                "check_silence": updated.check_silence,
                "silence_threshold_seconds": (
                    updated.silence_threshold_seconds
                ),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    verified = load_behavior_defaults(config)
    if verified != updated:
        raise RuntimeError(
            f"Behavior-default verification failed after writing {config}"
        )
    return updated, config, backup


def effective_behavior_flags(
    args: argparse.Namespace,
    defaults: BehaviorDefaults,
) -> BehaviorDefaults:
    """Resolve per-run force flags over persistent/built-in defaults."""
    embed_lyrics = (
        defaults.embed_lyrics
        if args.embed_lyrics is None
        else bool(args.embed_lyrics)
    )
    if getattr(args, "refresh_embedded_lyrics", False):
        embed_lyrics = True
    find_cover = (
        defaults.find_cover
        if args.find_cover is None
        else bool(args.find_cover)
    )
    check_silence = (
        defaults.check_silence
        if args.check_silence is None
        else bool(args.check_silence)
    )
    threshold = (
        defaults.silence_threshold_seconds
        if args.silence_threshold is None
        else float(args.silence_threshold)
    )
    if args.silence_threshold is not None:
        check_silence = True
    return BehaviorDefaults(
        embed_lyrics=embed_lyrics,
        find_cover=find_cover,
        check_silence=check_silence,
        silence_threshold_seconds=threshold,
    )


ACTION_SCOPE_KEYS = {
    "y": "yes",
    "n": "no",
    "a": "always",
    "v": "never",
    "f": "folder",
    "j": "folder",
    "s": "stop_folder",
    "d": "delete_art",
    "\x7f": "delete_art",
}


def action_scope_options(
    default_yes: bool,
    use_color: bool,
    *,
    allow_folder: bool = True,
    allow_always: bool = True,
    allow_stop_folder: bool = False,
    allow_delete_art: bool = False,
) -> str:
    """Render all single-key choices for a repeatable batch action."""
    yes_key = "Y" if default_yes else "y"
    no_key = "n" if default_yes else "N"
    choices = [f"{yes_key}=Yes", f"{no_key}=No"]
    if allow_always:
        choices.append("A=Always")
    if allow_stop_folder:
        choices.append("S=Not for This Folder")
    if allow_delete_art:
        choices.append("D=Delete Cover Art")
    choices.append("V=Never")
    if allow_folder:
        choices.append("F=Yes for This Folder")
    plain = "[" + " / ".join(choices) + "]"
    if not use_color:
        return plain
    chunks = [
        rgb_text("[", 255, 205, 55, True),
        rgb_text(f"{yes_key}=Yes", 95, 245, 135, True),
        rgb_text(" / ", 255, 165, 45, True),
        rgb_text(f"{no_key}=No", 255, 105, 105, True),
    ]
    if allow_always:
        chunks.extend([
            rgb_text(" / ", 255, 165, 45, True),
            rgb_text("A=Always", 255, 225, 80, True),
        ])
    if allow_stop_folder:
        chunks.extend([
            rgb_text(" / ", 255, 165, 45, True),
            rgb_text("S=Not for This Folder", 255, 205, 95, True),
        ])
    if allow_delete_art:
        chunks.extend([
            rgb_text(" / ", 255, 165, 45, True),
            rgb_text("D=Delete Cover Art", 255, 105, 105, True),
        ])
    chunks.extend([
        rgb_text(" / ", 255, 165, 45, True),
        rgb_text("V=Never", 255, 145, 80, True),
    ])
    if allow_folder:
        chunks.extend(
            [
                rgb_text(" / ", 255, 165, 45, True),
                rgb_text("F=Yes for This Folder", 145, 215, 255, True),
            ]
        )
    chunks.append(rgb_text("]", 255, 205, 55, True))
    return "".join(chunks)


def action_scope_prompt(
    question: str,
    default_yes: bool,
    use_color: bool,
    indent: str = "",
    *,
    allow_folder: bool = True,
    allow_always: bool = True,
    allow_stop_folder: bool = False,
    allow_delete_art: bool = False,
) -> str:
    """Build the urgent repeatable-action prompt."""
    return prompt_with_option_legend(
        urgent_prompt_text(question, use_color),
        action_scope_options(
            default_yes,
            use_color,
            allow_folder=allow_folder,
            allow_always=allow_always,
            allow_stop_folder=allow_stop_folder,
            allow_delete_art=allow_delete_art,
        ),
        indent=indent,
    )


def action_scope_answer(choice: str, use_color: bool) -> str:
    """Render the stable answer replacing a repeatable prompt's options."""
    labels = {
        "yes": ("Yes!", (95, 245, 135)),
        "no": ("No!", (255, 105, 105)),
        "always": ("Always!", (255, 225, 80)),
        "never": ("Never!", (255, 125, 80)),
        "folder": ("All in This Folder!", (145, 215, 255)),
        "stop_folder": ("Not for This Folder!", (255, 205, 95)),
        "delete_art": ("Cover Art Recycled!", (255, 105, 105)),
    }
    label, color = labels[choice]
    if not use_color:
        return label
    return (
        f"{ANSI['bold']}\033[38;2;{color[0]};{color[1]};{color[2]}m"
        f"{label}{ANSI['reset']}"
    )


def settled_action_scope_prompt(
    question: str,
    choice: str,
    use_color: bool,
    indent: str = "",
) -> str:
    """Render a completed repeatable prompt without its old option block."""
    return (
        f"{indent}{urgent_prompt_text(question, use_color)} "
        f"{action_scope_answer(choice, use_color)}"
    )


def prompt_for_action_scope(
    question: str,
    default_yes: bool,
    use_color: bool,
    key_reader=None,
    indent: str = "",
    *,
    allow_folder: bool = True,
    allow_always: bool = True,
    allow_stop_folder: bool = False,
    allow_delete_art: bool = False,
) -> str:
    """Read Y/N/Always/Never/Folder with one key and no required Enter."""
    reader = key_reader or read_single_key
    steady_prompt = action_scope_prompt(
        question,
        default_yes,
        use_color,
        indent,
        allow_folder=allow_folder,
        allow_always=allow_always,
        allow_stop_folder=allow_stop_folder,
        allow_delete_art=allow_delete_art,
    )
    interactive_terminal = bool(
        getattr(sys.stdout, "isatty", lambda: False)()
    )
    print(
        blinking_approval_prompt(
            steady_prompt,
            use_color and interactive_terminal,
        ),
        end="",
        flush=True,
    )
    while True:
        key = reader()
        if key == "\x03":
            if interactive_terminal:
                print(ANSI["reset"], end="", flush=True)
            raise KeyboardInterrupt
        if key in {"\r", "\n"}:
            choice = "yes" if default_yes else "no"
        else:
            choice = ACTION_SCOPE_KEYS.get(key.casefold())
            if (
                choice is None
                or (choice == "folder" and not allow_folder)
                or (choice == "always" and not allow_always)
                or (choice == "stop_folder" and not allow_stop_folder)
                or (choice == "delete_art" and not allow_delete_art)
            ):
                invalid_key_beep()
                continue
        if interactive_terminal:
            erase_wrapped_console_text(steady_prompt)
            print(
                f"{settled_action_scope_prompt(question, choice, use_color, indent)}"
                f"{ANSI['erase_to_eol']}"
            )
        else:
            print(action_scope_answer(choice, use_color))
        reset_console_pager_after_user_input()
        return choice


def safe_finding_path(root: Path, finding: dict[str, Any]) -> Path:
    target = (root / finding["path"]).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"Refusing action outside audited root: {target}") from exc
    return target


def set_album_tag(path: Path, album: str) -> tuple[str, Path]:
    value = album.strip()
    if not value:
        raise ValueError("Album value cannot be blank")
    backup = backup_before_inline_replacement(path)
    if path.suffix.lower() == ".flac":
        audio = FLAC(path)
        set_flac_value(audio, "ALBUM", value)
        audio.save()
        written = [str(item) for item in FLAC(path).get("ALBUM", [])]
    else:
        audio = ensure_id3(path)
        audio.tags.delall("TALB")
        audio.tags.add(TALB(encoding=3, text=[value]))
        audio.save(v2_version=3)
        verified = ensure_id3(path)
        written = [
            str(item)
            for frame in verified.tags.getall("TALB")
            for item in getattr(frame, "text", [])
        ]
    if written != [value]:
        raise RuntimeError(f"Album verification failed; read back {written!r}")
    return value, backup


def prompt_for_album_tag(
    root: Path,
    finding: dict[str, Any],
    use_color: bool,
    input_reader=None,
) -> list[str]:
    target = safe_finding_path(root, finding)
    folder_prefix = "            📁 Folder: "
    folder_width = max(
        12,
        visible_console_size().columns - visible_cell_width(folder_prefix),
    )
    folder_text = middle_ellipsize(str(target.parent), folder_width)
    print(f"{folder_prefix}{varied_path(folder_text, use_color)}")
    print(f"            {music_filename(finding['path'], use_color)}")
    prompt = (
        "            "
        + urgent_prompt_text(
            "Album value (press ENTER to leave unchanged):",
            use_color,
        )
        + " "
    )
    text_reader = input_reader or input
    try:
        value = text_reader(prompt).strip()
    except EOFError:
        value = ""
    reset_console_pager_after_user_input()
    if not value:
        print(
            colorize(
                "            ❌ Unchanged — no album tag was added.", "dim", use_color
            )
        )
        return []
    written, backup = set_album_tag(target, value)
    print(
        colorize(
            f'            ✅ Added and verified ALBUM="{written}".', "green", use_color
        )
    )
    return [f"backup:{backup}", f"album:{written}"]


PUNK_GENRE_KEEP_EXISTING = "__keep_existing__"


def set_genre_tag(path: Path, genre: str) -> tuple[str, Path]:
    """Back up, write exactly one genre value, and verify it by reading it back."""
    value = str(genre).strip()
    if not value:
        raise ValueError("Genre value cannot be blank")
    backup = backup_before_inline_replacement(path)
    if path.suffix.casefold() == ".flac":
        audio = FLAC(path)
        audio["GENRE"] = [value]
        audio.save()
        written = [str(item) for item in FLAC(path).get("GENRE", [])]
    else:
        audio = ensure_id3(path)
        audio.tags.delall("TCON")
        audio.tags.add(TCON(encoding=3, text=[value]))
        audio.save(v2_version=3)
        verified = ensure_id3(path)
        written = [
            str(item)
            for frame in verified.tags.getall("TCON")
            for item in getattr(frame, "text", [])
        ]
    if written != [value]:
        raise RuntimeError(f"Genre verification failed; read back {written!r}")
    return value, backup


def punk_genre_menu_values(finding: dict[str, Any]) -> tuple[list[str], str]:
    """Return selectable simplified values plus the human-readable original tag."""
    details = finding.get("details", {})
    genres = [
        str(item).strip()
        for item in details.get("genres", [])
        if str(item).strip()
    ]
    components = [
        str(item).strip()
        for item in details.get("genre_components", [])
        if str(item).strip()
    ] or split_genre_components(genres)
    choices = ["Punk"]
    seen = {"punk"}
    for component in components:
        key = component.casefold()
        if key in seen:
            continue
        seen.add(key)
        choices.append(component)
    existing_text = " / ".join(genres) if genres else "(current tag unavailable)"
    return choices, existing_text


def prompt_for_punk_genre_selection(
    finding: dict[str, Any],
    *,
    use_color: bool,
    input_reader=None,
) -> str:
    """Choose Punk, one existing component, or keep the entire current tag."""
    choices, existing_text = punk_genre_menu_values(finding)
    print(
        rgb_text(
            "            🎸 Choose the replacement genre:",
            255,
            220,
            85,
            use_color,
        )
    )
    for index, value in enumerate(choices, start=1):
        default_note = "  ← ENTER default" if index == 1 else ""
        print(f"                {index}) {value}{default_note}")
    keep_index = len(choices) + 1
    print(
        f"                {keep_index}) Keep whole existing tag unchanged: "
        f"{existing_text}"
    )
    reader = input_reader or input
    while True:
        try:
            entered = reader("            ❓ Selection [ENTER=Punk]: ").strip()
        except EOFError:
            entered = ""
        reset_console_pager_after_user_input()
        if not entered:
            return "Punk"
        if entered.isdigit():
            selected = int(entered)
            if 1 <= selected <= len(choices):
                return choices[selected - 1]
            if selected == keep_index:
                return PUNK_GENRE_KEEP_EXISTING
        invalid_key_beep()


def prompt_remember_punk_genre_selection(
    selected: str,
    *,
    use_color: bool,
    key_reader=None,
) -> str:
    """Choose whether a genre choice is one-off, folder-scoped, or global."""
    reader = key_reader or read_single_key
    selected_label = (
        "keep each file's whole existing tag"
        if selected == PUNK_GENRE_KEEP_EXISTING
        else f'use genre "{selected}"'
    )
    question = f"Remember this choice ({selected_label}) for later punk-family findings?"
    legend = "[N=No / F=Yes for Rest of Folder / A=Always]"
    prompt = (
        "            "
        + urgent_prompt_text(question, use_color)
        + " "
        + rgb_text(legend, 255, 205, 70, use_color)
    )
    interactive_terminal = bool(
        getattr(sys.stdout, "isatty", lambda: False)()
    )
    print(
        blinking_approval_prompt(prompt, use_color and interactive_terminal),
        end="",
        flush=True,
    )
    while True:
        key = reader()
        if key == "\x03":
            raise KeyboardInterrupt
        lowered = key.casefold()
        if key in {"", "\r", "\n"} or lowered == "n":
            scope = "none"
            answer = "No!"
            break
        if lowered == "f":
            scope = "folder"
            answer = "Yes for Rest of Folder!"
            break
        if lowered == "a":
            if prompt_for_approval(
                "Are you sure? Always will reuse this genre choice for every "
                "remaining punk-family genre finding in this run.",
                default_yes=False,
                use_color=use_color,
                key_reader=key_reader,
                indent="            ",
            ):
                scope = "always"
                answer = "Always!"
                break
            # A declined Always confirmation returns to this scope prompt.
            print(
                blinking_approval_prompt(
                    prompt, use_color and interactive_terminal
                ),
                end="",
                flush=True,
            )
            continue
        invalid_key_beep()
    if interactive_terminal:
        erase_wrapped_console_text(prompt)
    else:
        print()
    print(
        "            "
        + urgent_prompt_text(question, use_color)
        + " "
        + rgb_text(
            answer,
            *(
                (145, 215, 255)
                if scope == "folder"
                else (255, 225, 80)
                if scope == "always"
                else (255, 105, 105)
            ),
            use_color,
        )
    )
    reset_console_pager_after_user_input()
    return scope


def read_text_and_encoding(path: Path) -> tuple[str, str]:
    """Decode text while retaining the encoding needed for a safe rewrite."""
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        return data.decode("utf-8-sig"), "utf-8-sig"
    for encoding in ("utf-8", "cp1252"):
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return data.decode(errors="replace"), "utf-8"


def apply_redundant_album_artist_filename_group(
    root: Path,
    finding: dict[str, Any],
) -> list[str]:
    """Atomically rename one album group and update local playlist references."""
    root = root.resolve()
    album_folder = safe_finding_path(root, finding)
    if not album_folder.is_dir():
        raise NotADirectoryError(f"Album folder is missing: {album_folder}")

    mappings: list[tuple[Path, Path]] = []
    for item in finding.get("details", {}).get("renames", []):
        source = Path(os.path.abspath(root / item["before"]))
        destination = Path(os.path.abspath(root / item["after"]))
        for candidate in (source, destination):
            try:
                candidate.relative_to(root)
            except ValueError as exc:
                raise ValueError(
                    f"Refusing grouped rename outside audited root: {candidate}"
                ) from exc
        if source.parent != album_folder or destination.parent != album_folder:
            raise ValueError(
                "Grouped album rename may only change immediate-child filenames"
            )
        mappings.append((source, destination))

    if not mappings:
        raise RuntimeError("Grouped album rename contains no files")
    destinations = [str(destination).casefold() for _source, destination in mappings]
    if len(destinations) != len(set(destinations)):
        raise FileExistsError("Grouped album rename proposes duplicate destinations")
    for source, destination in mappings:
        if not source.is_file():
            raise FileNotFoundError(f"Grouped rename source is missing: {source}")
        same_logical_path = (
            os.path.normcase(str(source))
            == os.path.normcase(str(destination))
        )
        if destination.exists() and not same_logical_path:
            raise FileExistsError(
                f"Refusing grouped rename collision: {destination}"
            )

    name_changes = {
        source.name: destination.name
        for source, destination in mappings
        if source.suffix.lower() in AUDIO_EXTS
    }
    playlist_updates: list[tuple[Path, str, str, str]] = []
    for relative in finding.get("details", {}).get("playlists", []):
        playlist = (root / relative).resolve()
        try:
            playlist.relative_to(root)
        except ValueError as exc:
            raise ValueError(
                f"Refusing playlist update outside audited root: {playlist}"
            ) from exc
        if not playlist.is_file() or playlist.parent != album_folder:
            raise FileNotFoundError(f"Album playlist is missing: {playlist}")
        original, encoding = read_text_and_encoding(playlist)
        updated = original
        for before_name, after_name in name_changes.items():
            updated = re.sub(
                re.escape(before_name),
                lambda _match, replacement=after_name: replacement,
                updated,
                flags=re.I,
            )
        if updated != original:
            playlist_updates.append(
                (playlist, original, updated, encoding)
            )

    actions: list[str] = []
    for playlist, _original, _updated, _encoding in playlist_updates:
        backup = backup_before_inline_replacement(playlist)
        actions.append(f"backup:{backup}")

    staged: list[tuple[Path, Path, Path]] = []
    finalized: list[tuple[Path, Path, Path]] = []
    try:
        for index, (source, destination) in enumerate(mappings, start=1):
            temporary = collision_safe_path(
                album_folder
                / f".audit_music_batch-rename-{index:04d}.tmp"
            )
            source.rename(temporary)
            staged.append((source, temporary, destination))
        for source, temporary, destination in staged:
            temporary.rename(destination)
            finalized.append((source, temporary, destination))
        for playlist, _original, updated, encoding in playlist_updates:
            playlist.write_text(updated, encoding=encoding)
    except Exception:
        for playlist, original, _updated, encoding in playlist_updates:
            try:
                playlist.write_text(original, encoding=encoding)
            except Exception:
                pass
        for source, _temporary, destination in reversed(finalized):
            try:
                if destination.exists() and not source.exists():
                    destination.rename(source)
            except Exception:
                pass
        finalized_temporaries = {
            temporary for _source, temporary, _destination in finalized
        }
        for source, temporary, _destination in reversed(staged):
            if temporary in finalized_temporaries:
                continue
            try:
                if temporary.exists() and not source.exists():
                    temporary.rename(source)
            except Exception:
                pass
        raise

    actions.append(f"renamed_group:{len(mappings)} files")
    if playlist_updates:
        actions.append(f"updated_playlists:{len(playlist_updates)}")
    return actions


def apply_finding(
    root: Path,
    finding: dict[str, Any],
    use_color: bool = True,
    key_reader=None,
    input_reader=None,
) -> list[str]:
    category = finding["category"]
    target = safe_finding_path(root, finding)

    if category in {
        "adobe_xmp",
        "bare_marker",
        "smaller_numbered_image_duplicate",
        "stale_transcription_marker",
        "tagrename_m3u8",
        "temporary_batch_file",
        "vad_scratch_srt",
    }:
        recycled = recycle_path(target)
        return [f"recycled:{recycled}"]

    if category == "wav_remaining":
        return convert_wav_to_flac(
            target,
            use_color=use_color,
            key_reader=key_reader,
        )

    if category == "corrupted_legacy_id3_frames":
        return repair_corrupted_legacy_id3_frames(target)

    if category in {"archive_missing_attrib", "archive_incomplete_attrib"}:
        attrib = target / "attrib.lst" if target.is_dir() else target
        existing = read_text(attrib) if attrib.exists() else ""
        actions: list[str] = []
        if DO_NOT_PLAY_LINE not in existing:
            separator = "" if not existing or existing.endswith(("\n", "\r")) else "\n"
            if attrib.exists():
                backup = backup_before_inline_replacement(attrib)
                actions.append(f"backup:{backup}")
            attrib.write_text(existing + separator + DO_NOT_PLAY_LINE + "\n", encoding="utf-8")
            actions.append(f"updated:{attrib}")
        return actions or [f"unchanged:{attrib}"]

    if category == "archive_missing_marker":
        marker = target / "__ this folder is for archival purposes, and has been flagged for exclusion from common playlists __"
        marker.touch(exist_ok=True)
        return [f"created:{marker}"]

    if category in GROUPED_RENAME_CATEGORIES:
        return apply_redundant_album_artist_filename_group(root, finding)

    if category == "all_caps_album_title":
        _renamed_audio, actions = prompt_for_all_caps_album_title_rename(
            target,
            str(finding.get("details", {}).get("proposed_name") or target.name),
            use_color=use_color,
            input_reader=input_reader,
        )
        return actions

    if category in {
        "embedded_lyrics_outdated",
        "plain_lyrics_not_embedded",
        "karaoke_not_embedded",
    }:
        actions = embed_lyrics(target, write=True)
        required_action = {
            "plain_lyrics_not_embedded": "plain_lyrics",
            "karaoke_not_embedded": "synced_lyrics",
        }.get(category)
        if (
            required_action is not None
            and required_action not in actions
        ) or (
            category == "embedded_lyrics_outdated"
            and not {"plain_lyrics", "synced_lyrics"}.intersection(actions)
        ):
            sidecar = finding.get("details", {}).get("sidecar", "[unknown]")
            raise RuntimeError(
                f"Validated sidecar did not produce the required lyric refresh: "
                f"{sidecar}"
            )
        return actions

    if category == "newer_lrc_needs_srt_backfill":
        return backfill_srt_from_lrc(target)

    if category == "missing_srt_from_lrc_txt":
        affected = [
            (root / str(relative)).resolve()
            for relative in finding.get("details", {}).get("affected_files", [])
        ]
        return generate_missing_srt_sidecars(
            root,
            target,
            expected_audio_paths=affected or None,
        )

    if category == "excessive_silence":
        editor = launch_audio_editor(target)
        actions = [f"opened_editor:{editor}", f"audio:{target}"]
        actions.extend(
            retreat_edited_audio(
                target,
                use_color=use_color,
                key_reader=key_reader,
            )
        )
        return actions

    if category == "missing_replaygain":
        replaygain_folder = target if target.is_dir() else target.parent
        return apply_argt_replaygain_folder(
            replaygain_folder,
            use_color=use_color,
            stream_output=False,
        )

    if category == "missing_embedded_art":
        if front_art_candidate(target) is None:
            return find_cover_and_embed(
                target,
                use_color=use_color,
                interactive=True,
                key_reader=key_reader,
            )
        actions = apply_art(target, write=True)
        if not actions:
            raise RuntimeError("No applicable artwork action was available")
        return actions

    if category in {
        "embedded_art_without_sidecar",
        "multiple_embedded_artworks",
    }:
        actions = apply_art(target, write=True)
        if not actions:
            raise RuntimeError("No applicable artwork action was available")
        return actions

    if category == "simplify_punk_genre":
        selected = str(
            finding.get("details", {}).get("selected_genre") or "Punk"
        )
        if selected == PUNK_GENRE_KEEP_EXISTING:
            return ["unchanged:genre"]
        written, backup = set_genre_tag(target, selected)
        return [f"backup:{backup}", f"genre:{written}"]

    if category == "read_only_audio":
        os.chmod(target, target.stat().st_mode | stat.S_IWRITE)
        if is_windows_read_only(target):
            raise RuntimeError("Windows read-only attribute remained set")
        return [f"writable:{target}"]

    if category == "filename_marker_style":
        proposed_name = str(
            finding.get("details", {}).get("proposed_name")
            or canonicalized_filename(target.name)
        )
        destination = target.with_name(proposed_name)
        if destination.exists():
            raise FileExistsError(f"Refusing rename collision: {destination}")
        target.rename(destination)
        return [f"renamed:{destination}"]

    raise NotImplementedError(f"No immediate-action handler for {category}")


def find_cover_group_key(path: Path) -> tuple[str, ...]:
    """Group album tracks so ``--find-cover`` downloads one artwork set once."""
    try:
        metadata = cover_lookup_metadata(path)
    except Exception:
        return ("file", str(path.resolve()).casefold())
    release_id = str(metadata.get("release_id") or "").casefold()
    album = normalized_match_text(str(metadata.get("album") or ""))
    artist = normalized_match_text(
        str(metadata.get("album_artist") or metadata.get("artist") or "")
    )
    if release_id:
        return ("release", str(path.parent.resolve()).casefold(), release_id)
    if album and artist:
        return (
            "album",
            str(path.parent.resolve()).casefold(),
            artist,
            album,
        )
    return ("file", str(path.resolve()).casefold())


def find_covers_for_batch(
    root: Path,
    data: dict[str, Any],
    *,
    interactive: bool,
    use_color: bool,
    key_reader=None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Apply ``--find-cover`` once per release, then re-audit the whole batch."""
    root = root.resolve()
    all_missing = [
        finding
        for finding in data.get("findings", [])
        if finding.get("category") == "missing_embedded_art"
    ]
    # Existing local Front art is not a search job. Leave it in the normal
    # interactive list, which previews the exact image and asks before
    # embedding. In particular, --find-cover must not download merely because
    # the audio has not yet embedded its available cover.jpg.
    missing = [
        finding
        for finding in all_missing
        if front_art_candidate(safe_finding_path(root, finding)) is None
    ]
    if not missing:
        return [], data
    print(
        "\n"
        + "\n".join(
            double_height_gradient_section(
                "Finding cover art",
                use_color,
                ((255, 235, 80), (95, 200, 255)),
            )
        )
    )
    groups: dict[tuple[str, ...], list[Path]] = defaultdict(list)
    for finding in missing:
        target = safe_finding_path(root, finding)
        key = find_cover_group_key(target)
        if target not in groups[key]:
            groups[key].append(target)

    results: list[dict[str, Any]] = []
    for targets in groups.values():
        representative = targets[0]
        print()
        cover_narration(
            "♪",
            str(representative.relative_to(root)),
            use_color=use_color,
            color=(110, 185, 215),
            dim=True,
            italic=True,
        )
        actions: list[str] = []
        error: str | None = None
        try:
            local_candidate = front_art_candidate(representative)
            if local_candidate is not None:
                cover_narration(
                    "🖼️",
                    f"Using existing local Front artwork {local_candidate.name}; "
                    "no network image download is needed.",
                    use_color=use_color,
                    color=(150, 215, 180),
                )
                for target in targets:
                    target_actions = apply_art(target, write=True)
                    if target_actions:
                        actions.extend(target_actions)
            else:
                actions = find_cover_and_embed(
                    representative,
                    audio_targets=targets,
                    album_scope=bool(
                        recognized_album_artist(representative.parent)
                        or len(targets) > 1
                    ),
                    use_color=use_color,
                    interactive=interactive,
                    key_reader=key_reader,
                )
            if not actions:
                raise RuntimeError("No cover-art change was applied")
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            cover_narration(
                "❌",
                error,
                use_color=use_color,
                color=(255, 90, 100),
            )
        results.append(
            {
                "paths": [str(path.relative_to(root)) for path in targets],
                "actions": actions,
                "error": error,
            }
        )

    refreshed = BatchAudit(
        root,
        include_archives=bool(data.get("include_archives")),
    ).audit()
    categories = {
        finding["path"]: finding["category"]
        for finding in refreshed["findings"]
        if finding["category"] == "missing_embedded_art"
    }
    for result in results:
        if result["error"] is None:
            unresolved = [
                path for path in result["paths"] if path in categories
            ]
            if unresolved:
                result["error"] = (
                    "Post-write re-audit still reports missing embedded art: "
                    + ", ".join(unresolved)
                )
                cover_narration(
                    "❌",
                    result["error"],
                    use_color=use_color,
                    color=(255, 90, 100),
                )
            else:
                result["actions"].append("re-audit:passed")
                for line in action_result_lines(result["actions"], use_color):
                    print(line)
    return results, refreshed


def audit_categories_for_path(root: Path, relative_path: str) -> set[str]:
    """Re-audit and return the current findings for one specific audio path."""
    return audit_categories_by_path(root).get(relative_path, set())


def audit_categories_by_path(root: Path) -> dict[str, set[str]]:
    """Re-audit once and group every current finding by audio-relative path."""
    auditor = BatchAudit(root)
    refreshed = auditor.audit()
    grouped = {auditor.rel(path): set() for path in auditor.audio_files}
    for finding in refreshed["findings"]:
        grouped.setdefault(finding["path"], set()).add(finding["category"])
    return grouped


def retreat_edited_audio(
    audio_path: Path,
    *,
    use_color: bool,
    key_reader=None,
) -> list[str]:
    """Wait for editing to finish, restore embeddable data, and re-audit."""
    wait_for_audio_editor_space(
        use_color=use_color,
        key_reader=key_reader,
    )
    if not audio_path.is_file():
        raise FileNotFoundError(
            f"The edited audio file no longer exists: {audio_path}"
        )

    actions: list[str] = []
    if audio_path.suffix.casefold() in {".mp3", ".flac"}:
        actions.extend(
            apply_replaygain_file(
                audio_path,
                use_color=use_color,
                stream_output=True,
            )
        )
    else:
        cover_narration(
            "⚠️",
            f"ReplayGain was not written to {audio_path.suffix.upper() or 'this format'}; "
            "portable ReplayGain tagging is supported here only for MP3 and FLAC.",
            use_color=use_color,
            color=(255, 190, 70),
        )

    lyric_actions = embed_lyrics(audio_path, write=True)
    actions.extend(lyric_actions)
    if front_art_candidate(audio_path) is not None:
        actions.extend(apply_art(audio_path, write=True))

    relative = audio_path.name
    remaining = audit_categories_for_path(audio_path.parent, relative)
    actions.append("re-audit:passed")
    cover_narration(
        "✅",
        "Edited file re-treated and re-audited; ReplayGain, available lyrics/"
        "karaoke, and approved sidecar artwork were refreshed where supported.",
        use_color=use_color,
        color=(95, 225, 130),
    )
    if remaining:
        cover_narration(
            "⚠️",
            "Remaining review findings: " + ", ".join(sorted(remaining)),
            use_color=use_color,
            color=(255, 190, 70),
            dim=True,
        )
    return actions


def interactive_apply(
    data: dict[str, Any],
    use_color: bool,
    key_reader=None,
    input_reader=None,
    artwork_preview_renderer=None,
) -> dict[str, Any]:
    coded = [f for f in data["findings"] if f.get("code")]
    applied: list[str] = []
    skipped: list[str] = []
    failed: list[str] = []
    decisions: list[dict[str, Any]] = []
    root = Path(data["resolved_root"])
    reaudited_categories: dict[str, set[str]] = {}
    printed_prompt = False
    remembered_category_choices: dict[str, str] = {}
    remembered_folder_approvals: set[tuple[str, str]] = set()
    remembered_folder_skips: set[tuple[str, str]] = set()
    remembered_punk_genre_selection: str | None = None
    remembered_punk_genre_folder_selections: dict[str, str] = {}

    for finding in coded:
        if not artwork_finding_still_needs_action(root, finding):
            skipped.append(finding["code"])
            decisions.append(
                {
                    "code": finding["code"],
                    "applied": False,
                    "skipped": True,
                    "error": None,
                    "actions": ["already_resolved_by_prior_artwork_action"],
                    "default": True,
                    "finding": finding,
                }
            )
            continue
        lyric_action = finding["category"] in {
            "embedded_lyrics_outdated",
            "plain_lyrics_not_embedded",
            "karaoke_not_embedded",
        }
        reaudit_action = (
            lyric_action
            or finding["category"] == "missing_replaygain"
            or finding["category"] == "missing_embedded_art"
            or finding["category"] == "newer_lrc_needs_srt_backfill"
            or finding["category"] == "missing_srt_from_lrc_txt"
            or finding["category"] == "all_caps_album_title"
            or finding["category"] in GROUPED_RENAME_CATEGORIES
        )
        if (
            reaudit_action
            and finding["path"] in reaudited_categories
            and finding["category"] not in reaudited_categories[finding["path"]]
        ):
            skipped.append(finding["code"])
            decisions.append(
                {
                    "code": finding["code"],
                    "applied": False,
                    "skipped": True,
                    "error": None,
                    "actions": ["already_resolved_after_reaudit"],
                    "default": True,
                    "finding": finding,
                }
            )
            continue
        default_yes = (
            finding["severity"] in {"safe_fix", "safe_cleanup"}
            or finding["category"] == "excessive_silence"
        )
        category_label = finding_category_label(finding["category"])
        if finding["category"] == "missing_album":
            category_label += ":"
        header_stops = ((255, 250, 80), (210, 145, 0))
        print(
            ("" if not printed_prompt else "\n")
            + "        "
            + decorated_gradient_header(
                category_label,
                use_color,
                header_stops,
                add_colon=False,
            )
        )
        printed_prompt = True
        if finding["category"] != "missing_album":
            print(
                "            "
                + rgb_text(
                    warning_finding_message(finding),
                    205,
                    155,
                    45,
                    use_color,
                )
            )
        actions: list[str] = []
        error = None
        should_apply = False
        if finding["category"] == "missing_album":
            try:
                actions = prompt_for_album_tag(
                    root,
                    finding,
                    use_color,
                    input_reader=input_reader,
                )
                should_apply = bool(actions)
                if should_apply:
                    applied.append(finding["code"])
                else:
                    skipped.append(finding["code"])
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
                failed.append(finding["code"])
                print(colorize(f"            FAILED: {error}", "red", use_color))
        else:
            for line in finding_target_lines(
                finding,
                use_color,
                root=root,
            ):
                # DEC double-height mode also doubles the line width. Six
                # leading spaces therefore occupy the same visual indent as
                # the ordinary twelve-space action detail indent.
                target_indent = (
                    "      "
                    if line.startswith((ANSI_DOUBLE_HEIGHT_TOP, ANSI_DOUBLE_HEIGHT_BOTTOM))
                    else "            "
                )
                print(f"{target_indent}{line}")
            for line in finding_sidecar_lines(finding, use_color):
                print(f"            {line}")
            if finding.get("suggestion"):
                print(f"            {suggested_text(finding, use_color)}")

            if finding["category"] == "simplify_punk_genre":
                target = safe_finding_path(root, finding)
                genre_folder_key = str(target.parent.resolve()).casefold()
                selected_genre = remembered_punk_genre_selection
                remembered_scope: str | None = (
                    "always" if selected_genre is not None else None
                )
                if selected_genre is None:
                    selected_genre = remembered_punk_genre_folder_selections.get(
                        genre_folder_key
                    )
                    if selected_genre is not None:
                        remembered_scope = "folder"
                if selected_genre is None:
                    selected_genre = prompt_for_punk_genre_selection(
                        finding,
                        use_color=use_color,
                        input_reader=input_reader,
                    )
                    remember_scope = prompt_remember_punk_genre_selection(
                        selected_genre,
                        use_color=use_color,
                        key_reader=key_reader,
                    )
                    if remember_scope == "always":
                        remembered_punk_genre_selection = selected_genre
                    elif remember_scope == "folder":
                        remembered_punk_genre_folder_selections[
                            genre_folder_key
                        ] = selected_genre
                else:
                    remembered_label = (
                        "keep whole existing tag unchanged"
                        if selected_genre == PUNK_GENRE_KEEP_EXISTING
                        else selected_genre
                    )
                    scope_label = (
                        "rest of this folder"
                        if remembered_scope == "folder"
                        else "all remaining findings"
                    )
                    print(
                        rgb_text(
                            f"            🎯 Genre choice: {remembered_label} "
                            f"(remembered for {scope_label})",
                            165,
                            205,
                            235,
                            use_color,
                            dim=True,
                        )
                    )

                if selected_genre == PUNK_GENRE_KEEP_EXISTING:
                    choice = "keep_existing"
                    skipped.append(finding["code"])
                    print(
                        rgb_text(
                            "            ↪️ Kept the whole existing genre tag unchanged.",
                            185,
                            175,
                            135,
                            use_color,
                            dim=True,
                        )
                    )
                    decisions.append(
                        {
                            "code": finding["code"],
                            "applied": False,
                            "skipped": True,
                            "error": None,
                            "actions": [],
                            "default": True,
                            "choice": choice,
                            "finding": finding,
                        }
                    )
                    continue

                error = None
                actions = []
                choice = "genre_value"
                try:
                    written, backup = set_genre_tag(target, selected_genre)
                    actions = [f"backup:{backup}", f"genre:{written}"]
                    verification = BatchAudit(target.parent).tag_snapshot(target)
                    written_back = [
                        str(item).strip()
                        for item in verification.get("genre", [])
                        if str(item).strip()
                    ]
                    if written_back != [written]:
                        raise RuntimeError(
                            f"Genre post-write verification read back {written_back!r}"
                        )
                    actions.append("re-audit:passed")
                    applied.append(finding["code"])
                    for line in action_result_lines(actions, use_color):
                        print(line)
                except Exception as exc:
                    error = f"{type(exc).__name__}: {exc}"
                    failed.append(finding["code"])
                    print(colorize(f"            FAILED: {error}", "red", use_color))
                decisions.append(
                    {
                        "code": finding["code"],
                        "applied": error is None,
                        "skipped": False,
                        "error": error,
                        "actions": actions,
                        "default": True,
                        "choice": choice,
                        "finding": finding,
                    }
                )
                continue

            question = approval_question(finding)
            target = safe_finding_path(root, finding)
            folder_level = bool(
                finding.get("details", {}).get("folder_level")
            )
            scope_folder = (
                target
                if finding["category"] in GROUPED_RENAME_CATEGORIES or folder_level
                else target.parent
            )
            folder_key = (
                str(finding["category"]),
                str(scope_folder.resolve()).casefold(),
            )
            allow_folder_scope = (
                folder_level
                or finding["category"] not in ROOT_WIDE_ACTION_CATEGORIES
            )
            replaygain_scope = finding["category"] == "missing_replaygain"
            local_cover_prompt = (
                finding["category"] == "missing_embedded_art"
                and front_art_candidate(target) is not None
            )
            choice = remembered_category_choices.get(
                str(finding["category"])
            )
            if (
                choice is None
                and allow_folder_scope
                and folder_key in remembered_folder_approvals
            ):
                choice = "folder"
            if choice is None and folder_key in remembered_folder_skips:
                choice = "stop_folder"
            if choice is None:
                preview_existing_front_sidecar(
                    root,
                    finding,
                    use_color=use_color,
                    preview_renderer=artwork_preview_renderer,
                )
                while True:
                    choice = prompt_for_action_scope(
                        question,
                        default_yes,
                        use_color,
                        key_reader=key_reader,
                        indent="            ",
                        allow_folder=allow_folder_scope,
                        allow_always=True,
                        allow_stop_folder=(
                            replaygain_scope or folder_level or local_cover_prompt
                        ),
                        allow_delete_art=local_cover_prompt,
                    )
                    if choice != "always":
                        break
                    if prompt_for_approval(
                        "Are you sure? Always will automatically approve every "
                        f"remaining {friendly_category(str(finding['category']))} "
                        "action in this run without asking again.",
                        default_yes=False,
                        use_color=use_color,
                        key_reader=key_reader,
                        indent="            ",
                    ):
                        break
                if choice in {"always", "never"}:
                    remembered_category_choices[
                        str(finding["category"])
                    ] = choice
                elif choice == "folder":
                    remembered_folder_approvals.add(folder_key)
                elif choice == "stop_folder":
                    remembered_folder_skips.add(folder_key)
            else:
                print(
                    settled_action_scope_prompt(
                        question,
                        choice,
                        use_color,
                        indent="            ",
                    )
                    + rgb_text(
                        "  (remembered)",
                        165,
                        165,
                        175,
                        use_color,
                        dim=True,
                    )
                )
            should_apply = choice in {"yes", "always", "folder"}
            should_delete_art = choice == "delete_art"
            if should_apply or should_delete_art:
                try:
                    if should_delete_art:
                        artwork = front_art_candidate(target)
                        if artwork is None:
                            raise RuntimeError("The displayed local cover art no longer exists")
                        actions = [f"recycled_art:{recycle_path(artwork)}"]
                    else:
                        actions = apply_finding(
                            root,
                            finding,
                            use_color=use_color,
                            key_reader=key_reader,
                            input_reader=input_reader,
                        )
                    extracted_art_approved = True
                    if finding["category"] in {
                        "embedded_art_without_sidecar",
                        "multiple_embedded_artworks",
                    }:
                        extracted_art_approved = review_extracted_art_sidecars(
                            actions,
                            use_color=use_color,
                            key_reader=key_reader,
                            preview_renderer=artwork_preview_renderer,
                        )
                    if finding["category"] == "filename_marker_style":
                        old_path = finding["path"]
                        new_name = str(
                            finding.get("details", {}).get("proposed_name")
                            or canonicalized_filename(Path(old_path).name)
                        )
                        new_path = str(Path(old_path).with_name(new_name))
                        for pending in coded:
                            if pending["path"] == old_path:
                                pending["path"] = new_path
                    elif finding["category"] in GROUPED_RENAME_CATEGORIES:
                        renamed_paths = {
                            item["before"]: item["after"]
                            for item in finding.get("details", {}).get(
                                "renames", []
                            )
                        }
                        for pending in coded:
                            pending["path"] = renamed_paths.get(
                                pending["path"],
                                pending["path"],
                            )
                    elif finding["category"] == "all_caps_album_title":
                        old_path = finding["path"]
                        new_path = next(
                            (
                                action.removeprefix("renamed:")
                                for action in actions
                                if action.startswith("renamed:")
                            ),
                            old_path,
                        )
                        old_stem = Path(old_path).stem.casefold()
                        new_stem = Path(new_path).stem
                        for pending in coded:
                            pending_path = Path(pending["path"])
                            if pending_path.name.casefold().startswith(old_stem + "."):
                                pending["path"] = str(
                                    pending_path.with_name(
                                        new_stem + pending_path.name[len(old_stem):]
                                    )
                                )
                    if reaudit_action and extracted_art_approved and not should_delete_art:
                        if finding["category"] == "missing_embedded_art":
                            # Do not rescan the whole batch after every cover
                            # embed. The write is local and its success can be
                            # verified precisely by rereading this one file.
                            if not any(
                                picture_type == 3
                                for _data, _mime, picture_type, _description
                                in embedded_pictures(target)
                            ):
                                raise RuntimeError(
                                    "Embedded front-cover verification failed"
                                )
                        elif finding["category"] in {
                            "embedded_lyrics_outdated",
                            "plain_lyrics_not_embedded",
                            "karaoke_not_embedded",
                        }:
                            # Lyric embedding is also a local write. Re-read
                            # only this file and its sidecars; a full folder
                            # scan here made F/Always painfully repetitive.
                            pending_lyric_actions = embed_lyrics(
                                target,
                                write=False,
                                force_refresh=False,
                            )
                            if pending_lyric_actions:
                                raise RuntimeError(
                                    "Embedded lyric verification failed; still needs: "
                                    + ", ".join(pending_lyric_actions)
                                )
                        else:
                            reaudited_categories = audit_categories_by_path(root)
                            current = reaudited_categories.get(
                                finding["path"], set()
                            )
                            if finding["category"] in current:
                                raise RuntimeError(
                                    "Approved action did not pass the post-write re-audit"
                                )
                        actions.append("re-audit:passed")
                    applied.append(finding["code"])
                    for line in action_result_lines(actions, use_color):
                        print(line)
                except Exception as exc:
                    error = f"{type(exc).__name__}: {exc}"
                    failed.append(finding["code"])
                    print(colorize(f"            FAILED: {error}", "red", use_color))
            else:
                skipped.append(finding["code"])
        decisions.append(
            {
                "code": finding["code"],
                "applied": (should_apply or should_delete_art) and error is None,
                "skipped": not (should_apply or should_delete_art),
                "error": error,
                "actions": actions,
                "default": default_yes,
                "choice": (
                    "album_value"
                    if finding["category"] == "missing_album"
                    else choice
                ),
                "finding": finding,
            }
        )

    return {
        "applied_codes": "".join(applied),
        "skipped_codes": "".join(skipped),
        "failed_codes": "".join(failed),
        "decisions": decisions,
    }


def run_unit_tests(use_color: bool = True) -> int:
    """Run self-contained generated-audio tests without touching a music batch."""
    global read_single_key
    import ast
    import builtins
    import contextlib
    import datetime
    import io
    import inspect
    import linecache
    import shutil
    import subprocess
    import tempfile
    import traceback
    import unittest
    import wave
    from unittest import mock

    lyric_findings = {
        "embedded_lyrics_outdated",
        "plain_lyrics_not_embedded",
        "karaoke_not_embedded",
        "missing_plain_lyrics",
        "missing_karaoke",
        "unusable_plain_lyric_sidecar",
        "unusable_karaoke_sidecar",
    }

    def make_silent_flac(folder: Path, stem: str, channels: int = 1) -> Path:
        encoder = shutil.which("flac")
        if not encoder:
            raise unittest.SkipTest("The flac encoder is required")
        wav_path = folder / f"{stem}.wav"
        flac_path = folder / f"{stem}.flac"
        flac_input_options: list[str] = []
        if channels > 2:
            wav_path.write_bytes(b"\x00\x00" * 8000 * channels)
            flac_input_options = [
                "--force-raw-format",
                "--endian=little",
                "--sign=signed",
                "--channels",
                str(channels),
                "--bps",
                "16",
                "--sample-rate",
                "8000",
            ]
        else:
            with wave.open(str(wav_path), "wb") as output:
                output.setnchannels(channels)
                output.setsampwidth(2)
                output.setframerate(8000)
                output.writeframes(b"\x00\x00" * 8000 * channels)
        subprocess.run(
            [
                encoder,
                "--silent",
                "--force",
                *flac_input_options,
                "--output-name",
                str(flac_path),
                str(wav_path),
            ],
            check=True,
            capture_output=True,
        )
        recycle_path(wav_path)
        return flac_path

    def make_silent_mp3(folder: Path, stem: str) -> Path:
        encoder = shutil.which("ffmpeg")
        if not encoder:
            raise unittest.SkipTest("ffmpeg is required for the MP3 test")
        mp3_path = folder / f"{stem}.mp3"
        subprocess.run(
            [
                encoder,
                "-hide_banner",
                "-loglevel",
                "error",
                "-f",
                "lavfi",
                "-i",
                "anullsrc=r=44100:cl=stereo",
                "-t",
                "1",
                "-q:a",
                "7",
                str(mp3_path),
            ],
            check=True,
            capture_output=True,
        )
        return mp3_path

    def make_patterned_flac(
        folder: Path,
        stem: str,
        segments: list[tuple[float, bool]],
    ) -> Path:
        """Create alternating audible/silent mono segments for analysis tests."""
        encoder = shutil.which("flac")
        if not encoder:
            raise unittest.SkipTest("The flac encoder is required")
        sample_rate = 8000
        wav_path = folder / f"{stem}.wav"
        flac_path = folder / f"{stem}.flac"
        with wave.open(str(wav_path), "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(sample_rate)
            for seconds, silent in segments:
                sample = (
                    b"\x00\x00"
                    if silent
                    else int(12000).to_bytes(
                        2,
                        byteorder="little",
                        signed=True,
                    )
                )
                output.writeframes(
                    sample * round(sample_rate * seconds)
                )
        subprocess.run(
            [
                encoder,
                "--silent",
                "--force",
                "--output-name",
                str(flac_path),
                str(wav_path),
            ],
            check=True,
            capture_output=True,
        )
        recycle_path(wav_path)
        return flac_path

    def make_stereo_peak_flac(
        folder: Path,
        stem: str,
        left_peak: float,
        right_peak: float,
    ) -> Path:
        """Create stereo generated audio with independently known peaks."""
        encoder = shutil.which("flac")
        if not encoder:
            raise unittest.SkipTest("The flac encoder is required")
        sample_rate = 8000
        wav_path = folder / f"{stem}.wav"
        flac_path = folder / f"{stem}.flac"
        left = round(32767 * max(-1.0, min(1.0, left_peak)))
        right = round(32767 * max(-1.0, min(1.0, right_peak)))
        frame = (
            int(left).to_bytes(2, byteorder="little", signed=True)
            + int(right).to_bytes(2, byteorder="little", signed=True)
        )
        with wave.open(str(wav_path), "wb") as output:
            output.setnchannels(2)
            output.setsampwidth(2)
            output.setframerate(sample_rate)
            output.writeframes(frame * sample_rate)
        subprocess.run(
            [
                encoder,
                "--silent",
                "--force",
                "--output-name",
                str(flac_path),
                str(wav_path),
            ],
            check=True,
            capture_output=True,
        )
        recycle_path(wav_path)
        return flac_path

    def finding_categories(report: dict[str, Any]) -> set[str]:
        return {item["category"] for item in report["findings"]}

    def make_test_jpeg(
        width: int = 720,
        height: int = 720,
        color: tuple[int, int, int] = (80, 120, 180),
    ) -> bytes:
        if Image is None:
            raise unittest.SkipTest("Pillow is required for artwork tests")
        output = io.BytesIO()
        Image.new("RGB", (width, height), color).save(
            output,
            format="JPEG",
            quality=92,
        )
        return output.getvalue()

    def tag_cover_search_release(
        path: Path,
        *,
        release_id: str = "11111111-2222-3333-4444-555555555555",
        release_group_id: str = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        album: str = "Test Album",
        artist: str = "Test Artist",
        total_tracks: int = 1,
    ) -> None:
        audio = FLAC(path)
        audio["ALBUM"] = [album]
        audio["ALBUMARTIST"] = [artist]
        audio["ARTIST"] = [artist]
        audio["DATE"] = ["2020"]
        audio["TRACKNUMBER"] = [f"1/{total_tracks}"]
        if release_id:
            audio["MUSICBRAINZ_ALBUMID"] = [release_id]
        if release_group_id:
            audio["MUSICBRAINZ_RELEASEGROUPID"] = [release_group_id]
        audio.save()

    def tag_complete_vocal_flac(path: Path) -> None:
        audio = FLAC(path)
        audio["TITLE"] = ["Complete Song"]
        audio["ARTIST"] = ["Test Artist"]
        audio["ALBUM"] = ["Test Album"]
        audio["GENRE"] = ["Rock"]
        audio["REPLAYGAIN_TRACK_GAIN"] = ["-5.00 dB"]
        audio["REPLAYGAIN_TRACK_PEAK"] = ["0.900000"]
        audio["LYRICS"] = ["A line"]
        audio["UNSYNCEDLYRICS"] = ["A line"]
        audio["SYNCEDLYRICS"] = ["[00:00.00]A line"]
        picture = Picture()
        picture.type = 3
        picture.mime = "image/jpeg"
        picture.data = b"\xff\xd8\xfffront"
        audio.add_picture(picture)
        audio.save()
        path.parent.joinpath("cover.jpg").write_bytes(picture.data)

    class GeneratedAudioTests(unittest.TestCase):
        @classmethod
        def setUpClass(cls) -> None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            cls.album_test_root = (
                Path(tempfile.gettempdir())
                / f"audit_music_batch-testdata-{timestamp}"
            )
            suffix = 2
            while cls.album_test_root.exists():
                cls.album_test_root = (
                    Path(tempfile.gettempdir())
                    / f"audit_music_batch-testdata-{timestamp}-{suffix}"
                )
                suffix += 1
            cls.album_test_root.mkdir(parents=True)

        @classmethod
        def tearDownClass(cls) -> None:
            if cls.album_test_root.exists():
                recycle_path(cls.album_test_root)

        def test_embeds_plain_and_timed_lyrics_and_passes_audit(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                audio_path = make_silent_flac(root, "01 Test Song")
                audio_path.with_suffix(".txt").write_text(
                    "First line\nSecond line\n", encoding="utf-8"
                )
                audio_path.with_suffix(".lrc").write_text(
                    "[00:00.00]First line\n[00:00.50]Second line\n", encoding="utf-8"
                )
                report = BatchAudit(root).audit(embed_lyrics_first=True)
                embedded_actions = [
                    action
                    for item in report["embedded_lyrics"]
                    for action in item["actions"]
                ]
                self.assertIn("plain_lyrics", embedded_actions)
                self.assertIn("synced_lyrics", embedded_actions)
                lyric_backups = [
                    Path(action.removeprefix("backup:"))
                    for action in embedded_actions
                    if action.startswith("backup:")
                ]
                self.assertEqual(1, len(lyric_backups))
                self.assertTrue(lyric_backups[0].is_file())
                lyric_backup_tags = FLAC(lyric_backups[0])
                self.assertFalse(lyric_backup_tags.get("LYRICS"))
                self.assertFalse(lyric_backup_tags.get("SYNCEDLYRICS"))
                self.assertRegex(
                    lyric_backups[0].name,
                    r"^01 Test Song\.flac\.bak\.\d{12}"
                    r"\.replaced-by-chatgpt\.bak$",
                )
                tagged = FLAC(audio_path)
                self.assertEqual(["First line\nSecond line"], tagged["LYRICS"])
                self.assertTrue(tagged["SYNCEDLYRICS"])
                categories = {
                    item["category"]
                    for item in report["findings"]
                    if item["category"] in lyric_findings
                }
                self.assertEqual(set(), categories)
                console = render_console_report(
                    report,
                    max_examples=0,
                    use_color=False,
                )
                self.assertIn(
                    "Lyric/karaoke embedding:",
                    console,
                )
                self.assertIn(
                    "🎤 Embedding lyrics & karaoke into file:",
                    console,
                )
                self.assertIn(
                    "🔧 Applied: plain lyrics, timed karaoke",
                    console,
                )
                self.assertIn(" ♪ 01 Test Song.flac", console)
                self.assertIn("💾 Backup:", console)
                self.assertNotIn(str(root), next(
                    line for line in console.splitlines() if "💾 Backup:" in line
                ))
                self.assertIn("✔️ Re-audited in this audit pass.", console)
                markdown = render_markdown(report, max_examples=0)
                self.assertIn(
                    "## Lyrics/Karaoke Embedded by `--embed-lyrics`",
                    markdown,
                )
                self.assertIn("`01 Test Song.flac`", markdown)

        def test_lyric_comments_are_never_embedded_and_newer_sidecars_refresh(
            self,
        ) -> None:
            comment_lines = (
                "# Generated by Claire\n"
                "# Sawyer’s WhisperAI-based\n"
                "# transcription system.\n"
                "# Kill yourself, Trumpers.\n"
            )
            for suffix, maker in (
                (".flac", make_silent_flac),
                (".mp3", make_silent_mp3),
            ):
                with self.subTest(suffix=suffix), tempfile.TemporaryDirectory() as temp:
                    root = Path(temp)
                    audio_path = maker(root, f"Comment Filter {suffix[1:]}")
                    txt = audio_path.with_suffix(".txt")
                    lrc = audio_path.with_suffix(".lrc")
                    txt.write_text(
                        comment_lines + "First lyric\nSecond lyric\n",
                        encoding="utf-8",
                    )
                    lrc.write_text(
                        "[00:00.00]# Generated by Claire\n"
                        "[00:00.10]First lyric\n"
                        "[00:00.50]Second lyric\n",
                        encoding="utf-8",
                    )
                    actions = embed_lyrics(audio_path, write=True)
                    self.assertIn("plain_lyrics", actions)
                    self.assertIn("synced_lyrics", actions)

                    def embedded_payloads() -> tuple[str, str]:
                        if suffix == ".flac":
                            tagged = FLAC(audio_path)
                            return (
                                str(tagged["LYRICS"][0]),
                                str(tagged["SYNCEDLYRICS"][0]),
                            )
                        tagged = MP3(audio_path, ID3=ID3)
                        plain_frames = tagged.tags.getall("USLT")
                        synced_frames = [
                            frame
                            for frame in tagged.tags.getall("TXXX")
                            if getattr(frame, "desc", "").upper()
                            == "SYNCEDLYRICS"
                        ]
                        return (
                            str(plain_frames[0].text),
                            str(synced_frames[0].text[0]),
                        )

                    plain, synced = embedded_payloads()
                    self.assertEqual("First lyric\nSecond lyric", plain)
                    self.assertEqual(
                        "[00:00.10]First lyric\n"
                        "[00:00.50]Second lyric",
                        synced,
                    )
                    for forbidden in (
                        "Generated by",
                        "WhisperAI",
                        "Kill yourself",
                    ):
                        self.assertNotIn(forbidden, plain)
                        self.assertNotIn(forbidden, synced)
                    self.assertEqual([], embed_lyrics(audio_path, write=True))

                    time.sleep(0.02)
                    os.utime(txt, None)
                    os.utime(lrc, None)
                    stale_report = BatchAudit(root).audit()
                    stale = [
                        finding
                        for finding in stale_report["findings"]
                        if finding["category"] == "embedded_lyrics_outdated"
                    ]
                    self.assertEqual(1, len(stale))
                    reasons = [
                        reason
                        for component in stale[0]["details"]["components"]
                        for reason in component["reasons"]
                    ]
                    self.assertTrue(
                        any("regenerated" in reason for reason in reasons)
                    )

                    refreshed = BatchAudit(root).audit(embed_lyrics_first=True)
                    refreshed_actions = [
                        action
                        for item in refreshed["embedded_lyrics"]
                        for action in item["actions"]
                    ]
                    self.assertIn("plain_lyrics", refreshed_actions)
                    self.assertIn("synced_lyrics", refreshed_actions)
                    self.assertNotIn(
                        "embedded_lyrics_outdated",
                        {
                            finding["category"]
                            for finding in refreshed["findings"]
                        },
                    )

                    txt.write_text(
                        comment_lines + "Replacement lyric\n",
                        encoding="utf-8",
                    )
                    lrc.write_text(
                        "[00:00.00]# transcription system\n"
                        "[00:00.25]Replacement lyric\n",
                        encoding="utf-8",
                    )
                    changed_report = BatchAudit(root).audit()
                    self.assertIn(
                        "embedded_lyrics_outdated",
                        {
                            finding["category"]
                            for finding in changed_report["findings"]
                        },
                    )
                    stale_finding = next(
                        finding
                        for finding in changed_report["findings"]
                        if finding["category"]
                        == "embedded_lyrics_outdated"
                    )
                    with contextlib.redirect_stdout(io.StringIO()):
                        interactive_result = interactive_apply(
                            {
                                **changed_report,
                                "findings": [stale_finding],
                            },
                            use_color=False,
                            key_reader=lambda: "y",
                        )
                    self.assertEqual(
                        stale_finding["code"],
                        interactive_result["applied_codes"],
                    )
                    plain, synced = embedded_payloads()
                    self.assertEqual("Replacement lyric", plain)
                    self.assertEqual(
                        "[00:00.25]Replacement lyric",
                        synced,
                    )
                    self.assertNotIn("#", plain)
                    self.assertNotIn("#", synced)
                    self.assertNotIn(
                        "embedded_lyrics_outdated",
                        audit_categories_for_path(
                            root,
                            audio_path.relative_to(root).as_posix(),
                        ),
                    )

        def test_newer_manual_lrc_is_backfilled_with_lrc2srt_only(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                audio_path = make_silent_flac(root, "LRC Backfill")
                lrc = audio_path.with_suffix(".lrc")
                srt = audio_path.with_suffix(".srt")
                audio_path.with_suffix(".txt").write_text(
                    "Edited lyric\n", encoding="utf-8"
                )
                srt.write_text(
                    "1\n00:00:00,000 --> 00:00:02,000\nOriginal lyric\n",
                    encoding="utf-8",
                )
                lrc.write_text("[00:00.00]Edited lyric\n", encoding="utf-8")
                os.utime(srt, (10, 10))
                os.utime(lrc, (20, 20))
                report = BatchAudit(root).audit()
                finding = next(
                    item for item in report["findings"]
                    if item["category"] == "newer_lrc_needs_srt_backfill"
                )
                self.assertEqual(
                    "Regenerate this older SRT from the newer MiniLyrics LRC now?",
                    approval_question(finding),
                )
                module = sys.modules[__name__]
                tool = root / "lrc2srt.py"
                tool.write_text("# test tool\n", encoding="utf-8")

                def rewrite_srt(*_args, **_kwargs):
                    srt.write_text(
                        "NOTE claire-sawyer-lrc2srt-converter-marker: generated-from-lrc\n\n"
                        "1\n00:00:00,000 --> 00:00:02,000\nEdited lyric\n",
                        encoding="utf-8",
                    )
                    os.utime(srt, (30, 30))
                    return mock.Mock(returncode=0)

                with mock.patch.object(
                    module,
                    "lrc2srt_executable",
                    return_value=tool,
                ), mock.patch.object(
                    subprocess,
                    "run",
                    side_effect=rewrite_srt,
                ) as run, contextlib.redirect_stdout(io.StringIO()):
                    actions = apply_finding(root, finding, use_color=False)
                self.assertIn(f"backfilled_srt:{srt}", actions)
                self.assertIn("--automatic-overwrites", run.call_args.args[0])
                self.assertNotIn(
                    "newer_lrc_needs_srt_backfill",
                    finding_categories(BatchAudit(root).audit()),
                )

                # A newer LRC that merely came from this SRT is deliberately
                # ignored; it is not a MiniLyrics edit to propagate backward.
                srt.write_text(
                    "1\n00:00:00,000 --> 00:00:02,000\nDerived lyric\n",
                    encoding="utf-8",
                )
                lrc.write_text("[00:00.00]Derived lyric\n", encoding="utf-8")
                os.utime(srt, (40, 40))
                os.utime(lrc, (50, 50))
                self.assertNotIn(
                    "newer_lrc_needs_srt_backfill",
                    finding_categories(BatchAudit(root).audit()),
                )

        def test_missing_srt_runs_folder_scoped_lyric_karaoke_fix_on_enter(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                audio_path = make_silent_flac(root, "Missing SRT")
                audio_path.with_suffix(".txt").write_text(
                    "Timed lyric\n",
                    encoding="utf-8",
                )
                audio_path.with_suffix(".lrc").write_text(
                    "[00:00.00]Timed lyric\n",
                    encoding="utf-8",
                )
                report = BatchAudit(root).audit()
                finding = next(
                    item
                    for item in report["findings"]
                    if item["category"] == "missing_srt_from_lrc_txt"
                )
                self.assertEqual(
                    "Run Lyric/Karaoke Fix for this folder now?",
                    approval_question(finding),
                )
                tool = root / "lrc2srt.py"
                tool.write_text("# test tool\n", encoding="utf-8")
                expected_srt = audio_path.with_suffix(".srt")
                commands: list[tuple[list[str], dict[str, Any]]] = []

                def fake_run(command, **options):
                    commands.append((list(command), dict(options)))
                    expected_srt.write_text(
                        "NOTE claire-sawyer-lrc2srt-converter-marker: "
                        "generated-from-lrc\n\n"
                        "1\n00:00:00,000 --> 00:00:02,000\nTimed lyric\n",
                        encoding="utf-8",
                    )
                    return mock.Mock(returncode=0, stdout="MiniLyricsFix: done")

                module = sys.modules[__name__]
                keys = iter(("f", "\r"))
                with mock.patch.object(
                    module,
                    "lrc2srt_executable",
                    return_value=tool,
                ), mock.patch.object(
                    subprocess,
                    "run",
                    side_effect=fake_run,
                ), mock.patch.object(
                    module,
                    "audit_categories_by_path",
                    return_value={finding["path"]: set()},
                ), mock.patch.object(
                    module,
                    "invalid_key_beep",
                ) as beep, contextlib.redirect_stdout(io.StringIO()) as output:
                    result = interactive_apply(
                        {**report, "findings": [finding]},
                        use_color=False,
                        key_reader=lambda: next(keys),
                    )

                self.assertEqual(finding["code"], result["applied_codes"])
                self.assertTrue(result["decisions"][0]["default"])
                beep.assert_not_called()
                self.assertIn("F=Yes for This Folder", output.getvalue())
                self.assertIn("A=Always", output.getvalue())
                self.assertIn("S=Not for This Folder", output.getvalue())
                self.assertEqual(
                    [
                        sys.executable,
                        str(tool),
                        "MiniLyricsFix",
                        "--recursive",
                        "--automatic-overwrites",
                    ],
                    commands[0][0],
                )
                self.assertEqual(str(root), commands[0][1]["cwd"])
                self.assertEqual(subprocess.PIPE, commands[0][1]["stdout"])
                self.assertTrue(expected_srt.is_file())
                self.assertNotIn("MiniLyricsFix", output.getvalue())
                self.assertIn("Lyric/Karaoke Fix", output.getvalue())

        def test_refresh_embedded_lyrics_forces_plain_and_karaoke_together(
            self,
        ) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                audio_path = make_silent_flac(root, "Forced Refresh")
                audio_path.with_suffix(".txt").write_text(
                    "Plain lyric\n",
                    encoding="utf-8",
                )
                audio_path.with_suffix(".lrc").write_text(
                    "[00:00.00]Timed karaoke\n",
                    encoding="utf-8",
                )
                first_actions = embed_lyrics(audio_path, write=True)
                self.assertIn("plain_lyrics", first_actions)
                self.assertIn("synced_lyrics", first_actions)
                self.assertEqual([], embed_lyrics(audio_path, write=True))

                report = BatchAudit(root).audit(
                    embed_lyrics_first=True,
                    refresh_embedded_lyrics=True,
                )
                self.assertEqual(
                    "refresh",
                    report["embedded_lyrics_mode"],
                )
                refreshed_actions = [
                    action
                    for item in report["embedded_lyrics"]
                    for action in item["actions"]
                ]
                self.assertIn("plain_lyrics", refreshed_actions)
                self.assertIn("synced_lyrics", refreshed_actions)
                self.assertEqual(
                    2,
                    len(
                        list(
                            root.glob(
                                "Forced Refresh.flac.bak.*."
                                "replaced-by-chatgpt*.bak"
                            )
                        )
                    ),
                )
                console = render_console_report(
                    report,
                    max_examples=0,
                    use_color=False,
                )
                self.assertIn(
                    "Lyric/karaoke embedding:",
                    console,
                )
                self.assertIn(
                    "🎤 Embedding lyrics & karaoke into file:",
                    console,
                )
                self.assertIn(
                    "🔧 Applied: plain lyrics, timed karaoke",
                    console,
                )
                markdown = render_markdown(report, max_examples=0)
                self.assertIn(
                    "## Lyrics/Karaoke Refreshed by "
                    "`--refresh-embedded-lyrics`",
                    markdown,
                )
                args = parse_args(
                    [".", "--refresh-embedded-lyrics"]
                )
                self.assertTrue(args.refresh_embedded_lyrics)
                self.assertIsNone(args.embed_lyrics)
                self.assertTrue(
                    effective_behavior_flags(
                        args,
                        BehaviorDefaults(embed_lyrics=False),
                    ).embed_lyrics
                )

        def test_instrumental_is_exempt(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                make_silent_flac(root, "02 Theme [instrumental]")
                report = BatchAudit(root).audit()
                categories = {
                    item["category"]
                    for item in report["findings"]
                    if item["category"] in lyric_findings
                }
                self.assertEqual(set(), categories)

        def test_exports_all_art_but_keeps_only_front_embedded(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                audio_path = make_silent_flac(root, "03 Artwork Test")
                tagged = FLAC(audio_path)
                for picture_type, payload in (
                    (3, b"\xff\xd8\xfffront"),
                    (4, b"\xff\xd8\xffback"),
                    (6, b"\xff\xd8\xffdisc"),
                ):
                    picture = Picture()
                    picture.type = picture_type
                    picture.mime = "image/jpeg"
                    picture.data = payload
                    tagged.add_picture(picture)
                tagged.save()
                art_actions = apply_art(audio_path, write=True)
                self.assertTrue(
                    any(action.startswith("backup:") for action in art_actions)
                )
                art_backup = Path(
                    next(
                        action.removeprefix("backup:")
                        for action in art_actions
                        if action.startswith("backup:")
                    )
                )
                self.assertEqual(3, len(FLAC(art_backup).pictures))
                self.assertTrue((root / "cover.jpg").exists())
                self.assertTrue((root / "back.jpg").exists())
                self.assertTrue((root / "disc.jpg").exists())
                remaining = FLAC(audio_path).pictures
                self.assertEqual(1, len(remaining))
                self.assertEqual(3, remaining[0].type)

                misc_audio = make_silent_flac(root, "Ghosts (2023)")
                misc_tagged = FLAC(misc_audio)
                misc_picture = Picture()
                misc_picture.type = 3
                misc_picture.mime = "image/jpeg"
                misc_picture.data = b"\xff\xd8\xffmisc"
                misc_tagged.add_picture(misc_picture)
                misc_tagged.save()
                misc_exports = export_art_sidecars(misc_audio, write=True)
                self.assertEqual(
                    [str(root / "Ghosts (2023).jpg")],
                    misc_exports,
                )

        def test_exact_musicbrainz_cover_saves_all_parts_and_embeds_only_front(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                audio_path = make_silent_flac(
                    root, "01 Complete Artwork [instrumental]"
                )
                tag_cover_search_release(audio_path)
                release_id = first_text(
                    FLAC(audio_path).get("MUSICBRAINZ_ALBUMID")
                )
                image_specs = [
                    ("front", ["Front"], "", True),
                    ("back", ["Back"], "", False),
                    ("lyrics", ["Booklet"], "Lyrics pages", False),
                    ("inlay", ["Liner"], "", False),
                    ("disc", ["Medium"], "CD face", False),
                    ("matrix", ["Matrix/Runout"], "", False),
                ]

                def fake_json(url: str, *, musicbrainz: bool = False):
                    self.assertFalse(musicbrainz)
                    self.assertIn(f"/release/{release_id}", url)
                    return {
                        "images": [
                            {
                                "id": image_id,
                                "image": f"https://images.test/{image_id}.jpg",
                                "types": types,
                                "comment": comment,
                                "front": front,
                                "approved": True,
                            }
                            for image_id, types, comment, front in image_specs
                        ]
                    }

                downloaded: list[str] = []

                def fake_image(url: str):
                    downloaded.append(url)
                    color_index = len(downloaded) * 25
                    return (
                        make_test_jpeg(
                            color=(
                                color_index % 255,
                                100,
                                180,
                            )
                        ),
                        "image/jpeg",
                        url,
                    )

                progress_calls: list[dict[str, Any]] = []

                class FakeProgress:
                    def __init__(self) -> None:
                        self.updates = 0

                    def update(self, amount: int) -> None:
                        self.updates += amount

                @contextmanager
                def fake_progress_bar(**kwargs):
                    progress_calls.append(kwargs)
                    yield FakeProgress()

                output = io.StringIO()
                with mock.patch.object(
                    sys.modules[__name__],
                    "progress_bar",
                    new=fake_progress_bar,
                ), contextlib.redirect_stdout(output):
                    actions = find_cover_and_embed(
                        audio_path,
                        album_scope=True,
                        use_color=False,
                        interactive=False,
                        json_fetcher=fake_json,
                        image_fetcher=fake_image,
                    )
                self.assertEqual(len(image_specs), len(downloaded))
                for filename in (
                    "cover.jpg",
                    "back.jpg",
                    "lyrics.jpg",
                    "inlay.jpg",
                    "disc.jpg",
                    "matrix.jpg",
                ):
                    self.assertTrue(root.joinpath(filename).is_file(), filename)
                pictures = FLAC(audio_path).pictures
                self.assertEqual(1, len(pictures))
                self.assertEqual(3, pictures[0].type)
                self.assertEqual(
                    root.joinpath("cover.jpg").read_bytes(),
                    pictures[0].data,
                )
                self.assertEqual(
                    len(image_specs),
                    sum(action.startswith("saved_art:") for action in actions),
                )
                self.assertTrue(
                    any(action.startswith("backup:") for action in actions)
                )
                self.assertEqual(
                    [
                        "🎨 Finding cover art",
                        "⬇️ Downloading cover artwork",
                    ],
                    [call["description"] for call in progress_calls],
                )
                narration = output.getvalue()
                for emoji in ("🌐", "🏷️", "🎯", "🖼️", "⬇️", "🔬", "🎵"):
                    self.assertIn(emoji, narration)
                self.assertNotIn(
                    "missing_embedded_art",
                    finding_categories(BatchAudit(root).audit()),
                )

                vinyl_match = CoverMatch(
                    source="test",
                    release_id="vinyl",
                    release_group_id="",
                    artist="Artist",
                    album="Album",
                    date="",
                    country="",
                    formats=("12\" Vinyl",),
                    confidence=100,
                    exact_id=True,
                    ambiguous=False,
                    artworks=(
                        CoverArtwork(
                            "m1",
                            "https://images.test/vinyl.jpg",
                            ("Medium",),
                            "",
                            False,
                            True,
                        ),
                    ),
                )
                self.assertEqual(
                    "vinyl.jpg",
                    artwork_name_plan(
                        vinyl_match,
                        audio_path,
                        album_scope=True,
                    )[0][1],
                )

        def test_bandcamp_cover_search_uses_original_front_art(self) -> None:
            metadata = {
                "artist": "Test Artist",
                "album_artist": "Test Artist",
                "album": "Test Album",
                "date": "2024",
            }
            requested: list[str] = []

            def fake_text(url: str) -> str:
                requested.append(url)
                if "bandcamp.com/search?" in url:
                    return """
                    <li class="searchresult album">
                      <div class="heading">
                        <a href="https://testartist.bandcamp.com/album/test-album">
                          Test Album
                        </a>
                      </div>
                      <div class="subhead">album by Test Artist</div>
                    </li>
                    """
                return """
                <meta content="Test Album, by Test Artist" name="title">
                <meta property="og:image"
                      content="https://f4.bcbits.com/img/a1234567890_16.jpg">
                """

            match = bandcamp_cover_match(metadata, fake_text)
            self.assertIsNotNone(match)
            assert match is not None
            self.assertEqual("Bandcamp", match.source)
            self.assertEqual("Test Artist", match.artist)
            self.assertEqual("Test Album", match.album)
            self.assertGreaterEqual(match.confidence, 94)
            self.assertEqual(2, len(requested))
            self.assertIn("Test+Artist+Test+Album", requested[0])
            self.assertEqual(1, len(match.artworks))
            self.assertTrue(match.artworks[0].front)
            self.assertEqual(
                "https://f4.bcbits.com/img/a1234567890_0.jpg",
                match.artworks[0].url,
            )

        def test_prefixed_album_folder_uses_cover_and_grouped_rename(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                folder = Path(temp) / "[2022] Death of a Fantasy"
                folder.mkdir()
                first = folder / "Lauren Sanderson - Death of a Fantasy - 01 Hi.flac"
                second = folder / "Lauren Sanderson - Death of a Fantasy - 02 Is It Normal.flac"
                first.touch()
                second.touch()
                self.assertEqual(
                    ("Lauren Sanderson", "Death of a Fantasy"),
                    inferred_album_filename_identity(folder),
                )
                self.assertEqual("Lauren Sanderson", recognized_album_artist(folder))
                self.assertTrue(is_album_track_filename(first))
                self.assertEqual("cover", exported_art_sidecar_stem(first, 3))
                self.assertEqual(
                    "01_Hi.flac",
                    album_prefixed_filename_proposal(
                        first.name,
                        "Lauren Sanderson",
                        "Death of a Fantasy",
                        11,
                    ),
                )

        def test_itunes_cover_search_uses_largest_verified_catalog_art(self) -> None:
            metadata = {
                "artist": "Test Artist",
                "album_artist": "Test Artist",
                "album": "Test Album",
            }

            def fake_json(url: str, *, musicbrainz: bool = False):
                self.assertFalse(musicbrainz)
                self.assertIn("itunes.apple.com/search", url)
                return {
                    "results": [{
                        "collectionId": 123,
                        "collectionName": "Test Album",
                        "artistName": "Test Artist",
                        "artworkUrl100": (
                            "https://is1-ssl.mzstatic.com/image/thumb/"
                            "Music/v4/example/100x100bb.jpg"
                        ),
                        "releaseDate": "2024-01-02T08:00:00Z",
                        "country": "USA",
                    }]
                }

            match = itunes_cover_match(metadata, fake_json)
            self.assertIsNotNone(match)
            assert match is not None
            self.assertEqual("Apple Music / iTunes", match.source)
            self.assertEqual("https://is1-ssl.mzstatic.com/image/thumb/"
                             "Music/v4/example/3000x3000bb.jpg",
                             match.artworks[0].url)
            self.assertTrue(match.artworks[0].front)

        def test_cover_tls_uses_verified_context_and_archive_fallback(self) -> None:
            release_id = "fc3ceb20-88ad-491f-b8df-1a2fc4f07845"
            caa_url = f"https://coverartarchive.org/release/{release_id}"
            response = mock.MagicMock()
            response.__enter__.return_value.read.return_value = (
                b'{"images": []}'
            )
            certificate_error = URLError(
                ssl.SSLCertVerificationError(
                    1,
                    "certificate has expired",
                )
            )
            with mock.patch.object(
                sys.modules[__name__],
                "urlopen",
                side_effect=[certificate_error, response],
            ) as opened:
                payload = cover_http_get_json(caa_url)
            self.assertEqual({"images": []}, payload)
            self.assertEqual(2, opened.call_count)
            first_context = opened.call_args_list[0].kwargs["context"]
            self.assertEqual(ssl.CERT_REQUIRED, first_context.verify_mode)
            self.assertTrue(first_context.check_hostname)
            fallback_request = opened.call_args_list[1].args[0]
            self.assertEqual(
                f"https://archive.org/download/mbid-{release_id}/index.json",
                fallback_request.full_url,
            )
            self.assertEqual(
                f"https://archive.org/download/mbid-{release_id}/"
                f"mbid-{release_id}-12345.jpg",
                cover_archive_image_fallback_url(
                    f"{caa_url}/12345.jpg"
                ),
            )

        def test_fuzzy_cover_requires_confirmation_before_any_image_download(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                audio_path = make_silent_flac(
                    root, "02 Fuzzy Cover [instrumental]"
                )
                tag_cover_search_release(
                    audio_path,
                    release_id="",
                    release_group_id="",
                )
                image_downloads: list[str] = []

                def fake_json(url: str, *, musicbrainz: bool = False):
                    if musicbrainz:
                        return {
                            "releases": [
                                {
                                    "id": "fuzzy-release",
                                    "title": "Test Album",
                                    "date": "2020",
                                    "country": "US",
                                    "score": 100,
                                    "artist-credit": [
                                        {
                                            "name": "Test Artist",
                                            "joinphrase": "",
                                        }
                                    ],
                                    "release-group": {"id": "fuzzy-group"},
                                    "media": [
                                        {
                                            "format": "CD",
                                            "track-count": 1,
                                        }
                                    ],
                                }
                            ]
                        }
                    if "/release/fuzzy-release" in url:
                        return {
                            "images": [
                                {
                                    "id": "front",
                                    "image": "https://images.test/front.jpg",
                                    "types": ["Front"],
                                    "front": True,
                                    "approved": True,
                                }
                            ]
                        }
                    return None

                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    with self.assertRaisesRegex(
                        RuntimeError, "candidate was declined"
                    ):
                        find_cover_and_embed(
                            audio_path,
                            album_scope=True,
                            use_color=False,
                            interactive=True,
                            key_reader=lambda: "n",
                            json_fetcher=fake_json,
                            image_fetcher=lambda url: (
                                image_downloads.append(url)
                                or (make_test_jpeg(), "image/jpeg", url)
                            ),
                        )
                self.assertEqual([], image_downloads)
                self.assertIn(
                    "Download and review this 1-image artwork set "
                    "(cover.jpg), then embed only cover.jpg as its "
                    "Front image?",
                    output.getvalue(),
                )
                self.assertIn("No!", output.getvalue())
                self.assertFalse(root.joinpath("cover.jpg").exists())
                self.assertEqual([], FLAC(audio_path).pictures)

        def test_invalid_downloaded_front_is_rejected_without_embedding(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                audio_path = make_silent_flac(
                    root, "03 Invalid Cover [instrumental]"
                )
                tag_cover_search_release(audio_path)

                def fake_json(url: str, *, musicbrainz: bool = False):
                    return {
                        "images": [
                            {
                                "id": "front",
                                "image": "https://images.test/not-image.jpg",
                                "types": ["Front"],
                                "front": True,
                                "approved": True,
                            }
                        ]
                    }

                with contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaisesRegex(
                        RuntimeError, "non-image content type"
                    ):
                        find_cover_and_embed(
                            audio_path,
                            album_scope=True,
                            use_color=False,
                            interactive=False,
                            json_fetcher=fake_json,
                            image_fetcher=lambda url: (
                                b"<html>not an image</html>",
                                "text/html",
                                url,
                            ),
                        )
                self.assertFalse(root.joinpath("cover.jpg").exists())
                self.assertEqual([], FLAC(audio_path).pictures)

        def test_missing_cover_interactive_yes_searches_embeds_and_reaudits(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                audio_path = make_silent_flac(
                    root, "04 Interactive Cover [instrumental]"
                )
                tag_cover_search_release(audio_path)
                finding = next(
                    item
                    for item in BatchAudit(root).audit()["findings"]
                    if item["category"] == "missing_embedded_art"
                )

                def fake_json(url: str, *, musicbrainz: bool = False):
                    return {
                        "images": [
                            {
                                "id": "front",
                                "image": "https://images.test/front.jpg",
                                "types": ["Front"],
                                "front": True,
                                "approved": True,
                            }
                        ]
                    }

                output = io.StringIO()
                module = sys.modules[__name__]
                with mock.patch.object(
                    module,
                    "cover_http_get_json",
                    side_effect=fake_json,
                ), mock.patch.object(
                    module,
                    "cover_http_get_bytes",
                    side_effect=lambda url: (
                        make_test_jpeg(),
                        "image/jpeg",
                        url,
                    ),
                ), mock.patch.object(
                    module,
                    "render_artwork_preview",
                    return_value="mock ANSI symbols",
                ), contextlib.redirect_stdout(output):
                    result = interactive_apply(
                        {
                            "findings": [finding],
                            "resolved_root": str(root),
                        },
                        use_color=False,
                        key_reader=lambda: "y",
                    )
                self.assertFalse(result["failed_codes"], result)
                self.assertTrue(root.joinpath("cover.jpg").is_file())
                self.assertEqual(1, len(FLAC(audio_path).pictures))
                self.assertIn("🌐 Searching exact MusicBrainz", output.getvalue())
                self.assertIn("✔️ Re-audit: passed", output.getvalue())
                self.assertNotIn(
                    "missing_embedded_art",
                    audit_categories_for_path(root, audio_path.name),
                )

        def test_find_cover_batch_downloads_one_release_set_for_all_tracks(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                album = root / "Test Artist" / "2020 - Test Album"
                album.mkdir(parents=True)
                tracks = [
                    make_silent_flac(album, "01 First [instrumental]"),
                    make_silent_flac(album, "02 Second [instrumental]"),
                ]
                for index, track in enumerate(tracks, start=1):
                    tag_cover_search_release(track, total_tracks=2)
                    tagged = FLAC(track)
                    tagged["TRACKNUMBER"] = [f"{index}/2"]
                    tagged.save()

                def fake_json(url: str, *, musicbrainz: bool = False):
                    return {
                        "images": [
                            {
                                "id": "front",
                                "image": "https://images.test/front.jpg",
                                "types": ["Front"],
                                "front": True,
                                "approved": True,
                            },
                            {
                                "id": "back",
                                "image": "https://images.test/back.jpg",
                                "types": ["Back"],
                                "front": False,
                                "approved": True,
                            },
                        ]
                    }

                image_calls: list[str] = []
                module = sys.modules[__name__]
                initial = BatchAudit(root).audit()
                cover_output = io.StringIO()
                with mock.patch.object(
                    module,
                    "cover_http_get_json",
                    side_effect=fake_json,
                ), mock.patch.object(
                    module,
                    "cover_http_get_bytes",
                    side_effect=lambda url: (
                        image_calls.append(url)
                        or (make_test_jpeg(), "image/jpeg", url)
                    ),
                ), contextlib.redirect_stdout(cover_output):
                    results, refreshed = find_covers_for_batch(
                        root,
                        initial,
                        interactive=False,
                        use_color=False,
                    )
                self.assertEqual(2, len(image_calls))
                self.assertTrue(album.joinpath("cover.jpg").is_file())
                self.assertTrue(album.joinpath("back.jpg").is_file())
                self.assertTrue(
                    all(len(FLAC(track).pictures) == 1 for track in tracks)
                )
                self.assertEqual(1, len(results))
                self.assertIsNone(results[0]["error"])
                self.assertIn("Finding cover art", cover_output.getvalue())
                self.assertNotIn(
                    "--find-cover artwork workflow",
                    cover_output.getvalue(),
                )
                self.assertNotIn(
                    "--find-cover release artwork",
                    cover_output.getvalue(),
                )
                self.assertIn("re-audit:passed", results[0]["actions"])
                self.assertNotIn(
                    "missing_embedded_art",
                    finding_categories(refreshed),
                )
                refreshed["found_cover_art"] = results
                self.assertIn(
                    "Artwork handled by --find-cover",
                    render_console_report(
                        refreshed,
                        max_examples=0,
                        use_color=False,
                    ),
                )
                self.assertIn(
                    "## Artwork Handled by `--find-cover`",
                    render_markdown(refreshed, max_examples=0),
                )

        def test_find_cover_defers_local_front_to_previewed_embedding(
            self,
        ) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                audio = make_silent_flac(
                    root,
                    "Local Front Priority [instrumental]",
                )
                cover = root / "cover.jpg"
                cover.write_bytes(make_test_jpeg())
                finding = next(
                    item
                    for item in BatchAudit(root).audit()["findings"]
                    if item["category"] == "missing_embedded_art"
                )
                # Simulate stale audit data to prove the prompt checks the
                # filesystem again instead of offering a network search.
                finding["details"]["sidecars"] = []
                finding["severity"] = "ask_first"
                finding["suggestion"] = "Search for release artwork."
                initial = {
                    "findings": [finding],
                    "resolved_root": str(root),
                }
                renderer = mock.Mock(return_value="mock Sixel")
                module = sys.modules[__name__]
                with mock.patch.object(
                    module,
                    "find_cover_and_embed",
                    side_effect=AssertionError(
                        "network cover search must not run with local Front art"
                    ),
                ) as network_search, contextlib.redirect_stdout(
                    io.StringIO()
                ) as output:
                    results, unchanged = find_covers_for_batch(
                        root,
                        initial,
                        interactive=True,
                        use_color=False,
                    )
                    applied = interactive_apply(
                        unchanged,
                        use_color=False,
                        key_reader=lambda: "y",
                        artwork_preview_renderer=renderer,
                    )
                self.assertEqual([], results)
                network_search.assert_not_called()
                renderer.assert_called_once_with(cover, use_color=False)
                self.assertFalse(applied["failed_codes"], applied)
                self.assertEqual(1, len(FLAC(audio).pictures))
                rendered = output.getvalue()
                self.assertIn(
                    "Embed the available front-cover sidecar (cover.jpg)",
                    rendered,
                )
                self.assertNotIn(
                    "Search for the release artwork, download",
                    rendered,
                )
                self.assertNotIn("Finding cover art", rendered)

        def test_misc_same_basename_art_is_previewed_and_embedded(
            self,
        ) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                stem = (
                    "Ghosts -- I'm Baby (by Lil Mariko) (live) "
                    "(20231027) (The Engine Rooms)"
                )
                audio = make_silent_flac(root, stem)
                sidecar = root / f"{stem}.jpg"
                sidecar.write_bytes(make_test_jpeg())
                finding = next(
                    item
                    for item in BatchAudit(root).audit()["findings"]
                    if item["category"] == "missing_embedded_art"
                )
                self.assertEqual(
                    [sidecar.name],
                    finding["details"]["sidecars"],
                )
                self.assertEqual(
                    "Embed the available front-cover sidecar "
                    f"({sidecar.name}) into this audio file now?",
                    approval_question(finding),
                )
                renderer = mock.Mock(return_value="mock Sixel")
                module = sys.modules[__name__]
                with mock.patch.object(
                    module,
                    "find_cover_and_embed",
                    side_effect=AssertionError(
                        "same-basename MISC art must prevent a download"
                    ),
                ) as network_search, contextlib.redirect_stdout(
                    io.StringIO()
                ) as output:
                    result = interactive_apply(
                        {
                            "findings": [finding],
                            "resolved_root": str(root),
                        },
                        use_color=False,
                        key_reader=lambda: "y",
                        artwork_preview_renderer=renderer,
                    )
                network_search.assert_not_called()
                renderer.assert_called_once_with(sidecar, use_color=False)
                self.assertFalse(result["failed_codes"], result)
                pictures = FLAC(audio).pictures
                self.assertEqual(1, len(pictures))
                self.assertEqual(sidecar.read_bytes(), pictures[0].data)
                rendered = output.getvalue()
                self.assertIn(sidecar.name, rendered)
                self.assertNotIn(
                    "Search for the release artwork, download",
                    rendered,
                )
                self.assertNotIn(
                    "missing_embedded_art",
                    audit_categories_for_path(root, audio.name),
                )

        def test_downloaded_artwork_preview_can_open_irfanview_then_approve(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                audio_path = make_silent_flac(
                    root, "05 Previewed Cover [instrumental]"
                )
                tag_cover_search_release(audio_path)

                def fake_json(url: str, *, musicbrainz: bool = False):
                    return {
                        "images": [
                            {
                                "id": "front",
                                "image": "https://images.test/front.jpg",
                                "types": ["Front"],
                                "front": True,
                                "approved": True,
                            }
                        ]
                    }

                previews: list[Path] = []
                views: list[Path] = []
                keys = iter(("v", "y"))
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    actions = find_cover_and_embed(
                        audio_path,
                        album_scope=True,
                        use_color=False,
                        interactive=True,
                        key_reader=lambda: next(keys),
                        json_fetcher=fake_json,
                        image_fetcher=lambda url: (
                            make_test_jpeg(),
                            "image/jpeg",
                            url,
                        ),
                        preview_renderer=lambda path, *, use_color: (
                            previews.append(path) or "mock ANSI symbols"
                        ),
                        image_viewer=lambda path: (
                            views.append(path)
                            or Path(r"C:\Mock\i_view32.exe")
                        ),
                    )
                self.assertEqual([root / "cover.jpg"], previews)
                self.assertEqual([root / "cover.jpg"], views)
                self.assertTrue(root.joinpath("cover.jpg").is_file())
                self.assertEqual(1, len(FLAC(audio_path).pictures))
                self.assertTrue(
                    any(action.startswith("embedded_art:") for action in actions)
                )
                narration = output.getvalue()
                self.assertIn(
                    "[Y=Yes/Enter | N=No | R=Refresh | V=View original]",
                    narration,
                )
                self.assertIn("Opened cover.jpg in i_view32.exe", narration)
                self.assertIn("Yes!", narration)

        def test_extracted_artwork_is_previewed_and_can_be_rejected(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                cover = root / "cover.jpg"
                back = root / "back.jpg"
                cover.write_bytes(make_test_jpeg())
                back.write_bytes(make_test_jpeg())
                actions = [
                    f"exported_art:{cover}",
                    f"exported_art:{back}",
                ]
                previews: list[Path] = []
                recycled: list[Path] = []
                module = sys.modules[__name__]
                with mock.patch.object(
                    module,
                    "recycle_path",
                    side_effect=lambda path: recycled.append(path) or path,
                ), contextlib.redirect_stdout(io.StringIO()):
                    approved = review_extracted_art_sidecars(
                        actions,
                        use_color=False,
                        key_reader=iter(("y", "n")).__next__,
                        preview_renderer=lambda path, *, use_color: (
                            previews.append(path) or "mock Sixel"
                        ),
                    )
                self.assertFalse(approved)
                self.assertEqual([cover, back], previews)
                self.assertIn("approved_extracted_art:cover.jpg", actions)
                self.assertIn(
                    "recycled_rejected_art:back.rejected-by-username.jpg",
                    actions,
                )
                self.assertEqual(
                    [root / "back.rejected-by-username.jpg"],
                    recycled,
                )

        def test_cover_review_refreshes_at_the_live_console_size(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                image_path = Path(temp) / "cover.jpg"
                image_path.write_bytes(make_test_jpeg())
                current_size = [os.terminal_size((100, 30))]
                rendered: list[os.terminal_size] = []
                keys = iter(("r", "y"))

                def preview(_path: Path, *, use_color: bool) -> str:
                    rendered.append(current_size[0])
                    return "mock ANSI symbols"

                def read_key() -> str:
                    key = next(keys)
                    if key == "r":
                        current_size[0] = os.terminal_size((150, 45))
                    return key

                module = sys.modules[__name__]
                with mock.patch.object(
                    module,
                    "visible_console_size",
                    side_effect=lambda: current_size[0],
                ), contextlib.redirect_stdout(io.StringIO()):
                    accepted = artwork_review_choice(
                        image_path,
                        label="cover.jpg",
                        use_color=False,
                        key_reader=read_key,
                        preview_renderer=preview,
                    )
                self.assertTrue(accepted)
                self.assertEqual(
                    [
                        os.terminal_size((100, 30)),
                        os.terminal_size((150, 45)),
                    ],
                    rendered,
                )

        def test_rejected_front_is_named_then_recycled_and_never_embedded(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                audio_path = make_silent_flac(
                    root, "06 Rejected Cover [instrumental]"
                )
                tag_cover_search_release(audio_path)

                def fake_json(url: str, *, musicbrainz: bool = False):
                    return {
                        "images": [
                            {
                                "id": "front",
                                "image": "https://images.test/front.jpg",
                                "types": ["Front"],
                                "front": True,
                                "approved": True,
                            }
                        ]
                    }

                mock_recycle = root / "mock-recycle-bin"
                mock_recycle.mkdir()
                recycled_names: list[str] = []

                def fake_recycle(path: Path) -> Path:
                    recycled_names.append(path.name)
                    path.replace(mock_recycle / path.name)
                    return path

                module = sys.modules[__name__]
                output = io.StringIO()
                with mock.patch.object(
                    module,
                    "recycle_path",
                    side_effect=fake_recycle,
                ), contextlib.redirect_stdout(output):
                    with self.assertRaisesRegex(
                        RuntimeError,
                        "Front artwork was rejected by username",
                    ):
                        find_cover_and_embed(
                            audio_path,
                            album_scope=True,
                            use_color=False,
                            interactive=True,
                            key_reader=lambda: "n",
                            json_fetcher=fake_json,
                            image_fetcher=lambda url: (
                                make_test_jpeg(),
                                "image/jpeg",
                                url,
                            ),
                            preview_renderer=lambda path, *, use_color: (
                                "mock ANSI symbols"
                            ),
                        )
                self.assertEqual(
                    ["cover.rejected-by-username.jpg"],
                    recycled_names,
                )
                self.assertFalse(root.joinpath("cover.jpg").exists())
                self.assertTrue(
                    mock_recycle.joinpath(
                        "cover.rejected-by-username.jpg"
                    ).is_file()
                )
                self.assertEqual([], FLAC(audio_path).pictures)
                self.assertIn("sent it to the Recycle Bin", output.getvalue())

        def test_rejected_nonfront_is_recycled_but_front_still_embeds(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                audio_path = make_silent_flac(
                    root, "07 Partial Artwork [instrumental]"
                )
                tag_cover_search_release(audio_path)

                def fake_json(url: str, *, musicbrainz: bool = False):
                    return {
                        "images": [
                            {
                                "id": "front",
                                "image": "https://images.test/front.jpg",
                                "types": ["Front"],
                                "front": True,
                                "approved": True,
                            },
                            {
                                "id": "back",
                                "image": "https://images.test/back.jpg",
                                "types": ["Back"],
                                "front": False,
                                "approved": True,
                            },
                        ]
                    }

                mock_recycle = root / "mock-recycle-bin"
                mock_recycle.mkdir()

                def fake_recycle(path: Path) -> Path:
                    path.replace(mock_recycle / path.name)
                    return path

                keys = iter(("y", "n"))
                module = sys.modules[__name__]
                with mock.patch.object(
                    module,
                    "recycle_path",
                    side_effect=fake_recycle,
                ), contextlib.redirect_stdout(io.StringIO()):
                    actions = find_cover_and_embed(
                        audio_path,
                        album_scope=True,
                        use_color=False,
                        interactive=True,
                        key_reader=lambda: next(keys),
                        json_fetcher=fake_json,
                        image_fetcher=lambda url: (
                            make_test_jpeg(),
                            "image/jpeg",
                            url,
                        ),
                        preview_renderer=lambda path, *, use_color: (
                            "mock ANSI symbols"
                        ),
                    )
                self.assertTrue(root.joinpath("cover.jpg").is_file())
                self.assertFalse(root.joinpath("back.jpg").exists())
                self.assertTrue(
                    mock_recycle.joinpath(
                        "back.rejected-by-username.jpg"
                    ).is_file()
                )
                self.assertEqual(1, len(FLAC(audio_path).pictures))
                self.assertIn(
                    "recycled_rejected_art:"
                    "back.rejected-by-username.jpg",
                    actions,
                )

        def test_artwork_preview_uses_full_live_console_with_text_reserve(self) -> None:
            large = artwork_preview_geometry(
                os.terminal_size((160, 50))
            )
            self.assertEqual(12, large.indent_columns)
            self.assertEqual(146, large.columns)
            self.assertEqual(43, large.rows)
            self.assertEqual(1022, large.pixel_width)
            self.assertEqual(602, large.pixel_height)

            small = artwork_preview_geometry(
                os.terminal_size((20, 8))
            )
            self.assertEqual(10, small.indent_columns)
            self.assertEqual(8, small.columns)
            self.assertEqual(4, small.rows)
            self.assertEqual(56, small.pixel_width)
            self.assertEqual(56, small.pixel_height)

            module = sys.modules[__name__]
            completed = mock.Mock(
                returncode=0,
                stdout=b"preview\n",
                stderr=b"",
            )
            with mock.patch.object(
                module,
                "chafa_executable",
                return_value=Path(r"C:\util\Chafa.exe"),
            ), mock.patch.object(
                module,
                "terminal_supports_sixel",
                return_value=True,
            ), mock.patch.object(
                module,
                "visible_console_size",
                return_value=os.terminal_size((160, 50)),
            ), mock.patch.object(
                module,
                "query_terminal_geometry",
                None,
            ), mock.patch.object(
                subprocess,
                "run",
                return_value=completed,
            ) as run, contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    "Chafa Sixel",
                    render_artwork_preview(
                        Path(r"C:\Music\cover.jpg"),
                        use_color=True,
                    ),
                )
            chafa_command = run.call_args.args[0]
            self.assertIn("--format=sixels", chafa_command)
            self.assertIn("--fit-width", chafa_command)
            self.assertIn("--colors=full", chafa_command)
            self.assertTrue(any(option.startswith("--view-size=") for option in chafa_command))
            self.assertIn("--optimize=9", chafa_command)
            self.assertIn("--work=9", chafa_command)
            self.assertIn("--color-space=din99d", chafa_command)

        def test_artwork_preview_width_doubles_but_caps_at_three_times_height(self) -> None:
            geometry = ArtworkPreviewGeometry(
                terminal_columns=160,
                terminal_rows=50,
                indent_columns=0,
                columns=120,
                rows=40,
                pixel_width=840,
                pixel_height=560,
            )
            scaled = scaled_artwork_geometry(geometry, scale=0.25)
            self.assertEqual(10, scaled.rows)
            # Ordinary width is 30, doubled to 60; 7x14 cells make that
            # physically 420x140, exactly the requested 3:1 cap.
            self.assertEqual(60, scaled.columns)
            options = scale_chafa_view_size(
                ["--view-size=120x40"],
                0.25,
            )
            self.assertEqual(["--view-size=60.0x10.0"], options)

        def test_embedded_art_target_folder_is_double_height(self) -> None:
            finding = {
                "category": "embedded_art_without_sidecar",
                "path": "1993 - These Monsters Are Real/1_Me & Her.flac",
            }
            lines = finding_target_lines(
                finding,
                use_color=True,
                terminal_columns=160,
            )
            self.assertTrue(lines[0].startswith(ANSI_DOUBLE_HEIGHT_TOP))
            self.assertTrue(lines[1].startswith(ANSI_DOUBLE_HEIGHT_BOTTOM))
            self.assertIn("Folder:", lines[0])
            self.assertIn("1_Me & Her.flac", lines[-1])

        def test_builtin_ansi_and_sixel_previews_need_no_chafa(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                image_path = Path(temp) / "preview.jpg"
                image_path.write_bytes(
                    make_test_jpeg(width=320, height=240)
                )
                with mock.patch.object(
                    sys.modules[__name__],
                    "visible_console_size",
                    return_value=os.terminal_size((100, 35)),
                ):
                    ansi = ansi_half_block_preview(
                        image_path,
                        use_color=True,
                    )
                    sixel = sixel_preview_bytes(image_path)
                self.assertIn("▀", ansi)
                self.assertIn("\033[38;2;", ansi)
                self.assertTrue(ansi.startswith("            "))
                self.assertEqual(28, len(ansi.splitlines()))
                self.assertTrue(sixel.startswith(b"\x1bPq"))
                self.assertTrue(sixel.endswith(b"\x1b\\"))
                self.assertIn(b'"1;1;523;392', sixel)
                with mock.patch.dict(
                    os.environ,
                    {"AUDIT_MUSIC_ART_PREVIEW": "sixel"},
                ):
                    self.assertTrue(terminal_supports_sixel())
                with mock.patch.dict(
                    os.environ,
                    {"AUDIT_MUSIC_ART_PREVIEW": "ansi"},
                ):
                    self.assertFalse(terminal_supports_sixel())

        def test_view_key_prefers_openimage_then_standalone_irfanview(self) -> None:
            module = sys.modules[__name__]
            image_path = Path(r"C:\Music\cover.jpg")
            launcher = Path(r"C:\BAT\openimage.bat")
            viewer = Path(
                r"C:\util2\IrfanViewPortable\App"
                r"\IrfanView\i_view32.exe"
            )
            with mock.patch.object(
                module,
                "openimage_launcher",
                return_value=launcher,
            ), mock.patch.object(
                module,
                "irfanview_executable",
                return_value=viewer,
            ), mock.patch.object(
                shutil,
                "which",
                side_effect=lambda name: (
                    r"C:\Mock\tcc.exe"
                    if name in {"tcc.exe", "tcc"}
                    else None
                ),
            ), mock.patch.object(
                subprocess,
                "Popen",
            ) as popen:
                self.assertEqual(launcher, launch_irfanview(image_path))
                self.assertEqual(
                    [
                        r"C:\Mock\tcc.exe",
                        "/c",
                        "call",
                        str(launcher),
                        str(image_path),
                    ],
                    popen.call_args.args[0],
                )

            with mock.patch.object(
                module,
                "openimage_launcher",
                return_value=launcher,
            ), mock.patch.object(
                module,
                "irfanview_executable",
                return_value=viewer,
            ), mock.patch.object(
                shutil,
                "which",
                return_value=None,
            ), mock.patch.object(
                subprocess,
                "Popen",
            ) as popen:
                self.assertEqual(viewer, launch_irfanview(image_path))
                self.assertEqual(
                    [str(viewer), str(image_path)],
                    popen.call_args.args[0],
                )

            with mock.patch.object(
                module,
                "openimage_launcher",
                return_value=None,
            ), mock.patch.object(
                module,
                "irfanview_executable",
                return_value=None,
            ):
                with self.assertRaisesRegex(
                    RuntimeError,
                    "IMAGE_VIEWER_EXECUTABLE",
                ):
                    launch_irfanview(image_path)

        def test_approved_karaoke_finding_applies_immediately(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                audio_path = make_silent_flac(
                    root, "04 Immediate Action (feat._Artist)"
                )
                audio_path.with_suffix(".txt").write_text("A line\n", encoding="utf-8")
                audio_path.with_suffix(".lrc").write_text(
                    "[00:00.00]A line\n", encoding="utf-8"
                )
                report = BatchAudit(root).audit()
                finding = next(
                    item
                    for item in report["findings"]
                    if item["category"] == "karaoke_not_embedded"
                )
                self.assertEqual(
                    audio_path.with_suffix(".lrc").name,
                    finding["details"]["sidecar"],
                )
                self.assertIn(
                    "a usable .LRC sidecar exists with 1 timestamped lyric line",
                    finding["message"],
                )
                self.assertEqual(
                    [
                        "📄 Confirmed sidecar: "
                        + audio_path.with_suffix(".lrc").name
                    ],
                    finding_sidecar_lines(finding, False),
                )
                self.assertEqual(
                    audio_path.with_suffix(".lrc"),
                    find_lyric_sidecar(audio_path, (".lrc",)),
                )
                self.assertIn("synced_lyrics", apply_finding(root, finding))
                self.assertTrue(FLAC(audio_path).get("SYNCEDLYRICS"))

        def test_header_only_lrc_does_not_shadow_usable_srt_embedding(
            self,
        ) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                audio_path = make_silent_flac(root, "03_Erotomania")
                lrc = audio_path.with_suffix(".lrc")
                srt = audio_path.with_suffix(".srt")
                txt = audio_path.with_suffix(".txt")
                header_only = (
                    "# Generated by Claire\n"
                    "# Sawyer’s WhisperAI-based\n"
                    "# transcription system.\n"
                    "# Kill yourself, Trumpers.\n"
                )
                lrc.write_text(header_only, encoding="utf-8")
                srt.write_text(
                    header_only
                    + "\n1\n"
                    "00:00:02,420 --> 00:00:04,140\n"
                    "First saw you\n\n"
                    "2\n"
                    "00:00:04,660 --> 00:00:06,640\n"
                    "Had a heart attack\n",
                    encoding="utf-8",
                )
                txt.write_text(
                    "First saw you\nHad a heart attack\n",
                    encoding="utf-8",
                )
                report = BatchAudit(root).audit()
                finding = next(
                    item
                    for item in report["findings"]
                    if item["category"] == "karaoke_not_embedded"
                )
                self.assertEqual(
                    srt.name,
                    finding["details"]["sidecar"],
                )
                self.assertIn(
                    "a usable .SRT sidecar exists with 2 timestamped lyric lines",
                    finding["message"],
                )
                actions = apply_finding(root, finding)
                self.assertIn("synced_lyrics", actions)
                embedded = FLAC(audio_path).get("SYNCEDLYRICS")
                self.assertTrue(embedded)
                self.assertIn("[00:02.42]First saw you", embedded[0])
                self.assertIn("[00:04.66]Had a heart attack", embedded[0])
                self.assertEqual(header_only, lrc.read_text(encoding="utf-8"))
                refreshed_categories = {
                    item["category"]
                    for item in BatchAudit(root).audit()["findings"]
                }
                self.assertNotIn(
                    "karaoke_not_embedded",
                    refreshed_categories,
                )

        def test_utf16_srt_is_automatically_embedded_as_karaoke(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                audio_path = make_silent_flac(root, "07_I'm Alright")
                srt = audio_path.with_suffix(".srt")
                srt.write_text(
                    "1\n"
                    "00:00:07,670 --> 00:00:12,260\n"
                    "Whoops\n\n"
                    "2\n"
                    "00:00:12,260 --> 00:00:13,350\n"
                    "I've been taking\n",
                    encoding="utf-16",
                )

                self.assertNotIn("\x00", read_text(srt))
                self.assertEqual(2, len(usable_timed_sidecar_entries(srt)))
                report = BatchAudit(root).audit(embed_lyrics_first=True)
                actions = [
                    action
                    for item in report["embedded_lyrics"]
                    for action in item["actions"]
                ]
                self.assertIn("plain_lyrics", actions)
                self.assertIn("synced_lyrics", actions)
                embedded = FLAC(audio_path).get("SYNCEDLYRICS")
                self.assertTrue(embedded)
                self.assertIn("[00:07.67]Whoops", embedded[0])
                self.assertIn("[00:12.26]I've been taking", embedded[0])
                categories = finding_categories(report)
                self.assertNotIn("unusable_karaoke_sidecar", categories)
                self.assertNotIn("karaoke_not_embedded", categories)

        def test_interactive_lyric_approval_embeds_and_reaudits(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                audio_path = make_silent_flac(root, "04b Interactive Lyrics")
                audio_path.with_suffix(".txt").write_text(
                    "A line\n", encoding="utf-8"
                )
                audio_path.with_suffix(".lrc").write_text(
                    "[00:00.00]A line\n", encoding="utf-8"
                )
                report = BatchAudit(root).audit()
                lyric_actions = [
                    finding
                    for finding in report["findings"]
                    if finding["category"]
                    in {"plain_lyrics_not_embedded", "karaoke_not_embedded"}
                ]
                self.assertTrue(lyric_actions)
                self.assertTrue(
                    all("--embed-lyrics" in finding["suggestion"] for finding in lyric_actions)
                )
                answers = iter(
                    "y"
                    if finding["category"] == "plain_lyrics_not_embedded"
                    else "n"
                    for finding in report["findings"]
                    if finding.get("code")
                    and finding["category"] != "missing_album"
                )
                interactive_output = io.StringIO()
                with contextlib.redirect_stdout(interactive_output):
                    result = interactive_apply(
                        report,
                        use_color=False,
                        key_reader=lambda: next(answers),
                        input_reader=lambda _prompt: "",
                    )
                self.assertFalse(interactive_output.getvalue().startswith("\n"))
                self.assertTrue(
                    interactive_output.getvalue().startswith("        ✨✱✨")
                )
                self.assertNotIn(
                    "Embed the available front-cover sidecar",
                    interactive_output.getvalue(),
                )
                self.assertIn(
                    "Search for the release artwork, download and preview every "
                    "supplied image part, and embed only an approved Front cover "
                    "now?",
                    interactive_output.getvalue(),
                )
                self.assertIn(
                    "\n            ❓ Embed the plain lyrics into this audio file now?\n"
                    "               [Y=Yes / n=No / A=Always / V=Never / "
                    "F=Yes for This Folder] Yes!",
                    interactive_output.getvalue(),
                )
                self.assertIn(
                    "            ⚠️ Plain lyrics are not embedded",
                    interactive_output.getvalue(),
                )
                self.assertIn(
                    "             ♪ 04b Interactive Lyrics.flac",
                    interactive_output.getvalue(),
                )
                self.assertIn(
                    "            🎤 Suggested:",
                    interactive_output.getvalue(),
                )
                self.assertIn(
                    "\n            🔧 Applied: ",
                    interactive_output.getvalue(),
                )
                self.assertIn(
                    "\n            💾 Backup: ",
                    interactive_output.getvalue(),
                )
                self.assertIn(
                    "\n            ✔️ Re-audit: passed",
                    interactive_output.getvalue(),
                )
                colored_results = "\n".join(
                    action_result_lines(
                        [
                            r"backup:C:\Music\song.flac.bak",
                            "plain_lyrics",
                            "re-audit:passed",
                        ],
                        use_color=True,
                    )
                )
                self.assertIn(
                    "\033[2m\033[38;2;145;150;160m"
                    "            💾 Backup:",
                    colored_results,
                )
                self.assertNotIn(r"C:\Music", colored_results)
                self.assertFalse(result["failed_codes"], result)
                self.assertTrue(
                    any(
                        "re-audit:passed" in decision["actions"]
                        for decision in result["decisions"]
                    )
                )
                remaining = audit_categories_for_path(
                    root, audio_path.relative_to(root).as_posix()
                )
                self.assertNotIn("plain_lyrics_not_embedded", remaining)
                self.assertNotIn("karaoke_not_embedded", remaining)

        def test_interactive_lyric_refusal_does_not_embed(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                audio_path = make_silent_flac(root, "04c Refused Lyrics")
                audio_path.with_suffix(".txt").write_text(
                    "A line\n", encoding="utf-8"
                )
                audio_path.with_suffix(".lrc").write_text(
                    "[00:00.00]A line\n", encoding="utf-8"
                )
                report = BatchAudit(root).audit()
                with contextlib.redirect_stdout(io.StringIO()):
                    result = interactive_apply(
                        report, use_color=False, key_reader=lambda: "n"
                    )
                self.assertFalse(result["applied_codes"])
                tagged = FLAC(audio_path)
                self.assertFalse(tagged.get("LYRICS"))
                self.assertFalse(tagged.get("SYNCEDLYRICS"))

        def test_progress_bar_rainbow_is_default_and_can_be_disabled(self) -> None:
            self.assertNotEqual(rainbow_hex(0.0), rainbow_hex(1 / 3))
            parameters = inspect.signature(progress_bar).parameters
            self.assertIs(parameters["rainbow"].default, True)
            self.assertEqual(0.05, parameters["mininterval"].default)
            self.assertEqual(0.5, parameters["maxinterval"].default)
            self.assertEqual(1, parameters["miniters"].default)
            self.assertIsNone(parameters["bar_format"].default)
            self.assertEqual(" file", spaced_unit("file"))
            self.assertEqual(" file", spaced_unit("  file "))
            self.assertEqual("", spaced_unit(""))
            self.assertIn("{n:,.0f} files found", ENUMERATION_PROGRESS_FORMAT)
            self.assertIn("{rate_fmt}", ENUMERATION_PROGRESS_FORMAT)
            self.assertIn("{n:,.0f}/{total:,.0f}", AUDIT_PROGRESS_FORMAT)
            self.assertNotIn("checks", AUDIT_PROGRESS_FORMAT)
            self.assertIn("rate_fmt", AUDIT_PROGRESS_FORMAT)
            self.assertIn("remaining", AUDIT_PROGRESS_FORMAT)
            compact = compact_progress_filename(
                Path("09_Bad Cop - The Very Long Song Title.mp3")
            )
            self.assertEqual(16, len(compact))
            self.assertIn("…", compact)
            audit = BatchAudit(Path("."))
            fake_progress = mock.Mock()
            fake_progress.format_dict = {"elapsed": 10.0, "n": 12.0}
            fake_progress.initial = 0.0
            audit.progress = fake_progress
            audit.progress_show_audio(
                Path("09_Bad Cop - The Very Long Song Title.mp3")
            )
            postfix = fake_progress.set_postfix_str.call_args.args[0]
            self.assertTrue(postfix.startswith("1.20/sec • "))
            self.assertLessEqual(len(postfix.rsplit(" • ", 1)[1]), 16)
            with progress_bar(
                total=None,
                description="test",
                enabled=False,
                rainbow=False,
            ) as progress:
                self.assertIsNone(progress)

        def test_file_enumeration_reports_each_discovered_file(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                root.joinpath("one.txt").write_text("1", encoding="utf-8")
                root.joinpath("two.txt").write_text("2", encoding="utf-8")
                root.joinpath("three.txt").write_text("3", encoding="utf-8")
                discovered_counts: list[int] = []
                audit = BatchAudit(root)
                audit.collect_files(on_file=discovered_counts.append)
                self.assertEqual([1, 2, 3], discovered_counts)
                self.assertEqual(3, len(audit.files))

        def test_small_interactive_audit_starts_progress_immediately(self) -> None:
            class TTYBuffer(io.StringIO):
                def isatty(self) -> bool:
                    return True

            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                root.joinpath("one.txt").write_text("1", encoding="utf-8")
                progress = mock.MagicMock()
                module = sys.modules[__name__]
                with mock.patch.object(
                    module.sys,
                    "stderr",
                    TTYBuffer(),
                ), mock.patch.object(
                    module,
                    "progress_bar",
                    return_value=contextlib.nullcontext(progress),
                ) as progress_factory:
                    BatchAudit(root).audit()
                progress_factory.assert_called_once()
                options = progress_factory.call_args.kwargs
                self.assertIsNone(options["total"])
                self.assertEqual("🔎 Finding files", options["description"])
                self.assertTrue(options["enabled"])
                progress.update.assert_any_call(1)

        def test_excessive_silence_has_positive_and_negative_controls(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                excessive = make_patterned_flac(
                    root,
                    "Excessive Silence [instrumental]",
                    [(1.0, False), (11.25, True), (1.0, False)],
                )
                acceptable = make_patterned_flac(
                    root,
                    "Acceptable Silence [instrumental]",
                    [(1.0, False), (9.5, True), (1.0, False)],
                )
                intervals = detect_silence_intervals(
                    excessive,
                    10.0,
                )
                self.assertEqual(1, len(intervals))
                self.assertEqual("internal", intervals[0]["position"])
                self.assertGreater(intervals[0]["duration"], 10.0)
                self.assertEqual(
                    [],
                    detect_silence_intervals(acceptable, 10.0),
                )
                report = BatchAudit(
                    root,
                    check_silence=True,
                    silence_threshold_seconds=10.0,
                ).audit()
                findings = [
                    finding
                    for finding in report["findings"]
                    if finding["category"] == "excessive_silence"
                ]
                self.assertEqual(1, len(findings))
                self.assertEqual(excessive.name, findings[0]["path"])
                self.assertIn("--review-waveforms", findings[0]["suggestion"])
                self.assertEqual(
                    10.0,
                    findings[0]["details"]["threshold_seconds"],
                )
                editor = Path(r"C:\Program Files\Adobe\Audition.exe")
                module = sys.modules[__name__]
                with mock.patch.object(
                    module,
                    "launch_audio_editor",
                    return_value=editor,
                ) as launch, mock.patch.object(
                    module,
                    "retreat_edited_audio",
                    return_value=["re-audit:passed"],
                ) as retreat, contextlib.redirect_stdout(io.StringIO()):
                    result = interactive_apply(
                        {**report, "findings": [findings[0]]},
                        use_color=False,
                        key_reader=lambda: "\r",
                    )
                self.assertEqual(findings[0]["code"], result["applied_codes"])
                self.assertTrue(result["decisions"][0]["default"])
                launch.assert_called_once_with(excessive)
                retreat.assert_called_once_with(
                    excessive,
                    use_color=False,
                    key_reader=mock.ANY,
                )

        def test_silence_analysis_starts_early_and_runs_concurrently(self) -> None:
            module = sys.modules[__name__]
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                for index in range(4):
                    (root / f"Track {index} [instrumental].flac").write_bytes(
                        b"fixture"
                    )
                active = 0
                maximum_active = 0
                lock = threading.Lock()
                two_started = threading.Event()
                release = threading.Event()

                def fake_detect(*_args, **_kwargs):
                    nonlocal active, maximum_active
                    with lock:
                        active += 1
                        maximum_active = max(maximum_active, active)
                        if active >= 2:
                            two_started.set()
                    release.wait(timeout=2.0)
                    with lock:
                        active -= 1
                    return []

                audit = BatchAudit(root, check_silence=True)

                def verify_background_started() -> None:
                    self.assertTrue(
                        two_started.wait(timeout=1.0),
                        "silence workers did not start during file collection",
                    )
                    release.set()

                audit.audit_filesystem = mock.Mock(
                    side_effect=verify_background_started
                )
                audit.audit_duplicates_and_archives = mock.Mock()
                audit.audit_audio_tags = mock.Mock()
                with mock.patch.object(
                    module.shutil,
                    "which",
                    return_value=r"C:\util\ffmpeg.exe",
                ), mock.patch.object(
                    module,
                    "detect_silence_intervals",
                    side_effect=fake_detect,
                ):
                    audit.audit()
                self.assertGreaterEqual(maximum_active, 2)

        def test_waveform_jpeg_generation_is_verified(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                audio = make_stereo_peak_flac(
                    root,
                    "Waveform Fixture [instrumental]",
                    0.50,
                    0.25,
                )
                staged = root / "staged.waveform.jpg"
                waveform, backup, generated_metrics = generate_waveform_jpeg(
                    audio,
                    destination=staged,
                    narrate=False,
                )
                self.assertEqual(staged, waveform)
                self.assertIsNone(backup)
                self.assertAlmostEqual(
                    50.0,
                    generated_metrics.peak_volume_percentage,
                    places=1,
                )
                self.assertEqual("image/jpeg", image_mime(waveform))
                with Image.open(waveform) as preview:
                    self.assertEqual(
                        (WAVEFORM_JPEG_WIDTH, WAVEFORM_JPEG_HEIGHT),
                        preview.size,
                    )
                    preview_rgb = preview.convert("RGB")
                    unboxed_gutter_pixel = preview_rgb.getpixel(
                        (preview.width - 2, 1)
                    )
                    self.assertLess(sum(unboxed_gutter_pixel), 50)
                    plot_border_pixel = preview_rgb.getpixel(
                        (WAVEFORM_PLOT_WIDTH - 3, 1)
                    )
                    self.assertLessEqual(
                        max(plot_border_pixel) - min(plot_border_pixel),
                        85,
                    )
                    self.assertGreater(sum(plot_border_pixel), 120)
                    tick_x = WAVEFORM_PLOT_WIDTH - 20
                    # Only the auto-scaled outer axis is labeled: no middle
                    # labels. A measured 50% peak uses a truthful ±55% axis.
                    for guide_y in (8, 692):
                        guide_pixel = preview_rgb.getpixel(
                            (tick_x, guide_y)
                        )
                        self.assertLess(
                            max(guide_pixel) - min(guide_pixel),
                            30,
                        )
                        self.assertGreater(sum(guide_pixel), 240)
                    for unlabelled_middle_y in (258, 442):
                        middle_pixel = preview_rgb.getpixel(
                            (WAVEFORM_PLOT_WIDTH + 10, unlabelled_middle_y)
                        )
                        self.assertLess(sum(middle_pixel), 80)
                    axis_pixel = preview_rgb.getpixel(
                        (WAVEFORM_PLOT_WIDTH - 1, 100)
                    )
                    self.assertLess(
                        max(axis_pixel) - min(axis_pixel),
                        30,
                    )
                    self.assertGreater(sum(axis_pixel), 180)
                    # A constant 50% channel fills most of its ±55% axis,
                    # retaining only the small labeled headroom.
                    rainbow_rows = [
                        y
                        for y in range(20, preview.height // 2 - 20)
                        for x in range(20, WAVEFORM_PLOT_WIDTH - 50)
                        if (
                            (pixel := preview_rgb.getpixel((x, y)))
                            and max(pixel) >= 120
                            and max(pixel) - min(pixel) >= 45
                        )
                    ]
                    self.assertTrue(rainbow_rows)
                    self.assertLessEqual(min(rainbow_rows), 35)
                    self.assertGreaterEqual(min(rainbow_rows), 8)
                    self.assertGreaterEqual(max(rainbow_rows), 315)
                    self.assertGreaterEqual(
                        max(rainbow_rows) - min(rainbow_rows),
                        280,
                    )
                    axis_ceiling = waveform_axis_ceiling_percent(
                        generated_metrics
                    )
                    channel_height = preview.height // 2
                    for channel_index, measured_peak in enumerate(
                        generated_metrics.channel_peak_percentages
                    ):
                        channel_region = preview_rgb.crop(
                            (
                                4,
                                channel_index * channel_height + 4,
                                WAVEFORM_PLOT_WIDTH - 4,
                                (channel_index + 1) * channel_height - 4,
                            )
                        )
                        envelope = waveform_colored_mask(
                            channel_region
                        ).getbbox()
                        self.assertIsNotNone(envelope)
                        rendered_ratio = (
                            (envelope[3] - envelope[1])
                            / channel_region.height
                        )
                        self.assertAlmostEqual(
                            measured_peak / axis_ceiling,
                            rendered_ratio,
                            # JPEG chroma bleed and the deliberate five-pixel
                            # true-peak emphasis can extend a nearly full-height
                            # envelope to the channel boundary. This generous
                            # compression tolerance still fails the former
                            # empty-canvas bug by a very wide margin.
                            delta=0.12,
                        )
                    metric_pixels = [
                        preview_rgb.getpixel((x, y))
                        for y in range(250, 450, 8)
                        for x in range(
                            WAVEFORM_PLOT_WIDTH + 20,
                            WAVEFORM_JPEG_WIDTH - 5,
                            8,
                        )
                    ]
                    self.assertTrue(
                        any(sum(pixel) > 250 for pixel in metric_pixels)
                    )
                self.assertTrue(staged.exists())
                self.assertFalse(
                    audio.with_name(f"{audio.stem}.waveform.jpg").exists()
                )

        def test_waveform_metrics_are_measured_and_formatted(self) -> None:
            output = "\n".join(
                (
                    "[astats] Channel: 1",
                    "[astats] Peak level dB: -0.175",
                    "[astats] Channel: 2",
                    "[astats] Peak level dB: -6.021",
                    "[astats] Overall",
                    "[astats] Peak level dB: -0.175",
                    "[astats] RMS level dB: -4.862",
                    "[silencedetect] silence_duration: 3.4",
                    "[silencedetect] silence_duration: 1.1",
                )
            )
            module = sys.modules[__name__]
            with mock.patch.object(
                module,
                "waveform_replaygain_factor",
                return_value=1.00004,
            ):
                metrics = parse_waveform_metrics(
                    output,
                    Path("fixture.flac"),
                    2,
                )
            self.assertAlmostEqual(98.0, metrics.peak_volume_percentage, places=1)
            self.assertAlmostEqual(57.1, metrics.average_volume_percentage, places=1)
            self.assertEqual((3.4, 4.5), (
                metrics.longest_silence_seconds,
                metrics.total_silence_seconds,
            ))
            self.assertEqual(
                (
                    "peak vol: 98%",
                    "avg vol: 57%",
                    "ReplayGain: +0.00 dB",
                    "gain: 1.00004",
                    "silence: 3s (longest)",
                ),
                waveform_metric_lines(metrics),
            )
            normal_colors = waveform_metric_value_colors(metrics, 10.0)
            self.assertNotEqual((255, 75, 85), normal_colors[4])
            excessive_metrics = replace(
                metrics,
                longest_silence_seconds=10.1,
            )
            excessive_colors = waveform_metric_value_colors(
                excessive_metrics,
                10.0,
            )
            self.assertEqual((255, 75, 85), excessive_colors[4])
            self.assertNotIn(
                (255, 75, 85),
                excessive_colors[:4] + excessive_colors[5:],
            )
            self.assertEqual(
                "ReplayGain: -9.23 dB",
                waveform_metric_lines(
                    replace(metrics, replaygain_factor=0.34554)
                )[2],
            )
            self.assertEqual(
                70.0,
                waveform_axis_ceiling_percent(
                    replace(
                        metrics,
                        channel_peak_percentages=(66.0, 40.0),
                        peak_volume_percentage=66.0,
                    )
                ),
            )
            self.assertEqual(
                80.0,
                waveform_axis_ceiling_percent(
                    replace(
                        metrics,
                        channel_peak_percentages=(75.0,),
                        peak_volume_percentage=75.0,
                    )
                ),
            )
            self.assertEqual(
                100.0,
                waveform_axis_ceiling_percent(
                    replace(
                        metrics,
                        channel_peak_percentages=(99.0,),
                        peak_volume_percentage=99.0,
                    )
                ),
            )
            almost_ten = replace(
                metrics,
                longest_silence_seconds=9.9999,
            )
            self.assertEqual(
                "silence: 9s (longest)",
                waveform_metric_lines(almost_ten)[-1],
            )

        def test_baked_replaygain_reencodes_mp3_and_refreshes_tags(self) -> None:
            ffmpeg = shutil.which("ffmpeg")
            metamp3 = shutil.which("metamp3")
            if not ffmpeg or not metamp3:
                raise unittest.SkipTest(
                    "ffmpeg and metamp3 are required for baked MP3 gain"
                )
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                audio = root / "Baked Gain [instrumental].mp3"
                subprocess.run(
                    [
                        ffmpeg,
                        "-hide_banner",
                        "-loglevel",
                        "error",
                        "-f",
                        "lavfi",
                        "-i",
                        "sine=frequency=440:sample_rate=44100",
                        "-t",
                        "1",
                        "-filter:a",
                        "volume=0.25",
                        "-q:a",
                        "4",
                        str(audio),
                    ],
                    check=True,
                    capture_output=True,
                )
                tagged = MP3(audio, ID3=ID3)
                if tagged.tags is None:
                    tagged.add_tags()
                tagged.tags.add(
                    TXXX(
                        encoding=3,
                        desc="replaygain_track_gain",
                        text=["+6.00 dB"],
                    )
                )
                tagged.tags.add(
                    TXXX(
                        encoding=3,
                        desc="replaygain_track_peak",
                        text=["0.25"],
                    )
                )
                tagged.tags.add(
                    APIC(
                        encoding=3,
                        mime="image/jpeg",
                        type=3,
                        desc="Front Cover",
                        data=make_test_jpeg(),
                    )
                )
                tagged.save(v2_version=3)
                _before_waveform, _before_backup, before_metrics = (
                    generate_waveform_jpeg(
                        audio,
                        destination=root / "before.waveform.jpg",
                        narrate=False,
                    )
                )
                before = audio.read_bytes()
                metrics = WaveformMetrics(
                    channel_peak_percentages=(25.0,),
                    peak_volume_percentage=25.0,
                    average_volume_percentage=10.0,
                    replaygain_factor=math.pow(10.0, 6.0 / 20.0),
                    longest_silence_seconds=0.0,
                    total_silence_seconds=0.0,
                )
                with contextlib.redirect_stdout(io.StringIO()):
                    backup, applied_db = bake_replaygain_into_audio(
                        audio,
                        metrics,
                        use_color=False,
                        stream_output=False,
                        ffmpeg_executable=ffmpeg,
                        metamp3_executable=metamp3,
                    )
                self.assertAlmostEqual(6.0, applied_db, places=2)
                self.assertTrue(backup.is_file())
                self.assertEqual(before, backup.read_bytes())
                self.assertNotEqual(before, audio.read_bytes())
                refreshed = MP3(audio, ID3=ID3)
                self.assertEqual(1, len(refreshed.tags.getall("APIC")))
                self.assertIsNotNone(waveform_replaygain_factor(audio))
                waveform, _backup, new_metrics = generate_waveform_jpeg(
                    audio,
                    destination=root / "baked.waveform.jpg",
                    narrate=False,
                )
                measured_ratio = (
                    new_metrics.peak_volume_percentage
                    / before_metrics.peak_volume_percentage
                )
                self.assertAlmostEqual(
                    math.pow(10.0, applied_db / 20.0),
                    measured_ratio,
                    delta=0.12,
                )
                recolor_newly_baked_waveform(waveform)
                with Image.open(waveform) as preview:
                    pixels = preview.convert("RGB").crop(
                        (0, 0, WAVEFORM_PLOT_WIDTH, preview.height)
                    ).getdata()
                    self.assertTrue(
                        any(
                            green > red + 50 and green > blue + 40
                            for red, green, blue in pixels
                        )
                    )

        def test_baked_replaygain_real_flac_survives_access_denied_replace(
            self,
        ) -> None:
            ffmpeg = shutil.which("ffmpeg")
            metaflac = shutil.which("metaflac")
            if not ffmpeg or not metaflac:
                raise unittest.SkipTest(
                    "ffmpeg and metaflac are required for baked FLAC gain"
                )
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                audio = root / "Baked Gain [instrumental].flac"
                subprocess.run(
                    [
                        ffmpeg,
                        "-hide_banner",
                        "-loglevel",
                        "error",
                        "-f",
                        "lavfi",
                        "-i",
                        "sine=frequency=523.25:sample_rate=48000",
                        "-t",
                        "1",
                        "-filter:a",
                        "volume=0.25",
                        "-c:a",
                        "flac",
                        str(audio),
                    ],
                    check=True,
                    capture_output=True,
                )
                tagged = FLAC(audio)
                tagged["title"] = ["Generated FLAC ReplayGain fixture"]
                tagged["replaygain_track_gain"] = ["+6.00 dB"]
                tagged["replaygain_track_peak"] = ["0.25"]
                picture = Picture()
                picture.type = 3
                picture.mime = "image/jpeg"
                picture.desc = "Front Cover"
                picture.data = make_test_jpeg()
                tagged.add_picture(picture)
                tagged.save()
                _before_waveform, _before_backup, before_metrics = (
                    generate_waveform_jpeg(
                        audio,
                        destination=root / "before.flac.waveform.jpg",
                        narrate=False,
                    )
                )
                before = audio.read_bytes()
                metrics = replace(
                    before_metrics,
                    replaygain_factor=math.pow(10.0, 6.0 / 20.0),
                )
                denied_replace = mock.Mock(
                    side_effect=PermissionError(
                        13,
                        "Access is denied",
                        str(audio),
                    )
                )
                recycler = mock.Mock(return_value=Path("Recycle Bin"))
                module = sys.modules[__name__]
                with mock.patch.object(
                    module.os,
                    "replace",
                    denied_replace,
                ), mock.patch.object(
                    module,
                    "recycle_path",
                    recycler,
                ), contextlib.redirect_stdout(io.StringIO()) as narration:
                    backup, applied_db = bake_replaygain_into_audio(
                        audio,
                        metrics,
                        use_color=False,
                        stream_output=False,
                        ffmpeg_executable=ffmpeg,
                        metaflac_executable=metaflac,
                    )
                denied_replace.assert_called_once()
                recycler.assert_called_once()
                self.assertIn(
                    "SHA-256-verified in-place media write",
                    narration.getvalue(),
                )
                self.assertAlmostEqual(6.0, applied_db, places=2)
                self.assertTrue(backup.is_file())
                self.assertEqual(before, backup.read_bytes())
                self.assertNotEqual(before, audio.read_bytes())
                refreshed = FLAC(audio)
                self.assertEqual(
                    ["Generated FLAC ReplayGain fixture"],
                    refreshed.get("title"),
                )
                self.assertEqual(1, len(refreshed.pictures))
                self.assertIsNotNone(waveform_replaygain_factor(audio))
                _waveform, _backup, new_metrics = generate_waveform_jpeg(
                    audio,
                    destination=root / "baked.flac.waveform.jpg",
                    narrate=False,
                )
                measured_ratio = (
                    new_metrics.peak_volume_percentage
                    / before_metrics.peak_volume_percentage
                )
                self.assertAlmostEqual(
                    math.pow(10.0, applied_db / 20.0),
                    measured_ratio,
                    delta=0.04,
                )

        def test_replaygain_bake_threshold_is_configurable_and_strict(
            self,
        ) -> None:
            audio = Path("Track.flac")

            def metrics_for_db(decibels: float) -> WaveformMetrics:
                return WaveformMetrics(
                    channel_peak_percentages=(50.0, 50.0),
                    peak_volume_percentage=50.0,
                    average_volume_percentage=25.0,
                    replaygain_factor=10 ** (decibels / 20.0),
                    longest_silence_seconds=0.0,
                    total_silence_seconds=0.0,
                )

            self.assertFalse(
                replaygain_needs_baking(metrics_for_db(0.05), audio)
            )
            self.assertFalse(
                replaygain_needs_baking(metrics_for_db(-0.05), audio)
            )
            self.assertTrue(
                replaygain_needs_baking(metrics_for_db(0.051), audio)
            )
            self.assertTrue(
                replaygain_needs_baking(metrics_for_db(-0.051), audio)
            )
            self.assertFalse(
                replaygain_needs_baking(
                    metrics_for_db(0.051),
                    Path("Track.wav"),
                )
            )

        def test_waveform_review_can_batch_bake_and_show_gradient_comparisons(
            self,
        ) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                first = root / "First [instrumental].flac"
                second = root / "Second [instrumental].mp3"
                first.write_bytes(b"fake flac")
                second.write_bytes(b"fake mp3")
                staging_root = root / "recycled-staging"
                module = sys.modules[__name__]
                generated: list[Path] = []
                baked: list[Path] = []
                recolored: list[Path] = []
                rendered: list[Path] = []
                keys = iter(["y", "n", "n"])

                def metric(decibels: float = 2.0) -> WaveformMetrics:
                    return WaveformMetrics(
                        channel_peak_percentages=(50.0, 50.0),
                        peak_volume_percentage=50.0,
                        average_volume_percentage=25.0,
                        replaygain_factor=10 ** (decibels / 20.0),
                        longest_silence_seconds=0.0,
                        total_silence_seconds=0.0,
                    )

                def fake_generate(
                    audio: Path,
                    *,
                    narrate: bool,
                    destination: Path,
                    **_kwargs,
                ) -> tuple[Path, None, WaveformMetrics]:
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(make_test_jpeg())
                    generated.append(audio)
                    return destination, None, metric(0.0 if generated.count(audio) > 1 else 2.0)

                def fake_bake(
                    audio: Path,
                    _metrics: WaveformMetrics,
                    **_kwargs,
                ) -> tuple[Path, float]:
                    baked.append(audio)
                    backup = audio.with_name(f"{audio.name}.bak.test.bak")
                    backup.write_bytes(audio.read_bytes())
                    return backup, 2.0

                def fake_renderer(path: Path, *, use_color: bool) -> str:
                    rendered.append(path)
                    return "test renderer"

                with mock.patch.object(
                    module,
                    "waveform_staging_root",
                    return_value=staging_root,
                ), mock.patch.object(
                    module,
                    "waveform_replaygain_factor",
                    return_value=10 ** (2.0 / 20.0),
                ), mock.patch.object(
                    module,
                    "generate_waveform_jpeg",
                    side_effect=fake_generate,
                ), mock.patch.object(
                    module,
                    "bake_replaygain_into_audio",
                    side_effect=fake_bake,
                ), mock.patch.object(
                    module,
                    "recolor_newly_baked_waveform",
                    side_effect=lambda path: recolored.append(path),
                ), mock.patch.object(
                    module,
                    "audio_editor_executable",
                    return_value=None,
                ), contextlib.redirect_stdout(io.StringIO()) as output:
                    result = review_waveforms(
                        root,
                        use_color=False,
                        key_reader=lambda: next(keys),
                        preview_renderer=fake_renderer,
                        workers=2,
                        approval_database_path=root / "reviews.sqlite3",
                    )

                self.assertCountEqual([first, second], baked)
                self.assertEqual(4, len(generated))
                self.assertEqual(2, len(recolored))
                self.assertEqual(4, len(rendered))
                self.assertTrue(
                    all(
                        "before-replaygain-bake" in rendered[index].name
                        for index in (0, 2)
                    )
                )
                self.assertTrue(
                    all(
                        "before-replaygain-bake" not in rendered[index].name
                        for index in (1, 3)
                    )
                )
                self.assertEqual(2, len(result["fine"]))
                self.assertEqual(
                    1,
                    output.getvalue().count(
                        "Bake ReplayGain into the audio data for all"
                    ),
                )

        def test_normal_audit_replaygain_bake_saves_gradient_comparisons(
            self,
        ) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                audio = root / "Normal Audit.flac"
                audio.write_bytes(b"fixture")
                cache_root = root / "recycled-staging"
                module = sys.modules[__name__]
                metrics = WaveformMetrics(
                    channel_peak_percentages=(50.0, 50.0),
                    peak_volume_percentage=50.0,
                    average_volume_percentage=25.0,
                    replaygain_factor=math.pow(10.0, 2.0 / 20.0),
                    longest_silence_seconds=0.0,
                    total_silence_seconds=0.0,
                )
                recolored: list[Path] = []

                def fake_generate(
                    _audio: Path,
                    *,
                    destination: Path,
                    **_kwargs,
                ) -> tuple[Path, None, WaveformMetrics]:
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(make_test_jpeg())
                    return destination, None, metrics

                with mock.patch.object(
                    module,
                    "waveform_staging_root",
                    return_value=cache_root,
                ), mock.patch.object(
                    module,
                    "waveform_replaygain_factor",
                    return_value=metrics.replaygain_factor,
                ), mock.patch.object(
                    module,
                    "prompt_for_approval",
                    return_value=True,
                ) as prompt, mock.patch.object(
                    module,
                    "generate_waveform_jpeg",
                    side_effect=fake_generate,
                ), mock.patch.object(
                    module,
                    "bake_replaygain_into_audio",
                    return_value=(root / "original.bak", 2.0),
                ) as baker, mock.patch.object(
                    module,
                    "recolor_before_baked_waveform",
                    side_effect=lambda path: recolored.append(path),
                ), mock.patch.object(
                    module,
                    "recolor_newly_baked_waveform",
                ) as green:
                    baked = bake_replaygain_for_batch(
                        [audio],
                        use_color=False,
                    )

                self.assertEqual([audio], baked)
                self.assertTrue(prompt.called)
                baker.assert_called_once()
                self.assertEqual(1, len(recolored))
                green.assert_called_once()
                self.assertTrue(recolored[0].is_file())
                self.assertTrue(green.call_args.args[0].is_file())

        def test_waveform_gain_prompt_bakes_then_shows_new_preview(self) -> None:
            metrics = WaveformMetrics(
                channel_peak_percentages=(50.0, 50.0),
                peak_volume_percentage=50.0,
                average_volume_percentage=12.0,
                replaygain_factor=math.pow(10.0, 3.0 / 20.0),
                longest_silence_seconds=0.0,
                total_silence_seconds=0.0,
            )
            refreshed_metrics = replace(
                metrics,
                peak_volume_percentage=70.6,
                replaygain_factor=1.0,
            )
            keys = iter(("b", "y", "n"))
            module = sys.modules[__name__]
            renderer = mock.Mock(return_value="mock Sixel")
            baker = mock.Mock(
                return_value=(Path("original.backup.flac"), 3.0)
            )
            generator = mock.Mock(
                return_value=(
                    Path("track.waveform.jpg"),
                    None,
                    refreshed_metrics,
                )
            )
            recolorer = mock.Mock()
            with tempfile.TemporaryDirectory() as temp:
                waveform = Path(temp) / "track.waveform.jpg"
                waveform.write_bytes(b"waveform fixture")
                generator.return_value = (
                    waveform,
                    None,
                    refreshed_metrics,
                )
                with mock.patch.object(
                    module,
                    "visible_console_size",
                    return_value=os.terminal_size((120, 40)),
                ), mock.patch.object(
                    module,
                    "recolor_before_baked_waveform",
                ), contextlib.redirect_stdout(io.StringIO()) as output:
                    decision, edits, reviewed = waveform_review_choice(
                        waveform,
                        Path("Track.flac"),
                        use_color=False,
                        key_reader=lambda: next(keys),
                        preview_renderer=renderer,
                        waveform_metrics=metrics,
                        gain_baker=baker,
                        waveform_generator=generator,
                        waveform_recolorer=recolorer,
                    )
                rendered_paths = [
                    call.args[0] for call in renderer.call_args_list
                ]
                self.assertEqual(waveform, rendered_paths[0])
                self.assertIn(
                    ".before-replaygain-bake",
                    rendered_paths[1].name,
                )
                self.assertEqual(waveform, rendered_paths[2])
            self.assertEqual(("fine", 0, Path("Track.flac")), (
                decision,
                edits,
                reviewed,
            ))
            baker.assert_called_once()
            generator.assert_called_once()
            recolorer.assert_called_once_with(waveform)
            self.assertEqual(3, renderer.call_count)
            self.assertIn("B=Bake ReplayGain", output.getvalue())
            self.assertIn("original red-to-purple waveform", output.getvalue())
            self.assertIn(
                "Comparison only — no response is needed",
                output.getvalue(),
            )
            self.assertIn("New waveform rendered in green", output.getvalue())
            self.assertIn(
                "fresh ReplayGain correction is +0.00 dB",
                output.getvalue(),
            )

        def test_waveform_review_defaults_to_current_folder(self) -> None:
            module = sys.modules[__name__]
            waveform_result = {
                "audio_files": 0,
                "fine": [],
                "problems": [],
                "edited": [],
                "failed": [],
                "staging_folder": "",
            }
            with mock.patch.object(
                shutil,
                "which",
                return_value=r"C:\util\ffmpeg.exe",
            ), mock.patch.object(
                module,
                "review_waveforms",
                return_value=waveform_result,
            ) as review:
                self.assertEqual(
                    0,
                    _main(["--review-waveforms", "--no-color"]),
                )
            review.assert_called_once()
            self.assertEqual(Path("."), review.call_args.args[0])

        def test_post_audit_waveform_offer_counts_before_prompt_and_can_run_or_be_suppressed(
            self,
        ) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                make_silent_flac(root, "Track [instrumental]")
                review_result = {
                    "audio_files": 1,
                    "fine": [str(root / "Track [instrumental].flac")],
                    "problems": [],
                    "edited": [],
                    "failed": [],
                    "staging_folder": str(root / "waveforms"),
                }
                reviewer = mock.Mock(return_value=review_result)
                output = io.StringIO()
                with mock.patch.object(
                    shutil,
                    "which",
                    return_value=r"C:\util\ffmpeg.exe",
                ), contextlib.redirect_stdout(output):
                    declined = offer_post_audit_waveform_review(
                        root,
                        interactive=True,
                        suppressed=False,
                        include_archives=False,
                        use_color=False,
                        workers=3,
                        key_reader=lambda: "n",
                        reviewer=reviewer,
                    )
                    accepted = offer_post_audit_waveform_review(
                        root,
                        interactive=True,
                        suppressed=False,
                        include_archives=True,
                        use_color=False,
                        workers=3,
                        key_reader=lambda: "y",
                        reviewer=reviewer,
                    )
                    suppressed = offer_post_audit_waveform_review(
                        root,
                        interactive=True,
                        suppressed=True,
                        include_archives=False,
                        use_color=False,
                        workers=3,
                        key_reader=lambda: (_ for _ in ()).throw(
                            AssertionError("Suppressed offer read a key")
                        ),
                        reviewer=reviewer,
                    )
                self.assertIsNone(declined)
                self.assertEqual(review_result, accepted)
                self.assertIsNone(suppressed)
                self.assertIn("1 total waveforms ➜ 1 to review / 0 already reviewed", output.getvalue())
                self.assertIn("Press “Y” to review the 1 un-reviewed waveform.", output.getvalue())
                self.assertIn("Press “F” to review all 1 waveform.", output.getvalue())
                self.assertIn("Run the interactive waveform review now? [Y/n/f]", output.getvalue())
                reviewer.assert_called_once()
                self.assertTrue(reviewer.call_args.kwargs["include_archives"])
                self.assertEqual(3, reviewer.call_args.kwargs["workers"])
                self.assertFalse(reviewer.call_args.kwargs["force_all"])
                self.assertTrue(
                    parse_args([".", "--no-review-waveforms"]).no_review_waveforms
                )
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit):
                        parse_args(
                            [
                                ".",
                                "--review-waveforms",
                                "--no-review-waveforms",
                            ]
                        )

        def test_post_audit_waveform_prompt_defaults_yes_and_f_forces_all(self) -> None:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(
                    "queued",
                    prompt_post_audit_waveform_review(
                        29, 11, 18, use_color=False, key_reader=lambda: "\r"
                    ),
                )
            rendered = output.getvalue()
            self.assertIn(
                "29 total waveforms ➜ 11 to review / 18 already reviewed",
                rendered,
            )
            self.assertIn(
                "Press “Y” to review the 11 un-reviewed waveforms.",
                rendered,
            )
            self.assertIn(
                "Press “F” to review all 29 waveforms.",
                rendered,
            )
            self.assertIn(
                "Run the interactive waveform review now? [Y/n/f]",
                rendered,
            )
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    "force_all",
                    prompt_post_audit_waveform_review(
                        29, 11, 18, use_color=False, key_reader=lambda: "f"
                    ),
                )
                self.assertEqual(
                    "no",
                    prompt_post_audit_waveform_review(
                        29, 11, 18, use_color=False, key_reader=lambda: "n"
                    ),
                )

        def test_post_audit_waveform_prompt_blinks_only_unreviewed_count_line(self) -> None:
            class TTYBuffer(io.StringIO):
                def isatty(self) -> bool:
                    return True

            output = TTYBuffer()
            with contextlib.redirect_stdout(output):
                choice = prompt_post_audit_waveform_review(
                    29, 11, 18, use_color=True, key_reader=lambda: "n"
                )
            self.assertEqual("no", choice)
            first_line = output.getvalue().splitlines()[0]
            self.assertIn(ANSI["blink"], first_line)
            self.assertIn("11", first_line)
            self.assertIn(ANSI["reset"], first_line)

        def test_zero_queued_waveform_offer_has_force_all(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                audio = make_silent_flac(root, "Approved [instrumental]")
                approvals = WaveformApprovalStore(root / "reviews.sqlite3")
                approvals.approve(audio)
                reviewer = mock.Mock(return_value={"audio_files": 1, "fine": []})
                output = io.StringIO()
                with mock.patch.object(
                    sys.modules[__name__],
                    "waveform_approval_database_path",
                    return_value=root / "reviews.sqlite3",
                ), mock.patch.object(
                    shutil, "which", return_value=r"C:\util\ffmpeg.exe"
                ), contextlib.redirect_stdout(output):
                    result = offer_post_audit_waveform_review(
                        root,
                        interactive=True,
                        suppressed=False,
                        include_archives=False,
                        use_color=False,
                        workers=2,
                        key_reader=lambda: "f",
                        reviewer=reviewer,
                    )
                self.assertEqual({"audio_files": 1, "fine": []}, result)
                self.assertIn("1 total waveforms ➜ 0 to review / 1 already reviewed", output.getvalue())
                self.assertIn("Press “Y” to review the 0 un-reviewed waveforms.", output.getvalue())
                self.assertIn("Press “F” to review all 1 waveform.", output.getvalue())
                self.assertIn("Run the interactive waveform review now? [Y/n/f]", output.getvalue())
                self.assertTrue(reviewer.call_args.kwargs["force_all"])

        def test_waveform_jpeg_readiness_rejects_partial_and_accepts_complete(self) -> None:
            if Image is None:
                self.skipTest("Pillow is required")
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                partial = root / "partial.jpg"
                partial.write_bytes(b"\xff\xd8\xff")
                with self.assertRaises(Exception):
                    ensure_waveform_jpeg_ready(partial)
                ready = root / "ready.jpg"
                Image.new("RGB", (32, 12), "black").save(ready, format="JPEG")
                size, modified = ensure_waveform_jpeg_ready(ready)
                self.assertGreater(size, 0)
                self.assertGreater(modified, 0)

        def test_waveform_review_inline_layout_uses_live_rows_below_cursor(self) -> None:
            cases = (
                ConsoleViewportState(200, 50, 0, 5, 0, 49),
                ConsoleViewportState(200, 50, 0, 28, 0, 49),
                ConsoleViewportState(200, 50, 0, 44, 0, 49),
                ConsoleViewportState(110, 28, 0, 22, 0, 27),
            )
            for state in cases:
                with self.subTest(state=state):
                    layout = waveform_review_layout_plan(
                        "very_long_album_track_name_that_can_wrap_in_the_review_prompt.flac",
                        index=1,
                        total=29,
                        comparison_active=True,
                        excessive_silence=False,
                        allow_bake_gain=True,
                        viewport_state=state,
                    )
                    self.assertEqual(2, layout.graph_count)
                    self.assertGreaterEqual(layout.graph_rows, 1)
                    self.assertLessEqual(layout.graph_rows, state.rows)
                    self.assertEqual(
                        max(0, layout.required_rows - state.rows_available_from_cursor),
                        layout.scroll_rows,
                    )
                    self.assertLessEqual(
                        layout.required_rows,
                        state.rows_available_from_cursor + layout.scroll_rows,
                    )

        def test_waveform_review_inline_scroll_never_clears_or_uses_alternate_screen(self) -> None:
            layout = WaveformReviewLayout(
                graph_rows=2, graph_count=2, fixed_text_rows=6,
                required_rows=12, rows_available_from_cursor=8,
                scroll_rows=4, terminal_columns=200, terminal_rows=50,
            )
            stream = io.StringIO()
            moved = ensure_waveform_review_vertical_room(layout, stream=stream)
            self.assertEqual(0, moved)
            rendered = stream.getvalue()
            self.assertEqual("", rendered)
            self.assertNotIn("?1049", rendered)
            self.assertNotIn("2J", rendered)
            self.assertNotIn("\x1b[H", rendered)

        def test_waveform_review_prompt_wrapping_is_in_vertical_budget(self) -> None:
            narrow = ConsoleViewportState(82, 32, 0, 8, 0, 31)
            wide = ConsoleViewportState(220, 32, 0, 8, 0, 31)
            narrow_layout = waveform_review_layout_plan(
                "01_An_Extremely_Long_Song_Name_With_Many_Words_And_Details.flac",
                index=3, total=29, comparison_active=True,
                excessive_silence=True, allow_bake_gain=True,
                viewport_state=narrow,
            )
            wide_layout = waveform_review_layout_plan(
                "01_An_Extremely_Long_Song_Name_With_Many_Words_And_Details.flac",
                index=3, total=29, comparison_active=True,
                excessive_silence=True, allow_bake_gain=True,
                viewport_state=wide,
            )
            self.assertGreater(narrow_layout.fixed_text_rows, wide_layout.fixed_text_rows)
            self.assertLessEqual(narrow_layout.required_rows, narrow.rows)
            self.assertLessEqual(wide_layout.required_rows, wide.rows)

        def test_waveform_geometry_halves_v113_widths_without_forcing_height(self) -> None:
            module = sys.modules[__name__]
            with mock.patch.object(
                module, "visible_console_size",
                return_value=os.terminal_size((200, 60)),
            ), mock.patch.object(
                module, "windows_console_font_cell_size",
                return_value=(10, 20),
            ):
                classic = artwork_preview_geometry(
                    indent_columns=12,
                    right_margin_columns=1,
                    reserved_text_rows=9,
                )
                single = waveform_preview_geometry(WAVEFORM_REVIEW_SCALE)
                pair = waveform_preview_geometry(WAVEFORM_COMPARISON_SCALE)

            self.assertEqual(0.30, WAVEFORM_REVIEW_WIDTH_SCALE)
            self.assertEqual(0.40, WAVEFORM_COMPARISON_WIDTH_SCALE)
            self.assertEqual(1.0, WAVEFORM_REVIEW_HEIGHT_SCALE)
            self.assertEqual(1.0, WAVEFORM_COMPARISON_HEIGHT_SCALE)
            self.assertEqual(round(classic.terminal_columns * 0.30), single.columns)
            self.assertEqual(classic.rows, single.rows)
            self.assertEqual(single.columns * 10, single.pixel_width)
            self.assertEqual(single.rows * 20, single.pixel_height)
            self.assertEqual(round(classic.terminal_columns * 0.40), pair.columns)
            self.assertEqual(classic.rows, pair.rows)
            self.assertEqual(pair.columns * 10, pair.pixel_width)
            self.assertEqual(pair.rows * 20, pair.pixel_height)

        def test_v131_uses_exactly_half_v113_widths(self) -> None:
            module = sys.modules[__name__]
            with mock.patch.object(
                module, "visible_console_size",
                return_value=os.terminal_size((200, 60)),
            ), mock.patch.object(
                module, "windows_console_font_cell_size",
                return_value=(10, 20),
            ):
                classic = artwork_preview_geometry(
                    indent_columns=12, right_margin_columns=1, reserved_text_rows=9
                )
                pair = waveform_preview_geometry(WAVEFORM_COMPARISON_WIDTH_SCALE)
                single = waveform_preview_geometry(WAVEFORM_REVIEW_WIDTH_SCALE)
            self.assertEqual(800, pair.pixel_width)
            self.assertEqual(pair.rows * 20, pair.pixel_height)
            self.assertEqual(600, single.pixel_width)
            self.assertEqual(single.rows * 20, single.pixel_height)

        def test_waveform_geometry_keeps_real_cell_height_for_cursor_math(self) -> None:
            """Geometry retains the measured cell height; raster aspect controls output."""
            module = sys.modules[__name__]
            with mock.patch.object(
                module, "visible_console_size",
                return_value=os.terminal_size((200, 60)),
            ), mock.patch.object(
                module, "windows_console_font_cell_size",
                return_value=(10, 40),
            ):
                pair = waveform_preview_geometry(WAVEFORM_COMPARISON_SCALE)
            self.assertEqual(80, pair.columns)
            self.assertEqual(51, pair.rows)
            self.assertEqual(800, pair.pixel_width)
            self.assertEqual(2040, pair.pixel_height)

        def test_v138_cursor_rows_never_use_more_than_probe_confirmed_20px(self) -> None:
            """Keep the bitmap and conservatively reserve from 20px text rows."""
            module = sys.modules[__name__]
            with mock.patch.object(
                module, "visible_console_size",
                return_value=os.terminal_size((200, 60)),
            ), mock.patch.object(
                module, "windows_console_font_cell_size",
                return_value=(10, 40),
            ):
                geometry = waveform_preview_geometry(
                    WAVEFORM_COMPARISON_WIDTH_FRACTION
                )
            payload = b'\x1bP0;1;0q"1;1;800;280#0~\x1b\\'
            self.assertEqual((800, 2040), (
                geometry.pixel_width, geometry.pixel_height
            ))
            with mock.patch.object(
                module,
                "_WAVEFORM_SIXEL_CURSOR_CELL_HEIGHT_PIXELS",
                None,
            ):
                self.assertEqual(14, sixel_display_rows(payload, geometry))
            with mock.patch.object(
                module,
                "_WAVEFORM_SIXEL_CURSOR_CELL_HEIGHT_PIXELS",
                20,
            ):
                self.assertEqual(14, sixel_display_rows(payload, geometry))
            self.assertEqual((800, 280), sixel_payload_pixel_size(payload))

        def test_v136_comparison_is_one_compact_contact_sheet_with_prompt_pad(self) -> None:
            """Before/after placement is encoded into one probe-validated frame."""
            if Image is None:
                self.skipTest("Pillow is required")
            module = sys.modules[__name__]
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                before = root / "before.jpg"
                after = root / "after.jpg"
                sheet = root / "sheet.jpg"
                Image.new("RGB", (2000, 700), (220, 35, 150)).save(
                    before, format="JPEG", quality=100, subsampling=0
                )
                Image.new("RGB", (2000, 700), (30, 220, 210)).save(
                    after, format="JPEG", quality=100, subsampling=0
                )
                create_waveform_comparison_contact_sheet(before, after, sheet)
                with Image.open(sheet) as contact:
                    self.assertEqual((2000, 790), contact.size)
                    self.assertLess(max(contact.getpixel((1000, 365))), 20)
                    self.assertLess(max(contact.getpixel((1000, 760))), 20)
                with mock.patch.object(
                    module, "visible_console_size",
                    return_value=os.terminal_size((200, 60)),
                ), mock.patch.object(
                    module, "windows_console_font_cell_size",
                    return_value=(10, 40),
                ), mock.patch.object(
                    module,
                    "_WAVEFORM_SIXEL_CURSOR_CELL_HEIGHT_PIXELS",
                    20,
                ):
                    prepared = prepare_waveform_preview(
                        sheet,
                        use_color=True,
                        width_fraction=WAVEFORM_COMPARISON_WIDTH_FRACTION,
                    )
                    payload = prepared.sixel_payload or b""
                    frame, reserved_rows = sixel_terminal_frame(
                        payload, geometry=prepared.geometry
                    )
            self.assertEqual((800, 316), sixel_payload_pixel_size(payload))
            self.assertEqual(17, reserved_rows)
            self.assertTrue(frame.startswith(b"\r\n" * reserved_rows))
            self.assertTrue(frame.endswith(b"\x1b[17B\r"))

        def test_prepare_waveform_preview_accepts_explicit_height_scale(self) -> None:
            """Pre-render call sites may pass the matching height scale."""
            module = sys.modules[__name__]
            fake_geometry = ArtworkPreviewGeometry(
                terminal_columns=100, terminal_rows=50, indent_columns=12,
                columns=40, rows=20, pixel_width=400, pixel_height=400,
            )
            with mock.patch.object(module, "ensure_waveform_jpeg_ready"), mock.patch.object(
                module, "waveform_preview_geometry", return_value=fake_geometry
            ) as geometry_mock, mock.patch.object(
                module, "sixel_preview_bytes", return_value=b"SIXEL"
            ):
                prepared = prepare_waveform_preview(
                    Path("dummy.jpg"),
                    use_color=True,
                    width_fraction=WAVEFORM_COMPARISON_WIDTH_FRACTION,
                    height_scale=WAVEFORM_COMPARISON_HEIGHT_SCALE,
                )
            geometry_mock.assert_called_once_with(
                WAVEFORM_COMPARISON_WIDTH_FRACTION,
                height_rows=None,
                height_scale=WAVEFORM_COMPARISON_HEIGHT_SCALE,
            )
            self.assertEqual(b"SIXEL", prepared.sixel_payload)

        def test_waveform_visual_regression_restored_pair_size_preserves_right_labels(self) -> None:
            """Render a half-size comparison and verify its metrics survive."""
            if Image is None or ImageDraw is None:
                self.skipTest("Pillow is required")
            module = sys.modules[__name__]
            with tempfile.TemporaryDirectory() as temp:
                waveform = Path(temp) / "visual-regression.jpg"
                image = Image.new("RGB", (WAVEFORM_JPEG_WIDTH, WAVEFORM_JPEG_HEIGHT), "black")
                draw = ImageDraw.Draw(image)
                cyan = waveform_channel_rgb(0)
                mid = WAVEFORM_JPEG_HEIGHT // 2
                draw.rectangle(
                    (8, mid - 150, WAVEFORM_PLOT_WIDTH - 12, mid + 150),
                    fill=cyan,
                )
                image.save(waveform, format="JPEG", quality=95)
                metrics = WaveformMetrics(
                    channel_peak_percentages=(100.0,),
                    peak_volume_percentage=100.0,
                    average_volume_percentage=65.0,
                    replaygain_factor=1.0,
                    longest_silence_seconds=0.0,
                    total_silence_seconds=0.0,
                )
                annotate_waveform_peak_guides(waveform, metrics)
                with mock.patch.object(
                    module, "visible_console_size",
                    return_value=os.terminal_size((200, 60)),
                ), mock.patch.object(
                    module, "windows_console_font_cell_size",
                    return_value=(10, 20),
                ):
                    geometry = waveform_preview_geometry(WAVEFORM_COMPARISON_SCALE)
                    with Image.open(waveform) as source:
                        raster = width_filling_preview_image(
                            source.convert("RGB"),
                            geometry.pixel_width,
                            geometry.pixel_height,
                        )
                    prepared = PreparedArtworkPreview(
                        mode="Sixel",
                        geometry=geometry,
                        sixel_payload=sixel_preview_bytes(
                            waveform,
                            geometry=geometry,
                            stretch_to_width=True,
                        ),
                    )

            # v113 comparison width was 160 columns/1600 px here. v131 halves
            # that to 80/800 and derives the 280-pixel height from 2000x700.
            self.assertEqual(80, geometry.columns)
            self.assertEqual(51, geometry.rows)
            self.assertEqual(800, geometry.pixel_width)
            self.assertEqual(1020, geometry.pixel_height)
            self.assertEqual((800, 280), raster.size)
            gutter_x = round(
                geometry.pixel_width * WAVEFORM_PLOT_WIDTH / WAVEFORM_JPEG_WIDTH
            )
            gutter = raster.crop((gutter_x, 0, raster.width, raster.height))
            upper = gutter.crop((0, 0, gutter.width, raster.height // 3))
            middle = gutter.crop((0, raster.height // 3, gutter.width, raster.height * 2 // 3))
            lower = gutter.crop((0, raster.height * 2 // 3, gutter.width, raster.height))

            # The 13% source gutter remains 104 physical pixels at 800px wide.
            self.assertGreaterEqual(gutter.width, 100)

            def visible_rows(region) -> int:
                rows = 0
                px = region.load()
                for y in range(region.height):
                    if any(max(px[x, y]) >= 70 for x in range(region.width)):
                        rows += 1
                return rows

            self.assertGreaterEqual(visible_rows(upper), 8)
            # The five-line peak/average/ReplayGain/gain/silence summary lives
            # in the middle third; require substantial visible text there.
            self.assertGreaterEqual(visible_rows(middle), 50)
            self.assertGreaterEqual(visible_rows(lower), 8)
            self.assertEqual(
                (800, 280),
                sixel_payload_pixel_size(prepared.sixel_payload or b""),
            )


        def test_waveform_sixel_payload_keeps_right_side_metric_summary_at_half_scale(self) -> None:
            """The metric gutter is present in the actual Sixel payload, not just the JPEG."""
            if Image is None or ImageDraw is None:
                self.skipTest("Pillow is required")
            module = sys.modules[__name__]
            with tempfile.TemporaryDirectory() as temp:
                waveform = Path(temp) / "metric-gutter.jpg"
                image = Image.new("RGB", (WAVEFORM_JPEG_WIDTH, WAVEFORM_JPEG_HEIGHT), "black")
                draw = ImageDraw.Draw(image)
                draw.rectangle((8, 150, WAVEFORM_PLOT_WIDTH - 12, 550), fill=waveform_channel_rgb(0))
                image.save(waveform, format="JPEG", quality=95)
                metrics = WaveformMetrics(
                    channel_peak_percentages=(100.0,), peak_volume_percentage=100.0,
                    average_volume_percentage=65.0, replaygain_factor=1.0,
                    longest_silence_seconds=0.0, total_silence_seconds=0.0,
                )
                annotate_waveform_peak_guides(waveform, metrics)
                with mock.patch.object(module, "visible_console_size", return_value=os.terminal_size((200, 60))), mock.patch.object(
                    module, "windows_console_font_cell_size", return_value=(10, 20)
                ):
                    prepared = prepare_waveform_preview(
                        waveform, use_color=True,
                        width_fraction=WAVEFORM_COMPARISON_WIDTH_FRACTION,
                    )
            payload = prepared.sixel_payload or b""
            self.assertEqual((800, 280), sixel_payload_pixel_size(payload))
            # Our encoder emits visible runs out into the final 5% of the raster
            # only because the percentage/metric text occupies that gutter.
            body = payload.decode("ascii", errors="ignore")
            raster_width = 800
            x = 0
            max_ink_x = 0
            i = body.find('"1;1;800;280')
            i = 0 if i < 0 else i
            while i < len(body):
                ch = body[i]
                if ch == "\x1b":
                    # Skip the opening DCS; stop only on the final ESC \\.
                    if i + 1 < len(body) and body[i + 1] == "\\":
                        break
                    i += 1
                    continue
                if ch == "$":
                    x = 0; i += 1; continue
                if ch == "-":
                    x = 0; i += 1; continue
                if ch == "#":
                    i += 1
                    while i < len(body) and body[i].isdigit(): i += 1
                    if i < len(body) and body[i] == ";":
                        while i < len(body) and body[i] not in "#$-!?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~\x1b": i += 1
                    continue
                if ch == "!":
                    j = i + 1
                    while j < len(body) and body[j].isdigit(): j += 1
                    count = int(body[i + 1:j] or "1")
                    if j < len(body) and 63 <= ord(body[j]) <= 126 and ord(body[j]) != 63:
                        max_ink_x = max(max_ink_x, x + count - 1)
                    x += count; i = j + 1; continue
                if 63 <= ord(ch) <= 126:
                    if ord(ch) != 63:
                        max_ink_x = max(max_ink_x, x)
                    x += 1
                i += 1
            self.assertGreater(max_ink_x, int(raster_width * 0.95))


        def test_waveform_review_heading_has_three_blank_lines_and_comparison_has_no_after_baking_narration(self) -> None:
            source = Path(__file__).read_text(encoding="utf-8")
            self.assertIn("for _ in range(3):\n        print()\n    print(\n        \"\\n\".join(\n            double_height_gradient_section(\n                \"Waveform review\"", source)
            review_source = source.split("def review_waveforms(", 1)[1].split("\ndef ", 1)[0]
            self.assertNotIn(
                "After baking: the cyan-to-green waveform below is the current audio and is the one being reviewed.",
                review_source,
            )

        def test_non_waveform_chafa_geometry_still_uses_shared_helper(self) -> None:
            class FakeLive:
                def chafa_options_for(self, reserved_rows: int) -> str:
                    self.reserved_rows = reserved_rows
                    return "--view-size=120x40 --font-ratio=10/20"
            fake = FakeLive()
            module = sys.modules[__name__]
            geometry = ArtworkPreviewGeometry(
                terminal_columns=160, terminal_rows=50, indent_columns=0,
                columns=120, rows=40, pixel_width=1200, pixel_height=800,
            )
            with mock.patch.object(module, "query_terminal_geometry", return_value=fake):
                options = chafa_sixel_geometry_options(geometry)
            self.assertEqual(ART_PREVIEW_RESERVED_TEXT_ROWS, fake.reserved_rows)
            self.assertTrue(any(option.startswith("--view-size=") for option in options))
            self.assertIn("--font-ratio=10/20", options)

        def test_waveform_geometry_reuses_shared_classic_metrics_without_extra_dpi_scaling(self) -> None:
            """The restored waveform size must come from shared classic geometry only."""
            module = sys.modules[__name__]
            for reported_scale in (1.0, 1.5, 2.0):
                with self.subTest(reported_scale=reported_scale), mock.patch.object(
                    module,
                    "visible_console_size",
                    return_value=os.terminal_size((200, 60)),
                ), mock.patch.object(
                    module,
                    "windows_console_font_cell_size",
                    return_value=(5, 10),
                ), mock.patch.object(
                    module,
                    "windows_console_pixel_scale_factor",
                    return_value=reported_scale,
                ):
                    comparison = waveform_preview_geometry(
                        WAVEFORM_COMPARISON_SCALE
                    )
                self.assertEqual(80, comparison.columns)
                self.assertEqual(51, comparison.rows)
                self.assertEqual(400, comparison.pixel_width)
                self.assertEqual(510, comparison.pixel_height)


        def test_sixel_terminal_frame_cannot_leave_following_text_inside_graph(self) -> None:
            """Reserve first, paint above, then return to the prompt row."""
            geometry = ArtworkPreviewGeometry(
                terminal_columns=200,
                terminal_rows=60,
                indent_columns=12,
                columns=160,
                rows=6,
                pixel_width=1600,
                pixel_height=120,
            )
            payload = b'\x1bP9;1;0q"1;1;1600;120#0;2;0;0;0\x1b\\'
            frame, reserved_rows = sixel_terminal_frame(
                payload, geometry=geometry
            )
            self.assertEqual(7, reserved_rows)
            self.assertTrue(frame.startswith(b"\r\n" * reserved_rows))
            self.assertIn(b"\x1b[7A\x1b7\r", frame)
            self.assertIn(payload + b"\x1b8", frame)
            self.assertTrue(frame.endswith(b"\x1b[7B\r"))

        def test_sixel_row_reservation_uses_declared_raster_height(self) -> None:
            """Reserve from the width-derived raster height, as v113 did."""
            module = sys.modules[__name__]
            geometry = ArtworkPreviewGeometry(
                terminal_columns=200,
                terminal_rows=60,
                indent_columns=12,
                columns=100,
                rows=13,
                pixel_width=1000,
                pixel_height=260,
            )
            payload = b'\x1bP9;1;0q"1;1;1000;260#0;2;0;0;0\x1b\\'
            with mock.patch.object(
                module, "windows_console_font_cell_size", return_value=None
            ):
                frame, reserved_rows = sixel_terminal_frame(
                    payload, geometry=geometry
                )
            self.assertEqual(14, reserved_rows)
            self.assertTrue(frame.startswith(b"\r\n" * reserved_rows))
            self.assertTrue(frame.endswith(b"\x1b[14B\r"))

        def test_first_waveform_render_finishes_before_later_jobs_are_submitted(self) -> None:
            events: list[str] = []

            class FakeFuture:
                def __init__(self, name: str, destination: Path) -> None:
                    self.name = name
                    self.destination = destination

                def result(self):
                    events.append(f"result:{self.name}")
                    return self.destination, None, mock.Mock()

            class FakeExecutor:
                def submit(self, _func, upcoming, **kwargs):
                    events.append(f"submit:{upcoming.name}")
                    return FakeFuture(upcoming.name, kwargs["destination"])

            tracks = [
                Path("first.flac"),
                Path("second.flac"),
                Path("third.flac"),
            ]
            with tempfile.TemporaryDirectory() as temp:
                futures, rendered = prioritized_waveform_render_futures(
                    tracks,
                    FakeExecutor(),
                    Path(temp),
                    acceptable_silence_seconds=10.0,
                    first_ready_callback=lambda path, _result: events.append(
                        f"preview:{path.name}"
                    ),
                )
            self.assertEqual(
                [
                    "submit:first.flac",
                    "result:first.flac",
                    "preview:first.flac",
                    "submit:second.flac",
                    "submit:third.flac",
                ],
                events,
            )
            self.assertIn(tracks[0], rendered)
            self.assertEqual(set(tracks), set(futures))

        def test_waveform_geometry_uses_uniform_review_and_comparison_scales(self) -> None:
            module = sys.modules[__name__]
            self.assertEqual(0.30, WAVEFORM_REVIEW_SCALE)
            self.assertEqual(0.40, WAVEFORM_COMPARISON_SCALE)
            self.assertEqual(1.0, WAVEFORM_REVIEW_HEIGHT_SCALE)
            self.assertEqual(1.0, WAVEFORM_COMPARISON_HEIGHT_SCALE)
            with mock.patch.object(
                module,
                "visible_console_size",
                return_value=os.terminal_size((200, 60)),
            ), mock.patch.object(
                module,
                "windows_console_font_cell_size",
                return_value=(10, 20),
            ):
                geometry = waveform_preview_geometry(WAVEFORM_REVIEW_SCALE)
                comparison = waveform_preview_geometry(WAVEFORM_COMPARISON_SCALE)
            self.assertEqual(12, geometry.indent_columns)
            self.assertEqual((60, 51, 600, 1020), (
                geometry.columns, geometry.rows, geometry.pixel_width, geometry.pixel_height
            ))
            self.assertEqual((80, 51, 800, 1020), (
                comparison.columns, comparison.rows,
                comparison.pixel_width, comparison.pixel_height
            ))
            source = Image.new("RGB", (1800, 700), "black")
            width_filled = width_filling_preview_image(
                source,
                geometry.pixel_width,
                geometry.pixel_height,
            )
            self.assertEqual(geometry.pixel_width, width_filled.width)
            self.assertEqual(
                round(700 * geometry.pixel_width / 1800),
                width_filled.height,
            )


        def test_waveform_preview_uses_pixel_aware_builtin_sixel(self) -> None:
            if Image is None:
                self.skipTest("Pillow is required")
            module = sys.modules[__name__]
            with tempfile.TemporaryDirectory() as temp:
                waveform = Path(temp) / "waveform.jpg"
                Image.new("RGB", (2000, 700), "black").save(
                    waveform, format="JPEG"
                )
                with mock.patch.object(
                    module,
                    "visible_console_size",
                    return_value=os.terminal_size((200, 60)),
                ), mock.patch.object(
                    module,
                    "windows_console_font_cell_size",
                    return_value=(10, 20),
                ), mock.patch.object(
                    module,
                    "chafa_executable",
                ) as chafa:
                    prepared = prepare_waveform_preview(
                        waveform,
                        use_color=True,
                        width_fraction=WAVEFORM_COMPARISON_WIDTH_FRACTION,
                    )
            self.assertEqual("Sixel", prepared.mode)
            self.assertEqual(80, prepared.geometry.columns)
            self.assertEqual(51, prepared.geometry.rows)
            self.assertEqual(800, prepared.geometry.pixel_width)
            self.assertEqual(1020, prepared.geometry.pixel_height)
            self.assertIn(b'"1;1;800;280', prepared.sixel_payload or b"")
            chafa.assert_not_called()

        def test_waveform_preview_scales_width_and_preserves_source_aspect(self) -> None:
            module = sys.modules[__name__]
            with mock.patch.object(
                module,
                "visible_console_size",
                return_value=os.terminal_size((200, 60)),
            ), mock.patch.object(
                module,
                "windows_console_font_cell_size",
                return_value=(10, 20),
            ):
                normal = waveform_preview_geometry(WAVEFORM_REVIEW_SCALE)
                comparison = waveform_preview_geometry(WAVEFORM_COMPARISON_SCALE)
            self.assertEqual((60, 51, 600, 1020), (
                normal.columns, normal.rows, normal.pixel_width, normal.pixel_height
            ))
            self.assertEqual((80, 51, 800, 1020), (
                comparison.columns, comparison.rows,
                comparison.pixel_width, comparison.pixel_height
            ))

        def test_waveform_sixel_path_restores_v113_aspect_and_opaque_background(self) -> None:
            """Regression harness for the restored v113 bitmap/Sixel pipeline."""
            if Image is None:
                self.skipTest("Pillow is required")
            module = sys.modules[__name__]
            with tempfile.TemporaryDirectory() as temp:
                waveform = Path(temp) / "waveform.jpg"
                image = Image.new("RGB", (2000, 700), "black")
                if ImageDraw is not None:
                    draw = ImageDraw.Draw(image)
                    # Known content at the top, middle and bottom must all survive.
                    draw.rectangle((0, 0, 1999, 35), fill=(240, 50, 180))
                    draw.rectangle((0, 332, 1999, 367), fill=(50, 230, 210))
                    draw.rectangle((0, 664, 1999, 699), fill=(240, 220, 50))
                image.save(waveform, format="JPEG", quality=95)
                with mock.patch.object(
                    module, "visible_console_size",
                    return_value=os.terminal_size((200, 60)),
                ), mock.patch.object(
                    module, "windows_console_font_cell_size",
                    return_value=(10, 20),
                ), mock.patch.object(
                    module, "windows_console_pixel_scale_factor",
                    return_value=1.0,
                ):
                    started = time.perf_counter()
                    prepared = prepare_waveform_preview(
                        waveform,
                        use_color=True,
                        width_fraction=WAVEFORM_COMPARISON_WIDTH_FRACTION,
                    )
                    elapsed = time.perf_counter() - started
            payload = prepared.sixel_payload or b""
            self.assertTrue(payload.startswith(b"\x1bP0;1;0q"))
            self.assertEqual((800, 280), sixel_payload_pixel_size(payload))
            self.assertEqual(math.ceil(280 / 6) - 1, payload.count(b"-"))
            # 280 physical pixels / at most 20 pixels per terminal row needs
            # at least 14 rows; a smaller measured cell safely reserves more.
            self.assertGreaterEqual(
                sixel_display_rows(payload, prepared.geometry), 14
            )
            # This is intentionally generous for CI; the old 1600x560/64-color
            # dithered path is several times slower and produces a much larger payload.
            self.assertLess(elapsed, 2.0)
            self.assertLess(len(payload), 500_000)

        def test_sixel_cursor_advance_matches_declared_raster_height(self) -> None:
            geometry = ArtworkPreviewGeometry(
                terminal_columns=200,
                terminal_rows=60,
                indent_columns=12,
                columns=160,
                rows=51,
                pixel_width=1600,
                pixel_height=1020,
            )
            payload = b'\x1bPq"1;1;1600;560#0~\x1b\\'
            self.assertEqual((1600, 560), sixel_payload_pixel_size(payload))
            self.assertEqual(28, sixel_display_rows(payload, geometry))

        def test_waveform_comparison_header_labels_before_and_after_without_renderer_status(self) -> None:
            plain = waveform_review_header(
                1, 11, comparison_active=True, use_color=False
            )
            self.assertEqual(
                "        🎛️ Waveform 1/11 (before, after):",
                plain,
            )
            colored = waveform_review_header(
                2, 7, comparison_active=True, use_color=True
            )
            stripped = re.sub(
                r"\x1b(?:\[[0-?]*[ -/]*[@-~]|#[34])", "", colored
            )
            self.assertEqual(
                "        🎛️ Waveform 2/7 (before, after):",
                stripped,
            )

        def test_wrapped_prompt_erases_every_rendered_row(self) -> None:
            module = sys.modules[__name__]
            prompt = "A deliberately long prompt " * 4
            with mock.patch.object(
                module,
                "visible_console_size",
                return_value=os.terminal_size((20, 30)),
            ), contextlib.redirect_stdout(io.StringIO()) as output:
                erase_wrapped_console_text(prompt)
            expected_rows = rendered_console_rows(prompt, 20)
            self.assertGreater(expected_rows, 1)
            self.assertEqual(
                expected_rows - 1,
                output.getvalue().count("\033[1A"),
            )
            self.assertEqual(
                expected_rows,
                output.getvalue().count(ANSI["erase_line"]),
            )
            question = "Does this waveform show a problem in Track.flac?"
            with mock.patch.object(
                module,
                "visible_console_size",
                return_value=os.terminal_size((80, 30)),
            ):
                wrapped = prompt_with_option_legend(
                    urgent_prompt_text(question, False),
                    waveform_review_choices(False),
                    indent="            ",
                )
            wrapped_lines = wrapped.rstrip().splitlines()
            self.assertGreaterEqual(len(wrapped_lines), 2)
            self.assertTrue(
                wrapped_lines[0].startswith(
                    "            ❓ Does this waveform"
                )
            )
            for continuation in wrapped_lines[1:]:
                self.assertTrue(
                    continuation.startswith(
                        "               "
                    )
                )
            styled_question = urgent_prompt_text(
                question,
                True,
                faint_italic_spans=("Track.flac",),
            )
            self.assertIn(
                f"{ANSI['dim']}{ANSI['italic']}",
                styled_question,
            )
            self.assertIn("Track.flac", styled_question)
            rendering = waveform_rendering_status(
                "A very long Ghosts (2023) title for wrapping.mp3",
                False,
                terminal_columns=34,
            )
            self.assertTrue(
                rendering.startswith("            ⏳ Rendering: ")
            )
            self.assertEqual(1, len(rendering.splitlines()))
            rendered = waveform_rendered_status(
                "A very long Ghosts (2023) title for wrapping.mp3",
                False,
                terminal_columns=34,
            )
            self.assertTrue(rendered.startswith("            ✅ Rendered: "))

        def test_waveform_diagnostic_can_edit_view_and_mark_problem(
            self,
        ) -> None:
            waveform = Path(r"C:\Temp\track.waveform.jpg")
            audio = Path(r"C:\Music\Track.flac")
            renamed_audio = audio.with_name("Track [waveform problem].flac")
            keys = iter(("p", "e", "v", "y", "y", "y"))
            calls = {
                "render": 0,
                "edit": 0,
                "retreat": 0,
                "preview": 0,
                "rename": 0,
                "view": 0,
            }

            def count(name: str, result):
                calls[name] += 1
                return result

            with contextlib.redirect_stdout(io.StringIO()) as output:
                decision, edits, reviewed_path = waveform_review_choice(
                    waveform,
                    audio,
                    use_color=False,
                    key_reader=lambda: next(keys),
                    preview_renderer=lambda path, *, use_color: count(
                        "render", "mock Sixel"
                    ),
                    image_viewer=lambda path: count(
                        "view", Path(r"C:\util\IrfanView.exe")
                    ),
                    audio_editor=lambda path: count(
                        "edit", Path(r"C:\Program Files\Adobe\Audition.exe")
                    ),
                    audio_retreater=lambda path, **_kwargs: count(
                        "retreat", []
                    ),
                    waveform_generator=lambda path, **_kwargs: (
                        waveform,
                        None,
                        WaveformMetrics(
                            channel_peak_percentages=(50.0, 50.0),
                            peak_volume_percentage=50.0,
                            average_volume_percentage=20.0,
                            replaygain_factor=1.0,
                            longest_silence_seconds=0.0,
                            total_silence_seconds=0.0,
                        ),
                    ),
                    audio_previewer=lambda path: count(
                        "preview", Path(r"C:\BAT\play_audio_file.py")
                    ),
                    problem_renamer=lambda path, **_kwargs: count(
                        "rename",
                        renamed_audio,
                    ),
                )
            self.assertEqual("problem", decision)
            self.assertEqual(2, edits)
            self.assertEqual(renamed_audio, reviewed_path)
            self.assertEqual(
                {
                    "render": 2,
                    "edit": 2,
                    "retreat": 2,
                    "preview": 1,
                    "rename": 1,
                    "view": 1,
                },
                calls,
            )
            rendered = output.getvalue()
            self.assertIn("N=It’s fine", rendered)
            self.assertIn("Y=There is a problem", rendered)
            self.assertIn("P=Preview audio", rendered)
            self.assertIn("E=Edit audio", rendered)
            self.assertIn("V=View fullscreen", rendered)
            self.assertIn(
                "Audio preview ended in play_audio_file.py",
                rendered,
            )
            self.assertIn("Yes — there is a problem.", rendered)
            self.assertIn("Want to edit this audio file now?", rendered)
            self.assertIn(
                "Want to rename this audio file to flag the problem?",
                rendered,
            )

        def test_excessive_silence_defaults_enter_to_audio_editor(
            self,
        ) -> None:
            keys = iter(("\r", "n"))
            editor = mock.Mock(
                return_value=Path(r"C:\Program Files\Adobe\Audition.exe")
            )
            with contextlib.redirect_stdout(io.StringIO()) as output:
                decision, edits, reviewed_path = waveform_review_choice(
                    Path(r"C:\Temp\track.waveform.jpg"),
                    Path(r"C:\Music\Track.flac"),
                    use_color=False,
                    key_reader=lambda: next(keys),
                    preview_renderer=lambda _path, *, use_color: "mock Sixel",
                    audio_editor=editor,
                    audio_retreater=lambda _path, **_kwargs: [],
                    excessive_silence=True,
                    longest_silence_seconds=12.5,
                    acceptable_silence_seconds=10.0,
                )
            self.assertEqual("fine", decision)
            self.assertEqual(1, edits)
            self.assertEqual(Path(r"C:\Music\Track.flac"), reviewed_path)
            editor.assert_called_once_with(Path(r"C:\Music\Track.flac"))
            self.assertIn("ENTER/E=Edit audio", output.getvalue())
            self.assertIn(
                "exceeding the 10s limit",
                output.getvalue(),
            )

        def test_editor_completion_requires_space_and_rejects_enter(
            self,
        ) -> None:
            module = sys.modules[__name__]
            keys = iter(("\r", "x", " "))
            with mock.patch.object(
                module,
                "invalid_key_beep",
            ) as beep, contextlib.redirect_stdout(io.StringIO()) as output:
                wait_for_audio_editor_space(
                    use_color=False,
                    key_reader=lambda: next(keys),
                )
            self.assertEqual(2, beep.call_count)
            self.assertIn("press SPACE", output.getvalue())
            self.assertIn("ENTER will not work", output.getvalue())
            self.assertIn("SPACE received", output.getvalue())

        def test_single_file_replaygain_targets_only_edited_audio(
            self,
        ) -> None:
            module = sys.modules[__name__]
            audio = Path(r"C:\Music\Edited Track.flac")
            backup = Path(
                r"C:\Music\Edited Track.flac.bak.202607302359."
                r"replaced-by-chatgpt.bak"
            )
            with mock.patch.object(
                module,
                "require_replaygain_program",
                return_value=r"C:\UTIL\metaflac.exe",
            ), mock.patch.object(
                module,
                "backup_before_inline_replacement",
                return_value=backup,
            ), mock.patch.object(
                module,
                "run_live_command",
            ) as run, mock.patch.object(
                Path,
                "is_file",
                return_value=True,
            ), contextlib.redirect_stdout(io.StringIO()):
                actions = apply_replaygain_file(
                    audio,
                    use_color=False,
                    stream_output=True,
                )
            run.assert_called_once_with(
                [
                    r"C:\UTIL\metaflac.exe",
                    "--add-replay-gain",
                    str(audio),
                ],
                cwd=audio.parent,
                stream_output=True,
            )
            self.assertEqual(
                [f"backup:{backup}", f"replaygain:{audio}"],
                actions,
            )

        def test_invalid_prompt_keys_beep_without_reprinting(self) -> None:
            module = sys.modules[__name__]
            output = io.StringIO()
            with mock.patch.object(
                module,
                "invalid_key_beep",
            ) as beep, contextlib.redirect_stdout(output):
                approval_keys = iter(("x", "n"))
                self.assertFalse(
                    prompt_for_approval(
                        "Continue this operation?",
                        False,
                        False,
                        key_reader=lambda: next(approval_keys),
                    )
                )
                scope_keys = iter(("x", "n"))
                self.assertEqual(
                    "no",
                    prompt_for_action_scope(
                        "Apply this repair?",
                        False,
                        False,
                        key_reader=lambda: next(scope_keys),
                    ),
                )
                artwork_keys = iter(("x", "y"))
                self.assertTrue(
                    artwork_review_choice(
                        Path(r"C:\Temp\cover.jpg"),
                        label="cover.jpg",
                        use_color=False,
                        key_reader=lambda: next(artwork_keys),
                        preview_renderer=(
                            lambda _path, *, use_color: "mock Sixel"
                        ),
                    )
                )
                waveform_keys = iter(("x", "n"))
                decision, edits, reviewed_path = waveform_review_choice(
                    Path(r"C:\Temp\track.waveform.jpg"),
                    Path(r"C:\Music\Track.flac"),
                    use_color=False,
                    key_reader=lambda: next(waveform_keys),
                    preview_renderer=(
                        lambda _path, *, use_color: "mock Sixel"
                    ),
                )
            self.assertEqual("fine", decision)
            self.assertEqual(0, edits)
            self.assertEqual(Path(r"C:\Music\Track.flac"), reviewed_path)
            self.assertEqual(4, beep.call_count)
            rendered = output.getvalue()
            self.assertEqual(
                1,
                rendered.count(
                    "Does this waveform show a problem in Track.flac?"
                ),
            )
            self.assertEqual(
                1,
                rendered.count(
                    "Approve this downloaded artwork image as cover.jpg?"
                ),
            )

            class LegacyTextBuffer(io.StringIO):
                @property
                def encoding(self) -> str:
                    return "cp1252"

            legacy_output = LegacyTextBuffer()
            with contextlib.redirect_stdout(legacy_output):
                self.assertFalse(
                    prompt_for_approval(
                        "Proceed despite missing tools?",
                        False,
                        False,
                        key_reader=lambda: "n",
                    )
                )
            self.assertIn(
                "? Proceed despite missing tools?",
                legacy_output.getvalue(),
            )
            if os.name == "nt":
                with mock.patch("winsound.Beep") as native_beep:
                    invalid_key_beep()
                native_beep.assert_called_once_with(100, 200)

        def test_waveform_problem_rename_includes_sidecars_backups_and_playlist(
            self,
        ) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                audio = root / "Track.flac"
                lyric = root / "Track.lrc"
                old_backup = root / "Track.flac.bak.202601010101.old.bak"
                playlist = root / "all.m3u"
                audio.write_bytes(b"audio")
                lyric.write_text("[00:00.00] lyric", encoding="utf-8")
                old_backup.write_bytes(b"backup")
                playlist.write_text("Track.flac\n", encoding="utf-8")

                renamed_audio, renamed, playlist_backups = (
                    rename_waveform_problem_family(
                        audio,
                        "Track [waveform problem].flac",
                    )
                )

                self.assertEqual(
                    root / "Track [waveform problem].flac",
                    renamed_audio,
                )
                self.assertEqual(3, len(renamed))
                self.assertTrue(renamed_audio.is_file())
                self.assertTrue(
                    root.joinpath(
                        "Track [waveform problem].lrc"
                    ).is_file()
                )
                self.assertTrue(
                    root.joinpath(
                        "Track [waveform problem].flac.bak."
                        "202601010101.old.bak"
                    ).is_file()
                )
                self.assertFalse(audio.exists())
                self.assertEqual(
                    "Track [waveform problem].flac\n",
                    playlist.read_text(encoding="utf-8"),
                )
                self.assertEqual(1, len(playlist_backups))
                self.assertEqual(
                    "Track.flac\n",
                    playlist_backups[0].read_text(encoding="utf-8"),
                )

        def test_waveform_review_keeps_only_disposable_staged_preview(
            self,
        ) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                audio = make_patterned_flac(
                    root,
                    "Disposable Waveform [instrumental]",
                    [(0.2, False), (0.2, True)],
                )
                audio_two = root / "Disposable Waveform 2 [instrumental].flac"
                audio_three = root / "Disposable Waveform 3 [instrumental].flac"
                shutil.copy2(audio, audio_two)
                shutil.copy2(audio, audio_three)
                expected_audio = [audio, audio_two, audio_three]
                staging_root = root / "recycled-staging"
                module = sys.modules[__name__]
                prepared_paths: list[Path] = []
                consumed_modes: list[str] = []
                geometry = ArtworkPreviewGeometry(
                    terminal_columns=100,
                    terminal_rows=35,
                    indent_columns=12,
                    columns=87,
                    rows=26,
                    pixel_width=609,
                    pixel_height=364,
                )

                def fake_generate(
                    _audio: Path,
                    *,
                    narrate: bool,
                    destination: Path,
                    **_kwargs,
                ) -> tuple[Path, None]:
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(make_test_jpeg())
                    return (
                        destination,
                        None,
                        WaveformMetrics(
                            channel_peak_percentages=(50.0, 50.0),
                            peak_volume_percentage=50.0,
                            average_volume_percentage=25.0,
                            replaygain_factor=None,
                            longest_silence_seconds=0.0,
                            total_silence_seconds=0.0,
                        ),
                    )

                def fake_prepare(
                    path: Path,
                    *,
                    use_color: bool,
                    **_kwargs,
                ) -> PreparedArtworkPreview:
                    prepared_paths.append(path)
                    return PreparedArtworkPreview(
                        mode="pre-rendered test preview",
                        geometry=geometry,
                        text_payload=f"prepared {path.name}",
                    )

                def fake_review(
                    waveform_path: Path,
                    audio_path: Path,
                    **options,
                ) -> tuple[str, int, Path]:
                    consumed_modes.append(
                        options["preview_renderer"](
                            waveform_path,
                            use_color=False,
                        )
                    )
                    return "fine", 0, audio_path

                with mock.patch.object(
                    module,
                    "waveform_staging_root",
                    return_value=staging_root,
                ), mock.patch.object(
                    module,
                    "generate_waveform_jpeg",
                    side_effect=fake_generate,
                ), mock.patch.object(
                    module,
                    "prepare_waveform_preview",
                    side_effect=fake_prepare,
                ), mock.patch.object(
                    module,
                    "waveform_preview_geometry",
                    return_value=geometry,
                ), mock.patch.object(
                    module,
                    "waveform_review_choice",
                    side_effect=fake_review,
                ), mock.patch.object(
                    module,
                    "audio_editor_executable",
                    return_value=None,
                ), contextlib.redirect_stdout(io.StringIO()) as output:
                    result = review_waveforms(
                        root,
                        use_color=False,
                        workers=2,
                        approval_database_path=root / "reviews.sqlite3",
                    )
                self.assertNotIn(
                    "Background waveform render is ready",
                    output.getvalue(),
                )
                self.assertIn("Disposable Waveform", output.getvalue())
                self.assertCountEqual(
                    [str(path) for path in expected_audio],
                    result["fine"],
                )
                self.assertEqual(3, len(prepared_paths))
                self.assertEqual(
                    ["pre-rendered test preview"] * 3,
                    consumed_modes,
                )
                self.assertIn(
                    "keeping up to 4 display-ready previews ahead",
                    output.getvalue(),
                )
                self.assertEqual([], result["problems"])
                staged_folder = Path(result["staging_folder"])
                self.assertTrue(staged_folder.is_dir())
                self.assertEqual(
                    3,
                    len(list(staged_folder.glob("*.waveform.jpg"))),
                )
                for source_audio in expected_audio:
                    self.assertFalse(
                        source_audio.with_name(
                            f"{source_audio.stem}.waveform.jpg"
                        ).exists()
                    )

        def test_waveform_approvals_persist_invalidate_prune_and_skip(
            self,
        ) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                database = root / "waveform-reviews.sqlite3"
                disposable = root / "Disposable.flac"
                disposable.write_bytes(b"first version")
                store = WaveformApprovalStore(database)
                store.approve(disposable)
                self.assertTrue(store.is_approved(disposable))

                disposable.write_bytes(b"changed version with new bytes")
                self.assertFalse(store.is_approved(disposable))
                store.approve(disposable)
                disposable.unlink()
                self.assertEqual(1, store.prune_if_oversized(max_bytes=0))

                audio = make_patterned_flac(
                    root,
                    "Already Approved [instrumental]",
                    [(0.2, False), (0.2, True)],
                )
                store.approve(audio)
                module = sys.modules[__name__]
                with mock.patch.object(
                    module,
                    "waveform_staging_root",
                    return_value=root / "staging",
                ), mock.patch.object(
                    module,
                    "generate_waveform_jpeg",
                ) as generate, mock.patch.object(
                    module,
                    "audio_editor_executable",
                    return_value=None,
                ), contextlib.redirect_stdout(io.StringIO()) as output:
                    result = review_waveforms(
                        root,
                        use_color=False,
                        workers=2,
                        approval_database_path=database,
                        key_reader=lambda: "n",
                    )
                generate.assert_not_called()
                self.assertEqual(1, result["audio_files"])
                self.assertEqual(0, result["queued"])
                self.assertEqual([str(audio)], result["previously_approved"])
                self.assertIn(
                    "1 unchanged, previously approved file skipped",
                    output.getvalue(),
                )

        def test_error_wrapper_and_progress_library_search_locations(self) -> None:
            plain = formatted_error(
                "ERROR: waveform rendering failed",
                False,
            )
            self.assertTrue(plain.startswith("💥💥💥 ERROR:"))
            self.assertTrue(plain.endswith("💥💥💥"))
            colored = formatted_error("waveform rendering failed", True)
            self.assertIn(f"{ANSI['blink']}{ANSI['bold']}", colored)
            self.assertIn("ERROR:", colored)
            self.assertEqual(
                (
                    _SCRIPT_DIR,
                    _SCRIPT_DIR / "clairecjs_util",
                    _SCRIPT_DIR / "clairecjs_utils",
                ),
                _PROGRESS_LIBRARY_SEARCH_DIRS,
            )
            with contextlib.redirect_stderr(io.StringIO()) as error_output:
                with self.assertRaises(SystemExit):
                    parse_args(
                        [
                            "--no-color",
                            "--waveform-workers",
                            "not-a-number",
                        ]
                    )
            error_line = error_output.getvalue().splitlines()[-1]
            self.assertTrue(error_line.startswith("💥💥💥 ERROR:"))
            self.assertTrue(error_line.endswith("💥💥💥"))

        def test_double_height_path_wraps_before_paired_output(self) -> None:
            lines = double_height_labeled_path(
                "Audit root:  ",
                r"C:\A very long incoming music folder\with several nested albums",
                use_color=True,
                red=120,
                green=225,
                blue=170,
                terminal_columns=80,
            )
            self.assertGreater(len(lines), 2)
            self.assertEqual(0, len(lines) % 2)
            strip_ansi = lambda text: re.sub(
                r"\x1b(?:\[[0-?]*[ -/]*[@-~]|#[34])", "", text
            )
            for index in range(0, len(lines), 2):
                top = strip_ansi(lines[index])
                bottom = strip_ansi(lines[index + 1])
                self.assertEqual(top, bottom)
                self.assertLessEqual(len(top), 35)
            continuation = strip_ansi(lines[2])
            first_line = strip_ansi(lines[0])
            expected_indent = visible_cell_width(
                first_line[: first_line.index("C:")]
            )
            self.assertEqual(
                expected_indent,
                len(continuation) - len(continuation.lstrip()),
            )
            results_header = double_height_gradient_section(
                "Interactive results",
                True,
                ((255, 135, 245), (175, 95, 240)),
            )
            self.assertEqual(2, len(results_header))
            self.assertTrue(results_header[0].startswith(ANSI_DOUBLE_HEIGHT_TOP))
            self.assertTrue(results_header[1].startswith(ANSI_DOUBLE_HEIGHT_BOTTOM))
            actions_header = double_height_gradient_section(
                "Actions available for your approval",
                True,
                ((255, 250, 80), (210, 145, 0)),
            )
            self.assertEqual(2, len(actions_header))
            self.assertTrue(actions_header[0].startswith(ANSI_DOUBLE_HEIGHT_TOP))
            self.assertTrue(
                actions_header[1].startswith(ANSI_DOUBLE_HEIGHT_BOTTOM)
            )

        def test_grouped_rename_hides_noops_and_keeps_album_folder_inline(
            self,
        ) -> None:
            finding = {
                "category": "filename_title_capitalization_group",
                "path": ".",
                "details": {
                    "renames": [
                        {
                            "before": "01_From Me To U.flac",
                            "after": "01_From Me To U.flac",
                        },
                        {
                            "before": "02_from me to u.flac",
                            "after": "02_From Me To U.flac",
                        },
                    ]
                },
            }
            table = rename_preview_table(
                finding,
                use_color=False,
                terminal_columns=100,
            )
            rendered_table = "\n".join(table)
            self.assertNotIn("01_From Me To U.flac", rendered_table)
            self.assertIn("02_from me to u.flac", rendered_table)
            self.assertIn("02_From Me To U.flac", rendered_table)
            self.assertEqual(
                "01_From Me To U.flac",
                capitalized_album_filename_proposal(
                    "01_from me to u.flac",
                    10,
                ),
            )
            target_lines = finding_target_lines(
                finding,
                use_color=False,
                root=Path(
                    r"T:\new\MUSIC\changerrecent\Babymetal"
                    r"\2025 - Metal Forth"
                ),
                terminal_columns=70,
            )
            self.assertTrue(target_lines[0].startswith("📁 Album folder: T:"))
            self.assertNotIn("Album folder: .", target_lines[0])
            self.assertNotIn("\n", target_lines[0])
            self.assertIn("…", target_lines[0])

        def test_unit_tests_disable_console_paging(self) -> None:
            self.assertFalse(console_paging_enabled(["--unit-tests"]))
            self.assertFalse(
                console_paging_enabled(["--unit-tests", "--no-color"])
            )
            self.assertFalse(console_paging_enabled([".", "--no-pager"]))
            self.assertTrue(console_paging_enabled(["."]))

        def test_console_pager_pauses_before_viewport_scroll(self) -> None:
            class TtyBuffer(io.StringIO):
                def isatty(self) -> bool:
                    return True

            output = TtyBuffer()
            keys: list[str] = []
            pager = ConsolePager(
                output,
                key_reader=lambda: keys.append(" ") or " ",
            )
            with mock.patch.object(
                sys.modules[__name__],
                "visible_console_size",
                return_value=os.terminal_size((20, 6)),
            ):
                pager.write("one\ntwo\nthree\nfour\n")
            self.assertEqual([" "], keys)
            self.assertIn("── More ── press any key to continue", output.getvalue())
            self.assertIn(ANSI["erase_line"], output.getvalue())
            self.assertEqual(9, visible_cell_width("♪ ✨ test"))
            strip_ansi = lambda text: re.sub(
                r"\x1b(?:\[[0-?]*[ -/]*[@-~]|#[34])", "", text
            )
            actions_header = double_height_gradient_section(
                "Actions available for your approval",
                True,
                ((255, 250, 80), (210, 145, 0)),
            )
            self.assertTrue(
                all(
                    "Actions available for your approval" in strip_ansi(line)
                    for line in actions_header
                )
            )
            self.assertIn("\033[38;2;255;250;80m", actions_header[0])
            self.assertNotIn("\033[38;2;130;245;160m", actions_header[0])
            clean_status = double_height_plain_status(
                "✓ No fixes or manual review items found.",
                True,
                ((130, 245, 160), (70, 195, 135)),
            )
            self.assertEqual(2, len(clean_status))
            self.assertTrue(clean_status[0].startswith(ANSI_DOUBLE_HEIGHT_TOP))
            self.assertTrue(clean_status[1].startswith(ANSI_DOUBLE_HEIGHT_BOTTOM))
            clean_visible = [strip_ansi(line) for line in clean_status]
            self.assertEqual(clean_visible[0], clean_visible[1])
            self.assertTrue(clean_visible[0].startswith("✓"))
            self.assertNotRegex(clean_visible[0], r"^\s")
            self.assertNotIn("✨", clean_visible[0])
            self.assertNotIn("✱", clean_visible[0])
            symmetric = decorated_gradient_header(
                "Symmetry",
                True,
                ((100, 255, 255), (80, 155, 255)),
                add_colon=True,
            )
            ornament_end = symmetric.index(ANSI["reset"]) + len(ANSI["reset"])
            left_ornament = symmetric[:ornament_end]
            self.assertTrue(symmetric.endswith(left_ornament))
            self.assertEqual(
                "        2 applied, 3 skipped, 1 failed.",
                interactive_results_summary(2, 3, 1, False),
            )
            colored_summary = interactive_results_summary(2, 3, 1, True)
            self.assertIn(rgb_text("2", 90, 225, 125, True), colored_summary)
            self.assertIn(rgb_text("3", 255, 215, 70, True), colored_summary)
            self.assertIn(rgb_text("1", 255, 95, 100, True), colored_summary)

        def test_cover_narration_aligns_and_italicizes_music_filename(self) -> None:
            plain = io.StringIO()
            with contextlib.redirect_stdout(plain):
                cover_narration(
                    "♪",
                    "02-babymetal.flac",
                    use_color=False,
                    dim=True,
                    italic=True,
                )
                cover_narration(
                    "🌐",
                    "Searching MusicBrainz.",
                    use_color=False,
                )
            lines = plain.getvalue().splitlines()
            self.assertTrue(lines[0].startswith("            ♪  "))
            self.assertTrue(lines[1].startswith("            🌐 "))
            self.assertEqual(
                visible_cell_width(lines[0].split("02-", 1)[0]),
                visible_cell_width(lines[1].split("Searching", 1)[0]),
            )

        def test_action_target_filename_is_prominent_bright_cyan(self) -> None:
            finding = {
                "category": "missing_embedded_art",
                "path": "MISC\\Artist - Song.mp3",
            }
            lines = finding_target_lines(finding, use_color=True)
            self.assertIn("Folder:", lines[0])
            line = lines[-1]
            self.assertIn(
                bright_cyan_path("Artist - Song.mp3", True),
                line,
            )
            self.assertNotIn(ANSI["dim"], line)
            self.assertIn(ANSI["italic"], line)

            colored = io.StringIO()
            with contextlib.redirect_stdout(colored):
                cover_narration(
                    "♪",
                    "02-babymetal.flac",
                    use_color=True,
                    dim=True,
                    italic=True,
                )
            self.assertIn(ANSI["italic"], colored.getvalue())
            self.assertIn("02-babymetal.flac", colored.getvalue())

        def test_single_key_prompt_styling_and_defaults(self) -> None:
            question = "Embed the timed karaoke lyrics into this audio file now?"
            strip_ansi = lambda text: re.sub(
                r"\x1b(?:\[[0-?]*[ -/]*[@-~]|#[34])", "", text
            )
            yes_prompt = approval_prompt(
                question, default_yes=True, use_color=True
            )
            no_prompt = approval_prompt(
                question, default_yes=False, use_color=True
            )
            self.assertIn(
                f"{ANSI['bold']}\033[38;2;95;245;135mY", yes_prompt
            )
            self.assertIn(
                f"{ANSI['dim']}\033[38;2;255;105;105mn", yes_prompt
            )
            self.assertIn(
                f"{ANSI['dim']}\033[38;2;95;245;135my", no_prompt
            )
            self.assertIn(
                f"{ANSI['bold']}\033[38;2;255;105;105mN", no_prompt
            )
            self.assertTrue(strip_ansi(yes_prompt).startswith("❓ "))
            self.assertIn("\033[38;2;255;105;45m", yes_prompt)
            self.assertNotIn("\033[38;2;75;220;255m", yes_prompt)
            self.assertIn(f"{ANSI['italic']}timed karaoke lyrics", yes_prompt)
            self.assertIn(f"{ANSI['italic']}audio file", yes_prompt)
            for answer_yes, expected in ((True, "Yes!"), (False, "No!")):
                settled = settled_approval_prompt(
                    question, answer_yes, True
                )
                visible_settled = strip_ansi(settled)
                self.assertTrue(visible_settled.startswith("❓ "))
                self.assertTrue(visible_settled.endswith(expected))
                self.assertNotIn("[", visible_settled)
                self.assertNotIn(ANSI["blink"], settled)
            indented = approval_prompt(
                question, True, True, indent="            "
            )
            self.assertTrue(indented.startswith("            "))
            self.assertTrue(strip_ansi(indented).lstrip().startswith("❓ "))

            self.assertNotIn("this action", indented.lower())
            expected_prompt_categories = EXECUTABLE_CATEGORIES - {"missing_album"}
            self.assertEqual(
                expected_prompt_categories, set(ACTION_PROMPT_QUESTIONS)
            )
            for category in expected_prompt_categories:
                concrete = approval_question({"category": category})
                self.assertTrue(concrete.endswith("?"), concrete)
                self.assertNotIn("this action", concrete.lower())
                rendered_prompt = approval_prompt(
                    concrete, True, True
                )
                self.assertTrue(strip_ansi(rendered_prompt).startswith("❓ "))
                self.assertIn(ANSI["italic"], rendered_prompt)
            for category, emoji in {
                "karaoke_not_embedded": "🎤",
                "missing_embedded_art": "🖼️",
                "missing_replaygain": "🎚️",
                "archive_missing_marker": "📁",
                "temporary_batch_file": "🗑️",
                "missing_album": "🏷️",
                "read_only_audio": "💡",
            }.items():
                suggestion = suggested_text(
                    {
                        "category": category,
                        "suggestion": "Do the appropriate thing.",
                    },
                    True,
                )
                self.assertTrue(
                    strip_ansi(suggestion).startswith(f"{emoji} Suggested:")
                )
                self.assertIn(ANSI["dim"], suggestion)
                self.assertIn("\033[38;2;75;155;190m", suggestion)
            self.assertEqual(
                " ♪ example.flac",
                music_filename("example.flac", False),
            )
            action_line = approval_action_line(
                {
                    "category": "missing_embedded_art",
                    "message": "No embedded front cover art.",
                },
                True,
            )
            self.assertIn(
                "\033[38;2;255;245;70m🎨 Embedded cover missing",
                action_line,
            )
            self.assertIn(
                "\033[38;2;205;155;45m⚠️ No embedded front cover art.",
                action_line,
            )
            self.assertEqual(
                "🎨 Embedded cover missing — ⚠️ No embedded front cover art.",
                strip_ansi(action_line),
            )
            self.assertTrue(
                warning_finding_message(
                    {
                        "message": "Timed karaoke lyrics are not embedded."
                    }
                ).startswith("⚠️ ")
            )
            self.assertEqual(
                "Extract the embedded artwork to an image sidecar now?",
                approval_question(
                    {"category": "embedded_art_without_sidecar"}
                ),
            )

            class TtyBuffer(io.StringIO):
                def isatty(self) -> bool:
                    return True

            tty_output = TtyBuffer()
            with contextlib.redirect_stdout(tty_output):
                self.assertFalse(
                    prompt_for_approval(
                        question,
                        True,
                        True,
                        key_reader=lambda: "n",
                        indent="            ",
                    )
                )
            rendered = tty_output.getvalue()
            erase = f"\r{ANSI['erase_line']}"
            waiting, steady = rendered.rsplit(erase, maxsplit=1)
            steady = steady.lstrip("\r")
            self.assertIn(ANSI["blink"], waiting)
            self.assertNotIn(ANSI["blink"], steady)
            self.assertTrue(steady.startswith("            "))
            visible_steady = strip_ansi(steady)
            self.assertIn("No!", visible_steady)
            self.assertNotIn("[Y/n]", visible_steady)
            self.assertNotIn("[y/N]", visible_steady)
            self.assertTrue(
                steady.endswith(f"{ANSI['erase_to_eol']}\n")
            )
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertTrue(
                    prompt_for_approval(
                        question, False, False, key_reader=lambda: "y"
                    )
                )
                self.assertFalse(
                    prompt_for_approval(
                        question, True, False, key_reader=lambda: "n"
                    )
                )
                self.assertTrue(
                    prompt_for_approval(
                        question, True, False, key_reader=lambda: "\r"
                    )
                )

        def test_default_no_prompt_can_erase_itself_completely(self) -> None:
            class TTYBuffer(io.StringIO):
                def isatty(self) -> bool:
                    return True

            output = TTYBuffer()
            with contextlib.redirect_stdout(output):
                answer = prompt_for_approval(
                    "Run the interactive waveform review now?",
                    default_yes=False,
                    use_color=False,
                    key_reader=lambda: "n",
                    indent="        ",
                    erase_on_no=True,
                )
            self.assertFalse(answer)
            rendered = output.getvalue()
            self.assertIn(
                "Run the interactive waveform review now?",
                rendered,
            )
            self.assertIn(ANSI["erase_line"], rendered)
            self.assertNotIn("No!", rendered)

            accepted_output = TTYBuffer()
            with contextlib.redirect_stdout(accepted_output):
                answer = prompt_for_approval(
                    "Run the interactive waveform review now?",
                    default_yes=False,
                    use_color=False,
                    key_reader=lambda: "y",
                    indent="        ",
                    erase_on_no=True,
                    erase_on_yes=True,
                )
            self.assertTrue(answer)
            accepted_rendered = accepted_output.getvalue()
            self.assertIn(ANSI["erase_line"], accepted_rendered)
            self.assertNotIn("Yes!", accepted_rendered)

        def test_action_prompts_remember_always_never_and_folder_scope(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                findings = []
                definitions = [
                    ("a", "temporary_batch_file", "one/a.bat"),
                    ("b", "temporary_batch_file", "two/b.bat"),
                    ("c", "adobe_xmp", "one/c.xmp"),
                    ("d", "adobe_xmp", "two/d.xmp"),
                    ("e", "bare_marker", "album/e"),
                    ("f", "bare_marker", "album/f"),
                    ("g", "bare_marker", "other/g"),
                ]
                for code, category, path in definitions:
                    findings.append(
                        {
                            "code": code,
                            "severity": "ask_first",
                            "category": category,
                            "path": path,
                            "message": "Generated action fixture.",
                            "suggestion": "Test the scoped decision.",
                        }
                    )
                keys = iter(("a", "y", "v", "f", "n"))
                keypresses: list[str] = []

                def read_key() -> str:
                    value = next(keys)
                    keypresses.append(value)
                    return value

                with mock.patch.object(
                    sys.modules[__name__],
                    "apply_finding",
                    return_value=["mocked"],
                ), contextlib.redirect_stdout(io.StringIO()):
                    result = interactive_apply(
                        {
                            "findings": findings,
                            "resolved_root": str(root),
                        },
                        use_color=False,
                        key_reader=read_key,
                    )
                self.assertEqual(["a", "y", "v", "f", "n"], keypresses)
                self.assertEqual("abef", result["applied_codes"])
                self.assertEqual("cdg", result["skipped_codes"])
                self.assertEqual(
                    [
                        "always",
                        "always",
                        "never",
                        "never",
                        "folder",
                        "folder",
                        "no",
                    ],
                    [decision["choice"] for decision in result["decisions"]],
                )

        def test_usage_requires_an_explicit_folder(self) -> None:
            usage = render_usage(False)
            colored_usage = render_usage(True)
            self.assertIn("audit_music_batch.py [foldername] [flags]", usage)
            self.assertLess(usage.index("Flags"), usage.index("Examples"))
            self.assertIn("Interactive workflow features", usage)
            self.assertIn("Chafa, Sixel, or ANSI artwork previews", usage)
            self.assertIn("parallel background pre-rendering", usage)
            self.assertIn(
                "B=Bake ReplayGain changes audio for players that ignore its tags",
                usage,
            )
            self.assertIn(
                "MP3 is decoded and LAME-re-encoded",
                usage,
            )
            self.assertIn("rainbow progress bars", usage)
            self.assertIn(
                "--interactive  --no-interactive",
                usage,
            )
            self.assertIn("[default = Yes]", usage)
            self.assertIn("[default = No]", usage)
            self.assertIn(
                "[default = "
                f"{load_behavior_defaults().silence_threshold_seconds:g} "
                "seconds]",
                usage,
            )
            self.assertIn("[default = 8 workers]", usage)
            self.assertEqual(8, parse_args(["."]).waveform_workers)
            self.assertIn("--embed-lyrics  --no-embed-lyrics", usage)
            self.assertIn("--refresh-embedded-lyrics", usage)
            self.assertIn(
                "plain lyrics and timed karaoke",
                usage,
            )
            self.assertIn("--find-cover  --no-find-cover", usage)
            self.assertIn("--check-silence  --no-silence-check", usage)
            self.assertIn("--review-waveforms", usage)
            embed_usage_line = next(
                line
                for line in usage.splitlines()
                if "--embed-lyrics" in line
            )
            cover_usage_line = next(
                line
                for line in usage.splitlines()
                if "--find-cover" in line and "--no-find-cover" in line
            )
            self.assertIn("[default = Yes]", embed_usage_line)
            self.assertIn("[default = No]", cover_usage_line)
            self.assertFalse(BehaviorDefaults().find_cover)
            self.assertIn(
                f"{ANSI['dim']}\033[38;2;255;190;95m[default = ",
                colored_usage,
            )
            self.assertIn(
                "\033[38;2;95;245;135mYes",
                colored_usage,
            )
            self.assertIn(
                "\033[38;2;255;105;105mNo",
                colored_usage,
            )
            self.assertEqual(
                "Matching MP3/FLAC pair",
                friendly_category("same_stem_mp3_flac"),
            )
            self.assertEqual(".", parse_args(["."]).root)
            self.assertIsNone(parse_args(["--no-interactive"]).root)
            self.assertIn("--find-cover", usage)
            self.assertTrue(parse_args([".", "--find-cover"]).find_cover)
            self.assertFalse(
                parse_args([".", "--no-find-cover"]).find_cover
            )
            self.assertFalse(
                parse_args([".", "--no-embed-lyrics"]).embed_lyrics
            )
            self.assertIsNone(parse_args(["."]).find_cover)
            self.assertIsNone(parse_args(["."]).embed_lyrics)
            defaults = BehaviorDefaults()
            self.assertEqual(
                BehaviorDefaults(),
                effective_behavior_flags(parse_args(["."]), defaults),
            )
            self.assertEqual(
                BehaviorDefaults(
                    embed_lyrics=False,
                    find_cover=False,
                ),
                effective_behavior_flags(
                    parse_args(
                        [".", "--no-embed-lyrics", "--no-find-cover"]
                    ),
                    defaults,
                ),
            )
            with tempfile.TemporaryDirectory() as temp:
                config = Path(temp) / BEHAVIOR_CONFIG_FILENAME
                self.assertEqual(
                    BehaviorDefaults(),
                    load_behavior_defaults(config),
                )
                keys = iter(("n", "y", "n"))
                with contextlib.redirect_stdout(io.StringIO()):
                    configured, written, backup = (
                        configure_behavior_defaults(
                            use_color=False,
                            key_reader=lambda: next(keys),
                            input_reader=lambda _prompt: "12.5",
                            path=config,
                        )
                    )
                self.assertEqual(
                    BehaviorDefaults(
                        embed_lyrics=False,
                        find_cover=True,
                        check_silence=False,
                        silence_threshold_seconds=12.5,
                    ),
                    configured,
                )
                self.assertEqual(config, written)
                self.assertIsNone(backup)
                self.assertEqual(configured, load_behavior_defaults(config))
                keys = iter(("y", "n", "y"))
                with contextlib.redirect_stdout(io.StringIO()):
                    reconfigured, _written, backup = (
                        configure_behavior_defaults(
                            use_color=False,
                            key_reader=lambda: next(keys),
                            input_reader=lambda _prompt: "",
                            path=config,
                        )
                    )
                self.assertEqual(
                    BehaviorDefaults(
                        embed_lyrics=True,
                        find_cover=False,
                        check_silence=True,
                        silence_threshold_seconds=12.5,
                    ),
                    reconfigured,
                )
                self.assertIsNotNone(backup)
                self.assertTrue(backup.is_file())
                self.assertRegex(
                    backup.name,
                    r"^audit_music_batch\.config\.json\.bak\.\d{12}"
                    r"\.replaced-by-chatgpt\.bak$",
                )
            simulated = {
                "mutagen": False,
                "Pillow": True,
                "send2trash": True,
                "claire_progressbar": True,
                "metamp3": True,
                "metaflac": False,
                "flac": True,
                "ffmpeg": True,
                "ffplay": True,
                "play_audio_file.py": True,
                "IrfanView": True,
            }
            missing = [
                requirement
                for requirement in dependency_requirements(
                    unit_tests=True,
                    availability=simulated,
                )
                if not requirement.available
            ]
            self.assertEqual(
                ["mutagen", "metaflac"],
                [requirement.name for requirement in missing],
            )
            warnings = render_dependency_warnings(missing, False)
            self.assertIn("core audit:", warnings)
            self.assertIn("approved repair:", warnings)
            self.assertIn("choosing No cancels", warnings)
            cover_requirements = dependency_requirements(
                find_cover=True,
                availability=simulated,
            )
            pillow_requirement = next(
                requirement
                for requirement in cover_requirements
                if requirement.name == "Pillow"
            )
            self.assertIn(
                "validating",
                pillow_requirement.capability,
            )
            viewer_requirement = next(
                requirement
                for requirement in cover_requirements
                if requirement.name == "IrfanView"
            )
            self.assertIn(
                "IMAGE_VIEWER_EXECUTABLE",
                viewer_requirement.capability,
            )

            rejected_output = io.StringIO()
            with contextlib.redirect_stdout(rejected_output):
                self.assertFalse(
                    run_dependency_preflight(
                        unit_tests=False,
                        interactive=True,
                        use_color=False,
                        key_reader=lambda: "n",
                        availability=simulated,
                    )
                )
            self.assertIn(
                "❓ Proceed with the audit despite these missing tools? "
                "[y/N] No!",
                rejected_output.getvalue(),
            )

            approved_output = io.StringIO()
            with contextlib.redirect_stdout(approved_output):
                self.assertTrue(
                    run_dependency_preflight(
                        unit_tests=False,
                        interactive=True,
                        use_color=False,
                        key_reader=lambda: "y",
                        availability=simulated,
                    )
                )
            self.assertIn("[y/N] Yes!", approved_output.getvalue())

            noninteractive_output = io.StringIO()
            with contextlib.redirect_stdout(noninteractive_output):
                self.assertTrue(
                    run_dependency_preflight(
                        unit_tests=False,
                        interactive=False,
                        use_color=False,
                        availability=simulated,
                    )
                )
            self.assertIn(
                "--no-interactive suppresses the prompt",
                noninteractive_output.getvalue(),
            )

        def test_complete_track_avoids_all_required_metadata_findings(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                audio_path = make_silent_flac(root, "05 Complete Song")
                tag_complete_vocal_flac(audio_path)

                categories = finding_categories(BatchAudit(root).audit())

                forbidden = {
                    "missing_genre",
                    "empty_genre",
                    "missing_title",
                    "missing_artist",
                    "missing_album",
                    "missing_replaygain",
                    "missing_embedded_art",
                    "embedded_art_without_sidecar",
                    "multiple_embedded_artworks",
                    "plain_lyrics_not_embedded",
                    "karaoke_not_embedded",
                    "missing_plain_lyrics",
                    "missing_karaoke",
                }
                self.assertTrue(forbidden.isdisjoint(categories))
                colored_report = render_console_report(
                    BatchAudit(root).audit(), max_examples=80, use_color=True
                )
                self.assertIn(ANSI_DOUBLE_HEIGHT_TOP, colored_report)
                self.assertIn("files processed;", colored_report)
                self.assertIn("checked for metadata, ReplayGain", colored_report)
                visible_report = re.sub(
                    r"\x1b(?:\[[0-?]*[ -/]*[@-~]|#[34])",
                    "",
                    colored_report,
                )
                clean_lines = [
                    line
                    for line in visible_report.splitlines()
                    if "No fixes or manual review items found." in line
                ]
                self.assertEqual(2, len(clean_lines))
                self.assertTrue(all(line.startswith("✓") for line in clean_lines))

        def test_incomplete_track_reports_every_required_metadata_family(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                make_silent_flac(root, "06 Incomplete Song")

                categories = finding_categories(BatchAudit(root).audit())

                self.assertTrue(
                    {
                        "missing_genre",
                        "missing_title",
                        "missing_artist",
                        "missing_album",
                        "missing_replaygain",
                        "missing_embedded_art",
                        "missing_plain_lyrics",
                        "missing_karaoke",
                    }.issubset(categories)
                )

        def test_filesystem_audit_tolerates_file_disappearing_after_enumeration(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                marker = root / ".CurrentlyDoingTranscriptionsHere"
                marker.touch()
                auditor = BatchAudit(root)
                auditor.files = [marker]
                marker.unlink()
                auditor.audit_filesystem()
                self.assertEqual([], auditor.findings)

        def test_filesystem_hygiene_positive_and_kept_cases(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                root.joinpath("__").touch()
                root.joinpath("__ keep this note __").touch()
                root.joinpath("history.bak").write_text("backup", encoding="utf-8")
                root.joinpath("transcription.log").write_text("log", encoding="utf-8")
                root.joinpath("metadata.json").write_text("{}", encoding="utf-8")
                root.joinpath("preview.m3u8").write_text("#EXTM3U", encoding="utf-8")
                root.joinpath("edit.xmp").write_text("xmp", encoding="utf-8")
                root.joinpath("temporary-get-the-missing-lyrics.bat").write_text(
                    "@echo off", encoding="utf-8"
                )
                root.joinpath("state.currentlydoingtranscriptionshere").touch()
                root.joinpath("active TODO note.txt").write_text("todo", encoding="utf-8")
                root.joinpath("bad;name.txt").write_text("bad", encoding="utf-8")
                root.joinpath("old.wma").write_bytes(b"not audio")
                root.joinpath("edit.wav").write_bytes(b"not audio")
                root.joinpath("completed-todos.log").write_text("done", encoding="utf-8")

                report = BatchAudit(root).audit()
                categories = finding_categories(report)

                self.assertTrue(
                    {
                        "bare_marker",
                        "kept_user_marker",
                        "backup_file",
                        "log_sidecar",
                        "json_sidecar",
                        "tagrename_m3u8",
                        "adobe_xmp",
                        "temporary_batch_file",
                        "stale_transcription_marker",
                        "active_todo_filename",
                        "forbidden_filename_char",
                        "unsupported_audio_format",
                        "wav_remaining",
                    }.issubset(categories)
                )
                completed = [
                    item
                    for item in report["findings"]
                    if item["path"] == "completed-todos.log"
                ]
                self.assertEqual([], completed)
                rendered = render_console_report(report, max_examples=80, use_color=False)
                self.assertIn("Backup files kept", rendered)
                self.assertIn("JSON sidecars kept", rendered)
                self.assertIn("Log sidecars kept", rendered)
                self.assertNotIn("history.bak", rendered)
                self.assertNotIn("transcription.log", rendered)
                self.assertNotIn("metadata.json", rendered)
                self.assertIn("\n        🚨           Problems:", rendered)
                alignment_data = dict(report)
                alignment_data["findings"] = list(report["findings"]) + [
                    {
                        "severity": "ask_first",
                        "category": "log_sidecar",
                        "path": f"extra-{number}.log",
                        "message": "Log sidecar.",
                    }
                    for number in range(24)
                ]
                aligned = render_console_report(
                    alignment_data, max_examples=80, use_color=False
                )
                self.assertIn("\n        💾  1 Backup files kept.", aligned)
                self.assertIn("\n        📜 25 Log sidecars kept.", aligned)
                severity_alignment_data = dict(report)
                severity_alignment_data["findings"] = list(
                    report["findings"]
                ) + [
                    {
                        "severity": "problem",
                        "category": "synthetic_problem",
                        "path": f"problem-{number}",
                        "message": "Synthetic problem.",
                    }
                    for number in range(98)
                ]
                severity_aligned = render_console_report(
                    severity_alignment_data,
                    max_examples=1,
                    use_color=False,
                )
                self.assertIn("🚨           Problems: 100 —", severity_aligned)
                self.assertIn("🔧        Fixes ready:   0 —", severity_aligned)
                self.assertIn("⚠️      Review needed:   2 —", severity_aligned)
                colored = render_console_report(report, max_examples=80, use_color=True)
                self.assertIn(ANSI["italic"], colored)
                self.assertIn(
                    f"{ANSI_DOUBLE_HEIGHT_TOP}{ANSI['bold']}",
                    colored,
                )
                self.assertGreaterEqual(colored.count(ANSI_DOUBLE_HEIGHT_TOP), 4)
            colorless = re.sub(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|#[34])", "", colored)
            self.assertIn("Findings by severity:", colorless)
            self.assertIn("Other files detected:", colorless)

        def test_tiny_audio_and_read_only_attribute_are_detected_and_repaired(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                tiny = root / "tiny.mp3"
                tiny.write_bytes(b"ID3")
                writable = make_silent_flac(root, "Read Only [instrumental]")
                os.chmod(writable, stat.S_IREAD)
                try:
                    report = BatchAudit(root).audit()
                    categories = finding_categories(report)
                    self.assertIn("suspiciously_tiny_audio", categories)
                    self.assertIn("read_only_audio", categories)
                    finding = next(
                        item
                        for item in report["findings"]
                        if item["category"] == "read_only_audio"
                    )
                    self.assertTrue(apply_finding(root, finding))
                    self.assertFalse(is_windows_read_only(writable))
                finally:
                    if writable.exists():
                        os.chmod(writable, stat.S_IWRITE | stat.S_IREAD)

        def test_canonical_filename_marker_is_detected_and_renamed(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                original = root / "Theme (instrumental).txt"
                original.write_text("no lyrics", encoding="utf-8")
                report = BatchAudit(root).audit()
                finding = next(
                    item
                    for item in report["findings"]
                    if item["category"] == "filename_marker_style"
                )
                self.assertEqual(
                    "Theme [instrumental].txt",
                    finding["details"]["proposed_name"],
                )
                apply_finding(root, finding)
                self.assertFalse(original.exists())
                self.assertTrue(root.joinpath("Theme [instrumental].txt").exists())

        def test_album_artist_filename_group_is_prompted_once_and_reaudited(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                album = root / "Babymetal" / "2019 - Metal Galaxy (Jap)"
                album.mkdir(parents=True)
                old_audio_names = [
                    "01-babymetal-song_one.flac",
                    "02-babymetal-a_very_long_song_name_(feat._guest_artist).flac",
                ]
                for audio_name in old_audio_names:
                    audio_path = make_silent_flac(
                        album,
                        Path(audio_name).stem,
                    )
                    backup_name = (
                        f"{audio_path.name}.bak.202607300930."
                        "replaced-by-chatgpt.bak"
                    )
                    album.joinpath(backup_name).write_bytes(
                        audio_path.read_bytes()
                    )
                    for extension, content in {
                        ".txt": "A line\n",
                        ".lrc": "[00:00.00]A line\n",
                        ".srt": "1\n00:00:00,000 --> 00:00:01,000\nA line\n",
                    }.items():
                        audio_path.with_suffix(extension).write_text(
                            content,
                            encoding="utf-8",
                        )
                playlist = album / "all.m3u"
                playlist.write_text(
                    "\n".join(old_audio_names) + "\n",
                    encoding="utf-8",
                )

                report = BatchAudit(root).audit()
                grouped = [
                    item
                    for item in report["findings"]
                    if item["category"]
                    == "redundant_album_artist_filename_group"
                ]
                self.assertEqual(1, len(grouped))
                finding = grouped[0]
                self.assertIn("code", finding)
                self.assertEqual(10, len(finding["details"]["renames"]))
                self.assertEqual(2, finding["details"]["audio_count"])
                self.assertEqual(2, finding["details"]["track_count"])
                self.assertEqual(
                    "02_Da Da Dance (feat Tak Matsumoto).flac",
                    redundant_artist_filename_proposal(
                        "02-babymetal-da_da_dance_(feat._tak_matsumoto).flac",
                        "Babymetal",
                        14,
                    ),
                )
                self.assertEqual(
                    ["Babymetal\\2019 - Metal Galaxy (Jap)\\all.m3u"],
                    finding["details"]["playlists"],
                )
                self.assertEqual(
                    "Rename these 10 album files to remove the redundant "
                    "artist name now?",
                    approval_question(finding),
                )
                table = rename_preview_table(
                    finding,
                    False,
                    terminal_columns=72,
                )
                self.assertIn("Before filename", table[0])
                self.assertIn("After filename", table[0])
                self.assertTrue(all(len(line) <= 60 for line in table))
                compact_table = rename_preview_table(
                    {
                        "details": {
                            "renames": [
                                {
                                    "before": "01. BABYMETAL - from me to u.flac",
                                    "after": "01_From Me To U.flac",
                                },
                                {
                                    "before": "02. BABYMETAL - RATATATA.flac",
                                    "after": "02_RATATATA.flac",
                                },
                            ]
                        }
                    },
                    False,
                    terminal_columns=190,
                )
                self.assertEqual(64, max(map(len, compact_table)))
                self.assertTrue(
                    all(len(line) + 12 <= 190 for line in compact_table)
                )
                proposed_names = {
                    Path(item["after"]).name
                    for item in finding["details"]["renames"]
                }
                self.assertIn("1_Song One.flac", proposed_names)
                self.assertIn(
                    "2_A Very Long Song Name (feat Guest Artist).flac",
                    proposed_names,
                )
                self.assertIn(
                    "1_Song One.flac.bak.202607300930."
                    "replaced-by-chatgpt.bak",
                    proposed_names,
                )

                keypresses: list[str] = []
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    result = interactive_apply(
                        {
                            "findings": [finding],
                            "resolved_root": str(root),
                        },
                        use_color=False,
                        key_reader=lambda: keypresses.append("y") or "y",
                    )
                self.assertEqual(["y"], keypresses)
                self.assertFalse(result["failed_codes"], result)
                self.assertIn("Before filename", output.getvalue())
                self.assertIn("After filename", output.getvalue())
                self.assertIn(
                    "[y=Yes / N=No / A=Always / V=Never / "
                    "F=Yes for This Folder] Yes!",
                    output.getvalue(),
                )
                self.assertIn(
                    "re-audit:passed",
                    result["decisions"][0]["actions"],
                )
                self.assertIn("💾 Backup:", output.getvalue())
                self.assertIn("🔧 Applied: renamed 10 files", output.getvalue())
                self.assertIn("✔️ Re-audit: passed", output.getvalue())

                for old_name in old_audio_names:
                    self.assertFalse(album.joinpath(old_name).exists())
                    self.assertTrue(
                        album.joinpath(
                            redundant_artist_filename_proposal(
                                old_name,
                                "Babymetal",
                                2,
                            )
                        ).exists()
                    )
                for track in (
                    "1_Song One",
                    "2_A Very Long Song Name (feat Guest Artist)",
                ):
                    for extension in (".txt", ".lrc", ".srt"):
                        self.assertTrue(album.joinpath(track + extension).is_file())
                    self.assertTrue(
                        album.joinpath(
                            f"{track}.flac.bak.202607300930."
                            "replaced-by-chatgpt.bak"
                        ).is_file()
                    )
                playlist_text = playlist.read_text(encoding="utf-8")
                self.assertIn("1_Song One.flac", playlist_text)
                self.assertNotIn("babymetal", playlist_text.lower())
                playlist_backups = list(
                    album.glob(
                        "all.m3u.bak.*.replaced-by-chatgpt*.bak"
                    )
                )
                self.assertEqual(1, len(playlist_backups))
                self.assertIn(
                    "01-babymetal-song_one.flac",
                    playlist_backups[0].read_text(encoding="utf-8"),
                )
                self.assertNotIn(
                    "redundant_album_artist_filename_group",
                    finding_categories(BatchAudit(root).audit()),
                )

            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                album = root / "MISC" / "2019 - Not An Artist Folder"
                album.mkdir(parents=True)
                make_silent_flac(album, "01-misc-song_one")
                make_silent_flac(album, "02-misc-song_two")
                self.assertNotIn(
                    "redundant_album_artist_filename_group",
                    finding_categories(BatchAudit(root).audit()),
                )

            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                album = root / "Babymetal" / "2019 - Collision"
                album.mkdir(parents=True)
                first = make_silent_flac(
                    album, "01-babymetal-song_one"
                )
                second = make_silent_flac(
                    album, "02-babymetal-song_two"
                )
                album.joinpath("1_Song One.flac").write_bytes(b"collision")
                finding = next(
                    item
                    for item in BatchAudit(root).audit()["findings"]
                    if item["category"]
                    == "redundant_album_artist_filename_group"
                )
                with self.assertRaises(FileExistsError):
                    apply_finding(root, finding, use_color=False)
                self.assertTrue(first.exists())
                self.assertTrue(second.exists())

        def test_multidisc_album_prefix_is_preserved_across_sidecars_and_backups(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                album = root / "Heavens To Betsy" / "1992 - Heavens To Betsy (demo)"
                album.mkdir(parents=True)
                stems = (
                    "1_1_Good Food",
                    "1_2_Factory",
                    "2_1_My Red Self",
                    "2_2_Baby's Gone",
                )
                audio_paths = [make_silent_flac(album, stem) for stem in stems]
                first = audio_paths[0]
                first.with_suffix(".lrc").write_text("[00:00.00]Line\n", encoding="utf-8")
                first.with_suffix(".txt").write_text("Line\n", encoding="utf-8")
                album.joinpath(first.name + "._vad_ten.srt").write_text(
                    "scratch", encoding="utf-8"
                )
                album.joinpath(
                    first.name + ".bak.202608121346.replaced-by-chatgpt.bak"
                ).write_bytes(first.read_bytes())

                self.assertTrue(album_uses_disc_track_prefix(audio_paths))
                self.assertIsNone(
                    capitalized_album_filename_proposal(
                        "1_1_Good Food.flac",
                        4,
                        compound_track_prefix=True,
                    )
                )
                self.assertIsNone(
                    capitalized_album_filename_proposal(
                        "1_1_Good Food.flac._vad_ten.srt",
                        4,
                        compound_track_prefix=True,
                    )
                )
                self.assertEqual(
                    "1_1_Good Food.flac",
                    capitalized_album_filename_proposal(
                        "1_1_good_food.flac",
                        4,
                        compound_track_prefix=True,
                    ),
                )
                findings = [
                    item
                    for item in BatchAudit(root).audit()["findings"]
                    if item["category"] == "filename_title_capitalization_group"
                ]
                self.assertEqual([], findings)

        def test_album_title_capitalization_group_includes_sidecars_and_backup(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                album = root / "Babymetal" / "2025 - Test Album"
                album.mkdir(parents=True)
                audio = make_silent_flac(album, "01_from_me_to_u")
                lyric = audio.with_suffix(".lrc")
                lyric.write_text("[00:00.00]Line\n", encoding="utf-8")
                backup = album / (
                    f"{audio.name}.bak.202607301200."
                    "replaced-by-chatgpt.bak"
                )
                backup.write_bytes(audio.read_bytes())
                make_silent_flac(album, "02_RATATATA")
                finding = next(
                    item
                    for item in BatchAudit(root).audit()["findings"]
                    if item["category"]
                    == "filename_title_capitalization_group"
                )
                proposed = {
                    Path(item["after"]).name
                    for item in finding["details"]["renames"]
                }
                self.assertIn("1_From Me To U.flac", proposed)
                self.assertIn("1_From Me To U.lrc", proposed)
                self.assertIn(
                    "1_From Me To U.flac.bak.202607301200."
                    "replaced-by-chatgpt.bak",
                    proposed,
                )
                with contextlib.redirect_stdout(io.StringIO()):
                    result = interactive_apply(
                        {
                            "findings": [finding],
                            "resolved_root": str(root),
                        },
                        use_color=False,
                        key_reader=lambda: "y",
                    )
                self.assertFalse(result["failed_codes"], result)
                self.assertTrue(
                    album.joinpath("1_From Me To U.flac").is_file()
                )
                self.assertTrue(
                    album.joinpath("1_From Me To U.lrc").is_file()
                )
                self.assertTrue(
                    album.joinpath(
                        "1_From Me To U.flac.bak.202607301200."
                        "replaced-by-chatgpt.bak"
                    ).is_file()
                )

        def test_trailing_download_tracking_ids_are_removed_from_titles(
            self,
        ) -> None:
            self.assertEqual(
                "01_Retrograde.mp3",
                redundant_artist_filename_proposal(
                    "01_Bad Cop-bad Cop-retrograde-e75e4ec6.mp3",
                    "Bad Cop, Bad Cop",
                    12,
                ),
            )
            self.assertEqual(
                "02_Im Done.mp3",
                capitalized_album_filename_proposal(
                    "02_im_done-35876105.mp3",
                    12,
                ),
            )
            self.assertEqual(
                "03_Womanarchist.mp3",
                capitalized_album_filename_proposal(
                    "03_womanarchist-f45_cc0d.mp3",
                    12,
                ),
            )
            self.assertEqual(
                "02_Im Done.mp3.bak.202607301445."
                "replaced-by-chatgpt.bak",
                capitalized_album_filename_proposal(
                    "02_im_done-35876105.mp3.bak.202607301445."
                    "replaced-by-chatgpt.bak",
                    12,
                ),
            )
            self.assertEqual(
                "04_Deadbeef.mp3",
                capitalized_album_filename_proposal(
                    "04_deadbeef.mp3",
                    12,
                ),
            )

        def test_multichannel_replaygain_is_detected_without_stereo_exemption(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                path = make_silent_flac(
                    root, "Surround Test [instrumental]", channels=6
                )
                report = BatchAudit(root).audit()
                categories = finding_categories(report)
                self.assertIn("multichannel_audio", categories)
                self.assertIn("missing_replaygain", categories)
                multichannel = next(
                    item
                    for item in report["findings"]
                    if item["category"] == "multichannel_audio"
                )
                self.assertEqual(6, multichannel["details"]["channels"])
                self.assertIn("rsgain", multichannel["suggestion"])

                audio = FLAC(path)
                # The established tagger writes a bare numeric gain; the
                # equally valid form "-7.25 dB" is covered by other tests.
                audio["REPLAYGAIN_TRACK_GAIN"] = ["-7.25"]
                audio["REPLAYGAIN_TRACK_PEAK"] = ["0.875"]
                audio.save()
                categories = finding_categories(BatchAudit(root).audit())
                self.assertIn("multichannel_audio", categories)
                self.assertNotIn("missing_replaygain", categories)

        def test_replaygain_findings_are_aggregated_per_folder(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                album = root / "Album"
                album.mkdir()
                first = make_silent_flac(album, "01_First [instrumental]")
                second = make_silent_flac(album, "02_Second [instrumental]")
                findings = [
                    item
                    for item in BatchAudit(root).audit()["findings"]
                    if item["category"] == "missing_replaygain"
                ]
                self.assertEqual(1, len(findings))
                finding = findings[0]
                self.assertEqual("Album", finding["path"])
                self.assertTrue(finding["details"]["folder_level"])
                self.assertEqual(2, finding["details"]["missing_count"])
                self.assertEqual(2, finding["details"]["total_count"])
                self.assertIn("all 2 audio files", finding["message"])

                audio = FLAC(first)
                audio["REPLAYGAIN_TRACK_GAIN"] = ["-7.25"]
                audio["REPLAYGAIN_TRACK_PEAK"] = ["0.875"]
                audio.save()
                findings = [
                    item
                    for item in BatchAudit(root).audit()["findings"]
                    if item["category"] == "missing_replaygain"
                ]
                self.assertEqual(1, len(findings))
                self.assertEqual(1, findings[0]["details"]["missing_count"])
                self.assertEqual(2, findings[0]["details"]["total_count"])
                self.assertIn("1 of 2 audio files", findings[0]["message"])
                self.assertTrue(second.is_file())

        def test_missing_srt_findings_are_aggregated_per_folder(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                album = root / "Album"
                album.mkdir()
                for stem in ("01_First", "02_Second"):
                    audio = make_silent_flac(album, stem)
                    audio.with_suffix(".txt").write_text("Lyric\n", encoding="utf-8")
                    audio.with_suffix(".lrc").write_text(
                        "[00:00.00]Lyric\n", encoding="utf-8"
                    )
                findings = [
                    item
                    for item in BatchAudit(root).audit()["findings"]
                    if item["category"] == "missing_srt_from_lrc_txt"
                ]
                self.assertEqual(1, len(findings))
                finding = findings[0]
                self.assertEqual("Album", finding["path"])
                self.assertTrue(finding["details"]["folder_level"])
                self.assertEqual(2, finding["details"]["missing_count"])
                self.assertEqual(2, len(finding["details"]["affected_files"]))
                self.assertIn("2 tracks in this folder", finding["message"])

        def test_lyric_karaoke_fix_treats_stale_nonzero_srt_as_already_done(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                audio = make_silent_flac(root, "01_Already Done")
                audio.with_suffix(".txt").write_text("Lyric\n", encoding="utf-8")
                audio.with_suffix(".lrc").write_text("[00:00.00]Lyric\n", encoding="utf-8")
                audio.with_suffix(".srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nLyric\n", encoding="utf-8")
                with mock.patch.object(subprocess, "run") as run, contextlib.redirect_stdout(io.StringIO()) as output:
                    actions = generate_missing_srt_sidecars(
                        root,
                        root,
                        expected_audio_paths=[audio],
                    )
                run.assert_not_called()
                self.assertIn("nothing to do", output.getvalue())
                self.assertTrue(any(action.startswith("lyric_karaoke_fix_summary:0|") for action in actions))

        def test_lyric_karaoke_fix_recycles_zero_byte_srt_then_regenerates(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                audio = make_silent_flac(root, "01_Empty SRT")
                audio.with_suffix(".txt").write_text("Lyric\n", encoding="utf-8")
                audio.with_suffix(".lrc").write_text("[00:00.00]Lyric\n", encoding="utf-8")
                empty_srt = audio.with_suffix(".srt")
                empty_srt.touch()
                tool = root / "lrc2srt.py"
                tool.write_text("# tool\n", encoding="utf-8")

                recycled: list[Path] = []
                def fake_recycle(path):
                    recycled.append(Path(path))
                    Path(path).unlink()
                    return Path(path)

                def fake_run(command, **options):
                    empty_srt.write_text(
                        "1\n00:00:00,000 --> 00:00:01,000\nLyric\n",
                        encoding="utf-8",
                    )
                    # Exercise the real-world oddity: nonzero status even though
                    # the expected output is now valid.
                    return mock.Mock(returncode=1, stdout="MiniLyricsFix: No files to process.")

                module = sys.modules[__name__]
                with mock.patch.object(module, "lrc2srt_executable", return_value=tool), mock.patch.object(module, "recycle_path", side_effect=fake_recycle), mock.patch.object(subprocess, "run", side_effect=fake_run), contextlib.redirect_stdout(io.StringIO()) as output:
                    actions = generate_missing_srt_sidecars(
                        root,
                        root,
                        expected_audio_paths=[audio],
                    )
                self.assertEqual([empty_srt], recycled)
                self.assertGreater(empty_srt.stat().st_size, 0)
                self.assertNotIn("MiniLyricsFix", output.getvalue())
                self.assertIn("Lyric/Karaoke Fix", output.getvalue())
                self.assertTrue(any(action.startswith("recycled_empty_srt:") for action in actions))

        def test_replaygain_progress_ticks_between_flac_completions(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                first = root / "01_First.flac"
                second = root / "02_Second.flac"
                first.write_bytes(b"a" * 1000)
                second.write_bytes(b"b" * 1000)
                snapshots: list[float] = []
                postfixes: list[str] = []

                class FakeProgress:
                    def __init__(self) -> None:
                        self.n = 0.0

                    def set_postfix_str(self, value, refresh=False):
                        postfixes.append(str(value))

                    def refresh(self):
                        snapshots.append(float(self.n))

                @contextmanager
                def fake_progress_bar(**_kwargs):
                    yield FakeProgress()

                elapsed_values = iter((1.0, 1.5))

                def fake_polled(command, *, cwd, on_tick=None, poll_seconds=0.10):
                    elapsed = next(elapsed_values)
                    if on_tick is not None:
                        on_tick(elapsed * 0.25)
                        on_tick(elapsed * 0.75)
                    return elapsed

                module = sys.modules[__name__]
                with mock.patch.object(
                    module, "require_replaygain_program", return_value="metaflac"
                ), mock.patch.object(
                    module, "run_silent_polled_command", side_effect=fake_polled
                ), mock.patch.object(
                    module, "record_replaygain_timing"
                ) as record_timing, mock.patch.object(
                    module, "progress_bar", new=fake_progress_bar
                ), contextlib.redirect_stdout(io.StringIO()) as output:
                    actions = apply_argt_replaygain_folder(
                        root, use_color=False, stream_output=False
                    )

                self.assertEqual(2, record_timing.call_count)
                self.assertTrue(any(0.5 < value < 1.0 for value in snapshots))
                self.assertTrue(any("ETA" in value for value in postfixes))
                self.assertNotIn("--add-replay-gain", output.getvalue())
                self.assertTrue(
                    any(action.startswith("replaygain_summary:2|0|2|") for action in actions)
                )

        def test_argt_replaygain_workflow_streams_and_reaudits(self) -> None:
            if not shutil.which("metamp3") or not shutil.which("metaflac"):
                raise unittest.SkipTest(
                    "metamp3 and metaflac are required for the ARGT test"
                )
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                mp3_path = make_silent_mp3(root, "ARGT MP3 [instrumental]")
                flac_path = make_silent_flac(root, "ARGT FLAC [instrumental]")
                cover = root / "cover.jpg"
                cover.write_bytes(b"\xff\xd8\xffdo-not-touch")
                cover_hash = hashlib.sha256(cover.read_bytes()).hexdigest()

                before = audit_categories_by_path(root)
                self.assertIn("missing_replaygain", before[str(mp3_path.name)])
                self.assertIn("missing_replaygain", before[str(flac_path.name)])

                actions = apply_argt_replaygain_folder(
                    root,
                    use_color=False,
                    stream_output=False,
                )
                backups = [
                    Path(action.removeprefix("backup:"))
                    for action in actions
                    if action.startswith("backup:")
                ]
                self.assertEqual(2, len(backups))
                self.assertTrue(all(path.is_file() for path in backups))
                self.assertTrue(mp3_path.is_file())
                self.assertTrue(flac_path.is_file())
                self.assertFalse(any(root.glob("ohhhh*")))
                self.assertEqual(
                    cover_hash, hashlib.sha256(cover.read_bytes()).hexdigest()
                )

                after = audit_categories_by_path(root)
                self.assertNotIn("missing_replaygain", after[str(mp3_path.name)])
                self.assertNotIn("missing_replaygain", after[str(flac_path.name)])

                previous_pair = globals()["_LAST_RANDOM_CONSOLE_PAIR"]
                globals()["_LAST_RANDOM_CONSOLE_PAIR"] = None
                try:
                    seeded = random.Random(20260730)
                    with contextlib.redirect_stdout(io.StringIO()):
                        first_color = emit_argt_random_color(
                            foreground_only=False,
                            use_color=True,
                            random_source=seeded,
                        )
                        second_color = emit_argt_random_color(
                            foreground_only=False,
                            use_color=True,
                            random_source=seeded,
                        )
                        foreground_color = emit_argt_random_color(
                            foreground_only=True,
                            use_color=True,
                            random_source=seeded,
                        )
                    self.assertRegex(first_color, r"^\x1b\[\d+;\d+m$")
                    self.assertRegex(second_color, r"^\x1b\[\d+;\d+m$")
                    self.assertRegex(foreground_color, r"^\x1b\[\d+m$")
                    self.assertNotEqual(first_color, second_color)
                finally:
                    globals()["_LAST_RANDOM_CONSOLE_PAIR"] = previous_pair

                class Completed:
                    returncode = 0
                    stdout = ""

                original_run = subprocess.run
                recorded_options: dict[str, Any] = {}

                def fake_run(command, **options):
                    recorded_options.update(options)
                    return Completed()

                subprocess.run = fake_run
                try:
                    with contextlib.redirect_stdout(io.StringIO()):
                        run_live_command(
                            ["example-tool", "--visible"],
                            cwd=root,
                            stream_output=True,
                        )
                finally:
                    subprocess.run = original_run
                self.assertNotIn("stdout", recorded_options)
                self.assertNotIn("stderr", recorded_options)

        def test_folder_wide_replaygain_prompt_offers_folder_and_always_choices(
            self,
        ) -> None:
            prompt = action_scope_prompt(
                ACTION_PROMPT_QUESTIONS["missing_replaygain"],
                default_yes=True,
                use_color=False,
                allow_folder=True,
                allow_always=True,
                allow_stop_folder=True,
            )
            self.assertIn("Run ReplayGain on this folder now?", prompt)
            self.assertIn("F=Yes for This Folder", prompt)
            self.assertIn("A=Always", prompt)
            self.assertIn("S=Not for This Folder", prompt)

        def test_finished_and_unfinished_vad_scratch_are_distinguished(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                finished = root / "finished.flac._vad_ten.srt"
                unfinished = root / "unfinished.flac._vad_ten.srt"
                finished.write_text("scratch", encoding="utf-8")
                unfinished.write_text("scratch", encoding="utf-8")
                root.joinpath("finished.txt").write_text("finished", encoding="utf-8")

                findings = BatchAudit(root).audit()["findings"]
                by_path = {item["path"]: item for item in findings if "vad_scratch" in item["category"]}

                self.assertEqual("safe_cleanup", by_path[finished.name]["severity"])
                self.assertEqual("ask_first", by_path[unfinished.name]["severity"])

        def test_archive_findings_disappear_after_immediate_actions(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                archive = root / "ORIGINAL-UNMERGED-VERSIONS"
                archive.mkdir()
                make_silent_flac(archive, "Theme [instrumental]")
                report = BatchAudit(root).audit()
                actionable = [
                    item
                    for item in report["findings"]
                    if item["category"]
                    in {"archive_missing_attrib", "archive_missing_marker"}
                ]
                self.assertEqual(2, len(actionable))
                for finding in actionable:
                    apply_finding(root, finding)

                categories = finding_categories(BatchAudit(root).audit())

                self.assertNotIn("archive_missing_attrib", categories)
                self.assertNotIn("archive_incomplete_attrib", categories)
                self.assertNotIn("archive_missing_marker", categories)

                attrib = archive / "attrib.lst"
                attrib.write_text("custom line\n", encoding="utf-8")
                incomplete = next(
                    item
                    for item in BatchAudit(root).audit()["findings"]
                    if item["category"] == "archive_incomplete_attrib"
                )
                repair_actions = apply_finding(root, incomplete)
                attrib_backups = [
                    Path(action.removeprefix("backup:"))
                    for action in repair_actions
                    if action.startswith("backup:")
                ]
                self.assertEqual(1, len(attrib_backups))
                self.assertTrue(attrib_backups[0].is_file())
                self.assertEqual(
                    "custom line\n", read_text(attrib_backups[0])
                )
                self.assertIn(DO_NOT_PLAY_LINE, read_text(attrib))

        def test_duplicate_audio_and_numbered_image_detection_has_negative_control(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                flac = make_silent_flac(root, "Duplicate [instrumental]")
                root.joinpath("Duplicate [instrumental].mp3").write_bytes(flac.read_bytes())
                root.joinpath("cover.jpg").write_bytes(b"\xff\xd8\xfflarger-image")
                root.joinpath("cover (2).jpg").write_bytes(b"\xff\xd8\xffsmall")
                root.joinpath("unique.jpg").write_bytes(b"\xff\xd8\xffunique")

                report = BatchAudit(root).audit()
                categories = finding_categories(report)

                self.assertIn("same_stem_mp3_flac", categories)
                self.assertIn("smaller_numbered_image_duplicate", categories)
                self.assertFalse(
                    any(
                        item["category"] == "smaller_numbered_image_duplicate"
                        and item["path"] == "unique.jpg"
                        for item in report["findings"]
                    )
                )

        def test_genre_comment_art_and_lyric_sidecar_findings(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                audio_path = make_silent_flac(root, "07 Sidecar Song")
                audio = FLAC(audio_path)
                audio["TITLE"] = ["Sidecar Song"]
                audio["ARTIST"] = ["Artist"]
                audio["ALBUM"] = ["Album"]
                audio["GENRE"] = ["Pop Punk; Riot Grrrl; Punk"]
                audio["COMMENT"] = ["https://example.test/song"]
                audio.save()
                audio_path.with_suffix(".txt").write_text("Line\n", encoding="utf-8")
                audio_path.with_suffix(".lrc").write_text(
                    "[00:00.00]Line\n", encoding="utf-8"
                )
                audio_path.with_suffix(".jpg").write_bytes(b"\xff\xd8\xffcover")

                categories = finding_categories(BatchAudit(root).audit())

                self.assertTrue(
                    {
                        "simplify_punk_genre",
                        "url_comment",
                        "missing_embedded_art",
                        "plain_lyrics_not_embedded",
                        "karaoke_not_embedded",
                        "missing_srt_from_lrc_txt",
                    }.issubset(categories)
                )

        def test_single_punk_family_genre_is_already_simple(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                audio_path = make_silent_flac(root, "Simple Punk [instrumental]")
                audio = FLAC(audio_path)
                audio["TITLE"] = ["Simple Punk"]
                audio["ARTIST"] = ["Artist"]
                audio["ALBUM"] = ["Album"]
                audio["GENRE"] = ["Punk Rock"]
                audio.save()
                categories = finding_categories(BatchAudit(root).audit())
                self.assertNotIn("simplify_punk_genre", categories)

        def test_punk_genre_menu_defaults_to_punk_and_offers_components(self) -> None:
            finding = {
                "details": {
                    "genres": ["Alternative Rock;Indie Rock;Punk;Rock"],
                    "genre_components": [
                        "Alternative Rock", "Indie Rock", "Punk", "Rock"
                    ],
                }
            }
            choices, existing = punk_genre_menu_values(finding)
            self.assertEqual(
                ["Punk", "Alternative Rock", "Indie Rock", "Rock"],
                choices,
            )
            self.assertEqual("Alternative Rock;Indie Rock;Punk;Rock", existing)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    "Punk",
                    prompt_for_punk_genre_selection(
                        finding, use_color=False, input_reader=lambda _prompt: ""
                    ),
                )
                self.assertEqual(
                    "Indie Rock",
                    prompt_for_punk_genre_selection(
                        finding, use_color=False, input_reader=lambda _prompt: "3"
                    ),
                )
                self.assertEqual(
                    PUNK_GENRE_KEEP_EXISTING,
                    prompt_for_punk_genre_selection(
                        finding, use_color=False, input_reader=lambda _prompt: "5"
                    ),
                )

        def test_punk_genre_choice_can_be_remembered_for_rest_of_folder(self) -> None:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                scope = prompt_remember_punk_genre_selection(
                    "Punk",
                    use_color=False,
                    key_reader=lambda: "f",
                )
            self.assertEqual("folder", scope)
            self.assertIn("F=Yes for Rest of Folder", output.getvalue())

        def test_genre_writer_backs_up_and_verifies_selected_value(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                audio_path = make_silent_flac(root, "Genre Choice [instrumental]")
                audio = FLAC(audio_path)
                audio["GENRE"] = ["Punk; Riot Grrrl; Rock"]
                audio.save()
                written, backup = set_genre_tag(audio_path, "Riot Grrrl")
                self.assertEqual("Riot Grrrl", written)
                self.assertTrue(backup.is_file())
                self.assertEqual(["Riot Grrrl"], FLAC(audio_path).get("GENRE"))
                self.assertEqual(
                    ["Punk; Riot Grrrl; Rock"], FLAC(backup).get("GENRE")
                )

        def test_detected_problems_header_emits_both_double_height_halves(self) -> None:
            report = {
                "root": ".",
                "resolved_root": str(Path.cwd()),
                "counts": {
                    "active_audio": 1,
                    "files": 1,
                    "by_severity": {},
                },
                "findings": [
                    {
                        "severity": "problem",
                        "category": "missing_genre",
                        "path": "song.flac",
                        "message": "Missing genre tag.",
                        "suggestion": "Set a genre.",
                        "code": None,
                        "details": {},
                    }
                ],
                "extension_counts": {},
                "mutagen_available": True,
                "pillow_available": True,
            }
            rendered = render_console_report(
                report, max_examples=80, use_color=True, interactive=False
            )
            def visible_text(value: str) -> str:
                return re.sub(
                    r"\x1b(?:\[[0-?]*[ -/]*[@-~]|#[34])",
                    "",
                    value,
                )

            visible = visible_text(rendered)
            self.assertIn("Detected Problems", visible)
            header_lines = [
                line
                for line in rendered.splitlines()
                if "Detected Problems" in visible_text(line)
            ]
            self.assertEqual(2, len(header_lines))
            self.assertTrue(header_lines[0].startswith(ANSI_DOUBLE_HEIGHT_TOP))
            self.assertTrue(header_lines[1].startswith(ANSI_DOUBLE_HEIGHT_BOTTOM))

        def test_no_argument_music_scan_includes_depth_zero_through_five_only(self) -> None:
            for audio_depth in range(6):
                with tempfile.TemporaryDirectory() as temp:
                    root = Path(temp)
                    folder = root
                    for index in range(audio_depth):
                        folder = folder / f"d{index + 1}"
                        folder.mkdir()
                    folder.joinpath("song.flac").write_bytes(b"music")
                    self.assertTrue(
                        music_exists_within_depth(root, 5),
                        f"audio at depth {audio_depth} should be detected",
                    )
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                folder = root
                for index in range(6):
                    folder = folder / f"d{index + 1}"
                    folder.mkdir()
                folder.joinpath("too-deep.mp3").write_bytes(b"music")
                self.assertFalse(music_exists_within_depth(root, 5))

        def test_no_argument_music_scan_follows_directory_links_without_looping(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                real = root / "real"
                real.mkdir()
                real.joinpath("song.flac").write_bytes(b"music")
                link = root / "linked"
                try:
                    link.symlink_to(real, target_is_directory=True)
                except (OSError, NotImplementedError):
                    self.skipTest("directory symlinks are unavailable")
                self.assertTrue(music_exists_within_depth(link, 5))
                # A loop must not matter because resolved directories are visited once.
                try:
                    (real / "loop").symlink_to(root, target_is_directory=True)
                except (OSError, NotImplementedError):
                    pass
                self.assertTrue(music_exists_within_depth(root, 5))

        def test_no_argument_menu_and_release_announcement_are_explicit(self) -> None:
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                choice = prompt_no_argument_menu(
                    use_color=False, key_reader=lambda: "1"
                )
            self.assertEqual("1", choice)
            visible = output.getvalue()
            self.assertIn("1) Run audit in this folder", visible)
            self.assertIn("2) Display usage instructions", visible)
            release = io.StringIO()
            with contextlib.redirect_stderr(release):
                announce_release(use_color=False)
            self.assertIn(AUDIT_MUSIC_BATCH_VERSION, release.getvalue())
            self.assertIn(AUDIT_MUSIC_BATCH_RELEASE_DATE, release.getvalue())

        def test_no_argument_windows_menu_does_not_depend_on_stdin_isatty(self) -> None:
            class NonTTY(io.StringIO):
                def isatty(self) -> bool:
                    return False
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                root.joinpath("song.flac").write_bytes(b"music")
                module = sys.modules[__name__]
                with mock.patch.object(Path, "cwd", return_value=root), mock.patch.object(
                    os, "name", "nt"
                ), mock.patch.object(sys, "stdin", NonTTY()), mock.patch.object(
                    module, "prompt_no_argument_menu", return_value="2"
                ) as menu, contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(0, _main([]))
                menu.assert_called_once()

        def test_untimed_lrc_is_not_mistaken_for_karaoke(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                audio_path = make_silent_flac(root, "08 Untimed Song")
                audio_path.with_suffix(".txt").write_text("Line\n", encoding="utf-8")
                audio_path.with_suffix(".lrc").write_text("Line\n", encoding="utf-8")

                categories = finding_categories(BatchAudit(root).audit())

                self.assertIn("lrc_txt_missing_srt_but_lrc_untimed", categories)
                self.assertIn("unusable_karaoke_sidecar", categories)
                self.assertNotIn("missing_karaoke", categories)
                self.assertNotIn("karaoke_not_embedded", categories)

        def test_safe_path_and_recycle_action(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                marker = root / "__"
                marker.touch()
                finding = next(
                    item
                    for item in BatchAudit(root).audit()["findings"]
                    if item["category"] == "bare_marker"
                )
                actions = apply_finding(root, finding)
                self.assertEqual([f"recycled:{marker}"], actions)
                self.assertFalse(marker.exists())
                with self.assertRaises(ValueError):
                    safe_finding_path(root, {"path": str(root / ".." / "outside.txt")})

        def test_zero_byte_media_and_sidecars_are_reported(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                root.joinpath("empty.flac").touch()
                root.joinpath("empty.lrc").touch()
                root.joinpath("empty.jpg").touch()

                report = BatchAudit(root).audit()
                zero_byte_paths = {
                    item["path"]
                    for item in report["findings"]
                    if item["category"] == "zero_byte_media_or_sidecar"
                }

                self.assertEqual({"empty.flac", "empty.lrc", "empty.jpg"}, zero_byte_paths)
                self.assertIn("unreadable_audio", finding_categories(report))

        def test_artwork_states_distinguish_sidecarless_single_and_multiple(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                audio_path = make_silent_flac(root, "09 Artwork States [instrumental]")
                audio = FLAC(audio_path)
                front = Picture()
                front.type = 3
                front.mime = "image/jpeg"
                front.data = b"\xff\xd8\xfffront"
                audio.add_picture(front)
                audio.save()
                categories = finding_categories(BatchAudit(root).audit())
                self.assertIn("embedded_art_without_sidecar", categories)
                self.assertNotIn("multiple_embedded_artworks", categories)

                root.joinpath("cover.jpg").write_bytes(front.data)
                audio = FLAC(audio_path)
                back = Picture()
                back.type = 4
                back.mime = "image/jpeg"
                back.data = b"\xff\xd8\xffback"
                audio.add_picture(back)
                audio.save()
                categories = finding_categories(BatchAudit(root).audit())
                self.assertNotIn("embedded_art_without_sidecar", categories)
                self.assertIn("multiple_embedded_artworks", categories)

                mp3_root = root / "mp3-misc"
                mp3_root.mkdir()
                mp3_path = make_silent_mp3(mp3_root, "Ghosts (2023)")
                mp3 = ensure_id3(mp3_path)
                mp3.tags.add(
                    APIC(
                        encoding=3,
                        mime="image/jpeg",
                        type=3,
                        desc="Cover",
                        data=b"\xff\xd8\xffmp3-front",
                    )
                )
                mp3.save(v2_version=3)
                self.assertIn(
                    "embedded_art_without_sidecar",
                    finding_categories(BatchAudit(mp3_root).audit()),
                )
                mp3_root.joinpath("Ghosts (2023).jpg").write_bytes(
                    b"\xff\xd8\xffsame-stem-sidecar"
                )
                self.assertNotIn(
                    "embedded_art_without_sidecar",
                    finding_categories(BatchAudit(mp3_root).audit()),
                )

        def test_second_matching_artwork_finding_is_resurveyed_and_skipped(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                first = make_silent_flac(root, "01 First")
                second = make_silent_flac(root, "02 Second")
                picture_data = b"\xff\xd8\xffshared-front"
                for audio_path in (first, second):
                    audio = FLAC(audio_path)
                    front = Picture()
                    front.type = 3
                    front.mime = "image/jpeg"
                    front.data = picture_data
                    audio.add_picture(front)
                    audio.save()
                findings = [
                    item for item in BatchAudit(root).audit()["findings"]
                    if item["category"] == "embedded_art_without_sidecar"
                ]
                self.assertEqual(2, len(findings))
                apply_finding(root, findings[0], use_color=False)
                self.assertFalse(
                    artwork_finding_still_needs_action(root, findings[1])
                )

        def test_archive_exclusion_and_comment_classification_have_controls(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                active = make_silent_flac(root, "10 Comment Song [instrumental]")
                audio = FLAC(active)
                audio["TITLE"] = ["Comment Song"]
                audio["ARTIST"] = ["Artist"]
                audio["ALBUM"] = ["Album"]
                audio["GENRE"] = [""]
                audio["COMMENT"] = ["A real descriptive comment"]
                audio.save()
                archive = root / "archive"
                archive.mkdir()
                make_silent_flac(archive, "Archived Vocal")

                default_report = BatchAudit(root).audit()
                included_report = BatchAudit(root, include_archives=True).audit()
                default_categories = finding_categories(default_report)
                included_categories = finding_categories(included_report)

                self.assertIn("empty_genre", default_categories)
                self.assertIn("comment_present", default_categories)
                self.assertNotIn("url_comment", default_categories)
                archived_default = [
                    item
                    for item in default_report["findings"]
                    if item["path"].startswith("archive\\")
                    and item["category"] == "missing_title"
                ]
                archived_included = [
                    item
                    for item in included_report["findings"]
                    if item["path"].startswith("archive\\")
                    and item["category"] == "missing_title"
                ]
                self.assertEqual([], archived_default)
                self.assertEqual(1, len(archived_included))

        def test_valid_genre_does_not_report_missing_or_empty_genre(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                path = make_silent_flac(root, "11 Valid Genre [instrumental]")
                audio = FLAC(path)
                audio["GENRE"] = ["Rock"]
                audio.save()
                categories = finding_categories(BatchAudit(root).audit())
                self.assertNotIn("missing_genre", categories)
                self.assertNotIn("empty_genre", categories)

        def test_empty_genre_reports_empty_genre(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                path = make_silent_flac(root, "12 Empty Genre [instrumental]")
                audio = FLAC(path)
                audio["GENRE"] = [""]
                audio.save()
                self.assertIn("empty_genre", finding_categories(BatchAudit(root).audit()))

        def test_present_replaygain_does_not_report_missing_replaygain(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                path = make_silent_flac(root, "13 ReplayGain [instrumental]")
                audio = FLAC(path)
                audio["REPLAYGAIN_TRACK_GAIN"] = ["-4.00 dB"]
                audio["REPLAYGAIN_TRACK_PEAK"] = ["0.8"]
                audio.save()
                self.assertNotIn(
                    "missing_replaygain", finding_categories(BatchAudit(root).audit())
                )

        def test_absent_replaygain_reports_missing_replaygain(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                make_silent_flac(root, "14 No ReplayGain [instrumental]")
                self.assertIn(
                    "missing_replaygain", finding_categories(BatchAudit(root).audit())
                )

        def test_embedded_plain_lyrics_do_not_report_missing_plain_lyrics(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                path = make_silent_flac(root, "15 Plain Lyrics")
                audio = FLAC(path)
                audio["LYRICS"] = ["A line"]
                audio.save()
                categories = finding_categories(BatchAudit(root).audit())
                self.assertNotIn("missing_plain_lyrics", categories)
                self.assertNotIn("plain_lyrics_not_embedded", categories)

        def test_absent_plain_lyrics_report_missing_plain_lyrics(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                make_silent_flac(root, "16 No Plain Lyrics")
                self.assertIn(
                    "missing_plain_lyrics", finding_categories(BatchAudit(root).audit())
                )

        def test_embedded_karaoke_does_not_report_missing_karaoke(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                path = make_silent_flac(root, "17 Embedded Karaoke")
                audio = FLAC(path)
                audio["SYNCEDLYRICS"] = ["[00:00.00]A line"]
                audio.save()
                categories = finding_categories(BatchAudit(root).audit())
                self.assertNotIn("missing_karaoke", categories)
                self.assertNotIn("karaoke_not_embedded", categories)

        def test_absent_karaoke_reports_missing_karaoke(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                make_silent_flac(root, "18 No Karaoke")
                report = BatchAudit(root).audit()
                finding = next(
                    item
                    for item in report["findings"]
                    if item["category"] == "missing_karaoke"
                )
                self.assertIn(
                    "no timestamped LRC/SRT sidecar were found",
                    finding["message"],
                )
                self.assertNotIn("code", finding)

        def test_all_caps_album_titles_offer_editable_normalization(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                album = root / "Lauren Sanderson" / "2022 - Death of a Fantasy"
                album.mkdir(parents=True)
                audio = make_silent_flac(album, "05_DON'T WATCH THE NEWS!")
                sidecar = audio.with_suffix(".srt")
                sidecar.write_text("1\n00:00:00,000 --> 00:00:01,000\nHi\n")
                mixed = make_silent_flac(album, "08_Girl From The Internet")
                self.assertEqual(
                    "05_Don't Watch The News!.flac",
                    all_caps_album_title_proposal(audio.name, 11),
                )
                self.assertIsNone(all_caps_album_title_proposal(mixed.name, 11))
                report = BatchAudit(root).audit()
                finding = next(
                    item for item in report["findings"]
                    if item["category"] == "all_caps_album_title"
                )
                with contextlib.redirect_stdout(io.StringIO()):
                    actions = apply_finding(
                        root,
                        finding,
                        use_color=False,
                        input_reader=lambda _prompt: "05_Custom News Title.flac",
                    )
                self.assertTrue((album / "05_Custom News Title.flac").is_file())
                self.assertTrue((album / "05_Custom News Title.srt").is_file())
                self.assertIn("renamed_family:2", actions)

        def test_embedded_cover_with_sidecar_does_not_report_art_problem(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                path = make_silent_flac(root, "19 Valid Art [instrumental]")
                tag_complete_vocal_flac(path)
                categories = finding_categories(BatchAudit(root).audit())
                self.assertNotIn("missing_embedded_art", categories)
                self.assertNotIn("embedded_art_without_sidecar", categories)

        def test_missing_embedded_cover_reports_missing_embedded_art(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                path = make_silent_flac(root, "20 Missing Art [instrumental]")
                path.with_suffix(".jpg").write_bytes(b"\xff\xd8\xffcover")
                finding = next(
                    item
                    for item in BatchAudit(root).audit()["findings"]
                    if item["category"] == "missing_embedded_art"
                )
                self.assertIn("code", finding)

            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                path = make_silent_flac(
                    root, "20 Sole Folder Image [instrumental]"
                )
                sole_art = root / "Metal Galaxy album scan.jpg"
                sole_art.write_bytes(b"\xff\xd8\xffsole-front")
                finding = next(
                    item
                    for item in BatchAudit(root).audit()["findings"]
                    if item["category"] == "missing_embedded_art"
                )
                self.assertIn("code", finding)
                self.assertEqual([], finding["details"]["sidecars"])
                self.assertIn(
                    "Search for the release artwork",
                    approval_question(finding),
                )
                self.assertEqual([], FLAC(path).pictures)

            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                path = make_silent_flac(
                    root, "20 Explicit Front [instrumental]"
                )
                cover = root / "cover.jpg"
                cover.write_bytes(make_test_jpeg())
                finding = next(
                    item
                    for item in BatchAudit(root).audit()["findings"]
                    if item["category"] == "missing_embedded_art"
                )
                question = approval_question(finding)
                self.assertEqual(
                    "Embed the available front-cover sidecar (cover.jpg) "
                    "into this audio file now?",
                    question,
                )
                styled_question = urgent_prompt_text(question, True)
                self.assertIn(ANSI["dim"], styled_question)
                self.assertIn(ANSI["italic"], styled_question)
                apply_finding(root, finding, use_color=False)
                self.assertEqual(1, len(FLAC(path).pictures))

            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                path = make_silent_flac(
                    root, "20 PNG Front [instrumental]"
                )
                png = root / "folder.png"
                Image.new("RGB", (80, 80), (10, 20, 30)).save(png)
                finding = next(
                    item
                    for item in BatchAudit(root).audit()["findings"]
                    if item["category"] == "missing_embedded_art"
                )
                self.assertIn("(folder.png)", approval_question(finding))
                apply_finding(root, finding, use_color=False)
                converted = root / "folder.jpg"
                self.assertTrue(converted.is_file())
                pictures = FLAC(path).pictures
                self.assertEqual(1, len(pictures))
                self.assertEqual("image/jpeg", pictures[0].mime)
                self.assertEqual(converted.read_bytes(), pictures[0].data)

            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                make_silent_flac(
                    root, "20 Preview Front [instrumental]"
                )
                folder_art = root / "folder.jpg"
                folder_art.write_bytes(make_test_jpeg())
                finding = next(
                    item
                    for item in BatchAudit(root).audit()["findings"]
                    if item["category"] == "missing_embedded_art"
                )
                renderer = mock.Mock(return_value="mock Sixel")
                with contextlib.redirect_stdout(io.StringIO()) as output:
                    result = interactive_apply(
                        {
                            "findings": [finding],
                            "resolved_root": str(root),
                        },
                        use_color=False,
                        key_reader=lambda: "n",
                        artwork_preview_renderer=renderer,
                    )
                renderer.assert_called_once_with(
                    folder_art,
                    use_color=False,
                )
                self.assertIn(
                    "Existing front-cover sidecar preview rendered with "
                    "mock Sixel: folder.jpg.",
                    output.getvalue(),
                )
                self.assertEqual(finding["code"], result["skipped_codes"])

            for image_name in (None, "back.jpg", "disc.jpg", "proof.jpg"):
                with self.subTest(image_name=image_name):
                    with tempfile.TemporaryDirectory() as temp:
                        root = Path(temp)
                        make_silent_flac(
                            root, "20 No Front Source [instrumental]"
                        )
                        if image_name:
                            root.joinpath(image_name).write_bytes(
                                b"\xff\xd8\xffnon-front"
                            )
                        finding = next(
                            item
                            for item in BatchAudit(root).audit()["findings"]
                            if item["category"] == "missing_embedded_art"
                        )
                        self.assertIn("code", finding)
                        self.assertTrue(
                            finding["details"]["action_available"]
                        )
                        self.assertIn(
                            "Search for the release artwork",
                            approval_question(finding),
                        )
                        if image_name == "proof.jpg":
                            with self.assertRaises(RuntimeError):
                                embed_front_art(
                                    root
                                    / "20 No Front Source [instrumental].flac",
                                    root / "proof.jpg",
                                    force=True,
                                )
            self.assertEqual(
                "🎨 Embedded cover missing",
                finding_category_label("missing_embedded_art"),
            )

        def test_single_embedded_cover_does_not_report_multiple_art(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                path = make_silent_flac(root, "21 Single Art [instrumental]")
                audio = FLAC(path)
                picture = Picture()
                picture.type = 3
                picture.mime = "image/jpeg"
                picture.data = b"\xff\xd8\xfffront"
                audio.add_picture(picture)
                audio.save()
                self.assertNotIn(
                    "multiple_embedded_artworks",
                    finding_categories(BatchAudit(root).audit()),
                )

        def test_multiple_embedded_covers_report_multiple_art(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                path = make_silent_flac(root, "22 Multiple Art [instrumental]")
                audio = FLAC(path)
                for picture_type in (3, 4):
                    picture = Picture()
                    picture.type = picture_type
                    picture.mime = "image/jpeg"
                    picture.data = b"\xff\xd8\xff" + bytes([picture_type])
                    audio.add_picture(picture)
                audio.save()
                self.assertIn(
                    "multiple_embedded_artworks",
                    finding_categories(BatchAudit(root).audit()),
                )

        def test_completed_todos_log_does_not_report_active_todo(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                root.joinpath("completed-todos.log").write_text("done", encoding="utf-8")
                findings = BatchAudit(root).audit()["findings"]
                self.assertFalse(
                    any(item["category"] == "active_todo_filename" for item in findings)
                )

        def test_active_todo_filename_reports_active_todo(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                root.joinpath("TODO fix this.txt").write_text("todo", encoding="utf-8")
                self.assertIn(
                    "active_todo_filename", finding_categories(BatchAudit(root).audit())
                )

        def test_backup_is_kept_not_cleanup(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                root.joinpath("song.bak").write_text("backup", encoding="utf-8")
                report = BatchAudit(root).audit()
                findings = report["findings"]
                backup = next(item for item in findings if item["category"] == "backup_file")
                self.assertEqual("never_default", backup["severity"])
                self.assertIsNone(backup.get("code"))
                write_reports(report, root, max_examples=0)
                json_report = root / "audit_music_batch_report.json"
                json_report.write_text("pre-replacement report", encoding="utf-8")
                write_reports(report, root, max_examples=0)
                json_backups = list(
                    root.glob(
                        "audit_music_batch_report.json.bak.*."
                        "replaced-by-chatgpt.bak"
                    )
                )
                self.assertEqual(1, len(json_backups))
                self.assertEqual(
                    "pre-replacement report",
                    json_backups[0].read_text(encoding="utf-8"),
                )

        def test_unique_art_filename_is_not_numbered_duplicate(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                root.joinpath("unique.jpg").write_bytes(b"\xff\xd8\xffunique")
                self.assertNotIn(
                    "smaller_numbered_image_duplicate",
                    finding_categories(BatchAudit(root).audit()),
                )

        def test_clean_filename_does_not_report_forbidden_characters(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                root.joinpath("clean filename.txt").write_text("clean", encoding="utf-8")
                self.assertNotIn(
                    "forbidden_filename_char", finding_categories(BatchAudit(root).audit())
                )

        def test_forbidden_filename_character_is_reported(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                root.joinpath("bad^filename.txt").write_text("bad", encoding="utf-8")
                self.assertIn(
                    "forbidden_filename_char", finding_categories(BatchAudit(root).audit())
                )

        def test_album_prompt_entered_value_is_written_and_verified(self) -> None:
            root = self.album_test_root / "album-entered"
            root.mkdir()
            path = make_silent_flac(root, "Album Entry [instrumental]")
            finding = {
                "path": path.name,
                "category": "missing_album",
                "message": "Missing album tag.",
            }
            prompts: list[str] = []
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                actions = prompt_for_album_tag(
                    root,
                    finding,
                    use_color=True,
                    input_reader=lambda prompt: prompts.append(prompt)
                    or "Unit Test Album",
                )
            self.assertEqual(2, len(actions))
            self.assertTrue(actions[0].startswith("backup:"))
            self.assertEqual("album:Unit Test Album", actions[1])
            album_backup = Path(actions[0].removeprefix("backup:"))
            self.assertTrue(album_backup.is_file())
            self.assertEqual([], FLAC(album_backup).get("ALBUM", []))
            self.assertRegex(
                album_backup.name,
                r"^Album Entry \[instrumental\]\.flac\.bak\.\d{12}"
                r"\.replaced-by-chatgpt\.bak$",
            )
            self.assertEqual(["Unit Test Album"], FLAC(path).get("ALBUM"))
            self.assertIn("📁 Folder:", output.getvalue())
            self.assertIn("♪", output.getvalue())
            self.assertIn("✅", output.getvalue())
            self.assertIn("❓", prompts[0])
            self.assertTrue(output.getvalue().startswith("            📁 Folder:"))
            visible_prompt = re.sub(
                r"\x1b(?:\[[0-?]*[ -/]*[@-~]|#[34])",
                "",
                prompts[0],
            )
            self.assertTrue(visible_prompt.startswith("            ❓"))
            self.assertIn("\033[38;2;255;105;45m", prompts[0])
            self.assertIn(
                f"{ANSI['italic']}ENTER{ANSI['reset']}", prompts[0]
            )
            self.assertRegex(
                self.album_test_root.name,
                r"^audit_music_batch-testdata-\d{14}(?:-\d+)?$",
            )
            fixed_backup = backup_before_inline_replacement(
                path, timestamp="202601131231"
            )
            collision_backup = backup_before_inline_replacement(
                path, timestamp="202601131231"
            )
            self.assertEqual(
                "Album Entry [instrumental].flac.bak.202601131231."
                "replaced-by-chatgpt.bak",
                fixed_backup.name,
            )
            self.assertEqual(
                "Album Entry [instrumental].flac.bak.202601131231."
                "replaced-by-chatgpt (1).bak",
                collision_backup.name,
            )
            cover = root / "cover.jpg"
            cover.write_bytes(b"cover")
            self.assertEqual(
                root / "cover (1).jpg", collision_safe_path(cover)
            )

        def test_album_prompt_blank_enter_does_not_add_album(self) -> None:
            root = self.album_test_root / "album-blank"
            root.mkdir()
            path = make_silent_flac(root, "Blank Album [instrumental]")
            finding = {
                "path": path.name,
                "category": "missing_album",
                "message": "Missing album tag.",
            }
            prompts: list[str] = []
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                actions = prompt_for_album_tag(
                    root,
                    finding,
                    use_color=False,
                    input_reader=lambda prompt: prompts.append(prompt) or "",
                )
            self.assertEqual([], actions)
            self.assertEqual([], FLAC(path).get("ALBUM", []))
            self.assertIn("♪", output.getvalue())
            self.assertIn("❌", output.getvalue())
            self.assertIn("❓", prompts[0])
            self.assertTrue(output.getvalue().startswith("            📁 Folder:"))
            self.assertTrue(prompts[0].startswith("            ❓"))
            self.assertIn("ENTER", prompts[0])

        def test_waveform_calibration_parser_and_height_scale_signature(self) -> None:
            args = parse_args(["--calibrate-waveform-terminal", "."])
            self.assertEqual(".", args.calibrate_waveform_terminal)
            parameters = inspect.signature(prepare_waveform_preview).parameters
            self.assertIn("height_scale", parameters)

        def test_waveform_calibration_passes_exact_same_source_to_both_renderers(self) -> None:
            source = Path(r"C:\Temp\same-waveform.jpg")
            geometry = ArtworkPreviewGeometry(100, 40, 0, 50, 20, 500, 400)
            fake_a = PreparedArtworkPreview("Chafa Sixel", geometry, sixel_payload=b'\x1bPq"1;1;10;20\x1b\\')
            fake_b = PreparedArtworkPreview("Sixel", geometry, sixel_payload=b'\x1bPq"1;1;10;20\x1b\\')
            with mock.patch(
                f"{__name__}.prepare_artwork_preview", return_value=fake_a
            ) as chafa_prepare, mock.patch(
                f"{__name__}.prepare_waveform_preview", return_value=fake_b
            ) as builtin_prepare:
                result_a, result_b = build_waveform_calibration_previews(
                    source, use_color=True
                )
            self.assertIs(fake_a, result_a)
            self.assertIs(fake_b, result_b)
            self.assertEqual(source, chafa_prepare.call_args.args[0])
            self.assertEqual(source, builtin_prepare.call_args.args[0])

        def test_waveform_calibration_report_is_copy_paste_stable(self) -> None:
            report = render_waveform_calibration_report(
                {
                    "source_image": "wave.jpg",
                    "renderer_A_shared_chafa": {"rating": {"width": "good"}},
                    "renderer_B_builtin_sixel": {"rating": {"height": "too short"}},
                }
            )
            self.assertTrue(report.startswith("===== WAVEFORM TERMINAL CALIBRATION REPORT ====="))
            self.assertIn('"source_image": "wave.jpg"', report)
            self.assertIn('"height": "too short"', report)
            self.assertTrue(report.endswith("===== END WAVEFORM TERMINAL CALIBRATION REPORT ====="))

        def test_calibration_preview_record_reports_declared_sixel_raster(self) -> None:
            geometry = ArtworkPreviewGeometry(100, 40, 0, 50, 20, 500, 400)
            prepared = PreparedArtworkPreview(
                "Sixel",
                geometry,
                sixel_payload=b'\x1bPq"1;1;842;459#0~\x1b\\',
            )
            record = calibration_preview_record(prepared)
            self.assertEqual([842, 459], record["declared_sixel_raster"])
            self.assertEqual([500, 400], record["geometry_pixels"])

        def test_v125_calibration_api_consistency(self) -> None:
            parameters = inspect.signature(
                run_waveform_terminal_calibration
            ).parameters
            self.assertEqual(
                ["target", "use_color", "key_reader", "line_reader"],
                list(parameters),
            )
            preview_parameters = inspect.signature(
                prepare_waveform_preview
            ).parameters
            self.assertEqual(
                [
                    "path",
                    "use_color",
                    "width_fraction",
                    "height_rows",
                    "height_scale",
                ],
                list(preview_parameters),
            )

        def test_direct_chafa_inherits_stdio_instead_of_capturing(self) -> None:
            calls: list[dict[str, Any]] = []

            class ImmediateProcess:
                def wait(self, timeout=None):
                    self.timeout = timeout
                    return 0

            def factory(command, **kwargs):
                calls.append({"command": command, **kwargs})
                return ImmediateProcess()

            result = run_direct_chafa_calibration(
                ["chafa", "--format=sixels", "wave.jpg"],
                timeout_seconds=2.5,
                popen_factory=factory,
                clock=lambda: 10.0,
            )
            self.assertEqual(0, result["return_code"])
            self.assertEqual("inherited directly by Chafa", result["stdio"])
            self.assertIsNone(calls[0]["stdout"])
            self.assertIsNone(calls[0]["stderr"])
            self.assertIsNone(calls[0]["stdin"])
            self.assertNotEqual(subprocess.PIPE, calls[0]["stdout"])

        def test_direct_chafa_watchdog_terminates_timeout(self) -> None:
            class TimedOutProcess:
                def __init__(self):
                    self.waits = 0
                    self.terminated = False
                    self.killed = False

                def wait(self, timeout=None):
                    self.waits += 1
                    if self.waits == 1:
                        raise subprocess.TimeoutExpired("chafa", timeout)
                    return -15

                def terminate(self):
                    self.terminated = True

                def kill(self):
                    self.killed = True

            process = TimedOutProcess()
            result = run_direct_chafa_calibration(
                ["chafa", "wave.jpg"],
                timeout_seconds=0.1,
                popen_factory=lambda *args, **kwargs: process,
                clock=lambda: 20.0,
            )
            self.assertTrue(result["timed_out"])
            self.assertTrue(result["terminated"])
            self.assertTrue(process.terminated)
            self.assertFalse(process.killed)

        def test_geometry_analysis_reports_disagreement_without_reconciliation(self) -> None:
            analysis = calibration_geometry_analysis(
                {
                    "visible_cells": [100, 20],
                    "win32_viewport": {"columns": 100, "rows": 20},
                    "windows_dpi_scale": 1.0,
                    "win32_font_cell_pixels": None,
                    "csi_14_text_area_pixels": {
                        "supported": True,
                        "width": 1000,
                        "height": 400,
                    },
                    "csi_16_cell_pixels": {
                        "supported": True,
                        "width": 10,
                        "height": 20,
                    },
                    "shared_geometry": {
                        "values": {"cell_width": 7, "cell_height": 14}
                    },
                }
            )
            self.assertEqual([10.0, 20.0], analysis[
                "derived_cell_pixels_from_csi14_visible_cells"
            ])
            self.assertIsNone(analysis["reconciled_cell_pixels"])
            self.assertTrue(analysis["cell_pixel_disagreements"])
            rendered = json.dumps(analysis, sort_keys=True)
            self.assertIn("claire_terminal_geometry", rendered)
            self.assertIn("csi_16t", rendered)

        def test_chunked_sixel_emission_bounds_every_write(self) -> None:
            blocks: list[bytes] = []
            result = emit_terminal_bytes_chunked(
                b"x" * 5001,
                chunk_size=1024,
                writer=lambda block: blocks.append(bytes(block)),
                clock=lambda: 30.0,
            )
            self.assertEqual(5001, sum(map(len, blocks)))
            self.assertLessEqual(max(map(len, blocks)), 1024)
            self.assertEqual(5, result["chunks"])
            self.assertEqual(5001, result["bytes_written"])

        def test_controlled_sixel_pattern_has_stable_known_raster(self) -> None:
            payload = controlled_sixel_test_pattern(100, 100)
            self.assertEqual((100, 100), sixel_payload_pixel_size(payload))
            self.assertTrue(payload.startswith(b"\x1bP9;1;0q"))
            self.assertTrue(payload.endswith(b"\x1b\\"))

        def test_v125_calibration_report_format_is_exactly_stable(self) -> None:
            data = {
                "audit_music_batch_version": "v125",
                "measurements": {"reconciled_cell_pixels": None},
            }
            expected = (
                "===== WAVEFORM TERMINAL CALIBRATION REPORT =====\n"
                "{\n"
                '  "audit_music_batch_version": "v125",\n'
                '  "measurements": {\n'
                '    "reconciled_cell_pixels": null\n'
                "  }\n"
                "}\n"
                "===== END WAVEFORM TERMINAL CALIBRATION REPORT ====="
            )
            self.assertEqual(expected, render_waveform_calibration_report(data))

    def unit_test_purpose(test) -> str:
        """Return a readable sentence instead of unittest's nested class ID."""
        method_name = test._testMethodName
        method = getattr(type(test), method_name)
        documented = inspect.getdoc(method)
        if documented:
            return documented.splitlines()[0].rstrip(".") + "."
        words = method_name.removeprefix("test_").replace("_", " ")
        return f"Verify that {words}."

    def short_repr(value: Any, limit: int = 600) -> str:
        """Keep expected/actual values useful without flooding the terminal."""
        rendered = repr(value)
        if len(rendered) <= limit:
            return rendered
        omitted = len(rendered) - limit
        return f"{rendered[:limit]}... <{omitted} more characters>"

    def failed_assertion_details(
        err,
        test,
    ) -> tuple[str, str, str, str]:
        """Interpret the last unittest assertion frame and evaluate its inputs."""
        frames = []
        current = err[2]
        while current is not None:
            frames.append(current)
            current = current.tb_next
        test_frame = next(
            (
                item
                for item in reversed(frames)
                if item.tb_frame.f_code.co_name == test._testMethodName
            ),
            frames[-1] if frames else None,
        )
        if test_frame is None:
            return (
                "(assertion source unavailable)",
                "The test should complete without an exception.",
                f"{err[0].__name__}: {err[1]}",
                "(location unavailable)",
            )
        filename = test_frame.tb_frame.f_code.co_filename
        line_number = test_frame.tb_lineno
        source = linecache.getline(filename, line_number).strip()
        location = f"{filename}:{line_number}"
        if "assert" not in source:
            source = "(assertion source unavailable or file changed during test run)"

        def evaluate(node):
            expression = ast.Expression(node)
            ast.fix_missing_locations(expression)
            return eval(
                compile(expression, filename, "eval"),
                test_frame.tb_frame.f_globals,
                test_frame.tb_frame.f_locals,
            )

        expected = "The assertion should pass."
        actual = f"{err[0].__name__}: {err[1]}"
        if not issubclass(err[0], AssertionError):
            return (
                "(unexpected exception; no assertion produced this failure)",
                "The test should complete without raising an exception.",
                f"{err[0].__name__}: {err[1]}",
                location,
            )
        parsed_source = False
        try:
            if source.startswith("("):
                raise ValueError("No stable assertion source")
            parsed = ast.parse(source)
            call = parsed.body[0].value
            assertion = (
                call.func.attr
                if isinstance(call, ast.Call)
                and isinstance(call.func, ast.Attribute)
                else ""
            )
            arguments = [
                evaluate(argument)
                for argument in getattr(call, "args", [])
            ]
            expression_texts = [
                ast.unparse(argument)
                for argument in getattr(call, "args", [])
            ]
            parsed_source = bool(assertion)
            if assertion == "assertFalse" and arguments:
                expected = (
                    f"{expression_texts[0]} should be false or empty."
                )
                actual = (
                    f"{expression_texts[0]} evaluated to "
                    f"{short_repr(arguments[0])}."
                )
            elif assertion == "assertTrue" and arguments:
                expected = f"{expression_texts[0]} should be true."
                actual = (
                    f"{expression_texts[0]} evaluated to "
                    f"{short_repr(arguments[0])}."
                )
            elif assertion in {"assertEqual", "assertNotEqual"} and len(arguments) >= 2:
                relationship = "equal" if assertion == "assertEqual" else "different"
                expected = (
                    f"{expression_texts[1]} should be {relationship} to "
                    f"{short_repr(arguments[0])}."
                )
                actual = (
                    f"{expression_texts[1]} evaluated to "
                    f"{short_repr(arguments[1])}."
                )
            elif assertion in {"assertIn", "assertNotIn"} and len(arguments) >= 2:
                relationship = "contain" if assertion == "assertIn" else "not contain"
                expected = (
                    f"{expression_texts[1]} should {relationship} "
                    f"{short_repr(arguments[0])}."
                )
                actual = (
                    f"{expression_texts[1]} evaluated to "
                    f"{short_repr(arguments[1])}."
                )
            elif assertion in {"assertIsNone", "assertIsNotNone"} and arguments:
                expected = (
                    f"{expression_texts[0]} should "
                    f"{'not ' if assertion == 'assertIsNotNone' else ''}be None."
                )
                actual = (
                    f"{expression_texts[0]} evaluated to "
                    f"{short_repr(arguments[0])}."
                )
        except Exception:
            # The normal exception text and compact traceback remain below.
            pass

        if not parsed_source:
            message = str(err[1])

            def literal(text: str) -> Any:
                try:
                    return ast.literal_eval(text)
                except Exception:
                    return text

            not_false = re.fullmatch(r"(.+) is not false", message, flags=re.S)
            not_true = re.fullmatch(r"(.+) is not true", message, flags=re.S)
            not_found = re.fullmatch(
                r"(.+) not found in (.+)",
                message,
                flags=re.S,
            )
            unexpectedly_found = re.fullmatch(
                r"(.+) unexpectedly found in (.+)",
                message,
                flags=re.S,
            )
            unequal = re.fullmatch(r"(.+) != (.+)", message, flags=re.S)
            if not_false:
                value = literal(not_false.group(1))
                expected = "The checked value should be false or empty."
                actual = f"The checked value was {short_repr(value)}."
            elif not_true:
                value = literal(not_true.group(1))
                expected = "The checked value should be true."
                actual = f"The checked value was {short_repr(value)}."
            elif not_found:
                member = literal(not_found.group(1))
                container = literal(not_found.group(2))
                expected = (
                    f"The collection should contain {short_repr(member)}."
                )
                actual = (
                    f"The collection was {short_repr(container)}."
                )
            elif unexpectedly_found:
                member = literal(unexpectedly_found.group(1))
                container = literal(unexpectedly_found.group(2))
                expected = (
                    f"The collection should not contain {short_repr(member)}."
                )
                actual = (
                    f"The collection was {short_repr(container)}."
                )
            elif unequal:
                expected_value = literal(unequal.group(1))
                actual_value = literal(unequal.group(2))
                expected = f"Expected value: {short_repr(expected_value)}."
                actual = f"Actual value: {short_repr(actual_value)}."
        return source or "(assertion source unavailable)", expected, actual, location

    class DescriptiveTestResult(unittest.TextTestResult):
        """Explain test intent and assertion values before technical traceback."""

        total_tests = 0
        use_color = True

        def progress_prefix(self) -> str:
            """Render a dynamic, aligned ``[ current/total] ➜`` test prefix."""
            total = max(1, int(self.total_tests))
            current = max(1, int(self.testsRun))
            width = len(str(total))
            current_text = f"{current:>{width}}"
            total_text = str(total)
            if not self.use_color:
                return f"[{current_text}/{total_text}] ➜ "
            bracket_color = "\033[38;2;155;120;255m"
            current_color = "\033[38;2;120;235;255m"
            slash_color = "\033[38;2;90;100;115m"
            total_color = "\033[38;2;145;185;205m"
            arrow_color = "\033[38;2;255;120;205m"
            return (
                f"{bracket_color}[{ANSI['reset']}"
                f"{ANSI['bold']}{current_color}{current_text}{ANSI['reset']}"
                f"{ANSI['faint']}{slash_color}/{ANSI['reset']}"
                f"{ANSI['faint']}{total_color}{total_text}{ANSI['reset']}"
                f"{bracket_color}]{ANSI['reset']} "
                f"{arrow_color}➜{ANSI['reset']} "
            )

        def description_color(self) -> str:
            """Return a subtly varied cyan-blue for the current test name."""
            index = max(1, int(self.testsRun))
            red = 135 + (index * 17) % 24
            green = 205 + (index * 11) % 34
            blue = 232 + (index * 7) % 23
            return f"\033[38;2;{red};{green};{blue}m"

        def getDescription(self, test) -> str:
            description = (
                f"{unit_test_purpose(test)} "
                f"[{test._testMethodName}]"
            )
            if self.use_color:
                description = (
                    f"{self.description_color()}{description}{ANSI['reset']}"
                )
            return f"{self.progress_prefix()}{description}"

        def _exc_info_to_string(self, err, test) -> str:
            source, expected, actual, location = failed_assertion_details(
                err,
                test,
            )
            technical = "".join(
                traceback.format_exception(*err)
            ).rstrip()
            return "\n".join(
                [
                    f"TEST PURPOSE: {unit_test_purpose(test)}",
                    f"FAILED CHECK: {source}",
                    f"EXPECTED: {expected}",
                    f"ACTUAL: {actual}",
                    f"LOCATION: {location}",
                    "",
                    "TECHNICAL TRACEBACK:",
                    technical,
                ]
            )

    class DescriptiveTestRunner(unittest.TextTestRunner):
        """Use the descriptive result while retaining standard test semantics."""

        resultclass = DescriptiveTestResult

        def __init__(
            self,
            *args,
            total_tests: int,
            use_color: bool,
            **kwargs,
        ) -> None:
            super().__init__(*args, **kwargs)
            self.total_tests = total_tests
            self.use_color = use_color

        def _makeResult(self):
            result = super()._makeResult()
            result.total_tests = self.total_tests
            result.use_color = self.use_color
            return result

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(GeneratedAudioTests)
    original_single_key_reader = read_single_key
    original_text_reader = builtins.input

    def reject_live_unit_test_input(*_args, **_kwargs):
        raise AssertionError(
            "--unit-tests attempted to read live STDIN. Pass a simulated "
            "key_reader/input_reader in that test."
        )

    read_single_key = reject_live_unit_test_input
    builtins.input = reject_live_unit_test_input
    try:
        result = DescriptiveTestRunner(
            verbosity=2,
            stream=sys.stdout,
            buffer=True,
            total_tests=suite.countTestCases(),
            use_color=use_color,
        ).run(suite)
    finally:
        read_single_key = original_single_key_reader
        builtins.input = original_text_reader
    return 0 if result.wasSuccessful() else 1


def render_markdown(data: dict[str, Any], max_examples: int) -> str:
    counts = data["counts"]
    lines = [
        "# Music Batch Audit",
        "",
        f"- Root: `{data['root']}`",
        f"- Active audio: `{counts['active_audio']}`",
        f"- Files: `{counts['files']}`",
        f"- Mutagen available: `{data['mutagen_available']}`",
        f"- Pillow available: `{data['pillow_available']}`",
    ]
    embedded = data.get("embedded_lyrics", [])
    if embedded:
        refresh_mode = data.get("embedded_lyrics_mode") == "refresh"
        heading = (
            "## Lyrics/Karaoke Refreshed by "
            "`--refresh-embedded-lyrics`"
            if refresh_mode
            else "## Lyrics/Karaoke Embedded by `--embed-lyrics`"
        )
        verb = "refreshed" if refresh_mode else "embedded"
        lines.extend(["", heading, ""])
        for item in embedded:
            changed = [
                humanized_action(str(action))
                for action in item.get("actions", [])
                if not str(action).startswith("backup:")
            ]
            description = ", ".join(changed) or "available lyrics"
            lines.append(
                f"- `{md_escape(str(item['path']))}` — {verb} {description}; "
                "re-audited in this pass."
            )
            for action in item.get("actions", []):
                if str(action).startswith("backup:"):
                    backup = str(action).removeprefix("backup:")
                    lines.append(f"  - Backup: `{md_escape(backup)}`")
    cover_results = data.get("found_cover_art", [])
    if cover_results:
        lines.extend(["", "## Artwork Handled by `--find-cover`", ""])
        for result in cover_results:
            status = (
                f"failed: {result['error']}"
                if result.get("error")
                else "applied and re-audited"
            )
            lines.append(
                f"- {len(result.get('paths', []))} audio file(s): {md_escape(status)}"
            )
            for path in result.get("paths", []):
                lines.append(f"  - `{md_escape(path)}`")
            for action in result.get("actions", []):
                if str(action).startswith("saved_art:"):
                    lines.append(
                        f"  - Saved artwork: "
                        f"`{md_escape(str(action).removeprefix('saved_art:'))}`"
                    )
    lines.extend(
        [
            "",
            "## Severity Counts",
            "",
            "| Severity | Count |",
            "|---|---:|",
        ]
    )
    for key in ("problem", "safe_fix", "safe_cleanup", "ask_first", "never_default", "info"):
        lines.append(f"| `{key}` | {counts['by_severity'].get(key, 0)} |")
    lines.extend(["", "## Proposal Codes", "", "| Code | Severity | Category | Path | Finding | Suggestion |", "|---|---|---|---|---|---|"])
    coded = [f for f in data["findings"] if f.get("code")]
    for finding in coded[: max_examples or None]:
        lines.append(
            "| `{}` | `{}` | `{}` | `{}` | {} | {} |".format(
                finding["code"],
                finding["severity"],
                finding["category"],
                md_escape(finding["path"]),
                md_escape(finding["message"]),
                md_escape(finding.get("suggestion", "")),
            )
        )
    if max_examples and len(coded) > max_examples:
        lines.append(f"|  |  |  |  | {len(coded) - max_examples} more omitted |  |")
    lines.extend(["", "## Never Default", "", "| Category | Path | Finding |", "|---|---|---|"])
    never = [f for f in data["findings"] if f["severity"] == "never_default"]
    for finding in never[: max_examples or None]:
        lines.append(f"| `{finding['category']}` | `{md_escape(finding['path'])}` | {md_escape(finding['message'])} |")
    return "\n".join(lines) + "\n"


def md_escape(text: str) -> str:
    return str(text).replace("|", "\\|")


def write_reports(data: dict[str, Any], output_dir: Path, max_examples: int) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "audit_music_batch_report.json"
    md_path = output_dir / "audit_music_batch_report.md"
    txt_path = output_dir / "audit_music_batch_report.txt"
    for report_path in (json_path, md_path, txt_path):
        if report_path.exists():
            backup_before_inline_replacement(report_path)
    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(render_markdown(data, max_examples=0), encoding="utf-8")
    txt_path.write_text(render_text(data, max_examples=0), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path), "text": str(txt_path)}


class AuditArgumentParser(argparse.ArgumentParser):
    """Give argparse failures the same visible error treatment as runtime failures."""

    def __init__(self, *args, error_color: bool = True, **kwargs) -> None:
        self.error_color = error_color
        super().__init__(*args, **kwargs)

    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        self.exit(
            2,
            console_safe_text(
                formatted_error(message, self.error_color) + "\n",
                sys.stderr,
            ),
        )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = AuditArgumentParser(
        description="Audit incoming music batches; interactive approvals apply supported actions immediately.",
        add_help=False,
        error_color="--no-color" not in argv,
    )
    parser.add_argument("root", nargs="?", default=None, help="Batch root to audit; use . for the current folder.")
    parser.add_argument("-h", "--help", action="store_true", help="Show the styled usage screen and exit.")
    parser.add_argument("--version", action="store_true", help="Show the named published release version and exit.")
    parser.add_argument("--include-archives", action="store_true", help="Include archived/deprecated audio in active tag checks.")
    parser.add_argument("--format", choices=("text", "json", "markdown"), default="text", help="Report format for stdout.")
    parser.add_argument("--write-reports", action="store_true", help="Write JSON, Markdown, and text reports.")
    parser.add_argument("--output-dir", type=Path, default=None, help="Report directory. Defaults to the audited root.")
    parser.add_argument("--max-examples", type=int, default=80, help="Max examples printed to stdout; 0 means all.")
    parser.add_argument(
        "--interactive",
        dest="interactive",
        action="store_true",
        default=True,
        help="Prompt through executable findings and apply approved actions immediately; this is the default.",
    )
    parser.add_argument(
        "--no-interactive",
        dest="interactive",
        action="store_false",
        help="Strictly read-only report mode; do not prompt or apply actions.",
    )
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI color in interactive prompts.")
    parser.add_argument(
        "--no-pager",
        action="store_true",
        help="Disable automatic More-style paging in an interactive console.",
    )
    parser.add_argument(
        "--unit-tests",
        action="store_true",
        help="Run self-contained generated-audio tests and exit without auditing or modifying a music folder.",
    )
    parser.add_argument(
        "--calibrate-waveform-terminal",
        nargs="?",
        const=".",
        default=None,
        metavar="AUDIO_OR_WAVEFORM",
        help=(
            "Run a controlled Windows-terminal waveform calibration instead of an audit. "
            "Give an audio file, waveform image, or folder; default is the current folder."
        ),
    )
    waveform_behavior = parser.add_mutually_exclusive_group()
    waveform_behavior.add_argument(
        "--review-waveforms",
        action="store_true",
        help=(
            "Diagnose per-track waveforms interactively; defaults to the "
            "current folder when no root is supplied."
        ),
    )
    waveform_behavior.add_argument(
        "--no-review-waveforms",
        "--no-waveform-review",
        dest="no_review_waveforms",
        action="store_true",
        help=(
            "Suppress the default-Yes offer to begin waveform review after "
            "a normal interactive audit."
        ),
    )
    parser.add_argument(
        "--waveform-workers",
        type=int,
        default=8,
        metavar="NUMBER",
        help="Background waveform render workers (1-8; default 8).",
    )
    lyric_behavior = parser.add_mutually_exclusive_group()
    lyric_behavior.add_argument(
        "--embed-lyrics",
        dest="embed_lyrics",
        action="store_true",
        default=None,
        help="Force automatic embedding of validated plain/timed lyric sidecars for this run.",
    )
    lyric_behavior.add_argument(
        "--no-embed-lyrics",
        dest="embed_lyrics",
        action="store_false",
        help="Suppress automatic lyric/karaoke embedding for this run.",
    )
    lyric_behavior.add_argument(
        "--refresh-embedded-lyrics",
        action="store_true",
        help=(
            "Force-refresh both plain lyrics and timed karaoke from every "
            "available validated sidecar, then re-audit."
        ),
    )
    cover_behavior = parser.add_mutually_exclusive_group()
    cover_behavior.add_argument(
        "--find-cover",
        dest="find_cover",
        action="store_true",
        default=None,
        help=(
            "Force finding release artwork for missing covers, review every supplied "
            "image part, embed only approved Front, and re-audit."
        ),
    )
    cover_behavior.add_argument(
        "--no-find-cover",
        dest="find_cover",
        action="store_false",
        help="Suppress automatic missing-cover lookup for this run.",
    )
    silence_behavior = parser.add_mutually_exclusive_group()
    silence_behavior.add_argument(
        "--check-silence",
        dest="check_silence",
        action="store_true",
        default=None,
        help="Force excessive-silence analysis for this run.",
    )
    silence_behavior.add_argument(
        "--no-silence-check",
        dest="check_silence",
        action="store_false",
        help="Suppress excessive-silence analysis for this run.",
    )
    parser.add_argument(
        "--silence-threshold",
        type=float,
        default=None,
        metavar="SECONDS",
        help="Flag silence strictly longer than this many seconds.",
    )
    parser.add_argument(
        "--configure-defaults",
        action="store_true",
        help="Interactively configure persistent automatic behavior defaults.",
    )
    parser.add_argument(
        "--show-defaults",
        action="store_true",
        help="Show effective automatic behavior defaults and their config source.",
    )
    return parser.parse_args(argv)


def announce_release(use_color: bool) -> None:
    """Always announce the published version and date before other work."""
    text = (
        f"🎵 audit_music_batch.py {AUDIT_MUSIC_BATCH_VERSION} — "
        f"{AUDIT_MUSIC_BATCH_RELEASE_DATE}"
    )
    if use_color:
        text = gradient_text(
            text,
            True,
            ((120, 235, 255), (255, 220, 80)),
        )
    print(console_safe_text(text, sys.stderr), file=sys.stderr, flush=True)


def music_exists_within_depth(
    root: Path,
    max_depth: int = NO_ARGUMENT_MUSIC_SCAN_MAX_DEPTH,
) -> bool:
    """Return quickly when music exists from root through max_depth children.

    Directory junctions/reparse points are followed because Soulseek trees are
    often reached through a junction.  Resolved directories are de-duplicated
    so a junction loop cannot make this bounded startup probe recurse forever.
    """
    start = root.resolve()
    depth_limit = max(0, int(max_depth))
    stack: list[tuple[Path, int]] = [(start, 0)]
    visited: set[str] = set()
    while stack:
        folder, depth = stack.pop()
        try:
            resolved = folder.resolve()
        except OSError:
            resolved = folder.absolute()
        key = os.path.normcase(str(resolved))
        if key in visited:
            continue
        visited.add(key)
        try:
            with os.scandir(folder) as entries:
                for entry in entries:
                    try:
                        # Follow reparse points/junctions here.  This is a shallow,
                        # depth-bounded existence probe, and visited prevents loops.
                        if entry.is_file(follow_symlinks=True):
                            if Path(entry.name).suffix.casefold() in KNOWN_AUDIO_EXTS:
                                return True
                        elif depth < depth_limit and entry.is_dir(follow_symlinks=True):
                            stack.append((Path(entry.path), depth + 1))
                    except OSError:
                        continue
        except OSError:
            continue
    return False


def prompt_no_argument_menu(
    *,
    use_color: bool,
    key_reader=None,
) -> str:
    """Choose current-folder audit or usage when no command-line args exist."""
    print()
    print(
        rgb_text(
            f"Music was found in the current folder (or within {NO_ARGUMENT_MUSIC_SCAN_MAX_DEPTH} subfolder levels):",
            255,
            220,
            85,
            use_color,
        )
    )
    print("1) Run audit in this folder")
    print("2) Display usage instructions")
    reader = key_reader or read_single_key
    while True:
        print("❓ Choice [1/2]: ", end="", flush=True)
        key = reader()
        if key == "\x03":
            print()
            raise KeyboardInterrupt
        if key in {"1", "2"}:
            print(key)
            reset_console_pager_after_user_input()
            return key
        invalid_key_beep()


def _main(argv: list[str] | None = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    use_color = "--no-color" not in raw_argv
    announce_release(use_color=use_color)
    if not raw_argv:
        current = Path.cwd()
        if music_exists_within_depth(current, NO_ARGUMENT_MUSIC_SCAN_MAX_DEPTH):
            # On Windows/TCC, sys.stdin.isatty() can be false even though
            # msvcrt.getwch() is fully interactive.  Do not use isatty() to
            # suppress the menu on Windows; retain nonblocking redirected-input
            # behavior on POSIX.
            can_prompt = os.name == "nt" or bool(
                getattr(sys.stdin, "isatty", lambda: False)()
            )
            if not can_prompt:
                print_usage(use_color=use_color)
                return 0
            try:
                choice = prompt_no_argument_menu(use_color=use_color)
            except EOFError:
                choice = "2"
            if choice == "1":
                raw_argv = ["."]
            else:
                print_usage(use_color=use_color)
                return 0
        else:
            print_usage(use_color=use_color)
            return 0
    args = parse_args(raw_argv)
    if args.help:
        print_usage(use_color=not args.no_color)
        return 0
    if args.version:
        print(
            f"audit_music_batch.py {AUDIT_MUSIC_BATCH_VERSION} "
            f"({AUDIT_MUSIC_BATCH_RELEASE_NAME}) — {AUDIT_MUSIC_BATCH_RELEASE_DATE}"
        )
        return 0
    if args.calibrate_waveform_terminal is not None:
        if not args.interactive:
            print_formatted_error(
                "--calibrate-waveform-terminal is interactive and cannot be combined with --no-interactive.",
                not args.no_color,
            )
            return 2
        try:
            return run_waveform_terminal_calibration(
                Path(args.calibrate_waveform_terminal),
                use_color=not args.no_color,
            )
        except Exception as exc:
            print_formatted_error(
                f"Waveform terminal calibration failed: {type(exc).__name__}: {exc}",
                not args.no_color,
            )
            return 2
    if args.review_waveforms and args.root is None:
        args.root = "."
    if args.configure_defaults:
        try:
            configured, config_path, backup = configure_behavior_defaults(
                use_color=not args.no_color,
            )
        except Exception as exc:
            print_formatted_error(
                f"{type(exc).__name__}: {exc}",
                not args.no_color,
            )
            return 2
        print()
        print(f"        ⚙️ Defaults saved: {config_path}")
        print(
            "        🎤 Automatic lyric/karaoke embedding: "
            + ("Yes" if configured.embed_lyrics else "No")
        )
        print(
            "        🎨 Automatic missing-cover lookup: "
            + ("Yes" if configured.find_cover else "No")
        )
        print(
            "        🔇 Automatic excessive-silence analysis: "
            + ("Yes" if configured.check_silence else "No")
        )
        print(
            "        ⏱️ Excessive-silence threshold: "
            f"{configured.silence_threshold_seconds:g} seconds"
        )
        if backup is not None:
            print(f"        💾 Previous config backup kept: {backup}")
        return 0
    if args.unit_tests:
        if not run_dependency_preflight(
            unit_tests=True,
            find_cover=False,
            interactive=args.interactive,
            use_color=not args.no_color,
        ):
            print(
                colorize(
                    "        🚫 Unit tests cancelled before creating any fixtures.",
                    "yellow",
                    not args.no_color,
                )
            )
            return 3
        return run_unit_tests(use_color=not args.no_color)
    if not 1 <= args.waveform_workers <= 8:
        print_formatted_error(
            "--waveform-workers must be between 1 and 8.",
            not args.no_color,
        )
        return 2
    if args.review_waveforms:
        if not args.interactive:
            print_formatted_error(
                "--review-waveforms is an interactive preview workflow "
                "and cannot be combined with --no-interactive.",
                not args.no_color,
            )
            return 2
        if shutil.which("ffmpeg") is None:
            print_formatted_error(
                "--review-waveforms requires ffmpeg in PATH.",
                not args.no_color,
            )
            return 3
        try:
            waveform_results = review_waveforms(
                Path(args.root),
                include_archives=args.include_archives,
                use_color=not args.no_color,
                interactive=True,
                workers=args.waveform_workers,
                silence_threshold_seconds=args.silence_threshold,
            )
        except Exception as exc:
            print_formatted_error(
                f"{type(exc).__name__}: {exc}",
                not args.no_color,
            )
            return 2
        return 1 if waveform_results["failed"] else 0
    try:
        defaults = load_behavior_defaults()
    except Exception as exc:
        print_formatted_error(
            f"{type(exc).__name__}: {exc}",
            not args.no_color,
        )
        return 2
    if (
        args.silence_threshold is not None
        and not 0.1 <= args.silence_threshold <= 3600.0
    ):
        print_formatted_error(
            "--silence-threshold must be from 0.1 through 3600 seconds.",
            not args.no_color,
        )
        return 2
    effective = effective_behavior_flags(args, defaults)
    if args.show_defaults:
        config = behavior_config_path()
        source = str(config) if config.is_file() else "built-in defaults"
        print(f"Configuration source: {source}")
        print(
            "Automatic lyric/karaoke embedding: "
            + ("Yes" if effective.embed_lyrics else "No")
        )
        print(
            "Automatic missing-cover lookup: "
            + ("Yes" if effective.find_cover else "No")
        )
        print(
            "Automatic excessive-silence analysis: "
            + ("Yes" if effective.check_silence else "No")
        )
        print(
            "Excessive-silence threshold: "
            f"{effective.silence_threshold_seconds:g} seconds"
        )
        return 0
    if args.root is None:
        print_usage(use_color=not args.no_color)
        print_formatted_error(
            "Name a folder to audit, or use . for the current folder.",
            not args.no_color,
        )
        return 2
    if not run_dependency_preflight(
        unit_tests=False,
        find_cover=effective.find_cover and args.interactive,
        check_silence=effective.check_silence,
        interactive=args.interactive,
        use_color=not args.no_color,
    ):
        print(
            colorize(
                "        🚫 Audit cancelled before scanning any music files.",
                "yellow",
                not args.no_color,
            )
        )
        return 3
    audit = BatchAudit(
        Path(args.root),
        include_archives=args.include_archives,
        check_silence=effective.check_silence,
        silence_threshold_seconds=effective.silence_threshold_seconds,
    )
    data = audit.audit(
        embed_lyrics_first=effective.embed_lyrics,
        refresh_embedded_lyrics=args.refresh_embedded_lyrics,
    )
    if args.interactive:
        baked_paths = bake_replaygain_for_batch(
            audit.audio_files,
            use_color=not args.no_color,
            acceptable_silence_seconds=(
                effective.silence_threshold_seconds
            ),
        )
        if baked_paths:
            data = audit.audit(
                embed_lyrics_first=effective.embed_lyrics,
                refresh_embedded_lyrics=args.refresh_embedded_lyrics,
            )
            data["baked_replaygain"] = [
                str(path) for path in baked_paths
            ]
    if effective.find_cover and args.interactive:
        original_embedded_lyrics = data.get("embedded_lyrics")
        original_embedded_lyrics_mode = data.get("embedded_lyrics_mode")
        cover_results, refreshed = find_covers_for_batch(
            Path(args.root),
            data,
            interactive=args.interactive,
            use_color=not args.no_color,
        )
        data = refreshed
        if original_embedded_lyrics is not None:
            data["embedded_lyrics"] = original_embedded_lyrics
            data["embedded_lyrics_mode"] = original_embedded_lyrics_mode
        data["found_cover_art"] = cover_results
    elif effective.find_cover:
        print(
            colorize(
                "        ⚠️ Automatic cover lookup was skipped because "
                "--no-interactive cannot review downloaded images; use "
                "--no-find-cover to suppress this notice.",
                "yellow",
                not args.no_color,
            )
        )

    output_dir = args.output_dir or Path(args.root)
    if args.write_reports:
        data["written_reports"] = write_reports(data, output_dir, args.max_examples)

    if args.format == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False))
    elif args.format == "markdown":
        print(render_markdown(data, args.max_examples), end="")
    else:
        print(
            console_safe_text(
                render_console_report(
                    data,
                    args.max_examples,
                    use_color=not args.no_color,
                    interactive=args.interactive,
                )
            ),
            end="",
        )
        if args.write_reports:
            print("Reports written:")
            for kind, path in data["written_reports"].items():
                print(f"  {kind}: {path}")
    waveform_handoff_failed = False
    if args.interactive:
        result = interactive_apply(data, use_color=not args.no_color)
        print_interactive_results(result, not args.no_color)
        try:
            waveform_handoff = offer_post_audit_waveform_review(
                Path(args.root),
                interactive=True,
                suppressed=args.no_review_waveforms,
                include_archives=args.include_archives,
                use_color=not args.no_color,
                workers=args.waveform_workers,
                silence_threshold_seconds=(
                    effective.silence_threshold_seconds
                ),
            )
            waveform_handoff_failed = bool(
                waveform_handoff
                and waveform_handoff.get("failed")
            )
            if waveform_handoff is not None:
                print_interactive_results(result, not args.no_color)
        except Exception as exc:
            waveform_handoff_failed = True
            print_formatted_error(
                f"Could not start the post-audit waveform review: "
                f"{type(exc).__name__}: {exc}",
                not args.no_color,
            )
    return (
        1
        if (
            data["counts"]["by_severity"].get("problem", 0)
            or waveform_handoff_failed
        )
        else 0
    )


def console_paging_enabled(raw_argv: list[str]) -> bool:
    """Disable paging for unit tests and explicit non-paged invocations."""
    return (
        "--no-pager" not in raw_argv
        and "--unit-tests" not in raw_argv
    )


def main(argv: list[str] | None = None) -> int:
    """Run with automatic paging unless explicitly disabled or redirected."""
    raw_argv = sys.argv[1:] if argv is None else argv
    with paged_console_output(console_paging_enabled(raw_argv)):
        return _main(raw_argv)


if __name__ == "__main__":
    raise SystemExit(main())
