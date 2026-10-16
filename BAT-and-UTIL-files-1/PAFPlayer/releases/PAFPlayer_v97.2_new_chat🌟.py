#!/usr/bin/env python3
"""Interactively preview an audio file from a Windows console.

This program uses FFplay and accepts any audio format FFmpeg can decode,
including WAV, FLAC, and MP3.

Playback controls
-----------------
Esc, X, Q, Ctrl+W, Alt+F4, Ctrl+C, or Ctrl+Break
    Stop playback immediately.
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
from pathlib import Path
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
from datetime import datetime, timezone
# Set to 0 when the terminal cannot render DEC SIXEL graphics.
WRITE_NOWPLAYING_THIS_OFTEN     = 5.0
PREVENT_WINAMP_PAUSE_WHEN_WE_ARE_PAUSED = 0
LYRIC_FADE_SECONDS              = 6.0
LYRIC_NEIGHBOR_MAX_BRIGHTNESS   = 0.66
LYRIC_NEXT_FADE_MAX_SECONDS     = 6.0
LYRIC_PREVIOUS_FADE_MAX_SECONDS = 6.0
LYRIC_PREVIEW_LEAD_SECONDS      = 0.25
LYRIC_SCROLL_ROW_STEPS          = 4
LYRIC_SCROLL_STEP_SECONDS       = 0.08
ENABLE_SIXEL_VISUALIZER         = 0
ENABLE_DRCS_VISUALIZER          = 1
DRCS_VISUALIZER_ROWS            = 16
TRIM_TOP_X_VISUALIZER_LINES     = 2
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
REDRAW_UI                       = "redraw-ui"
LASTFM_SCROBBLE_NOW             = "lastfm-scrobble-now"
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
    "milk": "\U0001f95b", "surrender": "\U0001f3f3\ufe0f",
    "red flag": "\U0001f6a9", "redflag": "\U0001f6a9",
    "go": "🟢", "wet": "💧", "umbrella": "☔️", "enterprise": "🏢",
    "life": "🌱", "mind": "🧠", "head": "🗣️", "day": "📆", "end": "🔚",
    "way": "🛣️", "bad": "👎", "good": "👍", "no": "🚫", "right": "👉",
    "left": "👈", "up": "⬆️", "down": "⬇️", "away": "👋", 
    "think": "💭", "know": "💡", "say": "🗣️", "tell": "📣", "make": "🛠️",
    "come": "🫄", "take": "🤲", "die": "💀", "lost": "🧭", "scissor": "✂", "cut": "✂",
    "alone": "🧍", "one": "1️⃣",  "infinite": "♾️", "infinitely": "♾️", "beginning": "🌅",
    "dream": "💭", "hope": "🤞", "sorry": "🙏", "thanks": "🙏", "thank": "🙏",
    "please": "🙏", "friend": "🫂", "friends": "🫂", "run": "🏃", "running": "🏃",
    "walk": "🚶", "walking": "🚶", "dancefloor": "🪩", "street": "🛣️",
    "lake": "🏞️", "sea": "🌊", "mountain": "⛰️", "sky": "🌌",
    "cloud": "☁️", "storm": "⛈️", "wind": "🌬️", "light": "💡", "dark": "🌑",
    "shadow": "👤", "voice": "🗣️", "mail": "📨", "letters": "🔤", "end": "🔚",
    "lie": "🤨", "lies": "🤨",  "cents": "¢", "cent": "¢", "bang": "💥", "!!": "‼"
})
SEMANTIC_PHRASES = {
    "!!!!": "‼‼",
    "beach umbrella": "🏖️", "love": "💞", "my heart": "💗", "no one": "🚫👤",
     "goodbye": "👋", 
    "i'm sorry": "🙏", "thank you": "🙏", "don't know": "🤷", "come on": "👉",
    "so many": "🔢", "too dead": "💀", "lost mind": "🧠", "one more": "➕ 1️⃣",
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


def stylize_karaoke_with_emojimax(text: str, style: int, enabled: bool) -> str:
    """Apply semantic emoji independently of the selected glyph style."""
    if not enabled:
        return stylize_karaoke_text(text, style)
    protected = text
    phrase_tokens: dict[str, str] = {}
    for index, (phrase, replacement) in enumerate(SEMANTIC_PHRASES.items()):
        token = f"\x00{index}\x00"
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


def load_playlist_resume(playlist_path: Path) -> tuple[Path, float] | None:
    """Load this playlist's last explicitly interrupted track and position."""
    if os.name != "nt":
        return None
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\ClaireCJS\play_audio_file") as key:
            raw, _kind = winreg.QueryValueEx(key, playlist_resume_value_name(playlist_path))
        payload = json.loads(str(raw))
        return Path(payload["track"]), max(0.0, float(payload["position"]))
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None


def save_playlist_resume(playlist_path: Path, track: Path, position: float) -> None:
    """Persist a playlist bookmark without storing account or media data."""
    if os.name != "nt":
        return
    import winreg
    payload = json.dumps({"track": str(track.absolute()), "position": max(0.0, position)})
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\ClaireCJS\play_audio_file") as key:
        winreg.SetValueEx(key, playlist_resume_value_name(playlist_path), 0, winreg.REG_SZ, payload)


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


def load_playlist(playlist_path: Path) -> list[Path]:
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
        enabled=bool(getattr(sys.stderr, "isatty", lambda: False)()),
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


def playlist_history_database_path() -> Path:
    """Return the small local SQLite database used for playlist rotation."""
    override = os.environ.get("PLAY_AUDIO_FILE_HISTORY_DB")
    return Path(override) if override else Path(__file__).resolve().with_name("play_audio_file-play-history.sqlite3")


def playlist_history_filename(track: Path) -> str:
    """Create a path identity that remains stable when only its drive changes."""
    path_text = str(track.resolve()).replace("/", "\\")
    _drive, tail = os.path.splitdrive(path_text)
    return tail.lstrip("\\").casefold()


