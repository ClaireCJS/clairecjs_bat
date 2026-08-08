#!/usr/bin/env python3
"""Patch Claire's existing claire_lastfm.py in place with track.updateNowPlaying.

This updater intentionally modifies the user's existing helper instead of replacing
it with an older repository copy, preserving newer features such as PAFPlayer's
recently-played history crawler.  A timestamped backup is created first.
"""
from __future__ import annotations

import argparse
import shutil
import time
from pathlib import Path

METHOD = r'''
    def update_now_playing(
        self,
        artist: str,
        title: str,
        album: Optional[str] = None,
        duration: Optional[int] = None,
        track_number: Optional[int] = None,
    ) -> Dict:
        """Report an ephemeral Last.fm ``track.updateNowPlaying`` state.

        Motivation: Now Playing is intentionally distinct from a scrobble.  It
        lets PAFPlayer show the track on Last.fm immediately when playback starts
        without adding anything to listening history.  A later ``track.scrobble``
        remains governed entirely by PAFPlayer's existing listened-time rules.

        This reuses the same API credentials, session key file, authentication
        flow, signature routine, and HTTP endpoint as ``scrobble``.
        """
        self._ensure_authenticated()
        if not self.session_key:
            raise RuntimeError("Failed to obtain session key")

        params = {
            "method": "track.updateNowPlaying",
            "api_key": API_KEY,
            "sk": self.session_key,
            "artist": artist,
            "track": title,
        }
        if album:
            params["album"] = album
        if duration:
            params["duration"] = str(duration)
        if track_number:
            params["trackNumber"] = str(track_number)
        params["api_sig"] = _api_signature(params)
        params["format"] = "json"

        response = requests.post(
            API_URL,
            data=params,
            timeout=globals().get("REQUEST_TIMEOUT_SECONDS", 30),
        )
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and data.get("error"):
            raise RuntimeError(
                f"Last.fm API error {data.get('error')}: "
                f"{data.get('message', 'unknown Last.fm API error')}"
            )
        return data

'''

WRAPPER = r'''
def update_now_playing_track(
    artist: str,
    title: str,
    album: Optional[str] = None,
    duration: Optional[int] = None,
    track_number: Optional[int] = None,
) -> Dict:
    """Convenience wrapper for Last.fm Now Playing updates.

    Motivation: PAFPlayer should use the same importable helper/session as real
    scrobbles while keeping the two API operations semantically separate.
    """
    return LastFMClient().update_now_playing(
        artist, title, album, duration, track_number
    )


'''

DOC_NOTE = '''\nNow Playing vs scrobbling\n-------------------------\nPAFPlayer also calls ``track.updateNowPlaying`` when a track starts. This is an\nephemeral status update only: it does not create a scrobble or listening-history\nentry. The existing ``track.scrobble`` path remains separate and is called only\nafter PAFPlayer's normal listened-time rules are satisfied (or explicitly forced).\n'''


def patch_source(text: str) -> str:
    if "def update_now_playing_track(" in text and "def update_now_playing(" in text:
        return text

    class_start = text.find("class LastFMClient:")
    if class_start < 0:
        raise RuntimeError("Could not find class LastFMClient in claire_lastfm.py")
    scrobble_pos = text.find("    def scrobble(", class_start)
    if scrobble_pos < 0:
        raise RuntimeError("Could not find LastFMClient.scrobble in claire_lastfm.py")
    text = text[:scrobble_pos] + METHOD + text[scrobble_pos:]

    wrapper_pos = text.find("def scrobble_track(")
    if wrapper_pos < 0:
        raise RuntimeError("Could not find scrobble_track convenience wrapper")
    after_wrapper = text.find("\ndef ", wrapper_pos + len("def scrobble_track("))
    if after_wrapper < 0:
        marker = text.find("# ---------------------------------------------------------------------------", wrapper_pos)
        if marker < 0:
            raise RuntimeError("Could not locate insertion point after scrobble_track")
        after_wrapper = marker
    text = text[:after_wrapper + 1] + WRAPPER + text[after_wrapper + 1:]

    # Add a compact module-level distinction without trying to rewrite the
    # helper's existing V2 crawler documentation wholesale.
    doc_end = text.find('"""', text.find('"""') + 3)
    if doc_end >= 0 and "Now Playing vs scrobbling" not in text[:doc_end]:
        text = text[:doc_end] + DOC_NOTE + text[doc_end:]
    return text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default="claire_lastfm.py")
    parser.add_argument("--output", help="write to a separate path instead of modifying in place")
    args = parser.parse_args()
    source = Path(args.path).expanduser().resolve()
    if not source.is_file():
        raise SystemExit(f"Not found: {source}")
    original = source.read_text(encoding="utf-8")
    patched = patch_source(original)
    target = Path(args.output).expanduser().resolve() if args.output else source
    if target == source and patched != original:
        stamp = time.strftime("%Y%m%d-%H%M%S")
        backup = source.with_name(source.name + f".before-v3-now-playing.{stamp}.bak")
        shutil.copy2(source, backup)
        print(f"Backup: {backup}")
    target.write_text(patched, encoding="utf-8")
    print(f"Updated: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
