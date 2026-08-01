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
try:
    from wcwidth import wcswidth
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
from claire_progressbar import progress_bar


# Set to 0 when the terminal cannot render DEC SIXEL graphics.
PREVENT_WINAMP_PAUSE_WHEN_WE_ARE_PAUSED = 0
LYRIC_FADE_SECONDS              = 5.0
ENABLE_SIXEL_VISUALIZER         = 0
ENABLE_DRCS_VISUALIZER          = 1
DRCS_VISUALIZER_ROWS            = 16
LYRIC_MAX_UNTIMED_SECONDS       = 15.0
SIXEL_VISUALIZER_ROWS           = 8
STOP                            = "stop"
SEEK_BACK_5                     = "seek-back-5"
SEEK_FORWARD_5                  = "seek-forward-5"
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
COLOR_FAVORITE_TOGGLE           = "color-favorite-toggle"
COLOR_FAVORITE_CYCLE            = "color-favorite-cycle"
KARAOKE_PREVIOUS                = "karaoke-previous"
KARAOKE_NEXT                    = "karaoke-next"
KARAOKE_TREATMENT_NEXT          = "karaoke-treatment-next"
KARAOKE_FAVORITE_TOGGLE         = "karaoke-favorite-toggle"
KARAOKE_FAVORITE_CYCLE          = "karaoke-favorite-cycle"
AUTOPLAY_TOGGLE                 = "autoplay-toggle"
PROGRESS_STYLE_PREVIOUS         = "progress-style-previous"
PROGRESS_STYLE_NEXT             = "progress-style-next"
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
DEFAULT_VISUALIZER_FADE_SECONDS = 1.0
AUDIO_EXTENSIONS = {
    ".aac", ".ac3", ".aif", ".aiff", ".alac", ".ape", ".au", ".dsf",
    ".dff", ".flac", ".m4a", ".mka", ".mp2", ".mp3", ".ogg", ".oga",
    ".opus", ".ra", ".shn", ".tta", ".wav", ".wma", ".wv",
}
NAVIGATION_ACTIONS = {
    PREVIOUS_FILE, NEXT_FILE, PREVIOUS_DIRECTORY, NEXT_DIRECTORY,
}
_AUDIO_DIRECTORY_CACHE: dict[Path, list[tuple[Path, list[Path]]]] = {}
_ASYNC_KEY_LATCH: set[int] = set()
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
COLOR_STYLE_NAMES = tuple(f"Color {number:02d}" for number in range(1, 31))
KARAOKE_LEGACY_STYLES = (11, 12, 13, 16, 17, 21, 22, 24, 26, 36, 37, 39, 41, 42, 46)

PROGRESS_STYLE_NAMES = tuple(f"Progress {number:02d}" for number in range(1, 16))



