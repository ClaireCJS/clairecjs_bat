"""Current-track data endpoints consumed by native local and remote tray viewers."""
from __future__ import annotations

from datetime import datetime, timezone
import io
import json
import secrets
import subprocess
from urllib.parse import parse_qs


def snapshot(owner, app):
    """Inspect the file currently owned by this server, on an HTTP worker only."""
    audio = owner.current_audio()
    state = owner.snapshot()
    unavailable = {"available": False, "message": "No current audio file is available.",
                   "file": {}, "tags": [], "lyrics": [], "art_count": 0,
                   "art_generation": int(state.get("art_generation") or 0),
                   "technical": {}, "technical_error": ""}
    if audio is None:
        return unavailable
    try:
        info = audio.stat()
        if not audio.is_file():
            return unavailable
    except OSError:
        return unavailable
    if str((state.get("track") or {}).get("path") or "") != str(audio):
        return unavailable
    lyrics = app.load_lyrics(audio)
    sidecar = app._find_timed_lyric_sidecar(audio)
    if sidecar is None:
        for candidate in (audio.with_suffix('.txt'), audio.parent / 'lyrics.txt'):
            if candidate.is_file():
                sidecar = candidate
                break
    lyric_source = "Related sidecar: " + sidecar.name if sidecar else "Embedded lyrics or metadata" if lyrics else ""
    technical, technical_error = {}, ""
    executable = app.ffprobe_executable()
    if executable is None:
        technical_error = "FFprobe is unavailable; container and stream details could not be read."
    else:
        try:
            result = subprocess.run(
                [str(executable), '-v', 'error', '-show_format', '-show_streams', '-show_chapters',
                 '-of', 'json', str(audio)], capture_output=True, text=True, encoding='utf-8',
                errors='replace', timeout=10, check=False,
            )
            if result.returncode:
                technical_error = "FFprobe could not read this file."
            else:
                technical = json.loads(result.stdout)
        except (OSError, subprocess.TimeoutExpired, ValueError):
            technical_error = "FFprobe details are unavailable for this file."
    return {
        "available": True,
        "file": {"name": audio.name, "path": str(audio), "size_bytes": info.st_size,
                 "modified_utc": datetime.fromtimestamp(info.st_mtime, timezone.utc).isoformat()},
        "duration_seconds": state.get("duration_seconds"),
        "tags": app.complete_audio_tag_rows(audio),
        "lyrics": [{"start": float(start), "end": None if end is None else float(end),
                    "text": str(text)} for start, end, text in lyrics],
        "lyric_source": lyric_source,
        "art_count": max(0, int(state.get("art_count") or 0)),
        "art_generation": int(state.get("art_generation") or 0),
        "technical": technical,
        "technical_error": technical_error,
    }


def artwork_preview(data, mime):
    """Send a bounded PNG preview that native Tk can show without Pillow locally."""
    try:
        from PIL import Image
        with Image.open(io.BytesIO(data)) as source:
            image = source.copy()
        image.thumbnail((640, 480))
        output = io.BytesIO()
        image.save(output, format='PNG')
        return output.getvalue(), 'image/png'
    except Exception:
        return data, mime


def wallpaper_bitmap(data, width, height):
    """Make a desktop-sized BMP on the server so tray clients need no Pillow."""
    if not data or not 320 <= width <= 1920 or not 240 <= height <= 1080:
        return None
    try:
        from PIL import Image
        with Image.open(io.BytesIO(data)) as source:
            cover = source.convert('RGB')
        cover.thumbnail((width, height))
        canvas = Image.new('RGB', (width, height), (20, 20, 24))
        canvas.paste(cover, ((width - cover.width) // 2, (height - cover.height) // 2))
        output = io.BytesIO()
        canvas.save(output, format='BMP')
        return output.getvalue()
    except (ImportError, OSError, ValueError):
        return None


def handle(handler, owner, path, app):
    """Serve the same metadata already available to opted-in LAN web clients."""
    if path not in ('/api/track-details', '/api/track-details/art', '/api/track-details/wallpaper'):
        return False
    if path == '/api/track-details':
        handler._json(200, snapshot(owner, app))
    else:
        params = parse_qs(handler.path.partition('?')[2])
        try:
            generation = int(params['generation'][0])
            index = int(params['index'][0]) if path.endswith('/art') else 0
        except (KeyError, IndexError, TypeError, ValueError):
            handler._json(400, {"error": "Artwork generation and index are required"})
            return True
        if path.endswith('/wallpaper'):
            try:
                width, height = int(params['width'][0]), int(params['height'][0])
                identity = params['identity'][0]
            except (KeyError, IndexError, TypeError, ValueError):
                handler._json(400, {"error": "Wallpaper size and owner identity are required"})
                return True
            instance = getattr(getattr(owner, 'workflows', None), 'instance', None)
            if (not instance or not instance.owns() or not identity
                    or not secrets.compare_digest(identity, instance.identity)):
                handler._json(409, {"error": "Official tray owner changed"})
                return True
            if not 320 <= width <= 1920 or not 240 <= height <= 1080:
                handler._json(400, {"error": "Wallpaper size is out of range"})
                return True
        art, mime = owner.art_snapshot_at_generation(generation, index)
        if art is None:
            handler._json(404, {"error": "Artwork no longer belongs to this track"})
        elif path.endswith('/wallpaper'):
            bitmap = wallpaper_bitmap(art, width, height)
            if bitmap is None:
                handler._json(503, {"error": "Could not render this album artwork"})
            elif not instance.owns() or not secrets.compare_digest(identity, instance.identity):
                handler._json(409, {"error": "Official tray owner changed"})
            else:
                handler._send(200, bitmap, 'image/bmp')
        else:
            preview, preview_mime = artwork_preview(art, mime)
            handler._send(200, preview, preview_mime)
    return True
