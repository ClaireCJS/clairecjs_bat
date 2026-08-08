#!/usr/bin/env python3
"""claire_lastfm
===================

Claire's Last.fm helper can be imported by PAFPlayer or run directly from a
command prompt.  The original job of this module is scrobbling one track.  V2
added a second, deliberately long-running maintenance mode that walks the user's
Last.fm recently-played history and backfills PAFPlayer's local latest-played
SQLite database.

Requirements
------------
* Python 3.8+
* ``requests`` (``pip install requests``)

Configuration
-------------
The module expects a Last.fm API key and secret from either these environment
variables::

    LASTFM_API_KEY
    LASTFM_API_SECRET

or ``bat/private.env`` containing::

    lastfm_api_key=...
    lastfm_api_secret=...

The optional ``LASTFM_USERNAME`` or ``PAFPLAYER_LASTFM_USERNAME`` environment
variable can pre-seed the account name used by history crawling.  Otherwise the crawler
tries the saved username, then the authenticated Last.fm session, and finally
asks interactively.  Once entered/discovered, the username is saved in
``~/.claire_lastfm_username`` for later PAFPlayer/claire_lastfm runs.

Authentication flow
-------------------
The first scrobble opens Last.fm authorization in a browser if no session key
exists.  The resulting session key remains stored as plaintext in
``~/.claire_lastfm_session`` for backward compatibility with older copies of
this helper.  The username is stored separately.

Command-line scrobbling
-----------------------
::

    python claire_lastfm.py --artist "Artist" --title "Song" --album "Album"

Recently-played history crawl
-----------------------------
::

    python claire_lastfm.py --crawl-lastfm-recently-played-pages

This mode uses Last.fm's official ``user.getRecentTracks`` web-service pages at
50 scrobbles per page.  Before fetching history it asks which Last.fm page to
start on; pressing Enter means page 1.  This makes a stopped crawl resumable
without re-requesting all newer pages.  From the chosen page it continues
backward through every page Last.fm reports.  The persistent page-progress bar
shows an ETA derived from the mean duration of up to the 50 most recently
completed pages; before any page has completed, ETA is shown as unknown.  Processing newest-first within the
selected range is intentional: as soon as a track identity has been seen, older
occurrences of that same identity cannot improve a latest-played database and
are therefore cheap to bypass.  Starting later than page 1 is safe because the
complete local PAFPlayer history is still loaded before crawling and every SQL
write is guarded so an older web timestamp cannot replace a newer local one.

Before the first web page is processed, the complete PAFPlayer table is read
into memory.  The crawler compares every dated Last.fm scrobble against that
snapshot and only writes when the web timestamp is newer.  SQL uses ``MAX`` as
an additional guard, so even if another PAFPlayer instance writes concurrently,
an older web play cannot replace a newer local play.

PAFPlayer's table is filename-first and intentionally does not retain full
paths.  A Last.fm page has artist/title/date but no local filename or duration.
For an already-known filename+artist/title identity, the crawler updates every matching
stored duration row.  For a history-only track that has no filename row at all,
the crawler seeds one filename-fast-path row using the normalized Last.fm title and a
sentinel duration of 1 second.  This is useful because PAFPlayer treats a sole
filename candidate as authoritative without probing metadata.  When PAFPlayer
later actually plays that file, its real duration/tag row is newer and naturally
supersedes the historical seed.  If a filename is already ambiguous and the
artist/title does not match an existing row, the crawler refuses to invent an identity;
that avoids turning a filename collision into a false history match.

The history database location is the same location PAFPlayer uses.  An explicit
``PLAY_AUDIO_FILE_HISTORY_DB`` environment variable wins.  Otherwise this helper
looks for ``play_audio_file.py`` in the current directory, ``C:\\bat``, its own
directory and PATH directories, then uses/creates
``play_audio_file-play-history.sqlite3`` beside that PAFPlayer script.

Display while crawling
----------------------
Each page keeps a two-line live display.  The first line is rewritten in place,
for example::

    Processing page 2: [ 63 songs /  34 bands] [total: 106 songs /  44 bands] [total time:0m07s] [going back to:2024-12-31] [Metallica] [L7] [KMFDM]

The song/band counters are minimum-width 3 so columns line up through 999; four
or more digits are allowed to expand naturally.  Every changing numeric field
is recolored on each refresh.  There is intentionally no ``25/50`` per-track
counter and no per-page elapsed-time field: Last.fm pages are fast enough that
those values add visual noise without useful information.

The ``going back to`` field is the oldest completed-play date encountered so
far in this run.  After it, the crawler uses the actual console width to append
a random sample of artist names already encountered; each sampled artist gets
its own color and only complete ``[Artist]`` blocks that fit before the right
edge are printed.

The second line is a rainbow page-position bar for the *entire Last.fm page
range*, not for tracks within a page.  Its position is simply ``current page /
total Last.fm pages``.  It stays completely fixed while all tracks on one page
are checked and moves only when crawling advances to another page.  When a page
completes its summary is left on screen and the next page's summary takes over
the live line below it.

Stopping is intentionally difficult because a multi-hour crawl is expensive to
restart.  Ctrl+C, Ctrl+Break, Q, X and Ctrl+W count as quit requests.  Three quit
requests are required before the crawler stops.  The first two only warn how
many confirmations remain.  Normal completion, a three-confirmation stop, and
fatal errors all leave already-committed page work intact.

Logging
-------
Every completed page is appended to ``lastfm-webpage-import.log`` beside this
script.  The log is deliberately plain text (Unicode decoration is cosmetic,
not structured logging).  Each page contains a divider, an emojified page
header, an ``* Updates:`` section, and a summary containing checked count,
updated database rows/bands, elapsed page time (for the audit log only) and total elapsed time.

Library use
-----------
::

    from claire_lastfm import scrobble_track
    scrobble_track("Artist", "Song", album="Album")
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import shutil
import signal
import sqlite3
import sys
import time
import unicodedata
import webbrowser
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path, PureWindowsPath
from typing import Dict, Iterable, Optional, Sequence

try:
    import requests  # type: ignore
except ImportError as exc:  # pragma: no cover - dependency failure is environment-specific
    raise RuntimeError(
        "The 'requests' library is required for Last.fm scrobbling/history crawling. "
        "Install it with 'pip install requests' and retry."
    ) from exc

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------
API_URL = "https://ws.audioscrobbler.com/2.0/"
REQUEST_TOKEN_URL = API_URL
SESSION_KEY_FILE = Path.home() / ".claire_lastfm_session"
USERNAME_FILE = Path.home() / ".claire_lastfm_username"
WEB_IMPORT_LOG_NAME = "lastfm-webpage-import.log"
PAF_HISTORY_DB_NAME = "play_audio_file-play-history.sqlite3"
RECENT_TRACKS_PAGE_SIZE = 50
WEB_HISTORY_SENTINEL_DURATION = 1
REQUEST_TIMEOUT_SECONDS = 30
REQUEST_RETRIES = 4

# Audio suffixes are used only for best-effort path display.  The crawler does
# not recursively index the music library: PAFPlayer's DB intentionally stores
# filename identities, so guessing a path would be more dangerous than useful.
AUDIO_SUFFIXES = {
    ".mp3", ".flac", ".m4a", ".aac", ".ogg", ".opus", ".wav", ".wma", ".ape",
}


def _get_env_var(name: str) -> str:
    """Return a required environment value.

    Motivation: keep credential failures explicit and centralized instead of
    letting a missing key surface later as a confusing Last.fm HTTP/API error.
    """
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable {name!r} is required but not set.")
    return value


def _load_api_credentials() -> tuple[str, str]:
    """Load the Last.fm API key/secret from environment or ``bat/private.env``.

    Motivation: the helper is used both from a checked-out repo and as a loose
    utility file, so secrets need a predictable non-source-code location in
    both workflows.
    """
    env_key = os.getenv("LASTFM_API_KEY")
    env_secret = os.getenv("LASTFM_API_SECRET")
    if env_key and env_secret:
        return env_key, env_secret

    candidate_paths = [
        Path("bat/private.env"),
        Path(__file__).resolve().parent / "bat" / "private.env",
        Path(__file__).resolve().parent.parent / "bat" / "private.env",
    ]
    for private_path in candidate_paths:
        if not private_path.exists():
            continue
        key: Optional[str] = None
        secret: Optional[str] = None
        for line in private_path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.lower().startswith("lastfm_api_key="):
                key = line.split("=", 1)[1].strip()
            elif line.lower().startswith("lastfm_api_secret="):
                secret = line.split("=", 1)[1].strip()
        if key and secret:
            return key, secret

    raise RuntimeError(
        "Last.fm API credentials not found. Set LASTFM_API_KEY and "
        "LASTFM_API_SECRET or provide bat/private.env."
    )


# Load credentials once so library calls fail early, matching the original helper.
API_KEY, API_SECRET = _load_api_credentials()


def _api_signature(params: Dict[str, str]) -> str:
    """Return the Last.fm MD5 request signature for ``params``.

    Motivation: authenticated Last.fm calls require an exact deterministic
    key/value ordering; one shared implementation prevents subtle signature
    drift between scrobbling and username discovery.
    """
    concatenated = "".join(f"{key}{value}" for key, value in sorted(params.items()))
    concatenated += API_SECRET
    return hashlib.md5(concatenated.encode("utf-8")).hexdigest()


def _request_json(method: str, *, params: dict[str, str], post: bool = False) -> dict:
    """Perform one Last.fm JSON request with bounded retry/backoff.

    Motivation: a history crawl may make thousands of page requests, so a
    transient 429/5xx/network hiccup should not destroy hours of completed work.
    """
    payload = dict(params)
    payload["method"] = method
    payload["api_key"] = API_KEY
    payload["format"] = "json"
    last_error: BaseException | None = None
    for attempt in range(REQUEST_RETRIES):
        try:
            if post:
                response = requests.post(API_URL, data=payload, timeout=REQUEST_TIMEOUT_SECONDS)
            else:
                response = requests.get(API_URL, params=payload, timeout=REQUEST_TIMEOUT_SECONDS)
            if response.status_code == 429 or response.status_code >= 500:
                raise requests.HTTPError(
                    f"Last.fm returned HTTP {response.status_code}", response=response
                )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict) and data.get("error"):
                code = data.get("error")
                message = data.get("message", "unknown Last.fm API error")
                if code in (16, 29) and attempt + 1 < REQUEST_RETRIES:
                    raise RuntimeError(f"temporary Last.fm API error {code}: {message}")
                raise RuntimeError(f"Last.fm API error {code}: {message}")
            if not isinstance(data, dict):
                raise RuntimeError("Last.fm returned a non-object JSON response")
            return data
        except (requests.RequestException, ValueError, RuntimeError) as exc:
            last_error = exc
            if attempt + 1 >= REQUEST_RETRIES:
                break
            time.sleep(min(8.0, 1.0 * (2 ** attempt)))
    raise RuntimeError(f"Last.fm request failed after {REQUEST_RETRIES} attempts: {last_error}")


class LastFMClient:
    """Small Last.fm client for authentication and scrobbling.

    Motivation: PAFPlayer needs one importable object that owns session-key
    persistence while standalone CLI modes can reuse the same credentials.
    """

    def __init__(self, session_file: Path | str = SESSION_KEY_FILE):
        """Load an existing session if present.

        Motivation: normal scrobbles must remain non-interactive after the user
        has authorized this application once.
        """
        self.session_file = Path(session_file)
        self.session_key: Optional[str] = None
        self.username: Optional[str] = None
        self._load_session()

    def _load_session(self) -> None:
        """Read the legacy plaintext session-key file.

        Motivation: V2 deliberately preserves the old on-disk format so older
        PAFPlayer/helper copies do not break when sharing the same home folder.
        """
        if self.session_file.exists():
            self.session_key = self.session_file.read_text(encoding="utf-8").strip() or None

    def _save_session(self) -> None:
        """Persist only the Last.fm session key.

        Motivation: keeping username metadata in a separate file avoids making
        the longstanding session-key file incompatible with older releases.
        """
        if self.session_key:
            self.session_file.write_text(self.session_key, encoding="utf-8")

    def _ensure_authenticated(self) -> None:
        """Create and save a session only when no usable session is loaded.

        Motivation: scrobbling is often called from live playback, so browser
        authentication must never repeat unnecessarily.
        """
        if self.session_key:
            return
        self.session_key = self._authenticate()
        self._save_session()

    def _authenticate(self) -> str:
        """Run Last.fm desktop authentication and return the new session key.

        Motivation: interactive browser authorization keeps the API secret out
        of user prompts and is the supported flow for this desktop helper.
        """
        token_params = {"method": "auth.getToken", "api_key": API_KEY}
        token_params["api_sig"] = _api_signature(token_params)
        token_params["format"] = "json"
        response = requests.get(API_URL, params=token_params, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        token = response.json()["token"]

        auth_url = f"https://www.last.fm/api/auth/?api_key={API_KEY}&token={token}"
        print("Opening browser for Last.fm authentication…")
        webbrowser.open(auth_url)

        timeout_seconds = 300
        interval = 2
        elapsed = 0
        while elapsed < timeout_seconds:
            time.sleep(interval)
            elapsed += interval
            poll_params = {"method": "auth.getSession", "api_key": API_KEY, "token": token}
            poll_params["api_sig"] = _api_signature(poll_params)
            poll_params["format"] = "json"
            poll_response = requests.get(
                API_URL, params=poll_params, timeout=REQUEST_TIMEOUT_SECONDS
            )
            try:
                data = poll_response.json()
            except ValueError:
                continue
            if "session" in data:
                session = data["session"]
                discovered_name = str(session.get("name") or "").strip()
                if discovered_name:
                    self.username = discovered_name
                    _save_lastfm_username(discovered_name)
                return str(session["key"])
            if data.get("error") not in (None, 14):
                raise RuntimeError(f"Authentication error: {data.get('message', 'unknown')}")
        raise RuntimeError(
            "Authentication timed out. Please ensure you authorized the application "
            "in the opened browser."
        )

    def discover_authenticated_username(self) -> Optional[str]:
        """Ask Last.fm which user owns the saved authenticated session.

        Motivation: the history crawler should not prompt for a username when
        PAFPlayer already has enough Last.fm authentication state to discover it.
        Failure is intentionally non-fatal because public history only needs a
        username, which can still come from env/file/prompt.
        """
        if self.username:
            return self.username
        if not self.session_key:
            return None
        signed = {
            "method": "user.getInfo",
            "api_key": API_KEY,
            "sk": self.session_key,
        }
        signed["api_sig"] = _api_signature(signed)
        signed["format"] = "json"
        try:
            response = requests.get(API_URL, params=signed, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
            data = response.json()
            name = str(data.get("user", {}).get("name") or "").strip()
            if name:
                self.username = name
                _save_lastfm_username(name)
                return name
        except (requests.RequestException, ValueError, AttributeError, TypeError):
            pass
        return None

    def scrobble(
        self,
        artist: str,
        title: str,
        album: Optional[str] = None,
        duration: Optional[int] = None,
        track_number: Optional[int] = None,
        timestamp: Optional[int] = None,
    ) -> Dict:
        """Submit one scrobble and return Last.fm's JSON response.

        Motivation: this is the original public behavior used by PAFPlayer; V2
        keeps its call signature stable while adding independent crawl features.
        """
        self._ensure_authenticated()
        if not self.session_key:
            raise RuntimeError("Failed to obtain session key")

        params = {
            "method": "track.scrobble",
            "api_key": API_KEY,
            "sk": self.session_key,
            "artist": artist,
            "track": title,
            "timestamp": str(timestamp or int(time.time())),
        }
        if album:
            params["album"] = album
        if duration:
            params["duration"] = str(duration)
        if track_number:
            params["trackNumber"] = str(track_number)
        params["api_sig"] = _api_signature(params)
        params["format"] = "json"

        response = requests.post(API_URL, data=params, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()


def scrobble_track(
    artist: str,
    title: str,
    album: Optional[str] = None,
    duration: Optional[int] = None,
    track_number: Optional[int] = None,
    timestamp: Optional[int] = None,
) -> Dict:
    """Convenience wrapper used by PAFPlayer and other Python callers.

    Motivation: callers should not need to construct/manage a client just to
    submit the common single-track scrobble operation.
    """
    return LastFMClient().scrobble(artist, title, album, duration, track_number, timestamp)


def _save_lastfm_username(username: str) -> None:
    """Persist the validated account name for future crawl runs.

    Motivation: asking for the same username on every multi-hour crawl is
    needless friction, and a separate file is backward compatible.
    """
    cleaned = username.strip()
    if cleaned:
        USERNAME_FILE.write_text(cleaned + "\n", encoding="utf-8")


def _resolve_lastfm_username(explicit: Optional[str] = None) -> str:
    """Find the Last.fm username from CLI/env/cache/session, then prompt.

    Motivation: "ask only if PAFPlayer doesn't know" requires several cheap
    sources to be exhausted before making the crawl interactive.
    """
    candidates = [
        explicit,
        os.getenv("PAFPLAYER_LASTFM_USERNAME"),
        os.getenv("LASTFM_USERNAME"),
    ]
    if USERNAME_FILE.exists():
        try:
            candidates.append(USERNAME_FILE.read_text(encoding="utf-8").strip())
        except OSError:
            pass
    for candidate in candidates:
        if candidate and candidate.strip():
            name = candidate.strip()
            _save_lastfm_username(name)
            return name

    discovered = LastFMClient().discover_authenticated_username()
    if discovered:
        return discovered

    if not sys.stdin.isatty():
        raise RuntimeError(
            "Last.fm username is unknown and stdin is not interactive. Set "
            "LASTFM_USERNAME or PAFPLAYER_LASTFM_USERNAME."
        )
    while True:
        name = input("Last.fm username for PAFPlayer history crawl: ").strip()
        if name:
            _save_lastfm_username(name)
            return name
        print("A Last.fm username is required.", file=sys.stderr)


def _normalize_history_text(value: str) -> str:
    """Match PAFPlayer's NFKC/whitespace/casefold text normalization.

    Motivation: a crawler identity must compare byte-for-byte with the keys the
    player itself writes, or the backfilled history would silently miss tracks.
    """
    normalized = unicodedata.normalize("NFKC", str(value or ""))
    return re.sub(r"\s+", " ", normalized).strip().casefold()


def _history_filename_key(value: str | os.PathLike[str] | Path) -> str:
    """Match PAFPlayer's extension/track-number-stripped basename key.

    Motivation: Last.fm supplies a title rather than a Windows path, but common
    local filenames such as ``01_Blackened.mp3`` normalize to the same key as
    the Last.fm title ``Blackened``.  The Last.fm title is normalized directly
    (rather than treated as a filename) so titles containing dots, such as
    ``Mr. Brightside``, are not accidentally mistaken for file extensions.
    """
    if isinstance(value, Path):
        name = value.name
    else:
        raw = str(value or "")
        name = PureWindowsPath(raw).name if "\\" in raw else Path(raw).name
    stem = PureWindowsPath(name).stem
    stem = re.sub(r"^(?:\s*\d{1,3}\s*[-_. ]+\s*)+", "", stem)
    return _normalize_history_text(stem)


def _history_tag_key(artist: str, title: str) -> str:
    """Return PAFPlayer's normalized ``artist\x1ftitle`` identity.

    Motivation: filename collisions exist, so artist/title is the second half
    of the player-compatible identity used to avoid cross-song contamination.
    """
    return "\x1f".join((_normalize_history_text(artist), _normalize_history_text(title)))


def _candidate_paf_script_paths() -> list[Path]:
    """Return likely PAFPlayer script locations in priority order.

    Motivation: ``claire_lastfm.py`` commonly lives in ``C:\\clairecjs_utils``
    while PAFPlayer itself lives in ``C:\\bat``; assuming the DB sits beside
    this helper would therefore update the wrong file.
    """
    candidates: list[Path] = [
        Path.cwd() / "play_audio_file.py",
        Path(r"C:\bat\play_audio_file.py"),
        Path(__file__).resolve().with_name("play_audio_file.py"),
        Path(__file__).resolve().parent.parent / "play_audio_file.py",
    ]
    which = shutil.which("play_audio_file.py")
    if which:
        candidates.append(Path(which))
    for directory in os.getenv("PATH", "").split(os.pathsep):
        if directory:
            candidates.append(Path(directory) / "play_audio_file.py")

    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = os.path.normcase(os.path.abspath(str(candidate)))
        if key not in seen:
            seen.add(key)
            unique.append(candidate)
    return unique


def _paf_history_database_path() -> Path:
    """Resolve the same SQLite path PAFPlayer uses.

    Motivation: the crawler is useful only if it changes PAFPlayer's actual
    history database; explicit override and PAF script discovery prevent a
    misleading shadow database beside the helper.
    """
    override = os.getenv("PLAY_AUDIO_FILE_HISTORY_DB")
    if override:
        return Path(override)

    script_candidates = _candidate_paf_script_paths()
    for script in script_candidates:
        if script.is_file():
            return script.resolve().with_name(PAF_HISTORY_DB_NAME)

    # If the script cannot be located, prefer an already-existing known DB.
    db_candidates = [
        Path.cwd() / PAF_HISTORY_DB_NAME,
        Path(r"C:\bat") / PAF_HISTORY_DB_NAME,
        Path(__file__).resolve().with_name(PAF_HISTORY_DB_NAME),
    ]
    existing = [path for path in db_candidates if path.is_file()]
    if existing:
        return max(existing, key=lambda path: path.stat().st_mtime)

    raise RuntimeError(
        "Could not locate PAFPlayer/play_audio_file.py or its history database. "
        "Set PLAY_AUDIO_FILE_HISTORY_DB to the exact play_audio_file-play-history.sqlite3 path."
    )


def _create_history_table(database: sqlite3.Connection) -> None:
    """Create PAFPlayer's current filename-first history table.

    Motivation: the crawler may be the first component to initialize history on
    a new installation, so it must be able to create the exact current schema.
    """
    database.execute(
        """CREATE TABLE played_tracks_recent (
            filename TEXT NOT NULL,
            duration_seconds INTEGER NOT NULL,
            tag TEXT NOT NULL,
            played_at REAL NOT NULL,
            PRIMARY KEY (filename, duration_seconds, tag)
        ) WITHOUT ROWID"""
    )


def _ensure_history_schema(database: sqlite3.Connection) -> None:
    """Migrate compatible older PAF history layouts to the current schema.

    Motivation: history backfill can be run after an older PAFPlayer release;
    matching PAFPlayer's own migration behavior avoids either data loss or SQL
    failures when the column order/key changed over time.
    """
    row = database.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='played_tracks_recent'"
    ).fetchone()
    if row is None:
        _create_history_table(database)
        return

    columns = [
        str(info[1])
        for info in database.execute("PRAGMA table_info(played_tracks_recent)").fetchall()
    ]
    expected = ["filename", "duration_seconds", "tag", "played_at"]
    if columns == expected:
        return

    if set(expected).issubset(columns):
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
            filename_key = _history_filename_key(str(filename))
            try:
                duration = int(duration_seconds)
                when = float(played_at)
            except (TypeError, ValueError):
                continue
            tag_text = str(tag)
            if not filename_key or duration <= 0 or not tag_text or tag_text == "\x1f":
                continue
            key = (filename_key, duration, tag_text)
            normalized[key] = max(normalized.get(key, float("-inf")), when)
        database.executemany(
            "INSERT INTO played_tracks_recent_new(filename, duration_seconds, tag, played_at) "
            "VALUES (?, ?, ?, ?)",
            [(filename, duration, tag, when) for (filename, duration, tag), when in normalized.items()],
        )
        database.execute("DROP TABLE played_tracks_recent")
        database.execute("ALTER TABLE played_tracks_recent_new RENAME TO played_tracks_recent")
        return

    # Preserve an old duration+tag-only table rather than pretending its missing
    # filenames can be reconstructed.  This mirrors PAFPlayer's safe migration.
    suffix = int(time.time())
    database.execute(
        f'ALTER TABLE played_tracks_recent RENAME TO "played_tracks_recent_backup_{suffix}"'
    )
    _create_history_table(database)


def _open_history_database() -> tuple[sqlite3.Connection, Path]:
    """Open PAFPlayer history with WAL/safe schema setup.

    Motivation: page commits should coexist with a live PAFPlayer process and
    remain durable without forcing full synchronous disk flushes on every row.
    """
    path = _paf_history_database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    database = sqlite3.connect(path, timeout=30.0)
    database.execute("PRAGMA journal_mode=WAL")
    database.execute("PRAGMA synchronous=NORMAL")
    _ensure_history_schema(database)
    database.execute("DROP INDEX IF EXISTS played_tracks_recent_tag_duration_idx")
    database.execute("DROP INDEX IF EXISTS played_tracks_recent_filename_played_idx")
    database.commit()
    return database, path


@dataclass
class HistoryMemory:
    """In-memory mirror of only the fields the crawler needs for fast skipping.

    Motivation: loading the compact table once avoids a SQLite SELECT for each
    scrobble across potentially hundreds of thousands of Last.fm history rows.
    """

    rows_by_filename: dict[str, list[tuple[int, str, float]]] = field(default_factory=dict)

    @classmethod
    def from_database(cls, database: sqlite3.Connection) -> "HistoryMemory":
        """Read the whole current history table into filename buckets.

        Motivation: page 1 is newest, so the memory map can be updated as writes
        happen and older pages then become pure in-memory skip checks.
        """
        memory = cls()
        for filename, duration, tag, played_at in database.execute(
            "SELECT filename, duration_seconds, tag, played_at FROM played_tracks_recent"
        ):
            memory.rows_by_filename.setdefault(str(filename), []).append(
                (int(duration), str(tag), float(played_at))
            )
        return memory

    def matching_rows(self, filename: str, tag: str) -> list[tuple[int, str, float]]:
        """Return rows with both the filename and normalized artist/title tag.

        Motivation: matching tag rows can be updated safely even when a filename
        has several real duration variants.
        """
        return [row for row in self.rows_by_filename.get(filename, []) if row[1] == tag]

    def max_matching_time(self, filename: str, tag: str) -> float:
        """Return the newest stored timestamp for this web identity.

        Motivation: this is the core cheap test that bypasses any database write
        when PAFPlayer already knows an equal/newer play.
        """
        return max((row[2] for row in self.matching_rows(filename, tag)), default=0.0)

    def update_matching_times(self, filename: str, tag: str, played_at: float) -> None:
        """Refresh all matching in-memory rows after SQL has been updated.

        Motivation: later/older pages must see writes made earlier in this same
        process without re-reading SQLite.
        """
        rows = self.rows_by_filename.get(filename, [])
        self.rows_by_filename[filename] = [
            (duration, stored_tag, max(stored_time, played_at) if stored_tag == tag else stored_time)
            for duration, stored_tag, stored_time in rows
        ]

    def seed(self, filename: str, tag: str, played_at: float) -> None:
        """Add one history-only sentinel identity to memory.

        Motivation: an old Last.fm play for a filename PAF has never seen should
        affect shuffle ordering immediately without pretending Last.fm supplied
        a real local duration.
        """
        self.rows_by_filename.setdefault(filename, []).append(
            (WEB_HISTORY_SENTINEL_DURATION, tag, played_at)
        )


@dataclass(frozen=True)
class RecentScrobble:
    """Minimal normalized representation of one dated Last.fm page row.

    Motivation: page parsing, DB comparison and display/logging should exchange
    one stable shape rather than passing raw Last.fm JSON dictionaries around.
    """

    artist: str
    title: str
    album: str
    timestamp: int

    @property
    def filename_key(self) -> str:
        """Derive PAFPlayer's fast filename identity from the Last.fm title.

        Motivation: the web service does not expose local file paths.
        """
        return _normalize_history_text(self.title)

    @property
    def tag_key(self) -> str:
        """Derive PAFPlayer's artist/title disambiguation identity.

        Motivation: normalized tags protect against filename collisions.
        """
        return _history_tag_key(self.artist, self.title)


def _artist_name(track: dict) -> str:
    """Extract artist text across Last.fm's two common JSON shapes.

    Motivation: API responses have historically represented artist either as a
    ``#text`` dict or a nested name, so defensive parsing keeps old/new payloads
    crawlable.
    """
    artist = track.get("artist", {})
    if isinstance(artist, dict):
        return str(artist.get("#text") or artist.get("name") or "").strip()
    return str(artist or "").strip()


def _album_name(track: dict) -> str:
    """Extract album text without making album presence mandatory.

    Motivation: album is useful context but PAF history identity is artist/title,
    and many scrobbles legitimately omit album metadata.
    """
    album = track.get("album", {})
    if isinstance(album, dict):
        return str(album.get("#text") or album.get("name") or "").strip()
    return str(album or "").strip()


def _parse_recent_scrobbles(payload: dict) -> tuple[list[RecentScrobble], int, int]:
    """Parse one ``user.getRecentTracks`` payload and pagination metadata.

    Motivation: now-playing entries have no historical timestamp and must never
    be backfilled as though they were completed past plays.
    """
    recent = payload.get("recenttracks", {})
    if not isinstance(recent, dict):
        raise RuntimeError("Last.fm response did not contain recenttracks")
    attributes = recent.get("@attr", {}) if isinstance(recent.get("@attr", {}), dict) else {}
    try:
        page = int(attributes.get("page", 1))
    except (TypeError, ValueError):
        page = 1
    try:
        total_pages = max(1, int(attributes.get("totalPages", 1)))
    except (TypeError, ValueError):
        total_pages = 1

    raw_tracks = recent.get("track", [])
    if isinstance(raw_tracks, dict):
        raw_tracks = [raw_tracks]
    if not isinstance(raw_tracks, list):
        raw_tracks = []

    parsed: list[RecentScrobble] = []
    for track in raw_tracks:
        if not isinstance(track, dict):
            continue
        date = track.get("date")
        if not isinstance(date, dict) or not date.get("uts"):
            continue  # current now-playing row, not a completed historical play
        try:
            timestamp = int(date["uts"])
        except (TypeError, ValueError):
            continue
        artist = _artist_name(track)
        title = str(track.get("name") or "").strip()
        if not artist or not title or timestamp <= 0:
            continue
        parsed.append(RecentScrobble(artist, title, _album_name(track), timestamp))
    return parsed, page, total_pages


def _fetch_recent_page(username: str, page: int) -> tuple[list[RecentScrobble], int]:
    """Fetch exactly one 50-item Last.fm recent-tracks page.

    Motivation: page-sized requests make progress/log sections correspond to
    the same units the user sees in Last.fm and bound recovery after failures.
    """
    payload = _request_json(
        "user.getRecentTracks",
        params={
            "user": username,
            "page": str(page),
            "limit": str(RECENT_TRACKS_PAGE_SIZE),
            "extended": "0",
        },
    )
    tracks, returned_page, total_pages = _parse_recent_scrobbles(payload)
    if returned_page != page:
        # Not fatal, but it is a strong signal if Last.fm ever changes paging.
        print(
            f"⚠ Last.fm returned page {returned_page} while page {page} was requested.",
            file=sys.stderr,
        )
    return tracks, total_pages


def _format_elapsed(seconds: float) -> str:
    """Format elapsed seconds as compact ``XmYYs``/``XhYYmZZs`` text.

    Motivation: the live display refreshes often, so stable compact time strings
    are easier to scan than verbose timedelta formatting.
    """
    whole = max(0, int(seconds))
    hours, remainder = divmod(whole, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}h{minutes:02d}m{secs:02d}s"
    return f"{minutes}m{secs:02d}s"


def _ansi_random_number(text: str) -> str:
    """Wrap one changing numeric field in a fresh bright 24-bit ANSI color.

    Motivation: Claire asked for every changing number to be visually distinct
    on every rewrite, while punctuation/labels remain stable anchors.
    """
    if not sys.stdout.isatty():
        return text
    rgb = tuple(random.randint(120, 255) for _ in range(3))
    return f"\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m{text}\033[0m"


def _colorize_elapsed(value: str) -> str:
    """Color each numeric run in a formatted elapsed-time string.

    Motivation: total elapsed time remains useful during a long crawl, and its
    changing digits should retain the same colorful PAFPlayer visual language.
    """
    return re.sub(r"\d+", lambda match: _ansi_random_number(match.group(0)), value)


def _ansi_random_text(text: str) -> str:
    """Color one non-numeric display token with a fresh bright ANSI color.

    Motivation: the trailing artist sampler is intentionally decorative and
    should make each sampled band visually distinct without coloring brackets.
    """
    if not sys.stdout.isatty():
        return text
    rgb = tuple(random.randint(120, 255) for _ in range(3))
    return f"\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m{text}\033[0m"


def _visible_len(text: str) -> int:
    """Return a conservative terminal-cell width after stripping ANSI escapes.

    Motivation: Windows terminals can wrap a line when Unicode characters occupy
    more display cells than ``len()`` suggests.  A wrapped status line destroys
    the crawler's two-row cursor model, so use ``wcwidth`` when available and
    fall back to ordinary character count only when that optional helper is not
    installed.
    """
    plain = re.sub(r"\x1b\[[0-9;]*m", "", text)
    try:
        from wcwidth import wcswidth
        measured = wcswidth(plain)
        if measured >= 0:
            return measured
    except Exception:
        pass
    return len(plain)


def _artist_sample_suffix(artists: Iterable[str], available_columns: int) -> str:
    """Build a random, individually-colored artist sample that fits exactly.

    Motivation: spare horizontal space is more useful as a lively glimpse of
    the artists being traversed than as padding.  Only whole ``[Artist]`` blocks
    are emitted so resizing a console cannot leave a chopped name at the edge.
    """
    if available_columns < 4:
        return ""
    choices = sorted({str(name).strip() for name in artists if str(name).strip()}, key=str.casefold)
    random.shuffle(choices)
    pieces: list[str] = []
    used = 0
    for artist in choices:
        plain = f" [{artist}]"
        width = _visible_len(plain)
        if used + width > available_columns:
            continue
        pieces.append(" [" + _ansi_random_text(artist) + "]")
        used += width
    return "".join(pieces)


def _crawler_summary_line(
    *,
    page: int,
    page_updates: int,
    page_bands: int,
    total_updates: int,
    total_bands: int,
    total_elapsed: float,
    oldest_timestamp: Optional[int],
    sampled_artists: Iterable[str],
) -> str:
    """Build the console-width-aware, colorized live crawler status line.

    Motivation: the useful live facts are database changes, total runtime, how
    far back in calendar time the crawl has reached, and representative artists.
    Per-track counts and per-page timing were removed because pages complete too
    quickly for those fields to justify their screen space.
    """
    oldest_date = "----------"
    if oldest_timestamp:
        oldest_date = datetime.fromtimestamp(oldest_timestamp).strftime("%Y-%m-%d")
    base = (
        f"Processing page {_ansi_random_number(str(page))}: "
        f"[{_ansi_random_number(f'{page_updates:3d}')} songs / "
        f"{_ansi_random_number(f'{page_bands:3d}')} bands] "
        f"[total: {_ansi_random_number(f'{total_updates:3d}')} songs / "
        f"{_ansi_random_number(f'{total_bands:3d}')} bands] "
        f"[total time:{_colorize_elapsed(_format_elapsed(total_elapsed))}] "
        f"[going back to:{oldest_date}]"
    )
    console_width = shutil.get_terminal_size((120, 24)).columns
    # Reserve one physical terminal cell. Some Windows console hosts auto-wrap
    # immediately when the final column is occupied, which would turn our one
    # logical status row into two physical rows and break ANSI cursor-up logic.
    safe_width = max(1, console_width - 1)
    available = max(0, safe_width - _visible_len(base))
    return base + _artist_sample_suffix(sampled_artists, available)


def _rainbow_bar(
    fraction: float,
    page: int,
    total_pages: int,
    width: Optional[int] = None,
    eta_seconds: Optional[float] = None,
) -> str:
    """Render a rainbow progress bar whose scale is the complete page history.

    Motivation: a 50-track page bar mostly measured network/CPU speed.  The
    meaningful progress question is how much of Last.fm's total paginated
    history has been traversed, so the bar is scaled to total pages instead.
    """
    fraction = min(1.0, max(0.0, float(fraction)))
    terminal_width = shutil.get_terminal_size((100, 24)).columns
    eta_text = f"  ETA:{_format_elapsed(eta_seconds)}" if eta_seconds is not None else "  ETA:--"
    suffix = f" page {page:,}/{max(1, total_pages):,}  {fraction * 100:5.1f}%{eta_text}"
    bar_width = width or max(10, terminal_width - len(suffix) - 3)
    filled = int(round(bar_width * fraction))
    empty = max(0, bar_width - filled)
    if sys.stdout.isatty():
        hue = fraction % 1.0
        import colorsys
        red, green, blue = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        rgb = (round(red * 255), round(green * 255), round(blue * 255))
        done = f"\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m{'█' * filled}\033[0m"
    else:
        done = "#" * filled
    rest = "░" * empty if sys.stdout.isatty() else "-" * empty
    return f"[{done}{rest}]{suffix}"


def _rolling_page_eta(page_times: Sequence[float], *, page: int, total_pages: int) -> Optional[float]:
    """Estimate crawl completion time from the most recent completed pages.

    Motivation: Last.fm page latency can change during a long crawl, so a
    recent rolling mean is more useful than extrapolating from the entire run.
    Up to the latest 50 completed pages are used; before the first page has
    completed the display intentionally shows an unknown ETA rather than a
    misleading guess.
    """
    recent = [max(0.0, float(value)) for value in page_times[-50:] if value >= 0]
    if not recent:
        return None
    remaining_pages = max(0, int(total_pages) - int(page))
    return (sum(recent) / len(recent)) * remaining_pages


class CrawlerDisplay:
    """Own the two-line in-place page display and cursor transitions.

    Motivation: page N+1 occupies page N's persistent progress-bar row while
    the completed summary remains visible above it; a fresh bar is then drawn on
    the new lower row. This gives the display a stable two-row live region without
    relying on track-level redraws.
    """

    def __init__(self) -> None:
        """Initialize display state without touching the terminal yet.

        Motivation: the first page should decide when live cursor output begins.
        """
        self.live = sys.stdout.isatty()
        self.started = False

    def start_page(
        self, summary: str, *, fraction: float, page: int, total_pages: int,
        eta_seconds: Optional[float] = None,
    ) -> None:
        """Place a new page summary where the prior bar was, then add a bar line.

        Motivation: this creates the requested vertical history of completed
        page summaries without leaving stale progress bars behind.
        """
        if self.live:
            if self.started:
                sys.stdout.write("\r\033[2K" + summary + "\n")
            else:
                sys.stdout.write(summary + "\n")
                self.started = True
            sys.stdout.write("\033[2K" + _rainbow_bar(fraction, page, total_pages, eta_seconds=eta_seconds))
            sys.stdout.flush()
        else:
            print(summary)
            self.started = True

    def refresh(
        self, summary: str, fraction: float, *, page: int, total_pages: int,
        eta_seconds: Optional[float] = None,
    ) -> None:
        """Rewrite summary and bar without scrolling the terminal.

        Motivation: long pages should communicate activity continuously while
        leaving only two live lines regardless of refresh count.
        """
        if self.live:
            sys.stdout.write("\r\033[1A\033[2K" + summary + "\n")
            sys.stdout.write("\033[2K" + _rainbow_bar(fraction, page, total_pages, eta_seconds=eta_seconds))
            sys.stdout.flush()

    def finish_page(
        self, summary: str, *, page: int, total_pages: int, fraction: float,
        eta_seconds: Optional[float] = None,
    ) -> None:
        """Freeze the page summary while deliberately leaving the bar visible.

        Motivation: the lower row is the crawler's persistent page-position
        indicator.  Older code redrew the bar and then immediately erased that
        same row with ``ESC[2K]``, making it appear to vanish between pages.
        Keeping the cursor on the resident bar lets ``start_page()`` overwrite
        that exact row with the next page summary and draw the new bar beneath
        it, so the lower row is never accidentally blanked.
        """
        if self.live:
            self.refresh(
                summary, fraction, page=page, total_pages=total_pages,
                eta_seconds=eta_seconds,
            )
            # IMPORTANT: do not clear this row. It remains the locked lower row
            # until start_page() intentionally replaces it for the next page.
            sys.stdout.flush()
        else:
            print(summary)

    def message(self, text: str) -> None:
        """Temporarily print a warning below/around the live display safely.

        Motivation: triple-quit confirmations must be visible without corrupting
        the ANSI cursor bookkeeping used by the page/status lines.
        """
        if self.live:
            sys.stdout.write("\r\033[2K" + text + "\n")
            sys.stdout.flush()
        else:
            print(text)

    def close(self) -> None:
        """Leave the cursor on a clean new line at final program exit.

        Motivation: an erased bar line without a trailing newline would make the
        shell prompt appear inside the crawler's display area.
        """
        if self.live and self.started:
            sys.stdout.write("\r\033[2K\n")
            sys.stdout.flush()


class QuitGuard:
    """Require three supported quit requests before ending a crawl.

    Motivation: a full history import can run for hours; one accidental Ctrl+C
    or Q should not discard the remaining crawl opportunity.
    """

    def __init__(self, display: CrawlerDisplay):
        """Create the guard and remember the display used for warnings.

        Motivation: signal handlers need a tiny state object they can safely
        update without raising KeyboardInterrupt on the first two requests.
        """
        self.display = display
        self.confirmations = 0
        self.stop_requested = False
        self._old_sigint = None
        self._old_sigbreak = None

    def __enter__(self) -> "QuitGuard":
        """Install Ctrl+C/Ctrl+Break handlers for the crawl's lifetime.

        Motivation: default Python signal behavior exits on the first interrupt,
        contrary to the requested three-confirmation safeguard.
        """
        self._old_sigint = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, self._signal_handler)
        if hasattr(signal, "SIGBREAK"):
            self._old_sigbreak = signal.getsignal(signal.SIGBREAK)  # type: ignore[attr-defined]
            signal.signal(signal.SIGBREAK, self._signal_handler)  # type: ignore[attr-defined]
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        """Restore prior handlers after the crawl.

        Motivation: imported/library use must not permanently change the host
        application's signal policy.
        """
        if self._old_sigint is not None:
            signal.signal(signal.SIGINT, self._old_sigint)
        if hasattr(signal, "SIGBREAK") and self._old_sigbreak is not None:
            signal.signal(signal.SIGBREAK, self._old_sigbreak)  # type: ignore[attr-defined]
        return False

    def _signal_handler(self, signum, frame) -> None:
        """Convert an interrupt signal into one of three required confirmations.

        Motivation: signal callbacks must not throw on confirmations 1/2, or
        requests would escape the guard as ordinary KeyboardInterrupt exceptions.
        """
        name = "Ctrl+Break" if hasattr(signal, "SIGBREAK") and signum == signal.SIGBREAK else "Ctrl+C"  # type: ignore[attr-defined]
        self.request(name)

    def request(self, source: str) -> None:
        """Record one quit key and stop only after the third request.

        Motivation: Q/X/Ctrl+W and signal-based keys should all obey exactly the
        same three-strike behavior.
        """
        if self.stop_requested:
            return
        self.confirmations += 1
        if self.confirmations >= 3:
            self.stop_requested = True
            self.display.message(f"🛑 Quit confirmed 3/3 by {source}; stopping after current safe point.")
        else:
            remaining = 3 - self.confirmations
            self.display.message(
                f"⚠ Quit request {self.confirmations}/3 ({source}). "
                f"Repeat a quit key {remaining} more time{'s' if remaining != 1 else ''} to stop."
            )

    def poll_console_keys(self) -> None:
        """Non-blockingly recognize PAF-style Q/X/Ctrl+W quit keys on Windows.

        Motivation: standalone crawling has no playback key loop, so without
        polling only signal-based quit keys would receive triple protection.
        """
        if os.name != "nt":
            return
        try:
            import msvcrt
        except ImportError:  # pragma: no cover
            return
        while msvcrt.kbhit():
            char = msvcrt.getwch()
            if char in ("q", "Q", "x", "X", "\x17"):
                label = "Ctrl+W" if char == "\x17" else char.upper()
                self.request(label)
            elif char in ("\x00", "\xe0") and msvcrt.kbhit():
                msvcrt.getwch()  # consume unrelated extended key sequence


@dataclass
class PageResult:
    """Counters and log lines produced while processing one Last.fm page.

    Motivation: display, logging and final totals need the same definition of
    "updated songs/bands" without recomputing page work.
    """

    checked: int = 0
    updated_rows: int = 0
    updated_bands: set[str] = field(default_factory=set)
    update_lines: list[str] = field(default_factory=list)


def _format_log_timestamp(timestamp: int) -> str:
    """Render a Last.fm Unix timestamp in the machine's local timezone.

    Motivation: page logs are for human audit and should match the user's local
    calendar rather than forcing mental UTC conversion.
    """
    return datetime.fromtimestamp(timestamp).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")


def _update_history_for_scrobble(
    database: sqlite3.Connection,
    memory: HistoryMemory,
    scrobble: RecentScrobble,
) -> tuple[int, list[str]]:
    """Apply one scrobble only if it improves PAFPlayer's latest-played time.

    Motivation: this function is the correctness boundary.  It combines the
    preloaded-memory fast skip, collision-safe sentinel seeding and SQL ``MAX``
    protection so web history can never move a track backward in time.
    """
    filename = scrobble.filename_key
    tag = scrobble.tag_key
    if not filename or not tag or tag == "\x1f":
        return 0, []
    when = float(scrobble.timestamp)

    matching = memory.matching_rows(filename, tag)
    if matching:
        newest = max(row[2] for row in matching)
        if newest >= when:
            return 0, []
        durations = sorted({row[0] for row in matching})
        database.executemany(
            """UPDATE played_tracks_recent
               SET played_at=MAX(played_at, ?)
               WHERE filename=? AND duration_seconds=? AND tag=?""",
            [(when, filename, duration, tag) for duration in durations],
        )
        memory.update_matching_times(filename, tag, when)
        details = [
            f"        Updated to {_format_log_timestamp(scrobble.timestamp)}: "
            f"{scrobble.artist} — {scrobble.title} "
            f"[PAF filename key={filename!r}, duration={duration}s]"
            for duration in durations
        ]
        return len(durations), details

    existing_filename_rows = memory.rows_by_filename.get(filename, [])
    if existing_filename_rows:
        # Do not add a duration=1 row to an already ambiguous/different filename;
        # PAFPlayer would then probe exact metadata and the synthetic duration
        # could never match. Skipping is safer than manufacturing a false play.
        return 0, []

    database.execute(
        """INSERT INTO played_tracks_recent(filename, duration_seconds, tag, played_at)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(filename, duration_seconds, tag)
           DO UPDATE SET played_at=MAX(played_tracks_recent.played_at, excluded.played_at)""",
        (filename, WEB_HISTORY_SENTINEL_DURATION, tag, when),
    )
    memory.seed(filename, tag, when)
    return 1, [
        f"        Updated to {_format_log_timestamp(scrobble.timestamp)}: "
        f"{scrobble.artist} — {scrobble.title} "
        f"[PAF filename key={filename!r}, web-history seed]"
    ]


def _append_page_log(
    *,
    log_path: Path,
    page: int,
    result: PageResult,
    page_elapsed: float,
    total_elapsed: float,
) -> None:
    """Append one completed page section to the requested plaintext log.

    Motivation: page-at-a-time flushes make the log a durable recovery/audit
    trail even if a later web request or manual stop ends the overall crawl.
    """
    lines = [
        "=" * 88,
        f"✨*✨*✨*✨  PAGE {page}  ✨*✨*✨*✨",
        "",
        "* Updates:",
    ]
    if result.update_lines:
        lines.extend(result.update_lines)
    else:
        lines.append("        (none)")
    lines.extend(
        [
            "",
            "- Page summary:",
            f"  Checked: {result.checked}",
            f"  Updated: {result.updated_rows} songs from {len(result.updated_bands)} bands",
            f"  Time elapsed: {_format_elapsed(page_elapsed)}",
            f"  Total time elapsed: {_format_elapsed(total_elapsed)}",
            "",
        ]
    )
    with log_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")


def _prompt_crawl_start_page() -> int:
    """Ask where a history crawl should resume, with Enter meaning page 1.

    Motivation: a deep Last.fm account can contain thousands of pages.  A
    remembered page number makes manual interruption/restart inexpensive while
    retaining the same newest-timestamp-wins database safety rules.
    """
    if not sys.stdin.isatty():
        return 1
    while True:
        raw = input("Start with which Last.fm page? [Enter = 1]: ").strip()
        if not raw:
            return 1
        try:
            page = int(raw)
        except ValueError:
            print("Please enter a positive page number, or press Enter for page 1.")
            continue
        if page >= 1:
            return page
        print("Please enter page 1 or greater.")


def crawl_lastfm_recently_played_pages(username: Optional[str] = None) -> None:
    """Walk all Last.fm recent-track pages and backfill PAFPlayer play history.

    Motivation: local Last.fm desktop logs only cover periods/machines where the
    logger existed.  Last.fm's account history can reach farther back, allowing
    PAFPlayer's history-biased shuffle to know about older listens it never saw.
    """
    username = _resolve_lastfm_username(username)
    page = _prompt_crawl_start_page()
    start_page = page
    database, database_path = _open_history_database()
    log_path = Path(__file__).resolve().with_name(WEB_IMPORT_LOG_NAME)
    memory = HistoryMemory.from_database(database)

    print(f"🎧 Last.fm user: {username}")
    print(f"⏪ Starting Last.fm crawl at page {start_page:,}.")
    print(f"🗃️  PAFPlayer history database: {database_path}")
    print(f"📝 Import log: {log_path}")
    print(f"🧠 Loaded {sum(len(rows) for rows in memory.rows_by_filename.values()):,} history rows into memory.")

    display = CrawlerDisplay()
    total_started = time.monotonic()
    total_updates = 0
    total_bands: set[str] = set()
    seen_web_identities: set[tuple[str, str]] = set()
    pages_completed = 0
    recent_page_times: list[float] = []
    total_pages: Optional[int] = None
    oldest_timestamp: Optional[int] = None
    encountered_artists: set[str] = set()

    try:
        with QuitGuard(display) as quit_guard:
            while total_pages is None or page <= total_pages:
                if quit_guard.stop_requested:
                    break

                page_started = time.monotonic()
                tracks, reported_total_pages = _fetch_recent_page(username, page)
                total_pages = reported_total_pages if total_pages is None else max(total_pages, reported_total_pages)
                page_total = len(tracks)
                result = PageResult()

                initial = _crawler_summary_line(
                    page=page,
                    page_updates=0,
                    page_bands=0,
                    total_updates=total_updates,
                    total_bands=len(total_bands),
                    total_elapsed=time.monotonic() - total_started,
                    oldest_timestamp=oldest_timestamp,
                    sampled_artists=encountered_artists,
                )
                # Page progress is intentionally page-granular: the bar remains
                # fixed while all tracks on this page are processed.
                initial_fraction = min(1.0, page / max(1, total_pages))
                display.start_page(
                    initial,
                    fraction=initial_fraction,
                    page=page,
                    total_pages=total_pages,
                    eta_seconds=_rolling_page_eta(
                        recent_page_times, page=page - 1, total_pages=total_pages
                    ),
                )

                for index, scrobble in enumerate(tracks, start=1):
                    quit_guard.poll_console_keys()
                    if quit_guard.stop_requested:
                        break
                    result.checked += 1
                    encountered_artists.add(scrobble.artist)
                    if oldest_timestamp is None or scrobble.timestamp < oldest_timestamp:
                        oldest_timestamp = scrobble.timestamp

                    web_identity = (scrobble.filename_key, scrobble.tag_key)
                    if web_identity not in seen_web_identities:
                        seen_web_identities.add(web_identity)
                        updated, details = _update_history_for_scrobble(database, memory, scrobble)
                        if updated:
                            result.updated_rows += updated
                            total_updates += updated
                            band_key = _normalize_history_text(scrobble.artist)
                            if band_key:
                                result.updated_bands.add(band_key)
                                total_bands.add(band_key)
                            result.update_lines.extend(details)

                    # Commit each row rather than each page so Ctrl+Break or power
                    # loss loses at most one SQL operation. WAL keeps this cheap.
                    database.commit()
                    # Deliberately do not redraw the live rows for every track.
                    # Motivation: the progress bar represents completed/page-level
                    # position, not track-level work, and Last.fm pages process so
                    # quickly that 50 redraws only create flicker and can expose
                    # terminal wrapping/cursor artifacts. The page is redrawn once
                    # with final values after all tracks on it have been processed.

                page_elapsed = time.monotonic() - page_started
                recent_page_times.append(page_elapsed)
                if len(recent_page_times) > 50:
                    del recent_page_times[:-50]
                total_elapsed = time.monotonic() - total_started
                final_summary = _crawler_summary_line(
                    page=page,
                    page_updates=result.updated_rows,
                    page_bands=len(result.updated_bands),
                    total_updates=total_updates,
                    total_bands=len(total_bands),
                    total_elapsed=total_elapsed,
                    oldest_timestamp=oldest_timestamp,
                    sampled_artists=encountered_artists,
                )
                final_fraction = page / max(1, total_pages)
                display.finish_page(
                    final_summary,
                    page=page,
                    total_pages=total_pages,
                    fraction=final_fraction,
                    eta_seconds=_rolling_page_eta(
                        recent_page_times, page=page, total_pages=total_pages
                    ),
                )
                _append_page_log(
                    log_path=log_path,
                    page=page,
                    result=result,
                    page_elapsed=page_elapsed,
                    total_elapsed=total_elapsed,
                )
                pages_completed += 1

                if quit_guard.stop_requested:
                    break
                if not tracks:
                    break
                page += 1

            display.close()
            if quit_guard.stop_requested:
                print(
                    f"🛑 Crawl stopped after three quit confirmations. "
                    f"Committed {total_updates:,} history-row update(s)."
                )
            else:
                print(
                    f"✅ Last.fm crawl complete from page {start_page:,}: {pages_completed:,} page(s), "
                    f"{total_updates:,} history-row update(s), {len(total_bands):,} band(s)."
                )
    finally:
        database.commit()
        database.close()


def _build_parser() -> argparse.ArgumentParser:
    """Build the standalone CLI with mutually exclusive scrobble/crawl modes.

    Motivation: V1 required artist/title unconditionally; V2 must let the new
    maintenance switch run by itself while preserving concise help and examples.
    """
    parser = argparse.ArgumentParser(
        description="Scrobble a track to Last.fm or crawl recent-history pages into PAFPlayer.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python claire_lastfm.py --artist "Metallica" --title "Blackened" --album "...And Justice for All"
  python claire_lastfm.py --crawl-lastfm-recently-played-pages

History crawl:
  Prompts for the starting Last.fm page (Enter = 1), then walks backward
  through 50-play pages; loads PAFPlayer's SQLite history into memory first and
  only writes newer timestamps. Ctrl+C/Ctrl+Break/Q/X/Ctrl+W require three quit
  confirmations. The live summary shows updates, total time, oldest date reached,
  and a console-width-aware random artist sample. The rainbow bar tracks overall
  progress through Last.fm pages and shows an ETA calculated from the rolling
  average of up to the 50 most recently completed pages. Every finished page is appended to
  lastfm-webpage-import.log.
""",
    )
    parser.add_argument("--artist", help="Artist name for single-track scrobbling")
    parser.add_argument("--title", help="Track title for single-track scrobbling")
    parser.add_argument("--album", help="Album name")
    parser.add_argument("--duration", type=int, help="Track duration in seconds")
    parser.add_argument("--track", type=int, dest="track_number", help="Track number on album")
    parser.add_argument("--timestamp", type=int, help="Unix timestamp when the track started")
    parser.add_argument(
        "--crawl-lastfm-recently-played-pages",
        action="store_true",
        help=(
            "prompt for a starting Last.fm history page, crawl backward, and backfill "
            "only newer timestamps into PAFPlayer's play-history database"
        ),
    )
    parser.add_argument(
        "--lastfm-username",
        help="optional username override for the crawl; normally discovered/saved automatically",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> None:
    """Dispatch either the history crawler or original one-track scrobble mode.

    Motivation: keeping one entry point makes the helper easy to invoke manually
    and keeps PAFPlayer's existing import/scrobble API unchanged.
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.crawl_lastfm_recently_played_pages:
        if any(
            value is not None
            for value in (
                args.artist,
                args.title,
                args.album,
                args.duration,
                args.track_number,
                args.timestamp,
            )
        ):
            parser.error(
                "--crawl-lastfm-recently-played-pages is a standalone mode; "
                "do not combine it with scrobble metadata options"
            )
        try:
            crawl_lastfm_recently_played_pages(args.lastfm_username)
        except Exception as exc:
            print(f"Error crawling Last.fm recently played pages: {exc}", file=sys.stderr)
            raise SystemExit(1)
        return

    if args.lastfm_username:
        parser.error("--lastfm-username is only used with --crawl-lastfm-recently-played-pages")
    if not args.artist or not args.title:
        parser.error("single-track scrobbling requires both --artist and --title")

    try:
        result = scrobble_track(
            artist=args.artist,
            title=args.title,
            album=args.album,
            duration=args.duration,
            track_number=args.track_number,
            timestamp=args.timestamp,
        )
        print("Scrobble successful:", json.dumps(result, indent=2))
    except Exception as exc:
        print("Error scrobbling track:", exc, file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
