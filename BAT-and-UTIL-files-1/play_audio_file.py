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

Run ``play_audio_file.py --unit-tests`` to exercise the key mapping and the
restart-at-offset seeking controller without playing real audio.
"""

from __future__ import annotations

import contextlib
import io
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock


STOP = "stop"
SEEK_BACK_5 = "seek-back-5"
SEEK_FORWARD_5 = "seek-forward-5"
SEEK_BACK_15 = "seek-back-15"
SEEK_FORWARD_15 = "seek-forward-15"
PAUSE_TOGGLE = "pause-toggle"
LOOP_TOGGLE = "loop-toggle"
VOLUME_UP_5 = "volume-up-5"
VOLUME_DOWN_5 = "volume-down-5"
VOLUME_UP_20 = "volume-up-20"
VOLUME_DOWN_20 = "volume-down-20"

SEEK_SECONDS = {
    SEEK_BACK_5: -5.0,
    SEEK_FORWARD_5: 5.0,
    SEEK_BACK_15: -15.0,
    SEEK_FORWARD_15: 15.0,
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


def ffplay_executable() -> Path:
    """Locate FFplay, which performs the actual audio decoding and output."""
    discovered = shutil.which("ffplay")
    if not discovered:
        raise RuntimeError(
            "ffplay was not found in PATH; install FFmpeg to preview audio"
        )
    return Path(discovered)


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
        errors="replace",
    )
    try:
        duration = float(result.stdout.strip())
    except (TypeError, ValueError):
        return None
    return duration if math.isfinite(duration) and duration > 0 else None


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
    if first.casefold() in {"q", "x"}:
        return STOP
    if first == " " or first.casefold() == "p":
        return PAUSE_TOGGLE
    if first.casefold() == "l":
        return LOOP_TOGGLE
    if ctrl and first.casefold() in {"c", "w"}:
        return STOP
    if first not in {"\x00", "\xe0"}:
        return None
    if extended == "K":
        return SEEK_BACK_15 if shift else SEEK_BACK_5
    if extended == "M":
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
) -> list[str]:
    """Build a quiet, audio-only FFplay command starting at an offset."""
    return [
        str(executable),
        "-nodisp",
        "-autoexit",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        f"{max(0.0, start_seconds):.3f}",
        "-volume",
        str(volume),
        str(audio_path),
    ]


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


def render_status(position: float, duration: float | None, indicator: str) -> str:
    """Render the single, repaintable playback-status row."""
    fraction = position / duration if duration else 0.0
    return (
        "\r\033[2K" + ansi_rgb(rainbow_rgb(fraction))
        + f"{indicator} {format_position(position)}"
        + (f" / {format_position(duration)}" if duration is not None else "")
        + "\033[0m"
    )


def write_console(text: str) -> None:
    sys.stdout.write(text)
    sys.stdout.flush()


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
) -> str:
    """Play one audio file with seeking, pausing, volume, and looping."""
    audio_path = validate_file(file_path)
    player = ffplay or ffplay_executable()
    duration = duration_probe(audio_path)
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

    position = 0.0
    volume = 100
    looping = True
    process = None
    def finish_playback(result: str) -> str:
        """Replace the complete playback UI with its final, compact title."""
        write_console(
            "\r\033[4A\033[2K\033[32m🔊 Played:\033[0m "
            f"\033[34;3m{audio_path.name}\033[0m ({format_duration_label(duration)})"
            "\033[J\033[0m\n"
        )
        return result

    try:
        write_console(
            "\033[32m🔊 Playing:\033[0m "
            f"\033[34;3m{audio_path.name}\033[0m ({format_duration_label(duration)})\n"
            "\033[2;90m   Stop: Esc/X/Q/Ctrl+W/Alt+F4/Ctrl+C/Ctrl+Break\033[0m\n"
            "\033[2;90m   Seek: ← / → 5 seconds; Shift+← / Shift+→ 15 seconds\033[0m\n"
            "\033[2;90m   Pause: Space/P; volume: ↑/↓ (Shift = faster); loop: L (on)\033[0m\n"
        )
        indicator = "▶️"
        last_status_write = 0.0
        while True:
            command = ffplay_command(player, audio_path, position, volume)
            process = process_factory(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            segment_started = monotonic()
            while process.poll() is None:
                elapsed = max(0.0, monotonic() - segment_started)
                now = monotonic()
                if now - last_status_write >= 0.1:
                    write_console(render_status(position + elapsed, duration, indicator))
                    last_status_write = now
                if abort_requested.is_set():
                    stop_process(process)
                    return finish_playback("stopped")
                action = key_action_reader()
                if action == STOP:
                    stop_process(process)
                    return finish_playback("stopped")
                if action == LOOP_TOGGLE:
                    looping = not looping
                    state = "on" if looping else "off"
                    write_console(f"\r\033[2K\033[2;90mLoop {state}; volume {volume}%\033[0m")
                    continue
                if action in VOLUME_STEPS:
                    volume = min(100, max(0, volume + VOLUME_STEPS[action]))
                    position += elapsed
                    if duration is not None:
                        position = min(position, max(0.0, duration - 0.05))
                    stop_process(process)
                    write_console(f"\r\033[2K\033[2;90mVolume {volume}%\033[0m")
                    break
                if action == PAUSE_TOGGLE:
                    position += elapsed
                    if duration is not None:
                        position = min(position, max(0.0, duration - 0.05))
                    stop_process(process)
                    write_console("\r\033[2K⏸️ Paused")
                    while True:
                        paused_action = key_action_reader()
                        if abort_requested.is_set() or paused_action == STOP:
                            return finish_playback("stopped")
                        if paused_action == PAUSE_TOGGLE:
                            indicator = "▶️"
                            break
                        if paused_action == LOOP_TOGGLE:
                            looping = not looping
                            state = "on" if looping else "off"
                            write_console(f"\r\033[2K\033[2;90mPaused; loop {state}; volume {volume}%\033[0m")
                        if paused_action in VOLUME_STEPS:
                            volume = min(100, max(0, volume + VOLUME_STEPS[paused_action]))
                            write_console(f"\r\033[2K\033[2;90mPaused; volume {volume}%\033[0m")
                        sleeper(0.02)
                    break
                if action in SEEK_SECONDS:
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
                    }[action]
                    write_console(render_status(position, duration, indicator))
                    break
                sleeper(0.02)
            else:
                if abort_requested.is_set():
                    return finish_playback("stopped")
                if looping:
                    position = 0.0
                    indicator = "🔁"
                    continue
                return finish_playback("completed")
    finally:
        stop_process(process)
        for supported, previous in previous_handlers.items():
            signal.signal(supported, previous)


def play_audio_filename(audio_filename: str | os.PathLike[str]) -> str:
    """Convenience entry point for callers that pass a filename."""
    return play_audio_file(audio_filename)


class PlayWaveFileTests(unittest.TestCase):
    """Embedded unit coverage for controls and process restarts."""

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
        self.assertEqual(PAUSE_TOGGLE, interpret_console_key("p"))
        self.assertEqual(LOOP_TOGGLE, interpret_console_key("l"))
        self.assertEqual(
            VOLUME_UP_5,
            interpret_console_key("\xe0", extended="H"),
        )
        self.assertEqual(
            VOLUME_DOWN_20,
            interpret_console_key("\xe0", extended="P", shift=True),
        )

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


def run_unit_tests() -> int:
    """Run this script's embedded tests with normal unittest reporting."""
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        PlayWaveFileTests
    )
    return 0 if unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful() else 1


def main(argv: list[str] | None = None) -> int:
    """Run unit tests or preview the single supplied audio filename."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments == ["--unit-tests"]:
        return run_unit_tests()
    if len(arguments) != 1:
        print("Usage: play_audio_file.py <audio-file>")
        print("       play_audio_file.py --unit-tests")
        return 2
    try:
        play_audio_file(arguments[0])
    except KeyboardInterrupt:
        print("\n⏹️ Playback stopped.")
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