def playlist_history_connection() -> sqlite3.Connection:
    """Open the private local history database and ensure its single table exists."""
    database = sqlite3.connect(playlist_history_database_path())
    database.execute(
        """CREATE TABLE IF NOT EXISTS played_tracks (
            filename TEXT NOT NULL,
            artist TEXT NOT NULL DEFAULT '',
            song TEXT NOT NULL DEFAULT '',
            played_at REAL NOT NULL
        )"""
    )
    database.execute("CREATE INDEX IF NOT EXISTS played_tracks_filename ON played_tracks(filename)")
    database.execute("CREATE INDEX IF NOT EXISTS played_tracks_tags ON played_tracks(artist, song)")
    return database


def playlist_history_mark_played(track: Path) -> None:
    """Append this selected playlist track to the local history."""
    try:
        tags = probe_audio_tags(track)
        artist = tags.get("Artist", "").strip().casefold()
        song = tags.get("Song", "").strip().casefold()
        with playlist_history_connection() as database:
            database.execute(
                "INSERT INTO played_tracks(filename, artist, song, played_at) VALUES (?, ?, ?, ?)",
                (playlist_history_filename(track), artist, song, time.time()),
            )
    except (OSError, sqlite3.Error):
        return


def choose_least_recent_playlist_track(
    entries: list[Path], status_callback=None,
) -> Path:
    """Choose randomly from the 15% played longest ago (or never played)."""
    if not entries:
        raise ValueError("Cannot choose from an empty playlist")
    if status_callback is not None:
        status_callback(True)
    try:
        filename_dates: dict[str, float] = {}
        filenames = [playlist_history_filename(entry) for entry in entries]
        with playlist_history_connection() as database:
            # Indexed filename batches are cheap even for huge history files.
            # Do not synchronously ffprobe every playlist entry here: that made
            # Next Track appear hung on large playlists.
            for offset in range(0, len(filenames), 900):
                batch = filenames[offset:offset + 900]
                placeholders = ", ".join("?" for _ in batch)
                rows = database.execute(
                    f"SELECT filename, MAX(played_at) FROM played_tracks "
                    f"WHERE filename IN ({placeholders}) GROUP BY filename",
                    batch,
                ).fetchall()
                for filename, played_at in rows:
                    filename_dates[str(filename)] = float(played_at)
        scored = [
            (filename_dates.get(playlist_history_filename(entry), 0.0), entry)
            for entry in entries
        ]
        scored.sort(key=lambda item: item[0])
        oldest_count = max(1, math.ceil(len(scored) * 0.15))
        cutoff = scored[oldest_count - 1][0]
        return random.choice([entry for played_at, entry in scored if played_at <= cutoff])
    except sqlite3.Error:
        return random.choice(entries)
    finally:
        if status_callback is not None:
            status_callback(False)


def audio_navigation_root(directory: Path) -> Path:
    """Prefer the surrounding MUSIC/MP3 library; otherwise use the parent."""
    for candidate in (directory, *directory.parents):
        if candidate.name.casefold() in {"music", "mp3"}:
            return candidate
    return directory.parent


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
    """Locate optional FFprobe for duration-aware forward seeking."""
    discovered = shutil.which("ffprobe")
    return Path(discovered) if discovered else None


