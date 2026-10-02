#!/usr/bin/env python3
"""Shared, UI-neutral audio processing used by Claire's music tools.

The destructive ReplayGain bake lives here so audit_music_batch.py and
PAFPlayer cannot silently diverge.  Callers own prompting and presentation;
this module owns staging, validation, backup, replacement, retagging, and
rollback.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import math
import os
from pathlib import Path
import shutil
import subprocess
from typing import Callable, Iterable, Sequence


ProgressCallback = Callable[[str], None]
CLAIRE_AUDIO_PROCESSING_VERSION = "V121"


@dataclass(frozen=True)
class AudioHealthResult:
    """UI-neutral metadata facts used by PAFPlayer's background health audit."""

    source: Path
    artist: str = ""
    title: str = ""
    album: str = ""
    year: str = ""
    genre: str = ""
    replaygain_valid: bool = False
    has_plain_lyrics: bool = False
    has_timed_lyrics: bool = False
    has_artwork: bool = False
    lyric_sync_messages: tuple[str, ...] = ()


def _tag_text(value: object) -> str:
    """Return a stable text value for Mutagen's list and ID3 frame types."""
    payload = getattr(value, "text", value)
    if isinstance(payload, (list, tuple)):
        return "; ".join(str(item).strip() for item in payload if str(item).strip())
    return str(payload or "").strip()


def _tag_rows(tags: object) -> Iterable[tuple[str, object]]:
    if tags is None:
        return ()
    try:
        return tuple((str(key), value) for key, value in tags.items())
    except (AttributeError, TypeError):
        return ()


def _first_tag(rows: Sequence[tuple[str, object]], *names: str) -> str:
    wanted = {name.casefold() for name in names}
    for key, value in rows:
        base = key.split(":", 1)[0].casefold()
        if key.casefold() in wanted or base in wanted:
            text = _tag_text(value)
            if text:
                return text
    return ""


def inspect_audio_health(audio_path: Path | str) -> AudioHealthResult:
    """Inspect common audio tags without decoding samples or changing the file.

    Mutagen deliberately handles each container's native tag representation.
    Unknown but readable formats return conservative empty/false facts; corrupt
    or unsupported files raise so the caller can log the underlying problem.
    """
    from mutagen import File as MutagenFile

    source = Path(audio_path).resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    tagged = MutagenFile(source)
    if tagged is None:
        raise RuntimeError(f"Unsupported or unreadable audio file: {source}")
    rows = tuple(_tag_rows(getattr(tagged, "tags", None)))

    expanded: list[tuple[str, object]] = list(rows)
    for key, value in rows:
        description = str(getattr(value, "desc", "") or "").strip()
        if description:
            expanded.append((description, value))
            expanded.append((f"{key.split(':', 1)[0]}:{description}", value))
    rows = tuple(expanded)

    gain = _first_tag(rows, "replaygain_track_gain", "TXXX:replaygain_track_gain")
    replaygain_valid = False
    if gain:
        try:
            replaygain_valid = math.isfinite(float(gain.casefold().replace("db", "").strip()))
        except ValueError:
            replaygain_valid = False

    keys = {key.casefold() for key, _value in rows}
    bases = {key.split(":", 1)[0] for key in keys}
    has_plain_lyrics = bool(
        {"uslt", "lyrics", "unsyncedlyrics", "unsynced lyrics"} & (keys | bases)
    )
    has_timed_lyrics = bool(
        {"sylt", "syncedlyrics", "synced lyrics", "lyrics-eng", "lyrics-xxx"}
        & (keys | bases)
    )
    has_artwork = bool(getattr(tagged, "pictures", ())) or bool(
        {"apic", "covr", "metadata_block_picture"} & (keys | bases)
    )

    return AudioHealthResult(
        source=source,
        artist=_first_tag(rows, "artist", "albumartist", "TPE1", "TPE2", "\xa9ART", "aART"),
        title=_first_tag(rows, "title", "TIT2", "\xa9nam"),
        album=_first_tag(rows, "album", "TALB", "\xa9alb"),
        year=_first_tag(rows, "date", "year", "TDRC", "TYER", "\xa9day"),
        genre=_first_tag(rows, "genre", "TCON", "\xa9gen"),
        replaygain_valid=replaygain_valid,
        has_plain_lyrics=has_plain_lyrics,
        has_timed_lyrics=has_timed_lyrics,
        has_artwork=has_artwork,
    )


@dataclass(frozen=True)
class ReplayGainBakeResult:
    source: Path
    backup: Path
    requested_db: float
    applied_db: float
    peak_limited: bool
    replacement_method: str


def replaygain_decibels_from_factor(factor: float | None) -> float | None:
    """Convert a positive ReplayGain multiplier to its tagged dB value."""
    if factor is None:
        return None
    value = float(factor)
    if not math.isfinite(value) or value <= 0:
        return None
    return 20.0 * math.log10(value)


