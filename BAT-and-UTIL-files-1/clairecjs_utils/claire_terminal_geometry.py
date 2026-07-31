"""Query live Windows terminal geometry, including character-cell pixels.

The VT query path works with terminal emulators such as Windows Terminal.
Classic consoles fall back to the Win32 console APIs.
"""

from __future__ import annotations

import argparse
import ctypes
import json
import math
import os
import re
import time
from ctypes import wintypes
from dataclasses import asdict, dataclass


ENABLE_ECHO_INPUT = 0x0004
ENABLE_LINE_INPUT = 0x0002
ENABLE_VIRTUAL_TERMINAL_INPUT = 0x0200
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
KEY_EVENT = 0x0001
OPEN_EXISTING = 3


class Coord(ctypes.Structure):
    _fields_ = (("x", ctypes.c_short), ("y", ctypes.c_short))


class SmallRect(ctypes.Structure):
    _fields_ = (
        ("left", ctypes.c_short),
        ("top", ctypes.c_short),
        ("right", ctypes.c_short),
        ("bottom", ctypes.c_short),
    )


class ConsoleScreenBufferInfo(ctypes.Structure):
    _fields_ = (
        ("size", Coord),
        ("cursor_position", Coord),
        ("attributes", wintypes.WORD),
        ("window", SmallRect),
        ("maximum_window_size", Coord),
    )


class ConsoleFontInfoEx(ctypes.Structure):
    _fields_ = (
        ("size", wintypes.ULONG),
        ("font_index", wintypes.DWORD),
        ("font_size", Coord),
        ("font_family", wintypes.UINT),
        ("font_weight", wintypes.UINT),
        ("face_name", wintypes.WCHAR * 32),
    )


class KeyEventRecord(ctypes.Structure):
    _fields_ = (
        ("key_down", wintypes.BOOL),
        ("repeat_count", wintypes.WORD),
        ("virtual_key_code", wintypes.WORD),
        ("virtual_scan_code", wintypes.WORD),
        ("unicode_char", wintypes.WCHAR),
        ("control_key_state", wintypes.DWORD),
    )


class InputEvent(ctypes.Union):
    _fields_ = (
        ("key_event", KeyEventRecord),
        ("padding", ctypes.c_byte * 16),
    )


class InputRecord(ctypes.Structure):
    _fields_ = (
        ("event_type", wintypes.WORD),
        ("event", InputEvent),
    )


@dataclass(frozen=True)
class TerminalGeometry:
    columns: int
    rows: int
    cell_width: int
    cell_height: int
    viewport_width: int
    viewport_height: int
    font_face: str
    source: str

    @property
    def chafa_options(self) -> str:
        # Chafa's pixel protocols define one view cell as 8x8 pixels. Scale
        # the terminal's character grid by its real cell height so Sixel
        # output reaches the physical viewport, while font-ratio accounts for
        # the cell's non-square width.
        sixel_scale = self.cell_height / 8
        view_width = max(1, math.floor(self.columns * sixel_scale))
        view_height = max(1, math.floor(self.rows * sixel_scale))
        return (
            f"--view-size={view_width}x{view_height} "
            f"--font-ratio={self.cell_width}/{self.cell_height}"
        )


def _kernel32():
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateFileW.argtypes = (
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    )
    kernel32.CreateFileW.restype = wintypes.HANDLE
    return kernel32


def _console_handle(kernel32, name: str):
    handle = kernel32.CreateFileW(
        name,
        GENERIC_READ | GENERIC_WRITE,
        FILE_SHARE_READ | FILE_SHARE_WRITE,
        None,
        OPEN_EXISTING,
        0,
        None,
    )
    invalid = ctypes.c_void_p(-1).value
    return None if handle in (None, invalid) else handle


def _vt_response(
    kernel32,
    input_handle,
    output_handle,
    timeout_seconds: float,
) -> str:
    original_mode = wintypes.DWORD()
    if not kernel32.GetConsoleMode(input_handle, ctypes.byref(original_mode)):
        return ""

    query_mode = (
        original_mode.value
        & ~(ENABLE_LINE_INPUT | ENABLE_ECHO_INPUT)
    ) | ENABLE_VIRTUAL_TERMINAL_INPUT
    if not kernel32.SetConsoleMode(input_handle, query_mode):
        return ""

    response: list[str] = []
    try:
        query = "\x1b[14t\x1b[16t\x1b[18t"
        written = wintypes.DWORD()
        if not kernel32.WriteConsoleW(
            output_handle,
            query,
            len(query),
            ctypes.byref(written),
            None,
        ):
            return ""

        deadline = time.monotonic() + max(0.05, timeout_seconds)
        records = (InputRecord * 64)()
        while time.monotonic() < deadline and response.count("t") < 3:
            pending = wintypes.DWORD()
            if not kernel32.GetNumberOfConsoleInputEvents(
                input_handle,
                ctypes.byref(pending),
            ):
                break
            if pending.value == 0:
                time.sleep(0.005)
                continue

            read = wintypes.DWORD()
            if not kernel32.ReadConsoleInputW(
                input_handle,
                records,
                min(len(records), pending.value),
                ctypes.byref(read),
            ):
                break
            for index in range(read.value):
                record = records[index]
                if record.event_type != KEY_EVENT:
                    continue
                key = record.event.key_event
                if not key.key_down or not key.unicode_char:
                    continue
                response.extend(key.unicode_char * max(1, key.repeat_count))
        return "".join(response)
    finally:
        kernel32.SetConsoleMode(input_handle, original_mode.value)


