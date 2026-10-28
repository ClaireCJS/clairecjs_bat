import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class V558GlobalSpeedTests(unittest.TestCase):
    def test_library_reconciliation_is_debounced_and_cancelled(self):
        source = (ROOT / 'PAFPlayer.py').read_text(encoding='utf-8')
        start = source.index('def _start_query_reconciliation')
        section = source[start:source.index('def _merge_reconciled', start)]
        self.assertIn('self._stop.wait(0.15)', section)
        self.assertIn('generation != self._query_scan_generation', section)
        worker = section[section.index('def worker() -> None:'):]
        self.assertLess(worker.index('self._stop.wait(0.15)'), worker.index('for root, _dirs, files in os.walk'))

    def test_tray_coalesces_registry_reads_and_hover_snapshots(self):
        source = (ROOT / 'PAFPlayer_tray.py').read_text(encoding='utf-8')
        self.assertIn('now - self._settings_cache_at < 0.5', source)
        self.assertIn('hover_now - self._last_hover_request_at >= 0.10', source)
        self.assertIn('self._invalidate_settings_cache()', source)

    def test_web_gallery_reuses_its_dom(self):
        source = (ROOT / 'PAFPlayer_tray.py').read_text(encoding='utf-8')
        self.assertIn("catalogSignature=''", source)
        self.assertIn('if(signature!==catalogSignature)', source)
        self.assertIn('gallery.replaceChildren(fragment)', source)
        self.assertIn('return TRAY_ICON_CATALOG', source)


if __name__ == '__main__':
    unittest.main()