def probe_duration_seconds(
    audio_path: Path,
    *,
    executable: Path | None = None,
) -> float | None:
    """Return the decoded duration, or ``None`` when it cannot be measured."""
    ffprobe = executable or ffprobe_executable()
    if ffprobe is None:
        return None
    result = subprocess.run(
        [
            str(ffprobe),
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    try:
        duration = float(result.stdout.strip())
    except (TypeError, ValueError):
        return None
    return duration if math.isfinite(duration) and duration > 0 else None


def probe_audio_tags(audio_path: Path) -> dict[str, str]:
    """Read common display tags from the container and first tagged stream."""
    ffprobe = ffprobe_executable()
    if ffprobe is None:
        return {}
    result = subprocess.run(
        [
            str(ffprobe), "-v", "error", "-show_entries",
            "format_tags:stream_tags", "-of", "json", str(audio_path),
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
        return {}
    merged: dict[str, str] = {}
    sources = [payload.get("format", {}).get("tags", {})]
    sources.extend(stream.get("tags", {}) for stream in payload.get("streams", []))
    for source in sources:
        for key, value in source.items():
            folded = str(key).casefold()
            if folded not in merged and str(value).strip():
                merged[folded] = str(value).strip()
    year = merged.get("year", "") or merged.get("date", "")[:4]
    return {
        "Artist": merged.get("artist", "") or merged.get("album_artist", ""),
        "Song": merged.get("title", ""),
        "Album": merged.get("album", ""),
        "Year": year,
        "Genre": merged.get("genre", ""),
        "Comment": merged.get("comment", "") or merged.get("description", ""),
    }


def load_lyrics(audio_path: Path) -> list[tuple[float, float | None, str]]:
    """Load timed LRC/SRT sidecars, or embedded/plain lyrics as a fallback."""
    candidates = [audio_path.with_suffix(suffix) for suffix in (".lrc", ".LRC", ".srt", ".SRT")]
    sidecar = next((path for path in candidates if path.is_file()), None)
    if sidecar is not None:
        text = sidecar.read_text(encoding="utf-8-sig", errors="replace")
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
# The settled bands are rows 0/1, 2/3, and 4/5. During the brief
    # transition they glide upward a normal terminal row at a time.
    return -step, 2 - step, 4 - step




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


ANSI_CSI_RE = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|#[0-9]|[()][ -~])")


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
    return "".join(result) + "\033[0m\033[K"


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


def format_tag_panel(tags: dict[str, str]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return a roomy, aligned metadata panel without truncating song titles."""
    width = max(80, shutil.get_terminal_size((120, 30)).columns - 1)
    left_start, song_start, right_start = 3, max(44, width // 2), max(78, round(width * .72))
    label_width = 7

    def field(label: str, value: str, *, italic: bool = False, vibrant: bool = False) -> tuple[str, str]:
        plain = f"{label.rjust(label_width)}: {value}"
        color = "\033[5;38;2;35;220;195m" if vibrant and label == "Song" else "\033[38;2;35;220;195m" if vibrant else "\033[3;38;2;175;195;215m" if italic else "\033[38;2;175;195;215m"
        ansi = f"\033[2;90m{label.rjust(label_width)}:\033[0m {color}{value}\033[0m"
        return plain, ansi

    artist, song, album = (str(tags.get(key, '') or '') for key in ('Artist', 'Song', 'Album'))
    year, genre, comment = (str(tags.get(key, '') or '') for key in ('Year', 'Genre', 'Comment'))
    song_lines = wrap_to_cells(song, max(16, width - song_start)) if song else []
    rows_plain: list[str] = []
    rows_ansi: list[str] = []
    first_song = song_lines[0] if song_lines else ''
    p, a = field('Artist', artist, vibrant=True)
    p = ' ' * left_start + p
    a = ' ' * left_start + a
    if first_song:
        sp, sa = field('Song', first_song, vibrant=True)
        p += ' ' * max(1, song_start - len(p)) + sp
        a += ' ' * max(1, song_start - terminal_cell_width(p[:song_start])) + sa
    rows_plain.append(p); rows_ansi.append(a)
    if album or len(song_lines) > 1 or year:
        p, a = field('Album', album)
        p = ' ' * left_start + p; a = ' ' * left_start + a
        if len(song_lines) > 1:
            sp, sa = field('Song', song_lines[1], vibrant=True)
            p += ' ' * max(1, song_start - len(p)) + sp
            a += ' ' * max(1, song_start - terminal_cell_width(p[:song_start])) + sa
        if year:
            yp, ya = field('Year', year)
            p += ' ' * max(0, right_start - len(p)) + yp
            a += ' ' * max(0, right_start - terminal_cell_width(p[:right_start])) + ya
        rows_plain.append(p); rows_ansi.append(a)
    for continuation in song_lines[2:]:
        p, a = field('Song', continuation, vibrant=True)
        rows_plain.append(' ' * song_start + p)
        rows_ansi.append(' ' * song_start + a)
    if genre or comment:
        p, a = field('Comment', comment)
        p = ' ' * left_start + p; a = ' ' * left_start + a
        if genre:
            gp, ga = field('Genre', genre)
            p += ' ' * max(0, right_start - len(p)) + gp
            a += ' ' * max(0, right_start - terminal_cell_width(p[:right_start])) + ga
        rows_plain.append(p); rows_ansi.append(a)
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
    if first in {"\x1b", "\x03", "\x17"}:
        return STOP
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
        return FADE_PREVIOUS if shift else FADE_NEXT
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
) -> str:
    """Render an eight-row spectrum driven by analyzed audio frequencies."""
    width = max(12, columns)
    heights = visualizer_mode_heights(spectrum_levels, width, mode)

    lines: list[str] = []
    rows = max(1, rows)
    # Preserve the configured 16-row canvas, but omit its rarely-used top
    # rendered band so the visible spectrum starts one line higher.
    for row in range(min(rows, TRIM_TOP_X_VISUALIZER_LINES), rows):
        threshold = 1 - (row + 1) / rows
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
                base_color = visualizer_color(color_style, row, column, width, rows)
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
    filled = round(bar_width * fraction)
    pairs = (
        ("█", "░"), ("▓", "·"), ("■", "□"), ("━", "─"), ("▰", "▱"),
        ("●", "○"), ("◆", "◇"), ("▮", "▯"), ("▉", "▏"), ("#", "."),
        ("=", "-"), ("▇", "▁"), ("▆", "▂"), ("▣", "▢"), ("█", " "),
        (">", " "), ("*", "."), ("+", "."), ("X", "x"), ("|", "."),
        ("■", "·"), ("▰", "▱"), ("▸", "▹"), ("●", "·"), ("◆", "·"),
    )
    filled_char, empty_char = pairs[(progress_style - 1) % len(pairs)]
    bar = filled_char * filled + empty_char * (bar_width - filled)
    bar_color = rainbow_rgb(fraction)
    if progress_style in {15, 25}:
        throb = 0.35 + 0.65 * max(0.0, min(1.0, pulse_energy))
        bar_color = tuple(round(component * throb) for component in bar_color)
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
        + ansi_rgb(bar_color) + f"{bar} {percentage}%\033[0m"
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


def _album_art_candidates(audio_path: Path) -> list[Path]:
    """Return conventional sidecar cover-art names in preference order."""
    stem = audio_path.with_suffix("")
    candidates = [
        audio_path.with_name(f"{audio_path.stem}{suffix}")
        for suffix in (".jpg", ".jpeg", ".png", ".webp")
    ]
    for name in ("cover", "folder", "front", "album", "artwork"):
        candidates.extend(audio_path.parent / f"{name}{suffix}" for suffix in (".jpg", ".jpeg", ".png", ".webp"))
    return [path for path in candidates if path != audio_path and path.is_file()]


def extract_album_art(audio_path: Path) -> bytes | None:
    """Extract embedded cover art once, falling back to nearby image files."""
    try:
        stat = audio_path.stat()
        cache_key = (str(audio_path.resolve()), stat.st_mtime_ns, stat.st_size)
    except OSError:
        cache_key = (str(audio_path), 0, 0)
    if cache_key in _ALBUM_ART_BYTES_CACHE:
        return _ALBUM_ART_BYTES_CACHE[cache_key]

    art: bytes | None = None
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
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
        for candidate in _album_art_candidates(audio_path):
            try:
                art = candidate.read_bytes()
                if art:
                    break
            except OSError:
                continue
    _ALBUM_ART_BYTES_CACHE[cache_key] = art
    return art


def extract_album_art_variants(audio_path: Path, limit: int = 4) -> list[bytes]:
    """Return up to four distinct embedded/sidecar art panels for preview."""
    variants: list[bytes] = []
    primary = extract_album_art(audio_path)
    if primary:
        variants.append(primary)
    names = (
        "back", "cd", "cassette", "vinyl", "inlay", "inlay1", "inside",
        "booklet", "other",
    )
    for name in names:
        for suffix in (".jpg", ".jpeg", ".png", ".webp"):
            candidate = audio_path.parent / f"{name}{suffix}"
            if not candidate.is_file():
                continue
            try:
                data = candidate.read_bytes()
            except OSError:
                continue
            if data and data not in variants:
                variants.append(data)
                break
        if len(variants) >= limit:
            break
    return variants[:limit]


def write_now_playing_art(audio_path: Path, data_target: Path) -> None:
    '''Write the current cover beside one now-playing data target as JPEG.'''
    art = extract_album_art(audio_path)
    if not art:
        return
    jpg_target = data_target.with_suffix('.jpg')
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
        f'comment={comment}', 'end_comment=1', 'subtitle=', 'end_subtitle=1',
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
    """Render up to four high-resolution aspect-preserving covers as one strip."""
    chafa = shutil.which("chafa")
    variants = extract_album_art_variants(audio_path, 4)
    if not chafa or not variants:
        return b""

    terminal = shutil.get_terminal_size((120, 30))
    preview_rows = max(14, min(26, terminal.lines // 2))
    try:
        from clairecjs_utils.claire_terminal_geometry import query_terminal_geometry
        geometry = query_terminal_geometry()
        cell_width, cell_height = geometry.cell_width, geometry.cell_height
    except Exception:
        # Matches Claire's normal Windows Terminal font ratio when the shared
        # geometry library is unavailable to the running interpreter.
        cell_width, cell_height = 10, 20

    # Chafa's SIXEL view units need the same pixel-derived geometry as Claire's
    # established command, not character counts. The old code used a 12-20px
    # canvas and then enlarged it, which destroyed the artwork's detail.
    display_columns = max(16, min(columns // 2, columns - 2))
    view_width = max(80, math.ceil(display_columns * cell_width / 4))
    view_height = max(56, math.ceil(preview_rows * cell_height / 4))
    # Keep ample source detail; Chafa --size below enforces the actual terminal
    # cell cap, independent of its pixel-graphics scaling behavior.
    source_width = max(view_width * 2, display_columns * cell_width)
    source_height = max(view_height * 2, preview_rows * cell_height)

    try:
        from PIL import Image  # type: ignore
        decoded: list[Image.Image] = []
        for data in variants:
            try:
                with Image.open(io.BytesIO(data)) as image:
                    decoded.append(image.convert("RGB").copy())
            except (OSError, ValueError):
                continue
        if not decoded:
            return b""
        gaps = max(0, len(decoded) - 1) * 8
        usable_width = max(1, source_width - gaps)
        panel_widths = [
            max(1, round(source_height * image.width / max(1, image.height)))
            for image in decoded
        ]
        total_panel_width = sum(panel_widths)
        if total_panel_width > usable_width:
            scale = usable_width / total_panel_width
            panel_widths = [max(1, round(width * scale)) for width in panel_widths]
        canvas_width = min(source_width, sum(panel_widths) + gaps)
        canvas = Image.new("RGB", (canvas_width, source_height), (0, 0, 0))
        x = 0
        for image, panel_width in zip(decoded, panel_widths):
            panel = image.resize((panel_width, source_height), Image.Resampling.LANCZOS)
            canvas.paste(panel, (x, 0))
            x += panel_width + 8
        payload = io.BytesIO()
        canvas.save(payload, format="PNG", optimize=False)
        art = payload.getvalue()
    except (ImportError, OSError, ValueError):
        art = variants[0]

    try:
        return subprocess.run(
            [chafa, "--format=sixels", "--colors=full", "--scale=max",
             f"--size={display_columns}x{preview_rows}",
             f"--font-ratio={cell_width}/{cell_height}",
             "--optimize=9", "--work=9", "--color-space=din99d", "-"],
            input=art, check=False, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            timeout=5,
        ).stdout.rstrip(b"\r\n")
    except (OSError, subprocess.TimeoutExpired):
        return b""
def render_sixel_visualizer(
    audio_path: Path, start_seconds: float, columns: int,
    album_art_background: bool = True,
) -> bytes:
    """Return one FFmpeg spectrum frame encoded as a DEC SIXEL image.

    The renderer is intentionally best-effort: an unsupported terminal simply
    receives no visualizer while normal audio controls continue working.
    """
    ffmpeg = shutil.which("ffmpeg")
    chafa = shutil.which("chafa")
    if not ffmpeg or not chafa:
        return b""
    chafa_geometry = getattr(render_sixel_visualizer, "_geometry", None)
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
                1, math.ceil(SIXEL_VISUALIZER_ROWS * geometry.cell_height / 8)
            )
            chafa_geometry = [
                f"--view-size={view_width}x{view_height}",
                f"--font-ratio={geometry.cell_width}/{geometry.cell_height}",
            ]
        except Exception:
            chafa_geometry = [
                f"--view-size={max(1, columns)}x{SIXEL_VISUALIZER_ROWS * 2}",
                "--font-ratio=8/16",
            ]
        render_sixel_visualizer._geometry = chafa_geometry
    pixels_wide = max(96, columns * 8)
    pixels_high = SIXEL_VISUALIZER_ROWS * 20
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
    now_playing_targets: list[Path] | None = None,
    album_art_display: bool = True,
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
    previous_console_title = get_console_title()
    title_artist = audio_tags.get('Artist', '')
    title_song = audio_tags.get('Song', '') or audio_path.stem
    title_identity = ' – '.join(value for value in (title_artist, title_song) if value)
    title_identity = title_identity or audio_path.name
    last_title_refresh = -10.0

    def refresh_console_title(now: float, paused: bool = False) -> None:
        nonlocal last_title_refresh
        if now - last_title_refresh < 0.25:
            return
        state = 'Paused' if paused else 'Playing'
        marquee = title_identity
        if len(marquee) > 54:
            ring = marquee + '   •   '
            offset = int(now * 4) % len(ring)
            marquee = (ring + ring)[offset:offset + 54]
        set_console_title(f'{state}: {marquee} — play_audio_file [{os.getpid()}]')
        last_title_refresh = now
    tag_plain_rows, tag_ansi_rows = format_tag_panel(audio_tags)
    lyrics = load_lyrics(audio_path) if lyrics_display else []
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
    last_sixel_refresh = -10.0
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
        min(DRCS_VISUALIZER_ROWS, max(0, terminal_lines - fixed_rows - 1))
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
            min(DRCS_VISUALIZER_ROWS, max(0, lines - fixed - 1))
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

    def render_static_header() -> None:
        """Render fixed rows without permitting implicit terminal wrapping."""
        available = max(12, shutil.get_terminal_size((120, 30)).columns - 1)
        header = (
            "\033[32m\U0001f50a\033[4GPlaying:\033[0m "
            f"\033[34;3m{audio_path.name}\033[0m ({format_duration_label(duration)})"
        )
        output = [move_to(HEADER_ROW) + truncate_ansi_to_cells(header, available)]
        for index, row in enumerate(tag_ansi_rows):
            output.append(move_to(1 + index) + truncate_ansi_to_cells(BIG_OFF + row, available))
        for index, text in enumerate(help_texts[:3]):
            output.append(
                move_to(HELP_ROW + index)
                + truncate_ansi_to_cells(f"{BIG_OFF}\033[2;90m{text}", available)
            )
        write_console("".join(output) + "\033[?25l")

    def render_help_overlay() -> None:
        """Temporarily replace metadata and upper display rows with the key map."""
        available = max(12, shutil.get_terminal_size((120, 30)).columns - 1)
        lines = (
            "Stop Esc/X/Q/Ctrl+W/Ctrl+C; pause Space/media/Pause; seek ←/→ 5s, Shift 15s, Ctrl 1m",
            "Tracks </>; folders {/}; media prev/next rewind/forward 10s; volume ↑/↓; balance numpad 4/6, 5=center",
            "Karaoke F2/F3 style; Shift+F2/F3 treatment; hold both 3s=style Megamix; Shift+both 3s/6s=Megamix1/2",
            "F4 emojimax; Ctrl-V visualizer; F6/F7 modes; Shift+F6/F7 treatments",
            "C/Shift+C colors; F/Shift+F fades; P progress; +/- speed; 2/5/7 output; L loop; R random; A autoplay",
            "F1 defaults; Alt+F1 undo reset; F5/Ctrl+L/Ctrl+R redraw; ? toggles this help",
            "Shift+F10: experimental karaoke-over-visualizer overlay",
        )
        rendered: list[str] = []
        for line in lines:
            rendered.extend(wrap_to_cells(line, available))
        overlay_rows = min(UI_ROWS, max(1, len(rendered)))
        clear_region(HEADER_ROW, overlay_rows)
        write_console("".join(
            move_to(HEADER_ROW + index) + BIG_OFF + "\033[2;38;2;125;135;145m"
            + truncate_to_cells(line, available) + "\033[0m\033[K"
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
            write_console(
                move_to(DRCS_ROW)
                + render_drcs_visualizer(
                    bar_width, levels, drcs_recent_energy, visualizer_mode, color_style,
                    drcs_rows,
                    fade_style,
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
        active_lyric = lyric_at(lyrics, current_position)
        if active_lyric is None:
            if last_lyric_index is not None:
                clear_region(LYRIC_ROW, LYRIC_ROWS)
                last_lyric_index = None
                lyric_transition_index = None
        else:
            lyric_index, lyric_text, opacity = active_lyric
            painted_lyric_rows: set[int] = set()
            readable = ((255, 220, 120), (150, 235, 255), (210, 180, 255), (170, 255, 185))
            line_capacity = max(10, max(20, bar_width) // 2)
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
                centered = center_to_cells(text, line_capacity)
                colored = colorize_karaoke_text(
                    centered, karaoke_treatment, seed, brightness
                )
                attributes = foreground_for(seed, brightness)
                if current:
                    attributes = "\033[48;2;0;22;26m" + attributes
                write_console(
                    move_to(LYRIC_ROW + row) + "\033#3" + attributes + colored + "\033[0m\033[K"
                    + move_to(LYRIC_ROW + row + 1) + "\033#4" + attributes + colored + "\033[0m\033[K"
                )

            def render_normal_line(
                row: int,
                text: str,
                seed: int,
                brightness: float,
                *,
                current: bool = False,
            ) -> None:
                if not 0 <= row < LYRIC_ROWS or brightness <= 0.001:
                    return
                painted_lyric_rows.add(row)
                styled = stylize_karaoke_with_emojimax(
                    text, karaoke_style, karaoke_emojimax
                )
                fitted = truncate_to_cells(styled, line_capacity, "…")
                centered = center_to_cells(fitted, line_capacity)
                colored = colorize_karaoke_text(
                    centered, karaoke_treatment, seed, brightness
                )
                attributes = foreground_for(seed, brightness)
                if current:
                    attributes = "\033[48;2;0;22;26m" + attributes
                write_console(
                    move_to(LYRIC_ROW + row) + BIG_OFF + attributes
                    + colored + "\033[0m\033[K"
                )

            def render_neighbor(
                row: int,
                entry: tuple[int, str],
                brightness: float,
            ) -> None:
                seed, text = entry
                if brightness <= 0.001:
                    return
                styled = compensate_double_height_cells(
                    stylize_karaoke_with_emojimax(text, karaoke_style, karaoke_emojimax)
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
                render_normal_line(row + 1, text, seed, brightness)

            def render_scrolling_line(
                row: int,
                text: str,
                seed: int,
                brightness: float,
                *,
                current: bool = False,
            ) -> None:
                if not 0 <= row or row + 1 >= LYRIC_ROWS or brightness <= 0.001:
                    return
                styled = compensate_double_height_cells(
                    stylize_karaoke_with_emojimax(text, karaoke_style, karaoke_emojimax)
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
                    )
            else:
                if previous_entry:
                    render_neighbor(0, previous_entry, previous_brightness)
                styled_current = compensate_double_height_cells(
                    stylize_karaoke_with_emojimax(lyric_text, karaoke_style, karaoke_emojimax)
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
                    render_neighbor(4, next_entry, next_brightness)
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
        """Render compact current-state glyphs; question mark opens full help."""
        loop_glyph = "\U0001f501" if looping else "\u21aa"
        shuffle_glyph = "\U0001f500" if shuffle_state and shuffle_state[0] else "\u2192"
        emoji_glyph = "+" if karaoke_emojimax else "-"
        sixel_glyph = "+" if sixel_enabled else "-"
        controls = (
            "\033[2;90m  ?: "
            f"\033[38;2;175;175;185m{loop_glyph} {shuffle_glyph}\033[2;90m  "
            f"K:{KARAOKE_STYLE_NAMES[karaoke_style - 1]}/{KARAOKE_TREATMENT_NAMES[karaoke_treatment - 1]} E:{emoji_glyph} "
            f"V:{'+' if drcs_enabled else '-'} W:{sixel_glyph} "
            f"M{visualizer_mode}:{VISUALIZER_TYPE_NAMES[(visualizer_mode - 1) % len(VISUALIZER_TYPE_NAMES)]}/"
            f"{VISUALIZER_TREATMENT_NAMES[(visualizer_mode - 1) // len(VISUALIZER_TYPE_NAMES)]} "
            f"C{color_style}:{COLOR_STYLE_NAMES[color_style - 1]} F:{FADE_STYLE_NAMES[fade_style - 1]} "
            f"S:{speed_color(PLAYBACK_SPEEDS[speed_index], progress)}{format_speed(PLAYBACK_SPEEDS[speed_index])}\033[2;90m "
            f"O:{output_channels} B:{balance:+d}"
        )
        available = max(12, shutil.get_terminal_size((120, 30)).columns - 1)
        write_console(
            move_to(CONTROLS_ROW)
            + truncate_ansi_to_cells(controls, available)
            + "\033[0m\033[K\033[?25l"
        )

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
        played_note = ", ".join(
            f"{format_position(start)}\N{EN DASH}{format_position(end)}"
            for start, end in merged
        )
        def _write_played_status(label: str | None) -> None:
            marker = f" \033[2;90m[{label}]\033[0m" if label else ""
            note = f" \033[2;90m[played {played_note}]\033[0m" if played_note else ""
            write_console(
                move_to(HEADER_ROW) + cursor_state + BIG_OFF + "\033[2K"
                + "\033[32m\U0001f50a  Played:\033[0m "
                + f"\033[34;3m{audio_path.name}\033[0m ({format_duration_label(duration)})"
                + marker + note + "\033[0m\n"
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
        write_console(
            ("\n" if initial_blank_line else "")
            + "\n" * UI_ROWS
            + f"\033[{UI_ROWS}A\r\033[s\033[?7l\033[?25l"
        )
        clear_region(0, UI_ROWS)
        write_console(define_all_player_drcs() + "\033[?25l")
        render_static_header()
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
                audio_path, position, visualizer_columns, album_art_display
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
                refresh_console_title(now)
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
                        render_static_header()
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
                if help_overlay_until and now >= help_overlay_until:
                    help_overlay_until = 0.0
                    clear_region(HEADER_ROW, min(UI_ROWS, 10))
                    render_static_header()
                    render_controls(min(1.0, displayed_position / duration) if duration else 0.0)
                if action is None and now - last_status_write >= 0.04:
                    show_status(displayed_position, indicator)
                    last_status_write = now
                if action is None and sixel_enabled and now - last_sixel_refresh >= 0.5:
                    frame = render_sixel_visualizer(
                        audio_path, displayed_position, visualizer_columns,
                        album_art_display,
                    )
                    if frame:
                        write_console(move_to(SIXEL_ROW))
                        write_console_bytes(frame)
                        write_console("\033[?25l")
                    last_sixel_refresh = now
                if action == HELP_OVERLAY:
                    if help_overlay_until:
                        help_overlay_until = 0.0
                        clear_region(HEADER_ROW, min(UI_ROWS, 10))
                        render_static_header()
                        render_controls(min(1.0, displayed_position / duration) if duration else 0.0)
                    else:
                        help_overlay_until = now + 8.0
                        render_help_overlay()
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
                    render_static_header()
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
                                DRCS_VISUALIZER_ROWS,
                                max(1, terminal_lines - (DRCS_ROW + (SIXEL_VISUALIZER_ROWS if sixel_enabled else 0) + LYRIC_ROWS) - 1),
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
                        refresh_console_title(paused_now, paused=True)
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
                            render_static_header()
                            render_controls(min(1.0, position / duration) if duration else 0.0)
                            last_drcs_position = None
                            last_lyric_index = None
                            show_status(position, "⏸️")
                        if PREVENT_WINAMP_PAUSE_WHEN_WE_ARE_PAUSED:
                            if guard_winamp and paused_now - last_winamp_enforcement >= 0.5:
                                if pause_playing_winamp() and manage_winamp:
                                    winamp_paused_by_preview = True
                                last_winamp_enforcement = paused_now
                        paused_action = key_action_reader()
                        if paused_action == HELP_OVERLAY:
                            if help_overlay_until:
                                help_overlay_until = 0.0
                                clear_region(HEADER_ROW, min(UI_ROWS, 10))
                                render_static_header()
                                render_controls(min(1.0, position / duration) if duration else 0.0)
                            else:
                                help_overlay_until = paused_now + 8.0
                                render_help_overlay()
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
        for key in ("\x1b", "x", "X", "q", "Q", "\x17", "\x03"):
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
        self.assertEqual(FADE_NEXT, interpret_console_key("f"))
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
        self.assertEqual("visualizer-mode-digit:3", interpret_console_key("3"))
        self.assertEqual(RESET_DEFAULTS, interpret_console_key("\x00", extended=";"))
        self.assertEqual(KARAOKE_PREVIOUS, interpret_console_key("\x00", extended="<"))
        self.assertEqual(KARAOKE_NEXT, interpret_console_key("\x00", extended="="))
        self.assertEqual(KARAOKE_TREATMENT_PREVIOUS, interpret_console_key("\x00", extended="<", shift=True))
        self.assertEqual(KARAOKE_TREATMENT_NEXT, interpret_console_key("\x00", extended="=", shift=True))
        self.assertEqual(KARAOKE_EMOJI_TOGGLE, interpret_console_key("\x00", extended=">"))
        self.assertEqual(KARAOKE_VISUALIZER_OVERLAY_TOGGLE, interpret_console_key("\x00", extended="D", shift=True))
        self.assertIsNone(interpret_console_key("v", ctrl=True, alt=True))
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

    def test_tag_panel_is_compact_and_omits_missing_tags(self) -> None:
        plain, ansi = format_tag_panel({
            "Artist": "Example Artist",
            "Song": "Example Song",
            "Album": "Example Album",
            "Year": "2026",
            "Genre": "Punk",
        })
        self.assertEqual(3, len(plain))
        self.assertEqual(3, len(ansi))
        self.assertIn("Artist: Example Artist", plain[0])
        self.assertIn("Album: Example Album", plain[1])
        self.assertEqual(10, plain[0].index(":"))
        self.assertEqual(plain[0].index(":"), plain[1].index(":"))
        self.assertEqual(plain[0].index("Example Artist"), plain[1].index("Example Album"))
        self.assertEqual(plain[1].rindex(":"), plain[2].rindex(":"))
        self.assertIn("\033[38;2;35;220;195mExample Artist", ansi[0])
        self.assertIn("\033[5;38;2;35;220;195mExample Song", ansi[0])

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
            self.assertEqual(30, len(COLOR_STYLE_NAMES))
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
        self.assertIn("❤️", stylize_karaoke_with_emojimax("love", 1, True))
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
        self.assertEqual((0, 2, 4), lyric_scroll_rows(0.0))
        self.assertEqual((-1, 1, 3), lyric_scroll_rows(LYRIC_SCROLL_STEP_SECONDS))
        self.assertEqual((-2, 0, 2), lyric_scroll_rows(LYRIC_SCROLL_STEP_SECONDS * 2))
        self.assertEqual((-3, -1, 1), lyric_scroll_rows(LYRIC_SCROLL_STEP_SECONDS * 3))
        self.assertIsNone(lyric_scroll_rows(LYRIC_SCROLL_STEP_SECONDS * 4))

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

        print("\033[96mUsage:\033[0m play_audio_file.py [options] <audio-file>")
        usage_line("-u, --usage", "show this usage")
        usage_line("-t, --unit-tests", "run embedded tests")
        usage_line("-e, --emoji-display-test", "test emojimaxxifying of text")
        usage_line("-l, --loop / -L, --no-loop", "loop the current track", "on")
        usage_line("-k, --karaoke / -K, --no-karaoke", "display available lyrics", "on")
        usage_line("-r, --random-file [directory]", "random file in one folder")
        usage_line("-R, --random-file-recursive [directory]", "random downward folder walk")
        usage_line("-p, --playlist FILE", "playlist; shuffled initially", "shuffle")
        usage_line("-b, --initial-blank-line / -B, --suppress-initial-blank-line", "leading blank line", "on")
        usage_line("-ghfl, --generate-play-history-from-lastfm-logs", "parse Last.fm logs and write play history CSV")
        usage_line("-dh, --display-play-history", "display the generated play‑history CSV")
        print("\n\033[94mVisualizer options:\033[0m")
        usage_line("-v, --visualizers / -V, --no-visualizers", "enable/disable both")
        usage_line("-d, --drcs-visualizer / -D, --no-drcs-visualizer", "DRCS spectrum", "on" if ENABLE_DRCS_VISUALIZER else "off")
        usage_line(
            "-s, --sixel-visualizer / -S, --no-sixel-visualizer",
            "SIXEL spectrum",
            "on" if ENABLE_SIXEL_VISUALIZER else "off",
            "not working under Windows 10 + Windows Terminal",
        )
        usage_line("-f, --fade-time SECONDS", "spectrum persistence; 0 disables", f"{DEFAULT_VISUALIZER_FADE_SECONDS:g}s")
        usage_line("Shift+F10", "experimental karaoke-over-visualizer overlay", "off")
        usage_line("-a, --album-art / -A, --no-album-art", "SIXEL artwork background", "on")
        print("\n\033[94mNow-playing sidecars:\033[0m")
        usage_line("-n, --no-now-playing", "suppress all DAT/JPG output")
        usage_line("-N, --no-now-playing-sidecar", "suppress script-side DAT/JPG only")
        usage_line("-o, --now-playing PATH", "also write DAT/JPG at PATH")
        print("\n\033[94mRequired Claire library files:\033[0m")
        print("  \033[38;2;145;205;255mC:\\clairecjs_utils\\claire_progressbar.py\033[0m"
              "  \033[38;2;210;165;255mplaylist progress bars\033[0m")
        print("  \033[38;2;145;205;255mPython package: wcwidth (optional)\033[0m"
              "              \033[38;2;210;165;255mUnicode terminal-cell measurement\033[0m")
        print("\n\033[2;90mV toggles the DRCS visualizer;"
              " W toggles the SIXEL visualizer.\033[0m")
        print("\033[2;90m?: toggle full keys; F2/F3: karaoke style; Shift+F2/F3: treatment; F4: emojimax.\033[0m")
        print("\033[2;90mHold F2+F3 3s: style Megamix; add Shift 3s/6s: treatment Megamix1/Megamix2.\033[0m")
        print("\033[2;90mF1: all defaults; Alt+F1: undo reset; F5/Ctrl+L/Ctrl+R: redraw.\033[0m")
        print("\033[2;90mShift+F10: karaoke/visualizer overlay; Ctrl+Alt+L: force Last.fm scrobble.\033[0m")
        print("\033[2;90mCtrl-V: visualizer; F6/F7: visualizer modes; Shift-F6/F7: interpretations; C/Shift+C: colors; F/Shift+F: fades.\033[0m")
        print("\033[2;90mP/Shift+P: progress style; A: autoplay (enables shuffle).\033[0m")
        print("\033[2;90m2: stereo; 5: 5.1 expansion; 7: 7.1 expansion.\033[0m")
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
        elif argument in {"--now-playing", "-o"}:
            argument_index += 1
            if argument_index >= len(arguments):
                print("ERROR: --now-playing requires a DAT pathname.", file=sys.stderr)
                return 2
            external_now_playing = Path(arguments[argument_index]).absolute()
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
        elif argument in {"--display-play-history", "-d"}:
            display_history = True
            # Early‑exit: display CSV and exit
            try:
                display_lastfm_play_history()
            except Exception as exc:
                print(f"❌ Failed to display play history: {exc}", file=sys.stderr)
                sys.exit(1)
            try:
                fade_seconds = float(argument.partition("=")[2])
            except ValueError:
                print("💥 ERROR: --fade-time must be a number.", file=sys.stderr)
                return 2
                sys.exit(1)
        elif argument.startswith("-"):
            print(f"💥 ERROR: Unknown option: {argument}", file=sys.stderr)
            return 2
        else:
            filenames.append(argument)
        argument_index += 1
    if not math.isfinite(fade_seconds) or fade_seconds < 0:
        print("💥 ERROR: --fade-time must be zero or greater.", file=sys.stderr)
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
                now_playing_targets.append(
                    Path(__file__).resolve().with_name('play_audio_file-now_playing.dat')
                )
            if external_now_playing is not None:
                now_playing_targets.append(external_now_playing)
        playlist_entries: list[Path] | None = None
        shuffle_state: list[bool] | None = None
        playlist_history: list[Path] = []
        playlist_played: set[Path] = set()
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
        playlist_path: Path | None = None
        initial_resume_position = 0.0
        playback_position_state = [0.0]
        autoplay_seen: dict[Path, set[Path]] = {}
        pending_folder_line: Path | None = None
        def playlist_history_status(active: bool) -> None:
            if active:
                write_console("\033[2;90m[checking play history]\033[0m")
            else:
                write_console("\r\033[2K")

        if playlist_argument is not None:
            playlist_path = Path(playlist_argument).absolute()
            playlist_entries = load_playlist(playlist_path)
            shuffle_state = [bool(persisted_settings['Shuffle'])]
            saved_resume = load_playlist_resume(playlist_path)
            resumed_entry = None
            if saved_resume is not None:
                saved_track, initial_resume_position = saved_resume
                resumed_entry = next(
                    (entry for entry in playlist_entries if entry.resolve() == saved_track.resolve()),
                    None,
                )
            # Playlist sessions begin in persistent shuffle mode: choose only
            # among the oldest 15% of history, never repeating while unplayed
            # entries remain.
            shuffle_state = [True]
            current_audio = resumed_entry or choose_least_recent_playlist_track(playlist_entries, playlist_history_status)
            if resumed_entry is not None:
                write_console(
                    f"\033[38;2;120;210;190m↩ Resuming playlist: {current_audio.name} "
                    f"at {format_position(initial_resume_position)}\033[0m\n"
                )
            else:
                initial_resume_position = 0.0
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

        if shuffle_state is None:
            shuffle_state = [False]
        while True:
            playback_position_state[0] = initial_resume_position
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
                    # Chafa may include a terminal line ending of its own;
                    # normalize it so the preview contributes only one row of
                    # cursor advance and leaves no blank margin below.
                    write_console_bytes(preplay_cover.rstrip(b"\r\n"))
                    write_console("\n")
            if pending_folder_line is not None:
                write_console(
                    "\033[?25l\033[38;2;140;210;255m" + "\U0001f4c1" + "  Folder:\033[0m "
                    + f"\033[38;2;140;210;255m{pending_folder_line}\033[0m\n"
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
                now_playing_targets=now_playing_targets,
                album_art_display=album_art_display,
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
            if playlist_entries is not None:
                playlist_history_mark_played(current_audio)
                playlist_history.append(current_audio)
                if result == "stopped":
                    if playlist_path is not None:
                        save_playlist_resume(
                            playlist_path, current_audio, playback_position_state[0]
                        )
                    break
                previous_directory = current_audio.parent.resolve()
                if result == PREVIOUS_FILE and len(playlist_history) > 1:
                    current_audio = playlist_history[-2]
                elif shuffle_state and shuffle_state[0]:
                    current_audio = choose_least_recent_playlist_track(playlist_entries, playlist_history_status)
                else:
                    current_index = playlist_entries.index(current_audio)
                    current_audio = playlist_entries[(current_index + 1) % len(playlist_entries)]
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
    Parse Last.fm scrobble logs and write a CSV file with columns:
    start,end,artist,title,album,duration_seconds.

    Searches common Last.fm log locations in priority order.
    Malformed lines are skipped.
    """

    local_appdata = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))

    candidate_paths = [
        # Normal Last.fm Scrobbler location
        local_appdata / "Last.fm" / "Last.fm Scrobbler.log",

        # Alternate log-directory layouts
        local_appdata / "Last.fm" / "logs" / "Last.fm Scrobbler.log",
        local_appdata / "Last.fm" / "logs" / "last.fm" / "Last.fm Scrobbler.log",

        # Older/custom fallback
        Path.home() / ".clairecjs_utils" / "lastfm_scrobbles.log",
    ]

    log_path = next((path for path in candidate_paths if path.is_file()), None)

    if log_path is None:
        searched = "\n".join(f"  {path}" for path in candidate_paths)
        raise FileNotFoundError(
            "Last.fm log file not found. Searched:\n"
            f"{searched}"
        )

    # Write CSV header
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "start",
            "end",
            "artist",
            "title",
            "album",
            "duration_seconds",
        ])

        for line in log_path.read_text(
            encoding="utf-8",
            errors="replace",
        ).splitlines():
            # Expected format: timestamp|artist|track|album|duration_ms
            parts = line.strip().split("|")
            if len(parts) != 5:
                continue

            ts, artist, title, album, dur_ms = parts

            try:
                start_dt = datetime.fromtimestamp(int(ts), tz=timezone.utc)
                duration = int(dur_ms) // 1000
                end_dt = start_dt + timedelta(seconds=duration)

                writer.writerow([
                    start_dt.isoformat(),
                    end_dt.isoformat(),
                    artist,
                    title,
                    album,
                    duration,
                ])
            except (ValueError, OverflowError, OSError):
                continue


def display_lastfm_play_history() -> None:
    """
    Read the CSV generated by ``generate_lastfm_play_history`` and print a
    formatted table to stdout. Uses simple column alignment.
    """
    csv_path = Path(__file__).resolve().with_name('lastfm_play_history.csv')
    if not csv_path.is_file():
        raise FileNotFoundError(f"Play‑history CSV not found at {csv_path}")

    rows = list(csv.reader(csv_path.open("r", encoding="utf-8")))
    header, *data = rows
    col_widths = [max(len(row[i]) for row in rows) for i in range(len(header))]
    fmt = " | ".join(f"{{:<{w}}}" for w in col_widths)
    print(fmt.format(*header))
    print("-+-".join("-"*w for w in col_widths))
    for row in data:
        print(fmt.format(*row))

if __name__ == "__main__":
    raise SystemExit(main())