semantic_OLD_v1 = {
    "love": "❤️", "heart": "💗", "fire": "🔥", "star": "⭐", "stars": "🌟",
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
         'control': '🎛️',
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
         'fight': '\U0001faef',
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
         'pill': '💊',
         'pilot': '🧑\u200d✈️',
         'pin': '📍',
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
         'prime': '′',
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
         'socks': '🧦🧦',
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
         'stars': '🌟',
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
         'sweat': '💦',
         'sweaty': '💦',
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

KARAOKE_STYLE_NAMES = tuple(f"Legacy {number:02d}" for number in KARAOKE_LEGACY_STYLES) + (
    "Every Letter Unicode", "Every Letter Emoji", "Closest Unicode/Emoji",
    "🤟 Semantic Word Emoji 🤟",
)
KARAOKE_TREATMENT_NAMES = (
    "Readable Solid", "Line Rainbow", "Word Rainbow",
    "Random Letter Color", "Hashed Word Color",
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
        return "".join(
            chr(0x1F1E6 + ord(character.upper()) - 65)
            if character.isascii() and character.isalpha() else character
            for character in text
        )
    if mode == 2:
        close = {
            "A": "🅰", "a": "🅰", "B": "🅱", "b": "🅱", "E": "ℰ", "e": "ℰ",
            "I": "ℐ", "i": "ℐ", "O": "⭕", "o": "⭕", "P": "🅿", "p": "🅿",
            "S": "§", "T": "✝", "X": "❌", "a": "🅰", "b": "🅱", "e": "ℰ",
            "i": "ℐ", "o": "⭕", "p": "🅿", "s": "§", "t": "✝", "x": "❌",
            "U": "𝒰", "u": "𝒰",
        }
        return text.translate(str.maketrans(close))
    return re.sub(r"\b[\w’']+\b", lambda match: semantic.get(match.group(0).casefold(), match.group(0)), text)




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
            fade_end = next_start
            fade_start = max(start, next_start - fade_seconds)
    else:
        fade_start = start + LYRIC_MAX_UNTIMED_SECONDS
        fade_end = fade_start + fade_seconds
    if position > fade_end:
        return None
    opacity = 1.0 if position <= fade_start else max(
        0.0, (fade_end - position) / max(0.001, fade_end - fade_start)
    )
    return active_index, text, opacity




def terminal_cell_width(text: str) -> int:
    """Measure Unicode by terminal cells instead of Python code points."""
    return max(0, wcswidth(text))


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


def colorize_karaoke_text(text: str, treatment: int, seed: int = 0) -> str:
    """Apply an independent ANSI truecolor treatment to styled lyrics."""
    mode = (treatment - 1) % len(KARAOKE_TREATMENT_NAMES)
    if mode == 0:
        return text
    if mode == 1:
        length = max(1, len(text) - 1)
        return "".join(ansi_rgb(rainbow_rgb(index / length)) + char for index, char in enumerate(text)) + "\033[0m"
    if mode in {2, 4}:
        words = list(re.finditer(r"\S+", text))
        result: list[str] = []
        cursor = 0
        for index, match in enumerate(words):
            result.append(text[cursor:match.start()])
            rgb = rainbow_rgb(index / max(1, len(words) - 1)) if mode == 2 else hashed_word_rgb(match.group(0))
            result.append(ansi_rgb(rgb) + match.group(0) + "\033[0m")
            cursor = match.end()
        result.append(text[cursor:])
        return "".join(result)
    return "".join(
        ansi_rgb(tuple(70 + (int(hashlib.sha256(f"{seed}:{index}:{channel}".encode()).hexdigest(), 16) % 186) for channel in range(3))) + character
        for index, character in enumerate(text)
    ) + "\033[0m"


def format_tag_panel(tags: dict[str, str]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return compact aligned metadata rows as plain and ANSI text."""
    terminal_width = max(80, shutil.get_terminal_size((120, 30)).columns)
    starts = (3, max(44, round(terminal_width * 0.36)), max(78, round(terminal_width * 0.68)))
    label_widths = (7, 4, 5)
    row_specs = (("Artist", "Song", None), ("Album", "Year", "Genre"))

    def shortened(value: str, limit: int) -> str:
        if len(value) <= limit:
            return value
        candidate = value[:max(1, limit - 1)].rstrip()
        if candidate.count("(") > candidate.count(")"):
            candidate = candidate.rsplit("(", 1)[0].rstrip()
        return candidate.rstrip(" ([{-") + "…"

    plain_rows: list[str] = []
    ansi_rows: list[str] = []
    for labels in row_specs:
        plain = ""
        ansi = ""
        any_present = False
        for column, label in enumerate(labels):
            if label is None:
                continue
            value = str(tags.get(label, "") or "")
            if not value:
                continue
            any_present = True
            start = starts[column]
            next_start = starts[column + 1] if column + 1 < len(starts) else terminal_width
            available = max(8, next_start - start - label_widths[column] - 3)
            value = shortened(value, available)
            aligned_label = label.rjust(label_widths[column])
            padding = " " * max(0, start - len(plain))
            plain += padding + f"{aligned_label}: {value}"
            value_style = (
                "\033[5;38;2;35;220;195m" if label == "Song"
                else "\033[38;2;35;220;195m" if label == "Artist"
                else "\033[0;38;2;175;195;215m"
            )
            ansi += padding + (
                f"\033[2;90m{aligned_label}:\033[0m {value_style}"
                f"{value}\033[0m"
            )
        if any_present:
            plain_rows.append(plain)
            ansi_rows.append(ansi)
    return tuple(plain_rows), tuple(ansi_rows)


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
    if first == "\x0b":
        return KARAOKE_FAVORITE_TOGGLE if alt else KARAOKE_TREATMENT_NEXT
    if first.casefold() in {"q", "x"}:
        return STOP
    if first == " ":
        return PAUSE_TOGGLE
    if first.casefold() == "p":
        return PROGRESS_STYLE_PREVIOUS if shift else PROGRESS_STYLE_NEXT
    if first == "=":
        return VOLUME_RESET
    if first.casefold() == "l":
        return LOOP_TOGGLE
    if first.casefold() == "r":
        return RANDOM_TOGGLE
    if first.casefold() == "f":
        return COLOR_FAVORITE_TOGGLE if shift else VISUALIZER_MODE_FAVORITE
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
        return DRCS_VISUALIZER_TOGGLE
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
        return VISUALIZER_MODE_FIRST
    if extended == "<":
        return VISUALIZER_MODE_PREVIOUS
    if extended == "=":
        return VISUALIZER_MODE_NEXT
    if extended == ">":
        return STOP if alt else VISUALIZER_TREATMENT_PREVIOUS
    if extended == "?":
        return VISUALIZER_TREATMENT_NEXT
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
    """Resume Winamp only when this preview was the thing that paused it."""
    if not should_resume or os.name != "nt":
        return
    import ctypes

    user32 = ctypes.windll.user32
    hwnd = user32.FindWindowW("Winamp v1.x", None)
    if not hwnd:
        return
    # Pause is a toggle, so only send it while Winamp is verifiably paused.
    if user32.SendMessageW(hwnd, 0x0400, 0, 104) != 3:
        return
    user32.SendMessageW(hwnd, 0x0111, 40046, 0)


def read_windows_key_action() -> str | None:
    """Nonblockingly read one supported playback command on Windows."""
    if os.name != "nt":
        raise RuntimeError(
            "Interactive preview controls currently require Windows"
        )
    import msvcrt

    # Polling Alt+F4 also stops the player when the terminal does not place
    # that combination in its console input buffer.
    if _windows_key_down(0x12) and _windows_key_down(0x73):
        return STOP
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
        0xB0: NEXT_FILE,
        0xB1: PREVIOUS_FILE,
        0xB2: STOP,
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
    ]
    filters: list[str] = []
    if speed != 1.0:
        filters.append(atempo_filter(speed))
    if volume > 100:
        filters.append(f"volume={volume / 100:g}")
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
        import numpy as np
    except ImportError:
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
    values = [
        (
            spectrum_levels[
                round(
                    ((column / max(1, width - 1)) ** 2.4)
                    * (source_width - 1)
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
    mode = min(len(VISUALIZER_MODE_NAMES), max(1, mode))
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


def visualizer_color(style: int, row: int, column: int, width: int) -> tuple[int, int, int]:
    """Return one of thirty spectrum color treatments."""
    style = (style - 1) % len(COLOR_STYLE_NAMES)
    group, variant = divmod(style, 6)
    vertical = row / max(1, DRCS_VISUALIZER_ROWS - 1)
    horizontal = column / max(1, width - 1)
    hue = (vertical * 0.78 + variant / 6 + horizontal * (0.08 * group)) % 1.0
    if group == 1:
        hue = (1.0 - vertical * 0.78 + variant / 6) % 1.0
    elif group == 2:
        hue = (horizontal * 0.85 + variant / 6) % 1.0
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
) -> str:
    """Render an eight-row spectrum driven by analyzed audio frequencies."""
    width = max(12, columns)
    heights = visualizer_mode_heights(spectrum_levels, width, mode)

    lines: list[str] = []
    for row in range(DRCS_VISUALIZER_ROWS):
        threshold = 1 - (row + 1) / DRCS_VISUALIZER_ROWS
        glyphs: list[str] = []
        last_color: tuple[int, int, int] | None = None
        for column, height in enumerate(heights):
            coverage = (height - threshold) * DRCS_VISUALIZER_ROWS
            level = min(8, max(0, round(coverage * 8)))
            source_column = (
                round(column * (len(recent_energy) - 1) / max(1, width - 1))
                if recent_energy else 0
            )
            energy = recent_energy[source_column] if recent_energy else 0.0
            energy = round(max(0.0, min(1.0, energy)) * 15) / 15
            brightness = energy ** 1.5
            base_color = visualizer_color(color_style, row, column, width)
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
    hue = 1 - index / (len(PLAYBACK_SPEEDS) - 1)
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
    )
    filled_char, empty_char = pairs[(progress_style - 1) % len(pairs)]
    bar = filled_char * filled + empty_char * (bar_width - filled)
    bar_color = rainbow_rgb(fraction)
    if progress_style == 15:
        throb = 0.35 + 0.65 * max(0.0, min(1.0, pulse_energy))
        bar_color = tuple(round(component * throb) for component in bar_color)
    prefix = "\r\033[1A\033[2K" if repaint else "\r\033[2K"
    return (
        prefix + ansi_rgb(rainbow_rgb(fraction))
        + f"{indicator} {format_position(position)}"
        + (f" / {format_position(duration)}" if duration is not None else "")
        + "\033[0m"
        + volume_status(volume, volume_direction)
        + "\n" + BIG_OFF + "\033[2K"
        + ansi_rgb(bar_color)
        + f"{bar} {percentage}%\033[0m"
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


def render_sixel_visualizer(audio_path: Path, start_seconds: float, columns: int) -> bytes:
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
        sixel = subprocess.run(
            [chafa, "--format=sixels", "--colors=full", "--scale=max", "--stretch",
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
    lyrics_display: bool = True,
    shuffle_state: list[bool] | None = None,
    visualizer_mode_state: list[int] | None = None,
    color_style_state: list[int] | None = None,
    karaoke_style_state: list[int] | None = None,
    karaoke_treatment_state: list[int] | None = None,
    progress_style_state: list[int] | None = None,
    autoplay_state: list[bool] | None = None,
    output_channels_state: list[int] | None = None,
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
    tag_plain_rows, tag_ansi_rows = format_tag_panel(probe_audio_tags(audio_path))
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
    volume = 100
    volume_direction = "up"
    output_channels = output_channels_state[0] if output_channels_state is not None else 2
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
    speed_index = PLAYBACK_SPEEDS.index(1.0)
    process = None
    status_rendered = False
    loop_indicator_until = 0.0
    last_sixel_refresh = -10.0
    last_winamp_enforcement = -10.0
    screen_closed = False
    drcs_timeline: tuple[bytes, int, int] = (b"", 12, SPECTRUM_ANALYSIS_FPS)
    drcs_recent_energy: list[float] = []
    last_drcs_position: float | None = None
    visualizer_fade_seconds = max(0.0, visualizer_fade_seconds)
    HEADER_ROW = 0
    HELP_ROW = 1 + len(tag_plain_rows)
    CONTROLS_ROW = HELP_ROW + 3
    CONTROLS_ROWS = 2
    DRCS_ROW = CONTROLS_ROW + CONTROLS_ROWS
    STATUS_ROW = DRCS_ROW + (DRCS_VISUALIZER_ROWS if drcs_enabled else 0)
    SIXEL_ROW = STATUS_ROW + 2
    LYRIC_ROW = SIXEL_ROW + (SIXEL_VISUALIZER_ROWS if sixel_enabled else 0)
    # Previous and next cues use one double-height line each; the current cue
    # reserves two so a long lyric can wrap without moving the rest of the UI.
    LYRIC_ROWS = 8 if lyrics else 0
    UI_ROWS = LYRIC_ROW + LYRIC_ROWS
    drcs_has_space = drcs_enabled
    sixel_has_space = sixel_enabled
    last_lyric_index: int | None = None
    played_ranges: list[tuple[float, float]] = []
    visualizer_mode = (
        visualizer_mode_state[0]
        if visualizer_mode_state is not None
        else load_favorite_visualizer_mode()
    )
    visualizer_mode_digits = ""
    color_style = color_style_state[0] if color_style_state is not None else 1
    karaoke_style = karaoke_style_state[0] if karaoke_style_state is not None else 1
    karaoke_treatment = karaoke_treatment_state[0] if karaoke_treatment_state is not None else 1
    progress_style = progress_style_state[0] if progress_style_state is not None else 1
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

    help_texts = (
        help_line("Stop", "Esc/X/Q/Ctrl+W/Alt+F4/Ctrl+C/Ctrl+Break"),
        help_line("Seek", "← / → 5 seconds; Shift+← / Shift+→ 15 seconds; Ctrl+← / Ctrl+→ 1 minute"),
        help_line("Files", "< / > previous/next (wraps here); folders: { / } previous/next with audio"),
        help_line("Pause", "Space/media; volume: ↑/↓ (= resets); speed: +/− (1×); output: 2/5/7 (stereo); loop: L (On); ")
        + initial_visualizer_help,
    )

    def render_static_header() -> None:
        """Render fixed rows without permitting implicit terminal wrapping."""
        available = max(12, shutil.get_terminal_size((120, 30)).columns - 1)
        header = (
            "\033[32m🔊 Playing:\033[0m "
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

    def show_status(current_position: float, indicator: str) -> None:
        """Paint the two-line status, preserving its fixed screen position."""
        nonlocal status_rendered, last_drcs_position, last_lyric_index
        if playback_position_state is not None:
            playback_position_state[0] = max(0.0, current_position)
        timestamp_text = (
            f"{indicator} {format_position(current_position)}"
            + (f" / {format_position(duration)}" if duration is not None else "")
            + volume_status_plain(volume, volume_direction)
        )
        widest_line = max(
            *(terminal_cell_width(text) for text in help_texts),
            *(terminal_cell_width(text) for text in tag_plain_rows),
            terminal_cell_width(title_text),
            terminal_cell_width(timestamp_text),
        )
        available_width = max(12, shutil.get_terminal_size((120, 30)).columns - 1)
        bar_width = max(1, min(widest_line, available_width) - len(" 100%"))
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
                    bar_width, levels, drcs_recent_energy, visualizer_mode, color_style
                )
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
        else:
            lyric_index, lyric_text, opacity = active_lyric
            readable = ((255, 220, 120), (150, 235, 255), (210, 180, 255), (170, 255, 185))
            base_red, base_green, base_blue = readable[lyric_index % len(readable)]
            foreground = ansi_rgb(tuple(max(2, round(component * opacity)) for component in (base_red, base_green, base_blue)))
            line_capacity = max(10, max(20, bar_width) // 2)

            def neighboring_text(direction: int) -> str:
                candidate = lyric_index + direction
                while 0 <= candidate < len(lyrics):
                    if lyrics[candidate][2].strip():
                        return lyrics[candidate][2]
                    candidate += direction
                return ""

            def double_height(row: int, text: str, *, current: bool, seed: int) -> None:
                centered = center_to_cells(text, line_capacity)
                colored = colorize_karaoke_text(centered, karaoke_treatment, seed)
                attributes = ("\033[48;2;2;3;5m" + foreground) if current else "\033[2m\033[38;2;95;125;120m"
                write_console(
                    move_to(LYRIC_ROW + row) + "\033#3" + attributes + colored + "\033[0m\033[K"
                    + move_to(LYRIC_ROW + row + 1) + "\033#4" + attributes + colored + "\033[0m\033[K"
                )

            def render_neighbor(row: int, text: str, seed: int) -> None:
                styled = stylize_karaoke_text(text, karaoke_style)
                if terminal_cell_width(styled) <= line_capacity:
                    double_height(row, styled, current=False, seed=seed)
                    return
                # Wide neighboring cues use one normal-height row so their
                # double-width cells cannot collide. They are 40% as bright
                # as the current cue and deliberately have no background.
                normal_capacity = max(10, bar_width)
                fitted = truncate_to_cells(styled, normal_capacity, "…")
                dim_rgb = tuple(round(component * 0.4) for component in (base_red, base_green, base_blue))
                write_console(
                    move_to(LYRIC_ROW + row + 1) + BIG_OFF + ansi_rgb(dim_rgb)
                    + center_to_cells(fitted, normal_capacity) + "\033[0m\033[K"
                )

            clear_region(LYRIC_ROW, LYRIC_ROWS)
            previous_text = neighboring_text(-1)
            next_text = neighboring_text(1)
            if previous_text:
                render_neighbor(0, previous_text, lyric_index - 1)
            styled_current = stylize_karaoke_text(lyric_text, karaoke_style)
            wrapped = wrap_to_cells(styled_current, line_capacity)
            pages = [wrapped[index:index + 2] for index in range(0, len(wrapped), 2)]
            cue_start = lyrics[lyric_index][0]
            page = pages[min(len(pages) - 1, max(0, int((current_position - cue_start) // 4)))]
            current_start_row = 2 if len(page) > 1 else 3
            for page_row, line in enumerate(page):
                double_height(current_start_row + page_row * 2, line, current=True, seed=lyric_index)
            if next_text:
                render_neighbor(6, next_text, lyric_index + 1)
            last_lyric_index = lyric_index
        write_console("\033[?25l")
        set_console_cursor_visible(False)
        status_rendered = True

    def render_controls(progress: float = 0.0) -> None:
        """Update the sole visible Loop On/Off state in the keystroke summary."""
        loop_word = "On" if looping else "Off"
        visualizer_help = (
            f"visualizer: V ({'On' if drcs_enabled else 'Off'}); "
            f"{VISUALIZER_MODE_NAMES[visualizer_mode - 1]} [F2/F3,F4/F5]; "
            f"{COLOR_STYLE_NAMES[color_style - 1]} [C]; "
            f"{KARAOKE_STYLE_NAMES[karaoke_style - 1]} / "
            f"{KARAOKE_TREATMENT_NAMES[karaoke_treatment - 1]} [K/Ctrl+K]; "
            f"{PROGRESS_STYLE_NAMES[progress_style - 1]} [P]; "
            f"autoplay: A ({'On' if autoplay_state and autoplay_state[0] else 'Off'})"
        )
        if sixel_enabled:
            visualizer_help += "; W (On)"
        controls_first = (
            "\033[2;90m"
            f"   {'Pause':>7}: Space/media; volume: up/down; speed: +/- ("
            f"{speed_color(PLAYBACK_SPEEDS[speed_index], progress)}"
            f"{format_speed(PLAYBACK_SPEEDS[speed_index])}\033[2;90m); "
            f"output: 2/5/7 ({'stereo' if output_channels == 2 else f'{output_channels}.1 expansion'}); "
            f"loop: L ({loop_word}); "
            + (
                f"random: R ({'On' if shuffle_state[0] else 'Off'}); "
                if shuffle_state is not None else ""
            )
        )
        controls_second = f"\033[2;90m   {'Display':>7}: {visualizer_help}"
        available = max(12, shutil.get_terminal_size((120, 30)).columns - 1)
        write_console(
            move_to(CONTROLS_ROW)
            + truncate_ansi_to_cells(controls_first, available)
            + move_to(CONTROLS_ROW + 1)
            + truncate_ansi_to_cells(controls_second, available)
            + "\033[?25l"
        )

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
        merged: list[list[float]] = []
        for start, end in sorted(played_ranges):
            if merged and start <= merged[-1][1] + 0.5:
                merged[-1][1] = max(merged[-1][1], end)
            else:
                merged.append([start, end])
        played_note = ", ".join(
            f"{format_position(start)}–{format_position(end)}"
            for start, end in merged
        )
        write_console(
            move_to(HEADER_ROW) + cursor_state
            + "\033[32m🔊  Played:\033[0m "
            f"\033[34;3m{audio_path.name}\033[0m ({format_duration_label(duration)})"
            + (f" \033[2;90m[played {played_note}]\033[0m" if played_note else "")
            + "\033[0m\n"
        )
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
            render_sixel_visualizer(audio_path, position, visualizer_columns)
            if sixel_enabled else b""
        )
        if sixel_frame:
            write_console(move_to(SIXEL_ROW))
            write_console_bytes(sixel_frame)
            write_console("\033[?25l")
        indicator = "▶️"
        last_status_write = 0.0
        last_terminal_size = shutil.get_terminal_size((120, 30))
        while True:
            speed = PLAYBACK_SPEEDS[speed_index]
            command = ffplay_command(
                player, audio_path, position, volume, speed, output_channels
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
                terminal_size = shutil.get_terminal_size((120, 30))
                if terminal_size != last_terminal_size:
                    last_terminal_size = terminal_size
                    visualizer_columns = max(12, terminal_size.columns - 1)
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
                if now - last_status_write >= 0.04:
                    show_status(displayed_position, indicator)
                    last_status_write = now
                if sixel_enabled and now - last_sixel_refresh >= 0.5:
                    frame = render_sixel_visualizer(
                        audio_path, displayed_position, visualizer_columns
                    )
                    if frame:
                        write_console(move_to(SIXEL_ROW))
                        write_console_bytes(frame)
                        write_console("\033[?25l")
                    last_sixel_refresh = now
                if abort_requested.is_set():
                    record_segment(displayed_position)
                    stop_process(process)
                    return finish_playback("stopped")
                action = key_action_reader()
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
                if action in {KARAOKE_PREVIOUS, KARAOKE_NEXT, KARAOKE_TREATMENT_NEXT, KARAOKE_FAVORITE_TOGGLE, KARAOKE_FAVORITE_CYCLE}:
                    if action == KARAOKE_PREVIOUS:
                        karaoke_style = ((karaoke_style - 2) % len(KARAOKE_STYLE_NAMES)) + 1
                    elif action == KARAOKE_NEXT:
                        karaoke_style = (karaoke_style % len(KARAOKE_STYLE_NAMES)) + 1
                    elif action == KARAOKE_TREATMENT_NEXT:
                        karaoke_treatment = (karaoke_treatment % len(KARAOKE_TREATMENT_NAMES)) + 1
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
                if action == SIXEL_VISUALIZER_TOGGLE:
                    sixel_enabled = not sixel_enabled
                    if not sixel_enabled:
                        clear_region(SIXEL_ROW, SIXEL_VISUALIZER_ROWS)
                        if sixel_has_space:
                            write_console(move_to(SIXEL_ROW) + f"\033[{SIXEL_VISUALIZER_ROWS}M")
                            if DRCS_ROW > SIXEL_ROW:
                                DRCS_ROW -= SIXEL_VISUALIZER_ROWS
                            if LYRIC_ROW > SIXEL_ROW:
                                LYRIC_ROW -= SIXEL_VISUALIZER_ROWS
                            UI_ROWS -= SIXEL_VISUALIZER_ROWS
                            sixel_has_space = False
                    elif not sixel_has_space:
                        if LYRIC_ROWS:
                            clear_region(LYRIC_ROW, LYRIC_ROWS)
                            write_console(move_to(LYRIC_ROW) + f"\033[{LYRIC_ROWS}M")
                            UI_ROWS -= LYRIC_ROWS
                        SIXEL_ROW = UI_ROWS
                        LYRIC_ROW = SIXEL_ROW + SIXEL_VISUALIZER_ROWS
                        added_rows = SIXEL_VISUALIZER_ROWS + LYRIC_ROWS
                        write_console(move_to(UI_ROWS) + "\n" * added_rows)
                        UI_ROWS += added_rows
                        sixel_has_space = True
                        last_lyric_index = None
                    render_controls()
                    show_status(displayed_position, indicator)
                    continue
                if action == DRCS_VISUALIZER_TOGGLE:
                    drcs_enabled = not drcs_enabled
                    if not drcs_enabled:
                        clear_region(DRCS_ROW, DRCS_VISUALIZER_ROWS)
                        if drcs_has_space:
                            write_console(move_to(DRCS_ROW) + f"\033[{DRCS_VISUALIZER_ROWS}M")
                            if STATUS_ROW > DRCS_ROW:
                                STATUS_ROW -= DRCS_VISUALIZER_ROWS
                            if SIXEL_ROW > DRCS_ROW:
                                SIXEL_ROW -= DRCS_VISUALIZER_ROWS
                            if LYRIC_ROW > DRCS_ROW:
                                LYRIC_ROW -= DRCS_VISUALIZER_ROWS
                            UI_ROWS -= DRCS_VISUALIZER_ROWS
                            drcs_has_space = False
                    else:
                        if not drcs_has_space:
                            if LYRIC_ROWS:
                                clear_region(LYRIC_ROW, LYRIC_ROWS)
                                write_console(move_to(LYRIC_ROW) + f"\033[{LYRIC_ROWS}M")
                                UI_ROWS -= LYRIC_ROWS
                            DRCS_ROW = UI_ROWS
                            LYRIC_ROW = DRCS_ROW + DRCS_VISUALIZER_ROWS
                            added_rows = DRCS_VISUALIZER_ROWS + LYRIC_ROWS
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
                        terminal_size = shutil.get_terminal_size((120, 30))
                        if terminal_size != last_terminal_size:
                            last_terminal_size = terminal_size
                            visualizer_columns = max(12, terminal_size.columns - 1)
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
                        if abort_requested.is_set() or paused_action == STOP:
                            return finish_playback("stopped")
                        if paused_action in NAVIGATION_ACTIONS:
                            return finish_playback(paused_action)
                        if paused_action == PAUSE_TOGGLE:
                            indicator = "▶️"
                            break
                        if paused_action == LOOP_TOGGLE:
                            looping = not looping
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
                        if paused_action in {KARAOKE_PREVIOUS, KARAOKE_NEXT, KARAOKE_TREATMENT_NEXT, KARAOKE_FAVORITE_TOGGLE, KARAOKE_FAVORITE_CYCLE}:
                            if paused_action == KARAOKE_PREVIOUS:
                                karaoke_style = ((karaoke_style - 2) % len(KARAOKE_STYLE_NAMES)) + 1
                            elif paused_action == KARAOKE_NEXT:
                                karaoke_style = (karaoke_style % len(KARAOKE_STYLE_NAMES)) + 1
                            elif paused_action == KARAOKE_TREATMENT_NEXT:
                                karaoke_treatment = (karaoke_treatment % len(KARAOKE_TREATMENT_NAMES)) + 1
                            elif paused_action == KARAOKE_FAVORITE_TOGGLE:
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
                        SEEK_BACK_15: "⏪", SEEK_FORWARD_15: "⏩",
                        SEEK_BACK_60: "⏮️", SEEK_FORWARD_60: "⏭️",
                    }[action]
                    show_status(position, indicator)
                    break
                sleeper(0.02)
            else:
                completed_position = position + max(
                    0.0, monotonic() - segment_started
                ) * speed
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
        self.assertEqual(VISUALIZER_MODE_FAVORITE, interpret_console_key("f"))
        self.assertEqual(COLOR_FAVORITE_TOGGLE, interpret_console_key("f", shift=True))
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
        self.assertEqual(VISUALIZER_MODE_FIRST, interpret_console_key("\x00", extended=";"))
        self.assertEqual(VISUALIZER_MODE_PREVIOUS, interpret_console_key("\x00", extended="<"))
        self.assertEqual(VISUALIZER_MODE_NEXT, interpret_console_key("\x00", extended="="))
        self.assertEqual(VISUALIZER_TREATMENT_PREVIOUS, interpret_console_key("\x00", extended=">"))
        self.assertEqual(VISUALIZER_TREATMENT_NEXT, interpret_console_key("\x00", extended="?"))
        self.assertEqual(
            DRCS_VISUALIZER_TOGGLE,
            interpret_console_key("v"),
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
            with mock.patch(__name__ + ".play_audio_file", return_value="completed") as player, mock.patch(
                __name__ + ".pause_playing_winamp", return_value=False
            ), mock.patch(__name__ + ".resume_winamp_if_paused_by_preview"), mock.patch(
                "random.choice", side_effect=lambda values: values[0]
            ), mock.patch(__name__ + ".load_playlist_resume", return_value=None), mock.patch(
                __name__ + ".clear_playlist_resume"
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
        self.assertEqual(2, len(plain))
        self.assertEqual(2, len(ansi))
        self.assertIn("Artist: Example Artist", plain[0])
        self.assertIn("Album: Example Album", plain[1])
        self.assertEqual(10, plain[0].index(":"))
        self.assertEqual(plain[0].index(":"), plain[1].index(":"))
        self.assertEqual(plain[0].index("Example Artist"), plain[1].index("Example Album"))
        self.assertEqual(plain[0].index("Example Song"), plain[1].index("2026"))
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
            self.assertLess(first[2], 1.0)
            long_gap = [(0.0, None, "Held line"), (40.0, None, "Later line")]
            self.assertLess(lyric_at(long_gap, 16.0)[2], 1.0)
            self.assertIsNone(lyric_at(long_gap, 19.0))

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
            self.assertEqual(19, len(KARAOKE_STYLE_NAMES))
            self.assertEqual(5, len(KARAOKE_TREATMENT_NAMES))
            self.assertEqual(15, len(PROGRESS_STYLE_NAMES))
            self.assertNotEqual(
                visualizer_mode_heights(bytes(range(40)), 40, 1),
                visualizer_mode_heights(bytes(range(40)), 40, 30),
            )

    def test_karaoke_styles_and_color_treatments_are_independent(self) -> None:
        self.assertNotIn("🎵", _legacy_karaoke_text("ABEI", 46))
        self.assertNotIn("✨", _legacy_karaoke_text("ABEI", 46))
        self.assertIn("❤️", stylize_karaoke_text("all you need is love", 19))
        self.assertTrue(stylize_karaoke_text("ABC", 17))
        self.assertIn("\033[38;2;", colorize_karaoke_text("one two", 5))
        self.assertEqual(hashed_word_rgb("can't"), hashed_word_rgb("cant"))
        wide = "A🅰⭕❤️B"
        self.assertGreater(terminal_cell_width(wide), len(wide))
        self.assertEqual(12, terminal_cell_width(center_to_cells(wide, 12)))
        self.assertLessEqual(terminal_cell_width(truncate_to_cells(wide * 3, 10, "…")), 10)
        self.assertTrue(all(terminal_cell_width(line) <= 8 for line in wrap_to_cells(wide * 3, 8)))
        clipped_ansi = truncate_ansi_to_cells(BIG_OFF + "\033[2m" + wide * 5, 9)
        visible_ansi = ANSI_CSI_RE.sub("", clipped_ansi)
        self.assertLessEqual(terminal_cell_width(visible_ansi), 9)

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
        self.assertEqual("0.000", commands[0][-4])
        self.assertEqual("5.000", commands[1][-4])
        self.assertEqual("20.000", commands[2][-4])
        self.assertTrue(all(command[-2] == "100" for command in commands))
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


def main(argv: list[str] | None = None) -> int:
    """Run unit tests or preview the single supplied audio filename."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments in (["--unit-tests"], ["-t"]):
        return run_unit_tests()
    if not arguments or any(option in arguments for option in ("--help", "--usage", "-h", "-u")):
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
        usage_line("-l, --loop / -L, --no-loop", "loop the current track", "on")
        usage_line("-k, --karaoke / -K, --no-karaoke", "display available lyrics", "on")
        usage_line("-r, --random-file [directory]", "random file in one folder")
        usage_line("-R, --random-file-recursive [directory]", "random downward folder walk")
        usage_line("-p, --playlist FILE", "playlist; shuffled initially", "shuffle")
        usage_line("-b, --initial-blank-line / -B, --suppress-initial-blank-line", "leading blank line", "on")
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
        print("\n\033[94mRequired Claire library files:\033[0m")
        print("  \033[38;2;145;205;255mC:\\clairecjs_utils\\claire_progressbar.py\033[0m"
              "  \033[38;2;210;165;255mplaylist progress bars\033[0m")
        print("  \033[38;2;145;205;255mPython package: wcwidth (optional)\033[0m"
              "              \033[38;2;210;165;255mUnicode terminal-cell measurement\033[0m")
        print("\n\033[2;90mV toggles the DRCS visualizer;"
              " W toggles the SIXEL visualizer.\033[0m")
        print("\033[2;90mF2/F3: render type; F4/F5: amplitude treatment;"
              " F: favorite/unfavorite; *: favorite visualizers.\033[0m")
        print("\033[2;90mC/Shift+C: color; Shift+F: favorite color; Alt+C: favorite colors.\033[0m")
        print("\033[2;90mK/Shift+K: karaoke style; Ctrl+K: treatment; Ctrl+Alt+K: favorite pair; Alt+K: favorite pairs.\033[0m")
        print("\033[2;90mP/Shift+P: progress style; A: autoplay (enables shuffle).\033[0m")
        print("\033[2;90m2: stereo; 5: 5.1 expansion; 7: 7.1 expansion.\033[0m")
        return 0
    sixel_enabled = bool(ENABLE_SIXEL_VISUALIZER)
    drcs_enabled = bool(ENABLE_DRCS_VISUALIZER)
    fade_seconds = DEFAULT_VISUALIZER_FADE_SECONDS
    looping_enabled = True
    loop_option_explicit = False
    lyrics_enabled = True
    random_mode = ""
    playlist_argument: str | None = None
    initial_blank_line = True
    filenames: list[str] = []
    argument_index = 0
    while argument_index < len(arguments):
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
    if not random_mode and playlist_argument is None and len(filenames) != 1:
        print("💥 ERROR: Supply exactly one audio filename.", file=sys.stderr)
        print("Run play_audio_file.py --usage for options.")
        return 2
    winamp_paused_by_session = pause_playing_winamp()
    try:
        playlist_entries: list[Path] | None = None
        shuffle_state: list[bool] | None = None
        playlist_history: list[Path] = []
        playlist_played: set[Path] = set()
        visualizer_mode_state = [load_favorite_visualizer_mode()]
        color_style_state = [1]
        karaoke_style_state = [1]
        karaoke_treatment_state = [1]
        progress_style_state = [1]
        autoplay_state = [False]
        output_channels_state = [2]
        playlist_path: Path | None = None
        initial_resume_position = 0.0
        playback_position_state = [0.0]
        autoplay_seen: dict[Path, set[Path]] = {}
        if playlist_argument is not None:
            playlist_path = Path(playlist_argument).absolute()
            playlist_entries = load_playlist(playlist_path)
            shuffle_state = [True]
            saved_resume = load_playlist_resume(playlist_path)
            resumed_entry = None
            if saved_resume is not None:
                saved_track, initial_resume_position = saved_resume
                resumed_entry = next(
                    (entry for entry in playlist_entries if entry.resolve() == saved_track.resolve()),
                    None,
                )
            current_audio = resumed_entry or random.choice(playlist_entries)
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
        if shuffle_state is None:
            shuffle_state = [False]
        while True:
            playback_position_state[0] = initial_resume_position
            result = play_audio_file(
                current_audio,
                sixel_visualizer=sixel_enabled,
                drcs_visualizer=drcs_enabled,
                visualizer_fade_seconds=fade_seconds,
                looping=looping_enabled and not autoplay_state[0],
                lyrics_display=lyrics_enabled,
                shuffle_state=shuffle_state,
                visualizer_mode_state=visualizer_mode_state,
                color_style_state=color_style_state,
                karaoke_style_state=karaoke_style_state,
                karaoke_treatment_state=karaoke_treatment_state,
                progress_style_state=progress_style_state,
                autoplay_state=autoplay_state,
                output_channels_state=output_channels_state,
                initial_position=initial_resume_position,
                playback_position_state=playback_position_state,
                initial_blank_line=initial_blank_line,
                manage_winamp=False,
                guard_winamp=True,
            )
            initial_resume_position = 0.0
            initial_blank_line = False
            if playlist_entries is not None:
                playlist_played.add(current_audio.resolve())
                playlist_history.append(current_audio)
                if result == "stopped":
                    if playlist_path is not None:
                        save_playlist_resume(
                            playlist_path, current_audio, playback_position_state[0]
                        )
                    break
                remaining = [
                    entry for entry in playlist_entries
                    if entry.resolve() not in playlist_played
                ]
                if not remaining:
                    if playlist_path is not None:
                        clear_playlist_resume(playlist_path)
                    break
                previous_directory = current_audio.parent.resolve()
                if result == PREVIOUS_FILE and len(playlist_history) > 1:
                    current_audio = playlist_history[-2]
                    playlist_played.discard(current_audio.resolve())
                elif shuffle_state and shuffle_state[0]:
                    current_audio = random.choice(remaining)
                else:
                    current_index = playlist_entries.index(current_audio)
                    current_audio = next(
                        playlist_entries[(current_index + step) % len(playlist_entries)]
                        for step in range(1, len(playlist_entries) + 1)
                        if playlist_entries[(current_index + step) % len(playlist_entries)].resolve()
                        not in playlist_played
                    )
                if current_audio.parent.resolve() != previous_directory:
                    write_console(
                        "\033[?25l\033[38;2;140;210;255m📁  Folder:\033[0m \033[38;2;140;210;255m"
                        f"{current_audio.parent}\033[0m\n"
                    )
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
                    write_console(
                        "\033[?25l\033[38;2;140;210;255m📁  Folder:\033[0m \033[38;2;140;210;255m"
                        f"{current_audio.parent}\033[0m\n"
                    )
                continue
            if result not in NAVIGATION_ACTIONS:
                break
            previous_directory = current_audio.parent.resolve()
            current_audio = navigate_audio_path(current_audio, result)
            if current_audio.parent.resolve() != previous_directory:
                write_console(
                    "\033[?25l\033[38;2;140;210;255m📁  Folder:\033[0m \033[38;2;140;210;255m"
                    f"{current_audio.parent}\033[0m\n"
                )
    except KeyboardInterrupt:
        print("\n⏹️ Playback stopped.")
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        resume_winamp_if_paused_by_preview(winamp_paused_by_session)
        write_console("\033[?25h")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
