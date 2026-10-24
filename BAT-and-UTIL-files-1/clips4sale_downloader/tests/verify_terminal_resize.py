"""Offline Windows pseudo-console smoke test; never opens a browser/download.

Run with the project Python. Requires pywinpty. Retains its diagnostic report
in a unique terminal-check-* directory, without overwriting/deleting files.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import threading
import time
import uuid


def child(report: Path):
    import clip4sale_preview_downloader as downloader

    panel = downloader.ProgressPanel()
    observed = []
    try:
        panel.set_total(20)
        panel.total.update(7)
        panel.transfer_progress(7 * 1048576, 10 * 1048576, "📥 Offline sample.mp4")
        for message in ("📥 Saved: sample.mp4", "↩️ Already complete", "🔁 Retry",
                        "⚠️ Media error: sample", "🎬 Clip heading", "🌐 Browser information"):
            panel.log(message)
        panel.log("TERMINAL_CHECK_READY")
        deadline = time.monotonic() + 7
        while time.monotonic() < deadline:
            with panel._lock:
                size = (panel.columns, panel.rows)
                if size not in observed:
                    # No draw/update calls here: the idle resize watcher must
                    # have noticed the actual console device changing size.
                    observed.append(size)
                    for label in ("🌈 Global", "📥 Offline sample.mp4"):
                        line = panel._progress_line(label, 7, 20, size[0])
                        assert panel._display_width(line) == size[0] - 1
            time.sleep(.02)
    finally:
        panel.close()
    with report.open("x", encoding="utf-8") as output:
        json.dump({"ansi": bool(panel.ansi), "sizes": observed,
                   "resize_thread_stopped": not panel._resize_thread.is_alive()}, output)


def parent():
    from winpty import PtyProcess

    folder = Path(__file__).resolve().parent / ("terminal-check-" + uuid.uuid4().hex)
    folder.mkdir()
    report = folder / "report.json"
    dimensions = [(80, 24), (180, 50), (70, 50), (60, 15), (120, 30)]
    environment = dict(os.environ, PYTHONUTF8="1", COLUMNS="80", LINES="24")
    environment.pop("C4SDL_NO_ANSI", None)
    process = PtyProcess.spawn(
        [sys.executable, "-B", str(Path(__file__).resolve()), "--child", str(report)],
        cwd=str(folder.parent), env=environment, dimensions=(24, 80))
    chunks = []
    ready = threading.Event()

    def read_console():
        while True:
            try:
                chunk = process.read(65536)
            except (EOFError, OSError):
                return
            chunks.append(chunk)
            if "\x1b[6n" in chunk:
                process.write("\x1b[1;1R")
            if "TERMINAL_CHECK_READY" in "".join(chunks):
                ready.set()

    reader = threading.Thread(target=read_console, daemon=True)
    reader.start()
    try:
        assert ready.wait(10), "Pseudo-console did not initialize"
        for columns, rows in dimensions[1:]:
            process.setwinsize(rows, columns)
            time.sleep(.6)
        deadline = time.monotonic() + 10
        while process.isalive() and time.monotonic() < deadline:
            time.sleep(.05)
        assert not process.isalive(), "Offline console test did not finish"
        reader.join(timeout=1)
        assert process.exitstatus == 0, "Pseudo-console child failed"
        result = json.loads(report.read_text(encoding="utf-8"))
        assert result["ansi"] and result["resize_thread_stopped"], result
        assert result["sizes"] == [list(size) for size in dimensions], result
        assert "38;2;" in "".join(chunks), "No true-color output reached the console"
        print("PASS: live Windows console grow/shrink, idle redraw, full-width bars, colors, cleanup")
        print("Report:", report)
    finally:
        with (folder / "console.txt").open("x", encoding="utf-8") as output:
            output.write("".join(chunks))
        # The bounded child exits itself; never signal other console jobs.
        if not process.isalive():
            process.close()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--child":
        child(Path(sys.argv[2]))
    else:
        parent()
