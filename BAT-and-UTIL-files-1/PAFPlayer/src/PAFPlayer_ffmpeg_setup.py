"""Explicit, checksum-verified FFmpeg setup in private PAFPlayer storage."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import uuid
from urllib.parse import urlsplit
from urllib.request import urlopen
import zipfile


MAX_ARCHIVE_BYTES = 2 * 1024 * 1024 * 1024
MAX_UNPACKED_BYTES = 5 * 1024 * 1024 * 1024
MAX_MEMBERS = 10000


def support_root():
    base = os.environ.get('LOCALAPPDATA') or str(Path.home() / 'AppData' / 'Local')
    return Path(base) / 'PAFPlayer' / 'support' / 'ffmpeg'


def _installed_sets(root=None):
    root = Path(root) if root is not None else support_root()
    if not root.is_dir():
        return []
    found = []
    for folder in root.iterdir():
        if not folder.is_dir() or not (folder / 'manifest.json').is_file():
            continue
        binaries = list(folder.rglob('ffmpeg.exe'))
        for ffmpeg in binaries:
            ffplay = ffmpeg.with_name('ffplay.exe')
            if ffplay.is_file():
                found.append((folder.stat().st_mtime_ns, folder, ffmpeg.parent))
                break
    return sorted(found, reverse=True)


def private_binary(name, root=None):
    if os.name != 'nt' or name not in ('ffmpeg', 'ffplay', 'ffprobe'):
        return None
    for _mtime, _folder, bin_dir in _installed_sets(root):
        candidate = bin_dir / (name + '.exe')
        if candidate.is_file():
            return candidate
    return None


def _version(binary):
    result = subprocess.run([str(binary), '-version'], capture_output=True,
                            text=True, timeout=15, check=True)
    line = (result.stdout or '').splitlines()[0] if result.stdout else ''
    if 'version' not in line.casefold():
        raise ValueError(str(binary.name) + ' did not report an FFmpeg version')
    return line.strip()


def _validate_source(url, expected_sha256):
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('FFmpeg ZIP source must be an HTTPS URL without embedded credentials')
    digest = str(expected_sha256).strip().lower()
    if not re.fullmatch('[0-9a-f]{64}', digest):
        raise ValueError('Expected SHA-256 must be exactly 64 hexadecimal characters')
    return digest, parsed.hostname


def _safe_extract(archive, target):
    with zipfile.ZipFile(archive) as zipped:
        members = zipped.infolist()
        if len(members) > MAX_MEMBERS or sum(item.file_size for item in members) > MAX_UNPACKED_BYTES:
            raise ValueError('FFmpeg ZIP exceeds the extraction safety limit')
        for item in members:
            normalized = item.filename.replace('\\', '/')
            parts = PurePosixPath(normalized).parts
            mode = item.external_attr >> 16
            if (not parts or normalized.startswith('/') or ':' in parts[0]
                    or any(part in ('', '.', '..') for part in parts)
                    or stat.S_ISLNK(mode)):
                raise ValueError('FFmpeg ZIP contains an unsafe path or link')
            destination = target.joinpath(*parts)
            if item.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                with zipped.open(item) as source, destination.open('xb') as output:
                    shutil.copyfileobj(source, output, length=1024 * 1024)


def install(url, expected_sha256, *, confirm=input, opener=urlopen, root=None):
    """Download only after explicit approval; leave existing installs untouched."""
    digest, host = _validate_source(url, expected_sha256)
    root = Path(root) if root is not None else support_root()
    prompt = (f'Download FFmpeg ZIP from {host}, verify SHA-256 {digest}, and install into '
              f'{root}? No PATH changes. Type YES to continue: ')
    if confirm(prompt).strip() != 'YES':
        raise InterruptedError('FFmpeg setup cancelled before download')
    root.mkdir(parents=True, exist_ok=True)
    for _mtime, folder, bin_dir in _installed_sets(root):
        if folder.name == digest:
            return {'path': str(bin_dir), 'version': _version(bin_dir / 'ffmpeg.exe'),
                    'sha256': digest, 'already_installed': True}
    stage = root / ('_install-' + uuid.uuid4().hex)
    stage.mkdir(exist_ok=False)
    try:
        archive = stage / 'download.zip'
        hasher = hashlib.sha256()
        total = 0
        with opener(url, timeout=30) as response, archive.open('xb') as output:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_ARCHIVE_BYTES:
                    raise ValueError('FFmpeg ZIP exceeds the download safety limit')
                output.write(chunk)
                hasher.update(chunk)
        if hasher.hexdigest() != digest:
            raise ValueError('FFmpeg ZIP SHA-256 mismatch; installation was rejected')
        payload = stage / 'payload'
        payload.mkdir()
        _safe_extract(archive, payload)
        candidates = list(payload.rglob('ffmpeg.exe'))
        bin_dir = next((item.parent for item in candidates if item.with_name('ffplay.exe').is_file()), None)
        if bin_dir is None:
            raise ValueError('The verified ZIP does not contain ffmpeg.exe and ffplay.exe together')
        versions = {name: _version(bin_dir / (name + '.exe')) for name in ('ffmpeg', 'ffplay')}
        (stage / 'manifest.json').write_text(json.dumps({
            'sha256': digest, 'source_host': host, 'versions': versions,
        }, indent=2), encoding='utf-8')
        relative_bin = bin_dir.relative_to(stage)
        destination = root / digest
        index = 1
        while destination.exists():
            destination = root / (digest + ' (' + str(index) + ')')
            index += 1
        stage.rename(destination)
        stage = None
        installed_bin = destination / relative_bin
        return {'path': str(installed_bin), 'version': versions['ffmpeg'],
                'sha256': digest, 'already_installed': False}
    finally:
        if stage is not None and stage.exists():
            try:
                from send2trash import send2trash
                send2trash(str(stage))
            except Exception as exc:
                raise RuntimeError('Incomplete FFmpeg staging kept at ' + str(stage)
                                   + ' because recycling failed: ' + str(exc)) from exc


def run_cli(arguments):
    if len(arguments) != 2:
        print('Usage: PAFPlayer --setup-ffmpeg HTTPS-ZIP-URL EXPECTED-SHA256')
        return 2
    try:
        result = install(arguments[0], arguments[1])
    except (ValueError, OSError, InterruptedError, RuntimeError, zipfile.BadZipFile,
            subprocess.SubprocessError) as exc:
        print('FFmpeg setup: ' + str(exc))
        print('Manual fallback: install FFmpeg/FFplay yourself, or provide a trusted ZIP URL and its SHA-256.')
        return 1
    print('FFmpeg ready: ' + result['version'])
    print('Private binaries: ' + result['path'])
    print('SHA-256: ' + result['sha256'])
    return 0
