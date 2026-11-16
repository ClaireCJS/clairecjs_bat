from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import PAFPlayer
from PAFPlayer_error_delivery import ErrorAlerts


class V651IdleDanceAndSessionErrorTests(unittest.TestCase):
    def test_configurable_dance_range_remains_monitor_safe(self):
        monitor = (0, 0, 1920, 1080, True, "DISPLAY1")
        geometry = (520, 520, 700, 200)
        small = PAFPlayer.external_album_art_idle_drift_bounds(geometry, geometry, monitor, 1)
        large = PAFPlayer.external_album_art_idle_drift_bounds(geometry, geometry, monitor, 20)
        self.assertGreater(large[1] - large[0], small[1] - small[0])
        self.assertGreaterEqual(large[0], 5)
        self.assertLessEqual(large[1] + geometry[0], 1915)
        self.assertGreaterEqual(large[2], 5)
        self.assertLessEqual(large[3] + geometry[1], 1075)

    def test_zero_dance_range_holds_origin(self):
        monitor = (0, 0, 1920, 1080, True, "DISPLAY1")
        geometry = (400, 300, 500, 250)
        self.assertEqual((500, 500, 250, 250), PAFPlayer.external_album_art_idle_drift_bounds(geometry, geometry, monitor, 0))

    def test_error_ledger_is_newest_first_and_deduplicated(self):
        alerts = ErrorAlerts()
        settings = {"ErrorPopupEnabled": 0, "ErrorWindowsNotificationEnabled": 0, "ErrorSoundEnabled": 0}
        with tempfile.TemporaryDirectory() as temp:
            first = Path(temp) / "missing-one.flac"
            second = Path(temp) / "missing-two.flac"
            self.assertTrue(alerts.emit(path=first, reason="missing", settings=settings))
            self.assertFalse(alerts.emit(path=first, reason="missing", settings=settings))
            self.assertTrue(alerts.emit(path=second, reason="missing", settings=settings, continuing=False))
            snapshot = alerts.snapshot()
        self.assertEqual(["missing-two.flac", "missing-one.flac"], [item["filename"] for item in snapshot])
        self.assertFalse(snapshot[0]["continuing"])
        self.assertIn("No playable track", snapshot[0]["outcome"])

    def test_web_badge_and_error_routes_are_present(self):
        source = Path(PAFPlayer.__file__).read_text(encoding="utf-8")
        for marker in ('id="sessionErrorBadge"', 'path == "/errors"', 'path == "/api/session-errors"', "session_error_count"):
            self.assertIn(marker, source)


if __name__ == "__main__":
    unittest.main()
