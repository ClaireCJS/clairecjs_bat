"""claire_lastfm
===================

This module provides a small helper for scrobbling tracks to Last.fm.  It can be
used as a command line tool or imported as a library.

Requirements
------------
* Python 3.8+
* ``requests`` library (``pip install requests``)

Configuration
-------------
The module expects two environment variables to be set:

``LASTFM_API_KEY``
    Your Last.fm API key.
``LASTFM_API_SECRET``
    Your Last.fm API secret.

If the environment variables are missing the module will raise a clear error.

Authentication flow
-------------------
The first time the module is used it will open a browser window asking the
user to authorize the application.  The resulting session key is stored in
``~/.claire_lastfm_session`` so subsequent calls do not need to re‑authenticate.

Usage
-----
Command line:

::

    python claire_lastfm.py --artist "Artist" --title "Song" [--album "Album"]

Library:

::

    from claire_lastfm import scrobble_track
    scrobble_track("Artist", "Song", album="Album")
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import sys
import time
import urllib.parse
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

# The `requests` library is a third‑party dependency that may not be
# available in all environments. Importing it unconditionally causes
# static type checkers (e.g. Pylance) to emit a warning if the package
# cannot be resolved. To make the module robust and provide a clear
# runtime error, we attempt to import `requests` and raise a helpful
# message if it is missing.
try:
    import requests  # type: ignore  # Suppress Pylance warning if the library is not installed in the analysis environment
except ImportError as exc:  # pragma: no cover - exercised via tests
    raise RuntimeError(
        "The 'requests' library is required for Last.fm scrobbling. "
        "Install it with 'pip install requests' and retry."
    ) from exc

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------
API_URL = "https://ws.audioscrobbler.com/2.0/"
REQUEST_TOKEN_URL = "https://ws.audioscrobbler.com/2.0/"
SESSION_KEY_FILE = Path.home() / ".claire_lastfm_session"


def _get_env_var(name: str) -> str:
    """Return the value of an environment variable or raise an error.

    Parameters
    ----------
    name:
        Name of the environment variable.
    """
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable {name!r} is required but not set.")
    return value


# Load API credentials from environment variables or a local private.env file.
# The private.env file is expected to be located at `bat/private.env` relative
# to the workspace root and contain lines of the form
#   lastfm_api_key=YOUR_KEY
#   lastfm_api_secret=YOUR_SECRET
# This allows developers to keep secrets out of the repository while still
# enabling local testing.
def _load_api_credentials() -> tuple[str, str]:
    """Load Last.fm API credentials.

    The function first checks the ``LASTFM_API_KEY`` and ``LASTFM_API_SECRET``
    environment variables. If they are not present, it falls back to reading a
    ``bat/private.env`` file located at the repository root. The file should
    contain ``lastfm_api_key=...`` and ``lastfm_api_secret=...`` lines.

    If neither source provides both values, a ``RuntimeError`` is raised with a
    clear message. This guarantees that callers always receive a valid tuple
    and prevents ``None`` values from propagating.
    """
    env_key = os.getenv("LASTFM_API_KEY")
    env_secret = os.getenv("LASTFM_API_SECRET")
    if env_key and env_secret:
        return env_key, env_secret

    private_path = Path("bat/private.env")
    if private_path.exists():
        key: Optional[str] = None
        secret: Optional[str] = None
        for line in private_path.read_text(encoding="utf-8").splitlines():
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
        "LASTFM_API_SECRET environment variables or provide them in "
        "bat/private.env."
    )

# Load credentials once at import time.
API_KEY, API_SECRET = _load_api_credentials()


def _api_signature(params: Dict[str, str]) -> str:
    """Return the MD5 API signature for a set of parameters.

    The signature is calculated by sorting the parameters alphabetically by
    key, concatenating key+value pairs, appending the API secret, and then
    computing the MD5 hash of the resulting string.
    """
    sorted_items = sorted(params.items())
    concatenated = "".join(f"{k}{v}" for k, v in sorted_items)
    concatenated += API_SECRET
    return hashlib.md5(concatenated.encode("utf-8")).hexdigest()


class LastFMClient:
    """Simple Last.fm client for scrobbling tracks.

    The client handles authentication, session key persistence, and the
    ``track.scrobble`` API call.
    """

    def __init__(self, session_file: Path | str = SESSION_KEY_FILE):
        self.session_file = Path(session_file)
        self.session_key: Optional[str] = None
        self._load_session()

    # ---------------------------------------------------------------------
    # Session handling
    # ---------------------------------------------------------------------
    def _load_session(self) -> None:
        if self.session_file.exists():
            self.session_key = self.session_file.read_text(encoding="utf-8").strip()

    def _save_session(self) -> None:
        if self.session_key:
            self.session_file.write_text(self.session_key, encoding="utf-8")

    def _ensure_authenticated(self) -> None:
        if self.session_key:
            return
        # No session key – perform OAuth flow
        self.session_key = self._authenticate()
        self._save_session()

    def _authenticate(self) -> str:
        """Perform the Last.fm OAuth flow and return a session key.

        The flow is:
        1. Request a temporary token.
        2. Open the authorization URL in the user's browser.
        3. Poll the API until the user authorises the request token.
        4. Exchange the request token for a session key.
        """
        # 1. Request token (signature must be calculated without the "format" parameter)
        token_params = {
            "method": "auth.getToken",
            "api_key": API_KEY,
        }
        token_params["api_sig"] = _api_signature(token_params)
        token_params["format"] = "json"
        resp = requests.get(API_URL, params=token_params)
        resp.raise_for_status()
        token = resp.json()["token"]

        # 2. Open browser for user to authorize
        auth_url = f"https://www.last.fm/api/auth/?api_key={API_KEY}&token={token}"
        print("Opening browser for Last.fm authentication…")
        webbrowser.open(auth_url)
        # 3. Wait for the user to authorize the request token.
        # The script will continuously poll the API until the session key is available.
        # Directly start polling the API; the loop will only exit once the
        # user has clicked "Allow" in the browser and the session becomes
        # available.

        # 4. Poll for the session key after the user authorizes.
        timeout_seconds = 300  # 5 minutes
        interval = 2
        elapsed = 0
        while elapsed < timeout_seconds:
            time.sleep(interval)
            elapsed += interval
            poll_params = {
                "method": "auth.getSession",
                "api_key": API_KEY,
                "token": token,
            }
            poll_params["api_sig"] = _api_signature(poll_params)
            poll_params["format"] = "json"
            poll_resp = requests.get(API_URL, params=poll_params)
            try:
                data = poll_resp.json()
            except ValueError:
                continue
            if "session" in data:
                return data["session"]["key"]
            # If the token is not yet authorized, the API may include error 14.
            if data.get("error") not in (None, 14):
                raise RuntimeError(f"Authentication error: {data.get('message', 'unknown')}")
        raise RuntimeError(
            "Authentication timed out. Please ensure you authorized the "
            "application in the opened browser."
        )

    # ---------------------------------------------------------------------
    # Scrobble API
    # ---------------------------------------------------------------------
    def scrobble(self, artist: str, title: str, album: Optional[str] = None,
                  duration: Optional[int] = None, track_number: Optional[int] = None,
                  timestamp: Optional[int] = None) -> Dict:
        """Scrobble a track to Last.fm.

        Parameters
        ----------
        artist, title:
            Track metadata.
        album:
            Optional album name.
        duration:
            Length of the track in seconds.
        track_number:
            Track number on the album.
        timestamp:
            Unix timestamp of when the track started playing.  If omitted the
            current time is used.
        """
        self._ensure_authenticated()
        if not self.session_key:
            raise RuntimeError("Failed to obtain session key")

        # Build the parameters required for the scrobble request.
        # The API signature must be calculated **before** adding the "format"
        # parameter, as the Last.fm API does not include "format" in the
        # signature calculation.
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

        # Compute the API signature before adding the format.
        params["api_sig"] = _api_signature(params)
        # Add the format parameter for the request.
        params["format"] = "json"

        resp = requests.post(API_URL, data=params)
        resp.raise_for_status()
        return resp.json()


# ---------------------------------------------------------------------------
# Library helper
# ---------------------------------------------------------------------------
def scrobble_track(artist: str, title: str, album: Optional[str] = None,
                    duration: Optional[int] = None, track_number: Optional[int] = None,
                    timestamp: Optional[int] = None) -> Dict:
    """Convenience wrapper for scrobbling a track.

    This function can be imported and called directly from other Python code.
    """
    client = LastFMClient()
    return client.scrobble(artist, title, album, duration, track_number, timestamp)


# ---------------------------------------------------------------------------
# Command line interface
# ---------------------------------------------------------------------------
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scrobble a track to Last.fm")
    parser.add_argument("--artist", required=True, help="Artist name")
    parser.add_argument("--title", required=True, help="Track title")
    parser.add_argument("--album", help="Album name")
    parser.add_argument("--duration", type=int, help="Track duration in seconds")
    parser.add_argument("--track", type=int, dest="track_number", help="Track number on album")
    parser.add_argument("--timestamp", type=int, help="Unix timestamp of when the track started")
    return parser


def main(argv: Optional[list[str]] = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
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
        sys.exit(1)


if __name__ == "__main__":
    main()