def peak_protected_replaygain_db(
    requested_db: float,
    peak_ratio: float | None,
    *,
    headroom: float = 0.999,
) -> float:
    """Limit positive gain so the measured peak remains below full scale."""
    requested = float(requested_db)
    if not math.isfinite(requested):
        raise ValueError("ReplayGain adjustment must be finite")
    if requested <= 0 or peak_ratio is None:
        return requested
    peak = max(0.0, float(peak_ratio))
    if peak <= 0:
        return requested
    return min(requested, 20.0 * math.log10(float(headroom) / peak))


def collision_safe_path(
    desired: Path | str,
    reserved: set[Path] | None = None,
) -> Path:
    """Return an unused sibling path, honoring optional in-memory reservations."""
    desired_path = Path(desired)
    occupied = reserved or set()
    if not desired_path.exists() and desired_path not in occupied:
        return desired_path
    suffix = desired_path.suffix
    stem = desired_path.name[:-len(suffix)] if suffix else desired_path.name
    index = 1
    while True:
        candidate = desired_path.with_name(f"{stem} ({index}){suffix}")
        if not candidate.exists() and candidate not in occupied:
            return candidate
        index += 1


def replacement_backup_path(
    path: Path | str,
    timestamp: str | None = None,
) -> Path:
    """Choose the standard timestamped sibling backup path for one replacement."""
    source = Path(path)
    stamp = timestamp or datetime.now().strftime("%Y%m%d%H%M")
    return collision_safe_path(
        source.with_name(
            f"{source.name}.bak.{stamp}.replaced-by-chatgpt.bak"
        )
    )


def backup_before_inline_replacement(
    path: Path | str,
    timestamp: str | None = None,
) -> Path:
    """Copy and size-verify a file before any in-place audio/tag replacement."""
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"Cannot back up missing file: {source}")
    backup = replacement_backup_path(source, timestamp)
    source_digest = _sha256(source)
    shutil.copy2(source, backup)
    if (
        not backup.is_file()
        or backup.stat().st_size != source.stat().st_size
        or _sha256(backup) != source_digest
    ):
        with contextlib_suppress_oserror():
            backup.unlink()
        raise RuntimeError(f"Replacement backup verification failed: {backup}")
    return backup


def _collision_safe_path(desired: Path) -> Path:
    """Backward-compatible private alias for early V114 callers."""
    return collision_safe_path(desired)


