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
import hashlib
import io
import json
import os
import random
import re
import shutil
import ssl
import stat
import subprocess
import sys
import tempfile
import textwrap
import time
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from collections import Counter, defaultdict
from contextlib import ExitStack, contextmanager, nullcontext
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, NoReturn

# USER CONFIGURATION ---------------------------------------------------------
# Set this to a full executable path only when automatic discovery cannot find
# your preferred image viewer. The V key first honors openimage.bat, then this
# value, then IrfanView found on PATH or in established portable paths.
IMAGE_VIEWER_EXECUTABLE: str | None = None

# Set this to a full executable path only when waveform review cannot discover
# Adobe Audition, Cool Edit, Sound Forge, Audacity, or another audio editor.
AUDIO_EDITOR_EXECUTABLE: str | None = None

# Artwork previews consume the terminal while retaining these rows for status,
# the approval prompt, and a possible IrfanView-open message.
ART_PREVIEW_RESERVED_TEXT_ROWS = 7
ART_PREVIEW_INDENT_COLUMNS = 12
ART_PREVIEW_RIGHT_MARGIN_COLUMNS = 2

# Built-in behavior defaults apply when no adjacent configuration file exists.
# Use --configure-defaults to create/update that file interactively.
BEHAVIOR_CONFIG_FILENAME = "audit_music_batch.config.json"
BUILTIN_DEFAULT_EMBED_LYRICS = True
BUILTIN_DEFAULT_FIND_COVER = False
BUILTIN_DEFAULT_CHECK_SILENCE = True
BUILTIN_DEFAULT_SILENCE_THRESHOLD_SECONDS = 10.0
SILENCE_DETECT_NOISE_DB = -50

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
DISCOGS_API_ROOT = "https://api.discogs.com"
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
    "bare_marker",
    "embedded_art_without_sidecar",
    "embedded_lyrics_outdated",
    "karaoke_not_embedded",
    "missing_embedded_art",
    "missing_replaygain",
    "missing_album",
    "multiple_embedded_artworks",
    "plain_lyrics_not_embedded",
    "read_only_audio",
    "redundant_album_artist_filename_group",
    "filename_title_capitalization_group",
    "filename_marker_style",
    "smaller_numbered_image_duplicate",
    "stale_transcription_marker",
    "tagrename_m3u8",
    "temporary_batch_file",
    "vad_scratch_srt",
}
GROUPED_RENAME_CATEGORIES = {
    "redundant_album_artist_filename_group",
    "filename_title_capitalization_group",
}
ACTION_PROMPT_QUESTIONS = {
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
    "karaoke_not_embedded": (
        "Embed the timed karaoke lyrics into this audio file now?"
    ),
    "missing_embedded_art": (
        "Use the available sidecar—or search for a verified release artwork "
        "set—and embed only its Front image now?"
    ),
    "missing_replaygain": (
        "Run the full ARGT ReplayGain workflow for this folder now?"
    ),
    "multiple_embedded_artworks": (
        "Export all artwork to sidecars and keep only the front cover embedded now?"
    ),
    "plain_lyrics_not_embedded": (
        "Embed the plain lyrics into this audio file now?"
    ),
    "read_only_audio": "Clear this audio file's read-only attribute now?",
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
}
PROMPT_NOUN_PHRASES = (
    "regenerated sidecar files",
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
    "italic": "\033[3m",
    "blink": "\033[5m",
    "erase_line": "\033[2K",
    "erase_to_eol": "\033[K",
}
ANSI_DOUBLE_HEIGHT_TOP = "\033#3"
ANSI_DOUBLE_HEIGHT_BOTTOM = "\033#4"

# Calibrated 2026-07-30 against 396 real batch files:
# median 0.5601054 seconds = 707.0098 files/second. The display threshold is
# deliberately rounded down to 600 so the bar appears before a one-second wait.
AUDIT_FILES_PER_SECOND = 707.0097878191683
PROGRESS_WAIT_SECONDS = 1.0
PROGRESS_FIRST_FILE_COUNT = 600
ENUMERATION_PROGRESS_FORMAT = (
    "{desc}: {n:,.0f} files found"
    " • {elapsed} elapsed • {rate_fmt}"
)
AUDIT_PROGRESS_FORMAT = (
    "{desc}: {percentage:3.0f}%|{bar}| "
    "{n:,.0f}/{total:,.0f} checks"
    " • {elapsed} elapsed • {rate_fmt}{postfix}"
)


def should_show_audit_progress(file_count: int) -> bool:
    """Show progress at the deliberately early 600-file threshold."""
    return file_count >= PROGRESS_FIRST_FILE_COUNT


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
    if send2trash is None:
        raise RuntimeError(
            "send2trash is unavailable; refusing permanent deletion"
        )
    if not path.exists():
        raise FileNotFoundError(f"Cannot recycle missing path: {path}")
    send2trash(str(path))
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


def apply_argt_replaygain_folder(
    folder: Path,
    *,
    use_color: bool,
    stream_output: bool = True,
) -> list[str]:
    """Reproduce ARGT's MP3-first, then per-FLAC ReplayGain workflow."""
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
    try:
        if mp3_files:
            metamp3 = require_replaygain_program("metamp3")
            print(
                console_safe_text(
                    "        🔢 Adding ReplayGain tags to MP3 files..."
                ),
                flush=True,
            )
            for path in mp3_files:
                backup = backup_before_inline_replacement(path)
                actions.append(f"backup:{backup}")

            sequester = collision_safe_path(folder / "ohhhh")
            sequester.mkdir()
            staged_paths: list[Path] = []
            try:
                for path in mp3_files:
                    staged = sequester / path.name
                    shutil.move(str(path), str(staged))
                    staged_paths.append(staged)
                    print(
                        console_safe_text(f"            ☑️ {path.name}"),
                        flush=True,
                    )
                emit_argt_random_color(
                    foreground_only=True, use_color=use_color
                )
                run_live_command(
                    [metamp3, "--replay-gain", "*.*"],
                    cwd=sequester,
                    stream_output=stream_output,
                )
            finally:
                restored = move_sequestered_files_back(sequester, folder)
                if sequester.exists() and not any(sequester.iterdir()):
                    recycle_path(sequester)
                    actions.append(f"recycled:{sequester}")
            for path in restored:
                actions.append(f"replaygain:{path}")
        else:
            print(
                console_safe_text("        🚫 No MP3s exist here."),
                flush=True,
            )

        if flac_files:
            metaflac = require_replaygain_program("metaflac")
            print(
                console_safe_text(
                    "        🔢 Adding ReplayGain tags to FLAC files..."
                ),
                flush=True,
            )
            for path in flac_files:
                emit_argt_random_color(
                    foreground_only=False, use_color=use_color
                )
                print(
                    console_safe_text(f"            ☑️ {path.name}"),
                    flush=True,
                )
                backup = backup_before_inline_replacement(path)
                actions.append(f"backup:{backup}")
                run_live_command(
                    [metaflac, "--add-replay-gain", str(path)],
                    cwd=folder,
                    stream_output=stream_output,
                )
                actions.append(f"replaygain:{path}")
        else:
            print(
                console_safe_text("        🚫 No FLACs exist here."),
                flush=True,
            )
    finally:
        if use_color:
            # Both original ARGT child BATs end in "bright red on black".
            print("\033[91;40m", end="", flush=True)
    return actions


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
    from mutagen.id3 import APIC, ID3, SYLT, TALB, TXXX, USLT
    from mutagen.mp3 import MP3
