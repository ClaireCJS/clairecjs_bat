import importlib.util
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


dj = load("v710_dj", ROOT / "src" / "PAFPlayer_dj.py")
player = load("v710_player", ROOT / "PAFPlayer.py")


class V710DjWakeSleepTests(unittest.TestCase):
    def controller(self):
        runtime = SimpleNamespace(
            root=Path(tempfile.mkdtemp(prefix="paf-v710-dj-")),
            settings={},
            lock=threading.RLock(),
            stop_event=threading.Event(),
            save_settings=lambda: None,
            app=SimpleNamespace(windows_session_is_locked=lambda: False),
        )
        return dj.Controller(runtime, lambda *args: (["unused.wav"], ""))

    def test_manual_sleep_and_wake_override_schedule_for_session(self):
        controller = self.controller()
        controller.set_manual_sleep(True)
        self.assertEqual("manual sleep", controller.sleep_status()[0])
        self.assertTrue(controller.status()["manual_sleep_override"])
        self.assertFalse(controller.start(True, current={"artist": "A", "title": "B"}))
        controller.set_manual_sleep(False)
        self.assertEqual(("", ""), controller.sleep_status())
        self.assertFalse(controller.status()["manual_sleep_override"])

    def test_requested_aliases_and_web_controls_are_routed(self):
        source = (ROOT / "PAFPlayer.py").read_text(encoding="utf-8")
        for alias in ("djwake", "wakedj", "djsleep", "sleepdj", "sleeping", "bed", "bedtime", "sleepy", "sleep"):
            self.assertIn("'" + alias + "'", source)
        html = player._paf_web_html()
        self.assertIn('id="djWakeNow"', html)
        self.assertIn('id="djSleepNow"', html)
        self.assertIn("command(wake,'djwake'", html)
        self.assertIn("command(sleep,'djsleep'", html)
        self.assertTrue(player.paf_web_action_is_allowed(player._HASH_COMMAND_PREFIX + "djwake"))
        self.assertTrue(player.paf_web_action_is_allowed(player._HASH_COMMAND_PREFIX + "djsleep"))


class V710KaraokeExpansionTests(unittest.TestCase):
    def test_hidden_config_gives_auto_expanded_karaoke_the_freed_space(self):
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            )
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 900})
                html = player._paf_web_html()
                page.route("http://paf.test/", lambda route: route.fulfill(status=200, content_type="text/html", body=html))
                page.goto("http://paf.test/", wait_until="domcontentloaded")
                shown = page.evaluate(
                    """async () => {
                      localStorage.setItem('paf-config-panel-enabled','1');
                      setupConfigPanelToggle();
                      localStorage.setItem('paf-web-lyric-height-px','90');
                      karaokeAutoExpand=true; lyricText='A lyric line'; lyricReservedHeight=90;
                      updateKaraokeReservation();
                      await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
                      return document.getElementById('lyricDock').getBoundingClientRect().height;
                    }"""
                )
                page.locator("#configPanelToggle").click()
                page.wait_for_timeout(100)
                hidden = page.locator("#lyricDock").evaluate("el => el.getBoundingClientRect().height")
                self.assertGreater(hidden, shown + 100, (shown, hidden))
                page.locator("#configPanelToggle").click()
                page.wait_for_timeout(100)
                restored = page.locator("#lyricDock").evaluate("el => el.getBoundingClientRect().height")
                self.assertAlmostEqual(90, restored, delta=2)
            finally:
                browser.close()


if __name__ == "__main__":
    unittest.main()
