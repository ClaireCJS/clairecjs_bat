import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("v722_player", ROOT / "PAFPlayer.py")
PLAYER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PLAYER
SPEC.loader.exec_module(PLAYER)


class V722VisualizerHeightSliderTests(unittest.TestCase):
    def test_height_slider_is_wide_and_stale_status_cannot_snap_active_drag_back(self):
        from playwright.sync_api import sync_playwright

        schema = PLAYER.paf_web_control_schema()
        status = {
            "version": "V722",
            "visualizer_rows": 16,
            "visualizer_rows_auto_tallest": 1,
            "drcs_enabled": True,
            "visualizer_bars_enabled": True,
            "visualizer_background_artwork_enabled": True,
            "art_color_bars": True,
            "position_seconds": 0,
            "duration_seconds": 1,
            "playing": False,
            "paused": True,
        }
        html = PLAYER._paf_web_html()

        def route_request(route):
            url = route.request.url
            if url == "http://paf.test/":
                route.fulfill(status=200, content_type="text/html", body=html)
            elif url.endswith("/api/control-schema"):
                route.fulfill(status=200, content_type="application/json", body=json.dumps(schema))
            elif url.endswith("/api/status"):
                route.fulfill(status=200, content_type="application/json", body=json.dumps(status))
            else:
                route.fulfill(status=200, content_type="application/json", body="{}")

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            )
            try:
                page = browser.new_page(viewport={"width": 1800, "height": 1000})
                page.route("http://paf.test/**", route_request)
                page.goto("http://paf.test/", wait_until="domcontentloaded")
                slider = page.locator("#ctl-visualizer_rows")
                slider.wait_for(state="attached")
                page.evaluate("document.body.classList.remove('config-panel-disabled');setupConfigTabs()")
                page.locator('#configTabs [data-target="visualizerSection"]').click()
                slider.wait_for(state="visible")
                self.assertGreaterEqual(slider.evaluate("el => el.getBoundingClientRect().width"), 420)
                result = page.evaluate(
                    """() => {
                      const slider=document.getElementById('ctl-visualizer_rows');
                      const auto=document.getElementById('ctl-visualizer_rows_auto_tallest');
                      auto.checked=true;
                      slider.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,pointerId:1}));
                      slider.value='31';slider.dispatchEvent(new Event('input',{bubbles:true}));
                      syncControls({visualizer_rows:16,visualizer_rows_auto_tallest:1});
                      const during={value:slider.value,auto:auto.checked,label:document.getElementById('lbl-visualizer_rows').textContent};
                      slider.dispatchEvent(new PointerEvent('pointerup',{bubbles:true,pointerId:1}));
                      syncControls({visualizer_rows:16,visualizer_rows_auto_tallest:1});
                      const pending=slider.value;
                      syncControls({visualizer_rows:31,visualizer_rows_auto_tallest:0});
                      syncControls({visualizer_rows:22,visualizer_rows_auto_tallest:0});
                      return {during,pending,after:slider.value};
                    }"""
                )
                self.assertEqual("31", result["during"]["value"])
                self.assertFalse(result["during"]["auto"])
                self.assertIn("31 rows", result["during"]["label"])
                self.assertEqual("31", result["pending"])
                self.assertEqual("22", result["after"])
            finally:
                browser.close()


if __name__ == "__main__":
    unittest.main()
