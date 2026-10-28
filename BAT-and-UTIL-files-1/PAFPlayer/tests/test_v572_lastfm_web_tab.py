"""Regression checks for the dedicated Last.fm web configuration tab."""

import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("pafplayer_v572_lastfm", ROOT / "PAFPlayer.py")
PAF = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = PAF
SPEC.loader.exec_module(PAF)


class LastFmWebTabTests(unittest.TestCase):
    def test_catalog_keeps_lastfm_actions_out_of_metadata(self):
        groups = {group["name"]: group["items"] for group in PAF.paf_web_action_catalog()}
        lastfm = {item["action"] for item in groups["Last.fm"]}
        metadata = {item["action"] for item in groups["Playlist / Metadata"]}
        self.assertEqual({PAF.WEB_VIEW_LASTFM_PROFILE, PAF.LASTFM_SCROBBLE_NOW}, lastfm)
        self.assertTrue(lastfm.isdisjoint(metadata))

    def test_tab_targets_its_own_section_and_reuses_existing_actions(self):
        html = PAF._paf_web_html()
        self.assertIn("['lastFmSection','Last.fm']", html)
        self.assertIn("if(displayName==='Last.fm')wrap.id='lastFmSection'", html)
        self.assertIn("(metadata||tags).after(lastFm)", html)
        self.assertIn("if(item.action==='web-view-lastfm-profile')openLastFmProfile()", html)
        self.assertIn("else action(item.action)", html)
        self.assertIn("/api/lastfm-profile", html)
        self.assertIn("Scrobbling requires Last.fm credentials", html)


if __name__ == "__main__":
    unittest.main()
