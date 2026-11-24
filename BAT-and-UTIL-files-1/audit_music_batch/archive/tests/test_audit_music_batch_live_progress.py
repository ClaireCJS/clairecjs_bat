import contextlib
import io
from pathlib import Path
import threading
import unittest
from unittest import mock

import audit_music_batch as audit


class LiveBakeProgressTests(unittest.TestCase):
    def test_refreshes_while_no_file_has_finished_and_stops_on_error(self):
        refreshed = threading.Event()
        progress = mock.Mock()
        calls = []
        def refresh():
            calls.append(1)
            if len(calls) >= 2:
                refreshed.set()
        progress.refresh.side_effect = refresh
        with mock.patch.object(audit, "progress_bar", return_value=contextlib.nullcontext(progress)) as factory:
            with self.assertRaisesRegex(RuntimeError, "interrupted"):
                with audit.live_bake_progress(total=2, description="🎚 Test", enabled=True):
                    self.assertTrue(refreshed.wait(2), "Bar must refresh without file completion")
                    progress.update.assert_not_called()
                    raise RuntimeError("interrupted")
        self.assertFalse(any(t.name == "audit-bake-progress" for t in threading.enumerate()))
        self.assertNotIn("rainbow", factory.call_args.kwargs)

    def test_disabled_bar_starts_no_refresh_thread(self):
        with mock.patch.object(audit, "progress_bar", return_value=contextlib.nullcontext(None)):
            with audit.live_bake_progress(total=1, description="test", enabled=False) as progress:
                self.assertIsNone(progress)
        self.assertFalse(any(t.name == "audit-bake-progress" for t in threading.enumerate()))

    def test_status_has_emoji_filename_and_actual_stage(self):
        progress = mock.Mock()
        output = io.StringIO()
        output.isatty = lambda: True
        with mock.patch.object(audit.sys, "stderr", output):
            audit.update_stable_bake_status(progress, Path("track.flac"), "Rendering before-waveform")
        self.assertIn("🎵 Processing file: track.flac", output.getvalue())
        progress.set_description_str.assert_called_once_with("🎚 Rendering before-waveform", refresh=False)

    def test_placeholder_is_removed(self):
        source = Path(audit.__file__).read_text(encoding="utf-8")
        self.assertNotIn("Processing file: preparing", source)
        self.assertIn('print(f"📓 Recovery journal:', source)