except Exception:  # pragma: no cover - exercised when mutagen is absent.
    mutagen_file = None
    FLAC = Picture = APIC = ID3 = SYLT = TALB = TXXX = USLT = MP3 = None


try:
    from PIL import Image
except Exception:  # pragma: no cover - optional dependency.
    Image = None


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
            "send2trash",
            detected("send2trash", send2trash is not None),
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
    if not re.match(r"^\s*(?:19|20)\d{2}\b", folder.name):
        return None
    artist = folder.parent.name.strip()
    if (
        not artist
        or artist.lower() in GENERIC_ARTIST_FOLDER_NAMES
        or len(re.sub(r"[^A-Za-z0-9]", "", artist)) < 3
    ):
        return None
    return artist


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


def canonical_song_title_text(text: str) -> str:
    """Normalize separators/feat and capitalize ordinary filename title words."""
    normalized = re.sub(r"_+", " ", str(text))
    normalized = re.sub(r"\bfeat\.(?=\s|\))", "feat", normalized, flags=re.I)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    normalized = re.sub(r"\(\s+", "(", normalized)
    normalized = re.sub(r"\s+\)", ")", normalized)
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


def capitalized_album_filename_proposal(
    filename: str,
    album_track_count: int,
) -> str | None:
    """Normalize track prefix, title spaces/case, and matching backup tails."""
    path = Path(filename)
    if path.suffix.casefold() not in CANONICAL_RENAME_EXTS:
        return None
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
    title_source, suffix = rename_title_and_suffix(
        path,
        match.group("rest"),
    )
    title = canonical_song_title_text(title_source)
    proposed = f"{track}_{title}{suffix}"
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

    def progress_update(self) -> None:
        if self.progress is not None:
            self.progress.update(1)

    def progress_show_audio(self, path: Path) -> None:
        """Refresh immediately with the audio file currently being opened."""
        if self.progress is not None:
            relative = self.rel(path)
            if len(relative) > 72:
                relative = "…" + relative[-71:]
            self.progress.set_postfix_str(relative, refresh=True)

    def progress_phase(self, description: str) -> None:
        """Show a new audit phase immediately without changing progress."""
        if self.progress is not None:
            self.progress.set_description(description, refresh=True)

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
        self, on_file: Callable[[int], None] | None = None
    ) -> None:
        if not self.root.exists():
            raise SystemExit(f"Batch root does not exist: {self.root}")
        discovered: list[Path] = []
        for path in self.root.rglob("*"):
            if path.is_file():
                discovered.append(path)
                if on_file is not None:
                    on_file(len(discovered))
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
            suffix = path.suffix.lower()
            name_lower = path.name.lower()
            size = path.stat().st_size
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

            if suffix in AUDIO_EXTS and is_windows_read_only(path) and not archived:
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
                self.add("ask_first", "wav_remaining", path, "WAV remains in active batch.", "Convert/deprecate/archive after confirming no edit-stage reason remains.")

            if "todo" in name_lower and path.name.lower() != "completed-todos.log" and not archived:
                self.add("problem", "active_todo_filename", path, "Active TODO remains in filename.", "Resolve the TODO, then remove it from active filenames and log it.")
            if re.search(r"[;%^]", path.name):
                self.add("ask_first", "forbidden_filename_char", path, "Filename contains one of ; % ^.", "Rename using the preferred safe equivalent.")
            if re.search(r"(?:Â|Ã|â€|�)", path.name):
                self.add("ask_first", "mojibake_filename", path, "Filename looks mojibaked.", "Review and rename if needed.")

            if suffix in IMAGE_EXTS and re.search(r" \([0-9]+\)$", path.stem):
                base_stem = re.sub(r" \([0-9]+\)$", "", path.stem)
                sibling = path.with_name(base_stem + path.suffix)
                if sibling.exists() and path.stat().st_size <= sibling.stat().st_size:
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
            track_numbers = {
                int(match.group("track"))
                for path in files
                if path.suffix.lower() in AUDIO_EXTS
                and (
                    match := re.match(
                        r"^(?P<track>\d{1,3})[-_. ]+",
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
                if proposed_name is None:
                    continue
                before = self.rel(path)
                after = self.rel(path.with_name(proposed_name))
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
                    f'Artist name "{artist}" is repeated after the track number '
                    f"in {len(renames)} album filenames.",
                    "Approve one grouped rename for the audio and matching "
                    "sidecars/backups; local playlist references will be "
                    "backed up and updated.",
                    artist=artist,
                    renames=renames,
                    audio_count=len(audio_renames),
                    track_count=album_track_count,
                    playlists=playlists,
                )

            case_renames: list[dict[str, str]] = []
            case_audio_renames: list[tuple[Path, str]] = []
            for path in sorted(files, key=lambda item: item.name.lower()):
                if self.rel(path) in redundant_before:
                    continue
                # Do not reinterpret a lone artist-prefixed title as ordinary
                # title text; the repeated pattern is the safety signal.
                if redundant_artist_filename_proposal(
                    path.name,
                    artist,
                    album_track_count,
                ) is not None:
                    continue
                proposed_name = capitalized_album_filename_proposal(
                    path.name,
                    album_track_count,
                )
                if proposed_name is None:
                    continue
                case_renames.append(
                    {
                        "before": self.rel(path),
                        "after": self.rel(path.with_name(proposed_name)),
                    }
                )
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

        for path in self.audio_files:
            self.progress_show_audio(path)
            snapshot = self.tag_snapshot(path)
            if "error" in snapshot:
                self.add("problem", "unreadable_audio", path, f"Could not read tags/audio: {snapshot['error']}", "Open/check/repair file.")
                self.progress_update()
                continue

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
                joined = " / ".join(genres).lower()
                if "punk" in joined and joined != "punk":
                    self.add("safe_fix", "simplify_punk_genre", path, f"Punk-family genre is {genres}.", "Collapse punk-family genre to Punk.")

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

            if not self.has_track_replaygain(path, snapshot):
                self.add(
                    "safe_fix",
                    "missing_replaygain",
                    path,
                    "Missing or invalid ReplayGain track gain/peak.",
                    "Approve the Y/n prompt to run the full ARGT-equivalent folder workflow: sequester all MP3s and run metamp3 first, then run metaflac on each FLAC, stream all output, and re-audit.",
                    channels=channels,
                )

            image_sidecars = self.folder_art_candidates(path.parent)
            if int(snapshot.get("art_count") or 0) == 0:
                severity = "safe_fix" if image_sidecars else "ask_first"
                suggestion = (
                    "Embed existing sidecar artwork."
                    if image_sidecars
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
                    sidecars=[self.rel(p) for p in image_sidecars],
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
            elif not image_sidecars and path.suffix.lower() == ".flac":
                self.add("ask_first", "embedded_art_without_sidecar", path, "FLAC has embedded art but no obvious sidecar art.", "For albums, extract cover.jpg; for MISC/loose FLACs, consider a track-specific JPG sidecar.")

            lyrics = snapshot.get("lyrics", {})
            has_unsynced = int(lyrics.get("unsynced") or 0) > 0
            has_synced = int(lyrics.get("synced") or 0) > 0 or int(lyrics.get("compat_synced") or 0) > 0
            lrc = self.sidecar(path, ".lrc")
            txt = self.sidecar(path, ".txt")
            srt = self.sidecar(path, ".srt")
            if not self.is_instrumental_or_no_lyrics(path):
                if lrc and txt and not srt:
                    if self.lrc_is_timestamped(lrc):
                        self.add(
                            "safe_fix",
                            "missing_srt_from_lrc_txt",
                            path,
                            "LRC and TXT sidecars exist, but the matching SRT sidecar is missing.",
                            "Before the audit pass, run lrc2srt.py MiniLyricsFix --recursive --automatic-overwrites from the batch root.",
                        )
                    else:
                        self.add(
                            "ask_first",
                            "lrc_txt_missing_srt_but_lrc_untimed",
                            path,
                            "LRC and TXT sidecars exist, but SRT is missing and the LRC does not look timestamped.",
                            "Review the LRC before trying to create an SRT.",
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

    def audit_excessive_silence(self) -> None:
        """Report decoded silence intervals strictly longer than the threshold."""
        if not self.check_silence:
            return
        if shutil.which("ffmpeg") is None:
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
        for path in self.audio_files:
            self.progress_show_audio(path)
            try:
                intervals = detect_silence_intervals(path, threshold)
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
                        "Run --review-waveforms to inspect the full-screen "
                        "waveform; trim only after confirming the silence is "
                        "unintentional.",
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

    def audit(
        self,
        embed_lyrics_first: bool = False,
        refresh_embedded_lyrics: bool = False,
    ) -> dict[str, Any]:
        progress = None
        embedded: list[dict[str, Any]] = []
        enumeration_started = time.monotonic()
        with ExitStack() as stack:
            def on_file(discovered_count: int) -> None:
                nonlocal progress
                if not sys.stderr.isatty():
                    return
                elapsed = time.monotonic() - enumeration_started
                if progress is None and (
                    should_show_audit_progress(discovered_count)
                    or elapsed > PROGRESS_WAIT_SECONDS
                ):
                    progress = stack.enter_context(
                        progress_bar(
                            total=None,
                            description="🔎 Finding files",
                            unit="files",
                            enabled=True,
                            bar_format=ENUMERATION_PROGRESS_FORMAT,
                        )
                    )
                    if progress is not None:
                        progress.update(discovered_count)
                elif progress is not None:
                    progress.update(1)

            self.collect_files(on_file=on_file)
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
                        enabled=sys.stderr.isatty()
                        and should_show_audit_progress(len(self.files)),
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
                self.progress_phase("🔇 Detecting excessive silence")
                self.audit_excessive_silence()
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


def extract_url_only_comment(text: str) -> str | None:
    match = re.fullmatch(r"(?:visit\s+)?(https?://\S+)\s*", text, flags=re.I)
    return match.group(1) if match else None


def read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="replace")


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
        plain = plain_from_lrc(read_text(lrc)) if lrc else plain_from_srt(read_text(srt))
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
    plain_source, _plain_line_count = first_usable_plain_sidecar(
        [
            candidate
            for candidate in (txt, lrc)
            if candidate and candidate.exists()
        ]
    )
    plain = (
        usable_plain_sidecar_content(plain_source)
        if plain_source
        else ""
    )
    synced = timed_sidecar_content(lrc) if lrc and lrc.exists() else ""
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
            and lrc
            and (
                force_refresh
                or lyric_refresh_reasons(
                    path,
                    lrc,
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
        and lrc
        and (
            force_refresh
            or lyric_refresh_reasons(
                path,
                lrc,
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
    if not metadata["album"] and folder_artist:
        metadata["album"] = folder_album
    if not metadata["album_artist"] and folder_artist:
        metadata["album_artist"] = folder_artist
    if not metadata["artist"]:
        metadata["artist"] = metadata["album_artist"]
    if not metadata["album_artist"]:
        metadata["album_artist"] = metadata["artist"]
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
    raise RuntimeError(
        "No release with an approved Front image was found on "
        "MusicBrainz/Cover Art Archive"
        + (
            "; Discogs was also checked"
            if os.environ.get("DISCOGS_TOKEN")
            else "; set DISCOGS_TOKEN to enable the Discogs fallback"
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


def waveform_preview_geometry() -> ArtworkPreviewGeometry:
    """Use nearly the full live viewport for diagnostic waveform review."""
    return artwork_preview_geometry(
        indent_columns=12,
        right_margin_columns=1,
        reserved_text_rows=9,
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
    """Fill the requested width without ever exceeding the height limit."""
    source_width, source_height = image.size
    if source_width < 1 or source_height < 1:
        raise RuntimeError("Preview source has invalid dimensions")
    proportional_height = max(
        1,
        round(source_height * width / source_width),
    )
    target_height = min(max(1, height), proportional_height)
    target = (max(1, width), target_height)
    if target == image.size:
        return image
    return image.resize(target, Image.Resampling.LANCZOS)


def ansi_half_block_preview(
    path: Path,
    *,
    use_color: bool,
    geometry: ArtworkPreviewGeometry | None = None,
    stretch_to_width: bool = False,
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
) -> bytes:
    """Encode a console-filling 64-color Sixel using only Pillow and stdlib."""
    if Image is None:
        raise RuntimeError("Pillow is unavailable for the Sixel preview")
    geometry = geometry or artwork_preview_geometry()
    with Image.open(path) as source:
        image = (
            width_filling_preview_image(
                source.convert("RGB"),
                geometry.pixel_width,
                geometry.pixel_height,
            )
            if stretch_to_width
            else fitted_preview_image(
                source.convert("RGB"),
                geometry.pixel_width,
                geometry.pixel_height,
            )
        )
        quantized = image.quantize(
            colors=64,
            method=Image.Quantize.MEDIANCUT,
            dither=Image.Dither.FLOYDSTEINBERG,
        )
        width, height = quantized.size
        palette = quantized.getpalette() or []
        used_colors = sorted(set(quantized.getdata()))
        color_pixels = {
            color: [
                (
                    round((palette[color * 3] / 255) * 100),
                    round((palette[color * 3 + 1] / 255) * 100),
                    round((palette[color * 3 + 2] / 255) * 100),
                )
            ]
            for color in used_colors
        }
        pixel_data = quantized.load()
        pieces = ["\033Pq", f'"1;1;{width};{height}']
        for color, values in color_pixels.items():
            red, green, blue = values[0]
            pieces.append(f"#{color};2;{red};{green};{blue}")
        for band_y in range(0, height, 6):
            masks: dict[int, bytearray] = {}
            for offset, y in enumerate(
                range(band_y, min(band_y + 6, height))
            ):
                bit = 1 << offset
                for x in range(width):
                    color = pixel_data[x, y]
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
                            pieces.append(
                                _sixel_run(previous, run_count)
                            )
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


def emit_sixel_preview(
    payload: bytes,
    *,
    geometry: ArtworkPreviewGeometry | None = None,
) -> None:
    """Write a prepared Sixel payload while retaining the standard indent."""
    geometry = geometry or artwork_preview_geometry()
    print(" " * geometry.indent_columns, end="", flush=True)
    stream = getattr(sys.stdout, "buffer", None)
    if stream is not None:
        stream.write(payload)
        stream.flush()
        print()
    else:
        print(payload.decode("ascii", errors="replace"))


def render_artwork_preview(
    path: Path,
    *,
    use_color: bool,
    prefer_sixel: bool = False,
    geometry: ArtworkPreviewGeometry | None = None,
    stretch_to_width: bool = False,
) -> str:
    """Fit artwork to the live console through Chafa or built-in renderers."""
    geometry = geometry or artwork_preview_geometry()
    chafa = chafa_executable()
    sixel = use_color and (
        prefer_sixel or terminal_supports_sixel()
    )
    if chafa is None and sixel:
        emit_sixel_preview(
            sixel_preview_bytes(
                path,
                geometry=geometry,
                stretch_to_width=stretch_to_width,
            ),
            geometry=geometry,
        )
        return "built-in Sixel"
    if chafa is None:
        print(
            ansi_half_block_preview(
                path,
                use_color=use_color,
                geometry=geometry,
                stretch_to_width=stretch_to_width,
            )
        )
        return "built-in ANSI half-blocks"
    output_format = "sixels" if sixel else "symbols"
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
        command.append("--fit-width")
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
            emit_sixel_preview(
                sixel_preview_bytes(
                    path,
                    geometry=geometry,
                    stretch_to_width=stretch_to_width,
                ),
                geometry=geometry,
            )
            return "built-in Sixel"
        print(
            ansi_half_block_preview(
                path,
                use_color=use_color,
                geometry=geometry,
                stretch_to_width=stretch_to_width,
            )
        )
        return "built-in ANSI half-blocks"
    if sixel:
        emit_sixel_preview(result.stdout, geometry=geometry)
        return "Chafa Sixel"
    rendered = result.stdout.decode(
        sys.stdout.encoding or "utf-8",
        errors="replace",
    )
    print(
        "\n".join(
            f"{' ' * geometry.indent_columns}{line}" if line else ""
            for line in rendered.rstrip().splitlines()
        )
    )
    return "Chafa ANSI symbols"


def render_waveform_preview(path: Path, *, use_color: bool) -> str:
    """Use the full preview geometry and prefer Sixel for waveform review."""
    return render_artwork_preview(
        path,
        use_color=use_color,
        prefer_sixel=True,
        geometry=waveform_preview_geometry(),
        stretch_to_width=True,
    )


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
    plain = "Y=Yes/Enter | N=No | R=Refresh | V=View original"
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
        cover_narration(
            "👁️",
            f"Preview rendered with {mode}.",
            use_color=use_color,
            color=(105, 95, 145),
            dim=True,
        )
        prompt_visible = False
        while True:
            prompt = urgent_prompt_text(question, use_color)
            steady = (
                f"            {prompt} "
                f"{artwork_review_choices(use_color)} "
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


def waveform_review_choices(use_color: bool) -> str:
    """Render explicit diagnostic waveform-review controls."""
    plain = (
        "N=It’s fine | Y=There is a problem | "
        "E=Edit audio | V=View fullscreen"
    )
    if not use_color:
        return f"[{plain}]"
    parts = (
        ("N", "=It’s fine | ", (95, 245, 135)),
        ("Y", "=There is a problem | ", (255, 105, 105)),
        ("E", "=Edit audio | ", (255, 185, 75)),
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


def waveform_review_choice(
    waveform_path: Path,
    audio_path: Path,
    *,
    use_color: bool,
    key_reader=None,
    preview_renderer=None,
    image_viewer=None,
    audio_editor=None,
    problem_renamer=None,
    rename_input_reader=None,
) -> tuple[str, int, Path]:
    """Review one disposable waveform for problems, editing, or navigation."""
    renderer = preview_renderer or render_waveform_preview
    viewer = image_viewer or launch_irfanview
    editor = audio_editor or launch_audio_editor
    renamer = problem_renamer or prompt_for_waveform_problem_rename
    question = f"Does this waveform show a problem in {audio_path.name}?"
    edits_opened = 0
    while True:
        rendered_size = visible_console_size()
        reset_console_pager_after_user_input()
        mode = renderer(waveform_path, use_color=use_color)
        cover_narration(
            "👁️",
            f"Diagnostic preview rendered with {mode}.",
            use_color=use_color,
            color=(105, 95, 145),
            dim=True,
        )
        prompt_visible = False
        while True:
            prompt = urgent_prompt_text(question, use_color)
            steady = (
                f"            {prompt} "
                f"{waveform_review_choices(use_color)} "
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
                except Exception as exc:
                    print_formatted_error(
                        f"Could not open an audio editor: {exc}",
                        use_color,
                    )
                continue
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


def waveform_frame_filters(audio_path: Path) -> str:
    """Draw the outer frame and a divider between every stacked channel."""
    line = "color=0x777777@0.60:t=fill"
    filters = [
        "drawbox=x=0:y=0:w=iw:h=ih:"
        "color=0x777777@0.60:t=4"
    ]
    channels = waveform_channel_count(audio_path)
    filters.extend(
        f"drawbox=x=0:y=ih*{index}/{channels}-2:w=iw:h=4:{line}"
        for index in range(1, channels)
    )
    return ",".join(filters)


def generate_waveform_jpeg(
    audio_path: Path,
    *,
    ffmpeg_executable: str | None = None,
    narrate: bool = True,
    destination: Path | None = None,
) -> tuple[Path, Path | None]:
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
    waveform_filters = (
        "showwavespic=s=1800x700:"
        "split_channels=1:colors=0x55dcff,"
        f"{waveform_frame_filters(audio_path)}"
    )
    command = [
        str(ffmpeg),
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(audio_path),
        "-filter_complex",
        waveform_filters,
        "-frames:v",
        "1",
        "-q:v",
        "2",
        str(temporary),
    ]
    if narrate:
        print(
            console_safe_text(
                "            ▶ Generating 1800×700 waveform JPEG with ffmpeg."
            ),
            flush=True,
        )
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="replace",
        check=False,
    )
    if result.returncode or not temporary.is_file():
        if temporary.exists():
            recycle_path(temporary)
        detail = str(result.stdout or "").strip()
        raise RuntimeError(
            f"ffmpeg waveform generation failed"
            + (f": {detail}" if detail else "")
        )
    if image_mime(temporary) != "image/jpeg":
        recycle_path(temporary)
        raise RuntimeError("ffmpeg did not generate a valid JPEG waveform")
    if target.exists():
        os.replace(temporary, target)
    else:
        temporary.rename(target)
    if image_mime(target) != "image/jpeg" or target.stat().st_size <= 0:
        raise RuntimeError(
            f"Waveform JPEG verification failed after staging: {target}"
        )
    return target, None


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
    workers: int = 2,
) -> dict[str, Any]:
    """Review disposable waveform previews for audible-file warning signs."""
    if not interactive:
        raise RuntimeError(
            "--review-waveforms requires interactive review; "
            "remove --no-interactive"
        )
    audit = BatchAudit(root, include_archives=include_archives)
    audit.collect_files()
    audio_files = audit.audio_files
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
    futures: dict[Path, Future] = {}
    try:
        for item_index, upcoming in enumerate(audio_files, start=1):
            staged_name = (
                f"{item_index:06d}-"
                f"{hashlib.sha256(str(upcoming).encode()).hexdigest()[:12]}"
                ".waveform.jpg"
            )
            futures[upcoming] = executor.submit(
                generate_waveform_jpeg,
                upcoming,
                narrate=False,
                destination=staging_folder / staged_name,
            )
        for index, audio_path in enumerate(audio_files, start=1):
            print()
            print(
                f"        🎛️ Waveform {index}/{len(audio_files)}:"
            )
            print(
                f"            {music_filename(audit.rel(audio_path), use_color)}"
            )
            future = futures[audio_path]
            if not future.done():
                print(
                    rgb_text(
                        "            ⏳ Finishing the background waveform render…",
                        190,
                        185,
                        150,
                        use_color,
                        dim=True,
                    )
                )
            try:
                staged_waveform, _staging_backup = future.result()
                decision, edit_count, reviewed_audio_path = waveform_review_choice(
                    staged_waveform,
                    audio_path,
                    use_color=use_color,
                    key_reader=key_reader,
                    preview_renderer=(
                        preview_renderer or render_waveform_preview
                    ),
                    image_viewer=image_viewer,
                    audio_editor=discovered_editor,
                )
                if edit_count:
                    edited.append(str(reviewed_audio_path))
                if decision == "fine":
                    fine.append(str(reviewed_audio_path))
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
        f"        {len(fine)} fine, {len(problems)} problem"
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
        "audio_files": len(audio_files),
        "fine": fine,
        "problems": problems,
        "edited": edited,
        "failed": failed,
        "staging_folder": str(staging_folder),
    }


def offer_post_audit_waveform_review(
    root: Path,
    *,
    interactive: bool,
    suppressed: bool,
    include_archives: bool,
    use_color: bool,
    workers: int,
    key_reader=None,
    reviewer=None,
) -> dict[str, Any] | None:
    """Offer a default-No handoff from a normal audit to waveform review."""
    if not interactive or suppressed:
        return None
    if not prompt_for_approval(
        "Run the interactive waveform review now?",
        False,
        use_color,
        key_reader=key_reader,
        indent="        ",
    ):
        return None
    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "Waveform review cannot start because ffmpeg is not in PATH"
        )
    review = reviewer or review_waveforms
    return review(
        root,
        include_archives=include_archives,
        use_color=use_color,
        interactive=True,
        key_reader=key_reader,
        workers=workers,
    )


def find_cover_and_embed(
    path: Path,
    *,
    audio_targets: list[Path] | None = None,
    album_scope: bool | None = None,
    use_color: bool = True,
    interactive: bool = True,
    key_reader=None,
    json_fetcher: Callable[..., dict[str, Any] | None] | None = None,
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
        "conservative release matches.",
        use_color=use_color,
        color=(85, 135, 165),
        dim=True,
    )
    with progress_bar(
        total=1,
        description="🎨 Finding cover art · MusicBrainz",
        unit="release",
        enabled=bool(getattr(sys.stderr, "isatty", lambda: False)()),
    ) as lookup_progress:
        match = resolve_cover_match(path, json_fetcher=json_fetcher)
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
        unit="image",
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
        stem = art_sidecar_stem(picture_type)
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


def front_art_candidate(path: Path) -> Path | None:
    candidates = folder_front_art_candidates(path.parent)
    return candidates[0] if candidates else None


def is_allowed_front_art_name(path: Path) -> bool:
    """Accept explicit Front names, including collision-safe numeric suffixes."""
    return bool(
        re.fullmatch(
            r"(?:cover|folder)(?: \(\d+\))?",
            path.stem,
            flags=re.IGNORECASE,
        )
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
    write: bool = True,
) -> tuple[Path, bool]:
    """Return a JPEG Front sidecar, creating a collision-safe copy if needed."""
    if not is_allowed_front_art_name(image):
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
    if not is_allowed_front_art_name(image):
        raise RuntimeError(
            f"Only cover.* or folder.* may be embedded; refusing {image.name}"
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


def render_text(data: dict[str, Any], max_examples: int) -> str:
    return render_console_report(data, max_examples, use_color=False)


SUMMARY_CATEGORIES = {
    "backup_file": ("Backup files kept", "backup"),
    "json_sidecar": ("JSON sidecars kept", "JSON"),
    "log_sidecar": ("Log sidecars kept", "log"),
    "kept_user_marker": ("User marker/comment files kept", "marker"),
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


def music_filename(path: str, use_color: bool) -> str:
    """Render a filename with a one-cell note aligned under two-cell emoji."""
    return f" ♪ {varied_path(path, use_color)}"


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
    renames = finding.get("details", {}).get("renames", [])
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
    backups = [
        action.removeprefix("backup:")
        for action in actions
        if action.startswith("backup:")
    ]
    for backup in backups:
        lines.append(
            rgb_text(
                f"{indent}💾 Backup: {backup}",
                190,
                195,
                205,
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
    applied = [
        humanized_action(action)
        for action in actions
        if not action.startswith("backup:")
        and not action.startswith("saved_art:")
        and not action.startswith("embedded_art:")
        and not action.startswith("recycled_rejected_art:")
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
    refresh_mode = data.get("embedded_lyrics_mode") == "refresh"
    flag = (
        "--refresh-embedded-lyrics"
        if refresh_mode
        else "--embed-lyrics"
    )
    verb = "refreshed" if refresh_mode else "embedded"
    title = (
        "Lyrics/karaoke refreshed by --refresh-embedded-lyrics"
        if refresh_mode
        else "Lyrics/karaoke embedded by --embed-lyrics"
    )
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
        lines.append(
            f"        🎤 {flag} {verb} {description}:"
        )
        lines.append(
            f"            {music_filename(str(item['path']), use_color)}"
        )
        for action in item.get("actions", []):
            if str(action).startswith("backup:"):
                backup = str(action).removeprefix("backup:")
                lines.append(
                    rgb_text(
                        f"            💾 Backup: {backup}",
                        190,
                        195,
                        205,
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


def finding_target_lines(
    finding: dict[str, Any],
    use_color: bool,
) -> list[str]:
    """Render an audio target or an album-level grouped-rename target."""
    if finding["category"] in GROUPED_RENAME_CATEGORIES:
        return [
            f"📁 Album folder: {varied_path(finding['path'], use_color)}",
            *rename_preview_table(finding, use_color),
        ]
    return [music_filename(finding["path"], use_color)]


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
    continuation_prefix = "    "
    chunks: list[tuple[str, str]] = []
    remaining = path
    prefix = first_prefix
    while remaining:
        available = max(1, double_height_capacity - len(prefix))
        chunks.append((prefix, remaining[:available]))
        remaining = remaining[available:]
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
        "lrc_txt_missing_srt_but_lrc_untimed": "Untimed LRC cannot create karaoke",
        "missing_plain_lyrics": "Plain lyrics missing",
        "missing_karaoke": "Timed karaoke missing",
        "unusable_karaoke_sidecar": "Timed sidecar needs repair",
        "unusable_plain_lyric_sidecar": "Plain-lyrics sidecar needs repair",
        "missing_embedded_art": "Embedded cover missing",
        "missing_replaygain": "ReplayGain missing",
        "karaoke_not_embedded": "Timed karaoke ready to embed",
        "plain_lyrics_not_embedded": "Plain lyrics ready to embed",
        "redundant_album_artist_filename_group": (
            "Redundant artist in album filenames"
        ),
        "filename_title_capitalization_group": (
            "Album filename capitalization"
        ),
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
    if category in GROUPED_RENAME_CATEGORIES:
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
        count = len(finding.get("details", {}).get("renames", []))
        return (
            f"Rename these {count} album files to remove the redundant "
            "artist name now?"
        )
    if category == "filename_title_capitalization_group":
        count = len(finding.get("details", {}).get("renames", []))
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
        ("Problems", visible_counts.get("problem", 0), "Must be fixed or investigated.", (255, 100, 105)),
        ("Fixes ready", visible_counts.get("safe_fix", 0), "Concrete repairs that can be applied.", (120, 225, 140)),
        ("Cleanup candidates", visible_counts.get("safe_cleanup", 0), "Removable items, applied only after approval.", (255, 195, 90)),
        ("Review needed", visible_counts.get("ask_first", 0), "Needs information or human judgment.", (230, 145, 245)),
        ("Kept files", kept_count, "Recognized support/history files being kept.", (120, 190, 245)),
        ("Information", visible_counts.get("info", 0), "Context only; no action normally required.", (155, 175, 195)),
    ]
    lines.extend(double_height_traffic_section("Findings by severity", use_color))
    lines.append("")
    for label, number, explanation, color in severity_rows:
        colored_number = rgb_text(str(number), *color, use_color)
        colored_label = rgb_text(label, *color, use_color)
        lines.append(f"        {colored_label}: {colored_number} — {explanation}")

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
        for category, (label, _noun) in SUMMARY_CATEGORIES.items():
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
                lines.append(f"        {colored_number} {label}.")

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
        for finding in coded[: max_examples or None]:
            lines.append(f"        {approval_action_line(finding, use_color)}")
            lines.extend(
                f"            {line}"
                for line in finding_target_lines(finding, use_color)
            )
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
                "Review needed — warnings",
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
        for finding in other_review[: max_examples or None]:
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
            lines.append(f"        {label} — {warning_finding_message(finding)}")
            lines.extend(
                f"            {line}"
                for line in finding_target_lines(finding, use_color)
            )
            lines.extend(
                f"            {line}"
                for line in finding_sidecar_lines(finding, use_color)
            )
            if finding.get("suggestion") and finding["category"] != "missing_album":
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
        "  * complete MusicBrainz/Cover Art Archive artwork-set discovery, with",
        "    every supplied part saved but only one approved Front image embedded",
        "  * full-console Chafa, Sixel, or ANSI artwork previews that automatically",
        "    re-render after a live window/font-size change; V opens the original",
        "  * full-width diagnostic waveform review with parallel background pre-rendering,",
        "    live resize, problem marking, image viewing, editing, and optional rename",
        "  * a default-No end-of-audit offer to begin waveform review immediately",
        "  * default detection of excessive leading, internal, or trailing silence",
        "  * comment-filtered plain/timed lyric embedding plus newer-sidecar refresh",
        "  * timestamped backups, immediate repairs, and post-write re-auditing",
        "  * rainbow progress bars and More-style single-key paging",
        "",
        *usage_header("✨✱✨ Usage ✨✱✨", use_color),
        "",
        f"  {command('audit_music_batch.py')} {example('[foldername]')} {command('[flags]')}",
        note(
            "  ^ A folder is required for a normal audit. "
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
            "  ^ Enable or suppress missing-cover lookup; approved Front is "
            "the only image embedded."
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
        f"{default_badge(False)}  {default_value_badge('2 workers')}",
        note(
            "  ^ Run waveform review directly, suppress its normal end-of-audit "
            "offer, or choose 1-8 pre-render workers."
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


def urgent_prompt_text(text: str, use_color: bool) -> str:
    """Style a question-led prompt urgently while italicizing its key nouns."""
    if not use_color:
        return f"❓ {text}"
    base = f"{ANSI['bold']}\033[38;2;255;105;45m"
    noun_style = f"{base}{ANSI['italic']}"
    noun_alternatives = [
        re.escape(phrase)
        for phrase in sorted(PROMPT_NOUN_PHRASES, key=len, reverse=True)
    ]
    pattern = re.compile(
        "(" + "|".join(noun_alternatives + [r"\([^()]+\.(?:jpe?g|png|webp|gif)\)"]) + ")",
        flags=re.IGNORECASE,
    )
    pieces = pattern.split(text)
    styled: list[str] = [base, "❓ "]
    for piece in pieces:
        if re.fullmatch(
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
            msvcrt.getwch()
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


def prompt_for_approval(
    question: str,
    default_yes: bool,
    use_color: bool,
    key_reader=None,
    indent: str = "",
) -> bool:
    reader = key_reader or read_single_key
    steady_prompt = approval_prompt(question, default_yes, use_color, indent)
    interactive_terminal = bool(
        getattr(sys.stdout, "isatty", lambda: False)()
    )
    waiting_prompt = blinking_approval_prompt(
        steady_prompt, use_color and interactive_terminal
    )
    print(waiting_prompt, end="", flush=True)
    while True:
        key = reader()
        if key == "\x03":
            if interactive_terminal:
                print(ANSI["reset"], end="", flush=True)
            raise KeyboardInterrupt
        if key in {"\r", "\n"}:
            if interactive_terminal:
                erase_wrapped_console_text(steady_prompt)
                print(
                    f"{settled_approval_prompt(question, default_yes, use_color, indent)}"
                    f"{ANSI['erase_to_eol']}"
                )
            else:
                print(approval_answer(default_yes, use_color))
            reset_console_pager_after_user_input()
            return default_yes
        lowered = key.lower()
        if lowered in {"y", "n"}:
            answer_yes = lowered == "y"
            if interactive_terminal:
                erase_wrapped_console_text(steady_prompt)
                print(
                    f"{settled_approval_prompt(question, answer_yes, use_color, indent)}"
                    f"{ANSI['erase_to_eol']}"
                )
            else:
                print(approval_answer(answer_yes, use_color))
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
}


def action_scope_options(default_yes: bool, use_color: bool) -> str:
    """Render all single-key choices for a repeatable batch action."""
    yes_key = "Y" if default_yes else "y"
    no_key = "n" if default_yes else "N"
    plain = (
        f"[{yes_key}=Yes / {no_key}=No / A=Always / V=Never / "
        "F=Just Do For This Folder]"
    )
    if not use_color:
        return plain
    chunks = [
        rgb_text("[", 255, 205, 55, True),
        rgb_text(f"{yes_key}=Yes", 95, 245, 135, True),
        rgb_text(" / ", 255, 165, 45, True),
        rgb_text(f"{no_key}=No", 255, 105, 105, True),
        rgb_text(" / ", 255, 165, 45, True),
        rgb_text("A=Always", 255, 225, 80, True),
        rgb_text(" / ", 255, 165, 45, True),
        rgb_text("V=Never", 255, 145, 80, True),
        rgb_text(" / ", 255, 165, 45, True),
        rgb_text("F=Just Do For This Folder", 145, 215, 255, True),
        rgb_text("]", 255, 205, 55, True),
    ]
    return "".join(chunks)


def action_scope_prompt(
    question: str,
    default_yes: bool,
    use_color: bool,
    indent: str = "",
) -> str:
    """Build the urgent repeatable-action prompt."""
    return (
        f"{indent}{urgent_prompt_text(question, use_color)} "
        f"{action_scope_options(default_yes, use_color)} "
    )


def action_scope_answer(choice: str, use_color: bool) -> str:
    """Render the stable answer replacing a repeatable prompt's options."""
    labels = {
        "yes": ("Yes!", (95, 245, 135)),
        "no": ("No!", (255, 105, 105)),
        "always": ("Always!", (255, 225, 80)),
        "never": ("Never!", (255, 125, 80)),
        "folder": ("Just This Folder!", (145, 215, 255)),
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
) -> str:
    """Read Y/N/Always/Never/Folder with one key and no required Enter."""
    reader = key_reader or read_single_key
    steady_prompt = action_scope_prompt(
        question,
        default_yes,
        use_color,
        indent,
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
            if choice is None:
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

    if category == "missing_replaygain":
        return apply_argt_replaygain_folder(
            target.parent,
            use_color=use_color,
            stream_output=True,
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
    missing = [
        finding
        for finding in data.get("findings", [])
        if finding.get("category") == "missing_embedded_art"
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


def interactive_apply(
    data: dict[str, Any],
    use_color: bool,
    key_reader=None,
    input_reader=None,
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

    for finding in coded:
        lyric_action = finding["category"] in {
            "embedded_lyrics_outdated",
            "plain_lyrics_not_embedded",
            "karaoke_not_embedded",
        }
        reaudit_action = (
            lyric_action
            or finding["category"] == "missing_replaygain"
            or finding["category"] == "missing_embedded_art"
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
        default_yes = finding["severity"] in {"safe_fix", "safe_cleanup"}
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
            for line in finding_target_lines(finding, use_color):
                print(f"            {line}")
            for line in finding_sidecar_lines(finding, use_color):
                print(f"            {line}")
            if finding.get("suggestion"):
                print(f"            {suggested_text(finding, use_color)}")
            question = approval_question(finding)
            target = safe_finding_path(root, finding)
            scope_folder = (
                target
                if finding["category"] in GROUPED_RENAME_CATEGORIES
                else target.parent
            )
            folder_key = (
                str(finding["category"]),
                str(scope_folder.resolve()).casefold(),
            )
            choice = remembered_category_choices.get(
                str(finding["category"])
            )
            if choice is None and folder_key in remembered_folder_approvals:
                choice = "folder"
            if choice is None:
                choice = prompt_for_action_scope(
                    question,
                    default_yes,
                    use_color,
                    key_reader=key_reader,
                    indent="            ",
                )
                if choice in {"always", "never"}:
                    remembered_category_choices[
                        str(finding["category"])
                    ] = choice
                elif choice == "folder":
                    remembered_folder_approvals.add(folder_key)
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
            if should_apply:
                try:
                    actions = apply_finding(
                        root,
                        finding,
                        use_color=use_color,
                        key_reader=key_reader,
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
                    if reaudit_action:
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
                "applied": should_apply and error is None,
                "skipped": not should_apply,
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


def run_unit_tests() -> int:
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
    from send2trash import send2trash
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
                send2trash(str(cls.album_test_root))

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
                    "Lyrics/karaoke embedded by --embed-lyrics",
                    console,
                )
                self.assertIn(
                    "🎤 --embed-lyrics embedded plain lyrics, timed karaoke:",
                    console,
                )
                self.assertIn(" ♪ 01 Test Song.flac", console)
                self.assertIn("💾 Backup:", console)
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
                    "Lyrics/karaoke refreshed by "
                    "--refresh-embedded-lyrics",
                    console,
                )
                self.assertIn(
                    "--refresh-embedded-lyrics refreshed "
                    "plain lyrics, timed karaoke",
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
                        "🎨 Finding cover art · MusicBrainz",
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
                return_value=False,
            ), mock.patch.object(
                module,
                "visible_console_size",
                return_value=os.terminal_size((160, 50)),
            ), mock.patch.object(
                subprocess,
                "run",
                return_value=completed,
            ) as run, contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(
                    "Chafa ANSI symbols",
                    render_artwork_preview(
                        Path(r"C:\Music\cover.jpg"),
                        use_color=True,
                    ),
                )
            chafa_command = run.call_args.args[0]
            self.assertIn("--size=146x43", chafa_command)
            self.assertIn("--scale=max", chafa_command)

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
                    "\n            ❓ Embed the plain lyrics into this audio file now? "
                    "[Y=Yes / n=No / A=Always / V=Never / "
                    "F=Just Do For This Folder] Yes!",
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
                    "\033[2m\033[38;2;190;195;205m"
                    "            💾 Backup:",
                    colored_results,
                )
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
            self.assertIn("{n:,.0f}/{total:,.0f} checks", AUDIT_PROGRESS_FORMAT)
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

        def test_waveform_jpeg_generation_is_verified(self) -> None:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                audio = make_silent_flac(
                    root,
                    "Waveform Fixture [instrumental]",
                    channels=2,
                )
                staged = root / "staged.waveform.jpg"
                waveform, backup = generate_waveform_jpeg(
                    audio,
                    destination=staged,
                    narrate=False,
                )
                self.assertEqual(staged, waveform)
                self.assertIsNone(backup)
                self.assertEqual("image/jpeg", image_mime(waveform))
                with Image.open(waveform) as preview:
                    self.assertEqual((1800, 700), preview.size)
                    border_pixel = preview.convert("RGB").getpixel((1, 1))
                    self.assertLess(
                        max(border_pixel) - min(border_pixel),
                        20,
                    )
                    self.assertGreater(sum(border_pixel), 120)
                    center_pixel = preview.convert("RGB").getpixel(
                        (preview.width // 2, preview.height // 2)
                    )
                    self.assertLess(
                        max(center_pixel) - min(center_pixel),
                        20,
                    )
                    self.assertGreater(sum(center_pixel), 120)
                self.assertTrue(staged.exists())
                self.assertFalse(
                    audio.with_name(f"{audio.stem}.waveform.jpg").exists()
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

        def test_post_audit_waveform_offer_can_run_or_be_suppressed(
            self,
        ) -> None:
            review_result = {
                "audio_files": 1,
                "fine": [r"C:\Music\Track.flac"],
                "problems": [],
                "edited": [],
                "failed": [],
                "staging_folder": r"C:\recycled\waveforms",
            }
            reviewer = mock.Mock(return_value=review_result)
            with mock.patch.object(
                shutil,
                "which",
                return_value=r"C:\util\ffmpeg.exe",
            ), contextlib.redirect_stdout(io.StringIO()):
                declined = offer_post_audit_waveform_review(
                    Path(r"C:\Music"),
                    interactive=True,
                    suppressed=False,
                    include_archives=False,
                    use_color=False,
                    workers=3,
                    key_reader=lambda: "n",
                    reviewer=reviewer,
                )
                accepted = offer_post_audit_waveform_review(
                    Path(r"C:\Music"),
                    interactive=True,
                    suppressed=False,
                    include_archives=True,
                    use_color=False,
                    workers=3,
                    key_reader=lambda: "y",
                    reviewer=reviewer,
                )
                suppressed = offer_post_audit_waveform_review(
                    Path(r"C:\Music"),
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
            reviewer.assert_called_once()
            self.assertTrue(
                reviewer.call_args.kwargs["include_archives"]
            )
            self.assertEqual(3, reviewer.call_args.kwargs["workers"])
            self.assertTrue(
                parse_args(
                    [".", "--no-review-waveforms"]
                ).no_review_waveforms
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

        def test_waveform_geometry_uses_nearly_full_live_console(self) -> None:
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
                geometry = waveform_preview_geometry()
            self.assertEqual(12, geometry.indent_columns)
            self.assertEqual(187, geometry.columns)
            self.assertEqual(51, geometry.rows)
            self.assertEqual(1870, geometry.pixel_width)
            self.assertEqual(1020, geometry.pixel_height)
            source = Image.new("RGB", (1800, 700), "black")
            width_filled = width_filling_preview_image(
                source,
                geometry.pixel_width,
                geometry.pixel_height,
            )
            self.assertEqual(geometry.pixel_width, width_filled.width)
            self.assertLessEqual(
                width_filled.height,
                geometry.pixel_height,
            )
            completed = mock.Mock(
                returncode=0,
                stdout=b"mock-sixel",
                stderr=b"",
            )
            with mock.patch.object(
                module,
                "chafa_executable",
                return_value=Path(r"C:\util\Chafa.exe"),
            ), mock.patch.object(
                subprocess,
                "run",
                return_value=completed,
            ) as run, mock.patch.object(
                module,
                "emit_sixel_preview",
            ) as emit:
                self.assertEqual(
                    "Chafa Sixel",
                    render_artwork_preview(
                        Path(r"C:\Temp\waveform.jpg"),
                        use_color=True,
                        prefer_sixel=True,
                        geometry=geometry,
                        stretch_to_width=True,
                    ),
                )
            command = run.call_args.args[0]
            self.assertIn("--size=187x51", command)
            self.assertIn("--view-size=187x51", command)
            self.assertIn("--fit-width", command)
            emit.assert_called_once_with(
                b"mock-sixel",
                geometry=geometry,
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

        def test_waveform_diagnostic_can_edit_view_and_mark_problem(
            self,
        ) -> None:
            waveform = Path(r"C:\Temp\track.waveform.jpg")
            audio = Path(r"C:\Music\Track.flac")
            renamed_audio = audio.with_name("Track [waveform problem].flac")
            keys = iter(("e", "v", "y", "y", "y"))
            calls = {
                "render": 0,
                "edit": 0,
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
                    "render": 1,
                    "edit": 2,
                    "rename": 1,
                    "view": 1,
                },
                calls,
            )
            rendered = output.getvalue()
            self.assertIn("N=It’s fine", rendered)
            self.assertIn("Y=There is a problem", rendered)
            self.assertIn("E=Edit audio", rendered)
            self.assertIn("V=View fullscreen", rendered)
            self.assertIn("Yes — there is a problem.", rendered)
            self.assertIn("Want to edit this audio file now?", rendered)
            self.assertIn(
                "Want to rename this audio file to flag the problem?",
                rendered,
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
                staging_root = root / "recycled-staging"
                module = sys.modules[__name__]

                def fake_generate(
                    _audio: Path,
                    *,
                    narrate: bool,
                    destination: Path,
                    **_kwargs,
                ) -> tuple[Path, None]:
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(make_test_jpeg())
                    return destination, None

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
                    "waveform_review_choice",
                    return_value=("fine", 0, audio),
                ), mock.patch.object(
                    module,
                    "audio_editor_executable",
                    return_value=None,
                ), contextlib.redirect_stdout(io.StringIO()) as output:
                    result = review_waveforms(
                        root,
                        use_color=False,
                        workers=1,
                    )
                self.assertNotIn(
                    "Background waveform render is ready",
                    output.getvalue(),
                )
                self.assertEqual([str(audio)], result["fine"])
                self.assertEqual([], result["problems"])
                staged_folder = Path(result["staging_folder"])
                self.assertTrue(staged_folder.is_dir())
                self.assertEqual(
                    1,
                    len(list(staged_folder.glob("*.waveform.jpg"))),
                )
                self.assertFalse(
                    audio.with_name(f"{audio.stem}.waveform.jpg").exists()
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
                keys = iter(("a", "v", "f", "n"))
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
                self.assertEqual(["a", "v", "f", "n"], keypresses)
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
            self.assertIn("[default = 2 workers]", usage)
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
            self.assertFalse(should_show_audit_progress(599))
            self.assertTrue(
                should_show_audit_progress(PROGRESS_FIRST_FILE_COUNT)
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
                self.assertIn("\n        Problems:", rendered)
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
                self.assertIn("\n         1 Backup files kept.", aligned)
                self.assertIn("\n        25 Log sidecars kept.", aligned)
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
                    "F=Just Do For This Folder] Yes!",
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
                audio["GENRE"] = ["Pop Punk"]
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
            self.assertIn("♪", output.getvalue())
            self.assertIn("✅", output.getvalue())
            self.assertIn("❓", prompts[0])
            self.assertTrue(output.getvalue().startswith("             ♪"))
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
            self.assertTrue(output.getvalue().startswith("             ♪"))
            self.assertTrue(prompts[0].startswith("            ❓"))
            self.assertIn("ENTER", prompts[0])

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

        def getDescription(self, test) -> str:
            return (
                f"{unit_test_purpose(test)} "
                f"[{test._testMethodName}]"
            )

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
        result = DescriptiveTestRunner(verbosity=2).run(suite)
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
            "Suppress the default-No offer to begin waveform review after "
            "a normal interactive audit."
        ),
    )
    parser.add_argument(
        "--waveform-workers",
        type=int,
        default=2,
        metavar="NUMBER",
        help="Background waveform render workers (1-8; default 2).",
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


def _main(argv: list[str] | None = None) -> int:
    raw_argv = sys.argv[1:] if argv is None else argv
    if not raw_argv:
        print_usage(use_color=True)
        return 0
    args = parse_args(raw_argv)
    if args.help:
        print_usage(use_color=not args.no_color)
        return 0
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
        return run_unit_tests()
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
        if result["decisions"]:
            results_header = "\n".join(
                double_height_gradient_section(
                    "Interactive results",
                    not args.no_color,
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
                    not args.no_color,
                )
                + "\n"
            )
        try:
            waveform_handoff = offer_post_audit_waveform_review(
                Path(args.root),
                interactive=True,
                suppressed=args.no_review_waveforms,
                include_archives=args.include_archives,
                use_color=not args.no_color,
                workers=args.waveform_workers,
            )
            waveform_handoff_failed = bool(
                waveform_handoff
                and waveform_handoff.get("failed")
            )
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


def main(argv: list[str] | None = None) -> int:
    """Run with automatic paging unless explicitly disabled or redirected."""
    raw_argv = sys.argv[1:] if argv is None else argv
    with paged_console_output("--no-pager" not in raw_argv):
        return _main(raw_argv)


if __name__ == "__main__":
    raise SystemExit(main())
