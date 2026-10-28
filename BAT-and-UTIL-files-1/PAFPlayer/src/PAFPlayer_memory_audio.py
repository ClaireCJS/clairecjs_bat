"""Bounded, seekable RAM source for a playing audio file on Windows."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import ctypes
import re
import threading


def available_buffer_bytes() -> int:
    """Leave Windows and the decoder room; do not impose a fixed file-size cap."""
    class MEMORYSTATUSEX(ctypes.Structure):
        _fields_ = [('dwLength', ctypes.c_ulong), ('dwMemoryLoad', ctypes.c_ulong),
                    ('ullTotalPhys', ctypes.c_ulonglong), ('ullAvailPhys', ctypes.c_ulonglong),
                    ('ullTotalPageFile', ctypes.c_ulonglong), ('ullAvailPageFile', ctypes.c_ulonglong),
                    ('ullTotalVirtual', ctypes.c_ulonglong), ('ullAvailVirtual', ctypes.c_ulonglong),
                    ('ullAvailExtendedVirtual', ctypes.c_ulonglong)]

    try:
        status = MEMORYSTATUSEX()
        status.dwLength = ctypes.sizeof(status)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return 0
        available = min(status.ullAvailPhys, status.ullAvailPageFile, status.ullAvailVirtual)
        reserve = max(1024 ** 3, status.ullTotalPhys // 8)
        return max(0, available - reserve)
    except (AttributeError, OSError):
        return 0


class MemoryAudioSource:
    """Serve immutable track bytes over loopback so decoders never open the file."""

    def __init__(self, data: bytes, suffix: str):
        if not data:
            raise ValueError("Cannot buffer an empty audio file")
        self.data = data
        safe_suffix = suffix.casefold() if re.fullmatch(r"\.[a-zA-Z0-9]{1,10}", suffix) else ".audio"
        self.path = "/track" + safe_suffix
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_HEAD(self):
                self._send(body=False)

            def do_GET(self):
                self._send(body=True)

            def _send(self, *, body: bool):
                if self.path != owner.path:
                    self.send_error(404)
                    return
                size = len(owner.data)
                first, last = 0, size - 1
                raw_range = self.headers.get("Range", "")
                partial = bool(raw_range)
                if partial:
                    match = re.fullmatch(r"bytes=(\d*)-(\d*)", raw_range.strip())
                    if not match or not any(match.groups()):
                        self._range_error(size)
                        return
                    start_text, end_text = match.groups()
                    try:
                        if start_text:
                            first = int(start_text)
                            last = min(size - 1, int(end_text)) if end_text else size - 1
                        else:
                            first = max(0, size - int(end_text))
                    except ValueError:
                        self._range_error(size)
                        return
                    if first >= size or last < first:
                        self._range_error(size)
                        return
                self.send_response(206 if partial else 200)
                self.send_header("Content-Type", "application/octet-stream")
                self.send_header("Accept-Ranges", "bytes")
                self.send_header("Content-Length", str(last - first + 1))
                if partial:
                    self.send_header("Content-Range", f"bytes {first}-{last}/{size}")
                self.end_headers()
                if body:
                    try:
                        view = memoryview(owner.data)
                        for offset in range(first, last + 1, 64 * 1024):
                            self.wfile.write(view[offset:min(last + 1, offset + 64 * 1024)])
                    except (BrokenPipeError, ConnectionResetError):
                        pass

            def _range_error(self, size: int):
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.send_header("Content-Length", "0")
                self.end_headers()

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        self.url = f"http://127.0.0.1:{self.server.server_port}{self.path}"
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.1}, name="paf-memory-audio", daemon=True)
        try:
            self.thread.start()
        except Exception:
            self.server.server_close()
            raise

    @classmethod
    def try_open(cls, path: Path, max_bytes: int | None = None) -> MemoryAudioSource | None:
        path = Path(path)
        try:
            if max_bytes is None:
                max_bytes = available_buffer_bytes()
            size = path.stat().st_size
            if not 0 < size <= max_bytes:
                return None
            with path.open("rb") as stream:
                data = stream.read(size + 1)
            if len(data) != size:
                return None
            return cls(data, path.suffix)
        except (OSError, MemoryError, RuntimeError):
            return None

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=1)
