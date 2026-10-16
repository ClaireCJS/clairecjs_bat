#!/usr/bin/env python3
# CHAT ARTIFACT BUILD: 2026-08-05-SINGLE-HEIGHT-KARAOKE-CENTERING-V20
"""Interactively preview an audio file from a Windows console.

This program uses FFplay and accepts any audio format FFmpeg can decode,
including WAV, FLAC, and MP3.

Playback controls
-----------------
X, Q, Ctrl+W, Alt+F4, Ctrl+C, or Ctrl+Break
    Stop playback immediately. Esc is ignored during normal playback.
Left / Right
    Seek backward or forward five seconds.
Shift+Left / Shift+Right
    Seek backward or forward fifteen seconds.
Ctrl+Left / Ctrl+Right
    Seek backward or forward one minute.
< / >
    Play the previous or next audio file in the current folder.
{ / }
    Play the previous or next directory containing audio files.

Run ``play_audio_file.py --unit-tests`` to exercise the key mapping and the
restart-at-offset seeking controller without playing real audio.
"""

from __future__ import annotations

import contextlib
import importlib
import importlib.util
import colorsys
import hashlib
import io
import json
import math
import os
from pathlib import Path, PureWindowsPath
import re
import random
import shutil
import signal
import sqlite3
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
import unittest
import unicodedata
import wave
from unittest import mock

# Use one encoding end-to-end.  Windows Terminal and Python both receive
# genuine Unicode; no CP1252 bridge strings are required.
if os.name == "nt":
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    except (AttributeError, OSError):
        pass
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

try:
    _wcwidth = importlib.import_module("wcwidth")
    wcswidth = _wcwidth.wcswidth
except ImportError:
    def wcswidth(text: str) -> int:
        """Small dependency-free terminal-width fallback."""
        width = 0
        joined = False
        for index, character in enumerate(text):
            codepoint = ord(character)
            category = unicodedata.category(character)
            if category.startswith("C") and character not in {"\u200d"}:
                return -1
            if unicodedata.combining(character) or codepoint in {0x200D, 0xFE0E, 0xFE0F}:
                if codepoint == 0x200D:
                    joined = True
                continue
            if joined:
                joined = False
                continue
            next_is_emoji_selector = index + 1 < len(text) and ord(text[index + 1]) == 0xFE0F
            if 0x1F1E6 <= codepoint <= 0x1F1FF:
                width += 1
            elif (
                unicodedata.east_asian_width(character) in {"W", "F"}
                or 0x1F000 <= codepoint <= 0x1FAFF
                or next_is_emoji_selector
            ):
                width += 2
            else:
                width += 1
        return width

_CLAIRE_UTILS_DIR = r"C:\clairecjs_utils"
if _CLAIRE_UTILS_DIR not in sys.path:
    sys.path.insert(0, _CLAIRE_UTILS_DIR)
# The `claire_progressbar` module is optional and may not be available in
# all environments.  Import it lazily and provide a minimal stub that
# satisfies the type checker and runtime expectations.
try:
    from claire_progressbar import progress_bar  # type: ignore
except ImportError:  # pragma: no cover
    # A very small stand‑in that mimics the context‑manager interface used
    # throughout the code.  It simply discards all progress updates.
    class _DummyProgressBar:
        def __init__(self, *_, **__):
            pass

        def update(self, *_, **__):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_, **__):
            return False

    def progress_bar(*_, **__):  # type: ignore
        return _DummyProgressBar()


import csv
from datetime import datetime, timezone, timedelta
# Set to 0 when the terminal cannot render DEC SIXEL graphics.
PLAYER_BUILD_ID                 = "2026-08-05-single-height-karaoke-centering-v20"
WRITE_NOWPLAYING_THIS_OFTEN     = 5.0
PREVENT_WINAMP_PAUSE_WHEN_WE_ARE_PAUSED = 0
LYRIC_FADE_SECONDS              = 6.0
LYRIC_NEIGHBOR_MAX_BRIGHTNESS   = 0.66
LYRIC_NEXT_FADE_MAX_SECONDS     = 6.0
LYRIC_PREVIOUS_FADE_MAX_SECONDS = 6.0
LYRIC_PREVIEW_LEAD_SECONDS      = 0.25
LYRIC_SCROLL_ROW_STEPS          = 2
LYRIC_SCROLL_STEP_SECONDS       = 0.08
HIDE_EMOJI_WHEN_FADE_IS_UNDER_X_PERCENT = 25
HIDE_PREVIOUS_EMOJI_WHEN_FADE_IS_UNDER_X_PERCENT = 50
NEXT_SUNG_LINE_EMOJIMAXX_ON_AT_FIRST = 1  # When this is 1, the upcoming/next karaoke line uses Emojimax from the very first visible instant of its fade-in instead of waiting for the fade threshold above; when set to 0, the upcoming line follows HIDE_EMOJI_WHEN_FADE_IS_UNDER_X_PERCENT and therefore begins as ordinary stylized words before switching to emoji later in the fade.  The currently-sung line always keeps Emojimax, while only the already-sung/fading-out line is allowed to turn emoji back into words according to HIDE_PREVIOUS_EMOJI_WHEN_FADE_IS_UNDER_X_PERCENT.
TITLE_MARQUEE_CHARS_PER_SECOND  = 6.0
TITLE_MARQUEE_REFRESH_SECONDS   = 0.12
LYRIC_TITLE_RETURN_TO_SONG_GAP_SECONDS = 3.0
SONG_RAINBOW_CYCLE_SECONDS      = 14.0 / 1.10
SONG_RAINBOW_THROB_SECONDS      = 3.5 / 1.10
ARTIST_RAINBOW_THROB_SECONDS    = SONG_RAINBOW_THROB_SECONDS / 1.33
SHUFFLE_RAINBOW_THROB_SECONDS   = SONG_RAINBOW_THROB_SECONDS / 3.0  # 50% faster than the previous shuffle pulse
SHUFFLE_RAINBOW_CYCLE_SECONDS   = SONG_RAINBOW_CYCLE_SECONDS / 2.0
SHUFFLE_EXPIRATION_IN_HOURS      = 5.0  # Reuse a completed internally shuffled playlist until this many hours have elapsed, unless the playlist file itself changes first.
PROGRESS_EMPTY_BACKGROUND_BRIGHTNESS_BOOST = 1.08
PLAYING_PATH_RGB                = (105, 235, 145)
NOW_PLAYING_SONG_INFO           = Path(r"C:\mp3\lists\winamp_now_playing.txt")
NOW_PLAYING_ART                 = Path(r"C:\mp3\lists\winamp_now_playing.jpg")
ENABLE_SIXEL_VISUALIZER         = 0
ENABLE_DRCS_VISUALIZER          = 1
DRCS_VISUALIZER_ROWS            = 16
TRUNCATE_TOP_VISUALIZER_LINES   = 1  # Drop this many rarely-hit top spectrum bands without leaving blank terminal rows.
DEFAULT_KARAOKE_VISUALIZER_EXPANSION = True
LYRIC_MAX_UNTIMED_SECONDS       = 15.0
SIXEL_VISUALIZER_ROWS           = 8
STOP                            = "stop"
SEEK_BACK_5                     = "seek-back-5"
SEEK_FORWARD_5                  = "seek-forward-5"
SEEK_BACK_10                    = "seek-back-10"
SEEK_FORWARD_10                 = "seek-forward-10"
SEEK_BACK_15                    = "seek-back-15"
SEEK_FORWARD_15                 = "seek-forward-15"
SEEK_BACK_60                    = "seek-back-60"
SEEK_FORWARD_60                 = "seek-forward-60"
PAUSE_TOGGLE                    = "pause-toggle"
LOOP_TOGGLE                     = "loop-toggle"
VOLUME_UP_5                     = "volume-up-5"
VOLUME_DOWN_5                   = "volume-down-5"
VOLUME_UP_20                    = "volume-up-20"
VOLUME_DOWN_20                  = "volume-down-20"
VOLUME_RESET                    = "volume-reset"
SPEED_UP                        = "speed-up"
SPEED_DOWN                      = "speed-down"
OUTPUT_STEREO                   = "output-stereo"
OUTPUT_51                       = "output-5.1"
OUTPUT_71                       = "output-7.1"
SIXEL_VISUALIZER_TOGGLE         = "sixel-visualizer-toggle"
DRCS_VISUALIZER_TOGGLE          = "drcs-visualizer-toggle"
KARAOKE_VISUALIZER_OVERLAY_TOGGLE = "karaoke-visualizer-overlay-toggle"
ALBUM_ART_VISUALIZER_TOGGLE     = "album-art-visualizer-toggle"
KARAOKE_VISUALIZER_EXPAND_TOGGLE = "karaoke-visualizer-expand-toggle"
RANDOM_TOGGLE                   = "random-toggle"
VISUALIZER_MODE_FIRST           = "visualizer-mode-first"
VISUALIZER_MODE_PREVIOUS        = "visualizer-mode-previous"
VISUALIZER_MODE_NEXT            = "visualizer-mode-next"
VISUALIZER_MODE_FAVORITE        = "visualizer-mode-favorite"
VISUALIZER_FAVORITE_CYCLE       = "visualizer-favorite-cycle"
VISUALIZER_TREATMENT_PREVIOUS   = "visualizer-treatment-previous"
VISUALIZER_TREATMENT_NEXT       = "visualizer-treatment-next"
COLOR_PREVIOUS                  = "color-previous"
COLOR_NEXT                      = "color-next"
FADE_PREVIOUS                   = "fade-previous"
FADE_NEXT                       = "fade-next"
COLOR_FAVORITE_TOGGLE           = "color-favorite-toggle"
COLOR_FAVORITE_CYCLE            = "color-favorite-cycle"
KARAOKE_PREVIOUS                = "karaoke-previous"
KARAOKE_NEXT                    = "karaoke-next"
KARAOKE_TREATMENT_PREVIOUS      = "karaoke-treatment-previous"
KARAOKE_TREATMENT_NEXT          = "karaoke-treatment-next"
KARAOKE_STYLE_MEGAMIX           = "karaoke-style-megamix"
KARAOKE_TREATMENT_MEGAMIX1      = "karaoke-treatment-megamix1"
KARAOKE_TREATMENT_MEGAMIX2      = "karaoke-treatment-megamix2"
KARAOKE_EMOJI_TOGGLE            = "karaoke-emoji-toggle"
KARAOKE_FAVORITE_TOGGLE         = "karaoke-favorite-toggle"
KARAOKE_FAVORITE_CYCLE          = "karaoke-favorite-cycle"
AUTOPLAY_TOGGLE                 = "autoplay-toggle"
PROGRESS_STYLE_PREVIOUS         = "progress-style-previous"
PROGRESS_STYLE_NEXT             = "progress-style-next"
HELP_OVERLAY                    = "help-overlay"
DISMISS_OVERLAY                 = "dismiss-overlay"
FAVORITE_MENU                   = "favorite-menu"
REDRAW_UI                       = "redraw-ui"
LASTFM_SCROBBLE_NOW             = "lastfm-scrobble-now"
GOTO_URL                        = "goto-url"
RESET_DEFAULTS                  = "reset-defaults"
UNDO_RESET_DEFAULTS             = "undo-reset-defaults"
BALANCE_LEFT                    = "balance-left"
BALANCE_RIGHT                   = "balance-right"
BALANCE_CENTER                  = "balance-center"
PREVIOUS_FILE                   = "previous-file"
NEXT_FILE                       = "next-file"
PREVIOUS_DIRECTORY              = "previous-directory"
NEXT_DIRECTORY                  = "next-directory"
PLAYBACK_SPEEDS                 = (0.001, 0.01, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 12.5, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0)
_CURSOR_SUPPRESSION_ACTIVE      = False
BIG_OFF                         = "\033#5"
VOLUME_DRCS_BODY                = "|"
VOLUME_DRCS_UP_WAVES            = "}"
VOLUME_DRCS_DOWN_WAVES          = "~"
DRCS_TILE_CHARS                 = "abcdefghi"
SPECTRUM_ANALYSIS_HEIGHT        = 64
#SPECTRUM_ANALYSIS_FPS          = 25
SPECTRUM_ANALYSIS_FPS           = 60
DEFAULT_VISUALIZER_FADE_SECONDS = 0.08
MARQUEE_ANIMATION_IF_LONGER_THAN = 20
ENABLE_GENRE_EMOJI               = True
TITLE_MARQUEE_WIDTH              = 54
ALBUM_ART_PREVIEW_COLUMNS        = 4
ALBUM_ART_PREVIEW_ROWS           = 4
ALBUM_ART_PREVIEW_MAX_IMAGES     = ALBUM_ART_PREVIEW_COLUMNS * ALBUM_ART_PREVIEW_ROWS
ALBUM_ART_DIVIDER_GUARD_PIXELS   = 2  # Keep the lowest SIXEL pixels from visually bleeding across a following text divider without adding a whole blank terminal row.
ALBUM_ART_IMAGE_EXTENSIONS       = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff"}
# The artwork is composited into the same PNG as the spectrum before Chafa
# encodes it as SIXEL.  Keeping these values here makes the visual treatment
# easy to tune without changing the renderer.
ENABLE_ALBUM_ART_BACKGROUND     = True
ALBUM_ART_BACKGROUND_BRIGHTNESS = 0.22  # 0 = black, 1 = original artwork
ALBUM_ART_SPECTRUM_OPACITY      = 1.0   # 1 = preserve the existing spectrum
AUDIO_EXTENSIONS = {
    ".aac", ".ac3", ".aif", ".aiff", ".alac", ".ape", ".au", ".dsf",
    ".dff", ".flac", ".m4a", ".mka", ".mp2", ".mp3", ".ogg", ".oga",
    ".opus", ".ra", ".shn", ".tta", ".wav", ".wma", ".wv",
}
NAVIGATION_ACTIONS = {
    PREVIOUS_FILE, NEXT_FILE, PREVIOUS_DIRECTORY, NEXT_DIRECTORY,
}
_AUDIO_DIRECTORY_CACHE: dict[Path, list[tuple[Path, list[Path]]]] = {}
_ALBUM_ART_BYTES_CACHE: dict[tuple[str, int, int], bytes | None] = {}
_ASYNC_KEY_LATCH: set[int] = set()
_ASYNC_EXTENDED_SUPPRESS_ONCE: dict[str, float] = {}
_ASYNC_HOLD_STARTED: dict[str, float] = {}
_ASYNC_HOLD_STAGE: dict[str, int] = {}
VISUALIZER_TYPE_NAMES = (
    "Classic", "Legacy Classic", "Eighth Blocks", "Soft Blocks", "Dense Blocks",
    "Half Blocks", "Thin Blocks", "Wide Blocks", "Shaded Columns", "Stepped Columns",
    "Braille", "Dots", "Circles", "Diamonds", "Runes", "Stars", "Math Symbols",
    "Gothic Marks", "Sparkles", "ASCII Fine", "ASCII Heavy", "Digital", "Needles",
    "Rounded", "Minimal",
)
VISUALIZER_TREATMENT_NAMES = (
    "Punch", "Balanced", "Soft", "Tight", "Smooth", "Pulse", "Skyline", "Peaks",
    "Compressed", "Expanded", "Transient", "Valleys", "Wide", "Hot", "Quiet",
)
VISUALIZER_MODE_NAMES = tuple(
    f"{type_name} + {treatment_name}"
    for treatment_name in VISUALIZER_TREATMENT_NAMES
    for type_name in VISUALIZER_TYPE_NAMES
)
VISUALIZER_GLYPH_PALETTES = (
    "abcdefghi", "abcdefghi", " ▁▂▃▄▅▆▇█", "  ░░▒▒▓▓█", " ·∙•●◉◉██",
    " .:-=+*#@", " 12345678", " abcdefgh", " ○◔◑◕●◉██", " ◌○◍◎●◉██",
    " ᛫᛬᛭ᛮᛯᛰ██", " ⠁⠃⠇⡇⣇⣧⣷█", " ･·•●◆◈██", " ˙·∙•●⬤██", " ⌞⌜╞╠╬▓██",
    " _▁▂▃▄▆▇█", " .oO0@#██", " ,;irsXA#", " `'^~*=#@", " ㆍ◦○◉●◆██",
    " ︱▏▎▍▌▋▊█", " ︳┃┃╋╋▓██", " ⋅∘∙●◉⬢██", " ｡ﾟ･:*:▓█", " .·°º¤ø██",
)
COLOR_STYLE_NAMES = (
    "Color 01", "Color 02", "Color 03", "Color 04", "Color 05", "Color 06",
    "Color 07", "Color 08", "Color 09", "Color 10", "Color 11", "Color 12",
    "Color 13 Horizon", "Color 14 Horizon", "Color 15 Prism", "Color 16 Horizon",
    "Color 17 Horizon", "Color 18 Horizon",
    "Color 19", "Color 20", "Color 21", "Color 22", "Color 23", "Color 24",
    "Color 25", "Color 26", "Color 27", "Color 28", "Color 29", "Color 30",
    "Color 31 Amplitude", "Color 32 Red-Purple",
)
KARAOKE_LEGACY_STYLES = (11, 12, 13, 16, 17, 21, 22, 24, 26, 36, 37, 39, 41, 42, 46)

PROGRESS_STYLE_NAMES = tuple(f"Progress {number:02d}" for number in range(1, 26))
FADE_STYLE_NAMES = ("Energy dim", "ROYGBIV decay", "Hard cutoff", "Pulse decay")



semantic_OLD_v1 = {
    "love": "❤️", "heart": "💗", "fire": "🔥", "star": "🌟", "stars": "✨",
    "sun": "☀️", "moon": "🌙", "world": "🌍", "earth": "🌎", "home": "🏠",
    "music": "🎶", "song": "🎵", "dance": "💃", "dancing": "💃", "party": "🎉",
    "cry": "😭", "crying": "😭", "tears": "😢", "smile": "😊", "laugh": "😂",
    "kiss": "💋", "baby": "👶", "girl": "👧", "boy": "👦", "man": "👨",
    "woman": "👩", "eyes": "👀", "eye": "👁️", "night": "🌃", "rain": "🌧️",
    "snow": "❄️", "money": "💰", "time": "⏳", "phone": "📱", "car": "🚗",
    "train": "🚆", "plane": "✈️", "devil": "😈", "angel": "😇", "dead": "💀",
    "death": "💀", "broken": "💔", "king": "👑", "queen": "👑",
}
# semantic_expanded.py
#
# Expanded semantic emoji / Unicode-symbol replacement table.
# Built against:
#   - COCA Top-5000 frequency dataset (5050 ranked POS rows)
#   - Unicode Emoji 17.0 emoji-test.txt short names
#   - Unicode 17.0 UnicodeData.txt symbol names
#
# Quality rule:
#   Prefer a meaningful emoji; use an ordinary Unicode symbol when it conveys
#   an abstract concept better; leave meaningless function-word matches alone.
#
# Special requested behavior:
#   moist -> 💦
#   heel  -> 👠
#   heels -> 👠👠
#   skull -> 💀
#   dead  -> ☠️
#   death -> ⚰️
#
# Total entries: 794
#
semantic = {'address': '📍',
         'adult': '🧑',
         'afraid': '😨',
         'african': '🌍',
         'airplane': '✈️',
         'airport': '🛫',
         'alarm': '⏰',
         'alien': '👽',
         'ambulance': '🚑',
         'anchor': '⚓',
         'and': '&',
         'angel': '😇',
         'anger': '😡',
         'angle': '∠',
         'angry': '😠',
         'answer': '💬',
         'ant': '🐜',
         'anxious': '😰',
         'apple': '🍎',
         'approximate': '≈',
         'approximately': '≈',
         'arm': '💪',
         'arms': '💪',
         'art': '🎨',
         'artist': '🧑\u200d🎨',
         'astronaut': '🧑\u200d🚀',
         'at': '@',
         'attachment': '📎',
         'avocado': '🥑',
         'baby': '👶',
         'back': '🔙',
         'backpack': '🎒',
         'backward': '⏪',
         'bacon': '🥓',
         'bag': '👜',
         'ball': '⚽',
         'balloon': '🎈',
         'banana': '🍌',
         'bandage': '🩹',
         'bank': '🏦',
         'bar': '🍫',
         'baseball': '⚾',
         'basket': '🧺',
         'basketball': '🏀',
         'bat': '🦇',
         'battery': '🔋',
         'beach': '🏖️',
         'bear': '🐻',
         'because': '∵',
         'bed': '🛏️',
         'bee': '🐝',
         'beer': '🍺',
         'bell': '🔔',
         'bicycle': '🚲',
         'bike': '🚲',
         'bikini': '👙',
         'bird': '🐦',
         'birthday': '🎂',
         'black': '⚫',
         'blood': '🩸',
         'blue': '🔵',
         'blueberry': '🫐',
         'boat': '⛵',
         'bomb': '💣',
         'bone': '🦴',
         'bones': '🦴',
         'book': '📖',
         'books': '📚',
         'boot': '🥾',
         'boots': '🥾🥾',
         'bowl': '🥣',
         'box': '📦',
         'boxing': '🥊',
         'boy': '👦',
         'brain': '🧠',
         'bread': '🍞',
         'brick': '🧱',
         'bridge': '🌉',
         'bright': '🔆',
         'british': '🇬🇧',
         'broken': '💔',
         'brown': '🟤',
         'bucket': '🪣',
         'bug': '🐛',
         'building': '🏢',
         'bulb': '💡',
         'bull': '🐂',
         'bullet': '•',
         'burger': '🍔',
         'burrito': '🌯',
         'bus': '🚌',
         'business': '💼',
         'butter': '🧈',
         'butterfly': '🦋',
         'cake': '🎂',
         'calendar': '📅',
         'call': '📞',
         'camera': '📷',
         'candle': '🕯️',
         'candy': '🍬',
         'cap': '🧢',
         'car': '🚗',
         'card': '💳',
         'carrot': '🥕',
         'cars': '🚗🚗',
         'cash': '💵',
         'castle': '🏰',
         'cat': '🐱',
         'cats': '🐱🐱',
         'celebrate': '🎉',
         'celebration': '🎊',
         'chain': '⛓️',
         'chair': '🪑',
         'chart': '📊',
         'chat': '💬',
         'check': '✅',
         'cheese': '🧀',
         'chef': '🧑\u200d🍳',
         'cherries': '🍒',
         'cherry': '🍒',
         'chess': '♟️',
         'chicken': '🐔',
         'child': '🧒',
         'children': '🧒',
         'chocolate': '🍫',
         'church': '⛪',
         'cigarette': '🚬',
         'circle': '⭕',
         'city': '🏙️',
         'clip': '📎',
         'clock': '🕒',
         'clothes': '👚',
         'clothing': '👚',
         'cloud': '☁️',
         'clouds': '☁️',
         'clown': '🤡',
         'coat': '🧥',
         'coconut': '🥥',
         'coffee': '☕',
         'coffin': '⚰️',
         'coin': '🪙',
         'coins': '🪙🪙',
         'cold': '🥶',
         'comet': '☄️',
         'computer': '💻',
         'confused': '😕',
         'confusion': '😕',
         'construction': '🚧',
         'contact': '📇',
         'controller': '🎮',
         'cook': '🧑\u200d🍳',
         'cookie': '🍪',
         'cooking': '🍳',
         'cool': '😎',
         'cop': '👮',
         'copyright': '©',
         'corn': '🌽',
         'correct': '✅',
         'couple': '💑',
         'cover': '📔',
         'cow': '🐄',
         'crab': '🦀',
         'crazy': '🤪',
         'credit': '💳',
         'cross': '❌',
         'crown': '👑',
         'cry': '😭',
         'crying': '😭',
         'cup': '🥤',
         'dad': '👨',
         'daddy': '👨',
         'dance': '💃',
         'dancing': '💃',
         'danger': '⚠️',
         'dark': '🌑',
         'date': '📅',
         'dead': '☠️',
         'deadly': '☠️',
         'death': '⚰️',
         'decline': '📉',
         'deer': '🦌',
         'degree': '°',
         'delete': '🗑️',
         'department': '🏬',
         'desert': '🏜️',
         'desktop': '🖥️',
         'detective': '🕵️',
         'devil': '😈',
         'diamond': '🔷',
         'dice': '🎲',
         'die': '⚰️',
         'dinosaur': '🦖',
         'disk': '💾',
         'divide': '➗',
         'dizzy': '😵\u200d💫',
         'dna': '🧬',
         'doctor': '🧑\u200d⚕️',
         'document': '📄',
         'dog': '🐶',
         'dogs': '🐶🐶',
         'dollar': '💵',
         'dollars': '💵',
         'dolphin': '🐬',
         'door': '🚪',
         'down': '⬇️',
         'dragon': '🐉',
         'dream': '💭',
         'dreaming': '💭',
         'dress': '👗',
         'drink': '🥤',
         'drop': '💧',
         'drops': '💧💧💧',
         'drum': '🥁',
         'drums': '🥁',
         'duck': '🦆',
         'dying': '🪦',
         'e-mail': '📧',
         'eagle': '🦅',
         'ear': '👂',
         'ears': '👂👂',
         'earth': '🌎',
         'east': '→',
         'egg': '🥚',
         'eggplant': '🍆',
         'eggs': '🥚🥚',
         'elder': '🧓',
         'elephant': '🐘',
         'elevator': '🛗',
         'email': '📧',
         'embarrassed': '😳',
         'empty': '∅',
         'end': '🔚',
         'envelope': '✉️',
         'equal': '=',
         'equals': '=',
         'error': '❌',
         'european': '🇪🇺',
         'exchange': '🔄',
         'eye': '👁️',
         'eyes': '👀',
         'face': '🙂',
         'factory': '🏭',
         'fall': '📉',
         'false': '❌',
         'family': '👪',
         'fan': '🪭',
         'farmer': '🧑\u200d🌾',
         'fast': '⚡',
         'father': '👨',
         'fear': '😨',
         'feet': '🦶🦶',
         'female': '♀',
         'ferry': '⛴️',
         'fever': '🤒',
         'field': '🌾',
         'fight': '\U0001f94a',
         'file': '📁',
         'film': '🎞️',
         'find': '🔎',
         'finger': '☝️',
         'fingers': '🖐️',
         'fire': '🔥',
         'firefighter': '🧑\u200d🚒',
         'firetruck': '🚒',
         'fish': '🐟',
         'flame': '🔥',
         'flashlight': '🔦',
         'flight': '✈️',
         'flirt': '😉',
         'floor': '🪵',
         'flower': '🌸',
         'flowers': '💐',
         'fly': '🪰',
         'fog': '🌫️',
         'folder': '📁',
         'food': '🍽️',
         'foot': '🦶',
         'football': '🏈',
         'forest': '🌲',
         'forever': '∞',
         'forward': '⏩',
         'fox': '🦊',
         'free': '🆓',
         'french': '🇫🇷',
         'fries': '🍟',
         'frightened': '😱',
         'frog': '🐸',
         'fuel': '⛽',
         'full': '🌕',
         'funeral': '⚰️',
         'funny': '🤣',
         'furious': '🤬',
         'game': '🎮',
         'games': '🎮',
         'garden': '🪴',
         'garlic': '🧄',
         'gas': '⛽',
         'gear': '⚙️',
         'ghost': '👻',
         'gift': '🎁',
         'girl': '👧',
         'glass': '🥛',
         'glasses': '👓',
         'globe': '🌐',
         'go': '🟢',
         'goal': '🥅',
         'goat': '🐐',
         'golf': '⛳',
         'graduate': '🎓',
         'graduation': '🎓',
         'grandfather': '👴',
         'grandma': '👵',
         'grandmother': '👵',
         'grandpa': '👴',
         'grape': '🍇',
         'grapes': '🍇',
         'graph': '📈',
         'grass': '🌿',
         'grave': '🪦',
         'greater': '>',
         'green': '🟢',
         'grin': '😁',
         'ground': '🌍',
         'growth': '📈',
         'guard': '💂',
         'guitar': '🎸',
         'gun': '🔫',
         'hair': '💇',
         'hamburger': '🍔',
         'hammer': '🔨',
         'hand': '✋',
         'hands': '🙌',
         'happiness': '😊',
         'happy': '😊',
         'hat': '🎩',
         'hats': '🎩🎩',
         'head': '👤',
         'health': '⚕️',
         'heart': '💗',
         'heartbreak': '💔',
         'hearts': '💕',
         'heel': '👠',
         'heels': '👠👠',
         'helicopter': '🚁',
         'help': '🆘',
         'herb': '🌿',
         'high': '🔆',
         'hole': '🕳️',
         'home': '🏠',
         'honey': '🍯',
         'hook': '🪝',
         'hope': '🤞',
         'horse': '🐴',
         'hospital': '🏥',
         'hot': '🥵',
         'hotdog': '🌭',
         'hotel': '🏨',
         'house': '🏠',
         'hug': '🤗',
         'hugging': '🫂',
         'hundred': '💯',
         'hurt': '🤕',
         'ice': '🧊',
         'icecream': '🍨',
         'idea': '💡',
         'ill': '🤒',
         'inbox': '📥',
         'infinity': '∞',
         'info': 'ℹ️',
         'information': 'ℹ️',
         'injury': '🤕',
         'integral': '∫',
         'internet': '🌐',
         'intersection': '∩',
         'island': '🏝️',
         'jar': '🫙',
         'jeans': '👖',
         'job': '💼',
         'join': '🔗',
         'joy': '😂',
         'judge': '🧑\u200d⚖️',
         'key': '🔑',
         'keyboard': '⌨️',
         'keys': '🔑',
         'king': '🤴',
         'kiss': '💋',
         'kissing': '😘',
         'knife': '🔪',
         'koala': '🐨',
         'label': '🏷️',
         'lake': '🏞️',
         'laptop': '💻',
         'laugh': '😂',
         'laughing': '😂',
         'leaf': '🍃',
         'leaves': '🍂',
         'left': '⬅️',
         'leg': '🦵',
         'legs': '🦵🦵',
         'lemon': '🍋',
         'less': '<',
         'letter': '✉️',
         'level': '🎚️',
         'liar': '🤥',
         'lie': '🤥',
         'light': '💡',
         'lightning': '⚡',
         'line': '―',
         'link': '🔗',
         'lion': '🦁',
         'lip': '👄',
         'lips': '👄',
         'lizard': '🦎',
         'lobster': '🦞',
         'location': '📍',
         'lock': '🔒',
         'locked': '🔒',
         'love': '❤️',
         'loveletter': '💌',
         'low': '🔅',
         'luck': '🍀',
         'lucky': '🍀',
         'luggage': '🧳',
         'lungs': '🫁',
         'machine': '⚙️',
         'mad': '😡',
         'magnet': '🧲',
         'mail': '✉️',
         'male': '♂',
         'man': '👨',
         'map': '🗺️',
         'meat': '🥩',
         'mechanic': '🧑\u200d🔧',
         'medal': '🏅',
         'medical': '⚕️',
         'medicine': '💊',
         'melon': '🍈',
         'message': '💬',
         'microphone': '🎤',
         'military': '🪖',
         'milk': '🥛',
         'mirror': '🪞',
         'mobile': '📱',
         'moist': '💦',
         'mom': '👩',
         'mommy': '👩',
         'money': '💰',
         'monkey': '🐒',
         'moon': '🌙',
         'mosque': '🕌',
         'mother': '👩',
         'motorcycle': '🏍️',
         'mountain': '⛰️',
         'mountains': '🏔️',
         'mouse': '🖱️',
         'mouth': '👄',
         'movie': '🎬',
         'muscle': '💪',
         'mushroom': '🍄',
         'music': '🎶',
         'nausea': '🤢',
         'nauseous': '🤢',
         'nerd': '🤓',
         'nervous': '😬',
         'network': '🌐',
         'new': '🆕',
         'news': '📰',
         'newspaper': '📰',
         'next': '⏭️',
         'no': '🚫',
         'noodle': '🍜',
         'noodles': '🍜',
         'north': '↑',
         'nose': '👃',
         'note': '📝',
         'notes': '📝',
         'number': '#',
         'nurse': '🧑\u200d⚕️',
         'ocean': '🌊',
         'octopus': '🐙',
         'off': '📴',
         'office': '🏢',
         'officer': '👮',
         'oil': '🛢️',
         'ok': '👌',
         'okay': '👌',
         'olive': '🫒',
         'onion': '🧅',
         'online': '🌐',
         'open': '📂',
         'orange': '🟠',
         'outbox': '📤',
         'owl': '🦉',
         'package': '📦',
         'page': '📄',
         'pain': '🤕',
         'paint': '🎨',
         'panda': '🐼',
         'pants': '👖',
         'paper': '📄',
         'paragraph': '¶',
         'parallel': '∥',
         'park': '🏞️',
         'party': '🎉',
         'pause': '⏸️',
         'peace': '☮️',
         'peach': '🍑',
         'pen': '🖊️',
         'pencil': '✏️',
         'penguin': '🐧',
         'people': '👥',
         'pepper': '🌶️',
         'percent': '%',
         'perpendicular': '⊥',
         'person': '🧑',
         'phone': '📱',
         'photo': '📸',
         'piano': '🎹',
         'picture': '🖼️',
         'pie': '🥧',
         'piece': '🧩',
         'pig': '🐷',
         'piggy': '🐷',
         'pigs': '🐷🐷',
         'pill': '💊',
         'pills': '💊💊',
         'pilot': '🧑\u200d✈️',
         'pineapple': '🍍',
         'pizza': '🍕',
         'plane': '✈️',
         'planet': '🪐',
         'plant': '🌱',
         'play': '▶️',
         'plug': '🔌',
         'plus': '➕',
         'police': '👮',
         'post': '📮',
         'potato': '🥔',
         'pray': '🙏',
         'prayer': '🙏',
         'present': '🎁',
         'previous': '⏮️',
         'prince': '🤴',
         'princess': '👸',
         'printer': '🖨️',
         'product': '∏',
         'purple': '🟣',
         'purse': '👛',
         'pushpin': '📌',
         'queen': '👸',
         'question': '❓',
         'quiet': '🤫',
         'rabbit': '🐰',
         'race': '🏁',
         'radio': '📻',
         'rage': '🤬',
         'rain': '🌧️',
         'rainy': '🌧️',
         'rat': '🐀',
         'receive': '📥',
         'record': '⏺️',
         'red': '🔴',
         'refresh': '🔄',
         'registered': '®',
         'repeat': '🔁',
         'response': '💬',
         'rice': '🍚',
         'right': '➡️',
         'ring': '💍',
         'rings': '💍💍',
         'rise': '📈',
         'rising': '📈',
         'river': '🏞️',
         'road': '🛣️',
         'robot': '🤖',
         'rock': '🪨',
         'rocket': '🚀',
         'romance': '💞',
         'romantic': '💞',
         'root': '√',
         'rose': '🌹',
         'sad': '😢',
         'sadness': '😢',
         'safety': '🦺',
         'salad': '🥗',
         'salt': '🧂',
         'sandwich': '🥪',
         'satellite': '🛰️',
         'save': '💾',
         'saxophone': '🎷',
         'scale': '⚖️',
         'scared': '😱',
         'school': '🏫',
         'scientist': '🧑\u200d🔬',
         'scissors': '✂️',
         'score': '🎼',
         'screen': '🖥️',
         'sea': '🌊',
         'seal': '🦭',
         'search': '🔍',
         'seat': '💺',
         'section': '§',
         'seed': '🌱',
         'send': '📤',
         'shark': '🦈',
         'shield': '🛡️',
         'ship': '🚢',
         'shirt': '👕',
         'shock': '😲',
         'shocked': '😲',
         'shoe': '👟',
         'shoes': '👟👟',
         'shop': '🛍️',
         'shower': '🚿',
         'shuffle': '🔀',
         'shy': '🫣',
         'sick': '🤒',
         'silence': '🤫',
         'silent': '🤐',
         'sing': '🎤',
         'singer': '🎤',
         'skull': '💀',
         'sky': '🌌',
         'sleep': '😴',
         'sleeping': '😴',
         'sleepy': '😴',
         'smile': '😊',
         'smiling': '😊',
         'snail': '🐌',
         'snake': '🐍',
         'snakes': '🐍🐍🐍',
         'sneeze': '🤧',
         'sneezing': '🤧',
         'snow': '❄️',
         'snowy': '🌨️',
         'soap': '🧼',
         'soccer': '⚽',
         'sock': '🧦',
         'socks': '🧦',
         'soldier': '🪖',
         'song': '🎵',
         'songs': '🎶',
         'soon': '🔜',
         'sound': '🔊',
         'soup': '🍲',
         'south': '↓',
         'space': '🌌',
         'spaghetti': '🍝',
         'sparkle': '✨',
         'sparkles': '✨',
         'speak': '🗣️',
         'speaker': '🔊',
         'speech': '🗣️',
         'spider': '🕷️',
         'sport': '🏅',
         'spy': '🕵️',
         'square': '⬜',
         'stadium': '🏟️',
         'star': '⭐',
         'stars': '🌠',
         'start': '▶️',
         'station': '🚉',
         'stone': '🪨',
         'stop': '🛑',
         'store': '🏬',
         'storm': '⛈️',
         'straight': '➡️',
         'strawberry': '🍓',
         'street': '🛣️',
         'stress': '😫',
         'stressed': '😫',
         'student': '🧑\u200d🎓',
         'subway': '🚇',
         'suitcase': '🧳',
         'sum': '∑',
         'sun': '☀️',
         'sunflower': '🌻',
         'sunglasses': '🕶️',
         'sunny': '☀️',
         'sunrise': '🌅',
         'sunset': '🌇',
         'surprise': '😮',
         'surprised': '😮',
         'sushi': '🍣',
         'sweaty': '💦',
         'moist': '💦',                
         'sweet': '🍭',
         'sweets': '🍭',
         'sword': '⚔️',
         't-shirt': '👕',
         'taco': '🌮',
         'talk': '🗣️',
         'taxi': '🚕',
         'tea': '🍵',
         'teacher': '🧑\u200d🏫',
         'tear': '😢',
         'tears': '😢',
         'teeth': '🦷',
         'telephone': '☎️',
         'telescope': '🔭',
         'television': '📺',
         'temple': '🛕',
         'tennis': '🎾',
         'tent': '⛺',
         'test': '🧪',
         'theater': '🎭',
         'therefore': '∴',
         'think': '🤔',
         'thinking': '🤔',
         'thought': '💭',
         'thread': '🧵',
         'thumb': '👍',
         'thunder': '⛈️',
         'ticket': '🎫',
         'tiger': '🐯',
         'time': '⏳',
         'tired': '😫',
         'together': '🫂',
         'toilet': '🚽',
         'tomato': '🍅',
         'tongue': '👅',
         'tool': '🛠️',
         'tools': '🛠️',
         'tooth': '🦷',
         'top': '🔝',
         'tornado': '🌪️',
         'town': '🏘️',
         'track': '🛤️',
         'trademark': '™',
         'train': '🚆',
         'tram': '🚊',
         'trash': '🗑️',
         'travel': '🧳',
         'tree': '🌳',
         'trees': '🌲',
         'triangle': '🔺',
         'trophy': '🏆',
         'truck': '🚚',
         'true': '✅',
         'trumpet': '🎺',
         'tshirt': '👕',
         'turkey': '🦃',
         'turtle': '🐢',
         'tv': '📺',
         'unicorn': '🦄',
         'union': '∪',
         'unlock': '🔓',
         'unlocked': '🔓',
         'up': '⬆️',
         'vampire': '🧛',
         'vehicle': '🚙',
         'victory': '✌️',
         'video': '📹',
         'violin': '🎻',
         'volcano': '🌋',
         'volleyball': '🏐',
         'volume': '🔊',
         'vomit': '🤮',
         'warning': '⚠️',
         'watch': '⌚',
         'water': '💧',
         'watermelon': '🍉',
         'wave': '🌊',
         'web': '🌐',
         'wedding': '💒',
         'west': '←',
         'wet': '💦',
         'whale': '🐋',
         'wheel': '🛞',
         'white': '⚪',
         'win': '🏆',
         'wind': '💨',
         'window': '🪟',
         'windy': '💨',
         'wine': '🍷',
         'wing': '🪽',
         'wink': '😉',
         'winking': '😉',
         'winner': '🏆',
         'wolf': '🐺',
         'woman': '👩',
         'wonder': '🤔',
         'wood': '🪵',
         'work': '💼',
         'worker': '👷',
         'world': '🌍',
         'worried': '😟',
         'worry': '😟',
         'wrench': '🔧',
         'writer': '✍️',
         'writing': '✍️',
         'wrong': '❌',
         'yellow': '🟡',
         'yes': '✅',
         'zombie': '🧟',
         'zoom': '🔎'
}
semantic.update({
    "pirate": "🏴‍☠️",
    "milk": "\U0001f95b", "surrender": "\U0001f3f3\ufe0f",
    "red flag": "\U0001f6a9", "redflag": "\U0001f6a9",
    "go": "🟢", "wet": "💧", "umbrella": "☔️", "enterprise": "🏢",
    "life": "🌱", "mind": "🧠", "head": "🗣️", "day": "📆", "end": "🔚",
    "way": "🛣️", "bad": "👎", "good": "👍", "no": "🚫", "right": "👉",
    "left": "👈", "up": "⬆️", "down": "⬇️", "away": "👋", 
    "think": "💭", "know": "💡", "say": "🗣️", "tell": "📣", "make": "🛠️",
    "come": "🫄", "take": "🤲", "die": "💀", "lost": "🧭", "scissor": "✂", "cut": "✂",
    "alone": "🧍", "one": "❶", "two": "❷", "three": "❸", "four": "❹", "five": "❺",
    "six": "❻", "seven": "❼", "eight": "❽", "nine": "❾", "ten": "❿",
    "1": "❶", "2": "❷", "3": "❸", "4": "❹", "5": "❺", "6": "❻", "7": "❼", "8": "❽", "9": "❾", "10": "❿",
    "infinite": "♾️", "infinitely": "♾️", "beginning": "🌅",
    "dream": "💭", "hope": "🤞", "sorry": "🙏", "thanks": "🙏", "thank": "🙏",
    "please": "🙏", "friend": "🫂", "friends": "🫂", "run": "🏃", "running": "🏃",
    "walk": "🚶", "walking": "🚶", "dancefloor": "🪩", "street": "🛣️",
    "lake": "🏞️", "sea": "🌊", "mountain": "⛰️", "sky": "🌌",
    "cloud": "☁️", "storm": "⛈️", "wind": "🌬️", "light": "💡", "dark": "🌑",
    "shadow": "👤", "voice": "🗣️", "mail": "📨", "letters": "🔤", "end": "🔚",
    "lie": "🤨", "lies": "🤨",  "cents": "¢", "cent": "¢", "bang": "💥", "!!": "‼"
})
# Force the glyphs that render correctly in Windows Terminal double-height mode.
semantic["world"] = "🌍"
semantic["snake"] = "🐍"
semantic["snakes"] = "🐍🐍🐍"
semantic.pop("fan", None)  # A fan is too ambiguous for Emojimax substitution.
SEMANTIC_PHRASES = {
    "!!!!": "‼‼",
    "beach umbrella": "🏖️", "love": "💞", "my heart": "💗", "no one": "🚫👤",
     "goodbye": "👋", 
    "i'm sorry": "🙏", "thank you": "🙏", "don't know": "🤷", "come on": "👉",
    "so many": "🔢", "too dead": "💀", "lost mind": "🧠", "one of": "❶ of", "one more": "➕ ❶",
    "forever young": "♾️👶", "on fire": "🔥", "fall in love": "💘",
}

KARAOKE_STYLE_NAMES = (
    "Plain", "Fraktur", "Fraktur Clean", "Fraktur Framed",
    "Circled", "Circled Clean", "Cursive", "Cursive Clean",
    "Cursive Framed", "Uppercase", "Greek", "Greek Clean",
    "Greek Framed", "Leetspeak", "Leetspeak Clean", "Symbol Mix",
    "Unicode Sans", "Enclosed Letters", "Closest Unicode", "Script", "Megamix",
)
KARAOKE_TREATMENT_NAMES = (
    "Readable Solid", "Line Rainbow", "Word Rainbow",
    "Random Letter Color", "Hashed Word Color", "Megamix1", "Megamix2",
)

def _legacy_karaoke_text(text: str, style: int) -> str:
    """Render one of the original fifty styles by its original number."""
    style = (style - 1) % 50
    family, decoration = divmod(style, 5)
    upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    lower = "abcdefghijklmnopqrstuvwxyz"
    targets = (
        upper + lower,
        "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ",
        "𝐀𝐁𝐂𝐃𝐄𝐅𝐆𝐇𝐈𝐉𝐊𝐋𝐌𝐍𝐎𝐏𝐐𝐑𝐒𝐓𝐔𝐕𝐖𝐗𝐘𝐙𝐚𝐛𝐜𝐝𝐞𝐟𝐠𝐡𝐢𝐣𝐤𝐥𝐦𝐧𝐨𝐩𝐪𝐫𝐬𝐭𝐮𝐯𝐰𝐱𝐲𝐳",
        "𝔄𝔅ℭ𝔇𝔈𝔉𝔊ℌℑ𝔍𝔎𝔏𝔐𝔑𝔒𝔓𝔔ℜ𝔖𝔗𝔘𝔙𝔚𝔛𝔜ℨ𝔞𝔟𝔠𝔡𝔢𝔣𝔤𝔥𝔦𝔧𝔨𝔩𝔪𝔫𝔬𝔭𝔮𝔯𝔰𝔱𝔲𝔳𝔴𝔵𝔶𝔷",
        "ⒶⒷⒸⒹⒺⒻⒼⒽⒾⒿⓀⓁⓂⓃⓄⓅⓆⓇⓈⓉⓊⓋⓌⓍⓎⓏⓐⓑⓒⓓⓔⓕⓖⓗⓘⓙⓚⓛⓜⓝⓞⓟⓠⓡⓢⓣⓤⓥⓦⓧⓨⓩ",
        "𝓐𝓑𝓒𝓓𝓔𝓕𝓖𝓗𝓘𝓙𝓚𝓛𝓜𝓝𝓞𝓟𝓠𝓡𝓢𝓣𝓤𝓥𝓦𝓧𝓨𝓩𝓪𝓫𝓬𝓭𝓮𝓯𝓰𝓱𝓲𝓳𝓴𝓵𝓶𝓷𝓸𝓹𝓺𝓻𝓼𝓽𝓾𝓿𝔀𝔁𝔂𝔃",
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
    )        
    family %= 10
    if family < len(targets):
        result = text.translate(str.maketrans(upper + lower, targets[family]))
    elif family == 5:
        result = text.upper()
    elif family == 6:
        result = text.title()
    elif family == 7:
        result = text.translate(str.maketrans("AEIOUaeiou", "ΛΞΙΘЦλξιθц"))
    elif family == 8:
        result = text.translate(str.maketrans("AEIOSTaeiost", "431057431057"))
    else:
        result = text.translate(str.maketrans({
            "A": "🅰", "a": "🅰", "B": "🅱", "b": "🅱", "E": "ℰ", "e": "ℰ",
            "I": "ℐ", "i": "ℐ", "O": "⭕", "o": "⭕", "P": "🅿", "p": "🅿",
            "S": "§", "T": "✝", "X": "❌", "a": "🅰", "b": "🅱", "e": "ℰ",
            "i": "ℐ", "o": "⭕", "p": "🅿", "s": "§", "t": "✝", "x": "❌",
            "U": "𝒰", "u": "𝒰",
        }))
    if decoration == 1:
        result = " ".join(result)
    elif decoration == 2:
        result = f"✦ {result} ✦"
    elif decoration == 3:
        result = f"⸎ {result} ⸎"
    elif decoration == 4:
        result = f"🎤 {result} 🎤"
    return result


def stylize_karaoke_text(text: str, style: int) -> str:
    """Apply a retained or purpose-built karaoke glyph style."""
    global semantic
    index = (style - 1) % len(KARAOKE_STYLE_NAMES)
    if index == 0:
        return text
    index -= 1
    if index < len(KARAOKE_LEGACY_STYLES):
        return _legacy_karaoke_text(text, KARAOKE_LEGACY_STYLES[index])
    mode = index - len(KARAOKE_LEGACY_STYLES)
    if mode == 0:
        table = {
            **{chr(65 + offset): chr(0x1D5D4 + offset) for offset in range(26)},
            **{chr(97 + offset): chr(0x1D5EE + offset) for offset in range(26)},
        }
        return text.translate(str.maketrans(table))
    if mode == 1:
        table = {
            **{chr(65 + offset): chr(0x24B6 + offset) for offset in range(26)},
            **{chr(97 + offset): chr(0x24D0 + offset) for offset in range(26)},
        }
        return text.translate(str.maketrans(table))
    if mode == 2:
        close = {
            "A": "🅰", "a": "🅰", "B": "🅱", "b": "🅱", "E": "ℰ", "e": "ℰ",
            "I": "ℐ", "i": "ℐ", "O": "⭕", "o": "⭕", "P": "🅿", "p": "🅿",
            "S": "§", "T": "✝", "X": "❌", "a": "🅰", "b": "🅱", "e": "ℰ",
            "i": "ℐ", "o": "⭕", "p": "🅿", "s": "§", "t": "✝", "x": "❌",
            "U": "𝒰", "u": "𝒰",
        }
        return text.translate(str.maketrans(close))
    if mode == 3:
        return _legacy_karaoke_text(text, 21)
    pieces = re.split(r"(\s+)", text)
    base_style_count = len(KARAOKE_STYLE_NAMES) - 1
    return "".join(
        piece if not piece.strip() else stylize_karaoke_text(
            piece,
            int(hashlib.sha256(f"{index}:{piece}".encode("utf-8")).hexdigest(), 16)
            % base_style_count + 1,
        )
        for index, piece in enumerate(pieces)
    )


def stylize_karaoke_with_emojimax(
    text: str,
    style: int,
    enabled: bool,
    opacity: float = 1.0,
    *,
    force_emoji_when_enabled: bool = False,
    fade_threshold_percent: float | None = None,
) -> str:
    """Apply semantic emoji; the sung line keeps emoji while neighbors obey fade thresholds."""
    threshold = (
        HIDE_EMOJI_WHEN_FADE_IS_UNDER_X_PERCENT
        if fade_threshold_percent is None else float(fade_threshold_percent)
    )
    emoji_visible = bool(
        enabled
        and (
            force_emoji_when_enabled
            or max(0.0, min(1.0, opacity)) * 100.0 >= threshold
        )
    )
    if not emoji_visible:
        return stylize_karaoke_text(text, style)
    protected = text
    phrase_tokens: dict[str, str] = {}
    for index, (phrase, replacement) in enumerate(SEMANTIC_PHRASES.items()):
        token = "\ue000" + chr(0xE100 + index) + "\ue001"
        replaced = re.sub(re.escape(phrase), token, protected, flags=re.IGNORECASE)
        if replaced != protected:
            phrase_tokens[token] = replacement
            protected = replaced
    pieces: list[str] = []
    cursor = 0
    for match in re.finditer(r"\b[\w’']+\b", protected):
        pieces.append(stylize_karaoke_text(protected[cursor:match.start()], style))
        word = match.group(0)
        pieces.append(semantic.get(word.casefold(), stylize_karaoke_text(word, style)))
        cursor = match.end()
    pieces.append(stylize_karaoke_text(protected[cursor:], style))
    result = "".join(pieces)
    for token, replacement in phrase_tokens.items():
        result = result.replace(stylize_karaoke_text(token, style), replacement).replace(token, replacement)
    return result




def registry_favorites(name: str) -> list[int]:
    if os.name != "nt":
        return []
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\ClaireCJS\play_audio_file") as key:
            value, _kind = winreg.QueryValueEx(key, name)
        return [int(item) for item in str(value).split(",") if item.strip().isdigit()]
    except OSError:
        return []


def save_registry_favorites(name: str, values: list[int]) -> None:
    if os.name != "nt":
        return
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\ClaireCJS\play_audio_file") as key:
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, ",".join(map(str, sorted(set(values)))))


PLAYER_SETTING_DEFAULTS: dict[str, int] = {
    "VisualizerMode": 1,
    "ColorStyle": 1,
    "KaraokeStyle": 1,
    "KaraokeTreatment": 2,
    "KaraokeEmojimax": 1,
    "ProgressStyle": 1,
    "OutputChannels": 2,
    "Balance": 0,
    "Volume": 100,
    "SpeedIndex": PLAYBACK_SPEEDS.index(1.0),
    "Looping": 1,
    "Shuffle": 1,
    "Autoplay": 0,
    "DrcsEnabled": int(bool(ENABLE_DRCS_VISUALIZER)),
    "SixelEnabled": int(bool(ENABLE_SIXEL_VISUALIZER)),
}


def load_player_settings() -> dict[str, int]:
    settings = dict(PLAYER_SETTING_DEFAULTS)
    if os.name != "nt":
        return settings
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\ClaireCJS\play_audio_file") as key:
            for name in settings:
                try:
                    value, _kind = winreg.QueryValueEx(key, name)
                    settings[name] = int(value)
                except (OSError, TypeError, ValueError):
                    pass
    except OSError:
        pass
    settings["VisualizerMode"] = min(len(VISUALIZER_MODE_NAMES), max(1, settings["VisualizerMode"]))
    settings["ColorStyle"] = min(len(COLOR_STYLE_NAMES), max(1, settings["ColorStyle"]))
    settings["KaraokeStyle"] = min(len(KARAOKE_STYLE_NAMES), max(1, settings["KaraokeStyle"]))
    settings["KaraokeTreatment"] = min(len(KARAOKE_TREATMENT_NAMES), max(1, settings["KaraokeTreatment"]))
    settings["ProgressStyle"] = min(len(PROGRESS_STYLE_NAMES), max(1, settings["ProgressStyle"]))
    settings["OutputChannels"] = settings["OutputChannels"] if settings["OutputChannels"] in {2, 5, 7} else 2
    settings["Balance"] = min(100, max(-100, settings["Balance"]))
    settings["Volume"] = min(400, max(0, settings["Volume"]))
    settings["SpeedIndex"] = min(len(PLAYBACK_SPEEDS) - 1, max(0, settings["SpeedIndex"]))
    return settings


def save_player_settings(settings: dict[str, int]) -> None:
    if os.name != "nt":
        return
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\ClaireCJS\play_audio_file") as key:
        for name, value in settings.items():
            winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, int(value))


def playlist_resume_value_name(playlist_path: Path) -> str:
    """Return a stable registry value name for one playlist."""
    identity = str(playlist_path.absolute()).casefold().encode("utf-8")
    return "PlaylistResume_" + hashlib.sha256(identity).hexdigest()[:24]


LAST_PLAYLIST_RESUME_VALUE = "PlaylistResume_Last"


def _decode_playlist_resume(raw: object) -> tuple[Path, float] | None:
    try:
        payload = json.loads(str(raw))
        return Path(payload["track"]), max(0.0, float(payload["position"]))
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None


def load_playlist_resume(playlist_path: Path) -> tuple[Path, float] | None:
    """Load the most recently interrupted playlist track, across playlists.

    The old per-playlist value is retained as a compatibility fallback, but the
    global bookmark wins: starting a newly generated playlist should continue
    the song that was actually playing when the player was last closed, if that
    song is still present in the new playlist.
    """
    if os.name != "nt":
        return None
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\ClaireCJS\play_audio_file") as key:
            for value_name in (LAST_PLAYLIST_RESUME_VALUE, playlist_resume_value_name(playlist_path)):
                try:
                    raw, _kind = winreg.QueryValueEx(key, value_name)
                except OSError:
                    continue
                decoded = _decode_playlist_resume(raw)
                if decoded is not None:
                    return decoded
    except OSError:
        pass
    return None


def save_playlist_resume(playlist_path: Path, track: Path, position: float) -> None:
    """Persist both the playlist bookmark and the global last-played bookmark."""
    if os.name != "nt":
        return
    import winreg
    payload = json.dumps({"track": str(track.absolute()), "position": max(0.0, position)})
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\ClaireCJS\play_audio_file") as key:
        winreg.SetValueEx(key, playlist_resume_value_name(playlist_path), 0, winreg.REG_SZ, payload)
        winreg.SetValueEx(key, LAST_PLAYLIST_RESUME_VALUE, 0, winreg.REG_SZ, payload)


def clear_playlist_resume(playlist_path: Path) -> None:
    """Remove a completed playlist bookmark."""
    if os.name != "nt":
        return
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\ClaireCJS\play_audio_file", 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, playlist_resume_value_name(playlist_path))
    except OSError:
        pass


def toggle_registry_favorite(name: str, value: int) -> bool:
    values = registry_favorites(name)
    added = value not in values
    values.remove(value) if not added else values.append(value)
    save_registry_favorites(name, values)
    return added


def next_registry_favorite(name: str, current: int) -> int:
    values = registry_favorites(name)
    if not values:
        return current
    return values[(values.index(current) + 1) % len(values)] if current in values else values[0]


def first_registry_favorite(name: str, current: int) -> int:
    """Return the first saved favorite, or leave the current value unchanged."""
    values = registry_favorites(name)
    return values[0] if values else current


def load_favorite_visualizer_mode() -> int:
    """Load the favored DRCS mode from the current user's registry."""
    default_mode = VISUALIZER_TREATMENT_NAMES.index("Compressed") * len(VISUALIZER_TYPE_NAMES) + 1
    if os.name != "nt":
        return default_mode
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\ClaireCJS\play_audio_file") as key:
            value, _kind = winreg.QueryValueEx(key, "VisualizerMode")
        return min(len(VISUALIZER_MODE_NAMES), max(1, int(value)))
    except (OSError, TypeError, ValueError):
        return default_mode


def save_favorite_visualizer_mode(mode: int) -> None:
    """Persist the favored DRCS mode without replacing a config file."""
    if os.name != "nt":
        return
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\ClaireCJS\play_audio_file") as key:
        winreg.SetValueEx(key, "VisualizerMode", 0, winreg.REG_DWORD, int(mode))

SEEK_SECONDS = {
    SEEK_BACK_5: -5.0,
    SEEK_FORWARD_5: 5.0,
    SEEK_BACK_10: -10.0,
    SEEK_FORWARD_10: 10.0,
    SEEK_BACK_15: -15.0,
    SEEK_FORWARD_15: 15.0,
    SEEK_BACK_60: -60.0,
    SEEK_FORWARD_60: 60.0,
}

VOLUME_STEPS = {
    VOLUME_UP_5: 5,
    VOLUME_DOWN_5: -5,
    VOLUME_UP_20: 20,
    VOLUME_DOWN_20: -20,
}


def validate_file(file_path: str | os.PathLike[str]) -> Path:
    """Return a resolved, nonempty regular-file path or raise clearly."""
    path = Path(file_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(
            f"The specified file does not exist: {path}"
        )
    if not path.is_file():
        raise IsADirectoryError(
            f"The specified path is a directory, not a file: {path}"
        )
    if path.stat().st_size == 0:
        raise ValueError(f"The specified file is empty: {path}")
    return path


def natural_path_key(path: Path) -> tuple[object, ...]:
    """Sort paths naturally and case-insensitively, including numeric names."""
    return tuple(
        int(part) if part.isdigit() else part.casefold()
        for part in re.split(r"(\d+)", str(path))
    )


def audio_files_in(directory: Path) -> list[Path]:
    """Return supported audio files directly inside one directory."""
    try:
        files = [
            path for path in directory.iterdir()
            if path.is_file() and path.suffix.casefold() in AUDIO_EXTENSIONS
        ]
    except OSError:
        return []
    return sorted(files, key=natural_path_key)


def random_audio_file(directory: Path) -> Path:
    """Choose one audio file from a directory without walking descendants."""
    choices = audio_files_in(directory.resolve())
    if not choices:
        raise FileNotFoundError(f"No audio files were found in: {directory}")
    return random.choice(choices)


def random_audio_file_recursive(directory: Path) -> Path:
    """Random-walk downward one directory at a time, then choose a leaf file."""
    current = directory.resolve()
    while True:
        try:
            children = [path for path in current.iterdir() if path.is_dir()]
        except OSError as exc:
            raise OSError(f"Could not inspect random directory {current}: {exc}") from exc
        if not children:
            return random_audio_file(current)
        current = random.choice(children)


def load_playlist(playlist_path: Path, *, show_progress: bool = True) -> list[Path]:
    """Load local audio entries from M3U/M3U8, PLS, or XSPF playlists."""
    playlist = playlist_path.expanduser().resolve()
    if not playlist.is_file():
        raise FileNotFoundError(f"Playlist does not exist: {playlist}")
    text = playlist.read_text(encoding="utf-8-sig", errors="replace")
    suffix = playlist.suffix.casefold()
    entries: list[str]
    if suffix == ".pls":
        entries = [
            value.strip()
            for line in text.splitlines()
            for key, separator, value in [line.partition("=")]
            if separator and key.casefold().startswith("file") and value.strip()
        ]
    elif suffix == ".xspf":
        entries = re.findall(r"<location>(.*?)</location>", text, flags=re.I | re.S)
        from urllib.parse import unquote, urlparse
        entries = [
            unquote(urlparse(value.strip()).path.lstrip("/"))
            if value.strip().casefold().startswith("file:") else value.strip()
            for value in entries
        ]
    else:
        entries = [
            line.strip() for line in text.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
    resolved: list[Path] = []
    with progress_bar(
        total=len(entries),
        description="🎶 Loading playlist",
        unit="entry",
        enabled=bool(show_progress and getattr(sys.stderr, "isatty", lambda: False)()),
    ) as playlist_progress:
        for entry in entries:
            if not re.match(r"^[a-z][a-z0-9+.-]*://", entry, flags=re.I):
                candidate = Path(entry)
                if not candidate.is_absolute():
                    candidate = playlist.parent / candidate
                candidate = candidate.resolve()
                if candidate.is_file() and candidate.suffix.casefold() in AUDIO_EXTENSIONS:
                    resolved.append(candidate)
            if playlist_progress is not None:
                playlist_progress.update(1)
    if not resolved:
        raise ValueError(f"Playlist contains no usable local audio files: {playlist}")
    return resolved


def _playlist_line_candidate(playlist: Path, line: str, *, require_file: bool = True) -> Path | None:
    """Resolve one line-oriented playlist entry without reading the whole list."""
    text = line.strip().lstrip("\ufeff")
    if not text:
        return None
    suffix = playlist.suffix.casefold()
    if suffix == ".pls":
        key, separator, value = text.partition("=")
        if not separator or not key.casefold().startswith("file"):
            return None
        text = value.strip()
    elif suffix == ".xspf":
        match = re.search(r"<location>(.*?)</location>", text, flags=re.I | re.S)
        if not match:
            return None
        text = match.group(1).strip()
        from urllib.parse import unquote, urlparse
        if text.casefold().startswith("file:"):
            text = unquote(urlparse(text).path.lstrip("/"))
    elif text.startswith("#"):
        return None
    if re.match(r"^[a-z][a-z0-9+.-]*://", text, flags=re.I):
        return None
    candidate = Path(text)
    if not candidate.is_absolute():
        candidate = playlist.parent / candidate
    try:
        candidate = candidate.resolve(strict=False)
    except OSError:
        candidate = candidate.absolute()
    if candidate.suffix.casefold() not in AUDIO_EXTENSIONS:
        return None
    if require_file and not candidate.is_file():
        return None
    return candidate


def find_track_in_playlist_fast(playlist_path: Path, track: Path) -> Path | None:
    """Check a saved track with random-access text lookup, not a full parse."""
    playlist = playlist_path.expanduser().resolve()
    target = track.expanduser().resolve(strict=False)
    suffix = playlist.suffix.casefold()
    try:
        if suffix == ".xspf":
            # XML locations may be URL-escaped, so use the ordinary location
            # extraction here. XSPF is uncommon; M3U/PLS take the mmap fast path.
            text = playlist.read_text(encoding="utf-8-sig", errors="replace")
            for line in re.findall(r"<location>.*?</location>", text, flags=re.I | re.S):
                candidate = _playlist_line_candidate(playlist, line, require_file=False)
                if candidate is not None and candidate == target:
                    return target if target.is_file() else None
            return None

        import mmap
        needle = target.name.encode("utf-8", errors="ignore")
        if not needle or playlist.stat().st_size <= 0:
            return None
        with playlist.open("rb") as handle, mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as mapped:
            position = mapped.find(needle)
            while position >= 0:
                line_start = mapped.rfind(b"\n", 0, position) + 1
                line_end = mapped.find(b"\n", position)
                if line_end < 0:
                    line_end = len(mapped)
                line = mapped[line_start:line_end].decode("utf-8", errors="replace")
                candidate = _playlist_line_candidate(playlist, line, require_file=False)
                if candidate is not None and candidate == target:
                    return target if target.is_file() else None
                position = mapped.find(needle, position + max(1, len(needle)))
    except (OSError, ValueError):
        return None
    return None


def quick_random_playlist_track(playlist_path: Path, *, attempts: int = 64) -> Path:
    """Pick a usable playlist entry by random file seeks whenever practical.

    M3U/M3U8 and PLS are line-oriented, so a large list does not need to be
    parsed from the beginning just to start playback. XSPF is sampled in chunks
    around random byte offsets. A full load is only the fallback.
    """
    playlist = playlist_path.expanduser().resolve()
    size = playlist.stat().st_size
    if size <= 0:
        raise ValueError(f"Playlist is empty: {playlist}")
    suffix = playlist.suffix.casefold()
    with playlist.open("rb") as handle:
        for _ in range(max(1, attempts)):
            offset = random.randrange(size)
            handle.seek(offset)
            if offset:
                handle.readline()  # discard the partial line containing the seek point
            if suffix == ".xspf":
                blob = handle.read(min(65536, max(4096, size)))
                text = blob.decode("utf-8", errors="replace")
                locations = re.findall(r"<location>.*?</location>", text, flags=re.I | re.S)
                random.shuffle(locations)
                candidate_lines = locations
            else:
                candidate_lines = [
                    handle.readline().decode("utf-8", errors="replace")
                    for _line_number in range(24)
                ]
            for line in candidate_lines:
                candidate = _playlist_line_candidate(playlist, line)
                if candidate is not None:
                    return candidate
    # Small, unusual, or pathologically formatted playlists can fall back to
    # the ordinary parser; normal large M3U/PLS startup never gets here.
    return random.choice(load_playlist(playlist, show_progress=False))


def playlist_history_database_path() -> Path:
    """Return the small local SQLite database used for playlist rotation."""
    override = os.environ.get("PLAY_AUDIO_FILE_HISTORY_DB")
    return Path(override) if override else Path(__file__).resolve().with_name("play_audio_file-play-history.sqlite3")


# Paths are deliberately only in-process cache keys. They are never written to
# SQLite. Persistent history uses a cheap normalized filename key first, then
# duration + normalized Artist/Title to disambiguate filename collisions.
# The metadata cache lets duration + tags share one ffprobe result.
_AUDIO_METADATA_CACHE: dict[str, tuple[int, int, float | None, dict[str, str]]] = {}
_PLAYLIST_HISTORY_IDENTITY_CACHE: dict[str, tuple[int, int, tuple[str, int, str]]] = {}
_PLAYLIST_HISTORY_LAST_PLAYED_CACHE: dict[str, float] = {}


def normalize_playlist_history_text(value: str) -> str:
    """Normalize an identity component without throwing away punctuation."""
    normalized = unicodedata.normalize("NFKC", str(value or ""))
    return re.sub(r"\s+", " ", normalized).strip().casefold()


def playlist_history_filename_key(value: str | os.PathLike[str] | Path) -> str:
    """Return the cheap basename-only history key.

    No directory is retained. The audio extension and a conventional leading
    numeric track prefix (``08_``, ``7-``, ``03.`` and similar) are stripped so
    a library move or format conversion does not defeat the filename fast path.
    """
    if isinstance(value, Path):
        name = value.name
    else:
        raw = str(value or "")
        # Last.fm logs contain Windows paths even when tests run elsewhere.
        name = PureWindowsPath(raw).name if "\\" in raw else Path(raw).name
    stem = PureWindowsPath(name).stem
    stem = re.sub(r"^(?:\s*\d{1,3}\s*[-_. ]+\s*)+", "", stem)
    return normalize_playlist_history_text(stem)


def playlist_history_tag_key(tags: dict[str, str]) -> str:
    """Return the normalized Artist+Song identity used after filename."""
    artist = normalize_playlist_history_text(tags.get("Artist", ""))
    song = normalize_playlist_history_text(tags.get("Song", ""))
    return "\x1f".join((artist, song))


def probe_audio_history_identity(track: Path) -> tuple[str, int, str]:
    """Read basename key, duration and Artist/Title using one metadata probe."""
    duration, tags = probe_audio_metadata(track)
    try:
        numeric = float(duration) if duration is not None else 0.0
        duration_seconds = max(1, int(round(numeric))) if math.isfinite(numeric) and numeric > 0 else 0
    except (TypeError, ValueError):
        duration_seconds = 0
    return playlist_history_filename_key(track), duration_seconds, playlist_history_tag_key(tags)


def cache_playlist_history_identity(
    track: Path,
    duration_seconds: float | int | None,
    tags: dict[str, str],
) -> tuple[str, int, str]:
    """Cache an exact identity from metadata the player already obtained."""
    try:
        numeric = float(duration_seconds) if duration_seconds is not None else 0.0
        rounded_duration = max(1, int(round(numeric))) if math.isfinite(numeric) and numeric > 0 else 0
    except (TypeError, ValueError):
        rounded_duration = 0
    identity = (
        playlist_history_filename_key(track),
        rounded_duration,
        playlist_history_tag_key(tags),
    )
    try:
        stat = track.stat()
        cache_key = str(track.resolve()).casefold()
        _PLAYLIST_HISTORY_IDENTITY_CACHE[cache_key] = (stat.st_size, stat.st_mtime_ns, identity)
    except OSError:
        pass
    return identity


def playlist_history_identity(track: Path) -> tuple[str, int, str]:
    """Return (filename_key, duration_seconds, normalized Artist+Title tag).

    The filename key is basename-only, with extension and a leading numeric
    track prefix removed. Full paths are used only as in-process cache keys and
    are never persisted.
    """
    try:
        stat = track.stat()
        cache_key = str(track.resolve()).casefold()
        cached = _PLAYLIST_HISTORY_IDENTITY_CACHE.get(cache_key)
        if cached is not None and cached[0] == stat.st_size and cached[1] == stat.st_mtime_ns:
            return cached[2]
    except OSError:
        stat = None
        cache_key = str(track.absolute()).casefold()

    identity = probe_audio_history_identity(track)
    if stat is not None:
        _PLAYLIST_HISTORY_IDENTITY_CACHE[cache_key] = (stat.st_size, stat.st_mtime_ns, identity)
    return identity


def _create_playlist_history_table(database: sqlite3.Connection) -> None:
    database.execute(
        """CREATE TABLE played_tracks_recent (
            filename TEXT NOT NULL,
            duration_seconds INTEGER NOT NULL,
            tag TEXT NOT NULL,
            played_at REAL NOT NULL,
            PRIMARY KEY (filename, duration_seconds, tag)
        ) WITHOUT ROWID"""
    )


def _playlist_history_migrate_schema(database: sqlite3.Connection) -> None:
    """Migrate older history schemas to filename-first composite identity."""
    row = database.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='played_tracks_recent'"
    ).fetchone()
    if row is None:
        _create_playlist_history_table(database)
        return

    columns = [
        str(info[1])
        for info in database.execute("PRAGMA table_info(played_tracks_recent)").fetchall()
    ]
    expected = ["filename", "duration_seconds", "tag", "played_at"]
    if columns == expected:
        return

    if {"filename", "duration_seconds", "tag", "played_at"}.issubset(columns):
        rows = database.execute(
            "SELECT filename, duration_seconds, tag, played_at FROM played_tracks_recent"
        ).fetchall()
        database.execute("DROP TABLE IF EXISTS played_tracks_recent_new")
        database.execute(
            """CREATE TABLE played_tracks_recent_new (
                filename TEXT NOT NULL,
                duration_seconds INTEGER NOT NULL,
                tag TEXT NOT NULL,
                played_at REAL NOT NULL,
                PRIMARY KEY (filename, duration_seconds, tag)
            ) WITHOUT ROWID"""
        )
        normalized: dict[tuple[str, int, str], float] = {}
        for filename, duration_seconds, tag, played_at in rows:
            filename_key = playlist_history_filename_key(str(filename))
            try:
                duration = int(duration_seconds)
                when = float(played_at)
            except (TypeError, ValueError):
                continue
            if not filename_key or duration <= 0 or not tag or str(tag) == "\x1f":
                continue
            key = (filename_key, duration, str(tag))
            normalized[key] = max(normalized.get(key, float("-inf")), when)
        database.executemany(
            "INSERT INTO played_tracks_recent_new(filename, duration_seconds, tag, played_at) VALUES (?, ?, ?, ?)",
            [(filename, duration, tag, when) for (filename, duration, tag), when in normalized.items()],
        )
        database.execute("DROP TABLE played_tracks_recent")
        database.execute("ALTER TABLE played_tracks_recent_new RENAME TO played_tracks_recent")
        return

    # The short-lived duration+tag-only schema cannot be losslessly converted
    # because it intentionally discarded filenames. Preserve it as a backup,
    # then start the filename-indexed table cleanly; re-importing Last.fm logs
    # will repopulate every play for which the logs contain filename evidence.
    suffix = int(time.time())
    backup = f"played_tracks_recent_backup_{suffix}"
    database.execute(f'ALTER TABLE played_tracks_recent RENAME TO "{backup}"')
    _create_playlist_history_table(database)


def playlist_history_connection() -> sqlite3.Connection:
    """Open the latest-only history DB and ensure its optimized schema exists."""
    database = sqlite3.connect(playlist_history_database_path())
    database.execute("PRAGMA journal_mode=WAL")
    database.execute("PRAGMA synchronous=NORMAL")
    _playlist_history_migrate_schema(database)
    # filename is the left-most column of the WITHOUT ROWID primary-key B-tree,
    # so both filename-only candidate lookups and exact three-part lookups use
    # the table itself; no redundant secondary index is needed.
    database.execute("DROP INDEX IF EXISTS played_tracks_recent_tag_duration_idx")
    database.execute("DROP INDEX IF EXISTS played_tracks_recent_filename_played_idx")
    return database


def playlist_history_mark_identity_played(
    filename: str,
    duration_seconds: int,
    tag: str,
    played_at: float | None = None,
    *,
    database: sqlite3.Connection | None = None,
) -> None:
    """Upsert one exact identity, retaining only its most recent play time."""
    filename_key = playlist_history_filename_key(filename)
    if not filename_key or duration_seconds <= 0 or not tag or tag == "\x1f":
        return
    when = time.time() if played_at is None else float(played_at)
    owns_database = database is None
    db = database or playlist_history_connection()
    try:
        db.execute(
            """INSERT INTO played_tracks_recent(filename, duration_seconds, tag, played_at)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(filename, duration_seconds, tag)
               DO UPDATE SET played_at=MAX(played_tracks_recent.played_at, excluded.played_at)""",
            (filename_key, int(duration_seconds), str(tag), when),
        )
        if owns_database:
            db.commit()
    finally:
        if owns_database:
            db.close()


def format_last_heard_age(seconds: float) -> str:
    """Format an elapsed age compactly for the Last heard metadata field."""
    seconds = max(0.0, float(seconds))
    minutes = seconds / 60.0
    if minutes < 60.0:
        return f"{max(1, round(minutes))}min"
    hours = minutes / 60.0
    if hours < 24.0:
        rounded = round(hours * 4.0) / 4.0
        return f"{rounded:g}hr"
    days = hours / 24.0
    if days < 7.0:
        rounded = round(days * 2.0) / 2.0
        return f"{rounded:g}d"
    if days < 28.0:
        rounded = round(days / 7.0 * 2.0) / 2.0
        return f"{rounded:g}w"
    if days < 365.25:
        months = max(1, round(days / 30.4375))
        return f"{months}mo" if months == 1 else f"{months}mos"
    years = days / 365.25
    rounded = round(years, 1)
    return f"{rounded:g}yr"


def playlist_history_runtime_key(track: Path) -> str:
    """Return the in-process path key used for background history results."""
    try:
        return str(track.resolve()).casefold()
    except OSError:
        return str(track.absolute()).casefold()


def playlist_history_last_played(
    track: Path,
    *,
    duration_seconds: float | int | None = None,
    tags: dict[str, str] | None = None,
) -> float | None:
    """Return a background-cached play time without querying history per track."""
    return _PLAYLIST_HISTORY_LAST_PLAYED_CACHE.get(playlist_history_runtime_key(track))


def playlist_history_mark_played(
    track: Path,
    *,
    duration_seconds: float | int | None = None,
    tags: dict[str, str] | None = None,
) -> None:
    """Remember only the latest play for filename+duration+normalized tags."""
    try:
        if duration_seconds is not None and tags is not None:
            filename, duration, tag = cache_playlist_history_identity(track, duration_seconds, tags)
        else:
            filename, duration, tag = playlist_history_identity(track)
        playlist_history_mark_identity_played(filename, duration, tag)
    except (OSError, sqlite3.Error):
        return


def playlist_history_scores(
    entries: list[Path], status_callback=None,
) -> list[tuple[float, Path]]:
    """Read persistent play history once and score every playlist entry.

    Filename-only matches are cheap. Metadata is probed only when the history
    database contains multiple identities for the same normalized filename.
    """
    if not entries:
        return []
    if status_callback is not None:
        status_callback(True)
    try:
        filename_keys = [playlist_history_filename_key(entry) for entry in entries]
        rows_by_filename: dict[str, list[tuple[int, str, float]]] = {}
        unique_filenames = sorted({key for key in filename_keys if key})
        with playlist_history_connection() as database:
            for offset in range(0, len(unique_filenames), 900):
                batch = unique_filenames[offset:offset + 900]
                if not batch:
                    continue
                placeholders = ",".join("?" for _ in batch)
                rows = database.execute(
                    "SELECT filename, duration_seconds, tag, played_at "
                    f"FROM played_tracks_recent WHERE filename IN ({placeholders})",
                    batch,
                ).fetchall()
                for filename, duration_seconds, tag, played_at in rows:
                    rows_by_filename.setdefault(str(filename), []).append(
                        (int(duration_seconds), str(tag), float(played_at))
                    )

        scored: list[tuple[float, Path]] = []
        for entry, filename_key in zip(entries, filename_keys):
            candidates = rows_by_filename.get(filename_key, [])
            if not candidates:
                played_at = 0.0
            elif len(candidates) == 1:
                played_at = candidates[0][2]
            else:
                try:
                    _filename, duration, tag = playlist_history_identity(entry)
                except OSError:
                    played_at = 0.0
                else:
                    matches = [
                        when for stored_duration, stored_tag, when in candidates
                        if stored_duration == duration and stored_tag == tag
                    ]
                    played_at = max(matches, default=0.0)
            scored.append((played_at, entry))
            _PLAYLIST_HISTORY_LAST_PLAYED_CACHE[playlist_history_runtime_key(entry)] = played_at
        return scored
    finally:
        if status_callback is not None:
            status_callback(False)


def choose_least_recent_playlist_track(
    entries: list[Path], status_callback=None,
) -> Path:
    """Choose randomly from the 15% played longest ago (or never played)."""
    if not entries:
        raise ValueError("Cannot choose from an empty playlist")
    try:
        scored = playlist_history_scores(entries, status_callback)
        scored.sort(key=lambda item: item[0])
        oldest_count = max(1, math.ceil(len(scored) * 0.15))
        cutoff = scored[oldest_count - 1][0]
        return random.choice([entry for played_at, entry in scored if played_at <= cutoff])
    except sqlite3.Error:
        return random.choice(entries)


def build_playlist_shuffle_order(
    entries: list[Path], status_callback=None,
) -> list[Path]:
    """Build the entire history-biased shuffle order once, before playback.

    Never-played tracks are randomized first. Previously played tracks follow
    from oldest to newest in randomized 15%-sized buckets. No history lookup is
    needed when advancing from one track to the next.
    """
    if not entries:
        return []
    try:
        scored = playlist_history_scores(entries, status_callback)
    except sqlite3.Error:
        order = list(entries)
        random.shuffle(order)
        return order

    never_played = [entry for played_at, entry in scored if played_at <= 0.0]
    played = sorted(
        ((played_at, entry) for played_at, entry in scored if played_at > 0.0),
        key=lambda item: item[0],
    )
    random.shuffle(never_played)
    order = list(never_played)
    bucket_size = max(1, math.ceil(len(entries) * 0.15))
    for offset in range(0, len(played), bucket_size):
        bucket = [entry for _played_at, entry in played[offset:offset + bucket_size]]
        random.shuffle(bucket)
        order.extend(bucket)
    return order


def build_playlist_shuffle_order_progressive(
    entries: list[Path], progress_callback=None,
) -> list[Path]:
    """Build the historical shuffle in ten visible 10% history-query chunks."""
    if not entries:
        if progress_callback is not None:
            progress_callback("historical shuffling done")
        return []
    scored: list[tuple[float, Path]] = []
    try:
        for chunk_index in range(10):
            low = chunk_index * 10
            high = low + 10
            if progress_callback is not None:
                progress_callback(f"shuffling {low}%–{high}%")
            start = len(entries) * chunk_index // 10
            end = len(entries) * (chunk_index + 1) // 10
            if end > start:
                scored.extend(playlist_history_scores(entries[start:end]))
    except sqlite3.Error:
        order = list(entries)
        random.shuffle(order)
        if progress_callback is not None:
            progress_callback("historical shuffling done")
        return order

    never_played = [entry for played_at, entry in scored if played_at <= 0.0]
    played = sorted(
        ((played_at, entry) for played_at, entry in scored if played_at > 0.0),
        key=lambda item: item[0],
    )
    random.shuffle(never_played)
    order = list(never_played)
    bucket_size = max(1, math.ceil(len(entries) * 0.15))
    for offset in range(0, len(played), bucket_size):
        bucket = [entry for _played_at, entry in played[offset:offset + bucket_size]]
        random.shuffle(bucket)
        order.extend(bucket)
    if progress_callback is not None:
        progress_callback("historical shuffling done")
    return order



def playlist_shuffle_cache_path(playlist_path: Path) -> Path:
    """Return the per-playlist temporary cache file for the completed shuffle order."""
    identity = str(playlist_path.resolve()).casefold().encode("utf-8")
    digest = hashlib.sha256(identity).hexdigest()[:32]
    return Path(tempfile.gettempdir()) / "play_audio_file" / "shuffle_cache" / f"{digest}.json"


def load_playlist_shuffle_cache(
    playlist_path: Path,
    expiration_hours: float,
) -> tuple[list[Path], list[Path]] | None:
    """Load a fresh completed shuffle, invalidating it if age or playlist metadata changed."""
    if expiration_hours <= 0:
        return None
    cache_path = playlist_shuffle_cache_path(playlist_path)
    try:
        playlist_stat = playlist_path.stat()
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
        created_at = float(payload["created_at"])
        if time.time() - created_at > expiration_hours * 3600.0:
            return None
        if int(payload.get("playlist_mtime_ns", -1)) != int(playlist_stat.st_mtime_ns):
            return None
        if int(payload.get("playlist_size", -1)) != int(playlist_stat.st_size):
            return None
        entries = [Path(value) for value in payload["entries"]]
        order = [Path(value) for value in payload["order"]]
        for key, value in dict(payload.get("last_played", {})).items():
            try:
                _PLAYLIST_HISTORY_LAST_PLAYED_CACHE[str(key)] = float(value)
            except (TypeError, ValueError):
                continue
        if not entries or not order:
            return None
        # The playlist file is unchanged, but individual media files can still
        # disappear.  Filter them out rather than reviving dead cache entries.
        entry_keys = {str(entry.resolve()).casefold() for entry in entries if entry.is_file()}
        entries = [entry for entry in entries if str(entry.resolve()).casefold() in entry_keys]
        order = [entry for entry in order if str(entry.resolve()).casefold() in entry_keys]
        if not entries or not order:
            return None
        return entries, order
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        return None


def save_playlist_shuffle_cache(
    playlist_path: Path,
    entries: list[Path],
    order: list[Path],
) -> None:
    """Atomically cache the fully prepared internal playlist shuffle in the temp directory."""
    if not entries or not order:
        return
    cache_path = playlist_shuffle_cache_path(playlist_path)
    try:
        playlist_stat = playlist_path.stat()
        payload = {
            "created_at": time.time(),
            "playlist": str(playlist_path.resolve()),
            "playlist_mtime_ns": int(playlist_stat.st_mtime_ns),
            "playlist_size": int(playlist_stat.st_size),
            "entries": [str(entry) for entry in entries],
            "order": [str(entry) for entry in order],
            "last_played": {
                playlist_history_runtime_key(entry): float(
                    _PLAYLIST_HISTORY_LAST_PLAYED_CACHE.get(playlist_history_runtime_key(entry), 0.0)
                )
                for entry in entries
            },
        }
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = cache_path.with_suffix(cache_path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        os.replace(temporary, cache_path)
    except OSError:
        return

def audio_navigation_root(directory: Path) -> Path:
    """Prefer the surrounding MUSIC/MP3 library; otherwise use the parent."""
    for candidate in (directory, *directory.parents):
        if candidate.name.casefold() in {"music", "mp3"}:
            return candidate
    return directory.parent


def advance_playlist_visit_history(
    history: list[Path],
    cursor: int,
    result: str,
    queue_neighbor,
) -> tuple[Path, int]:
    """Move through actual visit history without re-appending tracks while going back."""
    if not history:
        first = queue_neighbor(0)
        history.append(first)
        return first, 0
    if result == PREVIOUS_FILE:
        if cursor > 0:
            cursor -= 1
            return history[cursor], cursor
        previous_track = queue_neighbor(-1)
        history.insert(0, previous_track)
        return previous_track, 0
    if result in {NEXT_FILE, "completed"} and cursor + 1 < len(history):
        cursor += 1
        return history[cursor], cursor
    next_track = queue_neighbor(1)
    if cursor + 1 < len(history):
        del history[cursor + 1:]
    history.append(next_track)
    return next_track, len(history) - 1


def navigate_audio_path(current_path: Path, action: str) -> Path:
    """Resolve one wrapping file or audio-directory navigation action."""
    current_path = current_path.resolve()
    current_directory = current_path.parent
    direction = -1 if action in {PREVIOUS_FILE, PREVIOUS_DIRECTORY} else 1
    if action in {PREVIOUS_FILE, NEXT_FILE}:
        files = audio_files_in(current_directory)
        if not files:
            return current_path
        try:
            current_index = files.index(current_path)
        except ValueError:
            current_index = 0
        return files[(current_index + direction) % len(files)]

    root = audio_navigation_root(current_directory).resolve()

    def children(directory: Path) -> list[Path]:
        try:
            return sorted(
                (path.resolve() for path in directory.iterdir() if path.is_dir()),
                key=natural_path_key,
            )
        except OSError:
            return []

    def adjacent(directory: Path) -> Path | None:
        if direction > 0:
            nested = children(directory)
            if nested:
                return nested[0]
        cursor = directory
        while cursor != root and root in cursor.parents:
            siblings = children(cursor.parent)
            try:
                index = siblings.index(cursor)
            except ValueError:
                index = -1
            target_index = index + direction
            if 0 <= target_index < len(siblings):
                target = siblings[target_index]
                if direction < 0:
                    while children(target):
                        target = children(target)[-1]
                return target
            cursor = cursor.parent
        if directory == root:
            return None
        wrapped = root
        nested = children(wrapped)
        if direction > 0:
            return nested[0] if nested else root
        while nested:
            wrapped = nested[-1]
            nested = children(wrapped)
        return wrapped

    candidate = adjacent(current_directory)
    deadline = time.monotonic() + 4.0
    while candidate is not None and time.monotonic() < deadline:
        files = audio_files_in(candidate)
        if files:
            return files[-1 if direction < 0 else 0]
        candidate = adjacent(candidate)
    return current_path


def ffplay_executable() -> Path:
    """Locate FFplay, which performs the actual audio decoding and output."""
    discovered = shutil.which("ffplay")
    if not discovered:
        raise RuntimeError(
            "ffplay was not found in PATH.\n" + tool_install_instructions("ffmpeg")
        )
    return Path(discovered)


def tool_install_instructions(tool: str) -> str:
    """Return Winget installation and Desktop App Installer recovery steps."""
    commands = {
        "ffmpeg": "winget install -e --id Gyan.FFmpeg",
        "chafa": "winget install -e --id hpjansson.Chafa",
    }
    install = commands[tool.casefold()]
    return (
        f"Install {tool}: {install}\n"
        "If winget is unavailable, install/register it with:\n"
        'powershell -Command "Add-AppxPackage -RegisterByFamilyName -MainPackage '
        'Microsoft.DesktopAppInstaller_8wekyb3d8bbwe"\n'
        "If that does not work, try:\n"
        'powershell -Command "Add-AppxPackage -Path \\\"https://aka.ms/getwinget\\\""'
    )


def ffprobe_executable() -> Path | None:
    """Locate optional FFprobe for duration and metadata inspection."""
    discovered = shutil.which("ffprobe")
    return Path(discovered) if discovered else None


def _audio_metadata_cache_location(audio_path: Path) -> tuple[str, int, int] | None:
    try:
        stat = audio_path.stat()
        return str(audio_path.resolve()).casefold(), stat.st_size, stat.st_mtime_ns
    except OSError:
        return None


def _id3_synchsafe_int(raw: bytes) -> int:
    """Decode a four-byte ID3 synchsafe integer."""
    if len(raw) != 4:
        return 0
    return (
        ((raw[0] & 0x7F) << 21)
        | ((raw[1] & 0x7F) << 14)
        | ((raw[2] & 0x7F) << 7)
        | (raw[3] & 0x7F)
    )


def _swap_adjacent_bytes(raw: bytes) -> bytes:
    """Undo the pair-swapped byte damage seen in some malformed ID3 text."""
    swapped = bytearray()
    for index in range(0, len(raw), 2):
        pair = raw[index:index + 2]
        swapped.extend(pair[::-1] if len(pair) == 2 else pair)
    return bytes(swapped)


def _clean_recovered_id3_text(text: str) -> str:
    """Strip NULs/BOM debris while preserving normal Unicode text."""
    return text.replace("\ufeff", "").replace("\x00", "").strip()


def _decode_id3_text_payload(payload: bytes) -> str:
    """Decode normal ID3 text plus the broken UTF-8/BOM/pair-swapped variant.

    A few damaged files in this library declare encoding 3 (UTF-8), then place a
    UTF-16 BOM in front of bytes whose adjacent pairs were swapped.  Standards-
    compliant readers quite reasonably discard those frames.  Recover that exact
    signature before falling back to the normal ID3 text encodings.
    """
    if not payload:
        return ""
    encoding = payload[0]
    raw = payload[1:]

    if encoding == 3 and raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        damaged = raw[2:]
        candidate = _swap_adjacent_bytes(damaged)
        for codec in ("utf-8", "cp1252", "latin1"):
            try:
                recovered = _clean_recovered_id3_text(candidate.decode(codec))
            except UnicodeDecodeError:
                continue
            if recovered and sum(character.isprintable() for character in recovered) >= max(1, len(recovered) - 1):
                return recovered

    codec = {0: "latin1", 1: "utf-16", 2: "utf-16-be", 3: "utf-8"}.get(encoding)
    if codec is None:
        return ""
    try:
        return _clean_recovered_id3_text(raw.decode(codec, errors="replace"))
    except (LookupError, UnicodeError):
        return ""


def _recover_raw_id3_display_tags(audio_path: Path) -> dict[str, str]:
    """Best-effort raw ID3 recovery for MP3s rejected by normal tag readers.

    This is deliberately conservative: recovered values only fill otherwise-empty
    display fields.  It never overwrites a valid ffprobe tag and it does not infer
    Artist or Album from directory names.
    """
    if audio_path.suffix.casefold() != ".mp3":
        return {}
    try:
        with audio_path.open("rb") as handle:
            header = handle.read(10)
            if len(header) != 10 or header[:3] != b"ID3":
                return {}
            major = header[3]
            if major not in {3, 4}:
                return {}
            tag_size = _id3_synchsafe_int(header[6:10])
            if tag_size <= 0 or tag_size > 64 * 1024 * 1024:
                return {}
            body = handle.read(tag_size)
    except OSError:
        return {}

    # Skip an extended header when present.  This is uncommon here, but keeping
    # the raw reader standards-aware prevents false frame IDs on healthy files.
    position = 0
    if header[5] & 0x40 and len(body) >= 4:
        if major == 3:
            extended_size = int.from_bytes(body[:4], "big", signed=False)
            position = min(len(body), 4 + max(0, extended_size))
        else:
            extended_size = _id3_synchsafe_int(body[:4])
            position = min(len(body), max(4, extended_size))

    recovered: dict[str, str] = {}
    frame_map = {
        "TIT2": "Song",
        "TPE1": "Artist",
        "TPE2": "Artist",  # album artist is better than nothing if TPE1 is absent
        "TALB": "Album",
        "TCON": "Genre",
        "TDRC": "Year",
        "TYER": "Year",
    }
    while position + 10 <= len(body):
        frame_header = body[position:position + 10]
        frame_id_bytes = frame_header[:4]
        if frame_id_bytes == b"\x00\x00\x00\x00":
            break
        try:
            frame_id = frame_id_bytes.decode("ascii")
        except UnicodeDecodeError:
            break
        if not re.fullmatch(r"[A-Z0-9]{4}", frame_id):
            break
        frame_size = (
            int.from_bytes(frame_header[4:8], "big", signed=False)
            if major == 3 else _id3_synchsafe_int(frame_header[4:8])
        )
        if frame_size <= 0 or position + 10 + frame_size > len(body):
            break
        payload = body[position + 10:position + 10 + frame_size]
        field = frame_map.get(frame_id)
        if field and field not in recovered:
            value = _decode_id3_text_payload(payload)
            if field == "Year":
                match = re.search(r"\b(?:19|20)\d{2}\b", value)
                value = match.group(0) if match else value[:4]
            if value:
                recovered[field] = value
        elif frame_id == "COMM" and "Comment" not in recovered and len(payload) > 4:
            # COMM = encoding byte + three-byte language + description + text.
            encoding = payload[0]
            rest = payload[4:]
            delimiter = b"\x00\x00" if encoding in {1, 2} else b"\x00"
            split_at = rest.find(delimiter)
            text_payload = bytes([encoding]) + (rest[split_at + len(delimiter):] if split_at >= 0 else rest)
            value = _decode_id3_text_payload(text_payload)
            if value:
                recovered["Comment"] = value
        elif frame_id in {"WOAR", "WOAF", "WOAS", "WORS", "WPUB"} and "URL" not in recovered:
            value = payload.decode("latin1", errors="replace").strip("\x00 \t\r\n")
            if re.match(r"https?://", value, flags=re.I):
                recovered["URL"] = value
        position += 10 + frame_size
    return recovered


def _fallback_song_title_from_filename(audio_path: Path) -> str:
    """Turn a filename such as ``19_Scott.mp3`` into a safe title fallback."""
    stem = audio_path.stem.strip()
    # Only strip a leading number when it is visibly a track prefix.  A song
    # genuinely named ``1984.mp3`` therefore remains ``1984``.
    title = re.sub(r"^\s*\d{1,3}\s*[-_.]+\s*", "", stem, count=1)
    title = re.sub(r"_+", " ", title).strip()
    return title or stem


def probe_audio_metadata(
    audio_path: Path,
    *,
    executable: Path | None = None,
) -> tuple[float | None, dict[str, str]]:
    """Return duration and display tags from one cached ffprobe invocation."""
    cache_location = _audio_metadata_cache_location(audio_path)
    if cache_location is not None:
        cache_key, size, mtime_ns = cache_location
        cached = _AUDIO_METADATA_CACHE.get(cache_key)
        if cached is not None and cached[0] == size and cached[1] == mtime_ns:
            return cached[2], dict(cached[3])

    ffprobe = executable or ffprobe_executable()
    payload: dict[str, object] = {}
    if ffprobe is not None:
        result = subprocess.run(
            [
                str(ffprobe), "-v", "error", "-show_entries",
                "format=duration:format_tags:stream_tags", "-of", "json", str(audio_path),
            ],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        try:
            payload = json.loads(result.stdout)
        except (TypeError, ValueError, json.JSONDecodeError):
            payload = {}

    duration: float | None = None
    try:
        raw_duration = float(payload.get("format", {}).get("duration", ""))
        if math.isfinite(raw_duration) and raw_duration > 0:
            duration = raw_duration
    except (TypeError, ValueError):
        pass

    merged: dict[str, str] = {}
    sources = [payload.get("format", {}).get("tags", {})]
    sources.extend(stream.get("tags", {}) for stream in payload.get("streams", []))
    for source in sources:
        if not isinstance(source, dict):
            continue
        for key, value in source.items():
            folded = str(key).casefold()
            if folded not in merged and str(value).strip():
                merged[folded] = str(value).strip()
    year = merged.get("year", "") or merged.get("date", "")[:4]
    tags = {
        "Artist": merged.get("artist", "") or merged.get("album_artist", ""),
        "Song": merged.get("title", ""),
        "Album": merged.get("album", ""),
        "Year": year,
        "Genre": merged.get("genre", ""),
        "URL": merged.get("url", ""),
        "Comment": merged.get("comment", "") or merged.get("description", ""),
    }

    # Some damaged MP3s contain valid-looking ID3 frame headers whose text is
    # rejected by ffprobe/Mutagen because the encoding marker and payload bytes
    # disagree.  Recover only fields that the normal probe could not read.
    for field, value in _recover_raw_id3_display_tags(audio_path).items():
        if not tags.get(field) and value:
            tags[field] = value

    # A missing title is still recoverable without guessing who made the track
    # or which album it belongs to.  Keep Artist/Album blank unless the file gave
    # us trustworthy metadata, but make ``19_Scott.mp3`` display as ``Scott``.
    if not tags.get("Song"):
        tags["Song"] = _fallback_song_title_from_filename(audio_path)

    if cache_location is not None:
        cache_key, size, mtime_ns = cache_location
        _AUDIO_METADATA_CACHE[cache_key] = (size, mtime_ns, duration, dict(tags))
    return duration, tags


def probe_duration_seconds(
    audio_path: Path,
    *,
    executable: Path | None = None,
) -> float | None:
    """Return decoded duration, sharing the same cached ffprobe as tag reads."""
    duration, _tags = probe_audio_metadata(audio_path, executable=executable)
    return duration


def probe_audio_tags(audio_path: Path) -> dict[str, str]:
    """Read display tags, sharing the same cached ffprobe as duration reads."""
    _duration, tags = probe_audio_metadata(audio_path)
    return tags


def _read_lyrics_sidecar_text(path: Path) -> str:
    """Decode lyric sidecars, including UTF-16 SRT files from subtitle tools."""
    data = path.read_bytes()
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16", errors="replace")
    if data.startswith(b"\xef\xbb\xbf"):
        return data.decode("utf-8-sig", errors="replace")
    sample = data[:512]
    if sample and sample.count(b"\x00") >= max(4, len(sample) // 8):
        even_nuls = sample[0::2].count(0)
        odd_nuls = sample[1::2].count(0)
        encoding = "utf-16-be" if even_nuls > odd_nuls else "utf-16-le"
        return data.decode(encoding, errors="replace")
    return data.decode("utf-8-sig", errors="replace")


def load_lyrics(audio_path: Path) -> list[tuple[float, float | None, str]]:
    """Load timed lyrics, preferring SRT sidecars over LRC/embedded lyrics."""
    # SRT wins because it supplies explicit END timestamps for every cue.
    candidates = [audio_path.with_suffix(suffix) for suffix in (".srt", ".SRT", ".lrc", ".LRC")]
    sidecar = next((path for path in candidates if path.is_file()), None)
    if sidecar is not None:
        try:
            text = _read_lyrics_sidecar_text(sidecar)
        except OSError:
            text = ""
        timed: list[tuple[float, float | None, str]] = []
        if sidecar.suffix.casefold() == ".lrc":
            for line in text.splitlines():
                stamps = re.findall(r"\[(\d+):(\d+(?:\.\d+)?)\]", line)
                lyric = re.sub(r"(?:\[\d+:\d+(?:\.\d+)?\])+", "", line).strip()
                for minutes, seconds in stamps:
                    if lyric:
                        timed.append((int(minutes) * 60 + float(seconds), None, lyric))
        else:
            pattern = re.compile(
                r"(?ms)^\s*\d+\s*\n(\d\d):(\d\d):(\d\d)[,.](\d{3})\s*-->\s*"
                r"(\d\d):(\d\d):(\d\d)[,.](\d{3})\s*\n(.*?)(?=\n\s*\n|\Z)"
            )
            for match in pattern.finditer(text):
                values = [int(value) for value in match.groups()[:8]]
                start = values[0] * 3600 + values[1] * 60 + values[2] + values[3] / 1000
                end = values[4] * 3600 + values[5] * 60 + values[6] + values[7] / 1000
                lyric = " ".join(part.strip() for part in match.group(9).splitlines() if part.strip())
                if lyric:
                    timed.append((start, end, re.sub(r"<[^>]+>", "", lyric)))
        if timed:
            return sorted(timed)
    # Plain-text fallback: adjacent .txt or directory lyrics.txt.
    for plain_path in (audio_path.with_suffix(".txt"), audio_path.parent / "lyrics.txt"):
        if not plain_path.is_file():
            continue
        try:
            plain_text = plain_path.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue
        sections = re.split(r"(?m)^\s*\[(.+?)\]\s*$", plain_text)
        selected = plain_text
        if len(sections) > 1:
            selected = ""
            for offset in range(1, len(sections), 2):
                heading, body = sections[offset], sections[offset + 1]
                if audio_path.stem.casefold() in heading.casefold() or audio_path.name.casefold() in heading.casefold():
                    selected = body
                    break
        lines = [line.strip() for line in selected.splitlines() if line.strip() and not line.lstrip().startswith(("#", ";"))]
        if lines:
            return [(index * 4.0, None, line) for index, line in enumerate(lines)]
    ffprobe = ffprobe_executable()
    if ffprobe is None:
        return []
    result = subprocess.run(
        [str(ffprobe), "-v", "error", "-show_entries", "format_tags:stream_tags", "-of", "json", str(audio_path)],
        check=False, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        text=True, encoding="utf-8", errors="replace",
    )
    try:
        payload = json.loads(result.stdout)
    except (TypeError, ValueError, json.JSONDecodeError):
        return []
    sources = [payload.get("format", {}).get("tags", {})]
    sources.extend(stream.get("tags", {}) for stream in payload.get("streams", []))
    for source in sources:
        for key, value in source.items():
            if str(key).casefold() in {"lyrics", "unsyncedlyrics", "unsynced lyrics", "lyric"}:
                lines = [line.strip() for line in str(value).splitlines() if line.strip()]
                return [(0.0, None, line) for line in lines]
    return []


def lyric_at(
    entries: list[tuple[float, float | None, str]],
    position: float,
    fade_seconds: float = LYRIC_FADE_SECONDS,
) -> tuple[int, str, float] | None:
    """Return the lyric and its fade opacity at a playback position."""
    if not entries:
        return None
    fade_seconds = max(0.0, fade_seconds)
    timed = any(start > 0 or end is not None for start, end, _text in entries)
    if not timed:
        slot = 4.0
        index = min(len(entries) - 1, max(0, int(position // slot)))
        within = position - index * slot
        fade_start = max(0.0, slot - fade_seconds)
        opacity = 1.0 if within <= fade_start else max(0.0, (slot - within) / max(0.001, fade_seconds))
        return index, entries[index][2], opacity
    active_index = max(
        (index for index, (start, _end, _text) in enumerate(entries) if start <= position),
        default=-1,
    )
    if active_index < 0:
        return None
    start, explicit_end, text = entries[active_index]
    next_start = entries[active_index + 1][0] if active_index + 1 < len(entries) else None
    if explicit_end is not None:
        fade_start = explicit_end
        fade_end = explicit_end + fade_seconds
    elif next_start is not None:
        maximum_fade_start = start + LYRIC_MAX_UNTIMED_SECONDS
        if next_start > maximum_fade_start + fade_seconds:
            fade_start = maximum_fade_start
            fade_end = fade_start + fade_seconds
        else:
            # Keep the current cue fully bright until its scheduled end.
            fade_start = next_start
            fade_end = next_start + fade_seconds
    else:
        fade_start = start + LYRIC_MAX_UNTIMED_SECONDS
        fade_end = fade_start + fade_seconds
    if position > fade_end:
        return None
    opacity = 1.0 if position <= fade_start else max(
        0.0, (fade_end - position) / max(0.001, fade_end - fade_start)
    )
    return active_index, text, opacity


def lyric_title_text_at(
    entries: list[tuple[float, float | None, str]],
    position: float,
    short_gap_seconds: float = LYRIC_TITLE_RETURN_TO_SONG_GAP_SECONDS,
) -> str | None:
    """Return the lyric that should exclusively occupy the console title bar.

    A sung line owns the title through its cue.  If the next nonblank lyric is
    less than ``short_gap_seconds`` away, keep the just-sung line in the title
    through that brief gap instead of flashing back to track metadata.
    """
    if not entries:
        return None
    short_gap_seconds = max(0.0, short_gap_seconds)
    timed = any(start > 0 or end is not None for start, end, _text in entries)
    if not timed:
        active = lyric_at(entries, position)
        return active[1].strip() if active is not None and active[1].strip() else None

    # Most recent nonblank lyric whose cue has begun.
    current_index = max(
        (
            index
            for index, (start, _end, text) in enumerate(entries)
            if start <= position and text.strip()
        ),
        default=-1,
    )
    if current_index < 0:
        return None
    start, explicit_end, text = entries[current_index]

    next_any_start = (
        entries[current_index + 1][0]
        if current_index + 1 < len(entries)
        else None
    )
    if explicit_end is not None:
        cue_end = explicit_end
    elif next_any_start is not None:
        cue_end = next_any_start
    else:
        cue_end = start + LYRIC_MAX_UNTIMED_SECONDS

    if position <= cue_end:
        return text.strip()

    next_nonblank_start = next(
        (
            cue_start
            for cue_start, _cue_end, cue_text in entries[current_index + 1:]
            if cue_text.strip()
        ),
        None,
    )
    if (
        next_nonblank_start is not None
        and next_nonblank_start > position
        and next_nonblank_start - cue_end < short_gap_seconds
    ):
        return text.strip()
    return None


def lyric_neighbor_opacities(
    entries: list[tuple[float, float | None, str]],
    index: int,
    position: float,
) -> tuple[float, float]:
    """Return previous fade-out and next fade-in brightness factors."""
    if not 0 <= index < len(entries):
        return 0.0, 0.0
    timed = any(start > 0 or end is not None for start, end, _text in entries)
    cue_start = entries[index][0] if timed else index * 4.0
    next_start = (
        entries[index + 1][0] if timed else (index + 1) * 4.0
    ) if index + 1 < len(entries) else None

    previous_duration = LYRIC_PREVIOUS_FADE_MAX_SECONDS
    if next_start is not None:
        previous_duration = min(previous_duration, max(0.001, next_start - cue_start))
    previous_progress = min(1.0, max(0.0, (position - cue_start) / max(0.001, previous_duration)))
    previous_brightness = LYRIC_NEIGHBOR_MAX_BRIGHTNESS * (1.0 - previous_progress)

    next_brightness = 0.0
    if next_start is not None:
        fade_end = max(cue_start, next_start - LYRIC_PREVIEW_LEAD_SECONDS)
        fade_duration = min(
            LYRIC_NEXT_FADE_MAX_SECONDS,
            max(0.001, fade_end - cue_start),
        )
        fade_start = fade_end - fade_duration
        next_progress = min(1.0, max(0.0, (position - fade_start) / fade_duration))
        next_brightness = LYRIC_NEIGHBOR_MAX_BRIGHTNESS * next_progress
    return previous_brightness, next_brightness


def lyric_scroll_rows(elapsed: float) -> tuple[int, int, int] | None:
    """Return normal-height previous/current/next rows for a cue transition."""
    step_seconds = max(0.001, LYRIC_SCROLL_STEP_SECONDS)
    step = max(0, int(max(0.0, elapsed) / step_seconds))
    if step >= max(1, LYRIC_SCROLL_ROW_STEPS):
        return None
    # The settled bands are adjacent at 0/1, 2/3, and 4/5. Moving upward by
    # two normal rows places each double-height line exactly in its predecessor's
    # band; there is no longer a blank spacer row to scroll through.
    # Start from the *old* three bands and move them upward. At cue change,
    # previous_entry was the old current (2/3), lyric_text was the old next
    # (4/5), and next_entry starts just below the visible lyric area (6/7).
    # After one intermediate row, the normal settled repaint lands at 0/1,
    # 2/3, 4/5. This prevents the current line overshooting to row 1 and
    # snapping back down to row 2.
    return 2 - step, 4 - step, 6 - step




def terminal_cell_width(text: str) -> int:
    """Measure Unicode by terminal cells instead of Python code points."""
    return max(0, wcswidth(text))


def terminal_display_signature() -> tuple[int, int, int, int]:
    '''Include font-cell geometry so text-size changes trigger a redraw.'''
    now = time.monotonic()
    cached = getattr(terminal_display_signature, '_cached', None)
    cached_at = getattr(terminal_display_signature, '_cached_at', -10.0)
    if cached is not None and now - cached_at < 0.5:
        return cached
    size = shutil.get_terminal_size((120, 30))
    cell_width = cell_height = 0
    try:
        from clairecjs_utils.claire_terminal_geometry import query_terminal_geometry
        geometry = query_terminal_geometry()
        cell_width = int(geometry.cell_width)
        cell_height = int(geometry.cell_height)
    except (ImportError, AttributeError, OSError, TypeError, ValueError):
        pass
    signature = size.columns, size.lines, cell_width, cell_height
    terminal_display_signature._cached = signature
    terminal_display_signature._cached_at = now
    return signature


def compensate_double_height_cells(text: str) -> str:
    '''Add the cell Windows Terminal fails to advance for wide DECDHL glyphs.'''
    clusters: list[str] = []
    cluster = ''
    for character in text:
        continuing = bool(cluster) and (
            unicodedata.combining(character)
            or ord(character) in {0x200D, 0xFE0E, 0xFE0F}
            or cluster.endswith(chr(0x200D))
        )
        if cluster and not continuing:
            clusters.append(cluster)
            cluster = ''
        cluster += character
    if cluster:
        clusters.append(cluster)
    def needs_terminal_workaround(item: str) -> bool:
        emoji_presentation = any(
            ord(character) == 0xFE0F
            or 0x1F000 <= ord(character) <= 0x1FAFF
            for character in item
        )
        return emoji_presentation and terminal_cell_width(item) >= 2

    # Windows Terminal already advances emoji/wide glyphs correctly; adding
    # unconditional spacers caused the visible gaps in karaoke lines.
    return ''.join(clusters)


ANSI_CSI_RE = re.compile(
    r"\x1b(?:\[[0-?]*[ -/]*[@-~]|#[0-9]|[()][ -~]|\]8;;.*?(?:\x07|\x1b\\))",
    re.DOTALL,
)


def truncate_ansi_to_cells(text: str, maximum_cells: int) -> str:
    """Truncate styled text without counting or cutting ANSI CSI sequences."""
    result: list[str] = []
    visible = ""
    index = 0
    while index < len(text):
        match = ANSI_CSI_RE.match(text, index)
        if match:
            result.append(match.group(0))
            index = match.end()
            continue
        character = text[index]
        if terminal_cell_width(visible + character) > max(0, maximum_cells):
            break
        result.append(character)
        visible += character
        index += 1
    return "".join(result) + "\033]8;;\033\\\033[0m\033[K"


def truncate_to_cells(text: str, maximum_cells: int, ellipsis: str = "") -> str:
    """Fit Unicode text to a cell budget without counting zero-width marks."""
    budget = max(0, maximum_cells - terminal_cell_width(ellipsis))
    result = ""
    for character in text:
        candidate = result + character
        if terminal_cell_width(candidate) > budget:
            break
        result = candidate
    return result.rstrip() + (ellipsis if terminal_cell_width(text) > maximum_cells else "")


def center_to_cells(text: str, width: int) -> str:
    """Center Unicode using its rendered cell width."""
    remaining = max(0, width - terminal_cell_width(text))
    left = remaining // 2
    return " " * left + text + " " * (remaining - left)


def wrap_to_cells(text: str, width: int) -> list[str]:
    """Word-wrap Unicode against terminal cells, splitting oversized words."""
    width = max(1, width)
    lines: list[str] = []
    current = ""
    for word in text.split():
        proposal = word if not current else current + " " + word
        if terminal_cell_width(proposal) <= width:
            current = proposal
            continue
        if current:
            lines.append(current)
            current = ""
        while terminal_cell_width(word) > width:
            chunk = truncate_to_cells(word, width)
            if not chunk:
                break
            lines.append(chunk)
            word = word[len(chunk):]
        current = word
    if current or not lines:
        lines.append(current)
    return lines


def hashed_word_rgb(word: str) -> tuple[int, int, int]:
    """Match print_with_columns.py's SHA-256/HSL foreground-color hash."""
    cleaned = unicodedata.normalize("NFC", word[:19].upper())
    cleaned = cleaned.replace("'", "").replace("’", "").replace("`", "").replace("-", "").replace(".", "")
    hue = int(hashlib.sha256(cleaned.encode("utf-8")).hexdigest(), 16) % 360
    red, green, blue = colorsys.hls_to_rgb(hue / 360, 0.5, 0.9)
    return round(red * 255), round(green * 255), round(blue * 255)


def colorize_karaoke_text(
    text: str,
    treatment: int,
    seed: int = 0,
    brightness: float = 1.0,
) -> str:
    """Apply foreground-only truecolor without disturbing caller attributes."""
    brightness = min(1.0, max(0.0, brightness))

    def colored(rgb: tuple[int, int, int]) -> str:
        return ansi_rgb(tuple(max(0, round(component * brightness)) for component in rgb))

    mode = (treatment - 1) % len(KARAOKE_TREATMENT_NAMES)
    if mode == 0:
        return text
    if mode == 1:
        # Per‑character rainbow: apply background before each character.
        length = max(1, len(text) - 1)
        return "".join(colored(rainbow_rgb(index / length)) + char for index, char in enumerate(text))
    if mode in {2, 4}:
        # Per‑word rainbow or hashed word color: apply background before each word.
        words = list(re.finditer(r"\S+", text))
        result: list[str] = []
        cursor = 0
        for index, match in enumerate(words):
            result.append(text[cursor:match.start()])
            rgb = rainbow_rgb(index / max(1, len(words) - 1)) if mode == 2 else hashed_word_rgb(match.group(0))
            result.append(colored(rgb) + match.group(0))
            cursor = match.end()
        result.append(text[cursor:])
        return "".join(result)
    if mode == 5:
        result: list[str] = []
        cursor = 0
        for index, match in enumerate(re.finditer(r"\S+", text)):
            result.append(text[cursor:match.start()])
            selected = int(hashlib.sha256(
                f"{seed}:{index}:{match.group(0)}".encode("utf-8")
            ).hexdigest(), 16) % 5 + 1
            result.append(colorize_karaoke_text(
                match.group(0), selected, seed + index, brightness
            ))
            cursor = match.end()
        result.append(text[cursor:])
        return "".join(result)
    if mode == 6:
        selected = int(hashlib.sha256(
            f"{seed}:{text}".encode("utf-8")
        ).hexdigest(), 16) % 5 + 1
        return colorize_karaoke_text(text, selected, seed, brightness)
    # Per‑character hash: apply background before each character.
    return "".join(
        colored(tuple(70 + (int(hashlib.sha256(f"{seed}:{index}:{channel}".encode()).hexdigest(), 16) % 186) for channel in range(3))) + character
        for index, character in enumerate(text)
    )


def metadata_rainbow_rgb(
    position: float,
    hue_phase: float = 0.0,
    *,
    throb_seconds: float = SONG_RAINBOW_THROB_SECONDS,
    cycle_seconds: float = SONG_RAINBOW_CYCLE_SECONDS,
    pulse_phase: float = 0.0,
) -> tuple[int, int, int]:
    """Rainbow metadata with independently tunable hue-cycle and brightness-throb speeds."""
    position = max(0.0, position)
    hue = (position / max(0.001, cycle_seconds) + hue_phase) % 1.0
    pulse = 0.72 + 0.28 * (0.5 + 0.5 * math.sin(
        2.0 * math.pi * position / max(0.001, throb_seconds)
        + 2.0 * math.pi * pulse_phase
    ))
    red, green, blue = colorsys.hsv_to_rgb(hue, 0.92, pulse)
    return round(red * 255), round(green * 255), round(blue * 255)


def song_rainbow_rgb(
    position: float, throb_seconds: float = SONG_RAINBOW_THROB_SECONDS
) -> tuple[int, int, int]:
    return metadata_rainbow_rgb(position, 0.0, throb_seconds=throb_seconds)


def artist_rainbow_rgb(
    position: float, throb_seconds: float = ARTIST_RAINBOW_THROB_SECONDS
) -> tuple[int, int, int]:
    # Hue remains exactly opposite Song even though Artist brightness throbs faster.
    return metadata_rainbow_rgb(
        position, 0.5, throb_seconds=throb_seconds, pulse_phase=0.5
    )


_URL_PATTERN = re.compile(r"(?i)\bhttps?://[^\s<>\"']+")

OSC8_ST = "\033\\"
OSC8_CLOSE = "\033]8;;\033\\"

def osc8_hyperlink(url: str, label: str | None = None) -> str:
    """Return a Windows-Terminal-friendly OSC 8 hyperlink around visible text."""
    target = str(url or "").replace("\x1b", "").replace("\x07", "")
    visible = str(label if label is not None else url)
    if not target:
        return visible
    return f"\033]8;;{target}{OSC8_ST}{visible}{OSC8_CLOSE}"

def style_text_with_clickable_urls(text: str, base_style: str) -> str:
    """Apply a base ANSI style while making any complete HTTP(S) URLs OSC-8 clickable."""
    source = str(text or "")
    pieces: list[str] = [base_style]
    cursor = 0
    for match in _URL_PATTERN.finditer(source):
        pieces.append(source[cursor:match.start()])
        raw = match.group(0)
        url = raw.rstrip(".,;:)]}")
        trailing = raw[len(url):]
        if url:
            pieces.append("\033[4;38;2;100;205;255m")
            pieces.append(osc8_hyperlink(url, url))
            pieces.append("\033[0m" + base_style)
        pieces.append(trailing)
        cursor = match.end()
    pieces.append(source[cursor:])
    pieces.append("\033[0m")
    return "".join(pieces)


def extract_urls(text: str) -> list[str]:
    """Extract HTTP(S) URLs in display order, trimming sentence punctuation."""
    urls: list[str] = []
    seen: set[str] = set()
    for match in _URL_PATTERN.finditer(str(text or "")):
        url = match.group(0).rstrip(".,;:)]}")
        folded = url.casefold()
        if url and folded not in seen:
            seen.add(folded)
            urls.append(url)
    return urls


def goto_urls_from_tags(tags: dict[str, str]) -> list[str]:
    """URL tag first, then unique URLs found in Comment; cap menu choices at three."""
    ordered: list[str] = []
    seen: set[str] = set()
    for source in (tags.get("URL", ""), tags.get("Comment", "")):
        for url in extract_urls(source):
            folded = url.casefold()
            if folded not in seen:
                seen.add(folded)
                ordered.append(url)
    return ordered


def genre_emoji_for(genre: str) -> str:
    """Return one compact genre glyph, favoring the most specific match."""
    text = genre.casefold()
    if not text.strip():
        return ""
    if any(token in text for token in ("television", "tv ", "tv-", "tv/", "cartoon", "anime")):
        return "📺"
    if any(token in text for token in ("soundtrack", "movie", "film", "cinema", "motion picture")):
        return "🎥"
    if any(token in text for token in ("classical", "orchestral", "symphony", "symphonic", "chamber")):
        return "🎼"
    if "punk" in text:
        return "🧷"
    if "metal" in text:
        return "🤘"
    if "rock" in text:
        return "🎸"
    return ""


def format_tag_panel(
    tags: dict[str, str],
    *,
    artist_rgb: tuple[int, int, int] = (220, 60, 180),
    song_rgb: tuple[int, int, int] = (35, 220, 195),
    album_art_visualizer_enabled: bool = False,
    karaoke_visualizer_expansion_enabled: bool = False,
    genre_emoji_enabled: bool = ENABLE_GENRE_EMOJI,
    width: int | None = None,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Pack metadata left-to-right by priority with aligned label colons."""
    width = max(40, width or (shutil.get_terminal_size((120, 30)).columns - 1))
    indent = 3
    gap = "   "

    marker_bits: list[str] = []
    if album_art_visualizer_enabled:
        marker_bits.append("🎨")
    # 💹 expansion is the default now; only advertise the non-default disabled state.
    if not karaoke_visualizer_expansion_enabled:
        marker_bits.append("💹−")
    marker_visible = ("  " + "  ".join(marker_bits)) if marker_bits else ""
    marker_reserve_cells = terminal_cell_width("  🎨  💹−")
    marker_padding = max(0, marker_reserve_cells - terminal_cell_width(marker_visible))
    experiment_suffix = marker_visible + " " * marker_padding

    artist = str(tags.get("Artist", "") or "")
    song = str(tags.get("Song", "") or "")
    album = str(tags.get("Album", "") or "")
    year = str(tags.get("Year", "") or "")
    genre = str(tags.get("Genre", "") or "")
    url = str(tags.get("URL", "") or "")
    comment = str(tags.get("Comment", "") or "")
    last_heard = str(tags.get("Last heard", "") or "")
    if comment.strip().casefold() == "cover (front)":
        comment = ""
    primary_urls = {item.casefold() for item in extract_urls(url)}
    comment_urls = extract_urls(comment)
    # A Comment whose sole content is URL(s) already present in the real URL
    # tag adds no information, even if sentence punctuation surrounds it.
    comment_remainder = _URL_PATTERN.sub("", comment).strip(" \t\r\n.,;:()[]{}<>")
    if comment_urls and not comment_remainder and all(item.casefold() in primary_urls for item in comment_urls):
        comment = ""

    fields: list[tuple[str, str, str]] = []
    if artist:
        fields.append(("Artist", artist, "artist"))
    if song:
        fields.append(("Song", song, "song"))
    if album:
        fields.append(("Album", album, "normal"))
    if year:
        fields.append(("Year", year, "normal"))
    if last_heard:
        fields.append(("Last heard", last_heard, "normal"))
    if genre:
        genre_glyph = genre_emoji_for(genre) if genre_emoji_enabled else ""
        genre_display = genre + (f" {genre_glyph}" if genre_glyph else "") + experiment_suffix
        fields.append(("Genre", genre_display, "genre"))
    if url:
        fields.append(("URL", url, "url"))
    if comment:
        fields.append(("Comment", comment, "comment"))

    label_width = max((len(label) for label, _value, _kind in fields), default=0)
    usable = max(20, width - indent)

    def ansi_value(kind: str, value: str, *, hyperlink_target: str | None = None) -> str:
        if kind == "song":
            return ansi_rgb(song_rgb) + value + "\033[0m"
        if kind == "artist":
            return ansi_rgb(artist_rgb) + value + "\033[0m"
        if kind == "comment":
            return style_text_with_clickable_urls(value, "\033[3;38;2;175;195;215m")
        if kind == "url":
            target = hyperlink_target or value
            return "\033[4;38;2;100;205;255m" + osc8_hyperlink(target, value) + "\033[0m"
        return "\033[38;2;175;195;215m" + value + "\033[0m"

    rows_plain: list[str] = []
    rows_ansi: list[str] = []
    current_plain = " " * indent
    current_ansi = " " * indent
    current_colons: list[int] = []
    known_colon_stops: list[int] = []

    def flush() -> None:
        nonlocal current_plain, current_ansi, current_colons, known_colon_stops
        if current_plain.strip():
            rows_plain.append(current_plain.rstrip())
            rows_ansi.append(current_ansi.rstrip())
            # Earlier rows establish useful visual tab stops for later rows.
            # We only move a later field RIGHT to one of these stops when that
            # extra alignment still fits; alignment is never allowed to create
            # a wrap that the ordinary three-space gap would have avoided.
            for colon in current_colons:
                if colon not in known_colon_stops:
                    known_colon_stops.append(colon)
            known_colon_stops.sort()
        current_plain = " " * indent
        current_ansi = " " * indent
        current_colons = []

    for field_index, (label, value, kind) in enumerate(fields):
        # Fixed-width labels keep every colon vertically aligned on rows that wrap.
        label_plain = f"{label:>{label_width}}: "
        label_ansi = f"\033[2;90m{label:>{label_width}}:\033[0m "
        chunk_plain = label_plain + value
        chunk_ansi = label_ansi + ansi_value(kind, value, hyperlink_target=value if kind == "url" else None)
        separator = "" if not current_plain.strip() else gap
        if current_plain.strip() and known_colon_stops:
            current_width = terminal_cell_width(current_plain)
            default_colon = current_width + terminal_cell_width(separator) + label_width
            future_stops = [stop for stop in known_colon_stops if stop >= default_colon]
            if future_stops:
                target_colon = future_stops[0]
                aligned_gap = max(terminal_cell_width(gap), target_colon - current_width - label_width)
                aligned_separator = " " * aligned_gap
                default_fits = terminal_cell_width(current_plain + separator + chunk_plain) <= width
                aligned_fits = terminal_cell_width(current_plain + aligned_separator + chunk_plain) <= width
                if aligned_fits or not default_fits:
                    separator = aligned_separator
        # Do not strand Year at the far right of a row when it can begin the
        # next row beside the following field. This keeps Album/Year/Genre
        # groupings visually coherent while preserving the aligned colons.
        if label == "Year" and current_plain.strip() and field_index + 1 < len(fields):
            next_label, next_value, _next_kind = fields[field_index + 1]
            next_plain = f"{next_label:>{label_width}}: " + next_value
            with_year = current_plain + separator + chunk_plain
            with_year_and_next = with_year + gap + next_plain
            fresh_year = " " * indent + chunk_plain
            if (
                terminal_cell_width(with_year) <= width
                and terminal_cell_width(with_year_and_next) > width
                and terminal_cell_width(fresh_year + gap + next_plain) <= width
            ):
                flush()
                separator = ""
        if terminal_cell_width(current_plain + separator + chunk_plain) <= width:
            colon_at = terminal_cell_width(current_plain) + terminal_cell_width(separator) + label_width
            current_plain += separator + chunk_plain
            current_ansi += separator + chunk_ansi
            current_colons.append(colon_at)
            continue
        flush()
        if terminal_cell_width(" " * indent + chunk_plain) <= width:
            current_plain += chunk_plain
            current_ansi += chunk_ansi
            current_colons.append(indent + label_width)
            continue

        value_width = max(8, usable - terminal_cell_width(label_plain))
        wrapped = wrap_to_cells(value, value_width) or [""]
        first = wrapped[0]
        current_plain += label_plain + first
        current_ansi += label_ansi + ansi_value(kind, first, hyperlink_target=value if kind == "url" else None)
        current_colons.append(indent + label_width)
        flush()
        continuation_indent = " " * (indent + terminal_cell_width(label_plain))
        for continuation in wrapped[1:-1]:
            rows_plain.append(continuation_indent + continuation)
            rows_ansi.append(continuation_indent + ansi_value(kind, continuation, hyperlink_target=value if kind == "url" else None))
        if len(wrapped) > 1:
            current_plain = continuation_indent + wrapped[-1]
            current_ansi = continuation_indent + ansi_value(kind, wrapped[-1], hyperlink_target=value if kind == "url" else None)
    flush()
    return tuple(rows_plain), tuple(rows_ansi)

def interpret_console_key(
    first: str,
    *,
    extended: str | None = None,
    shift: bool = False,
    ctrl: bool = False,
    alt: bool = False,
) -> str | None:
    """Translate one Windows console key event into a playback action."""
    if first in {"\x03", "\x17"}:
        return STOP
    # Escape is deliberately non-destructive during normal playback.  It is
    # still consumed by modal menus as their local cancel/back key.
    if first == "\x1b":
        return DISMISS_OVERLAY
    if first == "?":
        return HELP_OVERLAY
    if first == "\x0b":
        return KARAOKE_FAVORITE_TOGGLE if alt else KARAOKE_TREATMENT_NEXT
    if first.casefold() in {"q", "x"}:
        return STOP
    if first == " ":
        return PAUSE_TOGGLE
    # Ctrl+Alt+V is intentionally reserved for the terminal/user.
    if ctrl and alt and first.casefold() == "v":
        return None
    if ctrl and alt and first.casefold() == "l":
        return LASTFM_SCROBBLE_NOW
    if first == "\x07" or (ctrl and first.casefold() == "g"):
        return GOTO_URL
    if ctrl and first.casefold() in {"l", "r"}:
        return REDRAW_UI
    if first.casefold() == "p":
        return PROGRESS_STYLE_PREVIOUS if shift else PROGRESS_STYLE_NEXT
    if first == "=":
        return VOLUME_RESET
    if first.casefold() == "l":
        return LOOP_TOGGLE
    if first.casefold() == "r":
        return RANDOM_TOGGLE
    if first.casefold() == "f":
        if shift:
            return FADE_PREVIOUS
        if alt:
            return FADE_NEXT
        return FAVORITE_MENU
    if first == "*":
        return VISUALIZER_FAVORITE_CYCLE
    if first.casefold() == "c" and not ctrl:
        return COLOR_FAVORITE_CYCLE if alt else (COLOR_PREVIOUS if shift else COLOR_NEXT)
    if first.casefold() == "k":
        if ctrl:
            return KARAOKE_FAVORITE_TOGGLE if alt else KARAOKE_TREATMENT_NEXT
        return KARAOKE_FAVORITE_CYCLE if alt else (KARAOKE_PREVIOUS if shift else KARAOKE_NEXT)
    if first.casefold() == "a":
        return AUTOPLAY_TOGGLE
    if first in {"2", "5", "7"}:
        return {"2": OUTPUT_STEREO, "5": OUTPUT_51, "7": OUTPUT_71}[first]
    if first.isdigit():
        return f"visualizer-mode-digit:{first}"
    if first.casefold() == "v":
        return DRCS_VISUALIZER_TOGGLE if ctrl else None
    if first.casefold() == "w" and not ctrl:
        return SIXEL_VISUALIZER_TOGGLE
    if first == "<":
        return PREVIOUS_FILE
    if first == ">":
        return NEXT_FILE
    if first == "{":
        return PREVIOUS_DIRECTORY
    if first == "}":
        return NEXT_DIRECTORY
    if first in {"+", "="}:
        return SPEED_UP
    if first in {"-", "_"}:
        return SPEED_DOWN
    if ctrl and first.casefold() in {"c", "w"}:
        return STOP
    if first not in {"\x00", "\xe0"}:
        return None
    if extended == ";":
        return UNDO_RESET_DEFAULTS if alt else RESET_DEFAULTS
    if extended == "<":
        if ctrl:
            return VISUALIZER_MODE_PREVIOUS
        return KARAOKE_TREATMENT_PREVIOUS if shift else KARAOKE_PREVIOUS
    if extended == "=":
        if ctrl:
            return VISUALIZER_MODE_NEXT
        return KARAOKE_TREATMENT_NEXT if shift else KARAOKE_NEXT
    if extended == ">":
        return STOP if alt else KARAOKE_EMOJI_TOGGLE
    if extended == "?":
        return REDRAW_UI
    if extended == "@":
        return VISUALIZER_TREATMENT_PREVIOUS if shift else VISUALIZER_MODE_PREVIOUS
    if extended == "A":
        return VISUALIZER_TREATMENT_NEXT if shift else VISUALIZER_MODE_NEXT
    # Windows F8 uses scan code 66 ("B"). Ctrl+Alt+F8 toggles the
    # experimental artwork-composited spectrum in the main visualizer area.
    if extended == "B" and ctrl and alt:
        return ALBUM_ART_VISUALIZER_TOGGLE
    # Windows F9 uses scan code 67 ("C"). Ctrl+Alt+F9 lets the DRCS
    # visualizer temporarily occupy the lyric reservation while all three
    # karaoke bands are blank.
    if extended == "C" and ctrl and alt:
        return KARAOKE_VISUALIZER_EXPAND_TOGGLE
    # Windows F10 uses scan code 68 ("D").
    if extended == "D" and shift:
        return KARAOKE_VISUALIZER_OVERLAY_TOGGLE
    # The Windows console usually encodes Ctrl+Left/Right as dedicated
    # extended scan codes 115/116 ("s"/"t"), with no live Ctrl state left
    # for GetAsyncKeyState to observe by the time msvcrt returns the event.
    if extended == "s":
        return SEEK_BACK_60
    if extended == "t":
        return SEEK_FORWARD_60
    if extended == "K":
        if ctrl:
            return SEEK_BACK_60
        return SEEK_BACK_15 if shift else SEEK_BACK_5
    if extended == "M":
        if ctrl:
            return SEEK_FORWARD_60
        return SEEK_FORWARD_15 if shift else SEEK_FORWARD_5
    if extended == "H":
        return VOLUME_UP_20 if shift else VOLUME_UP_5
    if extended == "P":
        return VOLUME_DOWN_20 if shift else VOLUME_DOWN_5
    # F4 is scan code 62 (">"); some Windows hosts report Alt+F4 as 107
    # ("k").  The asynchronous Alt/F4 check below covers other hosts.
    if alt and extended in {">", "k"}:
        return STOP
    return None


def _windows_key_down(virtual_key: int) -> bool:
    """Report a Windows modifier/key state without adding dependencies."""
    if os.name != "nt":
        return False
    import ctypes

    return bool(ctypes.windll.user32.GetAsyncKeyState(virtual_key) & 0x8000)


def _windows_question_mark_down() -> bool:
    """Question mark is Shift+/ on the standard Windows keyboard layout."""
    return os.name == "nt" and _windows_key_down(0x10) and _windows_key_down(0xBF)


def read_windows_menu_choice() -> str | None:
    """Read one raw menu choice without translating it into a player command."""
    if os.name != "nt":
        return None
    import msvcrt
    if not msvcrt.kbhit():
        return None
    first = msvcrt.getwch()
    if first in {"\x00", "\xe0"}:
        if msvcrt.kbhit():
            msvcrt.getwch()
        return None
    return first


def pause_playing_winamp() -> bool:
    """Pause Winamp only when it was playing; return whether we paused it."""
    if os.name != "nt":
        return False
    import ctypes

    user32 = ctypes.windll.user32
    hwnd = user32.FindWindowW("Winamp v1.x", None)
    if not hwnd:
        return False
    # IPC_ISPLAYING (104): 1=playing, 3=paused, 0=stopped.
    state = user32.SendMessageW(hwnd, 0x0400, 0, 104)
    if state != 1:
        return False
    # Winamp command 40046 is Pause. 40047 is Stop -- never use that here.
    user32.SendMessageW(hwnd, 0x0111, 40046, 0)
    deadline = time.monotonic() + 0.75
    while time.monotonic() < deadline:
        state = user32.SendMessageW(hwnd, 0x0400, 0, 104)
        if state == 3:
            return True
        if state != 1:
            return False
        time.sleep(0.025)
    return False


def resume_winamp_if_paused_by_preview(should_resume: bool) -> None:
    """Resume Winamp only if this preview had paused a still-running instance."""
    if not should_resume or os.name != "nt":
        return
    import ctypes

    user32 = ctypes.windll.user32
    hwnd = user32.FindWindowW("Winamp v1.x", None)
    if not hwnd:
        return
    state = user32.SendMessageW(hwnd, 0x0400, 0, 104)
    if state == 3:
        user32.SendMessageW(hwnd, 0x0111, 40046, 0)
    elif state == 0:
        user32.SendMessageW(hwnd, 0x0111, 40045, 0)


def find_winamp_executable() -> Path | None:
    """Find a conventional Winamp executable without hardcoding one install."""
    candidates: list[Path] = []
    discovered = shutil.which("winamp.exe")
    if discovered:
        candidates.append(Path(discovered))
    for variable in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        root = os.environ.get(variable)
        if root:
            candidates.extend((
                Path(root) / "Winamp" / "winamp.exe",
                Path(root) / "WinAmp" / "winamp.exe",
            ))
    try:
        import winreg
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\App Paths\winamp.exe",
        ) as key:
            value, _kind = winreg.QueryValueEx(key, None)
            candidates.insert(0, Path(str(value).strip().strip(chr(34))))
    except OSError:
        pass
    return next((path for path in candidates if path.is_file()), None)


def merged_playback_ranges(ranges: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Merge overlapping listened ranges so seeking cannot inflate play time."""
    merged: list[list[float]] = []
    for start, end in sorted(ranges):
        if merged and start <= merged[-1][1] + 0.5:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return [(start, end) for start, end in merged]


def is_lastfm_scrobble_eligible(
    duration: float | None, ranges: list[tuple[float, float]],
) -> bool:
    """Submit once at least half of a known-duration track has been heard."""
    if duration is None or duration <= 0:
        return False
    listened = sum(max(0.0, end - start) for start, end in merged_playback_ranges(ranges))
    return listened >= duration * 0.50


LASTFM_LOG_MAX_BYTES = 30 * 1024 * 1024
LASTFM_SETUP_URL = "https://www.last.fm/api/account/create"

def _lastfm_sidecar_path() -> Path:
    return Path(__file__).with_name("play_audio_file.fm")

def _lastfm_prompt_marker_path() -> Path:
    return Path(__file__).with_name("play_audio_file-lastfm-setup-asked.txt")

def load_lastfm_credentials() -> bool:
    """Load credentials from env first, then an optional local .fm sidecar."""
    if os.getenv("LASTFM_API_KEY") and os.getenv("LASTFM_API_SECRET"):
        return True
    path = _lastfm_sidecar_path()
    try:
        for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = (part.strip() for part in line.split("=", 1))
            if key in {"LASTFM_API_KEY", "LASTFM_API_SECRET", "LASTFM_USERNAME", "LASTFM_PASSWORD"} and value:
                os.environ.setdefault(key, value)
    except OSError:
        pass
    return bool(os.getenv("LASTFM_API_KEY") and os.getenv("LASTFM_API_SECRET"))

def maybe_prompt_for_lastfm_setup() -> None:
    """Ask once whether Last.fm setup guidance would be useful."""
    if load_lastfm_credentials() or _lastfm_prompt_marker_path().exists():
        return
    try:
        answer = input("\nLast.fm credentials are not configured. Do you use Last.fm? [y/N] ").strip().casefold()
    except (EOFError, KeyboardInterrupt):
        answer = ""
    marker = _lastfm_prompt_marker_path()
    try:
        marker.write_text("yes\n" if answer in {"y", "yes"} else "no\n", encoding="ascii")
    except OSError:
        pass
    if answer not in {"y", "yes"}:
        return
    print("\nTo scrobble, create a Last.fm API application and keep its API key and shared secret private.")
    print("Set LASTFM_API_KEY and LASTFM_API_SECRET as environment variables, or create")
    print(f"  {_lastfm_sidecar_path()}")
    print("with lines such as LASTFM_API_KEY=... and LASTFM_API_SECRET=... .")
    try:
        input("Press any key to open the Last.fm API page... ")
        import webbrowser
        webbrowser.open(LASTFM_SETUP_URL)
    except (EOFError, KeyboardInterrupt, OSError):
        return

def _lastfm_log_path() -> Path:
    """Use C:\\logs when available; otherwise keep a sidecar beside this script."""
    preferred = Path(r"C:\logs")
    try:
        if preferred.is_dir() or preferred.exists():
            preferred.mkdir(parents=True, exist_ok=True)
            return preferred / "play_audio_file-lastfm.log"
    except OSError:
        pass
    return Path(__file__).with_name("play_audio_file-lastfm.log")


def _append_lastfm_log(message: str) -> None:
    path = _lastfm_log_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.stat().st_size > LASTFM_LOG_MAX_BYTES:
            stamp = time.strftime("%Y%m%d")
            rolled = path.with_name(f"{path.name}.rolled-log-to-recycle-ben-for-being-over-30M.{stamp}.log.bak")
            suffix = 1
            while rolled.exists():
                rolled = path.with_name(f"{path.name}.rolled-log-to-recycle-ben-for-being-over-30M.{stamp} ({suffix}).log.bak")
                suffix += 1
            try:
                from send2trash import send2trash
                path.replace(rolled)
                send2trash(str(rolled))
            except Exception:
                if path.exists():
                    path.replace(rolled)
        with path.open("a", encoding="utf-8", errors="replace") as handle:
            handle.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {message}\n")
    except OSError:
        pass


def scrobble_track_async(
    tags: dict[str, str], duration: float | None,
    ranges: list[tuple[float, float]], started_at: int,
    status_callback=None,
    force: bool = False,
) -> bool:
    """Submit an eligible scrobble without letting network/auth block playback."""
    artist = tags.get("Artist", "").strip()
    title = tags.get("Song", "").strip()
    if not artist or not title or (not force and not is_lastfm_scrobble_eligible(duration, ranges)):
        if status_callback:
            status_callback("not logged")
        return False
    # Avoid importing the helper when Last.fm is not configured. Its import
    # intentionally validates credentials, which should never affect audio.
    if not load_lastfm_credentials():
        _append_lastfm_log(f"SKIP artist={artist!r} title={title!r}: credentials not configured")
        if status_callback:
            status_callback("not logged")
        return False

    def submit() -> None:
        try:
            from clairecjs_utils.claire_lastfm import scrobble_track
            response = scrobble_track(
                artist, title, album=tags.get("Album") or None,
                duration=round(duration) if duration else None,
                timestamp=started_at,
            )
            _append_lastfm_log(f"OK artist={artist!r} title={title!r} response={response!r}")
        except Exception as exc:
            _append_lastfm_log(f"ERROR artist={artist!r} title={title!r} error={exc!r}")
            if status_callback:
                status_callback("not logged")
            return
        if status_callback:
            status_callback("logged")

    threading.Thread(target=submit, name="lastfm-scrobble", daemon=True).start()
    return True


def read_windows_key_action() -> str | None:
    """Nonblockingly read one supported playback command on Windows."""
    if os.name != "nt":
        raise RuntimeError(
            "Interactive preview controls currently require Windows"
        )
    import msvcrt

    shift_down = _windows_key_down(0x10)
    f2_f3_down = _windows_key_down(0x71) and _windows_key_down(0x72)
    hold_name = "karaoke-treatment-megamix" if shift_down else "karaoke-style-megamix"
    other_hold = "karaoke-style-megamix" if shift_down else "karaoke-treatment-megamix"
    if f2_f3_down:
        _ASYNC_HOLD_STARTED.setdefault(hold_name, time.monotonic())
        _ASYNC_HOLD_STARTED.pop(other_hold, None)
        _ASYNC_HOLD_STAGE.pop(other_hold, None)
        elapsed = time.monotonic() - _ASYNC_HOLD_STARTED[hold_name]
        stage = _ASYNC_HOLD_STAGE.get(hold_name, 0)
        if shift_down and elapsed >= 6.0 and stage < 2:
            _ASYNC_HOLD_STAGE[hold_name] = 2
            return KARAOKE_TREATMENT_MEGAMIX2
        if elapsed >= 3.0 and stage < 1:
            _ASYNC_HOLD_STAGE[hold_name] = 1
            return KARAOKE_TREATMENT_MEGAMIX1 if shift_down else KARAOKE_STYLE_MEGAMIX
        return None
    _ASYNC_HOLD_STARTED.clear()
    _ASYNC_HOLD_STAGE.clear()

    # Function-key modifier combinations are polled directly instead of relying
    # on msvcrt to preserve Ctrl/Alt/Shift state on an extended key event.
    # Windows Terminal can deliver the F-key bytes after the modifiers have
    # already changed state, which made Ctrl+Alt+F8/F9 look like no-ops.
    ctrl_down = _windows_key_down(0x11)
    alt_down = _windows_key_down(0x12)
    shift_down = _windows_key_down(0x10)
    modified_function_keys = (
        (0x77, "B", ctrl_down and alt_down, ALBUM_ART_VISUALIZER_TOGGLE),  # F8
        (0x78, "C", ctrl_down and alt_down, KARAOKE_VISUALIZER_EXPAND_TOGGLE),  # F9
        (0x79, "D", shift_down, KARAOKE_VISUALIZER_OVERLAY_TOGGLE),  # F10
    )
    for virtual_key, scan_character, modifiers_match, action in modified_function_keys:
        latch_key = 0x400 + virtual_key
        down = bool(modifiers_match and _windows_key_down(virtual_key))
        if down and latch_key not in _ASYNC_KEY_LATCH:
            _ASYNC_KEY_LATCH.add(latch_key)
            # msvcrt may also queue the same extended key. Suppress exactly one
            # matching buffered event so a single press cannot toggle on then off.
            _ASYNC_EXTENDED_SUPPRESS_ONCE[scan_character] = time.monotonic() + 1.0
            return action
        if not _windows_key_down(virtual_key):
            _ASYNC_KEY_LATCH.discard(latch_key)

    if _windows_key_down(0x12):
        for virtual_key, action in (
            (0x43, COLOR_FAVORITE_CYCLE),
            (0x4B, KARAOKE_FAVORITE_TOGGLE if _windows_key_down(0x11) else KARAOKE_FAVORITE_CYCLE),
        ):
            latch_key = 0x100 + virtual_key
            down = _windows_key_down(virtual_key)
            if down and latch_key not in _ASYNC_KEY_LATCH:
                _ASYNC_KEY_LATCH.add(latch_key)
                return action
            if not down:
                _ASYNC_KEY_LATCH.discard(latch_key)
    media_keys = {
        0x13: PAUSE_TOGGLE,  # Pause/Break
        0xB3: PAUSE_TOGGLE,  # Media play/pause
        0xB0: SEEK_FORWARD_10,
        0xB1: SEEK_BACK_10,
        0x64: BALANCE_LEFT,
        0x66: BALANCE_RIGHT,
        0x65: BALANCE_CENTER,
    }
    for virtual_key, action in media_keys.items():
        down = _windows_key_down(virtual_key)
        if down and virtual_key not in _ASYNC_KEY_LATCH:
            _ASYNC_KEY_LATCH.add(virtual_key)
            return action
        if not down:
            _ASYNC_KEY_LATCH.discard(virtual_key)
    if not msvcrt.kbhit():
        return None
    first = msvcrt.getwch()
    shift = _windows_key_down(0x10)
    ctrl = _windows_key_down(0x11)
    alt = _windows_key_down(0x12)
    extended = (
        msvcrt.getwch() if first in {"\x00", "\xe0"} else None
    )
    if extended is not None:
        deadline = _ASYNC_EXTENDED_SUPPRESS_ONCE.get(extended)
        if deadline is not None:
            _ASYNC_EXTENDED_SUPPRESS_ONCE.pop(extended, None)
            if time.monotonic() <= deadline:
                return None
        # Discard any stale one-shot suppressions so they cannot affect a later press.
        for scan_character, expiry in tuple(_ASYNC_EXTENDED_SUPPRESS_ONCE.items()):
            if time.monotonic() > expiry:
                _ASYNC_EXTENDED_SUPPRESS_ONCE.pop(scan_character, None)
    return interpret_console_key(
        first,
        extended=extended,
        shift=shift,
        ctrl=ctrl,
        alt=alt,
    )


def ffplay_command(
    executable: Path,
    audio_path: Path,
    start_seconds: float,
    volume: int,
    speed: float = 1.0,
    output_channels: int = 2,
    balance: int = 0,
    output_rate: int = 192000,
) -> list[str]:
    """Build a quiet, audio-only FFplay command starting at an offset."""
    command = [
        str(executable),
        "-nodisp",
        "-autoexit",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        f"{max(0.0, start_seconds):.3f}",
        "-volume",
        str(min(100, volume)),
        "-ar",
        str(192000 if output_rate not in {96000, 192000} else output_rate),
    ]
    filters: list[str] = []
    if speed != 1.0:
        filters.append(atempo_filter(speed))
    if volume > 100:
        filters.append(f"volume={volume / 100:g}")
    if balance:
        balance = min(100, max(-100, balance))
        left_gain = 1.0 if balance <= 0 else 1.0 - balance / 100.0
        right_gain = 1.0 if balance >= 0 else 1.0 + balance / 100.0
        filters.append(
            f"pan=stereo|c0={left_gain:.3f}*c0|c1={right_gain:.3f}*c1"
        )
    if output_channels != 2:
        filters.append(output_expansion_filter(output_channels))
    if filters:
        command.extend(["-af", ",".join(filters)])
    return command + [str(audio_path)]


def output_expansion_filter(output_channels: int) -> str:
    """Apply Claire's MatrixMixer-style phase-derived speaker expansion."""
    if output_channels == 5:
        return (
            "aformat=channel_layouts=stereo,"
            "pan=5.1(side)|FL=FL|FR=FR|FC=0.1*FL+0.1*FR|"
            "LFE=0.25*FL+0.25*FR|SL=1.4*FL-1.4*FR|SR=-1.4*FL+1.4*FR,"
            "lowpass=f=66:c=LFE,alimiter=limit=0.95"
        )
    if output_channels == 7:
        return (
            "aformat=channel_layouts=stereo,"
            "pan=7.1|FL=FL|FR=FR|FC=0.1*FL+0.1*FR|"
            "LFE=0.25*FL+0.25*FR|BL=0.9*FL-0.9*FR|BR=-0.9*FL+0.9*FR|"
            "SL=1.4*FL-1.4*FR|SR=-1.4*FL+1.4*FR,"
            "lowpass=f=66:c=LFE,alimiter=limit=0.95"
        )
    raise ValueError(f"Unsupported output expansion: {output_channels}")


def atempo_filter(speed: float) -> str:
    """Split extreme speeds into valid FFmpeg atempo stages (0.5–2.0)."""
    factors: list[float] = []
    remaining = speed
    while remaining > 2.0:
        factors.append(2.0)
        remaining /= 2.0
    while remaining < 0.5:
        factors.append(0.5)
        remaining /= 0.5
    factors.append(remaining)
    return ",".join(f"atempo={factor:.9g}" for factor in factors)


def stop_process(process) -> None:
    """Terminate a live FFplay child and ensure it cannot linger."""
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=1.0)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=1.0)


def set_console_cursor_visible(visible: bool) -> None:
    """Set cursor visibility through Win32 as well as the ANSI caller path."""
    if os.name != "nt":
        return
    try:
        import ctypes

        class CursorInfo(ctypes.Structure):
            _fields_ = [("size", ctypes.c_uint32), ("visible", ctypes.c_int)]

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        info = CursorInfo()
        info.size = ctypes.sizeof(info)
        if kernel32.GetConsoleCursorInfo(handle, ctypes.byref(info)):
            info.visible = int(visible)
            kernel32.SetConsoleCursorInfo(handle, ctypes.byref(info))
    except (AttributeError, OSError, ValueError):
        pass
def format_position(seconds: float | None) -> str:
    """Format an optional duration or playback position compactly."""
    if seconds is None:
        return "unknown"
    whole = max(0, int(seconds))
    hours, remainder = divmod(whole, 3600)
    minutes, secs = divmod(remainder, 60)
    return (
        f"{hours}:{minutes:02d}:{secs:02d}"
        if hours
        else f"{minutes}:{secs:02d}"
    )


def format_duration_label(seconds: float | None) -> str:
    """Format a duration compactly for the preview title."""
    if seconds is None:
        return "unknown length"
    whole = max(0, int(seconds))
    hours, remainder = divmod(whole, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}h{minutes:02d}m{secs:02d}s" if hours else f"{minutes}m{secs:02d}s"


def rainbow_rgb(progress: float) -> tuple[int, int, int]:
    """Return a truecolor red-to-violet rainbow color for playback progress."""
    progress = min(1.0, max(0.0, progress))
    hue = progress * 0.75
    sector = int(hue * 6)
    fraction = hue * 6 - sector
    x = int(255 * (1 - abs((sector % 2) + fraction - 1)))
    colors = ((255, x, 0), (x, 255, 0), (0, 255, x), (0, x, 255), (x, 0, 255))
    return colors[min(sector, len(colors) - 1)]


def ansi_rgb(rgb: tuple[int, int, int]) -> str:
    return f"\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m"



def _drcs_pattern(rows: tuple[str, ...]) -> str:
    """Encode a small monochrome bitmap as the sixel payload of one DRCS glyph."""
    width = len(rows[0])
    bands: list[str] = []
    for top in range(0, len(rows), 6):
        columns: list[str] = []
        for column in range(width):
            bits = sum(
                1 << bit
                for bit in range(6)
                if top + bit < len(rows) and rows[top + bit][column] == "#"
            )
            columns.append(chr(0x3F + bits))
        bands.append("".join(columns))
    return "/".join(bands)


def define_volume_drcs() -> str:
    """Define a speaker and two wave glyphs in unused |, }, and ~ slots."""
    body = (
        "..........",
        "..........",
        "......##..",
        ".....###..",
        "....####..",
        "...#####..",
        "..######..",
        "########..",
        "########..",
        "########..",
        "########..",
        "########..",
        "########..",
        "..######..",
        "...#####..",
        "....####..",
        ".....###..",
        "......##..",
        "..........",
        "..........",
    )
    up_waves = (
        "..........",
        "..........",
        "..##......",
        "....##....",
        ".....##...",
        ".##...##..",
        "...##..##.",
        "....##..##",
        ".....#..##",
        ".....#...#",
        ".....#...#",
        ".....#..##",
        "....##..##",
        "...##..##.",
        ".##...##..",
        ".....##...",
        "....##....",
        "..##......",
        "..........",
        "..........",
    )
    down_waves = (
        "..........",
        "..........",
        "..........",
        "..........",
        "..........",
        "..##......",
        "....##....",
        ".....##...",
        "......##..",
        ".......#..",
        ".......#..",
        "......##..",
        ".....##...",
        "....##....",
        "..##......",
        "..........",
        "..........",
        "..........",
        "..........",
        "..........",
    )
    # Pcn 92 maps to |; Pe 1 only reloads these three slots.  The unregistered
    # "space @" charset is selected only while the player emits its icon.
    return (
        "\033P0;92;1;10;0;2;20;0{ @"
        + _drcs_pattern(body)
        + ";"
        + _drcs_pattern(up_waves)
        + ";"
        + _drcs_pattern(down_waves)
        + "\033\\"
    )




def define_visualizer_drcs() -> str:
    """Download nine fill-level tiles into the soft-font a-i slots."""
    patterns: list[str] = []
    for level in range(9):
        filled_rows = round(level * 20 / 8)
        rows = tuple(
            "##########" if row >= 20 - filled_rows else ".........."
            for row in range(20)
        )
        patterns.append(_drcs_pattern(rows))
    # Pcn 65 maps to ASCII a. Pe=1 preserves the volume and existing slots.
    return (
        "\033P0;65;1;10;0;2;20;0{ @"
        + ";".join(patterns)
        + "\033\\"
    )


def define_all_player_drcs() -> str:
    """Download visualizer and speaker glyphs in one soft-font definition."""
    visual_payload = define_visualizer_drcs().split("{ @", 1)[1][:-2]
    volume_payload = define_volume_drcs().split("{ @", 1)[1][:-2]
    blank = _drcs_pattern(tuple(".........." for _row in range(20)))
    # a-i are spectrum fill tiles; j-{ are deliberately unused; |, }, ~ are
    # the three speaker pieces. One download avoids Windows Terminal replacing
    # the spectrum font with the later speaker download.
    filler_count = ord("|") - ord("j")
    payload = ";".join((visual_payload, *([blank] * filler_count), volume_payload))
    return "\033P0;65;1;10;0;2;20;0{ @" + payload + "\033\\"


def build_audio_spectrum_timeline(
    audio_path: Path,
    columns: int,
    duration_limit: float | None = None,
    start_seconds: float = 0.0,
) -> tuple[bytes, int, int]:
    """Analyze the real audio into one frequency-height frame per time slice."""
    width = max(12, columns)
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return b"", width, SPECTRUM_ANALYSIS_FPS
    spectrum_filter = (
        f"showfreqs=s={width}x{SPECTRUM_ANALYSIS_HEIGHT}:mode=bar:"
        "ascale=sqrt:fscale=log:win_size=2048:overlap=0.15:"
        "averaging=1:colors=white,format=gray,"
        f"fps={SPECTRUM_ANALYSIS_FPS}"
    )
    command = [
        ffmpeg, "-v", "error", "-ss", f"{max(0.0, start_seconds):g}",
        "-i", str(audio_path),
        *(["-t", f"{duration_limit:g}"] if duration_limit is not None else []),
        "-filter_complex", f"[0:a]{spectrum_filter}[visual]",
        "-map", "[visual]", "-f", "rawvideo", "-pix_fmt", "gray", "-",
    ]
    process = None
    timeline = bytearray()
    frame_size = width * SPECTRUM_ANALYSIS_HEIGHT
    try:
        import numpy as np  # type: ignore
    except ImportError:  # pragma: no cover
        np = None
    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        if process.stdout is None:
            return b"", width, SPECTRUM_ANALYSIS_FPS
        while True:
            frame = bytearray()
            while len(frame) < frame_size:
                chunk = process.stdout.read(frame_size - len(frame))
                if not chunk:
                    break
                frame.extend(chunk)
            if len(frame) != frame_size:
                break
            if np is not None:
                pixels = np.frombuffer(frame, dtype=np.uint8).reshape(
                    SPECTRUM_ANALYSIS_HEIGHT, width
                )
                lit = pixels > 8
                any_lit = lit.any(axis=0)
                first_lit = lit.argmax(axis=0)
                raw_heights = np.where(
                    any_lit,
                    SPECTRUM_ANALYSIS_HEIGHT - first_lit,
                    0,
                )
                scaled = np.minimum(
                    SPECTRUM_ANALYSIS_HEIGHT, raw_heights * 1.4
                ).astype(np.uint8)
                timeline.extend(scaled.tobytes())
                continue
            raw_frame: list[int] = []
            for column in range(width):
                first_lit_row = SPECTRUM_ANALYSIS_HEIGHT
                for row in range(SPECTRUM_ANALYSIS_HEIGHT):
                    if frame[row * width + column] > 8:
                        first_lit_row = row
                        break
                raw_height = SPECTRUM_ANALYSIS_HEIGHT - first_lit_row
                raw_frame.append(raw_height)
            timeline.extend(
                min(SPECTRUM_ANALYSIS_HEIGHT, round(height * 1.4))
                for height in raw_frame
            )
        process.wait(timeout=3)
        if process.returncode:
            return b"", width, SPECTRUM_ANALYSIS_FPS
        data = bytes(timeline)
        nonzero = sorted(value for value in data if value)
        if nonzero:
            reference = nonzero[min(len(nonzero) - 1, round(len(nonzero) * 0.97))]
            gain = (SPECTRUM_ANALYSIS_HEIGHT * 0.94) / max(1, reference)
            data = bytes(
                min(SPECTRUM_ANALYSIS_HEIGHT, round(value * gain))
                for value in data
            )
        return data, width, SPECTRUM_ANALYSIS_FPS
    except (OSError, subprocess.TimeoutExpired):
        if process is not None and process.poll() is None:
            process.kill()
        return b"", width, SPECTRUM_ANALYSIS_FPS


def spectrum_frame_at(
    timeline: tuple[bytes, int, int],
    position: float,
) -> bytes:
    """Return the analyzed frequency heights nearest a playback position."""
    data, width, frames_per_second = timeline
    frame_count = len(data) // width
    if not frame_count:
        return b""
    frame_index = min(
        frame_count - 1,
        max(0, int(position * frames_per_second)),
    )
    start = frame_index * width
    return data[start:start + width]


def visualizer_mode_heights(
    spectrum_levels: bytes,
    width: int,
    mode: int,
) -> list[float]:
    """Transform one spectrum frame into one of thirty comparison styles."""
    source_width = len(spectrum_levels)
    mode = min(len(VISUALIZER_MODE_NAMES), max(1, mode))
    horizontal_power = 2.30 if mode == 1 else 2.40
    values = [
        (
            spectrum_levels[
                round(
                    ((column / max(1, width - 1)) ** horizontal_power)
                    * (source_width - 1) * 0.90
                )
            ] / SPECTRUM_ANALYSIS_HEIGHT
        ) if source_width else 0.0
        for column in range(width)
    ]
    # showfreqs naturally overstates the first logarithmic bins. Apply a
    # frequency-dependent compensation in every mode so bass can still peak
    # without living permanently at the ceiling.
    values = [
        max(0.0, value * (0.30 + 0.70 * ((column + 1) / width) ** 0.30) - 0.065)
        for column, value in enumerate(values)
    ]
    treatment = (mode - 1) // len(VISUALIZER_TYPE_NAMES)
    visualizer_type = (mode - 1) % len(VISUALIZER_TYPE_NAMES)
    radii = (0, 1, 2, 3, 0, 1, 2, 0, 3, 1, 0, 2, 4, 0, 1)
    radius = radii[treatment]
    if radius:
        values = [
            sum(values[max(0, index - radius):min(width, index + radius + 1)])
            / len(values[max(0, index - radius):min(width, index + radius + 1)])
            for index in range(width)
        ]
    if treatment in {1, 6, 11}:  # tighter valleys
        values = [max(0.0, value - 0.08) for value in values]
    elif treatment in {3, 8, 13}:  # pulse-like compression
        values = [value ** 0.72 for value in values]
    elif treatment in {4, 9, 14}:  # stepped skyline
        values = [round(value * 8) / 8 for value in values]
    elif treatment in {5, 10}:  # emphasize upper-frequency sparks
        values = [value * (0.72 + 0.38 * index / max(1, width - 1)) for index, value in enumerate(values)]
    gammas = (1.0, 1.28, 0.78, 1.08, 0.62, 1.5, 0.9, 1.15, 0.7, 1.35, 0.82, 1.7, 0.55, 1.02, 1.22)
    gains = (0.90, 0.78, 0.98, 0.76, 1.0, 0.72, 0.88, 0.82, 1.0, 0.74, 0.96, 0.68, 1.0, 0.86, 0.80)
    type_gain = 1.08 if visualizer_type == 0 else (0.95 if visualizer_type == 1 else 1.0)
    return [min(1.0, max(0.0, value) ** gammas[treatment] * gains[treatment] * type_gain) for value in values]


def visualizer_color(style: int, row: int, column: int, width: int, rows: int = DRCS_VISUALIZER_ROWS) -> tuple[int, int, int]:
    """Return one of thirty spectrum color treatments."""
    style = (style - 1) % 30  # Color 31/32 are energy-aware renderer special cases.
    group, variant = divmod(style, 6)
    vertical = row / max(1, rows - 1)
    horizontal = column / max(1, width - 1)
    hue = (vertical * 0.78 + variant / 6 + horizontal * (0.08 * group)) % 1.0
    if group == 1:
        hue = (1.0 - vertical * 0.78 + variant / 6) % 1.0
    elif group == 2:
        # Colors 13–18 are the horizontal-spectrum family. Color 15 is
        # Prism: a broad left-to-right ROYGBIV sweep with a subtle vertical
        # bend, keeping neighboring spectrum bands visually distinct.
        horizon_cycles = (0.68, 0.78, 0.96, 1.08, 0.88, 0.74)
        horizon_offsets = (0.02, 0.12, 0.00, 0.90, 0.54, 0.72)
        horizon_bends = (0.03, -0.04, 0.07, -0.06, 0.05, -0.03)
        hue = (
            horizon_offsets[variant]
            + horizontal * horizon_cycles[variant]
            + (1.0 - vertical) * horizon_bends[variant]
        ) % 1.0
    saturation = (1.0, 0.82, 0.68, 1.0, 0.9)[group]
    value = (1.0, 0.88, 1.0, 0.78, 0.94)[group]
    red, green, blue = colorsys.hsv_to_rgb(hue, saturation, value)
    return round(red * 255), round(green * 255), round(blue * 255)


def render_drcs_visualizer(
    columns: int,
    spectrum_levels: bytes,
    recent_energy: list[float],
    mode: int = 1,
    color_style: int = 1,
    rows: int = DRCS_VISUALIZER_ROWS,
    fade_style: int = 1,
    truncate_top_lines: int = TRUNCATE_TOP_VISUALIZER_LINES,
) -> str:
    """Render exactly *rows* terminal rows after dropping top spectrum bands."""
    width = max(12, columns)
    heights = visualizer_mode_heights(spectrum_levels, width, mode)

    lines: list[str] = []
    rows = max(1, rows)
    truncate_top_lines = max(0, int(truncate_top_lines))
    # Add virtual source bands above the visible canvas, then omit them. This
    # truly truncates low-probability top bands WITHOUT reserving blank rows.
    source_rows = rows + truncate_top_lines
    for row in range(truncate_top_lines, source_rows):
        threshold = 1 - (row + 1) / source_rows
        glyphs: list[str] = []
        last_color: tuple[int, int, int] | None = None
        for column, height in enumerate(heights):
            coverage = (height - threshold) * rows
            level = min(8, max(0, round(coverage * 8)))
            source_column = (
                round(column * (len(recent_energy) - 1) / max(1, width - 1))
                if recent_energy else 0
            )
            energy = recent_energy[source_column] if recent_energy else 0.0
            energy = round(max(0.0, min(1.0, energy)) * 15) / 15
            brightness = energy ** 1.5
            fade_style = (fade_style - 1) % len(FADE_STYLE_NAMES) + 1
            instant_amplitude = min(1.0, max(0.0, height))
            if color_style == 31:
                # Every cell in one column takes its hue from the live column
                # amplitude; normal recent-energy brightness still handles fade.
                red, green, blue = colorsys.hsv_to_rgb(0.76 * (1.0 - instant_amplitude), 1.0, 1.0)
                base_color = (round(red * 255), round(green * 255), round(blue * 255))
            elif color_style == 32:
                # A new hit is red. Once its live level drops, the retained
                # energy trail moves toward purple while dimming normally.
                impact = instant_amplitude / max(0.001, energy)
                impact = min(1.0, max(0.0, impact))
                violet, red = (145, 0, 255), (255, 32, 0)
                base_color = tuple(round(violet[index] * (1.0 - impact) + red[index] * impact) for index in range(3))
            else:
                base_color = visualizer_color(color_style, row, column, width, source_rows)
            if fade_style == 2:
                base_color = rainbow_rgb(1.0 - energy * 0.75)
            elif fade_style == 3:
                brightness = 1.0 if energy >= 0.35 else energy * 0.25
            elif fade_style == 4:
                brightness *= 0.55 + 0.45 * energy
            if (mode - 1) // len(VISUALIZER_TYPE_NAMES) == len(VISUALIZER_TREATMENT_NAMES) - 1:
                # Special final treatment: high-energy bars are red; as they
                # decay, their hue travels through ROYGBIV toward violet.
                base_color = rainbow_rgb(1.0 - energy * 0.75)
            color = tuple(round(component * brightness) for component in base_color)
            if color != last_color:
                glyphs.append(ansi_rgb(color))
                last_color = color
            visualizer_type = (mode - 1) % len(VISUALIZER_TYPE_NAMES)
            palette = (VISUALIZER_GLYPH_PALETTES[visualizer_type] + "█████████")[:9]
            glyphs.append(palette[level])
        visualizer_type = (mode - 1) % len(VISUALIZER_TYPE_NAMES)
        if visualizer_type in {0, 1}:
            lines.append("\033( @" + "".join(glyphs) + "\033(B\033[0m\033[K")
        else:
            lines.append("".join(glyphs) + "\033(B\033[0m\033[K")
    return ("\r\n" + BIG_OFF).join(lines)


def volume_icon(direction: str) -> str:
    """Render a dedicated blue-body/white-waves DRCS speaker icon."""
    waves = VOLUME_DRCS_UP_WAVES if direction == "up" else VOLUME_DRCS_DOWN_WAVES
    return (
        "\033( @"
        + f"\033[38;2;255;255;255m{VOLUME_DRCS_BODY}"
        + f"\033[38;2;70;150;255m{waves}"
        + "\033(B\033[0m"
    )


def volume_status(volume: int, direction: str) -> str:
    """Show non-default volume on its own red-to-violet rainbow scale."""
    if volume == 100:
        return ""
    color = ansi_rgb(rainbow_rgb(1 - (max(0, min(100, volume)) / 100)))
    return f"        {volume_icon(direction)} {color}Volume: {int(volume)}%\033[0m"


def volume_status_plain(volume: int, direction: str = "up") -> str:
    """Return the visible volume text without ANSI styling."""
    return "" if volume == 100 else f"        🔊 Volume: {int(volume)}%"


def format_speed(speed: float) -> str:
    return f"{speed:g}×"


def speed_color(speed: float, progress: float) -> str:
    """Use faint help color at 1× and a speed ladder elsewhere."""
    if speed == 1.0:
        return "\033[2;90m"
    index = PLAYBACK_SPEEDS.index(speed)
    # Keep the slow end in a brighter blue/violet band instead of reaching the
    # darkest extreme of the full rainbow. Fastest remains the reddest.
    normalized = 1 - index / (len(PLAYBACK_SPEEDS) - 1)
    hue = normalized * 0.65
    return ansi_rgb(rainbow_rgb(hue))


def loop_status(looping: bool, progress: float) -> str:
    """Show the persistent state in the same red-to-violet playback color."""
    icon = "🔁" if looping else "➡️"
    return (
        f"        {icon}"
        + ansi_rgb(rainbow_rgb(progress))
        + f" Loop: {'On' if looping else 'Off'}\033[0m"
    )


def loop_status_plain(looping: bool) -> str:
    """Return the visible loop state without ANSI styling."""
    return f"        {'🔁' if looping else '➡️'} Loop: {'On' if looping else 'Off'}"


def render_status(
    position: float,
    duration: float | None,
    indicator: str,
    volume: int,
    volume_direction: str,
    looping: bool,
    bar_width: int,
    *,
    repaint: bool,
    progress_style: int = 1,
    pulse_energy: float = 0.0,
) -> str:
    """Render repaintable time and progress-bar rows."""
    fraction = min(1.0, max(0.0, position / duration)) if duration else 0.0
    percentage = int(fraction * 100)
    filled_eighth_cells = round(bar_width * 8 * fraction)
    full_cells, partial_eighth = divmod(filled_eighth_cells, 8)
    pairs = (
        ("█", "░"), ("▓", "·"), ("■", "□"), ("━", "─"), ("▰", "▱"),
        ("●", "○"), ("◆", "◇"), ("▮", "▯"), ("▉", "▏"), ("#", "."),
        ("=", "-"), ("▇", "▁"), ("▆", "▂"), ("▣", "▢"), ("█", " "),
        (">", " "), ("*", "."), ("+", "."), ("X", "x"), ("|", "."),
        ("■", "·"), ("▰", "▱"), ("▸", "▹"), ("●", "·"), ("◆", "·"),
    )
    filled_char, empty_char = pairs[(progress_style - 1) % len(pairs)]
    # Unicode left-block fractions give 1/8-cell granularity without consuming
    # another terminal column: ▏▎▍▌▋▊▉. This is 8× finer than whole cells.
    partial_blocks = ("", "▏", "▎", "▍", "▌", "▋", "▊", "▉")
    partial = partial_blocks[partial_eighth]
    empty_cells = max(0, bar_width - full_cells - (1 if partial else 0))
    bar_color = rainbow_rgb(fraction)
    if progress_style in {15, 25}:
        throb = 0.35 + 0.65 * max(0.0, min(1.0, pulse_energy))
        bar_color = tuple(round(component * throb) for component in bar_color)
    # A Unicode fractional block paints only the LEFT fraction of its cell.
    # If the rest of that cell (and the rest of the unplayed bar) falls back
    # to the terminal's black background, the moving 1/8-cell edge develops a
    # visible black seam.  Treat the whole unplayed remainder as one continuous
    # dim, rainbow-tinted background.  The fractional boundary cell and every
    # empty cell therefore share exactly the same background RGB.
    if empty_char in {"░", "▒", "▱", "▯", "□", "○", "◇", "▢", "▹"}:
        empty_bg_strength = 0.22
    else:
        empty_bg_strength = 0.10
    empty_bg_strength *= PROGRESS_EMPTY_BACKGROUND_BRIGHTNESS_BOOST
    empty_bg = tuple(
        min(255, round(component * empty_bg_strength))
        for component in bar_color
    )
    empty_bg_ansi = f"\033[48;2;{empty_bg[0]};{empty_bg[1]};{empty_bg[2]}m"

    partial_ansi = ""
    if partial:
        partial_ansi = (
            ansi_rgb(bar_color)
            + empty_bg_ansi
            + partial
            + "\033[49m"
        )
    empty_ansi = ""
    if empty_cells:
        # The unplayed remainder is deliberately texture-free: its tinted
        # background alone forms the bar, while the fractional edge stays crisp.
        empty_ansi = empty_bg_ansi + (" " * empty_cells) + "\033[49m"
    bar_ansi = (
        ansi_rgb(bar_color)
        + filled_char * full_cells
        + partial_ansi
        + empty_ansi
    )

    # The clock, optional volume readout, and progress bar share one row.
    # The caller positions the cursor at STATUS_ROW, so repainting must not
    # move vertically; that was the source of the old blank row above the
    # visualizer.
    prefix = "\r\033[2K"
    clock = (
        f"{indicator} {format_position(position)}"
        + (f" / {format_position(duration)}" if duration is not None else "")
    )
    volume_text = volume_status(volume, volume_direction)
    return (
        prefix + ansi_rgb(rainbow_rgb(fraction)) + clock + "\033[0m"
        + volume_text + "  "
        + bar_ansi + f" {percentage}%\033[0m"
    )


def write_console(text: str) -> None:
    if _CURSOR_SUPPRESSION_ACTIVE:
        text += "\033[?25l"
    sys.stdout.write(text)
    sys.stdout.flush()


def write_console_bytes(data: bytes) -> None:
    """Write a terminal protocol payload without a text transcoding round trip."""
    sys.stdout.flush()
    binary_output = getattr(sys.stdout, "buffer", None)
    if binary_output is None:
        sys.stdout.write(data.decode("ascii", errors="ignore"))
        sys.stdout.flush()
        return
    binary_output.write(data)
    binary_output.flush()
    if _CURSOR_SUPPRESSION_ACTIVE:
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()


def get_console_title() -> str:
    '''Read the current application title without printing an OSC sequence.'''
    if os.name != 'nt':
        return ''
    try:
        import ctypes
        buffer = ctypes.create_unicode_buffer(1024)
        ctypes.windll.kernel32.GetConsoleTitleW(buffer, len(buffer))
        return buffer.value
    except (AttributeError, OSError):
        return ''


def set_console_title(title: str) -> None:
    '''Set the Windows Terminal tab/console title.'''
    if os.name != 'nt':
        return
    try:
        import ctypes
        ctypes.windll.kernel32.SetConsoleTitleW(str(title))
    except (AttributeError, OSError):
        pass


def _album_art_priority(path: Path) -> tuple[int, tuple[object, ...]]:
    """Sort nearby artwork as cover > back > cd > inlay* > other > matrix."""
    stem = path.stem.casefold()
    if "matrix" in stem:
        priority = 5
    elif stem.startswith("cover"):
        priority = 0
    elif stem.startswith("back"):
        priority = 1
    elif stem == "cd":
        priority = 2
    elif stem.startswith("inlay"):
        priority = 3
    else:
        priority = 4
    return priority, natural_path_key(path)


def _all_nearby_image_files(audio_path: Path) -> list[Path]:
    try:
        return [
            path for path in audio_path.parent.iterdir()
            if path.is_file()
            and path != audio_path
            and path.suffix.casefold() in ALBUM_ART_IMAGE_EXTENSIONS
        ]
    except OSError:
        return []


def _folder_uses_per_track_sidecar_art(audio_path: Path, images: list[Path] | None = None) -> bool:
    """Detect loose-song folders where JPGs belong to individual audio stems."""
    images = _all_nearby_image_files(audio_path) if images is None else images
    exact = [path for path in images if path.stem.casefold() == audio_path.stem.casefold()]
    if not exact:
        return False
    audio = audio_files_in(audio_path.parent)
    if len(audio) < 2:
        return False
    image_stems = {path.stem.casefold() for path in images}
    matched_sidecars = sum(path.stem.casefold() in image_stems for path in audio)
    # Album folders normally number every track; loose collections frequently
    # do not. Two or more exact audio↔image stem matches is strong evidence that
    # unrelated JPGs are per-track sidecars rather than shared album artwork.
    all_numbered = all(bool(re.match(r"^\s*\d{1,3}(?:[\s._-]|$)", path.stem)) for path in audio)
    return matched_sidecars >= 2 and not all_numbered


def _album_art_candidates(audio_path: Path) -> list[Path]:
    """Return appropriate nearby art, isolating exact sidecars in loose-song folders."""
    candidates = _all_nearby_image_files(audio_path)
    if _folder_uses_per_track_sidecar_art(audio_path, candidates):
        exact = [path for path in candidates if path.stem.casefold() == audio_path.stem.casefold()]
        return sorted(exact, key=natural_path_key)
    return sorted(candidates, key=_album_art_priority)


def extract_album_art(audio_path: Path) -> bytes | None:
    """Extract embedded cover art once, falling back to preferred nearby art."""
    try:
        stat = audio_path.stat()
        cache_key = (str(audio_path.resolve()), stat.st_mtime_ns, stat.st_size)
    except OSError:
        cache_key = (str(audio_path), 0, 0)
    if cache_key in _ALBUM_ART_BYTES_CACHE:
        return _ALBUM_ART_BYTES_CACHE[cache_key]

    art: bytes | None = None
    nearby_candidates = _album_art_candidates(audio_path)
    per_track_sidecar_only = _folder_uses_per_track_sidecar_art(audio_path)
    if per_track_sidecar_only and nearby_candidates:
        try:
            art = nearby_candidates[0].read_bytes()
        except OSError:
            art = None
    ffmpeg = shutil.which("ffmpeg")
    if art is None and ffmpeg:
        try:
            result = subprocess.run(
                [str(ffmpeg), "-v", "error", "-i", str(audio_path),
                 "-map", "0:v:0", "-frames:v", "1", "-f", "image2pipe",
                 "-vcodec", "png", "-"],
                check=False, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout:
                art = result.stdout
        except (OSError, subprocess.TimeoutExpired):
            pass
    if art is None:
        for candidate in nearby_candidates:
            try:
                art = candidate.read_bytes()
                if art:
                    break
            except OSError:
                continue
    _ALBUM_ART_BYTES_CACHE[cache_key] = art
    return art


def _album_art_visual_fingerprint(data: bytes) -> tuple[int, int, tuple[int, int, int], tuple[int, ...]] | None:
    """Return tolerant image fingerprints so JPEG/embedded encodings deduplicate."""
    try:
        from PIL import Image, ImageStat  # type: ignore
        with Image.open(io.BytesIO(data)) as image:
            rgb = image.convert("RGB")
            tiny_rgb = rgb.resize((16, 16), Image.Resampling.LANCZOS)
            mean = tuple(round(value) for value in ImageStat.Stat(tiny_rgb).mean[:3])
            gray = rgb.convert("L")
            dh = gray.resize((9, 8), Image.Resampling.LANCZOS)
            dp = list(dh.getdata())
            dhash = 0
            for row in range(8):
                for column in range(8):
                    dhash = (dhash << 1) | int(dp[row * 9 + column] > dp[row * 9 + column + 1])
            ah = gray.resize((8, 8), Image.Resampling.LANCZOS)
            ap = list(ah.getdata())
            avg = sum(ap) / max(1, len(ap))
            ahash = 0
            for value in ap:
                ahash = (ahash << 1) | int(value >= avg)
            normalized = tuple(gray.resize((16, 16), Image.Resampling.LANCZOS).getdata())
        return dhash, ahash, mean, normalized
    except (ImportError, OSError, ValueError, TypeError):
        return None


def _album_art_fingerprints_match(
    left: tuple[int, int, tuple[int, int, int], tuple[int, ...]] | None,
    right: tuple[int, int, tuple[int, int, int], tuple[int, ...]] | None,
) -> bool:
    if left is None or right is None:
        return False
    ld, la, lrgb, lp = left
    rd, ra, rrgb, rp = right
    dh = (ld ^ rd).bit_count()
    ah = (la ^ ra).bit_count()
    color_distance = sum((lrgb[i] - rrgb[i]) ** 2 for i in range(3)) ** 0.5
    mean_abs_difference = sum(abs(a - b) for a, b in zip(lp, rp)) / max(1, len(lp))
    # Same picture re-encoded/resized usually lands comfortably inside these;
    # genuinely different cover/back/disc scans do not.
    return (dh <= 7 and ah <= 7 and color_distance <= 75) or mean_abs_difference <= 9.0


def extract_album_art_variants(
    audio_path: Path,
    limit: int = ALBUM_ART_PREVIEW_MAX_IMAGES,
) -> list[bytes]:
    """Return relevant artwork, suppressing exact and near-visual duplicates."""
    variants: list[bytes] = []
    raw_hashes: set[bytes] = set()
    fingerprints: list[tuple[int, int, tuple[int, int, int], tuple[int, ...]] | None] = []

    def consider(data: bytes | None) -> None:
        if not data or len(variants) >= limit:
            return
        raw_hash = hashlib.sha256(data).digest()
        if raw_hash in raw_hashes:
            return
        fingerprint = _album_art_visual_fingerprint(data)
        if any(_album_art_fingerprints_match(fingerprint, old) for old in fingerprints):
            return
        raw_hashes.add(raw_hash)
        fingerprints.append(fingerprint)
        variants.append(data)

    candidates = _album_art_candidates(audio_path)
    if _folder_uses_per_track_sidecar_art(audio_path):
        # In a loose collection with per-track JPGs, do not leak another song's art.
        for candidate in candidates:
            try:
                consider(candidate.read_bytes())
            except OSError:
                continue
        return variants[:limit]

    consider(extract_album_art(audio_path))
    for candidate in candidates:
        try:
            consider(candidate.read_bytes())
        except OSError:
            continue
        if len(variants) >= limit:
            break
    return variants[:limit]


def console_cursor_row() -> int | None:
    """Return the Windows console-buffer cursor row when available."""
    if os.name != "nt":
        return None
    try:
        import ctypes
        from ctypes import wintypes

        class COORD(ctypes.Structure):
            _fields_ = [("X", wintypes.SHORT), ("Y", wintypes.SHORT)]

        class SMALL_RECT(ctypes.Structure):
            _fields_ = [("Left", wintypes.SHORT), ("Top", wintypes.SHORT),
                        ("Right", wintypes.SHORT), ("Bottom", wintypes.SHORT)]

        class CSBI(ctypes.Structure):
            _fields_ = [("dwSize", COORD), ("dwCursorPosition", COORD),
                        ("wAttributes", wintypes.WORD), ("srWindow", SMALL_RECT),
                        ("dwMaximumWindowSize", COORD)]

        handle = ctypes.windll.kernel32.GetStdHandle(-11)
        info = CSBI()
        if ctypes.windll.kernel32.GetConsoleScreenBufferInfo(handle, ctypes.byref(info)):
            return int(info.dwCursorPosition.Y)
    except (AttributeError, OSError, ValueError):
        pass
    return None


def scroll_console_viewport_to_output() -> None:
    """Best-effort Windows viewport snap to the current output cursor on track changes."""
    if os.name != "nt":
        return
    try:
        import ctypes
        from ctypes import wintypes

        class COORD(ctypes.Structure):
            _fields_ = [("X", wintypes.SHORT), ("Y", wintypes.SHORT)]

        class SMALL_RECT(ctypes.Structure):
            _fields_ = [("Left", wintypes.SHORT), ("Top", wintypes.SHORT),
                        ("Right", wintypes.SHORT), ("Bottom", wintypes.SHORT)]

        class CSBI(ctypes.Structure):
            _fields_ = [("dwSize", COORD), ("dwCursorPosition", COORD),
                        ("wAttributes", wintypes.WORD), ("srWindow", SMALL_RECT),
                        ("dwMaximumWindowSize", COORD)]

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        info = CSBI()
        if not kernel32.GetConsoleScreenBufferInfo(handle, ctypes.byref(info)):
            return
        height = info.srWindow.Bottom - info.srWindow.Top + 1
        top = max(0, info.dwCursorPosition.Y - height + 1)
        rect = SMALL_RECT(0, top, max(0, info.dwSize.X - 1), top + height - 1)
        kernel32.SetConsoleWindowInfo(handle, True, ctypes.byref(rect))
    except (AttributeError, OSError, ValueError):
        return


def default_now_playing_data_target() -> Path:
    """Choose the default now-playing target without forcing a machine-specific folder.

    On Windows, ``C:\\mp3\\lists\\winamp_now_playing.txt`` (plus the matching
    JPG) is preferred only when ``C:\\mp3\\lists`` already exists.  Otherwise
    the player falls back to its portable script-side
    ``play_audio_file-now_playing.dat/.jpg`` pair.
    """
    if os.name == "nt" and NOW_PLAYING_SONG_INFO.parent.is_dir():
        return NOW_PLAYING_SONG_INFO
    return Path(__file__).resolve().with_name("play_audio_file-now_playing.dat")


def write_now_playing_art(audio_path: Path, data_target: Path) -> None:
    '''Write the current cover beside one now-playing data target as JPEG.'''
    art = extract_album_art(audio_path)
    if not art:
        return
    jpg_target = (
        NOW_PLAYING_ART
        if os.name == "nt" and data_target == NOW_PLAYING_SONG_INFO
        else data_target.with_suffix('.jpg')
    )
    try:
        from PIL import Image  # type: ignore
        jpg_target.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(io.BytesIO(art)) as image:
            image.convert('RGB').save(jpg_target, 'JPEG', quality=92, optimize=True)
    except (ImportError, OSError, ValueError):
        return


def write_now_playing_data(
    targets: list[Path], audio_path: Path, tags: dict[str, str],
    position: float, duration: float | None, paused: bool, speed: float,
) -> None:
    '''Write Winamp-compatible metadata plus this player mode and speed.'''
    artist = tags.get('Artist', '')
    title = tags.get('Song', '') or audio_path.stem
    album = tags.get('Album', '')
    year = tags.get('Year', '')
    genre = tags.get('Genre', '')
    comment = tags.get('Comment', '')
    mode = 'paused' if paused else 'playing'
    headline = ' – '.join(value for value in (artist, title, album) if value)
    lines = [
        headline, str(audio_path), f'elapsed={format_position(position)}',
        f'album={album}', f'year={year}',
        f'genre={genre}', f'length={format_position(duration)}',
        f'artist={artist}', f'title={title}', f'filename={audio_path}',
        f'url={tags.get("URL", "")}', f'comment={comment}', 'end_comment=1', 'subtitle=', 'end_subtitle=1',
        'composer=', f'mode={mode}',
        f'speed={format_speed(speed)}',
    ]
    payload = '\n'.join(lines) + '\n'
    for target in targets:
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(payload, encoding='utf-8')
        except OSError:
            continue


def composite_album_art_background(
    spectrum_png: bytes,
    album_art: bytes,
    width: int,
    height: int,
) -> bytes:
    """Place dimmed cover art behind non-black spectrum pixels."""
    try:
        from PIL import Image, ImageChops, ImageEnhance, ImageFilter, ImageOps  # type: ignore
    except ImportError:  # pragma: no cover - Chafa still works without Pillow.
        return spectrum_png
    try:
        with Image.open(io.BytesIO(album_art)) as source:
            source = source.convert("RGB")
            # A soft zoomed copy fills any side gutters; the sharp foreground
            # always contains the complete cover, so no artwork is discarded.
            background = ImageOps.fit(
                source, (width, height), method=Image.Resampling.LANCZOS
            ).filter(ImageFilter.GaussianBlur(max(1, width // 80)))
            foreground = ImageOps.contain(
                source, (width, height), method=Image.Resampling.LANCZOS
            )
            left = (width - foreground.width) // 2
            top = (height - foreground.height) // 2
            background.paste(foreground, (left, top))
            background = ImageEnhance.Brightness(background).enhance(
                max(0.0, min(1.0, ALBUM_ART_BACKGROUND_BRIGHTNESS))
            ).convert("RGBA")
        spectrum = Image.open(io.BytesIO(spectrum_png)).convert("RGBA")
        spectrum = spectrum.resize((width, height), Image.Resampling.LANCZOS)
        alpha = ImageChops.lighter(
            ImageChops.lighter(spectrum.getchannel("R"), spectrum.getchannel("G")),
            spectrum.getchannel("B"),
        )
        spectrum.putalpha(alpha.point(lambda value: round(value * max(
            0.0, min(1.0, ALBUM_ART_SPECTRUM_OPACITY)
        ))))
        return_png = io.BytesIO()
        Image.alpha_composite(background, spectrum).convert("RGB").save(
            return_png, format="PNG", optimize=False
        )
        return return_png.getvalue()
    except (OSError, ValueError, TypeError):
        return spectrum_png


def render_preplay_album_cover(audio_path: Path, columns: int) -> bytes:
    """Render up to sixteen covers as a four-column by four-row SIXEL grid."""
    chafa = shutil.which("chafa")
    variants = extract_album_art_variants(audio_path, ALBUM_ART_PREVIEW_MAX_IMAGES)
    if not chafa or not variants:
        return b""

    try:
        from clairecjs_utils.claire_terminal_geometry import query_terminal_geometry
        geometry = query_terminal_geometry()
        cell_width, cell_height = geometry.cell_width, geometry.cell_height
    except Exception:
        # Matches Claire's normal Windows Terminal font ratio when the shared
        # geometry library is unavailable to the running interpreter.
        cell_width, cell_height = 10, 20

    # One artwork tile is approximately one quarter of the usable console
    # width.  A short final row remains quarter-width tiles instead of being
    # stretched to fill the terminal.
    usable_columns = max(16, columns - 1)
    tile_columns = max(8, usable_columns // ALBUM_ART_PREVIEW_COLUMNS)
    grid_columns = min(ALBUM_ART_PREVIEW_COLUMNS, len(variants))
    grid_rows = min(
        ALBUM_ART_PREVIEW_ROWS,
        math.ceil(len(variants) / ALBUM_ART_PREVIEW_COLUMNS),
    )
    display_columns = min(usable_columns, tile_columns * grid_columns)
    tile_rows = max(4, math.ceil(tile_columns * cell_width / max(1, cell_height)))
    display_rows = tile_rows * grid_rows

    # Build square-ish pixel tiles so mixed front/back/disc/inlay artwork keeps
    # its aspect ratio.  Black letterboxing is preferable to cropping scans.
    scale = 2
    tile_width_px = max(64, tile_columns * cell_width * scale)
    tile_height_px = max(64, tile_rows * cell_height * scale)
    gap_px = 0  # Artwork tiles touch; no artificial black gutters between panels.

    try:
        from PIL import Image, ImageOps  # type: ignore
        decoded: list[Image.Image] = []
        for data in variants:
            try:
                with Image.open(io.BytesIO(data)) as image:
                    decoded.append(image.convert("RGB").copy())
            except (OSError, ValueError):
                continue
        if not decoded:
            return b""

        grid_columns = min(ALBUM_ART_PREVIEW_COLUMNS, len(decoded))
        grid_rows = min(
            ALBUM_ART_PREVIEW_ROWS,
            math.ceil(len(decoded) / ALBUM_ART_PREVIEW_COLUMNS),
        )
        display_columns = min(usable_columns, tile_columns * grid_columns)
        display_rows = tile_rows * grid_rows
        canvas_width = grid_columns * tile_width_px + max(0, grid_columns - 1) * gap_px
        canvas_height = grid_rows * tile_height_px + max(0, grid_rows - 1) * gap_px
        canvas = Image.new("RGB", (canvas_width, canvas_height), (0, 0, 0))

        priority_groups = [
            decoded[index:index + ALBUM_ART_PREVIEW_COLUMNS]
            for index in range(0, min(len(decoded), ALBUM_ART_PREVIEW_MAX_IMAGES), ALBUM_ART_PREVIEW_COLUMNS)
        ]
        grid_order = [image for group in reversed(priority_groups) for image in group]
        row_lengths = [len(group) for group in reversed(priority_groups)]
        for index, image in enumerate(grid_order):
            # Highest-priority group is intentionally the LAST visible row so
            # the default bottom-of-terminal viewport contains the best art.
            prior = 0
            row = 0
            for group_length in row_lengths:
                if index < prior + group_length:
                    column = index - prior
                    break
                prior += group_length
                row += 1
            fitted = ImageOps.contain(
                image,
                (tile_width_px, tile_height_px),
                method=Image.Resampling.LANCZOS,
            )
            x = column * (tile_width_px + gap_px) + (tile_width_px - fitted.width) // 2
            y = row * (tile_height_px + gap_px) + (tile_height_px - fitted.height) // 2
            canvas.paste(fitted, (x, y))

        # Some Windows Terminal/SIXEL combinations rasterize the final few
        # image pixels across the following text-row boundary.  Paint a tiny
        # guard INSIDE the image rather than adding a whole terminal blank row.
        guard = max(0, min(canvas.height, int(ALBUM_ART_DIVIDER_GUARD_PIXELS)))
        if guard:
            from PIL import ImageDraw  # type: ignore
            ImageDraw.Draw(canvas).rectangle(
                (0, canvas.height - guard, canvas.width, canvas.height),
                fill=(0, 0, 0),
            )

        payload = io.BytesIO()
        canvas.save(payload, format="PNG", optimize=False)
        art = payload.getvalue()
    except (ImportError, OSError, ValueError):
        art = variants[0]
        grid_columns = 1
        grid_rows = 1
        display_columns = tile_columns
        display_rows = tile_rows

    try:
        return subprocess.run(
            [chafa, "--format=sixels", "--colors=full", "--scale=max",
             f"--size={display_columns}x{display_rows}",
             f"--font-ratio={cell_width}/{cell_height}",
             "--optimize=9", "--work=9", "--color-space=din99d", "-"],
            input=art, check=False, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=8,
        ).stdout.rstrip(b"\r\n")
    except (OSError, subprocess.TimeoutExpired):
        return b""

def render_sixel_visualizer(
    audio_path: Path, start_seconds: float, columns: int,
    album_art_background: bool = True,
    rows: int = SIXEL_VISUALIZER_ROWS,
) -> bytes:
    """Return one FFmpeg spectrum frame encoded as a DEC SIXEL image.

    The renderer is intentionally best-effort: an unsupported terminal simply
    receives no visualizer while normal audio controls continue working.
    """
    ffmpeg = shutil.which("ffmpeg")
    chafa = shutil.which("chafa")
    if not ffmpeg or not chafa:
        return b""
    rows = max(1, int(rows))
    geometry_cache = getattr(render_sixel_visualizer, "_geometry_cache", {})
    geometry_key = (columns, rows)
    chafa_geometry = geometry_cache.get(geometry_key)
    if chafa_geometry is None:
        try:
            from clairecjs_utils.claire_terminal_geometry import (
                query_terminal_geometry,
            )

            geometry = query_terminal_geometry()
            # Chafa's --view-size uses 8x8 Sixel cells. Convert the requested
            # character-cell rectangle to those units using the real font size.
            view_width = max(1, math.ceil(columns * geometry.cell_width / 8))
            view_height = max(
                1, math.ceil(rows * geometry.cell_height / 8)
            )
            chafa_geometry = [
                f"--view-size={view_width}x{view_height}",
                f"--font-ratio={geometry.cell_width}/{geometry.cell_height}",
            ]
        except Exception:
            chafa_geometry = [
                f"--view-size={max(1, columns)}x{rows * 2}",
                "--font-ratio=8/16",
            ]
        geometry_cache[geometry_key] = chafa_geometry
        render_sixel_visualizer._geometry_cache = geometry_cache
    pixels_wide = max(96, columns * 8)
    pixels_high = rows * 20
    spectrum = (
        f"showspectrum=s={pixels_wide}x{pixels_high}:"
        "mode=combined:color=rainbow:slide=replace:legend=0"
    )
    try:
        frame = subprocess.run(
            [ffmpeg, "-v", "error", "-ss", f"{start_seconds:.3f}", "-i",
             str(audio_path), "-filter_complex", f"[0:a]{spectrum}[visual]",
             "-map", "[visual]", "-frames:v", "1",
             "-f", "image2pipe", "-vcodec", "png", "-"],
            check=False, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=3,
        ).stdout
        if not frame:
            return b""
        if ENABLE_ALBUM_ART_BACKGROUND and album_art_background:
            album_art = extract_album_art(audio_path)
            if album_art:
                frame = composite_album_art_background(
                    frame, album_art, pixels_wide, pixels_high
                )
        sixel = subprocess.run(
            [chafa, "--format=sixels", "--colors=full", "--scale=1", "--stretch",
             "--optimize=9", "--work=9", "--color-space=din99d",
             *chafa_geometry, "-"],
            input=frame, check=False,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=3,
        ).stdout
        # Chafa owns cursor visibility when run interactively. It is a captured
        # child here, so strip only those toggles and preserve every Sixel byte.
        return sixel.replace(b"\033[?25l", b"").replace(b"\033[?25h", b"")
    except (OSError, subprocess.TimeoutExpired):
        return b""


def play_audio_file(
    file_path: str | os.PathLike[str],
    *,
    ffplay: Path | None = None,
    duration_probe=probe_duration_seconds,
    key_action_reader=read_windows_key_action,
    process_factory=subprocess.Popen,
    monotonic=time.monotonic,
    sleeper=time.sleep,
    install_signal_handlers: bool = True,
    sixel_visualizer: bool | None = None,
    drcs_visualizer: bool | None = None,
    visualizer_fade_seconds: float = DEFAULT_VISUALIZER_FADE_SECONDS,
    looping: bool = True,
    looping_state: list[bool] | None = None,
    lyrics_display: bool = True,
    shuffle_state: list[bool] | None = None,
    visualizer_mode_state: list[int] | None = None,
    color_style_state: list[int] | None = None,
    karaoke_style_state: list[int] | None = None,
    karaoke_treatment_state: list[int] | None = None,
    karaoke_emojimax_state: list[bool] | None = None,
    progress_style_state: list[int] | None = None,
    autoplay_state: list[bool] | None = None,
    output_channels_state: list[int] | None = None,
    balance_state: list[int] | None = None,
    volume_state: list[int] | None = None,
    speed_index_state: list[int] | None = None,
    drcs_enabled_state: list[bool] | None = None,
    sixel_enabled_state: list[bool] | None = None,
    album_art_visualizer_state: list[bool] | None = None,
    karaoke_visualizer_expansion_state: list[bool] | None = None,
    now_playing_targets: list[Path] | None = None,
    album_art_display: bool = True,
    genre_emoji_enabled: bool = ENABLE_GENRE_EMOJI,
    marquee_animation_if_longer_than: int = MARQUEE_ANIMATION_IF_LONGER_THAN,
    song_throb_seconds: float = SONG_RAINBOW_THROB_SECONDS,
    artist_throb_seconds: float = ARTIST_RAINBOW_THROB_SECONDS,
    shuffle_throb_seconds: float = SHUFFLE_RAINBOW_THROB_SECONDS,
    truncate_top_visualizer_lines: int = TRUNCATE_TOP_VISUALIZER_LINES,
    background_status_state: list[str | None] | None = None,
    initial_position: float = 0.0,
    playback_position_state: list[float] | None = None,
    initial_blank_line: bool = True,
    manage_winamp: bool = True,
    guard_winamp: bool | None = None,
) -> str:
    """Play one audio file with seeking, pausing, volume, and looping."""
    global _CURSOR_SUPPRESSION_ACTIVE
    audio_path = validate_file(file_path)
    player = ffplay or ffplay_executable()
    duration = duration_probe(audio_path)
    audio_tags = probe_audio_tags(audio_path)
    # Reuse metadata the player already paid to obtain when recording playlist
    # history; this prevents a second history-only ffprobe after playback.
    cache_playlist_history_identity(audio_path, duration, audio_tags)
    previous_played_at = playlist_history_last_played(
        audio_path, duration_seconds=duration, tags=audio_tags
    )
    if previous_played_at is not None and previous_played_at > 0:
        audio_tags = dict(audio_tags)
        audio_tags["Last heard"] = format_last_heard_age(time.time() - previous_played_at)
    lyrics = load_lyrics(audio_path) if lyrics_display else []
    goto_urls = goto_urls_from_tags(audio_tags)
    previous_console_title = get_console_title()
    title_artist = audio_tags.get('Artist', '')
    title_song = audio_tags.get('Song', '') or audio_path.stem
    title_identity = ' – '.join(value for value in (title_artist, title_song) if value)
    title_identity = title_identity or audio_path.name
    last_title_refresh = -10.0
    title_marquee_started = monotonic()
    title_marquee_source = title_identity

    def refresh_console_title(
        now: float, playback_position: float | None = None, paused: bool = False
    ) -> None:
        nonlocal last_title_refresh, title_marquee_started, title_marquee_source
        if now - last_title_refresh < TITLE_MARQUEE_REFRESH_SECONDS:
            return
        state = '⏸️' if paused else '▶️'
        lyric_source = (
            lyric_title_text_at(lyrics, playback_position)
            if playback_position is not None
            else None
        )
        lyric_text = lyric_source.strip() if lyric_source else ""
        # Static lyrics retain the symmetric microphone framing.  Animated
        # lyrics use ONLY a trailing microphone: it is a low-disruption cycle
        # delimiter and avoids a microphone jumping around at the left edge.
        if lyric_text:
            lyric_width = wcswidth(lyric_text)
            if lyric_width < 0:
                lyric_width = len(lyric_text)
            lyric_is_animated = lyric_width > max(0, marquee_animation_if_longer_than)
            source = f"{lyric_text} 🎤" if lyric_is_animated else f"🎤 {lyric_text} 🎤"
        else:
            lyric_is_animated = False
            source = title_identity
        if source != title_marquee_source:
            title_marquee_source = source
            title_marquee_started = now
        source_width = wcswidth(source)
        if source_width < 0:
            source_width = len(source)
        if source_width > max(0, marquee_animation_if_longer_than):
            # Lyric marquees use plain whitespace between cycles; the old
            # decorative bullet looked like punctuation belonging to the lyric.
            ring = source + ('   ' if lyric_text else '   •   ')
            offset = int(
                max(0.0, now - title_marquee_started) * TITLE_MARQUEE_CHARS_PER_SECOND
            ) % len(ring)
            repeated = ring * (math.ceil((TITLE_MARQUEE_WIDTH + offset) / len(ring)) + 1)
            marquee = repeated[offset:offset + TITLE_MARQUEE_WIDTH].rstrip()
        else:
            marquee = source
        if lyric_source:
            # Karaoke owns the title bar completely while sung/held through a short gap.
            set_console_title(marquee)
        else:
            set_console_title(f'{state} {marquee} — play_audio_file [{os.getpid()}]')
        last_title_refresh = now
    tag_plain_rows, tag_ansi_rows = format_tag_panel(
        audio_tags, genre_emoji_enabled=genre_emoji_enabled
    )
    winamp_paused_by_preview = pause_playing_winamp() if manage_winamp else False
    guard_winamp = manage_winamp if guard_winamp is None else guard_winamp
    abort_requested = threading.Event()
    previous_handlers: dict[int, object] = {}

    def request_abort(_signum, _frame) -> None:
        abort_requested.set()

    if install_signal_handlers:
        supported_signals = [signal.SIGINT]
        if hasattr(signal, "SIGBREAK"):
            supported_signals.append(signal.SIGBREAK)
        for supported in supported_signals:
            previous_handlers[supported] = signal.getsignal(supported)
            signal.signal(supported, request_abort)

    position = max(0.0, initial_position)
    if duration is not None:
        position = min(position, max(0.0, duration - 0.05))
    if looping_state is not None:
        looping = looping_state[0]
    volume = volume_state[0] if volume_state is not None else 100
    volume_direction = "up"
    output_channels = output_channels_state[0] if output_channels_state is not None else 2
    balance = balance_state[0] if balance_state is not None else 0
    sixel_enabled = (
        bool(ENABLE_SIXEL_VISUALIZER)
        if sixel_visualizer is None else sixel_visualizer
    )
    drcs_enabled = (
        bool(ENABLE_DRCS_VISUALIZER)
        if drcs_visualizer is None else drcs_visualizer
    )
    # Ctrl+Alt+F8 is an experimental runtime mode, so begin disabled even
    # though the renderer capability itself is available. It uses a SIXEL-composited spectrum in the DRCS visualizer region.
    album_art_visualizer_enabled = (
        bool(album_art_visualizer_state[0]) if album_art_visualizer_state is not None else False
    )
    karaoke_visualizer_expansion_enabled = (
        bool(karaoke_visualizer_expansion_state[0])
        if karaoke_visualizer_expansion_state is not None else DEFAULT_KARAOKE_VISUALIZER_EXPANSION
    )
    if drcs_enabled and not shutil.which("ffmpeg"):
        raise RuntimeError(
            "The DRCS visualizer requires FFmpeg.\n"
            + tool_install_instructions("ffmpeg")
        )
    if sixel_enabled and not shutil.which("chafa"):
        raise RuntimeError(
            "The SIXEL visualizer requires Chafa.\n"
            + tool_install_instructions("chafa")
        )
    speed_index = speed_index_state[0] if speed_index_state is not None else PLAYBACK_SPEEDS.index(1.0)
    process = None
    status_rendered = False
    loop_indicator_until = 0.0
    help_overlay_until = 0.0
    favorite_menu_active = False
    favorite_restore_mode = False
    last_background_status = (
        background_status_state[0] if background_status_state else None
    )
    last_sixel_refresh = -10.0
    last_metadata_animation_write = -10.0
    last_now_playing_write = -10.0
    last_winamp_enforcement = -10.0
    screen_closed = False
    drcs_timeline: tuple[bytes, int, int] = (b"", 12, SPECTRUM_ANALYSIS_FPS)
    drcs_recent_energy: list[float] = []
    last_drcs_position: float | None = None
    visualizer_fade_seconds = max(0.0, visualizer_fade_seconds)
    HEADER_ROW = 0
    HELP_ROW = 1 + len(tag_plain_rows)
    CONTROLS_ROW = HELP_ROW
    CONTROLS_ROWS = 1
    # Keep the final grey controls line immediately followed by the compact
    # clock/progress row, then place the visualizer directly below it.
    STATUS_ROW = CONTROLS_ROW + CONTROLS_ROWS
    DRCS_ROW = STATUS_ROW + 1
    # Exactly three double-height lyric bands: previous, current, next.
    LYRIC_ROWS = 6 if lyrics else 0
    LYRIC_ROW = STATUS_ROW + 1
    DRCS_ROW = LYRIC_ROW + LYRIC_ROWS
    terminal_lines = shutil.get_terminal_size((120, 30)).lines
    fixed_rows = DRCS_ROW + (SIXEL_VISUALIZER_ROWS if sixel_enabled else 0)
    drcs_rows = (
        min(max(0, DRCS_VISUALIZER_ROWS - truncate_top_visualizer_lines), max(0, terminal_lines - fixed_rows))
        if drcs_enabled else 0
    )
    SIXEL_ROW = DRCS_ROW + drcs_rows
    # Previous and next cues use one double-height line each; the current cue
    # reserves two so a long lyric can wrap without moving the rest of the UI.
    UI_ROWS = SIXEL_ROW + (SIXEL_VISUALIZER_ROWS if sixel_enabled else 0)
    drcs_has_space = drcs_rows > 0
    sixel_has_space = sixel_enabled
    last_lyric_index: int | None = None
    lyric_transition_index: int | None = None
    karaoke_visualizer_overlay = False
    lyric_transition_started_at = 0.0
    reset_undo_state: dict[str, int] | None = None
    played_ranges: list[tuple[float, float]] = []
    track_started_at = int(time.time())

    def reflow_rows_for_terminal() -> None:
        '''Shrink/grow the visualizer reservation while protecting karaoke.'''
        nonlocal drcs_rows, DRCS_ROW, STATUS_ROW, SIXEL_ROW, LYRIC_ROW, UI_ROWS
        old_ui_rows = UI_ROWS
        lines = shutil.get_terminal_size((120, 30)).lines
        fixed = STATUS_ROW + 1 + (SIXEL_VISUALIZER_ROWS if sixel_enabled else 0) + LYRIC_ROWS
        desired = (
            min(max(0, DRCS_VISUALIZER_ROWS - truncate_top_visualizer_lines), max(0, lines - fixed))
            if drcs_enabled else 0
        )
        drcs_rows = desired
        LYRIC_ROW = DRCS_ROW if karaoke_visualizer_overlay else STATUS_ROW + 1
        DRCS_ROW = (STATUS_ROW + 1 + LYRIC_ROWS) if karaoke_visualizer_overlay else (STATUS_ROW + 1 + LYRIC_ROWS)
        SIXEL_ROW = DRCS_ROW + drcs_rows
        UI_ROWS = SIXEL_ROW + (SIXEL_VISUALIZER_ROWS if sixel_enabled else 0)
        if UI_ROWS > old_ui_rows:
            write_console(move_to(old_ui_rows) + '\n' * (UI_ROWS - old_ui_rows))
        elif UI_ROWS < old_ui_rows:
            clear_region(UI_ROWS, old_ui_rows - UI_ROWS)
            write_console(move_to(UI_ROWS) + f'\033[{old_ui_rows - UI_ROWS}M')
    visualizer_mode = (
        visualizer_mode_state[0]
        if visualizer_mode_state is not None
        else load_favorite_visualizer_mode()
    )
    visualizer_mode_digits = ""
    color_style = color_style_state[0] if color_style_state is not None else 1
    karaoke_style = karaoke_style_state[0] if karaoke_style_state is not None else 1
    karaoke_treatment = karaoke_treatment_state[0] if karaoke_treatment_state is not None else 2
    karaoke_emojimax = karaoke_emojimax_state[0] if karaoke_emojimax_state is not None else False
    progress_style = progress_style_state[0] if progress_style_state is not None else 1
    fade_style = 1
    last_visualizer_digit_at = -10.0
    last_volume_action: str | None = None
    last_volume_change_at = -10.0
    volume_repeat_count = 0

    def move_to(row: int) -> str:
        return "\033(B\033[u" + (f"\033[{row}B" if row else "") + "\r" + BIG_OFF

    def clear_region(start_row: int, row_count: int) -> None:
        write_console(
            "".join(
                move_to(start_row + row) + "\033[2K"
                for row in range(row_count)
            )
        )
    title_text = f"🔊 Playing: {audio_path.name} ({format_duration_label(duration)})"
    initial_visualizer_help = (
        f"visualizer: V ({'On' if drcs_enabled else 'Off'}); "
        f"mode {visualizer_mode}: {VISUALIZER_MODE_NAMES[visualizer_mode - 1]} "
        "[F2/F3 type; F4/F5 treatment; F favorite; *=favorites]"
        + ("; W (On)" if sixel_enabled else "")
    )
    def help_line(label: str, text: str) -> str:
        return f"   {label:>7}: {text}"

    help_texts: tuple[str, ...] = ()

    def current_tag_rows(current_position: float) -> tuple[tuple[str, ...], tuple[str, ...]]:
        available = max(12, shutil.get_terminal_size((120, 30)).columns - 1)
        return format_tag_panel(
            audio_tags,
            artist_rgb=artist_rainbow_rgb(current_position, artist_throb_seconds),
            song_rgb=song_rainbow_rgb(current_position, song_throb_seconds),
            album_art_visualizer_enabled=album_art_visualizer_enabled,
            karaoke_visualizer_expansion_enabled=karaoke_visualizer_expansion_enabled,
            genre_emoji_enabled=genre_emoji_enabled,
            width=available,
        )

    def render_metadata_rows(current_position: float) -> None:
        """Animate the Playing filename plus Artist/Song metadata colors."""
        _plain, animated_rows = current_tag_rows(current_position)
        available = max(12, shutil.get_terminal_size((120, 30)).columns - 1)
        output: list[str] = [
            move_to(HEADER_ROW)
            + truncate_ansi_to_cells(playing_header_ansi(current_position), available)
            + "\033[K"
        ]
        for index in range(len(tag_plain_rows)):
            row = animated_rows[index] if index < len(animated_rows) else ""
            output.append(
                move_to(1 + index)
                + truncate_ansi_to_cells(BIG_OFF + row, available)
                + "\033[K"
            )
        write_console("".join(output) + "\033[?25l")

    def current_background_label() -> str | None:
        return (
            background_status_state[0]
            if background_status_state and background_status_state[0]
            else None
        )

    def background_status_ansi(label: str, leading: str = " ") -> str:
        """Render active shuffling as a blinking 3×-speed rainbow throb."""
        if label.casefold().startswith("shuffling "):
            rgb = metadata_rainbow_rgb(
                monotonic(),
                0.25,
                throb_seconds=shuffle_throb_seconds,
                cycle_seconds=SHUFFLE_RAINBOW_CYCLE_SECONDS,
                pulse_phase=0.25,
            )
            return f"{leading}\033[1;5m{ansi_rgb(rgb)}[{label}]\033[0m"
        return f"{leading}\033[2;90m[{label}]\033[0m"

    def playing_header_layout() -> tuple[str, str | None, bool]:
        """Choose full path vs basename and whether the status marker fits inline."""
        available = max(12, shutil.get_terminal_size((120, 30)).columns - 1)
        duration_label = format_duration_label(duration)
        full_path_plain = f"🔊 Playing: {audio_path} ({duration_label})"
        display_path = str(audio_path) if terminal_cell_width(full_path_plain) <= available else audio_path.name
        base_plain = f"🔊 Playing: {display_path} ({duration_label})"
        label = current_background_label()
        marker_plain = f" [{label}]" if label else ""
        marker_inline = bool(label and terminal_cell_width(base_plain + marker_plain) <= available)
        return display_path, label, marker_inline

    def playing_header_ansi(current_position: float) -> str:
        """Render Playing path with an always-animated basename/song filename."""
        display_path, background_label, marker_inline = playing_header_layout()
        background_marker = (
            background_status_ansi(background_label)
            if background_label and marker_inline else ""
        )
        duration_label = format_duration_label(duration)
        display_text = str(display_path)
        basename = audio_path.name
        if display_text.endswith(basename):
            folder_prefix = display_text[:-len(basename)]
            filename_text = basename
        else:
            folder_prefix = ""
            filename_text = display_text
        path_ansi = ""
        if folder_prefix:
            path_ansi += "\033[3m" + ansi_rgb(PLAYING_PATH_RGB) + folder_prefix + "\033[0m"
        # Playing path/filename is informational and stays static; Artist/Song metadata throbs.
        path_ansi += "\033[3m" + ansi_rgb(PLAYING_PATH_RGB) + filename_text + "\033[0m"
        return (
            "\033[32m\U0001f50a\033[4GPlaying:\033[0m "
            + path_ansi
            + f" \033[2;38;2;165;175;185m({duration_label})\033[0m"
            + background_marker
        )

    def render_static_header(current_position: float = 0.0) -> None:
        """Render fixed rows without permitting implicit terminal wrapping."""
        available = max(12, shutil.get_terminal_size((120, 30)).columns - 1)
        header = playing_header_ansi(current_position)
        output = [move_to(HEADER_ROW) + truncate_ansi_to_cells(header, available)]
        _plain_rows, animated_rows = current_tag_rows(current_position)
        for index in range(len(tag_plain_rows)):
            row = animated_rows[index] if index < len(animated_rows) else ""
            output.append(move_to(1 + index) + truncate_ansi_to_cells(BIG_OFF + row, available) + "\033[K")
        for index, text in enumerate(help_texts[:3]):
            output.append(
                move_to(HELP_ROW + index)
                + truncate_ansi_to_cells(f"{BIG_OFF}\033[2;90m{text}", available)
            )
        write_console("".join(output) + "\033[?25l")

    def render_help_overlay() -> None:
        """Temporarily replace the upper UI with a compact, color-grouped key map."""
        available = max(12, shutil.get_terminal_size((120, 30)).columns - 1)

        # Each group is intentionally untitled: color is the grouping cue.
        # Keys are the brightest element, descriptions are calmer, and the
        # ⫽ delimiter is an accent shade between the two so the eye can scan
        # the map quickly without semicolon soup.
        groups = (
            (
                ((115, 255, 160), (88, 205, 145), (105, 155, 130)),
                (
                    ("X/Q/Ctrl+W/Ctrl+C/Alt+F4", "⏹ stop"),
                    ("Space/Pause", "⏯ pause/resume"),
                    ("←/→", "⏪⏩ seek 5s"),
                    ("Shift+←/→", "seek 15s"),
                    ("Ctrl+←/→", "seek 60s"),
                    ("+/-", "🐇/🐢 speed"),
                    ("2/5/7", "🔊 stereo/5.1/7.1"),
                    ("L", "🔁 loop"),
                ),
            ),
            (
                ((105, 225, 255), (80, 180, 215), (95, 145, 165)),
                (
                    ("</>", "⏮/⏭ track"),
                    ("{/}", "📁 previous/next folder"),
                    ("R", "🔀 shuffle"),
                    ("A", "▶ autoplay"),
                    ("↑/↓", "volume ±5%"),
                    ("Shift+↑/↓", "volume ±20%"),
                    ("=", "volume 100%"),
                    ("Num4/6/5", "balance L/R/center"),
                ),
            ),
            (
                ((255, 125, 235), (215, 95, 195), (160, 105, 155)),
                (
                    ("F4", "✨ Emojimaxx"),
                    ("F2/F3", "karaoke style −/+"),
                    ("Shift+F2/F3", "karaoke treatment −/+"),
                    ("Shift+K / K", "style −/+"),
                    ("Ctrl+K", "next treatment"),
                    ("Alt+K", "favorite karaoke cycle"),
                    ("Ctrl+Alt+K", "toggle karaoke favorite"),
                    ("F2+F3 hold", "style Megamix"),
                ),
            ),
            (
                ((150, 160, 255), (118, 125, 220), (112, 120, 165)),
                (
                    ("Ctrl+V", "DRCS visualizer"),
                    ("W", "SIXEL visualizer"),
                    ("F6/F7", "visualizer style −/+"),
                    ("Shift+F6/F7", "visualizer treatment −/+"),
                    ("C/Shift+C", "color +/−"),
                    ("*", "favorite visualizer"),
                    ("F", "Favorite style/treatment/color/etc"),
                ),
            ),
            (
                ((255, 205, 90), (220, 165, 70), (165, 135, 85)),
                (
                    ("P/Shift+P", "progress style +/−"),
                ),
            ),
            (
                ((255, 155, 95), (220, 125, 75), (165, 115, 90)),
                (
                    ("Ctrl+Alt+F8", "🎨 artwork spectrum"),
                    ("Ctrl+Alt+F9", "💹 blank-karaoke expansion"),
                    ("Shift+F10", "↕ karaoke/visualizer overlay"),
                    ("Ctrl+G", "🔗 open track URL(s)"),
                    ("Ctrl+Alt+L", "Last.fm scrobble now"),
                    ("F1", "defaults"),
                    ("Alt+F1", "undo defaults"),
                    ("F5/Ctrl+L/Ctrl+R", "redraw"),
                    ("?", "help; hold to keep visible"),
                    ("Esc", "close help/menu"),
                ),
            ),
        )

        def rgb_escape(rgb: tuple[int, int, int], *, bold: bool = False) -> str:
            prefix = "\033[1;" if bold else "\033["
            return prefix + f"38;2;{rgb[0]};{rgb[1]};{rgb[2]}m"

        rendered: list[str] = []
        for (key_rgb, separator_rgb, text_rgb), items in groups:
            row_ansi = ""
            row_cells = 0
            for key, description in items:
                plain = f"{key} ⫽ {description}"
                chunk_cells = terminal_cell_width(plain)
                spacer = 2 if row_cells else 0
                if row_cells and row_cells + spacer + chunk_cells > available:
                    rendered.append(row_ansi + "\033[0m")
                    row_ansi = ""
                    row_cells = 0
                    spacer = 0
                if spacer:
                    row_ansi += "  "
                    row_cells += spacer
                row_ansi += (
                    rgb_escape(key_rgb, bold=True) + key
                    + " " + rgb_escape(separator_rgb) + "⫽"
                    + " " + rgb_escape(text_rgb) + description
                )
                row_cells += chunk_cells
            if row_ansi:
                rendered.append(row_ansi + "\033[0m")

        overlay_rows = min(UI_ROWS, max(1, len(rendered)))
        clear_region(HEADER_ROW, overlay_rows)
        write_console("".join(
            move_to(HEADER_ROW + index) + BIG_OFF
            + truncate_ansi_to_cells(line, available)
            for index, line in enumerate(rendered[:overlay_rows])
        ) + "\033[?25l")

    def change_volume(action: str, now: float) -> None:
        """Apply held-key acceleration while keeping volume within 0–400%."""
        nonlocal volume, volume_direction, last_volume_action
        nonlocal last_volume_change_at, volume_repeat_count
        if action == VOLUME_RESET:
            volume = 100
            volume_direction = "up"
            last_volume_action = action
            last_volume_change_at = now
            volume_repeat_count = 0
            if volume_state is not None:
                volume_state[0] = volume
            return
        if action == last_volume_action and now - last_volume_change_at <= 0.30:
            volume_repeat_count += 1
        else:
            volume_repeat_count = 0
        last_volume_action = action
        last_volume_change_at = now
        base_step = VOLUME_STEPS[action]
        multiplier = min(8, 1 + volume_repeat_count // 4)
        volume = min(400, max(0, volume + base_step * multiplier))
        volume_direction = "up" if base_step > 0 else "down"
        if volume_state is not None:
            volume_state[0] = volume

    def show_status(current_position: float, indicator: str) -> None:
        """Paint the two-line status, preserving its fixed screen position."""
        nonlocal status_rendered, last_drcs_position, last_lyric_index
        nonlocal lyric_transition_index, lyric_transition_started_at
        if playback_position_state is not None:
            playback_position_state[0] = max(0.0, current_position)
        timestamp_text = (
            f"{indicator} {format_position(current_position)}"
            + (f" / {format_position(duration)}" if duration is not None else "")
            + volume_status_plain(volume, volume_direction)
        )
        available_width = max(12, shutil.get_terminal_size((120, 30)).columns - 1)
        clock_plain = (
            f"{indicator} {format_position(current_position)}"
            + (f" / {format_position(duration)}" if duration is not None else "")
        )
        volume_plain = volume_status_plain(volume, volume_direction)
        # Reserve the clock, optional volume text, two requested spaces, and
        # the percentage suffix; the remaining terminal width belongs to the bar.
        reserved = (
            terminal_cell_width(clock_plain) + terminal_cell_width(volume_plain)
            + 2 + len(" 100%")
        )
        bar_width = max(1, available_width - reserved)
        # The progress bar shares its row with clock/volume, but the spectrum
        # and double-height karaoke own the full console width.
        visualizer_width = available_width
        karaoke_line_capacity = max(10, available_width // 2)
        active_lyric = lyric_at(lyrics, current_position)
        expand_visualizer_into_lyrics = bool(
            karaoke_visualizer_expansion_enabled
            and LYRIC_ROWS
            and active_lyric is None
            and not karaoke_visualizer_overlay
        )
        levels = b""
        if drcs_enabled:
            levels = spectrum_frame_at(drcs_timeline, current_position)
            if len(drcs_recent_energy) != len(levels):
                drcs_recent_energy[:] = [0.0] * len(levels)
                last_drcs_position = None
            delta = (
                current_position - last_drcs_position
                if last_drcs_position is not None else 0.0
            )
            if delta < 0 or delta > 2.5:
                drcs_recent_energy[:] = [
                    level / SPECTRUM_ANALYSIS_HEIGHT for level in levels
                ]
            else:
                fade_step = (
                    (delta * 12.0) / visualizer_fade_seconds
                    if visualizer_fade_seconds > 0 else 1.0
                )
                for index, level in enumerate(levels):
                    current_energy = level / SPECTRUM_ANALYSIS_HEIGHT
                    drcs_recent_energy[index] = max(
                        current_energy,
                        drcs_recent_energy[index] - fade_step,
                    )
            last_drcs_position = current_position
            visualizer_row = LYRIC_ROW if expand_visualizer_into_lyrics else DRCS_ROW
            visualizer_rows = drcs_rows + (LYRIC_ROWS if expand_visualizer_into_lyrics else 0)
            if not album_art_visualizer_enabled:
                write_console(
                    move_to(visualizer_row)
                    + render_drcs_visualizer(
                        visualizer_width, levels, drcs_recent_energy, visualizer_mode, color_style,
                        visualizer_rows,
                        fade_style,
                        truncate_top_visualizer_lines + (LYRIC_ROWS if expand_visualizer_into_lyrics else 0),
                    )
                    + "\033[J"
                )
        write_console(
            move_to(STATUS_ROW)
            +
            render_status(
                current_position,
                duration,
                indicator,
                volume,
                volume_direction,
                looping,
                bar_width,
                repaint=False,
                progress_style=progress_style,
                pulse_energy=(
                    sum(levels) / (len(levels) * SPECTRUM_ANALYSIS_HEIGHT)
                    if levels else 0.0
                ),
            )
        )
        if active_lyric is None:
            if last_lyric_index is not None:
                # When F9 expansion is active, the spectrum has already
                # repainted these rows this frame; do not erase it immediately.
                if not expand_visualizer_into_lyrics:
                    clear_region(LYRIC_ROW, LYRIC_ROWS)
                last_lyric_index = None
                lyric_transition_index = None
        else:
            lyric_index, lyric_text, opacity = active_lyric
            painted_lyric_rows: set[int] = set()
            readable = ((255, 220, 120), (150, 235, 255), (210, 180, 255), (170, 255, 185))
            line_capacity = karaoke_line_capacity
            lyrics_are_timed = any(start > 0 or end is not None for start, end, _text in lyrics)

            def neighboring_entry(direction: int) -> tuple[int, str] | None:
                candidate = lyric_index + direction
                while 0 <= candidate < len(lyrics):
                    if lyrics[candidate][2].strip():
                        return candidate, lyrics[candidate][2]
                    candidate += direction
                return None

            def foreground_for(seed: int, brightness: float) -> str:
                brightness = min(1.0, max(0.0, brightness))
                return ansi_rgb(tuple(round(component * brightness) for component in readable[seed % len(readable)]))

            def lyric_line_payload(
                text: str, *, current: bool, seed: int, brightness: float,
                capacity: int | None = None,
            ) -> str:
                """Center a lyric; current-line background reaches halfway to each edge."""
                # Double-height DEC text consumes two physical terminal columns per
                # logical lyric cell, so its normal capacity is half the console.
                # Single-height fallback lines must instead center across the *full*
                # console width.  The optional capacity keeps those two coordinate
                # systems separate rather than accidentally centering long fallback
                # lyrics inside only the left half of the window.
                payload_capacity = line_capacity if capacity is None else max(1, capacity)
                text_width = min(payload_capacity, terminal_cell_width(text))
                remaining = max(0, payload_capacity - text_width)
                left_padding = remaining // 2
                right_padding = remaining - left_padding
                attributes = foreground_for(seed, brightness)
                colored_text = colorize_karaoke_text(
                    text, karaoke_treatment, seed, brightness
                )
                if not current:
                    return (
                        attributes
                        + " " * left_padding
                        + colored_text
                        + " " * right_padding
                    )
                # Leave the outer half of each margin untouched; highlight only
                # the text plus the inner half of the whitespace on each side.
                outer_left = left_padding // 2
                outer_right = right_padding // 2
                inner_left = left_padding - outer_left
                inner_right = right_padding - outer_right
                return (
                    " " * outer_left
                    + "\033[48;2;0;22;26m" + attributes
                    + " " * inner_left + colored_text + " " * inner_right
                    + "\033[0m"
                    + " " * outer_right
                )

            def double_height(
                row: int,
                text: str,
                *,
                current: bool,
                seed: int,
                brightness: float,
            ) -> None:
                """Render one settled lyric line with caller-controlled brightness."""
                if not 0 <= row or row + 1 >= LYRIC_ROWS:
                    return
                painted_lyric_rows.update((row, row + 1))
                fitted = truncate_to_cells(text, line_capacity, "…")
                payload = lyric_line_payload(
                    fitted, current=current, seed=seed, brightness=brightness
                )
                write_console(
                    move_to(LYRIC_ROW + row) + "\033#3" + payload + "\033[0m\033[K"
                    + move_to(LYRIC_ROW + row + 1) + "\033#4" + payload + "\033[0m\033[K"
                )

            def render_normal_line(
                row: int,
                text: str,
                seed: int,
                brightness: float,
                *,
                current: bool = False,
                emoji_threshold: float | None = None,
            ) -> None:
                if not 0 <= row < LYRIC_ROWS or brightness <= 0.001:
                    return
                painted_lyric_rows.add(row)
                styled = stylize_karaoke_with_emojimax(
                    text, karaoke_style, karaoke_emojimax, brightness,
                    fade_threshold_percent=emoji_threshold,
                )
                # This is deliberately the full terminal width.  `line_capacity`
                # is half-width because it is sized for DEC double-height lyrics;
                # using it here was why long single-height fallback lines appeared
                # visibly left-of-center.
                normal_line_capacity = available_width
                fitted = truncate_to_cells(styled, normal_line_capacity, "…")
                payload = lyric_line_payload(
                    fitted,
                    current=current,
                    seed=seed,
                    brightness=brightness,
                    capacity=normal_line_capacity,
                )
                write_console(
                    move_to(LYRIC_ROW + row) + BIG_OFF + payload + "\033[0m\033[K"
                )

            def render_neighbor(
                row: int,
                entry: tuple[int, str],
                brightness: float,
                *,
                emoji_threshold: float | None = None,
            ) -> None:
                seed, text = entry
                if brightness <= 0.001:
                    return
                styled = compensate_double_height_cells(
                    stylize_karaoke_with_emojimax(
                        text, karaoke_style, karaoke_emojimax, brightness,
                        fade_threshold_percent=emoji_threshold,
                    )
                )
                if terminal_cell_width(styled) <= line_capacity:
                    double_height(
                        row,
                        styled,
                        current=False,
                        seed=seed,
                        brightness=brightness,
                    )
                    return
                render_normal_line(row + 1, text, seed, brightness, emoji_threshold=emoji_threshold)

            def render_scrolling_line(
                row: int,
                text: str,
                seed: int,
                brightness: float,
                *,
                current: bool = False,
                emoji_threshold: float | None = None,
            ) -> None:
                if not 0 <= row or row + 1 >= LYRIC_ROWS or brightness <= 0.001:
                    return
                styled = compensate_double_height_cells(
                    stylize_karaoke_with_emojimax(
                        text,
                        karaoke_style,
                        karaoke_emojimax,
                        brightness,
                        force_emoji_when_enabled=current,
                        fade_threshold_percent=emoji_threshold,
                    )
                )
                fitted = truncate_to_cells(styled, line_capacity, "…")
                double_height(
                    row,
                    fitted,
                    current=current,
                    seed=seed,
                    brightness=brightness,
                )

            previous_entry = neighboring_entry(-1)
            next_entry = neighboring_entry(1)
            previous_brightness, next_brightness = lyric_neighbor_opacities(
                lyrics, lyric_index, current_position
            )
            prior_lyric_index = last_lyric_index
            if prior_lyric_index is not None and lyric_index == prior_lyric_index + 1:
                lyric_transition_index = lyric_index
                lyric_transition_started_at = current_position
            elif lyric_transition_index != lyric_index:
                lyric_transition_index = None

            transition_rows = None
            if lyric_transition_index == lyric_index:
                transition_rows = lyric_scroll_rows(
                    current_position - lyric_transition_started_at
                )
                if transition_rows is None:
                    lyric_transition_index = None

            if transition_rows is not None:
                previous_row, current_row, next_row = transition_rows
                if previous_entry:
                    render_scrolling_line(
                        previous_row,
                        previous_entry[1],
                        previous_entry[0],
                        previous_brightness,
                        emoji_threshold=HIDE_PREVIOUS_EMOJI_WHEN_FADE_IS_UNDER_X_PERCENT,
                    )
                render_scrolling_line(
                    current_row,
                    lyric_text,
                    lyric_index,
                    opacity,
                    current=True,
                )
                if next_entry:
                    render_scrolling_line(
                        next_row,
                        next_entry[1],
                        next_entry[0],
                        next_brightness,
                        emoji_threshold=(
                            0.0 if NEXT_SUNG_LINE_EMOJIMAXX_ON_AT_FIRST
                            else HIDE_EMOJI_WHEN_FADE_IS_UNDER_X_PERCENT
                        ),
                    )
            else:
                if previous_entry:
                    render_neighbor(
                        0, previous_entry, previous_brightness,
                        emoji_threshold=HIDE_PREVIOUS_EMOJI_WHEN_FADE_IS_UNDER_X_PERCENT,
                    )
                styled_current = compensate_double_height_cells(
                    stylize_karaoke_with_emojimax(
                        lyric_text,
                        karaoke_style,
                        karaoke_emojimax,
                        opacity,
                        force_emoji_when_enabled=True,
                    )
                )
                wrapped = wrap_to_cells(styled_current, line_capacity)
                pages = [wrapped[index:index + 2] for index in range(0, len(wrapped), 2)]
                cue_start = lyrics[lyric_index][0] if lyrics_are_timed else lyric_index * 4.0
                page = pages[min(len(pages) - 1, max(0, int((current_position - cue_start) // 4)))]
                # Fixed double-height bands: previous 0/1, current 2/3, next 4/5.
                current_start_row = 2
                for page_row, line in enumerate(page):
                    double_height(
                        current_start_row + page_row * 2,
                        line,
                        current=True,
                        seed=lyric_index,
                        brightness=opacity,
                    )
                if next_entry and len(page) == 1:
                    render_neighbor(
                        4,
                        next_entry,
                        next_brightness,
                        emoji_threshold=(
                            0.0 if NEXT_SUNG_LINE_EMOJIMAXX_ON_AT_FIRST
                            else HIDE_EMOJI_WHEN_FADE_IS_UNDER_X_PERCENT
                        ),
                    )
            # Do not erase rows immediately before repainting them: Windows
            # Terminal exposes that tiny gap as a conspicuous lyric strobe.
            # Painted rows overwrite in place; only abandoned rows are blanked.
            for unused_row in set(range(LYRIC_ROWS)) - painted_lyric_rows:
                write_console(move_to(LYRIC_ROW + unused_row) + BIG_OFF + "\033[2K")
            last_lyric_index = lyric_index
        write_console("\033[?25l")
        set_console_cursor_visible(False)
        status_rendered = True

    def render_controls(progress: float = 0.0) -> None:
        """Render compact current-state glyphs; overflow status gets this row."""
        loop_glyph = "\U0001f501" if looping else "\u21aa"
        shuffle_glyph = "\U0001f500" if shuffle_state and shuffle_state[0] else "\u2192"
        emoji_glyph = "+" if karaoke_emojimax else "-"
        sixel_glyph = "+" if sixel_enabled else "-"
        controls = (
            f"\033[2;90m  ?: "
            f"\033[38;2;175;175;185m{loop_glyph} {shuffle_glyph}\033[2;90m  "
            f"K:{KARAOKE_STYLE_NAMES[karaoke_style - 1]}/{KARAOKE_TREATMENT_NAMES[karaoke_treatment - 1]} E:{emoji_glyph} "
            f"V:{'+' if drcs_enabled else '-'} W:{sixel_glyph} "
            f"🎨{'+' if album_art_visualizer_enabled else '-'} "
            f"{'' if karaoke_visualizer_expansion_enabled else '💹- '}"
            f"↕{'+' if karaoke_visualizer_overlay else '-'} "
            f"M{visualizer_mode}:{VISUALIZER_TYPE_NAMES[(visualizer_mode - 1) % len(VISUALIZER_TYPE_NAMES)]}/"
            f"{VISUALIZER_TREATMENT_NAMES[(visualizer_mode - 1) // len(VISUALIZER_TYPE_NAMES)]} "
            f"C{color_style}:{COLOR_STYLE_NAMES[color_style - 1]} Fd:{FADE_STYLE_NAMES[fade_style - 1]} "
            f"S:{speed_color(PLAYBACK_SPEEDS[speed_index], progress)}{format_speed(PLAYBACK_SPEEDS[speed_index])}\033[2;90m "
            f"O:{output_channels} B:{balance:+d}"
        )
        available = max(12, shutil.get_terminal_size((120, 30)).columns - 1)
        _display_path, background_label, marker_inline = playing_header_layout()
        overflow_marker = (
            background_status_ansi(background_label, "  ")
            if background_label and not marker_inline else ""
        )
        marker_width = terminal_cell_width(f"  [{background_label}]") if overflow_marker else 0
        if overflow_marker and marker_width >= available:
            body = ""
            marker_rendered = truncate_ansi_to_cells(overflow_marker.lstrip(), available)
        else:
            body_budget = max(1, available - marker_width)
            body = truncate_ansi_to_cells(controls, body_budget)
            marker_rendered = overflow_marker
        write_console(
            move_to(CONTROLS_ROW)
            + body
            + marker_rendered
            + "\033[0m\033[K\033[?25l"
        )

    def open_goto_url_menu() -> None:
        """Open the URL tag first, then unique Comment URLs; audio keeps playing."""
        if not goto_urls:
            return
        selected: list[str] = []
        if len(goto_urls) == 1:
            selected = [goto_urls[0]]
        elif os.name == "nt":
            import msvcrt
            choices = goto_urls[:3]
            prompt = "which one: " + ",".join(str(i + 1) for i in range(len(choices))) + ",All"
            available = max(12, shutil.get_terminal_size((120, 30)).columns - 1)
            write_console(
                move_to(CONTROLS_ROW) + "\\033[1;38;2;120;220;255m[" + prompt + "]\\033[0m\\033[K"
            )
            while True:
                key = msvcrt.getwch()
                if key == "\\x1b":
                    break
                folded = key.casefold()
                if folded == "a":
                    selected = list(goto_urls)
                    break
                if key in {"1", "2", "3"}:
                    index = int(key) - 1
                    if index < len(choices):
                        selected = [choices[index]]
                        break
            render_controls()
        if not selected:
            return
        import webbrowser
        for index, url in enumerate(selected):
            webbrowser.open(url)
            if index + 1 < len(selected):
                sleeper(1.0)

    def render_favorite_prompt() -> None:
        available = max(12, shutil.get_terminal_size((120, 30)).columns - 1)
        if favorite_restore_mode:
            prompt = (
                "\033[1;38;2;255;210;110mRestore favorite?\033[0m "
                "\033[38;2;195;205;220mV:vis-style I:vis-treatment C:color "
                "K:karaoke-style T:karaoke-treatment E:emojimax A:all Esc:back\033[0m"
            )
        else:
            prompt = (
                "\033[1;38;2;255;210;110mFavorite which?\033[0m "
                "\033[38;2;195;205;220mV:vis-style I:vis-treatment C:color "
                "K:karaoke-style T:karaoke-treatment E:emojimax R:restore Esc:cancel\033[0m"
            )
        write_console(
            move_to(CONTROLS_ROW)
            + truncate_ansi_to_cells(prompt, available)
            + "\033[0m\033[K\033[?25l"
        )

    def apply_favorite_choice(choice: str) -> bool:
        """Handle F-menu input; True closes the menu, False keeps it open."""
        nonlocal visualizer_mode, color_style, karaoke_style, karaoke_treatment
        nonlocal karaoke_emojimax, favorite_restore_mode
        key = choice.casefold()

        visualizer_style = (visualizer_mode - 1) % len(VISUALIZER_TYPE_NAMES) + 1
        visualizer_treatment = (visualizer_mode - 1) // len(VISUALIZER_TYPE_NAMES) + 1

        def rebuild_visualizer(style: int, treatment: int) -> None:
            nonlocal visualizer_mode
            style = min(len(VISUALIZER_TYPE_NAMES), max(1, int(style)))
            treatment = min(len(VISUALIZER_TREATMENT_NAMES), max(1, int(treatment)))
            visualizer_mode = (treatment - 1) * len(VISUALIZER_TYPE_NAMES) + style

        def sync_favorite_states() -> None:
            if visualizer_mode_state is not None:
                visualizer_mode_state[0] = visualizer_mode
            if color_style_state is not None:
                color_style_state[0] = color_style
            if karaoke_style_state is not None:
                karaoke_style_state[0] = karaoke_style
            if karaoke_treatment_state is not None:
                karaoke_treatment_state[0] = karaoke_treatment
            if karaoke_emojimax_state is not None:
                karaoke_emojimax_state[0] = karaoke_emojimax

        if choice == "\x1b":
            if favorite_restore_mode:
                favorite_restore_mode = False
                render_favorite_prompt()
                return False
            return True

        if not favorite_restore_mode:
            if key == "v":
                toggle_registry_favorite("VisualizerStyleFavorites", visualizer_style)
            elif key == "i":
                toggle_registry_favorite("VisualizerTreatmentFavorites", visualizer_treatment)
            elif key == "c":
                toggle_registry_favorite("ColorFavorites", color_style)
            elif key == "k":
                toggle_registry_favorite("KaraokeStyleFavorites", karaoke_style)
            elif key == "t":
                toggle_registry_favorite("KaraokeTreatmentFavorites", karaoke_treatment)
            elif key == "e":
                # Emojimax is boolean, so its favorite is one remembered state,
                # not a cycle containing both on and off.
                save_registry_favorites("KaraokeEmojimaxFavorites", [int(karaoke_emojimax)])
            elif key == "r":
                favorite_restore_mode = True
                render_favorite_prompt()
                return False
            else:
                return False
            sync_favorite_states()
            return True

        restore_all = key == "a"
        recognized = restore_all or key in {"v", "i", "c", "k", "t", "e"}
        if not recognized:
            return False
        if restore_all or key == "v":
            visualizer_style = first_registry_favorite(
                "VisualizerStyleFavorites", visualizer_style
            )
        if restore_all or key == "i":
            visualizer_treatment = first_registry_favorite(
                "VisualizerTreatmentFavorites", visualizer_treatment
            )
        rebuild_visualizer(visualizer_style, visualizer_treatment)
        if restore_all or key == "c":
            color_style = first_registry_favorite("ColorFavorites", color_style)
        if restore_all or key == "k":
            karaoke_style = first_registry_favorite("KaraokeStyleFavorites", karaoke_style)
        if restore_all or key == "t":
            karaoke_treatment = first_registry_favorite(
                "KaraokeTreatmentFavorites", karaoke_treatment
            )
        if restore_all or key == "e":
            karaoke_emojimax = bool(first_registry_favorite(
                "KaraokeEmojimaxFavorites", int(karaoke_emojimax)
            ))
        sync_favorite_states()
        favorite_restore_mode = False
        return True

    def change_karaoke(action: str | None) -> bool:
        nonlocal karaoke_style, karaoke_treatment, karaoke_emojimax
        actions = {
            KARAOKE_PREVIOUS, KARAOKE_NEXT,
            KARAOKE_TREATMENT_PREVIOUS, KARAOKE_TREATMENT_NEXT,
            KARAOKE_STYLE_MEGAMIX, KARAOKE_TREATMENT_MEGAMIX1,
            KARAOKE_TREATMENT_MEGAMIX2, KARAOKE_EMOJI_TOGGLE,
            KARAOKE_FAVORITE_TOGGLE, KARAOKE_FAVORITE_CYCLE,
        }
        if action not in actions:
            return False
        if action == KARAOKE_PREVIOUS:
            karaoke_style = ((karaoke_style - 2) % len(KARAOKE_STYLE_NAMES)) + 1
        elif action == KARAOKE_NEXT:
            karaoke_style = (karaoke_style % len(KARAOKE_STYLE_NAMES)) + 1
        elif action == KARAOKE_TREATMENT_PREVIOUS:
            karaoke_treatment = ((karaoke_treatment - 2) % len(KARAOKE_TREATMENT_NAMES)) + 1
        elif action == KARAOKE_TREATMENT_NEXT:
            karaoke_treatment = (karaoke_treatment % len(KARAOKE_TREATMENT_NAMES)) + 1
        elif action == KARAOKE_STYLE_MEGAMIX:
            karaoke_style = KARAOKE_STYLE_NAMES.index("Megamix") + 1
        elif action == KARAOKE_TREATMENT_MEGAMIX1:
            karaoke_treatment = KARAOKE_TREATMENT_NAMES.index("Megamix1") + 1
        elif action == KARAOKE_TREATMENT_MEGAMIX2:
            karaoke_treatment = KARAOKE_TREATMENT_NAMES.index("Megamix2") + 1
        elif action == KARAOKE_EMOJI_TOGGLE:
            karaoke_emojimax = not karaoke_emojimax
        elif action == KARAOKE_FAVORITE_TOGGLE:
            favorite = (karaoke_style - 1) * len(KARAOKE_TREATMENT_NAMES) + karaoke_treatment
            toggle_registry_favorite("KaraokeFavorites", favorite)
        else:
            favorite = next_registry_favorite(
                "KaraokeFavorites",
                (karaoke_style - 1) * len(KARAOKE_TREATMENT_NAMES) + karaoke_treatment,
            )
            karaoke_style = (favorite - 1) // len(KARAOKE_TREATMENT_NAMES) + 1
            karaoke_treatment = (favorite - 1) % len(KARAOKE_TREATMENT_NAMES) + 1
        if karaoke_style_state is not None:
            karaoke_style_state[0] = karaoke_style
        if karaoke_treatment_state is not None:
            karaoke_treatment_state[0] = karaoke_treatment
        if karaoke_emojimax_state is not None:
            karaoke_emojimax_state[0] = karaoke_emojimax
        return True

    def current_mode_settings() -> dict[str, int]:
        return {
            "VisualizerMode": visualizer_mode,
            "ColorStyle": color_style,
            "KaraokeStyle": karaoke_style,
            "KaraokeTreatment": karaoke_treatment,
            "KaraokeEmojimax": int(karaoke_emojimax),
            "ProgressStyle": progress_style,
            "OutputChannels": output_channels,
            "Balance": balance,
            "Volume": volume,
            "SpeedIndex": speed_index,
            "Looping": int(looping),
            "Shuffle": int(bool(shuffle_state and shuffle_state[0])),
            "Autoplay": int(bool(autoplay_state and autoplay_state[0])),
            "DrcsEnabled": int(drcs_enabled),
            "SixelEnabled": int(sixel_enabled),
        }

    def apply_mode_settings(settings: dict[str, int]) -> None:
        nonlocal visualizer_mode, color_style, karaoke_style, karaoke_treatment
        nonlocal karaoke_emojimax, progress_style, output_channels, balance
        nonlocal volume, speed_index, looping, drcs_enabled, sixel_enabled
        visualizer_mode = settings["VisualizerMode"]
        color_style = settings["ColorStyle"]
        karaoke_style = settings["KaraokeStyle"]
        karaoke_treatment = settings["KaraokeTreatment"]
        karaoke_emojimax = bool(settings["KaraokeEmojimax"])
        progress_style = settings["ProgressStyle"]
        output_channels = settings["OutputChannels"]
        balance = settings["Balance"]
        volume = settings["Volume"]
        speed_index = settings["SpeedIndex"]
        looping = bool(settings["Looping"])
        drcs_enabled = bool(settings["DrcsEnabled"])
        sixel_enabled = bool(settings["SixelEnabled"])
        if shuffle_state is not None:
            shuffle_state[0] = bool(settings["Shuffle"])
        if autoplay_state is not None:
            autoplay_state[0] = bool(settings["Autoplay"])
        for state, value in (
            (visualizer_mode_state, visualizer_mode),
            (color_style_state, color_style),
            (karaoke_style_state, karaoke_style),
            (karaoke_treatment_state, karaoke_treatment),
            (progress_style_state, progress_style),
            (output_channels_state, output_channels),
            (balance_state, balance),
            (volume_state, volume),
            (speed_index_state, speed_index),
        ):
            if state is not None:
                state[0] = value
        if karaoke_emojimax_state is not None:
            karaoke_emojimax_state[0] = karaoke_emojimax
        if looping_state is not None:
            looping_state[0] = looping
        if drcs_enabled_state is not None:
            drcs_enabled_state[0] = drcs_enabled
        if sixel_enabled_state is not None:
            sixel_enabled_state[0] = sixel_enabled

    def reset_or_undo_modes(action: str | None) -> bool:
        nonlocal reset_undo_state
        if action == RESET_DEFAULTS:
            reset_undo_state = current_mode_settings()
            apply_mode_settings({
                **current_mode_settings(),
                **{key: value for key, value in PLAYER_SETTING_DEFAULTS.items()
                   if key in current_mode_settings()},
            })
            return True
        if action == UNDO_RESET_DEFAULTS and reset_undo_state is not None:
            restored = reset_undo_state
            reset_undo_state = current_mode_settings()
            apply_mode_settings(restored)
            return True
        return False

    def finish_playback(result: str) -> str:
        """Replace the complete playback UI with its final, compact title."""
        global _CURSOR_SUPPRESSION_ACTIVE
        nonlocal screen_closed
        screen_closed = True
        _CURSOR_SUPPRESSION_ACTIVE = False
        set_console_cursor_visible(result not in NAVIGATION_ACTIONS)
        clear_region(HEADER_ROW, UI_ROWS)
        if UI_ROWS > 1:
            # Delete the reserved UI rows so the terminal's prior contents are
            # pulled back up instead of leaving a karaoke-shaped blank crater.
            write_console(move_to(HEADER_ROW + 1) + f"\033[{UI_ROWS - 1}M")
        cursor_state = "\033[?7h" + ("\033[?25l" if result in NAVIGATION_ACTIONS else "\033[?25h")
        merged = merged_playback_ranges(played_ranges)
        # The listened-range annotation is useful when the user explicitly
        # changes tracks, because it explains how much of the abandoned song
        # was heard. A normally completed/stopped song should simply show its
        # logging state without the extra [played ...] history detail.
        played_note = (
            ", ".join(
                f"{format_position(start)}\N{EN DASH}{format_position(end)}"
                for start, end in merged
            )
            if result in NAVIGATION_ACTIONS
            else ""
        )
        final_background_label = (
            background_status_state[0]
            if background_status_state and background_status_state[0]
            else None
        )
        def _write_played_status(label: str | None) -> None:
            # A Played line is static scrollback. Never freeze a live shuffle
            # percentage there after its blinking/throbbing repaint has stopped.
            static_background = final_background_label
            if static_background and (
                static_background.casefold().startswith("shuffling ")
                or static_background.casefold() in {"reading playlist", "historical shuffling done"}
            ):
                static_background = None
            display_label = static_background or label
            available = max(12, shutil.get_terminal_size((120, 30)).columns - 1)
            base_plain = f"🔊  Played: {audio_path.name} ({format_duration_label(duration)})"
            base_ansi = (
                "\033[32m\U0001f50a  Played:\033[0m "
                + f"\033[34;3m{audio_path.name}\033[0m ({format_duration_label(duration)})"
            )
            suffix_plain = (f" [{display_label}]" if display_label else "") + (
                f" [played {played_note}]" if played_note else ""
            )
            suffix_ansi = (
                (f" \033[2;90m[{display_label}]\033[0m" if display_label else "")
                + (f" \033[2;90m[played {played_note}]\033[0m" if played_note else "")
            )
            if terminal_cell_width(base_plain + suffix_plain) <= available:
                first_line = truncate_ansi_to_cells(base_ansi + suffix_ansi, available)
                second_line = ""
            else:
                first_line = truncate_ansi_to_cells(base_ansi, available)
                second_line = truncate_ansi_to_cells(
                    "\033[2;90m    " + suffix_plain.strip() + "\033[0m", available
                ) if suffix_plain.strip() else ""
            write_console(
                move_to(HEADER_ROW) + cursor_state + BIG_OFF + "\033[2K"
                + first_line + "\033[0m"
                + (("\n\033[2K" + second_line + "\033[0m") if second_line else "")
                + "\n"
            )
        callback_seen = [False]
        def _logging_status(label: str) -> None:
            callback_seen[0] = True
            _write_played_status(label)
        _write_played_status("logging")
        submitted = scrobble_track_async(audio_tags, duration, merged, track_started_at, _logging_status)
        if not submitted and not callback_seen[0]:
            _write_played_status("not logged")
        return result

    try:
        _CURSOR_SUPPRESSION_ACTIVE = True
        set_console_cursor_visible(False)
        # Reserve exactly UI_ROWS physical rows.  Emitting UI_ROWS newlines
        # creates UI_ROWS+1 cursor rows (the starting row plus every newline),
        # which was the persistent blank line below the visualizer.
        reserve_newlines = max(0, UI_ROWS - 1)
        write_console(
            ("\n" if initial_blank_line else "")
            + "\n" * reserve_newlines
            + (f"\033[{reserve_newlines}A" if reserve_newlines else "")
            + "\r\033[s\033[?7l\033[?25l"
        )
        clear_region(0, UI_ROWS)
        write_console(define_all_player_drcs() + "\033[?25l")
        render_static_header(position)
        render_controls(0.0)
        visualizer_columns = max(12, shutil.get_terminal_size((120, 30)).columns - 1)
        spectrum_ready = threading.Event()

        def analyze_spectrum() -> None:
            nonlocal drcs_timeline
            global                 WRITE_NOWPLAYING_THIS_OFTEN 
            # Publish consecutive short chunks so playback never waits for a
            # whole-file pass and the available timeline continuously grows.
            chunk_seconds = 5.0
            offset = 0.0
            accumulated = bytearray()
            while duration is None or offset < duration:
                chunk = build_audio_spectrum_timeline(
                    audio_path,
                    visualizer_columns,
                    duration_limit=chunk_seconds,
                    start_seconds=offset,
                )
                if not chunk[0]:
                    break
                accumulated.extend(chunk[0])
                drcs_timeline = (
                    bytes(accumulated), chunk[1], chunk[2]
                )
                spectrum_ready.set()
                offset += chunk_seconds
                expected = chunk[1] * chunk[2] * chunk_seconds
                if len(chunk[0]) < expected * 0.5:
                    break

        spectrum_thread: threading.Thread | None = None
        if drcs_enabled:
            spectrum_thread = threading.Thread(
                target=analyze_spectrum,
                name="audio-spectrum-analysis",
                daemon=True,
            )
            spectrum_thread.start()
        sixel_frame = (
            render_sixel_visualizer(
                audio_path, position, visualizer_columns, album_art_visualizer_enabled
            )
            if sixel_enabled else b""
        )
        if sixel_frame:
            write_console(move_to(SIXEL_ROW))
            write_console_bytes(sixel_frame)
            write_console("\033[?25l")
        indicator = "▶️"
        output_rate = 192000
        lastfm_submission_attempted = False
        last_status_write = 0.0
        last_terminal_signature = terminal_display_signature()
        last_geometry_check = monotonic()
        while True:
            speed = PLAYBACK_SPEEDS[speed_index]
            command = ffplay_command(
                player, audio_path, position, volume, speed, output_channels, balance, output_rate
            )
            process = process_factory(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            segment_started = monotonic()
            segment_was_recorded = False

            def record_segment(end_position: float) -> None:
                nonlocal segment_was_recorded
                if segment_was_recorded:
                    return
                segment_was_recorded = True
                bounded_end = min(duration, end_position) if duration is not None else end_position
                if bounded_end - position > 3.0:
                    played_ranges.append((position, bounded_end))

            while process.poll() is None:
                elapsed = max(0.0, monotonic() - segment_started) * speed
                displayed_position = position + elapsed
                if duration is not None:
                    displayed_position = min(duration, displayed_position)
                now = monotonic()
                refresh_console_title(now, displayed_position)
                current_background_status = (
                    background_status_state[0] if background_status_state else None
                )
                if current_background_status != last_background_status:
                    last_background_status = current_background_status
                    # Repaint BOTH possible marker homes.  A long [shuffling …]
                    # label may have overflowed onto the controls row; repainting
                    # only the Playing row leaves the old percentage visibly stuck.
                    if not help_overlay_until:
                        render_static_header(displayed_position)
                        if not favorite_menu_active:
                            render_controls(
                                min(1.0, displayed_position / duration) if duration else 0.0
                            )
                if favorite_menu_active:
                    menu_choice = read_windows_menu_choice()
                    if menu_choice is not None and menu_choice.casefold() != "f":
                        if apply_favorite_choice(menu_choice):
                            favorite_menu_active = False
                            favorite_restore_mode = False
                            render_controls(min(1.0, displayed_position / duration) if duration else 0.0)
                            render_metadata_rows(displayed_position)
                    action = None
                else:
                    action = key_action_reader()
                active_ranges = played_ranges + ([(position, displayed_position)] if displayed_position - position > 3.0 else [])
                if not lastfm_submission_attempted and scrobble_track_async(
                    audio_tags, duration, active_ranges, track_started_at
                ):
                    lastfm_submission_attempted = True
                if abort_requested.is_set():
                    record_segment(displayed_position)
                    stop_process(process)
                    return finish_playback("stopped")
                if now_playing_targets and now - last_now_playing_write >= WRITE_NOWPLAYING_THIS_OFTEN:
                    write_now_playing_data(
                        now_playing_targets, audio_path, audio_tags,
                        displayed_position, duration, False, speed,
                    )
                    last_now_playing_write = now
                terminal_size = shutil.get_terminal_size((120, 30))
                if now - last_geometry_check >= 0.5:
                    terminal_signature = terminal_display_signature()
                    last_geometry_check = now
                    if terminal_signature != last_terminal_signature:
                        last_terminal_signature = terminal_signature
                        visualizer_columns = max(12, terminal_size.columns - 1)
                        reflow_rows_for_terminal()
                        clear_region(HEADER_ROW, UI_ROWS)
                        if help_overlay_until:
                            render_help_overlay()
                        else:
                            render_static_header(displayed_position)
                            if favorite_menu_active:
                                render_favorite_prompt()
                            else:
                                render_controls(
                                    min(1.0, displayed_position / duration) if duration else 0.0
                                )
                        last_drcs_position = None
                        last_lyric_index = None
                        last_sixel_refresh = -10.0
                if guard_winamp and now - last_winamp_enforcement >= 0.5:
                    if pause_playing_winamp() and manage_winamp:
                        winamp_paused_by_preview = True
                    last_winamp_enforcement = now
                if loop_indicator_until and now >= loop_indicator_until:
                    indicator = "▶️"
                    loop_indicator_until = 0.0
                if help_overlay_until and _windows_question_mark_down():
                    help_overlay_until = max(help_overlay_until, now + 8.0)
                if help_overlay_until:
                    if action == DISMISS_OVERLAY:
                        help_overlay_until = 0.0
                        clear_region(HEADER_ROW, min(UI_ROWS, 12))
                        render_static_header(displayed_position)
                        if favorite_menu_active:
                            render_favorite_prompt()
                        else:
                            render_controls(min(1.0, displayed_position / duration) if duration else 0.0)
                        show_status(displayed_position, indicator)
                        continue
                    if action == HELP_OVERLAY:
                        help_overlay_until = max(help_overlay_until, now + 8.0)
                        render_help_overlay()
                        continue
                    if now >= help_overlay_until:
                        help_overlay_until = 0.0
                        clear_region(HEADER_ROW, min(UI_ROWS, 12))
                        render_static_header(displayed_position)
                        if favorite_menu_active:
                            render_favorite_prompt()
                        else:
                            render_controls(min(1.0, displayed_position / duration) if duration else 0.0)
                    elif action is None:
                        # Help is modal: do not let metadata/status/visualizer repaints erase it.
                        continue
                    else:
                        help_overlay_until = 0.0
                        clear_region(HEADER_ROW, min(UI_ROWS, 12))
                        render_static_header(displayed_position)
                        if favorite_menu_active:
                            render_favorite_prompt()
                        else:
                            render_controls(min(1.0, displayed_position / duration) if duration else 0.0)
                if action is None and now - last_status_write >= 0.04:
                    show_status(displayed_position, indicator)
                    last_status_write = now
                if action is None and now - last_metadata_animation_write >= 0.12 and not favorite_menu_active:
                    active_background = current_background_label()
                    if active_background and active_background.casefold().startswith("shuffling "):
                        render_static_header(displayed_position)
                        render_controls(
                            min(1.0, displayed_position / duration) if duration else 0.0
                        )
                    else:
                        render_metadata_rows(displayed_position)
                    last_metadata_animation_write = now
                if action is None and album_art_visualizer_enabled and now - last_sixel_refresh >= 0.5:
                    active_now = lyric_at(lyrics, displayed_position)
                    expand_now = bool(
                        karaoke_visualizer_expansion_enabled and LYRIC_ROWS
                        and active_now is None and not karaoke_visualizer_overlay
                    )
                    art_row = LYRIC_ROW if expand_now else DRCS_ROW
                    art_rows = max(1, drcs_rows + (LYRIC_ROWS if expand_now else 0))
                    frame = render_sixel_visualizer(
                        audio_path, displayed_position, visualizer_columns, True, rows=art_rows
                    )
                    if frame:
                        write_console(move_to(art_row))
                        write_console_bytes(frame)
                        write_console("\033[?25l")
                    last_sixel_refresh = now
                if action is None and sixel_enabled and not album_art_visualizer_enabled and now - last_sixel_refresh >= 0.5:
                    frame = render_sixel_visualizer(
                        audio_path, displayed_position, visualizer_columns,
                        album_art_visualizer_enabled,
                    )
                    if frame:
                        write_console(move_to(SIXEL_ROW))
                        write_console_bytes(frame)
                        write_console("\033[?25l")
                    last_sixel_refresh = now
                if action == DISMISS_OVERLAY:
                    # Escape is non-destructive during normal playback; it only closes modals/help.
                    continue
                if action == HELP_OVERLAY:
                    help_overlay_until = now + 8.0
                    render_help_overlay()
                    continue
                if action == FAVORITE_MENU:
                    favorite_menu_active = True
                    favorite_restore_mode = False
                    render_favorite_prompt()
                    continue
                if action == GOTO_URL:
                    open_goto_url_menu()
                    show_status(displayed_position, indicator)
                    continue
                if action == LASTFM_SCROBBLE_NOW:
                    if scrobble_track_async(
                        audio_tags, duration,
                        played_ranges + ([(position, displayed_position)] if displayed_position > position else []),
                        track_started_at, force=True,
                    ):
                        lastfm_submission_attempted = True
                    continue
                if action == REDRAW_UI:
                    help_overlay_until = 0.0
                    clear_region(HEADER_ROW, UI_ROWS)
                    render_static_header(displayed_position)
                    render_controls(min(1.0, displayed_position / duration) if duration else 0.0)
                    last_drcs_position = None
                    last_lyric_index = None
                    last_sixel_refresh = -10.0
                    show_status(displayed_position, indicator)
                    continue
                if reset_or_undo_modes(action):
                    record_segment(displayed_position)
                    position += elapsed
                    if duration is not None:
                        position = min(position, max(0.0, duration - 0.05))
                    stop_process(process)
                    clear_region(HEADER_ROW, UI_ROWS)
                    render_static_header()
                    render_controls(min(1.0, position / duration) if duration else 0.0)
                    show_status(position, indicator)
                    break
                if action == STOP:
                    record_segment(displayed_position)
                    stop_process(process)
                    return finish_playback("stopped")
                if action in NAVIGATION_ACTIONS:
                    record_segment(displayed_position)
                    stop_process(process)
                    return finish_playback(action)
                if action == LOOP_TOGGLE:
                    looping = not looping
                    if looping_state is not None:
                        looping_state[0] = looping
                    indicator = "🔁" if looping else "➡️"
                    loop_indicator_until = now + 5.0
                    render_controls(min(1.0, displayed_position / duration) if duration else 0.0)
                    show_status(displayed_position, indicator)
                    continue
                if action == RANDOM_TOGGLE and shuffle_state is not None:
                    shuffle_state[0] = not shuffle_state[0]
                    render_controls(
                        min(1.0, displayed_position / duration)
                        if duration else 0.0
                    )
                    continue
                if action in {
                    VISUALIZER_MODE_FIRST,
                    VISUALIZER_MODE_PREVIOUS,
                    VISUALIZER_MODE_NEXT,
                    VISUALIZER_MODE_FAVORITE,
                    VISUALIZER_FAVORITE_CYCLE,
                    VISUALIZER_TREATMENT_PREVIOUS,
                    VISUALIZER_TREATMENT_NEXT,
                } or (isinstance(action, str) and action.startswith("visualizer-mode-digit:")):
                    visualizer_type = (visualizer_mode - 1) % len(VISUALIZER_TYPE_NAMES)
                    treatment = (visualizer_mode - 1) // len(VISUALIZER_TYPE_NAMES)
                    if action == VISUALIZER_MODE_FIRST:
                        visualizer_mode = 1
                        visualizer_mode_digits = ""
                    elif action == VISUALIZER_MODE_PREVIOUS:
                        visualizer_type = (visualizer_type - 1) % len(VISUALIZER_TYPE_NAMES)
                        visualizer_mode = treatment * len(VISUALIZER_TYPE_NAMES) + visualizer_type + 1
                        visualizer_mode_digits = ""
                    elif action == VISUALIZER_MODE_NEXT:
                        visualizer_type = (visualizer_type + 1) % len(VISUALIZER_TYPE_NAMES)
                        visualizer_mode = treatment * len(VISUALIZER_TYPE_NAMES) + visualizer_type + 1
                        visualizer_mode_digits = ""
                    elif action == VISUALIZER_TREATMENT_PREVIOUS:
                        treatment = (treatment - 1) % len(VISUALIZER_TREATMENT_NAMES)
                        visualizer_mode = treatment * len(VISUALIZER_TYPE_NAMES) + visualizer_type + 1
                    elif action == VISUALIZER_TREATMENT_NEXT:
                        treatment = (treatment + 1) % len(VISUALIZER_TREATMENT_NAMES)
                        visualizer_mode = treatment * len(VISUALIZER_TYPE_NAMES) + visualizer_type + 1
                    elif action == VISUALIZER_MODE_FAVORITE:
                        added = toggle_registry_favorite("VisualizerFavorites", visualizer_mode)
                        save_favorite_visualizer_mode(visualizer_mode if added else 1)
                    elif action == VISUALIZER_FAVORITE_CYCLE:
                        visualizer_mode = next_registry_favorite("VisualizerFavorites", visualizer_mode)
                    else:
                        if now - last_visualizer_digit_at > 1.0:
                            visualizer_mode_digits = ""
                        visualizer_mode_digits += action.rpartition(":")[2]
                        candidate_mode = int(visualizer_mode_digits)
                        if 1 <= candidate_mode <= len(VISUALIZER_MODE_NAMES):
                            visualizer_mode = candidate_mode
                        else:
                            visualizer_mode_digits = action.rpartition(":")[2]
                        last_visualizer_digit_at = now
                    if visualizer_mode_state is not None:
                        visualizer_mode_state[0] = visualizer_mode
                    render_controls(
                        min(1.0, displayed_position / duration)
                        if duration else 0.0
                    )
                    show_status(displayed_position, indicator)
                    continue
                if action in {FADE_PREVIOUS, FADE_NEXT}:
                    fade_style = ((fade_style - 2) % len(FADE_STYLE_NAMES)) + 1 if action == FADE_PREVIOUS else (fade_style % len(FADE_STYLE_NAMES)) + 1
                    render_controls(min(1.0, displayed_position / duration) if duration else 0.0)
                    show_status(displayed_position, indicator)
                    continue
                if action in {COLOR_PREVIOUS, COLOR_NEXT, COLOR_FAVORITE_TOGGLE, COLOR_FAVORITE_CYCLE}:
                    if action == COLOR_PREVIOUS:
                        color_style = ((color_style - 2) % len(COLOR_STYLE_NAMES)) + 1
                    elif action == COLOR_NEXT:
                        color_style = (color_style % len(COLOR_STYLE_NAMES)) + 1
                    elif action == COLOR_FAVORITE_TOGGLE:
                        toggle_registry_favorite("ColorFavorites", color_style)
                    else:
                        color_style = next_registry_favorite("ColorFavorites", color_style)
                    if color_style_state is not None:
                        color_style_state[0] = color_style
                    render_controls()
                    show_status(displayed_position, indicator)
                    continue
                if change_karaoke(action):
                    last_lyric_index = None
                    render_controls()
                    show_status(displayed_position, indicator)
                    continue
                if action in {PROGRESS_STYLE_PREVIOUS, PROGRESS_STYLE_NEXT}:
                    progress_style = (
                        ((progress_style - 2) % len(PROGRESS_STYLE_NAMES)) + 1
                        if action == PROGRESS_STYLE_PREVIOUS
                        else (progress_style % len(PROGRESS_STYLE_NAMES)) + 1
                    )
                    if progress_style_state is not None:
                        progress_style_state[0] = progress_style
                    render_controls()
                    show_status(displayed_position, indicator)
                    continue
                if action == AUTOPLAY_TOGGLE and autoplay_state is not None:
                    autoplay_state[0] = not autoplay_state[0]
                    if autoplay_state[0]:
                        looping = False
                        if shuffle_state is not None:
                            shuffle_state[0] = True
                    render_controls()
                    continue
                if action == ALBUM_ART_VISUALIZER_TOGGLE:
                    album_art_visualizer_enabled = not album_art_visualizer_enabled
                    if album_art_visualizer_state is not None:
                        album_art_visualizer_state[0] = album_art_visualizer_enabled
                    clear_region(LYRIC_ROW, LYRIC_ROWS + drcs_rows)
                    last_sixel_refresh = -10.0
                    render_static_header(displayed_position)
                    render_controls()
                    show_status(displayed_position, indicator)
                    continue
                if action == KARAOKE_VISUALIZER_EXPAND_TOGGLE:
                    karaoke_visualizer_expansion_enabled = not karaoke_visualizer_expansion_enabled
                    if karaoke_visualizer_expansion_state is not None:
                        karaoke_visualizer_expansion_state[0] = karaoke_visualizer_expansion_enabled
                    clear_region(LYRIC_ROW, LYRIC_ROWS)
                    last_lyric_index = None
                    render_static_header(displayed_position)
                    render_controls()
                    show_status(displayed_position, indicator)
                    continue
                if action == KARAOKE_VISUALIZER_OVERLAY_TOGGLE:
                    old_lyric_row = LYRIC_ROW
                    karaoke_visualizer_overlay = not karaoke_visualizer_overlay
                    LYRIC_ROW = DRCS_ROW if karaoke_visualizer_overlay else STATUS_ROW + 1
                    clear_region(old_lyric_row, LYRIC_ROWS)
                    clear_region(LYRIC_ROW, LYRIC_ROWS)
                    last_lyric_index = None
                    show_status(displayed_position, indicator)
                    continue
                if action == SIXEL_VISUALIZER_TOGGLE:
                    sixel_enabled = not sixel_enabled
                    if sixel_enabled_state is not None:
                        sixel_enabled_state[0] = sixel_enabled
                    if not sixel_enabled:
                        clear_region(SIXEL_ROW, SIXEL_VISUALIZER_ROWS)
                        if sixel_has_space:
                            write_console(move_to(SIXEL_ROW) + f"\033[{SIXEL_VISUALIZER_ROWS}M")
                            if LYRIC_ROW > SIXEL_ROW:
                                LYRIC_ROW -= SIXEL_VISUALIZER_ROWS
                            UI_ROWS -= SIXEL_VISUALIZER_ROWS
                            sixel_has_space = False
                    elif not sixel_has_space:
                        # Karaoke remains above the visualizer when SIXEL is
                        # enabled dynamically; append only the new image rows.
                        SIXEL_ROW = UI_ROWS
                        added_rows = SIXEL_VISUALIZER_ROWS
                        write_console(move_to(UI_ROWS) + "\n" * added_rows)
                        UI_ROWS += added_rows
                        sixel_has_space = True
                        last_lyric_index = None
                    render_controls()
                    show_status(displayed_position, indicator)
                    continue
                if action == DRCS_VISUALIZER_TOGGLE:
                    drcs_enabled = not drcs_enabled
                    if drcs_enabled_state is not None:
                        drcs_enabled_state[0] = drcs_enabled
                    if not drcs_enabled:
                        clear_region(DRCS_ROW, drcs_rows)
                        if drcs_has_space:
                            write_console(move_to(DRCS_ROW) + f"\033[{drcs_rows}M")
                            if SIXEL_ROW > DRCS_ROW:
                                SIXEL_ROW -= drcs_rows
                            if LYRIC_ROW > DRCS_ROW:
                                LYRIC_ROW -= drcs_rows
                            UI_ROWS -= drcs_rows
                            drcs_has_space = False
                    else:
                        if not drcs_has_space:
                            if LYRIC_ROWS:
                                clear_region(LYRIC_ROW, LYRIC_ROWS)
                                write_console(move_to(LYRIC_ROW) + f"\033[{LYRIC_ROWS}M")
                                UI_ROWS -= LYRIC_ROWS
                            DRCS_ROW = UI_ROWS
                            terminal_lines = shutil.get_terminal_size((120, 30)).lines
                            drcs_rows = min(
                                max(1, DRCS_VISUALIZER_ROWS - truncate_top_visualizer_lines),
                                max(1, terminal_lines - (DRCS_ROW + (SIXEL_VISUALIZER_ROWS if sixel_enabled else 0) + LYRIC_ROWS)),
                            )
                            LYRIC_ROW = DRCS_ROW + drcs_rows
                            added_rows = drcs_rows + LYRIC_ROWS
                            write_console(move_to(UI_ROWS) + "\n" * added_rows)
                            UI_ROWS += added_rows
                            drcs_has_space = True
                            last_lyric_index = None
                        if spectrum_thread is None or not spectrum_thread.is_alive() and not drcs_timeline[0]:
                            spectrum_thread = threading.Thread(
                                target=analyze_spectrum,
                                name="audio-spectrum-analysis",
                                daemon=True,
                            )
                            spectrum_thread.start()
                        drcs_recent_energy.clear()
                        last_drcs_position = None
                    render_controls()
                    show_status(displayed_position, indicator)
                    continue
                if action in {SPEED_UP, SPEED_DOWN}:
                    delta = 1 if action == SPEED_UP else -1
                    new_index = min(len(PLAYBACK_SPEEDS) - 1, max(0, speed_index + delta))
                    if new_index != speed_index:
                        record_segment(displayed_position)
                        speed_index = new_index
                        if speed_index_state is not None:
                            speed_index_state[0] = speed_index
                        indicator = "⏩" if delta > 0 else "⏪"
                        loop_indicator_until = now + 4.0
                        render_controls(min(1.0, (position + elapsed) / duration) if duration else 0.0)
                        position += elapsed
                        if duration is not None:
                            position = min(position, max(0.0, duration - 0.05))
                        stop_process(process)
                        break
                if action in {OUTPUT_STEREO, OUTPUT_51, OUTPUT_71}:
                    new_output_channels = {
                        OUTPUT_STEREO: 2, OUTPUT_51: 5, OUTPUT_71: 7,
                    }[action]
                    if new_output_channels != output_channels:
                        record_segment(displayed_position)
                        output_channels = new_output_channels
                        if output_channels_state is not None:
                            output_channels_state[0] = output_channels
                        position += elapsed
                        if duration is not None:
                            position = min(position, max(0.0, duration - 0.05))
                        stop_process(process)
                        render_controls(min(1.0, position / duration) if duration else 0.0)
                        break
                if action in {BALANCE_LEFT, BALANCE_RIGHT, BALANCE_CENTER}:
                    record_segment(displayed_position)
                    balance = (
                        0 if action == BALANCE_CENTER
                        else max(-100, balance - 10) if action == BALANCE_LEFT
                        else min(100, balance + 10)
                    )
                    if balance_state is not None:
                        balance_state[0] = balance
                    position += elapsed
                    if duration is not None:
                        position = min(position, max(0.0, duration - 0.05))
                    stop_process(process)
                    render_controls(min(1.0, position / duration) if duration else 0.0)
                    show_status(position, "↔")
                    break
                if action in VOLUME_STEPS or action == VOLUME_RESET:
                    record_segment(displayed_position)
                    change_volume(action, now)
                    indicator = "🔊" if volume_direction == "up" else "🔉"
                    loop_indicator_until = now + 4.0
                    position += elapsed
                    if duration is not None:
                        position = min(position, max(0.0, duration - 0.05))
                    stop_process(process)
                    show_status(position, indicator)
                    break
                if action == PAUSE_TOGGLE:
                    record_segment(displayed_position)
                    position += elapsed
                    if duration is not None:
                        position = min(position, max(0.0, duration - 0.05))
                    stop_process(process)
                    show_status(position, "⏸️")
                    while True:
                        paused_now = monotonic()
                        refresh_console_title(paused_now, position, paused=True)
                        if now_playing_targets and paused_now - last_now_playing_write >= 1.0:
                            write_now_playing_data(
                                now_playing_targets, audio_path, audio_tags,
                                position, duration, True, speed,
                            )
                            last_now_playing_write = paused_now
                        terminal_size = shutil.get_terminal_size((120, 30))
                        terminal_signature = terminal_display_signature()
                        if terminal_signature != last_terminal_signature:
                            last_terminal_signature = terminal_signature
                            visualizer_columns = max(12, terminal_size.columns - 1)
                            reflow_rows_for_terminal()
                            clear_region(HEADER_ROW, UI_ROWS)
                            if help_overlay_until:
                                render_help_overlay()
                            else:
                                render_static_header(position)
                                if favorite_menu_active:
                                    render_favorite_prompt()
                                else:
                                    render_controls(min(1.0, position / duration) if duration else 0.0)
                                show_status(position, "⏸️")
                            last_drcs_position = None
                            last_lyric_index = None
                        if PREVENT_WINAMP_PAUSE_WHEN_WE_ARE_PAUSED:
                            if guard_winamp and paused_now - last_winamp_enforcement >= 0.5:
                                if pause_playing_winamp() and manage_winamp:
                                    winamp_paused_by_preview = True
                                last_winamp_enforcement = paused_now
                        if favorite_menu_active:
                            menu_choice = read_windows_menu_choice()
                            if menu_choice is not None and menu_choice.casefold() != "f":
                                if apply_favorite_choice(menu_choice):
                                    favorite_menu_active = False
                                    favorite_restore_mode = False
                                    render_controls(min(1.0, position / duration) if duration else 0.0)
                                    render_metadata_rows(position)
                            paused_action = None
                        else:
                            paused_action = key_action_reader()
                        if help_overlay_until and _windows_question_mark_down():
                            help_overlay_until = max(help_overlay_until, paused_now + 8.0)
                        if help_overlay_until:
                            if paused_action == DISMISS_OVERLAY:
                                help_overlay_until = 0.0
                                clear_region(HEADER_ROW, min(UI_ROWS, 12))
                                render_static_header(position)
                                if favorite_menu_active:
                                    render_favorite_prompt()
                                else:
                                    render_controls(min(1.0, position / duration) if duration else 0.0)
                                show_status(position, "⏸️")
                                continue
                            if paused_action == HELP_OVERLAY:
                                help_overlay_until = max(help_overlay_until, paused_now + 8.0)
                                render_help_overlay()
                                continue
                            if paused_now >= help_overlay_until:
                                help_overlay_until = 0.0
                                clear_region(HEADER_ROW, min(UI_ROWS, 12))
                                render_static_header(position)
                                if favorite_menu_active:
                                    render_favorite_prompt()
                                else:
                                    render_controls(min(1.0, position / duration) if duration else 0.0)
                                show_status(position, "⏸️")
                            elif paused_action is None:
                                continue
                            else:
                                help_overlay_until = 0.0
                                clear_region(HEADER_ROW, min(UI_ROWS, 12))
                                render_static_header(position)
                                if favorite_menu_active:
                                    render_favorite_prompt()
                                else:
                                    render_controls(min(1.0, position / duration) if duration else 0.0)
                                show_status(position, "⏸️")
                        if paused_action == DISMISS_OVERLAY:
                            continue
                        if paused_action == HELP_OVERLAY:
                            help_overlay_until = paused_now + 8.0
                            render_help_overlay()
                            continue
                        if paused_action == FAVORITE_MENU:
                            favorite_menu_active = True
                            favorite_restore_mode = False
                            render_favorite_prompt()
                            continue
                        if paused_action == GOTO_URL:
                            open_goto_url_menu()
                            show_status(position, "⏸️")
                            continue
                        if paused_action == ALBUM_ART_VISUALIZER_TOGGLE:
                            album_art_visualizer_enabled = not album_art_visualizer_enabled
                            if album_art_visualizer_state is not None:
                                album_art_visualizer_state[0] = album_art_visualizer_enabled
                            clear_region(LYRIC_ROW, LYRIC_ROWS + drcs_rows)
                            last_sixel_refresh = -10.0
                            render_static_header(position)
                            render_controls(min(1.0, position / duration) if duration else 0.0)
                            show_status(position, "⏸️")
                            if album_art_visualizer_enabled:
                                active_now = lyric_at(lyrics, position)
                                expand_now = bool(
                                    karaoke_visualizer_expansion_enabled and LYRIC_ROWS
                                    and active_now is None and not karaoke_visualizer_overlay
                                )
                                art_row = LYRIC_ROW if expand_now else DRCS_ROW
                                art_rows = max(1, drcs_rows + (LYRIC_ROWS if expand_now else 0))
                                frame = render_sixel_visualizer(
                                    audio_path, position, visualizer_columns, True, rows=art_rows
                                )
                                if frame:
                                    write_console(move_to(art_row))
                                    write_console_bytes(frame)
                                    write_console("\033[?25l")
                            continue
                        if paused_action == KARAOKE_VISUALIZER_EXPAND_TOGGLE:
                            karaoke_visualizer_expansion_enabled = not karaoke_visualizer_expansion_enabled
                            if karaoke_visualizer_expansion_state is not None:
                                karaoke_visualizer_expansion_state[0] = karaoke_visualizer_expansion_enabled
                            clear_region(LYRIC_ROW, LYRIC_ROWS)
                            last_lyric_index = None
                            last_sixel_refresh = -10.0
                            render_static_header(position)
                            render_controls(min(1.0, position / duration) if duration else 0.0)
                            show_status(position, "⏸️")
                            continue
                        if paused_action == REDRAW_UI:
                            help_overlay_until = 0.0
                            clear_region(HEADER_ROW, UI_ROWS)
                            render_static_header()
                            render_controls(min(1.0, position / duration) if duration else 0.0)
                            last_drcs_position = None
                            last_lyric_index = None
                            show_status(position, "⏸️")
                            continue
                        if reset_or_undo_modes(paused_action):
                            clear_region(HEADER_ROW, UI_ROWS)
                            render_static_header()
                            render_controls(min(1.0, position / duration) if duration else 0.0)
                            last_drcs_position = None
                            last_lyric_index = None
                            show_status(position, "⏸️")
                            continue
                        if abort_requested.is_set() or paused_action == STOP:
                            return finish_playback("stopped")
                        if paused_action in NAVIGATION_ACTIONS:
                            return finish_playback(paused_action)
                        if paused_action == PAUSE_TOGGLE:
                            indicator = "▶️"
                            break
                        if paused_action == LOOP_TOGGLE:
                            looping = not looping
                            if looping_state is not None:
                                looping_state[0] = looping
                            render_controls(
                                min(1.0, position / duration)
                                if duration else 0.0
                            )
                            show_status(position, "⏸️")
                        if paused_action == RANDOM_TOGGLE and shuffle_state is not None:
                            shuffle_state[0] = not shuffle_state[0]
                            render_controls(
                                min(1.0, position / duration)
                                if duration else 0.0
                            )
                        if paused_action == VISUALIZER_MODE_FIRST:
                            visualizer_mode = 1
                            if visualizer_mode_state is not None:
                                visualizer_mode_state[0] = visualizer_mode
                            render_controls(min(1.0, position / duration) if duration else 0.0)
                        elif paused_action == VISUALIZER_MODE_PREVIOUS:
                            paused_type = ((visualizer_mode - 1) % len(VISUALIZER_TYPE_NAMES) - 1) % len(VISUALIZER_TYPE_NAMES)
                            paused_treatment = (visualizer_mode - 1) // len(VISUALIZER_TYPE_NAMES)
                            visualizer_mode = paused_treatment * len(VISUALIZER_TYPE_NAMES) + paused_type + 1
                            if visualizer_mode_state is not None:
                                visualizer_mode_state[0] = visualizer_mode
                            render_controls(min(1.0, position / duration) if duration else 0.0)
                        elif paused_action == VISUALIZER_MODE_NEXT:
                            paused_type = ((visualizer_mode - 1) % len(VISUALIZER_TYPE_NAMES) + 1) % len(VISUALIZER_TYPE_NAMES)
                            paused_treatment = (visualizer_mode - 1) // len(VISUALIZER_TYPE_NAMES)
                            visualizer_mode = paused_treatment * len(VISUALIZER_TYPE_NAMES) + paused_type + 1
                            if visualizer_mode_state is not None:
                                visualizer_mode_state[0] = visualizer_mode
                            render_controls(min(1.0, position / duration) if duration else 0.0)
                        elif paused_action == VISUALIZER_MODE_FAVORITE:
                            added = toggle_registry_favorite("VisualizerFavorites", visualizer_mode)
                            save_favorite_visualizer_mode(visualizer_mode if added else 1)
                        elif paused_action in {VISUALIZER_TREATMENT_PREVIOUS, VISUALIZER_TREATMENT_NEXT}:
                            paused_type = (visualizer_mode - 1) % len(VISUALIZER_TYPE_NAMES)
                            paused_treatment = (visualizer_mode - 1) // len(VISUALIZER_TYPE_NAMES)
                            paused_treatment = (
                                (paused_treatment - 1) % len(VISUALIZER_TREATMENT_NAMES)
                                if paused_action == VISUALIZER_TREATMENT_PREVIOUS
                                else (paused_treatment + 1) % len(VISUALIZER_TREATMENT_NAMES)
                            )
                            visualizer_mode = paused_treatment * len(VISUALIZER_TYPE_NAMES) + paused_type + 1
                            if visualizer_mode_state is not None:
                                visualizer_mode_state[0] = visualizer_mode
                            render_controls(min(1.0, position / duration) if duration else 0.0)
                        elif isinstance(paused_action, str) and paused_action.startswith("visualizer-mode-digit:"):
                            digit_now = monotonic()
                            if digit_now - last_visualizer_digit_at > 1.0:
                                visualizer_mode_digits = ""
                            visualizer_mode_digits += paused_action.rpartition(":")[2]
                            candidate_mode = int(visualizer_mode_digits)
                            if 1 <= candidate_mode <= len(VISUALIZER_MODE_NAMES):
                                visualizer_mode = candidate_mode
                            else:
                                visualizer_mode_digits = paused_action.rpartition(":")[2]
                            last_visualizer_digit_at = digit_now
                            if visualizer_mode_state is not None:
                                visualizer_mode_state[0] = visualizer_mode
                            render_controls(min(1.0, position / duration) if duration else 0.0)
                        if paused_action in {COLOR_PREVIOUS, COLOR_NEXT, COLOR_FAVORITE_TOGGLE, COLOR_FAVORITE_CYCLE}:
                            if paused_action == COLOR_PREVIOUS:
                                color_style = ((color_style - 2) % len(COLOR_STYLE_NAMES)) + 1
                            elif paused_action == COLOR_NEXT:
                                color_style = (color_style % len(COLOR_STYLE_NAMES)) + 1
                            elif paused_action == COLOR_FAVORITE_TOGGLE:
                                toggle_registry_favorite("ColorFavorites", color_style)
                            else:
                                color_style = next_registry_favorite("ColorFavorites", color_style)
                            if color_style_state is not None:
                                color_style_state[0] = color_style
                            render_controls(min(1.0, position / duration) if duration else 0.0)
                            show_status(position, "⏸️")
                        if change_karaoke(paused_action):
                            last_lyric_index = None
                            render_controls(min(1.0, position / duration) if duration else 0.0)
                            show_status(position, "⏸️")
                        if paused_action in {PROGRESS_STYLE_PREVIOUS, PROGRESS_STYLE_NEXT}:
                            progress_style = (((progress_style - 2) % len(PROGRESS_STYLE_NAMES)) + 1 if paused_action == PROGRESS_STYLE_PREVIOUS else (progress_style % len(PROGRESS_STYLE_NAMES)) + 1)
                            if progress_style_state is not None:
                                progress_style_state[0] = progress_style
                            render_controls(min(1.0, position / duration) if duration else 0.0)
                            show_status(position, "⏸️")
                        if paused_action == AUTOPLAY_TOGGLE and autoplay_state is not None:
                            autoplay_state[0] = not autoplay_state[0]
                            if autoplay_state[0]:
                                looping = False
                                if shuffle_state is not None:
                                    shuffle_state[0] = True
                            render_controls(min(1.0, position / duration) if duration else 0.0)
                        if paused_action in VOLUME_STEPS or paused_action == VOLUME_RESET:
                            change_volume(paused_action, monotonic())
                            show_status(position, "⏸️")
                        if paused_action in {OUTPUT_STEREO, OUTPUT_51, OUTPUT_71}:
                            output_channels = {
                                OUTPUT_STEREO: 2, OUTPUT_51: 5, OUTPUT_71: 7,
                            }[paused_action]
                            if output_channels_state is not None:
                                output_channels_state[0] = output_channels
                            render_controls(min(1.0, position / duration) if duration else 0.0)
                        if paused_action in {BALANCE_LEFT, BALANCE_RIGHT, BALANCE_CENTER}:
                            balance = (
                                0 if paused_action == BALANCE_CENTER
                                else max(-100, balance - 10) if paused_action == BALANCE_LEFT
                                else min(100, balance + 10)
                            )
                            if balance_state is not None:
                                balance_state[0] = balance
                            render_controls(min(1.0, position / duration) if duration else 0.0)
                            show_status(position, "⏸️")
                        sleeper(0.02)
                    break
                if action in SEEK_SECONDS:
                    record_segment(displayed_position)
                    destination = max(
                        0.0,
                        position + elapsed + SEEK_SECONDS[action],
                    )
                    if duration is not None:
                        destination = min(
                            destination,
                            max(0.0, duration - 0.05),
                        )
                    stop_process(process)
                    position = destination
                    indicator = {
                        SEEK_BACK_5: "↩️", SEEK_FORWARD_5: "↪️",
                        SEEK_BACK_10: "⏪", SEEK_FORWARD_10: "⏩",
                        SEEK_BACK_15: "⏪", SEEK_FORWARD_15: "⏩",
                        SEEK_BACK_60: "⏮️", SEEK_FORWARD_60: "⏭️",
                    }[action]
                    show_status(position, indicator)
                    break
                sleeper(0.02)
            else:
                startup_elapsed = max(0.0, monotonic() - segment_started)
                # FFplay/SDL exits immediately when a requested device rate is
                # unavailable. Retry once at 96 kHz before treating it as EOF.
                if output_rate == 192000 and startup_elapsed < 0.35 and (duration is None or duration > 1.0):
                    output_rate = 96000
                    continue
                completed_position = position + startup_elapsed * speed
                record_segment(
                    min(duration, completed_position)
                    if duration is not None else completed_position
                )
                if abort_requested.is_set():
                    return finish_playback("stopped")
                if looping:
                    position = 0.0
                    indicator = "🔁"
                    continue
                return finish_playback("completed")
    finally:
        stop_process(process)
        set_console_title(previous_console_title)
        resume_winamp_if_paused_by_preview(winamp_paused_by_preview)
        if not screen_closed:
            _CURSOR_SUPPRESSION_ACTIVE = False
            write_console("\033[?7h\033[u\033[?25h")
            set_console_cursor_visible(True)
        for supported, previous in previous_handlers.items():
            signal.signal(supported, previous)


def play_audio_filename(audio_filename: str | os.PathLike[str]) -> str:
    """Convenience entry point for callers that pass a filename."""
    return play_audio_file(audio_filename)


class PlayWaveFileTests(unittest.TestCase):
    """Embedded unit coverage for controls and process restarts."""

    @unittest.skipUnless(os.name == "nt", "Winamp messaging is Windows-only")
    def test_winamp_is_paused_and_resumed_without_stop(self) -> None:
        import ctypes

        state = {"value": 1}
        commands: list[int] = []
        user32 = mock.Mock()
        user32.FindWindowW.return_value = 123

        def send_message(_hwnd, message, parameter, _lparam):
            if message == 0x0400:
                return state["value"]
            if message == 0x0111:
                commands.append(parameter)
                if parameter == 40046:
                    state["value"] = 3 if state["value"] == 1 else 1
            return 0

        user32.SendMessageW.side_effect = send_message
        with mock.patch.object(ctypes, "windll", mock.Mock(user32=user32)):
            self.assertTrue(pause_playing_winamp())
            self.assertEqual(3, state["value"])
            resume_winamp_if_paused_by_preview(True)

        self.assertEqual(1, state["value"])
        self.assertEqual([40046, 40046], commands)
        self.assertNotIn(40047, commands)

    @unittest.skipUnless(os.name == "nt", "Winamp messaging is Windows-only")
    def test_resume_does_not_relaunch_missing_winamp(self) -> None:
        import ctypes

        user32 = mock.Mock()
        user32.FindWindowW.return_value = 0
        with mock.patch.object(ctypes, "windll", mock.Mock(user32=user32)), \
            mock.patch(__name__ + ".subprocess.Popen") as popen_mock:
            resume_winamp_if_paused_by_preview(True)

        popen_mock.assert_not_called()
        user32.SendMessageW.assert_not_called()

    def test_stop_and_seek_key_mappings(self) -> None:
        self.assertEqual(DISMISS_OVERLAY, interpret_console_key("\x1b"))
        for key in ("x", "X", "q", "Q", "\x17", "\x03"):
            self.assertEqual(STOP, interpret_console_key(key))
        self.assertEqual(
            STOP,
            interpret_console_key("w", ctrl=True),
        )
        self.assertEqual(
            STOP,
            interpret_console_key(
                "\x00",
                extended=">",
                alt=True,
            ),
        )
        self.assertEqual(
            SEEK_BACK_5,
            interpret_console_key("\xe0", extended="K"),
        )
        self.assertEqual(
            SEEK_FORWARD_5,
            interpret_console_key("\xe0", extended="M"),
        )
        self.assertEqual(
            SEEK_BACK_15,
            interpret_console_key(
                "\xe0",
                extended="K",
                shift=True,
            ),
        )
        self.assertEqual(
            SEEK_FORWARD_15,
            interpret_console_key(
                "\xe0",
                extended="M",
                shift=True,
            ),
        )
        self.assertEqual(PAUSE_TOGGLE, interpret_console_key(" "))
        self.assertEqual(PROGRESS_STYLE_NEXT, interpret_console_key("p"))
        self.assertEqual(PROGRESS_STYLE_PREVIOUS, interpret_console_key("p", shift=True))
        self.assertEqual(VOLUME_RESET, interpret_console_key("="))
        self.assertEqual(LOOP_TOGGLE, interpret_console_key("l"))
        self.assertEqual(FAVORITE_MENU, interpret_console_key("f"))
        self.assertEqual(FADE_NEXT, interpret_console_key("f", alt=True))
        self.assertEqual(FADE_PREVIOUS, interpret_console_key("f", shift=True))
        self.assertEqual(COLOR_NEXT, interpret_console_key("c"))
        self.assertEqual(COLOR_PREVIOUS, interpret_console_key("c", shift=True))
        self.assertEqual(COLOR_FAVORITE_CYCLE, interpret_console_key("c", alt=True))
        self.assertEqual(KARAOKE_NEXT, interpret_console_key("k"))
        self.assertEqual(KARAOKE_PREVIOUS, interpret_console_key("k", shift=True))
        self.assertEqual(KARAOKE_TREATMENT_NEXT, interpret_console_key("\x0b"))
        self.assertEqual(KARAOKE_FAVORITE_TOGGLE, interpret_console_key("\x0b", alt=True))
        self.assertEqual(KARAOKE_FAVORITE_CYCLE, interpret_console_key("k", alt=True))
        self.assertEqual(AUTOPLAY_TOGGLE, interpret_console_key("a"))
        self.assertEqual(GOTO_URL, interpret_console_key("\x07"))
        self.assertEqual("visualizer-mode-digit:3", interpret_console_key("3"))
        self.assertEqual(RESET_DEFAULTS, interpret_console_key("\x00", extended=";"))
        self.assertEqual(KARAOKE_PREVIOUS, interpret_console_key("\x00", extended="<"))
        self.assertEqual(KARAOKE_NEXT, interpret_console_key("\x00", extended="="))
        self.assertEqual(KARAOKE_TREATMENT_PREVIOUS, interpret_console_key("\x00", extended="<", shift=True))
        self.assertEqual(KARAOKE_TREATMENT_NEXT, interpret_console_key("\x00", extended="=", shift=True))
        self.assertEqual(KARAOKE_EMOJI_TOGGLE, interpret_console_key("\x00", extended=">"))
        self.assertEqual(KARAOKE_VISUALIZER_OVERLAY_TOGGLE, interpret_console_key("\x00", extended="D", shift=True))
        self.assertIsNone(interpret_console_key("v", ctrl=True, alt=True))
        self.assertEqual(ALBUM_ART_VISUALIZER_TOGGLE, interpret_console_key("\x00", extended="B", ctrl=True, alt=True))
        self.assertEqual(KARAOKE_VISUALIZER_EXPAND_TOGGLE, interpret_console_key("\x00", extended="C", ctrl=True, alt=True))
        self.assertEqual(REDRAW_UI, interpret_console_key("\x00", extended="?"))
        self.assertEqual(
            DRCS_VISUALIZER_TOGGLE,
            interpret_console_key("v", ctrl=True),
        )
        self.assertEqual(
            SIXEL_VISUALIZER_TOGGLE,
            interpret_console_key("w"),
        )
        self.assertEqual(
            STOP,
            interpret_console_key("w", ctrl=True),
        )
        self.assertEqual(
            SEEK_BACK_60,
            interpret_console_key("\xe0", extended="K", ctrl=True),
        )
        self.assertEqual(
            SEEK_FORWARD_60,
            interpret_console_key("\xe0", extended="M", ctrl=True),
        )
        self.assertEqual(
            SEEK_BACK_60,
            interpret_console_key("\xe0", extended="s"),
        )
        self.assertEqual(
            SEEK_FORWARD_60,
            interpret_console_key("\xe0", extended="t"),
        )
        self.assertEqual(PREVIOUS_FILE, interpret_console_key("<"))
        self.assertEqual(NEXT_FILE, interpret_console_key(">"))
        self.assertEqual(PREVIOUS_DIRECTORY, interpret_console_key("{"))
        self.assertEqual(NEXT_DIRECTORY, interpret_console_key("}"))
        self.assertEqual(
            VOLUME_UP_5,
            interpret_console_key("\xe0", extended="H"),
        )
        self.assertEqual(
            VOLUME_DOWN_20,
            interpret_console_key("\xe0", extended="P", shift=True),
        )
        self.assertEqual("", volume_status(100, "up"))
        self.assertIn("Volume: 25%", volume_status(25, "up"))
        self.assertIn("38;2;255;", volume_status(99, "up"))
        self.assertIn("38;2;127;0;255", volume_status(0, "down"))
        self.assertIn("Loop: On", loop_status(True, 0.5))
        self.assertIn("Loop: Off", loop_status(False, 0.5))
        self.assertIn(
            "50%",
            render_status(30, 60, "▶️", 100, "up", True, 60, repaint=False),
        )
        self.assertEqual("atempo=0.5,atempo=0.8", atempo_filter(0.4))
        self.assertEqual(
            "atempo=2,atempo=2,atempo=2,atempo=2,atempo=2,atempo=1.25",
            atempo_filter(40),
        )
        self.assertEqual(OUTPUT_STEREO, interpret_console_key("2"))
        self.assertEqual(OUTPUT_51, interpret_console_key("5"))
        self.assertEqual(OUTPUT_71, interpret_console_key("7"))
        self.assertEqual("visualizer-mode-digit:3", interpret_console_key("3"))

    def test_file_and_directory_navigation_wraps_as_requested(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            library = Path(temp) / "MUSIC"
            first_album = library / "Artist" / "01 Album"
            second_album = library / "Artist" / "02 Album"
            first_album.mkdir(parents=True)
            second_album.mkdir(parents=True)
            tracks = [first_album / name for name in ("1.flac", "2.flac", "10.flac")]
            other_tracks = [second_album / name for name in ("1.mp3", "2.mp3")]
            for track in (*tracks, *other_tracks):
                track.write_bytes(b"audio")

            self.assertEqual(tracks[1], navigate_audio_path(tracks[0], NEXT_FILE))
            self.assertEqual(tracks[0], navigate_audio_path(tracks[-1], NEXT_FILE))
            self.assertEqual(tracks[-1], navigate_audio_path(tracks[0], PREVIOUS_FILE))
            self.assertEqual(other_tracks[0], navigate_audio_path(tracks[0], NEXT_DIRECTORY))
            self.assertEqual(other_tracks[-1], navigate_audio_path(tracks[0], PREVIOUS_DIRECTORY))

    def test_random_modes_and_relative_playlist_do_not_require_tree_scan(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            leaf = root / "one" / "two"
            leaf.mkdir(parents=True)
            track = leaf / "track.flac"
            track.write_bytes(b"audio")
            with mock.patch("random.choice", side_effect=lambda values: values[0]), mock.patch(
                "os.walk", side_effect=AssertionError("random mode must not use os.walk")
            ):
                self.assertEqual(track.resolve(), random_audio_file_recursive(root))
            playlist = root / "list.m3u8"
            playlist.write_text("#EXTM3U\none/two/track.flac\n", encoding="utf-8")
            self.assertEqual([track.resolve()], load_playlist(playlist))

    def test_broken_id3_pair_swapped_text_is_recovered(self) -> None:
        self.assertEqual(
            "Ween Archive",
            _decode_id3_text_payload(b"\x03\xff\xfeeWneA crihev"),
        )

    def test_missing_song_tag_falls_back_to_track_filename(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            track = Path(temp) / "19_Scott.mp3"
            # A tiny ID3v2.3 tag with deliberately empty title/artist/album frames.
            frames = b"".join(
                frame + len(payload).to_bytes(4, "big") + b"\x00\x00" + payload
                for frame, payload in (
                    (b"TIT2", b"\x03"),
                    (b"TPE1", b"\x03"),
                    (b"TALB", b"\x03"),
                    (b"TDRC", b"\x002022"),
                )
            )
            size = len(frames)
            synchsafe = bytes((
                (size >> 21) & 0x7F,
                (size >> 14) & 0x7F,
                (size >> 7) & 0x7F,
                size & 0x7F,
            ))
            track.write_bytes(b"ID3\x03\x00\x00" + synchsafe + frames)
            _AUDIO_METADATA_CACHE.clear()
            with mock.patch(__name__ + ".ffprobe_executable", return_value=None):
                _duration, tags = probe_audio_metadata(track)
            self.assertEqual("Scott", tags["Song"])
            self.assertEqual("2022", tags["Year"])
            self.assertEqual("", tags["Artist"])
            self.assertEqual("", tags["Album"])

    def test_report_artist_grouping_ignores_features_punctuation_and_and_style(self) -> None:
        self.assertEqual(
            report_artist_group_key("Earth Wind & Fire"),
            report_artist_group_key("Earth, Wind And Fire"),
        )
        self.assertEqual(
            report_artist_group_key("Hank Williams Jr"),
            report_artist_group_key("Hank Williams Jr."),
        )
        self.assertEqual(
            report_artist_group_key("D·O·A·"),
            report_artist_group_key("D.O.A."),
        )
        self.assertEqual(
            report_artist_group_key("Eat Babies? feat Aaron Carter"),
            report_artist_group_key("EAT BABIES"),
        )

    def test_report_artist_display_strips_feature_credit_and_repairs_known_typo(self) -> None:
        self.assertEqual("Eat Babies?", clean_report_artist_display("Eat Babies? feat DJ Migraine"))
        self.assertEqual("Girls Rituals", clean_report_artist_display("Girls Ritual"))
        self.assertEqual(
            "Eat Babies?",
            most_common_report_artist_style({"EAT BABIES": 1, "Eat Babies?": 4, "EAT BABIES?": 1}),
        )

    def test_playlist_history_identity_uses_fast_normalized_filename_first(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            database_path = root / "history.sqlite3"
            track = root / "some" / "folder" / "08_Diamant.mp3"
            track.parent.mkdir(parents=True)
            track.write_bytes(b"audio")
            _PLAYLIST_HISTORY_IDENTITY_CACHE.clear()
            with mock.patch.dict(os.environ, {"PLAY_AUDIO_FILE_HISTORY_DB": str(database_path)}):
                playlist_history_mark_played(
                    track,
                    duration_seconds=154,
                    tags={"Artist": "  RAMMSTEIN ", "Song": "Ｄｉａｍａｎｔ"},
                )
                with playlist_history_connection() as database:
                    columns = [row[1] for row in database.execute("PRAGMA table_info(played_tracks_recent)")]
                    rows = database.execute(
                        "SELECT filename, duration_seconds, tag, played_at FROM played_tracks_recent"
                    ).fetchall()
            self.assertEqual(["filename", "duration_seconds", "tag", "played_at"], columns)
            self.assertEqual(1, len(rows))
            self.assertEqual("diamant", rows[0][0])
            self.assertEqual(154, rows[0][1])
            self.assertEqual("rammstein\x1fdiamant", rows[0][2])

    def test_playlist_history_migrates_filename_schema_and_normalizes_key(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            database_path = Path(temp) / "history.sqlite3"
            database = sqlite3.connect(database_path)
            database.execute(
                """CREATE TABLE played_tracks_recent (
                    duration_seconds INTEGER NOT NULL,
                    tag TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    played_at REAL NOT NULL,
                    PRIMARY KEY(duration_seconds, tag, filename)
                ) WITHOUT ROWID"""
            )
            database.executemany(
                "INSERT INTO played_tracks_recent VALUES (?, ?, ?, ?)",
                [
                    (154, "rammstein\x1fdiamant", r"C:\\mp3\\Rammstein\\08_Diamant.mp3", 10.0),
                    (154, "rammstein\x1fdiamant", "Diamant.flac", 20.0),
                ],
            )
            database.commit()
            database.close()
            with mock.patch.dict(os.environ, {"PLAY_AUDIO_FILE_HISTORY_DB": str(database_path)}):
                with playlist_history_connection() as migrated:
                    columns = [row[1] for row in migrated.execute("PRAGMA table_info(played_tracks_recent)")]
                    rows = migrated.execute(
                        "SELECT filename, duration_seconds, tag, played_at FROM played_tracks_recent"
                    ).fetchall()
            self.assertEqual(["filename", "duration_seconds", "tag", "played_at"], columns)
            self.assertEqual([("diamant", 154, "rammstein\x1fdiamant", 20.0)], rows)

    def test_playlist_history_preserves_unconvertible_duration_tag_schema_as_backup(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            database_path = Path(temp) / "history.sqlite3"
            database = sqlite3.connect(database_path)
            database.execute(
                """CREATE TABLE played_tracks_recent (
                    duration_seconds INTEGER NOT NULL,
                    tag TEXT NOT NULL,
                    played_at REAL NOT NULL,
                    PRIMARY KEY(duration_seconds, tag)
                ) WITHOUT ROWID"""
            )
            database.execute(
                "INSERT INTO played_tracks_recent VALUES (?, ?, ?)",
                (154, "rammstein\x1fdiamant", 20.0),
            )
            database.commit()
            database.close()
            with mock.patch.dict(os.environ, {"PLAY_AUDIO_FILE_HISTORY_DB": str(database_path)}):
                with playlist_history_connection() as migrated:
                    columns = [row[1] for row in migrated.execute("PRAGMA table_info(played_tracks_recent)")]
                    rows = migrated.execute("SELECT * FROM played_tracks_recent").fetchall()
                    backups = migrated.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'played_tracks_recent_backup_%'"
                    ).fetchall()
            self.assertEqual(["filename", "duration_seconds", "tag", "played_at"], columns)
            self.assertEqual([], rows)
            self.assertEqual(1, len(backups))

    def test_playlist_history_5000_unique_filenames_need_no_metadata_probe(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            database_path = root / "history.sqlite3"
            entries = [root / f"{index:04d}_Song {index}.mp3" for index in range(5000)]
            with mock.patch.dict(os.environ, {"PLAY_AUDIO_FILE_HISTORY_DB": str(database_path)}):
                with playlist_history_connection() as database:
                    database.executemany(
                        "INSERT INTO played_tracks_recent(filename, duration_seconds, tag, played_at) VALUES (?, ?, ?, ?)",
                        [
                            (playlist_history_filename_key(entry), 180, f"artist\x1fsong {index}", float(index + 1))
                            for index, entry in enumerate(entries)
                        ],
                    )
                with mock.patch(__name__ + ".playlist_history_identity", side_effect=AssertionError("unexpected probe")), mock.patch(
                    "random.choice", side_effect=lambda values: values[0]
                ):
                    chosen = choose_least_recent_playlist_track(entries)
            self.assertIn(chosen, entries)

    def test_playlist_shuffle_order_reads_history_once_and_returns_every_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            entries = [root / f"song-{index}.mp3" for index in range(20)]
            scores = [(float(index), entry) for index, entry in enumerate(entries)]
            with mock.patch(__name__ + ".playlist_history_scores", return_value=scores) as scorer:
                order = build_playlist_shuffle_order(entries)
            scorer.assert_called_once_with(entries, None)
            self.assertCountEqual(entries, order)

    def test_playlist_history_probes_only_ambiguous_filename_collision(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            database_path = root / "history.sqlite3"
            entry = root / "08_Diamant.mp3"
            filename = playlist_history_filename_key(entry)
            with mock.patch.dict(os.environ, {"PLAY_AUDIO_FILE_HISTORY_DB": str(database_path)}):
                with playlist_history_connection() as database:
                    database.executemany(
                        "INSERT INTO played_tracks_recent(filename, duration_seconds, tag, played_at) VALUES (?, ?, ?, ?)",
                        [
                            (filename, 154, "rammstein\x1fdiamant", 20.0),
                            (filename, 999, "other\x1fdiamant", 10.0),
                        ],
                    )
                with mock.patch(
                    __name__ + ".playlist_history_identity",
                    return_value=(filename, 154, "rammstein\x1fdiamant"),
                ) as identity_probe, mock.patch("random.choice", side_effect=lambda values: values[0]):
                    self.assertEqual(entry, choose_least_recent_playlist_track([entry]))
                identity_probe.assert_called_once_with(entry)

    def test_playlist_defaults_to_shuffle_and_advances_without_track_loop(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            tracks = [root / "one.flac", root / "two.flac"]
            for track in tracks:
                track.write_bytes(b"audio")
            playlist = root / "list.m3u"
            playlist.write_text("one.flac\ntwo.flac\n", encoding="utf-8")
            with mock.patch(__name__ + ".play_audio_file", side_effect=["completed", "stopped"]) as player, mock.patch(
                __name__ + ".pause_playing_winamp", return_value=False
            ), mock.patch(__name__ + ".resume_winamp_if_paused_by_preview"), mock.patch(
                "random.choice", side_effect=lambda values: values[0]
            ), mock.patch(__name__ + ".load_playlist_resume", return_value=None), mock.patch(
                __name__ + ".clear_playlist_resume"
            ), mock.patch(
                __name__ + ".load_player_settings", return_value=dict(PLAYER_SETTING_DEFAULTS)
            ), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, main(["--playlist", str(playlist)]))
            self.assertEqual(2, player.call_count)
            self.assertFalse(player.call_args_list[0].kwargs["looping"])
            self.assertEqual([True], player.call_args_list[0].kwargs["shuffle_state"])

    def test_playlist_quit_restores_and_saves_same_track_position(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first, second = root / "one.flac", root / "two.flac"
            first.write_bytes(b"audio")
            second.write_bytes(b"audio")
            playlist = root / "list.m3u8"
            playlist.write_text("one.flac\ntwo.flac\n", encoding="utf-8")
            with mock.patch(
                __name__ + ".load_playlist_resume", return_value=(second, 47.25)
            ), mock.patch(__name__ + ".save_playlist_resume") as saver, mock.patch(
                __name__ + ".play_audio_file", return_value="stopped"
            ) as player, mock.patch(
                __name__ + ".pause_playing_winamp", return_value=False
            ), mock.patch(__name__ + ".resume_winamp_if_paused_by_preview"), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, main(["--playlist", str(playlist)]))
            self.assertEqual(second.resolve(), Path(player.call_args.args[0]).resolve())
            self.assertEqual(47.25, player.call_args.kwargs["initial_position"])
            saver.assert_called_once()
            self.assertEqual(second.resolve(), Path(saver.call_args.args[1]).resolve())
            self.assertEqual(47.25, saver.call_args.args[2])

    def test_tag_panel_packs_fields_by_priority_and_reserves_mode_markers(self) -> None:
        plain, ansi = format_tag_panel({
            "Artist": "Example Artist",
            "Song": "Example Song",
            "Album": "Example Album",
            "Year": "2026",
            "Genre": "Punk",
            "Comment": "Great mix",
        }, width=200, song_rgb=(255, 0, 0), album_art_visualizer_enabled=True)
        self.assertEqual(1, len(plain))
        self.assertEqual(1, len(ansi))
        row = plain[0]
        self.assertLess(row.index("Artist:"), row.index("Song:"))
        self.assertLess(row.index("Song:"), row.index("Album:"))
        self.assertLess(row.index("Album:"), row.index("Year:"))
        self.assertLess(row.index("Year:"), row.index("Genre:"))
        self.assertLess(row.index("Genre:"), row.index("Comment:"))
        self.assertIn("Punk 🧷  🎨", row)
        self.assertIn("\033[38;2;255;0;0mExample Song", ansi[0])


    def test_srt_sidecar_preferred_and_utf16_decoded(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            audio = Path(temp) / "song.flac"
            audio.write_bytes(b"audio")
            audio.with_suffix(".lrc").write_text("[00:01.00]Wrong LRC\n", encoding="utf-8")
            audio.with_suffix(".srt").write_text(
                "1\n00:00:02,000 --> 00:00:03,500\nRight SRT\n\n",
                encoding="utf-16",
            )
            self.assertEqual([(2.0, 3.5, "Right SRT")], load_lyrics(audio))

    def test_emojimax_one_of_preserves_space_and_fan_is_plain(self) -> None:
        rendered = stylize_karaoke_with_emojimax("one of fan snakes", 1, True)
        self.assertIn("❶ of", rendered)
        self.assertIn("fan", rendered)
        self.assertIn("🐍🐍🐍", rendered)
        self.assertNotIn("🪭", rendered)

    def test_ui_refinements_v7_regressions(self) -> None:
        self.assertEqual("🌍", semantic["world"])
        self.assertEqual("love", stylize_karaoke_with_emojimax("love", 1, True, 0.24))
        self.assertIn("💞", stylize_karaoke_with_emojimax("love", 1, True, 0.25))
        self.assertEqual("10min", format_last_heard_age(10 * 60))
        self.assertEqual("1.25hr", format_last_heard_age(1.25 * 3600))
        self.assertEqual("2.5d", format_last_heard_age(2.5 * 86400))
        self.assertEqual("6mos", format_last_heard_age(6 * 30.4375 * 86400))
        self.assertEqual("1.1yr", format_last_heard_age(1.1 * 365.25 * 86400))
        self.assertIn("▏", render_status(1, 8, "▶", 100, "up", False, 1, repaint=False))
        rows, _ansi = format_tag_panel({
            "Artist": "Artist", "Song": "Song", "Album": "Some Album",
            "Year": "2026", "Genre": "Punk", "Comment": "Comment",
        }, width=56)
        self.assertNotIn("Year:", rows[0])
        self.assertIn("Year: 2026", rows[1])
        self.assertIn("Genre: Punk 🧷", rows[1])
        self.assertEqual(25, HIDE_EMOJI_WHEN_FADE_IS_UNDER_X_PERCENT)
        self.assertEqual(1, NEXT_SUNG_LINE_EMOJIMAXX_ON_AT_FIRST)
        self.assertEqual((105, 235, 145), PLAYING_PATH_RGB)
        markers, _marker_ansi = format_tag_panel(
            {"Genre": "Punk"}, width=120,
            album_art_visualizer_enabled=True,
            karaoke_visualizer_expansion_enabled=True,
        )
        self.assertIn("🎨", " ".join(markers))
        self.assertNotIn("💹", " ".join(markers))
        disabled_markers, _ = format_tag_panel(
            {"Genre": "Punk"}, width=120, karaoke_visualizer_expansion_enabled=False
        )
        self.assertIn("💹−", " ".join(disabled_markers))

    def test_v15_osc8_url_is_clickable_without_affecting_cell_width(self) -> None:
        url = "https://example.com/path?q=1"
        linked = osc8_hyperlink(url, url)
        self.assertIn("\033]8;;https://example.com/path?q=1\033\\", linked)
        self.assertEqual(url, ANSI_CSI_RE.sub("", linked))
        clipped = truncate_ansi_to_cells(linked, 12)
        self.assertIn(OSC8_CLOSE, clipped)
        self.assertLessEqual(terminal_cell_width(ANSI_CSI_RE.sub("", clipped)), 12)

    def test_v15_next_line_emojimax_is_immediate_but_previous_can_revert(self) -> None:
        self.assertEqual(1, NEXT_SUNG_LINE_EMOJIMAXX_ON_AT_FIRST)
        self.assertIn("💞", stylize_karaoke_with_emojimax("love", 1, True, 0.01, fade_threshold_percent=0.0))
        self.assertEqual("love", stylize_karaoke_with_emojimax("love", 1, True, 0.49, fade_threshold_percent=HIDE_PREVIOUS_EMOJI_WHEN_FADE_IS_UNDER_X_PERCENT))
        self.assertIn("💞", stylize_karaoke_with_emojimax("love", 1, True, 0.50, fade_threshold_percent=HIDE_PREVIOUS_EMOJI_WHEN_FADE_IS_UNDER_X_PERCENT))

    def test_ffprobe_tags_are_decoded_as_utf8(self) -> None:
        result = mock.Mock(
            stdout=json.dumps({"format": {"tags": {
                "artist": "Kill Switch․․․ Klick",
                "album": "TV Terror∶ Felching A Dead Horse",
            }}}),
            returncode=0,
        )
        with mock.patch(__name__ + ".ffprobe_executable", return_value=Path("ffprobe.exe")), mock.patch(
            "subprocess.run", return_value=result
        ) as runner:
            tags = probe_audio_tags(Path("song.flac"))
        self.assertEqual("Kill Switch․․․ Klick", tags["Artist"])
        self.assertEqual("TV Terror∶ Felching A Dead Horse", tags["Album"])
        self.assertEqual("utf-8", runner.call_args.kwargs["encoding"])

    def test_lrc_sidecar_drives_timed_lyrics(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            audio = Path(temp) / "song.flac"
            audio.write_bytes(b"audio")
            audio.with_suffix(".lrc").write_text(
                "[00:01.00]First line\n[00:03.50]Second line\n",
                encoding="utf-8",
            )
            entries = load_lyrics(audio)
            first = lyric_at(entries, 2.0)
            second = lyric_at(entries, 4.0)
            self.assertEqual((0, "First line"), first[:2] if first else None)
            self.assertEqual((1, "Second line"), second[:2] if second else None)
            self.assertEqual(1.0, first[2])
            long_gap = [(0.0, None, "Held line"), (40.0, None, "Later line")]
            self.assertLess(lyric_at(long_gap, 16.0)[2], 1.0)
            self.assertLess(lyric_at(long_gap, 19.0)[2], lyric_at(long_gap, 16.0)[2])

    def test_album_art_sidecar_is_discovered_and_cached(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            audio = Path(temp) / "song.flac"
            audio.write_bytes(b"audio")
            art = audio.with_suffix(".jpg")
            art.write_bytes(b"sidecar-art")
            with mock.patch("shutil.which", return_value=None):
                first = extract_album_art(audio)
                art.unlink()
                second = extract_album_art(audio)
            self.assertEqual(b"sidecar-art", first)
            self.assertEqual(first, second)

    @unittest.skipUnless(importlib.util.find_spec("PIL"), "Pillow is required")
    def test_album_art_composite_keeps_spectrum_visible(self) -> None:
        from PIL import Image

        def png(color: tuple[int, int, int]) -> bytes:
            output = io.BytesIO()
            Image.new("RGB", (4, 4), color).save(output, format="PNG")
            return output.getvalue()

        rendered = composite_album_art_background(
            png((255, 0, 0)), png((0, 0, 255)), 4, 4
        )
        with Image.open(io.BytesIO(rendered)) as image:
            self.assertEqual((255, 0, 0), image.getpixel((0, 0)))

        rendered = composite_album_art_background(
            png((0, 0, 0)), png((0, 255, 0)), 4, 4
        )
        with Image.open(io.BytesIO(rendered)) as image:
            self.assertGreater(image.getpixel((0, 0))[1], 0)

    @unittest.skipUnless(shutil.which("ffmpeg"), "FFmpeg is required")
    def test_drcs_timeline_and_single_font_download_are_nonempty(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            audio = Path(temp) / "inaudible-test-tone.wav"
            frames = bytearray()
            for sample in range(8000):
                value = int(12000 * math.sin(2 * math.pi * 440 * sample / 8000))
                frames.extend(value.to_bytes(2, "little", signed=True))
            with wave.open(str(audio), "wb") as output:
                output.setnchannels(1)
                output.setsampwidth(2)
                output.setframerate(8000)
                output.writeframes(frames)
            timeline = build_audio_spectrum_timeline(audio, 40, duration_limit=1.0)
            self.assertTrue(timeline[0])
            self.assertTrue(any(timeline[0]))
            rendered = render_drcs_visualizer(40, spectrum_frame_at(timeline, 0.25), [1.0] * 40)
            self.assertIn("\033( @", rendered)
            self.assertIn("\r\n", rendered)
            download = define_all_player_drcs()
            self.assertEqual(1, download.count("\033P"))
            self.assertEqual(375, len(VISUALIZER_MODE_NAMES))
            self.assertEqual(25, len(VISUALIZER_TYPE_NAMES))
            self.assertEqual(15, len(VISUALIZER_TREATMENT_NAMES))
            self.assertEqual(32, len(COLOR_STYLE_NAMES))
            self.assertEqual(21, len(KARAOKE_STYLE_NAMES))
            self.assertEqual(7, len(KARAOKE_TREATMENT_NAMES))
            self.assertEqual(25, len(PROGRESS_STYLE_NAMES))
            self.assertNotEqual(
                visualizer_mode_heights(bytes(range(40)), 40, 1),
                visualizer_mode_heights(bytes(range(40)), 40, 30),
            )

    def test_karaoke_styles_and_color_treatments_are_independent(self) -> None:
        self.assertNotIn("🎵", _legacy_karaoke_text("ABEI", 46))
        self.assertNotIn("✨", _legacy_karaoke_text("ABEI", 46))
        self.assertEqual("normal", stylize_karaoke_text("normal", 1))
        self.assertIn("💞", stylize_karaoke_with_emojimax("love", 1, True))
        self.assertNotIn("❤️", stylize_karaoke_with_emojimax("love", 1, False))
        self.assertTrue(stylize_karaoke_text("ABC", 17))
        self.assertIn("\033[38;2;", colorize_karaoke_text("one two", 5))
        self.assertNotIn("\033[0m", colorize_karaoke_text("one two", 5))
        self.assertNotIn("\033[48;2;", colorize_karaoke_text("one two", 5))
        self.assertNotEqual(
            colorize_karaoke_text("one two", 5, brightness=1.0),
            colorize_karaoke_text("one two", 5, brightness=0.4),
        )
        self.assertEqual(hashed_word_rgb("can't"), hashed_word_rgb("cant"))
        wide = "A🅰⭕❤️B"
        self.assertGreater(terminal_cell_width(wide), len(wide))
        self.assertEqual(12, terminal_cell_width(center_to_cells(wide, 12)))
        self.assertLessEqual(terminal_cell_width(truncate_to_cells(wide * 3, 10, "…")), 10)
        self.assertTrue(all(terminal_cell_width(line) <= 8 for line in wrap_to_cells(wide * 3, 8)))
        clipped_ansi = truncate_ansi_to_cells(BIG_OFF + "\033[2m" + wide * 5, 9)
        visible_ansi = ANSI_CSI_RE.sub("", clipped_ansi)
        self.assertLessEqual(terminal_cell_width(visible_ansi), 9)

    def test_lyric_neighbors_fade_and_scroll_by_normal_rows(self) -> None:
        entries = [
            (0.0, None, "previous"),
            (10.0, None, "current"),
            (20.0, None, "next"),
        ]
        previous_at_start, next_at_start = lyric_neighbor_opacities(entries, 1, 10.0)
        previous_later, next_later = lyric_neighbor_opacities(entries, 1, 16.0)
        _previous_at_end, next_at_end = lyric_neighbor_opacities(entries, 1, 19.75)
        self.assertAlmostEqual(LYRIC_NEIGHBOR_MAX_BRIGHTNESS, previous_at_start)
        self.assertEqual(0.0, next_at_start)
        self.assertLess(previous_later, previous_at_start)
        self.assertGreater(next_later, next_at_start)
        self.assertAlmostEqual(LYRIC_NEIGHBOR_MAX_BRIGHTNESS, next_at_end)
        self.assertEqual((2, 4, 6), lyric_scroll_rows(0.0))
        self.assertEqual((1, 3, 5), lyric_scroll_rows(LYRIC_SCROLL_STEP_SECONDS))
        self.assertIsNone(lyric_scroll_rows(LYRIC_SCROLL_STEP_SECONDS * 2))

    def test_seek_restarts_ffplay_at_requested_offsets(self) -> None:
        class FakeProcess:
            def __init__(self) -> None:
                self.running = True
                self.terminated = False

            def poll(self):
                return None if self.running else 0

            def terminate(self) -> None:
                self.terminated = True
                self.running = False

            def wait(self, timeout=None) -> int:
                self.running = False
                return 0

            def kill(self) -> None:
                self.running = False

        processes: list[FakeProcess] = []
        commands: list[list[str]] = []

        def factory(command, **_kwargs):
            commands.append(command)
            process = FakeProcess()
            processes.append(process)
            return process

        actions = iter(
            (SEEK_FORWARD_5, SEEK_FORWARD_15, STOP)
        )
        clock = iter((100.0,) * 20)
        with tempfile.TemporaryDirectory() as temp:
            audio = Path(temp) / "fixture.flac"
            audio.write_bytes(b"generated audio fixture")
            with contextlib.redirect_stdout(io.StringIO()):
                result = play_audio_file(
                    audio,
                    ffplay=Path("ffplay.exe"),
                    duration_probe=lambda _path: 60.0,
                    key_action_reader=lambda: next(actions),
                    process_factory=factory,
                    monotonic=lambda: next(clock),
                    sleeper=lambda _seconds: None,
                    install_signal_handlers=False,
                )
        self.assertEqual("stopped", result)
        self.assertEqual(3, len(commands))
        self.assertEqual("0.000", commands[0][commands[0].index("-ss") + 1])
        self.assertEqual("5.000", commands[1][commands[1].index("-ss") + 1])
        self.assertEqual("20.000", commands[2][commands[2].index("-ss") + 1])
        self.assertTrue(all(command[command.index("-volume") + 1] == "100" for command in commands))
        self.assertTrue(all(command[command.index("-ar") + 1] == "192000" for command in commands))
        self.assertTrue(all(process.terminated for process in processes))
        boosted = ffplay_command(Path("ffplay.exe"), audio, 0, 400, 1.0)
        self.assertIn("volume=4", boosted)
        self.assertEqual("100", boosted[boosted.index("-volume") + 1])
        expanded_51 = ffplay_command(Path("ffplay.exe"), audio, 0, 100, 1.0, 5)
        expanded_71 = ffplay_command(Path("ffplay.exe"), audio, 0, 100, 1.0, 7)
        self.assertIn("pan=5.1(side)", expanded_51[expanded_51.index("-af") + 1])
        self.assertIn("pan=7.1", expanded_71[expanded_71.index("-af") + 1])
        self.assertIn("SL=1.4*FL-1.4*FR", expanded_51[expanded_51.index("-af") + 1])
        self.assertIn("SL=1.4*FL-1.4*FR", expanded_71[expanded_71.index("-af") + 1])
        self.assertIn("lowpass=f=66:c=LFE", expanded_51[expanded_51.index("-af") + 1])
        self.assertIn("alimiter=limit=0.95", expanded_71[expanded_71.index("-af") + 1])

    def test_v12_lyric_title_owns_title_through_short_gap_only(self) -> None:
        lyrics = [
            (0.0, 2.0, "first line"),
            (4.0, 5.0, "second line"),
            (10.0, 11.0, "third line"),
        ]
        self.assertEqual("first line", lyric_title_text_at(lyrics, 2.5))
        self.assertEqual("second line", lyric_title_text_at(lyrics, 4.5))
        self.assertIsNone(lyric_title_text_at(lyrics, 5.1))
        self.assertEqual("third line", lyric_title_text_at(lyrics, 10.2))

    def test_v12_emojimax_current_line_never_reverts_during_fade(self) -> None:
        self.assertEqual("pirate", stylize_karaoke_with_emojimax("pirate", 1, True, 0.20))
        self.assertEqual(
            "🏴‍☠️",
            stylize_karaoke_with_emojimax(
                "pirate", 1, True, 0.20, force_emoji_when_enabled=True
            ),
        )
        self.assertEqual("🏴‍☠️", semantic["pirate"])

    def test_v12_playlist_previous_walks_real_visit_history(self) -> None:
        history = [Path(letter) for letter in "ABCDE"]
        cursor = 4
        queue_neighbor = lambda direction: Path("Z")
        observed = []
        for _ in range(4):
            track, cursor = advance_playlist_visit_history(
                history, cursor, PREVIOUS_FILE, queue_neighbor
            )
            observed.append(track.name)
        self.assertEqual(["D", "C", "B", "A"], observed)
        self.assertEqual([Path(letter) for letter in "ABCDE"], history)

    def test_v12_artist_throb_is_independent_and_faster(self) -> None:
        self.assertGreater(SONG_RAINBOW_THROB_SECONDS, ARTIST_RAINBOW_THROB_SECONDS)
        self.assertAlmostEqual(
            SONG_RAINBOW_THROB_SECONDS / 1.33,
            ARTIST_RAINBOW_THROB_SECONDS,
            places=6,
        )
        self.assertAlmostEqual(
            SONG_RAINBOW_THROB_SECONDS / 2.0,
            SHUFFLE_RAINBOW_THROB_SECONDS,
            places=6,
        )

    @unittest.skipUnless(shutil.which("ffplay"), "FFplay is required")
    def test_one_second_silence_completes_with_drcs_and_looping_off(self) -> None:
        """Catch visualizer startup deadlocks without producing audible sound."""
        with tempfile.TemporaryDirectory() as temp:
            audio = Path(temp) / "one-second-silence.wav"
            with wave.open(str(audio), "wb") as output:
                output.setnchannels(1)
                output.setsampwidth(2)
                output.setframerate(8000)
                output.writeframes(b"\0\0" * 8000)
            audio.with_suffix(".lrc").write_text(
                "[00:00.00]previous love\n[00:00.20]current fire\n[00:00.60]next star\n",
                encoding="utf-8",
            )
            result: list[str] = []
            failure: list[BaseException] = []

            def run_player() -> None:
                try:
                    with contextlib.redirect_stdout(io.StringIO()):
                        result.append(play_audio_file(
                            audio,
                            ffplay=Path(shutil.which("ffplay") or "ffplay"),
                            key_action_reader=lambda: None,
                            install_signal_handlers=False,
                            sixel_visualizer=False,
                            drcs_visualizer=True,
                            looping=False,
                            lyrics_display=True,
                            manage_winamp=False,
                        ))
                except BaseException as exc:
                    failure.append(exc)

            worker = threading.Thread(target=run_player, daemon=True)
            worker.start()
            worker.join(timeout=5.0)
            self.assertFalse(worker.is_alive(), "silent playback exceeded five seconds")
            if failure:
                raise failure[0]
            self.assertEqual(["completed"], result)


def run_unit_tests() -> int:
    """Run this script's embedded tests with normal unittest reporting."""
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        PlayWaveFileTests
    )
    return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1


def run_emoji_display_test() -> int:
    """Print numbered semantic substitutions so broken glyphs are easy to report."""
    print("\033[96mEmoji / Unicode substitution display test:\033[0m")
    print("\033[2;90mTell me the numbers that render wrong and I will swap those glyphs.\033[0m")
    rows: list[tuple[str, str, str]] = []
    for word, replacement in sorted(semantic.items()):
        rows.append(("word", word, replacement))
    for phrase, replacement in sorted(SEMANTIC_PHRASES.items()):
        rows.append(("phrase", phrase, replacement))
    label_width = max(10, min(28, max(len(label) for _kind, label, _replacement in rows)))
    for index, (kind, label, replacement) in enumerate(rows, start=1):
        codepoints = " ".join(f"U+{ord(character):04X}" for character in replacement)
        print(
            f"\033[38;2;120;225;155m#{index:04d}\033[0m "
            f"\033[2;90m{kind:<6}\033[0m "
            f"\033[38;2;145;205;255m{label:<{label_width}}\033[0m "
            f"\033[38;2;255;215;120m{replacement}\033[0m  "
            f"\033[2;90mcells={terminal_cell_width(replacement):>2} {codepoints}\033[0m"
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run unit tests or preview the single supplied audio filename."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments in (["--version"], ["--which-script"]):
        print(f"play_audio_file build {PLAYER_BUILD_ID}")
        print(Path(__file__).resolve())
        return 0
    if arguments in (["--unit-tests"], ["-t"]):
        return run_unit_tests()
    if arguments in (["--emoji-display-test"], ["-e"]):
        return run_emoji_display_test()
    if not arguments or any(option in arguments for option in ("--help", "--usage", "-h", "-u")):
        # Reset any lingering DEC double-height mode before clearing stale UI.
        print(BIG_OFF + "\033[J", end="")
        def usage_line(
            syntax: str,
            explanation: str = "",
            default: str = "",
            note: str = "",
        ) -> None:
            default_text = f"default: {default}" if default else ""
            print(
                f"  \033[38;2;145;205;255m{syntax:<68}\033[0m"
                f"\033[38;2;210;165;255m{explanation:<38}\033[0m"
                f"\033[38;2;120;225;155m{default_text:<13}\033[0m"
                + (f" \033[38;2;105;95;85m({note})\033[0m" if note else "")
            )

        def usage_banner(emoji: str, title: str) -> None:
            banner = f"{emoji}  {title}"
            print()
            print("\033#3\033[1;96m" + banner + "\033[0m")
            print("\033#4\033[1;96m" + banner + "\033[0m")
            print(BIG_OFF, end="")

        usage_banner("🎧", "USAGE")
        print("play_audio_file.py [options] <audio-file>")
        usage_banner("▶️", "PLAYBACK OPTIONS")
        usage_line("-u, --usage", "show this usage")
        usage_line("--version / --which-script", "show build ID and exact script path")
        usage_line("-t, --unit-tests", "run embedded tests")
        usage_line("-e, --emoji-display-test", "test emojimaxxifying of text")
        usage_line("-l, --loop / -L, --no-loop", "loop the current track", "on")
        usage_line("-k, --karaoke / -K, --no-karaoke", "display available lyrics", "on")
        usage_line("-r, --random-file [directory]", "random file in one folder")
        usage_line("-R, --random-file-recursive [directory]", "random downward folder walk")
        usage_line("-p, --playlist FILE", "playlist; shuffled initially", "shuffle")
        usage_line("--shuffle-expiration-in-hours=HOURS", "reuse the internally shuffled playlist until this age", f"{SHUFFLE_EXPIRATION_IN_HOURS:g}h", "if older, build a new historical shuffle")
        usage_line("--marqee-animation-if-longer-than=20", "animate window-title marquee above this length", str(MARQUEE_ANIMATION_IF_LONGER_THAN))
        usage_banner("🌈", "COLOR / THROB ANIMATION")
        usage_line("--song-throb-seconds=SECONDS", "Song brightness-throb period", f"{SONG_RAINBOW_THROB_SECONDS:.2f}s")
        usage_line("--artist-throb-seconds=SECONDS", "Artist brightness-throb period", f"{ARTIST_RAINBOW_THROB_SECONDS:.2f}s")
        usage_line("--shuffle-throb-seconds=SECONDS", "[shuffling …] brightness-throb period", f"{SHUFFLE_RAINBOW_THROB_SECONDS:.2f}s")
        usage_line("--genre-emoji / --no-genre-emoji", "show a genre-specific emoji beside Genre", "on")
        usage_line("-b, --initial-blank-line / -B, --suppress-initial-blank-line", "leading blank line", "on")
        usage_line("-ghfl, --generate-play-history-from-lastfm-logs", "parse Last.fm logs and write play history CSV")
        usage_line("-dh, --display-play-history", "display the generated play‑history CSV")
        usage_banner("📊", "VISUALIZER OPTIONS")
        usage_line("-v, --visualizers / -V, --no-visualizers", "enable/disable both")
        usage_line(
            "-s, --sixel-visualizer / -S, --no-sixel-visualizer",
            "SIXEL spectrum / image visualizer",
            "on" if ENABLE_SIXEL_VISUALIZER else "off",
        )
        usage_line(
            "-d, --drcs-visualizer / -D, --no-drcs-visualizer",
            "DRCS soft-font spectrum",
            "on" if ENABLE_DRCS_VISUALIZER else "off",
            "🚩 experimental: doesn't work for the developer, but might work for you",
        )
        usage_line("-f, --fade-time SECONDS", "spectrum persistence; 0 disables", f"{DEFAULT_VISUALIZER_FADE_SECONDS:g}s")
        usage_line("--truncate-top-visualizer-lines=N", "drop N rarely-hit top spectrum bands without blank rows", str(TRUNCATE_TOP_VISUALIZER_LINES))
        usage_line("Ctrl+Alt+F8", "toggle artwork-composited spectrum in the main visualizer area (🎨)", "off")
        usage_line("Ctrl+Alt+F9", "toggle visualizer expansion into blank karaoke rows; marker only when disabled", "on")
        usage_line("Shift+F10", "experimental karaoke-over-visualizer overlay", "off")
        usage_line("-a, --album-art / -A, --no-album-art", "SIXEL artwork background", "on")
        usage_banner("📡", "NOW-PLAYING FILES")
        usage_line("-n, --no-now-playing", "suppress all TXT/DAT + JPG output")
        usage_line(
            "-N, --no-now-playing-sidecar",
            "suppress the default now-playing target",
            note=r"uses C:\mp3\lists\winamp_now_playing.txt/.jpg when C:\mp3\lists exists; otherwise script-side play_audio_file-now_playing.dat/.jpg",
        )
        usage_line("-o, --now-playing PATH", "also write data at PATH and art at PATH with .jpg suffix")
        usage_banner("🧩", "REQUIRED / OPTIONAL LIBRARIES")
        print("  \033[38;2;145;205;255mclairecjs_utils / claire_progressbar\033[0m"
              "  \033[38;2;210;165;255mC:\\clairecjs_utils or an importable Python site-packages/site-lib location\033[0m")
        print("  \033[38;2;145;205;255mPython package: wcwidth (optional)\033[0m"
              "              \033[38;2;210;165;255mUnicode terminal-cell measurement\033[0m")
        print("\n\033[2;90mV toggles the DRCS visualizer;"
              " W toggles the SIXEL visualizer.\033[0m")
        print("\033[2;90m?: show full keys; F2/F3: karaoke style; Shift+F2/F3: treatment; F4: emojimax.\033[0m")
        print("\033[2;90mHold F2+F3 3s: style Megamix; add Shift 3s/6s: treatment Megamix1/Megamix2.\033[0m")
        print("\033[2;90mF1: all defaults; Alt+F1: undo reset; F5/Ctrl+L/Ctrl+R: redraw.\033[0m")
        print("\033[2;90mCtrl+Alt+F8: artwork-composited visualizer; Ctrl+Alt+F9: toggle default blank-karaoke expansion; Shift+F10: overlay.\033[0m")
        print("\033[2;90mURL fields use OSC 8 hyperlinks in compatible terminals (Windows Terminal: usually Ctrl+click); Ctrl+G opens URL tag / unique Comment URLs; Ctrl+Alt+L: force Last.fm scrobble.\033[0m")
        print("\033[2;90mCtrl-V: visualizer; F6/F7: visualizer modes; Shift-F6/F7: interpretations; C/Shift+C: colors; F: favorite menu; Shift+F/Alt+F: fades.\033[0m")
        print("\033[2;90mP/Shift+P: progress style; A: autoplay (enables shuffle).\033[0m")
        print("\033[2;90m2: stereo; 5: 5.1 expansion; 7: 7.1 expansion.\033[0m")
        usage_banner("🧪", "EXAMPLES")
        print(r"  play_audio_file.py --artist-throb-seconds=2.4 --song-throb-seconds=3.2 C:\mp3\song.mp3")
        print(r"  play_audio_file.py --shuffle-throb-seconds=1.6 --playlist C:\mp3\lists\favorites.m3u")
        print(r"  play_audio_file.py --shuffle-expiration-in-hours=5 --playlist C:\mp3\lists\favorites.m3u")
        print(r"  play_audio_file.py --no-genre-emoji --marqee-animation-if-longer-than=20 C:\mp3\song.mp3")
        print(r"  play_audio_file.py --truncate-top-visualizer-lines=1 C:\mp3\song.mp3")
        return 0
    persisted_settings = load_player_settings()
    sixel_enabled = bool(persisted_settings['SixelEnabled'])
    drcs_enabled = bool(persisted_settings['DrcsEnabled'])
    fade_seconds = DEFAULT_VISUALIZER_FADE_SECONDS
    looping_enabled = bool(persisted_settings['Looping'])
    loop_option_explicit = False
    lyrics_enabled = True
    random_mode = ""
    playlist_argument: str | None = None
    initial_blank_line = True
    now_playing_enabled = True
    now_playing_sidecar = True
    external_now_playing: Path | None = None
    album_art_display = True
    genre_emoji_enabled = ENABLE_GENRE_EMOJI
    marquee_animation_if_longer_than = MARQUEE_ANIMATION_IF_LONGER_THAN
    song_throb_seconds = SONG_RAINBOW_THROB_SECONDS
    artist_throb_seconds = ARTIST_RAINBOW_THROB_SECONDS
    shuffle_throb_seconds = SHUFFLE_RAINBOW_THROB_SECONDS
    shuffle_expiration_in_hours = SHUFFLE_EXPIRATION_IN_HOURS
    truncate_top_visualizer_lines = TRUNCATE_TOP_VISUALIZER_LINES
    filenames: list[str] = []
    argument_index = 0
    while argument_index < len(arguments):
        generate_history = False
        display_history = False
        argument = arguments[argument_index]
        if argument in {"--visualizers", "-v"}:
            drcs_enabled = True
            sixel_enabled = True
        elif argument in {"--no-visualizers", "-V"}:
            drcs_enabled = False
            sixel_enabled = False
        elif argument in {"--sixel-visualizer", "-s"}:
            sixel_enabled = True
        elif argument in {"--no-sixel-visualizer", "-S"}:
            sixel_enabled = False
        elif argument in {"--drcs-visualizer", "-d"}:
            drcs_enabled = True
        elif argument in {"--no-drcs-visualizer", "-D"}:
            drcs_enabled = False
        elif argument in {"--loop", "-l"}:
            looping_enabled = True
            loop_option_explicit = True
        elif argument in {"--no-loop", "-L"}:
            looping_enabled = False
            loop_option_explicit = True
        elif argument in {"--karaoke", "-k"}:
            lyrics_enabled = True
        elif argument in {"--no-karaoke", "-K"}:
            lyrics_enabled = False
        elif argument in {"--random-file", "-r"}:
            random_mode = "single"
        elif argument in {"--random-file-recursive", "-R"}:
            random_mode = "recursive"
        elif argument in {"--playlist", "-p"}:
            argument_index += 1
            if argument_index >= len(arguments):
                print("💥 ERROR: --playlist requires a playlist filename.", file=sys.stderr)
                return 2
            playlist_argument = arguments[argument_index]
        elif argument == "--shuffle-expiration-in-hours":
            argument_index += 1
            if argument_index >= len(arguments):
                print("💥 ERROR: --shuffle-expiration-in-hours requires a number of hours.", file=sys.stderr)
                return 2
            try:
                shuffle_expiration_in_hours = float(arguments[argument_index])
            except ValueError:
                print("💥 ERROR: --shuffle-expiration-in-hours must be a number.", file=sys.stderr)
                return 2
        elif argument.startswith("--shuffle-expiration-in-hours="):
            try:
                shuffle_expiration_in_hours = float(argument.partition("=")[2])
            except ValueError:
                print("💥 ERROR: --shuffle-expiration-in-hours must be a number.", file=sys.stderr)
                return 2
        elif argument in {"--initial-blank-line", "-b"}:
            initial_blank_line = True
        elif argument in {"--suppress-initial-blank-line", "-B"}:
            initial_blank_line = False
        elif argument in {"--no-now-playing", "-n"}:
            now_playing_enabled = False
        elif argument in {"--no-now-playing-sidecar", "-N"}:
            now_playing_sidecar = False
        elif argument in {"--album-art", "-a"}:
            album_art_display = True
        elif argument in {"--no-album-art", "-A"}:
            album_art_display = False
        elif argument == "--genre-emoji":
            genre_emoji_enabled = True
        elif argument == "--no-genre-emoji":
            genre_emoji_enabled = False
        elif argument in {"--now-playing", "-o"}:
            argument_index += 1
            if argument_index >= len(arguments):
                print("ERROR: --now-playing requires a DAT pathname.", file=sys.stderr)
                return 2
            external_now_playing = Path(arguments[argument_index]).absolute()
        elif argument in {"--marqee-animation-if-longer-than", "--marquee-animation-if-longer-than"}:
            argument_index += 1
            if argument_index >= len(arguments):
                print("💥 ERROR: --marqee-animation-if-longer-than requires a character count.", file=sys.stderr)
                return 2
            try:
                marquee_animation_if_longer_than = int(arguments[argument_index])
            except ValueError:
                print("💥 ERROR: --marqee-animation-if-longer-than must be an integer.", file=sys.stderr)
                return 2
        elif argument.startswith("--marqee-animation-if-longer-than=") or argument.startswith("--marquee-animation-if-longer-than="):
            try:
                marquee_animation_if_longer_than = int(argument.partition("=")[2])
            except ValueError:
                print("💥 ERROR: --marqee-animation-if-longer-than must be an integer.", file=sys.stderr)
                return 2
        elif argument == "--truncate-top-visualizer-lines":
            argument_index += 1
            if argument_index >= len(arguments):
                print("💥 ERROR: --truncate-top-visualizer-lines requires an integer.", file=sys.stderr)
                return 2
            try:
                truncate_top_visualizer_lines = int(arguments[argument_index])
            except ValueError:
                print("💥 ERROR: --truncate-top-visualizer-lines must be an integer.", file=sys.stderr)
                return 2
        elif argument.startswith("--truncate-top-visualizer-lines="):
            try:
                truncate_top_visualizer_lines = int(argument.partition("=")[2])
            except ValueError:
                print("💥 ERROR: --truncate-top-visualizer-lines must be an integer.", file=sys.stderr)
                return 2
        elif argument in {"--song-throb-seconds", "--artist-throb-seconds", "--shuffle-throb-seconds"}:
            option_name = argument
            argument_index += 1
            if argument_index >= len(arguments):
                print(f"💥 ERROR: {option_name} requires a number of seconds.", file=sys.stderr)
                return 2
            try:
                value = float(arguments[argument_index])
            except ValueError:
                print(f"💥 ERROR: {option_name} must be a number.", file=sys.stderr)
                return 2
            if option_name == "--song-throb-seconds":
                song_throb_seconds = value
            elif option_name == "--artist-throb-seconds":
                artist_throb_seconds = value
            else:
                shuffle_throb_seconds = value
        elif any(argument.startswith(prefix + "=") for prefix in (
            "--song-throb-seconds", "--artist-throb-seconds", "--shuffle-throb-seconds"
        )):
            option_name, _equals, raw_value = argument.partition("=")
            try:
                value = float(raw_value)
            except ValueError:
                print(f"💥 ERROR: {option_name} must be a number.", file=sys.stderr)
                return 2
            if option_name == "--song-throb-seconds":
                song_throb_seconds = value
            elif option_name == "--artist-throb-seconds":
                artist_throb_seconds = value
            else:
                shuffle_throb_seconds = value
        elif argument in {"--fade-time", "-f"}:
            argument_index += 1
            if argument_index >= len(arguments):
                print("💥 ERROR: --fade-time requires a number of seconds.", file=sys.stderr)
                return 2
            try:
                fade_seconds = float(arguments[argument_index])
            except ValueError:
                print("💥 ERROR: --fade-time must be a number.", file=sys.stderr)
                return 2
        elif argument.startswith("--fade-time="):
            try:
                fade_seconds = float(argument.partition("=")[2])
            except ValueError:
                print("💥 ERROR: --fade-time must be a number.", file=sys.stderr)
                return 2
        elif argument in {"--generate-play-history-from-lastfm-logs", "-ghfl"}:
            generate_history = True
            # Early‑exit: generate CSV and exit
            csv_path = Path(__file__).resolve().with_name('lastfm_play_history.csv')
            try:
                generate_lastfm_play_history(csv_path)
                print(f"✅ Play history written to {csv_path}")
                sys.exit(0)
            except Exception as exc:
                print(f"❌ Failed to generate play history: {exc}", file=sys.stderr)
                sys.exit(1)
            sys.exit(0)
        elif argument in {"--display-play-history", "-dh"}:
            # Early-exit: display CSV and exit.
            try:
                display_lastfm_play_history()
            except Exception as exc:
                print(f"❌ Failed to display play history: {exc}", file=sys.stderr)
                return 1
            return 0
        elif argument.startswith("-"):
            print(f"💥 ERROR: Unknown option: {argument}", file=sys.stderr)
            return 2
        else:
            filenames.append(argument)
        argument_index += 1
    if not math.isfinite(fade_seconds) or fade_seconds < 0:
        print("💥 ERROR: --fade-time must be zero or greater.", file=sys.stderr)
        return 2
    if marquee_animation_if_longer_than < 0:
        print("💥 ERROR: --marqee-animation-if-longer-than must be zero or greater.", file=sys.stderr)
        return 2
    if truncate_top_visualizer_lines < 0:
        print("💥 ERROR: --truncate-top-visualizer-lines must be zero or greater.", file=sys.stderr)
        return 2
    if not math.isfinite(shuffle_expiration_in_hours) or shuffle_expiration_in_hours < 0:
        print("💥 ERROR: --shuffle-expiration-in-hours must be zero or greater.", file=sys.stderr)
        return 2
    for option_name, value in (
        ("--song-throb-seconds", song_throb_seconds),
        ("--artist-throb-seconds", artist_throb_seconds),
        ("--shuffle-throb-seconds", shuffle_throb_seconds),
    ):
        if not math.isfinite(value) or value <= 0:
            print(f"💥 ERROR: {option_name} must be greater than zero.", file=sys.stderr)
            return 2
    playlist_suffixes = {".m3u", ".m3u8", ".pls", ".xspf"}
    if playlist_argument is None and len(filenames) == 1 and Path(filenames[0]).suffix.casefold() in playlist_suffixes:
        playlist_argument = filenames.pop()
    if random_mode and playlist_argument is not None:
        print("💥 ERROR: Random-file and playlist modes cannot be combined.", file=sys.stderr)
        return 2
    if playlist_argument is not None and filenames:
        print("💥 ERROR: Playlist mode does not accept an additional audio filename.", file=sys.stderr)
        return 2
    if random_mode and len(filenames) > 1:
        print("💥 ERROR: Random-file mode accepts at most one directory.", file=sys.stderr)
        return 2
    # Handle Last.fm history generation / display before playback starts
    if generate_history:
        csv_path = Path(__file__).resolve().with_name('lastfm_play_history.csv')
        try:
            generate_lastfm_play_history(csv_path)
            print(f"✅ Play history written to {csv_path}")
        except Exception as exc:
            print(f"❌ Failed to generate play history: {exc}", file=sys.stderr)
            return 1
        return 0
    if display_history:
        try:
            display_lastfm_play_history()
        except Exception as exc:
            print(f"❌ Failed to display play history: {exc}", file=sys.stderr)
            return 1
        return 0

    maybe_prompt_for_lastfm_setup()
    winamp_paused_by_session = False
    try:
        now_playing_targets: list[Path] = []
        if now_playing_enabled:
            if now_playing_sidecar:
                now_playing_targets.append(default_now_playing_data_target())
            if external_now_playing is not None:
                now_playing_targets.append(external_now_playing)
        playlist_entries: list[Path] | None = None
        playlist_shuffle_order: list[Path] | None = None
        playlist_ready_event: threading.Event | None = None
        playlist_background_error: list[BaseException | None] = [None]
        playlist_background_status_state: list[str | None] | None = None
        shuffle_state: list[bool] | None = None
        playlist_navigation_history: list[Path] = []
        playlist_navigation_cursor = -1
        visualizer_mode_state = [persisted_settings['VisualizerMode']]
        color_style_state = [persisted_settings['ColorStyle']]
        karaoke_style_state = [persisted_settings['KaraokeStyle']]
        karaoke_treatment_state = [persisted_settings['KaraokeTreatment']]
        karaoke_emojimax_state = [bool(persisted_settings['KaraokeEmojimax'])]
        progress_style_state = [persisted_settings['ProgressStyle']]
        autoplay_state = [bool(persisted_settings['Autoplay'])]
        output_channels_state = [persisted_settings['OutputChannels']]
        balance_state = [persisted_settings['Balance']]
        volume_state = [persisted_settings['Volume']]
        speed_index_state = [persisted_settings['SpeedIndex']]
        looping_state = [looping_enabled]
        drcs_enabled_state = [drcs_enabled]
        sixel_enabled_state = [sixel_enabled]
        album_art_visualizer_state = [False]
        karaoke_visualizer_expansion_state = [DEFAULT_KARAOKE_VISUALIZER_EXPANSION]
        playlist_path: Path | None = None
        initial_resume_position = 0.0
        playback_position_state = [0.0]
        autoplay_seen: dict[Path, set[Path]] = {}
        pending_folder_line: Path | None = None

        if playlist_argument is not None:
            playlist_path = Path(playlist_argument).absolute().resolve()
            shuffle_state = [True]
            playlist_background_status_state = ["reading playlist"]
            saved_resume = load_playlist_resume(playlist_path)
            resumed_entry = None
            if saved_resume is not None:
                saved_track, saved_position = saved_resume
                resumed_entry = find_track_in_playlist_fast(playlist_path, saved_track)
                if resumed_entry is not None:
                    initial_resume_position = saved_position
            if resumed_entry is not None:
                current_audio = resumed_entry
                write_console(
                    f"\033[38;2;120;210;190m↩ Resuming playlist: {current_audio.name} "
                    f"at {format_position(initial_resume_position)}\033[0m\n"
                )
            else:
                initial_resume_position = 0.0
                current_audio = quick_random_playlist_track(playlist_path)

            playlist_ready_event = threading.Event()
            initial_playlist_track = current_audio.resolve()

            def prepare_playlist_in_background() -> None:
                nonlocal playlist_entries, playlist_shuffle_order
                assert playlist_path is not None
                assert playlist_background_status_state is not None
                assert playlist_ready_event is not None
                try:
                    cached = load_playlist_shuffle_cache(
                        playlist_path, shuffle_expiration_in_hours
                    )
                    if cached is not None:
                        playlist_entries, cached_order = cached
                        playlist_shuffle_order = list(cached_order)
                        # A fresh completed cache means there is nothing to
                        # reshuffle or query; do not flash fake progress text.
                        playlist_background_status_state[0] = None
                    else:
                        playlist_entries = load_playlist(playlist_path, show_progress=False)

                        def shuffle_progress(label: str) -> None:
                            playlist_background_status_state[0] = label

                        playlist_shuffle_order = build_playlist_shuffle_order_progressive(
                            playlist_entries, shuffle_progress
                        )
                        save_playlist_shuffle_cache(
                            playlist_path, playlist_entries, playlist_shuffle_order
                        )
                    # The already-playing starter must be the head of the
                    # per-invocation queue, but that starter-specific rewrite
                    # is NOT saved into the persistent cache.
                    starter = next(
                        (entry for entry in playlist_entries if entry.resolve() == initial_playlist_track),
                        None,
                    )
                    if starter is not None:
                        playlist_shuffle_order = [starter] + [
                            entry for entry in playlist_shuffle_order if entry.resolve() != initial_playlist_track
                        ]
                    playlist_ready_event.set()
                    if cached is None:
                        # Let the completion message be visible briefly, then
                        # clear the shared marker so it cannot become permanent
                        # scrollback/status text.
                        playlist_background_status_state[0] = "historical shuffling done"
                        time.sleep(2.0)
                        playlist_background_status_state[0] = None
                except BaseException as exc:
                    playlist_background_error[0] = exc
                    playlist_background_status_state[0] = "playlist shuffle failed"
                finally:
                    playlist_ready_event.set()

            threading.Thread(
                target=prepare_playlist_in_background,
                name="playlist-loader-shuffler",
                daemon=True,
            ).start()
            if not loop_option_explicit:
                looping_enabled = False
        elif random_mode:
            selection_root = Path(filenames[0]) if filenames else Path.cwd()
            current_audio = (
                random_audio_file_recursive(selection_root)
                if random_mode == "recursive" else random_audio_file(selection_root)
            )
        else:
            current_audio = Path(filenames[0])
        if playlist_argument is None and not loop_option_explicit:
            # Single files (including random-file mode) loop by default.
            looping_enabled = True
        # Keep the UI/persisted state in sync with the actual startup policy.
        looping_state[0] = looping_enabled
        if playlist_path is not None:
            playlist_navigation_history = [current_audio]
            playlist_navigation_cursor = 0

        if shuffle_state is None:
            shuffle_state = [False]
        while True:
            playback_position_state[0] = initial_resume_position
            scroll_console_viewport_to_output()
            if pending_folder_line is not None:
                # Visually bind the upcoming cover to its folder/history block.
                separator_width = max(12, shutil.get_terminal_size((120, 30)).columns - 1)
                write_console(
                    "\033[2;90m" + "\u2500" * separator_width + "\033[0m\n"
                )
            preplay_cover = b""
            if album_art_display:
                preplay_cover = render_preplay_album_cover(
                    current_audio, max(12, shutil.get_terminal_size((120, 30)).columns - 1)
                )
                if preplay_cover:
                    # SIXEL-capable terminals differ on whether drawing the
                    # image advances the text cursor.  Measure the Windows
                    # console cursor and add a newline ONLY when the image did
                    # not already move us below itself; this removes the extra
                    # artwork→Playing blank row without risking text overdraw.
                    before_art_row = console_cursor_row()
                    write_console_bytes(preplay_cover.rstrip(b"\r\n"))
                    after_art_row = console_cursor_row()
                    if before_art_row is None or after_art_row is None or after_art_row <= before_art_row:
                        write_console("\n")
                    else:
                        write_console("\r")
            if pending_folder_line is not None:
                available = max(12, shutil.get_terminal_size((120, 30)).columns - 1)
                cached_duration = probe_duration_seconds(current_audio)
                full_playing = (
                    f"🔊 Playing: {current_audio} ({format_duration_label(cached_duration)})"
                )
                # If the complete path fits, play_audio_file puts it directly
                # on the Playing line; the separate Folder line would be redundant.
                if terminal_cell_width(full_playing) > available:
                    write_console(
                        "\033[?25l" + ansi_rgb(PLAYING_PATH_RGB) + "\U0001f4c1" + "  Folder:\033[0m "
                        + ansi_rgb(PLAYING_PATH_RGB) + f"{pending_folder_line}\033[0m\n"
                    )
                pending_folder_line = None
            for now_playing_target in now_playing_targets:
                write_now_playing_art(current_audio, now_playing_target)
            if not winamp_paused_by_session:
                winamp_paused_by_session = pause_playing_winamp()
            result = play_audio_file(
                current_audio,
                sixel_visualizer=sixel_enabled,
                drcs_visualizer=drcs_enabled,
                visualizer_fade_seconds=fade_seconds,
                looping=looping_enabled and not autoplay_state[0],
                looping_state=looping_state,
                lyrics_display=lyrics_enabled,
                shuffle_state=shuffle_state,
                visualizer_mode_state=visualizer_mode_state,
                color_style_state=color_style_state,
                karaoke_style_state=karaoke_style_state,
                karaoke_treatment_state=karaoke_treatment_state,
                karaoke_emojimax_state=karaoke_emojimax_state,
                progress_style_state=progress_style_state,
                autoplay_state=autoplay_state,
                output_channels_state=output_channels_state,
                balance_state=balance_state,
                volume_state=volume_state,
                speed_index_state=speed_index_state,
                drcs_enabled_state=drcs_enabled_state,
                sixel_enabled_state=sixel_enabled_state,
                album_art_visualizer_state=album_art_visualizer_state,
                karaoke_visualizer_expansion_state=karaoke_visualizer_expansion_state,
                now_playing_targets=now_playing_targets,
                album_art_display=album_art_display,
                genre_emoji_enabled=genre_emoji_enabled,
                marquee_animation_if_longer_than=marquee_animation_if_longer_than,
                song_throb_seconds=song_throb_seconds,
                artist_throb_seconds=artist_throb_seconds,
                shuffle_throb_seconds=shuffle_throb_seconds,
                truncate_top_visualizer_lines=truncate_top_visualizer_lines,
                background_status_state=playlist_background_status_state,
                initial_position=initial_resume_position,
                playback_position_state=playback_position_state,
                initial_blank_line=initial_blank_line and not bool(preplay_cover),
                manage_winamp=False,
                guard_winamp=True,
            )
            persisted_settings.update({
                'VisualizerMode': visualizer_mode_state[0],
                'ColorStyle': color_style_state[0],
                'KaraokeStyle': karaoke_style_state[0],
                'KaraokeTreatment': karaoke_treatment_state[0],
                'KaraokeEmojimax': int(karaoke_emojimax_state[0]),
                'ProgressStyle': progress_style_state[0],
                'OutputChannels': output_channels_state[0],
                'Balance': balance_state[0],
                'Volume': volume_state[0],
                'SpeedIndex': speed_index_state[0],
                'Looping': int(looping_state[0]),
                'Shuffle': int(shuffle_state[0]),
                'Autoplay': int(autoplay_state[0]),
                'DrcsEnabled': int(drcs_enabled_state[0]),
                'SixelEnabled': int(sixel_enabled_state[0]),
            })
            save_player_settings(persisted_settings)
            initial_resume_position = 0.0
            initial_blank_line = False
            if playlist_path is not None:
                playlist_history_mark_played(current_audio)
                if result == "stopped":
                    save_playlist_resume(
                        playlist_path, current_audio, playback_position_state[0]
                    )
                    break
                # The first song is deliberately allowed to start before the
                # playlist/history pass completes. We only need the final queue
                # at the moment we advance away from that starter.
                if playlist_ready_event is not None:
                    playlist_ready_event.wait()
                if playlist_background_error[0] is not None:
                    raise RuntimeError(
                        f"Could not finish playlist preparation: {playlist_background_error[0]}"
                    ) from playlist_background_error[0]
                if not playlist_entries:
                    raise ValueError(f"Playlist contains no usable local audio files: {playlist_path}")
                # The background progress occupies the old [logged] marker for
                # the first song only; subsequent tracks return to scrobble status.
                playlist_background_status_state = None
                previous_directory = current_audio.parent.resolve()

                def queue_neighbor(direction: int) -> Path:
                    """Return the adjacent track in the prepared playlist order."""
                    nonlocal playlist_shuffle_order
                    order = playlist_shuffle_order if shuffle_state and shuffle_state[0] else playlist_entries
                    if not order:
                        order = list(playlist_entries)
                    if shuffle_state and shuffle_state[0] and not playlist_shuffle_order:
                        playlist_shuffle_order = list(order)
                        random.shuffle(playlist_shuffle_order)
                        order = playlist_shuffle_order
                    try:
                        index = next(
                            i for i, entry in enumerate(order)
                            if entry.resolve() == current_audio.resolve()
                        )
                    except (StopIteration, OSError):
                        return order[0]
                    return order[(index + direction) % len(order)]

                current_audio, playlist_navigation_cursor = advance_playlist_visit_history(
                    playlist_navigation_history,
                    playlist_navigation_cursor,
                    result,
                    queue_neighbor,
                )

                if current_audio.parent.resolve() != previous_directory:
                    pending_folder_line = current_audio.parent
                continue
            if result == "completed" and autoplay_state[0]:
                current_directory = current_audio.parent.resolve()
                seen = autoplay_seen.setdefault(current_directory, set())
                seen.add(current_audio.resolve())
                remaining = [
                    path for path in audio_files_in(current_directory)
                    if path.resolve() not in seen
                ]
                previous_directory = current_directory
                if remaining:
                    current_audio = random.choice(remaining)
                else:
                    current_audio = navigate_audio_path(current_audio, NEXT_DIRECTORY)
                    autoplay_seen.setdefault(current_audio.parent.resolve(), set())
                if current_audio.parent.resolve() != previous_directory:
                    pending_folder_line = current_audio.parent
                continue
            if result not in NAVIGATION_ACTIONS:
                break
            previous_directory = current_audio.parent.resolve()
            current_audio = navigate_audio_path(current_audio, result)
            if current_audio.parent.resolve() != previous_directory:
                pending_folder_line = current_audio.parent
    except KeyboardInterrupt:
        print("\n⏹️ Playback stopped.")
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        resume_winamp_if_paused_by_preview(winamp_paused_by_session)
        write_console("\033[?25h")
    return 0


# Helper functions for Last.fm play‑history generation and display

def generate_lastfm_play_history(csv_path: Path) -> None:
    """
    Parse Last.fm/Audioscrobbler logs and write a CSV file with columns:
    start,end,artist,title,album,duration_seconds.

    Claire's archived Last.fm Desktop Scrobbler diagnostic logs live under
    C:\\logs\\last.fm. In those logs completed plays appear in QMap(...)
    Track.scrobble records. They occur both as single records and as indexed
    batches (track[0], artist[0], timestamp[0], etc.) when queued scrobbles are
    submitted. Both forms are parsed here.

    Older custom pipe-delimited and Audioscrobbler TSV records are retained as
    fallbacks. Multiple/overlapping log snapshots are combined and deduplicated.

    Interactive terminals get a three-line in-place display: total byte
    progress, current-file byte progress, and a live unique-play counter.
    """

    local_appdata = Path(
        os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")
    )

    log_roots = [
        Path(r"C:\logs\last.fm"),
        local_appdata / "Last.fm",
        local_appdata / "Last.fm" / "logs",
        local_appdata / "Last.fm" / "logs" / "last.fm",
    ]
    explicit_files = [
        local_appdata / "Last.fm" / "Last.fm Scrobbler.log",
        Path.home() / ".clairecjs_utils" / "lastfm_scrobbles.log",
    ]

    log_files: list[Path] = []
    seen_paths: set[str] = set()

    def add_file(path: Path) -> None:
        try:
            resolved_key = str(path.resolve()).casefold()
        except OSError:
            resolved_key = str(path.absolute()).casefold()
        if resolved_key not in seen_paths and path.is_file():
            seen_paths.add(resolved_key)
            log_files.append(path)

    # C:\logs\last.fm is deliberately searched first. Its archived files are
    # cumulative/overlapping snapshots, so deduplication below is essential.
    for root in log_roots:
        if root.is_file():
            add_file(root)
            continue
        if not root.is_dir():
            continue
        try:
            for path in sorted(root.rglob("*"), key=natural_path_key):
                if not path.is_file():
                    continue
                name = path.name.casefold()
                if (
                    path.suffix.casefold() in {".log", ".txt"}
                    or "scrobbl" in name
                    or "last.fm" in name
                    or "lastfm" in name
                ):
                    add_file(path)
        except OSError:
            pass

    for path in explicit_files:
        add_file(path)

    if not log_files:
        searched = "\n".join(f"  {path}" for path in [*log_roots, *explicit_files])
        raise FileNotFoundError(
            "No Last.fm log files were found. Searched:\n" + searched
        )

    def parse_unix_timestamp(value: str) -> datetime:
        raw = float(value.strip())
        if raw > 10_000_000_000:  # tolerate milliseconds too
            raw /= 1000.0
        return datetime.fromtimestamp(raw, tz=timezone.utc)

    def decode_log_line(data: bytes) -> str:
        """Decode a single modern UTF-8 or old Windows-1252 log line."""
        try:
            return data.decode("utf-8-sig")
        except UnicodeDecodeError:
            # Last.fm Scrobbler 2.1.33 writes CP1252 bytes on this machine.
            return data.decode("cp1252", errors="replace")

    # Qt's QMap debug output is a run of tuples such as:
    #   ("album", "...")("artist", "...")...
    # Values can contain literal quotes (e.g. 12" Mix), so a quote only ends a
    # value when followed by the QMap tuple boundary.
    qmap_pair_re = re.compile(
        r'\("([^"\\]+)", "(.*?)"\)(?=\(|\)|\s*$)'
    )


    # Current Last.fm Scrobbler logs expose the local basename in two places.
    # We correlate that evidence to the eventual Track.scrobble in memory, but
    # never persist a directory, extension, or numeric track prefix.
    fingerprint_filename_re = re.compile(r"filename=(.*?)&fileextension=", re.IGNORECASE)
    fingerprint_time_re = re.compile(r"[?&]time=(\d+)", re.IGNORECASE)

    def parse_fingerprint_filename(line: str) -> tuple[int, str] | None:
        if "fingerprint/query/" not in line.casefold() or "filename=" not in line.casefold():
            return None
        filename_match = fingerprint_filename_re.search(line)
        time_match = fingerprint_time_re.search(line)
        if filename_match is None or time_match is None:
            return None
        filename_key = playlist_history_filename_key(filename_match.group(1))
        if not filename_key:
            return None
        try:
            return int(time_match.group(1)), filename_key
        except ValueError:
            return None

    def parse_start_filename(line: str) -> tuple[tuple[int, str], str] | None:
        if 'PlayerCommandParser::PlayerCommandParser() "START ' not in line:
            return None
        artist_match = re.search(r"&a=(.*?)&d=", line)
        title_match = re.search(r"&t=(.*?)&b=", line)
        duration_match = re.search(r"&l=(\d+)&p=", line)
        path_match = re.search(r'&p=(.*)"\s*$', line)
        if not all((artist_match, title_match, duration_match, path_match)):
            return None
        filename_key = playlist_history_filename_key(path_match.group(1))
        if not filename_key:
            return None
        try:
            duration = int(duration_match.group(1))
        except ValueError:
            return None
        tag = playlist_history_tag_key({
            "Artist": artist_match.group(1),
            "Song": title_match.group(1),
        })
        if duration <= 0 or not tag or tag == "\x1f":
            return None
        return (duration, tag), filename_key

    def build_record(fields: dict[str, str], suffix: str = ""):
        artist = fields.get(f"artist{suffix}", "").strip()
        title = fields.get(f"track{suffix}", "").strip()
        album = fields.get(f"album{suffix}", "").strip()
        timestamp_value = fields.get(f"timestamp{suffix}", "").strip()
        duration_value = fields.get(f"duration{suffix}", "").strip()
        if not artist or not title or not timestamp_value:
            return None
        try:
            start_dt = parse_unix_timestamp(timestamp_value)
            duration = max(0, int(round(float(duration_value or 0))))
        except (ValueError, OverflowError, OSError):
            return None
        return start_dt, artist, title, album, duration

    def parse_qmap_scrobbles(line: str):
        """Return all Track.scrobble records from one QMap log line."""
        if "QMap(" not in line or "scrobble" not in line.casefold():
            return None

        fields = {key: value for key, value in qmap_pair_re.findall(line)}
        if fields.get("method", "").casefold() != "track.scrobble":
            return None

        # Ordinary one-track submission (used by the current 2026 log too).
        if "timestamp" in fields:
            record = build_record(fields)
            return [] if record is None else [record]

        # Queued/batched submission. Last.fm uses indexed keys, usually in
        # batches of 50, and can omit album[n] when the album is blank.
        indices = sorted(
            int(match.group(1))
            for key in fields
            for match in [re.fullmatch(r"timestamp\[(\d+)\]", key)]
            if match
        )
        records = []
        for index in indices:
            record = build_record(fields, f"[{index}]")
            if record is not None:
                records.append(record)
        return records

    def parse_legacy_line(line: str):
        stripped = line.strip().lstrip("\ufeff")
        if not stripped or stripped.startswith("#"):
            return None

        # Old/custom Claire format:
        # timestamp|artist|track|album|duration_ms
        pipe = stripped.split("|")
        if len(pipe) == 5:
            ts, artist, title, album, duration_value = [part.strip() for part in pipe]
            try:
                start_dt = parse_unix_timestamp(ts)
                duration_raw = float(duration_value)
                duration = int(round(duration_raw / 1000.0))
                if duration < 0:
                    return None
                return start_dt, artist, title, album, duration
            except (ValueError, OverflowError, OSError):
                pass

        # Audioscrobbler 1.0/1.1 format:
        # artist, album, title, track-number, duration-seconds, rating, unix-time
        tab = stripped.split("\t")
        if len(tab) >= 7:
            artist, album, title = tab[0].strip(), tab[1].strip(), tab[2].strip()
            duration_value, rating, ts = tab[4].strip(), tab[5].strip(), tab[6].strip()
            try:
                start_dt = parse_unix_timestamp(ts)
                duration = max(0, int(round(float(duration_value))))
                if rating and rating.upper() not in {"L", "S"}:
                    return None
                return start_dt, artist, title, album, duration
            except (ValueError, OverflowError, OSError):
                pass

        return None

    def row_key(row: tuple[datetime, str, str, str, int]) -> tuple[str, str, str, str, int]:
        start_dt, artist, title, album, duration = row
        return start_dt.isoformat(), artist, title, album, duration

    def format_bytes(value: int) -> str:
        amount = float(max(0, value))
        for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
            if amount < 1024.0 or unit == "TiB":
                return f"{amount:.0f} {unit}" if unit == "B" else f"{amount:.1f} {unit}"
            amount /= 1024.0
        return f"{amount:.1f} TiB"

    def make_bar(done: int, total: int, width: int) -> str:
        if total <= 0:
            fraction = 1.0
        else:
            fraction = min(1.0, max(0.0, done / total))
        filled = min(width, max(0, int(round(fraction * width))))
        return "█" * filled + "░" * (width - filled)

    file_sizes: dict[Path, int] = {}
    for path in log_files:
        try:
            file_sizes[path] = path.stat().st_size
        except OSError:
            file_sizes[path] = 0
    total_bytes = sum(file_sizes.values())
    total_bytes_done = 0
    unique_rows_by_key: dict[
        tuple[str, str, str, str, int], tuple[datetime, str, str, str, int]
    ] = {}
    filename_by_row_key: dict[tuple[str, str, str, str, int], str] = {}
    fingerprint_filename_by_timestamp: dict[int, str] = {}
    pending_start_filename_by_identity: dict[tuple[int, str], str] = {}
    parser_version = "QMAP3"
    total_record_count = 0
    total_lines = 0
    qmap_signature_lines = 0
    qmap_scrobble_lines = 0
    qmap_scrobble_records = 0
    malformed_scrobble_lines = 0
    parse_samples: list[tuple[Path, str]] = []

    progress_stream = sys.stderr
    interactive_progress = bool(getattr(progress_stream, "isatty", lambda: False)())
    progress_started = False
    last_progress_time = 0.0
    last_progress_bytes = -1

    def render_progress(
        file_index: int,
        log_path: Path,
        file_bytes_done: int,
        *,
        force: bool = False,
    ) -> None:
        nonlocal progress_started, last_progress_time, last_progress_bytes
        if not interactive_progress:
            return
        now = time.monotonic()
        if not force and total_bytes_done - last_progress_bytes < 65536 and now - last_progress_time < 0.05:
            return
        last_progress_time = now
        last_progress_bytes = total_bytes_done

        columns = max(72, shutil.get_terminal_size((100, 24)).columns)
        # Leave enough room for labels, percentages and byte counters.
        bar_width = max(18, min(52, columns - 48))
        file_total = file_sizes.get(log_path, 0)
        total_pct = 100.0 if total_bytes <= 0 else min(100.0, 100.0 * total_bytes_done / total_bytes)
        file_pct = 100.0 if file_total <= 0 else min(100.0, 100.0 * file_bytes_done / file_total)
        display_name = log_path.name
        max_name = max(12, columns - (bar_width + 32))
        if len(display_name) > max_name:
            display_name = "…" + display_name[-(max_name - 1):]

        lines = [
            f"Total  [{make_bar(total_bytes_done, total_bytes, bar_width)}] "
            f"{total_pct:6.2f}%  {format_bytes(total_bytes_done)}/{format_bytes(total_bytes)}",
            f"File {file_index:>2}/{len(log_files):<2} "
            f"[{make_bar(file_bytes_done, file_total, bar_width)}] {file_pct:6.2f}%  {display_name}",
            f"Plays found: {len(unique_rows_by_key):,}",
        ]

        if progress_started:
            progress_stream.write("\r\033[2A")
        for index, line in enumerate(lines):
            progress_stream.write("\033[2K\r" + line)
            if index < len(lines) - 1:
                progress_stream.write("\n")
        progress_stream.flush()
        progress_started = True

    if interactive_progress:
        render_progress(1, log_files[0], 0, force=True)

    for file_index, log_path in enumerate(log_files, 1):
        file_bytes_done = 0
        fingerprint_filename_by_timestamp.clear()
        pending_start_filename_by_identity.clear()
        try:
            handle = log_path.open("rb")
        except OSError as exc:
            print(f"⚠️ Could not read Last.fm log {log_path}: {exc}", file=sys.stderr)
            total_bytes_done += file_sizes.get(log_path, 0)
            render_progress(file_index, log_path, file_sizes.get(log_path, 0), force=True)
            continue

        with handle:
            for raw_line in handle:
                byte_count = len(raw_line)
                file_bytes_done += byte_count
                total_bytes_done += byte_count
                line = decode_log_line(raw_line).rstrip("\r\n")
                if not line.strip() or line.lstrip().startswith("#"):
                    render_progress(file_index, log_path, file_bytes_done)
                    continue
                total_lines += 1
                if "Track.scrobble" in line and "QMap(" in line:
                    qmap_signature_lines += 1

                fingerprint_info = parse_fingerprint_filename(line)
                if fingerprint_info is not None:
                    fingerprint_timestamp, fingerprint_filename = fingerprint_info
                    fingerprint_filename_by_timestamp[fingerprint_timestamp] = fingerprint_filename

                start_info = parse_start_filename(line)
                if start_info is not None:
                    start_identity, start_filename = start_info
                    pending_start_filename_by_identity[start_identity] = start_filename

                unique_before = len(unique_rows_by_key)
                qmap_records = parse_qmap_scrobbles(line)
                if qmap_records is not None:
                    qmap_scrobble_lines += 1
                    qmap_scrobble_records += len(qmap_records)
                    total_record_count += len(qmap_records)
                    if not qmap_records:
                        malformed_scrobble_lines += 1
                        if len(parse_samples) < 8:
                            parse_samples.append((log_path, line[:500]))
                    else:
                        indexed_batch = "timestamp[" in line
                        for record in qmap_records:
                            key = row_key(record)
                            unique_rows_by_key.setdefault(key, record)
                            start_dt, artist, title, _album, duration = record
                            timestamp_key = int(round(start_dt.timestamp()))
                            filename_key = (
                                fingerprint_filename_by_timestamp.get(timestamp_key, "")
                                or fingerprint_filename_by_timestamp.get(timestamp_key + 1, "")
                                or fingerprint_filename_by_timestamp.get(timestamp_key - 1, "")
                            )
                            if not filename_key and not indexed_batch:
                                tag = playlist_history_tag_key({"Artist": artist, "Song": title})
                                filename_key = pending_start_filename_by_identity.get((duration, tag), "")
                            if filename_key and key not in filename_by_row_key:
                                filename_by_row_key[key] = filename_key
                else:
                    legacy_record = parse_legacy_line(line)
                    if legacy_record is not None:
                        total_record_count += 1
                        unique_rows_by_key.setdefault(row_key(legacy_record), legacy_record)

                # A newly discovered unique play gets an immediate visual update;
                # otherwise rendering is throttled to avoid slowing the scan.
                render_progress(
                    file_index,
                    log_path,
                    file_bytes_done,
                    force=len(unique_rows_by_key) != unique_before,
                )

        # Account for a file whose final bytes were not yielded as lines only in
        # the unlikely event the filesystem size changed while we were reading it.
        expected_size = file_sizes.get(log_path, file_bytes_done)
        if file_bytes_done < expected_size:
            total_bytes_done += expected_size - file_bytes_done
            file_bytes_done = expected_size
        render_progress(file_index, log_path, file_bytes_done, force=True)

    if interactive_progress and progress_started:
        progress_stream.write("\n")
        progress_stream.flush()

    unique_rows = sorted(unique_rows_by_key.values(), key=lambda row: row[0])

    # A regression guard: these diagnostic logs visibly contain QMap
    # Track.scrobble records. Never silently claim success with an empty CSV if
    # a future edit accidentally replaces/breaks the QMap parser again.
    if qmap_signature_lines and qmap_scrobble_records == 0:
        raise RuntimeError(
            f"Last.fm parser {parser_version} saw {qmap_signature_lines:,} "
            "QMap Track.scrobble line(s) but parsed zero records. "
            "Refusing to write an empty history; the QMap parser is broken."
        )

    # Seed the same latest-only SQLite history used by playlist rotation.
    # Filename is a lookup accelerator, but only when the log itself provides
    # trustworthy local-file evidence. We never invent a basename for batched
    # historical scrobbles that lack START/fingerprint context.
    latest_by_identity: dict[tuple[str, int, str], float] = {}
    for row in unique_rows:
        start_dt, artist, title, _album, duration = row
        filename = filename_by_row_key.get(row_key(row), "")
        tag = playlist_history_tag_key({"Artist": artist, "Song": title})
        if not filename or duration <= 0 or not tag or tag == "\x1f":
            continue
        identity = (filename, int(duration), tag)
        played_at = start_dt.timestamp()
        previous = latest_by_identity.get(identity)
        if previous is None or played_at > previous:
            latest_by_identity[identity] = played_at

    if latest_by_identity:
        with playlist_history_connection() as history_db:
            history_db.executemany(
                """INSERT INTO played_tracks_recent(filename, duration_seconds, tag, played_at)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(filename, duration_seconds, tag)
                   DO UPDATE SET played_at=MAX(played_tracks_recent.played_at, excluded.played_at)""",
                [
                    (filename, duration, tag, played_at)
                    for (filename, duration, tag), played_at in latest_by_identity.items()
                ],
            )

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "start", "end", "artist", "title", "album", "duration_seconds",
        ])
        for start_dt, artist, title, album, duration in unique_rows:
            end_dt = start_dt + timedelta(seconds=duration)
            writer.writerow([
                start_dt.isoformat(), end_dt.isoformat(), artist, title, album, duration,
            ])

    duplicate_count = total_record_count - len(unique_rows)
    print(f"🧭 Last.fm history parser: {parser_version}")
    print(
        f"🎧 Last.fm history: {len(unique_rows)} unique plays from "
        f"{len(log_files)} log file(s); {duplicate_count} overlapping duplicate "
        f"record(s) removed."
    )
    print(
        f"   Parsed {qmap_scrobble_records} play record(s) from "
        f"{qmap_scrobble_lines} Track.scrobble QMap line(s); "
        f"{malformed_scrobble_lines} malformed. Scanned {total_lines} nonblank lines "
        f"({format_bytes(total_bytes)})."
    )
    print(
        f"   Indexed {len(latest_by_identity):,} latest filename+duration+tag identities "
        f"in {playlist_history_database_path()}."
    )
    for log_path in log_files:
        print(f"   📄 {log_path}")

    if malformed_scrobble_lines and parse_samples:
        print(
            "⚠️ Some Track.scrobble records could not be parsed. Samples:",
            file=sys.stderr,
        )
        for path, sample in parse_samples:
            print(f"   {path.name}: {sample}", file=sys.stderr)


def clean_report_artist_display(value: str) -> str:
    """Return the report-facing artist name before duplicate grouping.

    Feature credits are intentionally discarded only for this report.  The
    source CSV/history remains untouched.  A tiny alias table also repairs
    known one-off tagging mistakes without changing playback metadata.
    """
    artist = unicodedata.normalize("NFKC", str(value or "")).strip()
    artist = re.sub(r"\s+", " ", artist)
    artist = re.sub(
        r"\s+(?:feat(?:uring)?|ft)\.?\s+.*$",
        "",
        artist,
        flags=re.IGNORECASE,
    ).strip()

    # One known singular typo in the library.
    typo_key = re.sub(r"[\W_]+", "", artist, flags=re.UNICODE).casefold()
    if typo_key == "girlsritual":
        return "Girls Rituals"
    return artist or "(unknown artist)"


def report_artist_group_key(value: str) -> str:
    """Return a forgiving identity key for the play-history artist report.

    Punctuation and spacing do not distinguish artists here.  Ampersands and
    the word ``and`` are equivalent, so e.g. ``Earth Wind & Fire`` and
    ``Earth, Wind And Fire`` collapse into one row.
    """
    artist = clean_report_artist_display(value).casefold()
    artist = artist.replace("&", " and ")
    artist = re.sub(r"\band\b", " and ", artist, flags=re.IGNORECASE)
    return re.sub(r"[\W_]+", "", artist, flags=re.UNICODE) or "unknownartist"


def most_common_report_artist_style(variant_counts: dict[str, int]) -> str:
    """Choose the most frequently occurring cleaned spelling/styling.

    Dict insertion order intentionally breaks exact ties in favor of the first
    spelling encountered in the history file.
    """
    if not variant_counts:
        return "(unknown artist)"
    return max(variant_counts, key=lambda variant: variant_counts[variant])


def display_lastfm_play_history() -> None:
    """Print an alphabetical, terminal-safe per-artist play-history table."""
    csv_path = Path(__file__).resolve().with_name("lastfm_play_history.csv")
    if not csv_path.is_file():
        raise FileNotFoundError(f"Play-history CSV not found at {csv_path}")

    artist_stats: dict[str, dict[str, object]] = {}
    total_songs = 0
    overall_first: datetime | None = None
    overall_last: datetime | None = None

    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"start", "artist"}
        missing = required.difference(reader.fieldnames or ())
        if missing:
            raise ValueError(
                "Play-history CSV is missing required column(s): "
                + ", ".join(sorted(missing))
            )

        for row in reader:
            raw_artist = (row.get("artist") or "").strip() or "(unknown artist)"
            artist = clean_report_artist_display(raw_artist)
            artist_key = report_artist_group_key(raw_artist)
            start_text = (row.get("start") or "").strip()
            if not start_text:
                continue

            try:
                started = datetime.fromisoformat(start_text.replace("Z", "+00:00"))
            except ValueError:
                continue

            stats = artist_stats.setdefault(
                artist_key,
                {"count": 0, "first": started, "last": started, "variants": {}},
            )
            variants = stats["variants"]
            assert isinstance(variants, dict)
            variants[artist] = int(variants.get(artist, 0)) + 1
            stats["count"] = int(stats["count"]) + 1
            if started < stats["first"]:  # type: ignore[operator]
                stats["first"] = started
            if started > stats["last"]:  # type: ignore[operator]
                stats["last"] = started

            total_songs += 1
            if overall_first is None or started < overall_first:
                overall_first = started
            if overall_last is None or started > overall_last:
                overall_last = started

    # Keep the table one cell shy of the terminal's right edge so Windows
    # Terminal never auto-wraps the final border.  Songs and Date range have
    # naturally bounded content, so give them only as much room as they need;
    # the Artist column receives the remaining width.
    terminal_columns = max(20, shutil.get_terminal_size((120, 30)).columns)
    table_budget = max(7, terminal_columns - 1)

    def date_range(first: datetime, last: datetime) -> str:
        first_date = first.date().isoformat()
        last_date = last.date().isoformat()
        return first_date if first_date == last_date else f"{first_date}–{last_date}"

    song_values = ["Songs", str(total_songs)] + [
        str(stats["count"]) for stats in artist_stats.values()
    ]
    date_values = ["Date range", "—"]
    date_values.extend(
        date_range(stats["first"], stats["last"])  # type: ignore[arg-type]
        for stats in artist_stats.values()
    )
    if overall_first is not None and overall_last is not None:
        date_values.append(date_range(overall_first, overall_last))

    songs_width = max(terminal_cell_width(value) for value in song_values)
    date_width = max(terminal_cell_width(value) for value in date_values)

    # Four non-content cells are occupied by ║...║...║...║.  Preserve the two
    # compact columns and let only Artist flex.  On absurdly narrow terminals,
    # Artist bottoms out at one cell rather than forcing the terminal to wrap.
    artist_width = max(1, table_budget - 4 - songs_width - date_width)
    column_widths = (artist_width, songs_width, date_width)

    artist_horizontal = "═" * artist_width
    songs_horizontal = "═" * songs_width
    date_horizontal = "═" * date_width
    top_border = f"╔{artist_horizontal}╦{songs_horizontal}╦{date_horizontal}╗"
    middle_border = f"╠{artist_horizontal}╬{songs_horizontal}╬{date_horizontal}╣"
    bottom_border = f"╚{artist_horizontal}╩{songs_horizontal}╩{date_horizontal}╝"

    def rainbow_gradient(text: str) -> str:
        """Apply a left-to-right truecolor rainbow without changing cell width."""
        if not text:
            return text
        visible_characters = [character for character in text if not character.isspace()]
        denominator = max(1, len(visible_characters) - 1)
        colored: list[str] = []
        visible_index = 0
        for character in text:
            if character.isspace():
                colored.append(character)
                continue
            colored.append(ansi_rgb(rainbow_rgb(visible_index / denominator)))
            colored.append(character)
            visible_index += 1
        colored.append("\033[0m")
        return "".join(colored)

    def centered_styled(plain_text: str, styled_text: str, width: int) -> str:
        """Center styled text according to the unstyled terminal-cell width."""
        remaining = max(0, width - terminal_cell_width(plain_text))
        left = remaining // 2
        right = remaining - left
        return " " * left + styled_text + " " * right

    def render_row(values: tuple[str, str, str], *, rainbow_artist: bool = False) -> None:
        wrapped = [
            wrap_to_cells(value, width)
            for value, width in zip(values, column_widths)
        ]
        row_height = max(len(lines) for lines in wrapped)
        for line_index in range(row_height):
            cells: list[str] = []
            for column_index, (lines, width) in enumerate(zip(wrapped, column_widths)):
                plain_line = lines[line_index] if line_index < len(lines) else ""
                if rainbow_artist and column_index == 0 and plain_line:
                    styled_line = rainbow_gradient(plain_line)
                else:
                    styled_line = plain_line
                cells.append(centered_styled(plain_line, styled_line, width))
            print(f"║{cells[0]}║{cells[1]}║{cells[2]}║")

    header = ("Artist", "Songs", "Date range")

    print(top_border)
    render_row(header)
    print(middle_border)

    resolved_artist_rows = [
        (
            most_common_report_artist_style(stats["variants"]),  # type: ignore[arg-type]
            stats,
        )
        for stats in artist_stats.values()
    ]
    for artist, stats in sorted(resolved_artist_rows, key=lambda item: item[0].casefold()):
        render_row(
            (
                artist,
                str(stats["count"]),
                date_range(stats["first"], stats["last"]),  # type: ignore[arg-type]
            ),
            rainbow_artist=True,
        )

    # Repeat the column labels immediately before the total, with a full
    # double-line separator on both sides so the summary remains unmistakable.
    print(middle_border)
    render_row(header)
    print(middle_border)

    if overall_first is not None and overall_last is not None:
        total_range = date_range(overall_first, overall_last)
    else:
        total_range = "—"
    render_row(("TOTAL", str(total_songs), total_range))
    print(bottom_border)


if __name__ == "__main__":
    raise SystemExit(main())