def query_terminal_geometry(
    *,
    timeout_seconds: float = 1.2,
) -> TerminalGeometry:
    """Return geometry for the terminal attached to the current process."""
    if os.name != "nt":
        size = os.get_terminal_size()
        return TerminalGeometry(
            columns=size.columns,
            rows=size.lines,
            cell_width=1,
            cell_height=2,
            viewport_width=size.columns,
            viewport_height=size.lines * 2,
            font_face="",
            source="posix",
        )

    kernel32 = _kernel32()
    input_handle = _console_handle(kernel32, "CONIN$")
    output_handle = _console_handle(kernel32, "CONOUT$")
    if input_handle is None or output_handle is None:
        size = os.get_terminal_size()
        return TerminalGeometry(
            columns=size.columns,
            rows=size.lines,
            cell_width=8,
            cell_height=16,
            viewport_width=size.columns * 8,
            viewport_height=size.lines * 16,
            font_face="",
            source="fallback",
        )

    try:
        response = _vt_response(
            kernel32,
            input_handle,
            output_handle,
            timeout_seconds,
        )

        viewport_match = re.search(r"\x1b\[4;(\d+);(\d+)t", response)
        cell_match = re.search(r"\x1b\[6;(\d+);(\d+)t", response)
        text_match = re.search(r"\x1b\[8;(\d+);(\d+)t", response)

        screen = ConsoleScreenBufferInfo()
        have_screen = bool(
            kernel32.GetConsoleScreenBufferInfo(
                output_handle,
                ctypes.byref(screen),
            )
        )
        font = ConsoleFontInfoEx()
        font.size = ctypes.sizeof(font)
        have_font = bool(
            kernel32.GetCurrentConsoleFontEx(
                output_handle,
                False,
                ctypes.byref(font),
            )
        )

        columns = (
            int(text_match.group(2))
            if text_match
            else (
                screen.window.right - screen.window.left + 1
                if have_screen
                else 0
            )
        )
        rows = (
            int(text_match.group(1))
            if text_match
            else (
                screen.window.bottom - screen.window.top + 1
                if have_screen
                else 0
            )
        )
        cell_width = (
            int(cell_match.group(2))
            if cell_match
            else (font.font_size.x if have_font else 0)
        )
        cell_height = (
            int(cell_match.group(1))
            if cell_match
            else (font.font_size.y if have_font else 0)
        )
        viewport_width = (
            int(viewport_match.group(2))
            if viewport_match
            else columns * cell_width
        )
        viewport_height = (
            int(viewport_match.group(1))
            if viewport_match
            else rows * cell_height
        )

        if columns <= 0 or rows <= 0:
            fallback = os.get_terminal_size()
            columns = max(1, fallback.columns)
            rows = max(1, fallback.lines)
        if cell_width <= 0 and viewport_width > 0:
            cell_width = max(1, round(viewport_width / columns))
        if cell_height <= 0 and viewport_height > 0:
            cell_height = max(1, round(viewport_height / rows))
        cell_width = max(1, cell_width or 8)
        cell_height = max(1, cell_height or 16)
        viewport_width = max(1, viewport_width or columns * cell_width)
        viewport_height = max(1, viewport_height or rows * cell_height)

        return TerminalGeometry(
            columns=columns,
            rows=rows,
            cell_width=cell_width,
            cell_height=cell_height,
            viewport_width=viewport_width,
            viewport_height=viewport_height,
            font_face=font.face_name if have_font else "",
            source="vt" if (
                viewport_match or cell_match or text_match
            ) else "win32",
        )
    finally:
        kernel32.CloseHandle(input_handle)
        kernel32.CloseHandle(output_handle)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--format",
        choices=("json", "chafa"),
        default="json",
    )
    parser.add_argument("--timeout", type=float, default=1.2)
    args = parser.parse_args(argv)
    geometry = query_terminal_geometry(timeout_seconds=args.timeout)
    if args.format == "chafa":
        print(geometry.chafa_options)
    else:
        print(json.dumps(asdict(geometry), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