def _backup_source(path: Path) -> Path:
    return backup_before_inline_replacement(path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _replace_verified(staged: Path, destination: Path) -> str:
    staged_size = staged.stat().st_size
    staged_digest = _sha256(staged)
    try:
        os.replace(staged, destination)
        if (
            destination.stat().st_size != staged_size
            or _sha256(destination) != staged_digest
        ):
            raise RuntimeError("SHA-256 verification of the atomic media replacement failed")
        return "atomic-replace"
    except OSError as exc:
        denied = (
            isinstance(exc, PermissionError)
            or getattr(exc, "winerror", None) in {5, 32}
            or getattr(exc, "errno", None) in {1, 13}
        )
        if not denied:
            raise
    with staged.open("rb") as source, destination.open("wb") as target:
        shutil.copyfileobj(source, target, length=1024 * 1024)
        target.flush()
        os.fsync(target.fileno())
    if destination.stat().st_size != staged_size or _sha256(destination) != staged_digest:
        raise RuntimeError("SHA-256 verification of the in-place media write failed")
    with contextlib_suppress_oserror():
        staged.unlink()
    return "verified-copy-fallback"


class contextlib_suppress_oserror:
    """Tiny local suppressor that keeps this leaf module dependency-light."""
    def __enter__(self):
        return self

    def __exit__(self, exception_type, _exception, _traceback):
        return bool(exception_type and issubclass(exception_type, OSError))


def _run(command: Sequence[str], *, stream_output: bool, cwd: Path | None = None) -> None:
    options: dict[str, object] = {"check": False, "cwd": str(cwd) if cwd else None}
    if not stream_output:
        options.update(stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
    result = subprocess.run(list(command), **options)
    if result.returncode:
        detail = str(getattr(result, "stdout", "") or "").strip()
        raise RuntimeError(
            f"Audio command failed with exit code {result.returncode}: "
            f"{subprocess.list2cmdline(list(command))}" + (f"\n{detail}" if detail else "")
        )


def _track_gain_present(path: Path) -> bool:
    suffix = path.suffix.casefold()
    if suffix == ".flac":
        from mutagen.flac import FLAC
        tagged = FLAC(path)
        return any(str(key).casefold() == "replaygain_track_gain" for key in tagged.keys())
    from mutagen.mp3 import MP3
    tagged = MP3(path)
    if tagged.tags is None:
        return False
    return any(
        str(getattr(frame, "desc", "")).casefold() == "replaygain_track_gain"
        for frame in tagged.tags.getall("TXXX")
    )


def _validate_and_remove_gain(path: Path) -> None:
    if path.suffix.casefold() == ".flac":
        from mutagen.flac import FLAC
        tagged = FLAC(path)
        if not tagged.info or tagged.info.length <= 0:
            raise RuntimeError("Baked FLAC has no valid audio stream")
        for key in list(tagged.keys()):
            if str(key).casefold().startswith("replaygain_"):
                del tagged[key]
        tagged.save()
        return
    from mutagen.mp3 import MP3
    tagged = MP3(path)
    if not tagged.info or tagged.info.length <= 0:
        raise RuntimeError("Re-encoded MP3 has no valid audio stream")
    if tagged.tags is not None:
        for frame in list(tagged.tags.getall("TXXX")):
            if str(frame.desc).casefold().startswith("replaygain_"):
                tagged.tags.delall(f"TXXX:{frame.desc}")
        tagged.save(v2_version=3)


def bake_replaygain_into_audio(
    audio_path: Path | str,
    requested_db: float,
    *,
    peak_ratio: float | None = None,
    stream_output: bool = True,
    progress: ProgressCallback | None = None,
    ffmpeg_executable: str | None = None,
    metaflac_executable: str | None = None,
    metamp3_executable: str | None = None,
) -> ReplayGainBakeResult:
    """Bake gain into FLAC/MP3 samples, retag, verify, and roll back on failure."""
    source = Path(audio_path).resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    suffix = source.suffix.casefold()
    if suffix not in {".flac", ".mp3"}:
        raise RuntimeError("Baked ReplayGain currently supports FLAC and MP3 audio")
    applied_db = peak_protected_replaygain_db(requested_db, peak_ratio)
    peak_limited = applied_db < float(requested_db) - 0.01
    ffmpeg = ffmpeg_executable or shutil.which("ffmpeg")
    tagger = (
        metaflac_executable or shutil.which("metaflac")
        if suffix == ".flac"
        else metamp3_executable or shutil.which("metamp3")
    )
    if not ffmpeg or not tagger:
        required = "ffmpeg and metaflac" if suffix == ".flac" else "ffmpeg and metamp3"
        raise RuntimeError(f"Baking {suffix[1:].upper()} ReplayGain requires {required} in PATH")
    if progress:
        progress(f"Baking {applied_db:+.2f} dB" + (" (peak limited)" if peak_limited else ""))

    temporary = _collision_safe_path(source.with_name(f".{source.name}.baking-replaygain{suffix}"))
    if suffix == ".flac":
        from mutagen.flac import FLAC
        original = FLAC(source)
        bits = int(getattr(getattr(original, "info", None), "bits_per_sample", 16) or 16)
        command = [
            str(ffmpeg), "-hide_banner", "-y", "-i", str(source),
            "-map", "0", "-map_metadata", "0", "-c", "copy", "-c:a", "flac",
            "-sample_fmt", "s16" if bits <= 16 else "s32",
            "-filter:a", f"volume={applied_db:+.8f}dB", str(temporary),
        ]
        tag_command = [str(tagger), "--add-replay-gain", str(source)]
    else:
        command = [
            str(ffmpeg), "-hide_banner", "-y", "-i", str(source),
            "-map", "0", "-map_metadata", "0", "-c", "copy", "-c:a", "libmp3lame",
            "-q:a", "0", "-filter:a", f"volume={applied_db:+.8f}dB",
            "-id3v2_version", "3", str(temporary),
        ]
        tag_command = [str(tagger), "--replay-gain", str(source)]

    backup: Path | None = None
    replacement_method = ""
    try:
        _run(command, stream_output=stream_output)
        if not temporary.is_file():
            raise RuntimeError("FFmpeg did not create the staged audio file")
        _validate_and_remove_gain(temporary)
        backup = _backup_source(source)
        replacement_method = _replace_verified(temporary, source)
        _run(tag_command, stream_output=stream_output, cwd=source.parent)
        if not _track_gain_present(source):
            raise RuntimeError("Fresh ReplayGain tags were not verified")
    except Exception:
        with contextlib_suppress_oserror():
            temporary.unlink()
        if backup is not None and backup.is_file():
            shutil.copy2(backup, source)
            if (
                source.stat().st_size != backup.stat().st_size
                or _sha256(source) != _sha256(backup)
            ):
                raise RuntimeError(
                    f"ReplayGain bake failed and rollback verification also failed; "
                    f"the verified backup remains at {backup}"
                )
        raise
    if backup is None:
        raise RuntimeError("Baked ReplayGain backup verification failed")
    return ReplayGainBakeResult(
        source=source,
        backup=backup,
        requested_db=float(requested_db),
        applied_db=applied_db,
        peak_limited=peak_limited,
        replacement_method=replacement_method,
    )
