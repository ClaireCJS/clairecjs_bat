"""The mirrored Playback device default must save and remain visible."""

from pathlib import Path
import unittest
from unittest import mock

import PAFPlayer as app


class AudioSourceDefaultTests(unittest.TestCase):
    def test_output_combination_default_uses_existing_persistent_setting(self):
        devices = [
            {"value": -1, "label": "System default"},
            {"value": 0, "label": "Speakers"},
        ]
        with mock.patch.object(app, "waveout_output_devices", return_value=devices):
            with mock.patch.object(app, "save_user_default") as save:
                self.assertTrue(app.set_paf_web_choice_default("output_devices_mask", 2))
                save.assert_called_once_with("OutputDevicesMask", 2)

    def test_mirrored_def_click_saves_and_sits_beside_device_chooser(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.skipTest("Playwright is unavailable")
        browsers = (
            Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
            Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        )
        executable = next((path for path in browsers if path.is_file()), None)
        if executable is None:
            self.skipTest("A local Chromium browser is unavailable")

        html = app._paf_web_html()
        css = html.split("<style>", 1)[1].split("</style>", 1)[0]
        first = html.index("function makeMultiOutputDeviceControl(")
        device_js = html[first:html.index("let multiOutMicTimer=", first)]
        first = html.index("let playbackMirrorSource=null;")
        mirror_js = html[first:html.index("let configTabScrollRaf=", first)]
        harness = """
window.calls=[];
window.action=()=>{};
window.confirm=()=>true;
window.fetch=async (path,options)=>{
  const request=JSON.parse(options.body);
  window.calls.push(request);
  return {ok:true,json:async()=>({default_value:request.value,favorite_values:[]})};
};
""" + device_js + mirror_js + """
window.buildAudioSourceTest=()=>{
  const layout=document.createElement('div');layout.id='playbackLayout';
  document.body.appendChild(layout);
  const control=makeMultiOutputDeviceControl({
    key:'output_device',label:'Device:',default_value:1,favorite_values:[],
    options:[{value:-1,label:'System default'},{value:0,label:'Speakers'}]
  });
  control._setMultiOutputMask(2);
  layout.appendChild(control);
  setupMirroredPlayback(layout);
};
"""
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=str(executable), headless=True)
            try:
                page = browser.new_page(viewport={"width": 1200, "height": 700})
                page.set_content(
                    '<html><head><style>' + css + '</style></head><body>'
                    '<div id="playbackMirrorHost"></div></body></html>'
                )
                page.add_script_tag(content=harness)
                page.evaluate("buildAudioSourceTest()")
                page.locator("#playbackMirrorLayout input[type=radio]").click()
                page.wait_for_function("window.calls.length===1", timeout=3000)
                page.wait_for_function(
                    "document.querySelector('#playbackMirrorLayout input[type=radio]').checked",
                    timeout=3000,
                )
                self.assertEqual(
                    [{"kind": "default", "key": "output_devices_mask", "value": 2, "enabled": True}],
                    page.evaluate("window.calls"),
                )
                self.assertTrue(page.locator("#playbackLayout input[type=radio]").is_checked())
                geometry = page.evaluate("""() => {
  const control=document.querySelector('#playbackMirrorLayout [data-control-key="output_device"]');
  const button=control.querySelector('.multi-output-button').getBoundingClientRect();
  const def=control.querySelector('input[type=radio]').getBoundingClientRect();
  return {buttonTop:button.top,buttonHeight:button.height,buttonRight:button.right,
          defTop:def.top,defLeft:def.left};
}""")
                self.assertLess(abs(geometry["defTop"] - geometry["buttonTop"]), geometry["buttonHeight"])
                self.assertGreaterEqual(geometry["defLeft"], geometry["buttonRight"])
                page.locator("#playbackMirrorLayout input[type=radio]").click()
                self.assertEqual(1, len(page.evaluate("window.calls")))
            finally:
                browser.close()


if __name__ == "__main__":
    unittest.main()
