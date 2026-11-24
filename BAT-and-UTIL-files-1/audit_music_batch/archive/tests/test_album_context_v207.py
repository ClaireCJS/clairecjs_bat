import tempfile
import unittest
from pathlib import Path

import audit_music_batch as a


class AlbumContextTests(unittest.TestCase):
    def test_album_proposals_and_companions(self):
        albums = {
            "2013 - Focus Your Anger [EP]": [
                ("Gouge Away_Focus Your Anger_0101_Chemical X", "1_Chemical X"),
                ("Gouge Away_Focus Your Anger_0102_Good Will", "2_Good Will"),
                ("Gouge Away_Focus Your Anger_0103_Enough", "3_Enough")],
            "2013 - Still Bored [EP]": [
                ("1_Still Bored - Still Bored", "1_Still Bored"),
                ("2_Still Bored", "2_Still Bored"),
                ("3_Still Bored - Still Scorned Still Bored", "3_Still Scorned Still Bored")],
            "2016 - , Dies": [("12 - R.O.T", "12_R.O.T.")],
            "2017 - Swallow-Sweat [single]": [("Gouge Away - 02 - Sweat", "2_Sweat")],
            "2018 - Audiotree Live (live) (20181212) (NYC Portland Arms)": [
                ("1_Fed Up (Audiotree live version)", "1_Fed Up (Audiotree live version) (live) (20181212) (NYC Portland Arms)"),
                ("2_Studio Track", "2_Studio Track")],
            "2020 - Consider [single]": [
                ("1_Consider--Gouge Away[gouge away]-Consider B W Wave Of Mutilation", "1_Consider"),
                ("2_Wave Of Mutilation--Gouge Away[gouge away]-Consider B W Wave Of Mutilation", "2_Wave Of Mutilation (by Pixies)")],
            "2023 - Idealized": [("Gouge Away_Idealized_0101_Idealized", "1_Idealized")]}
        root = Path(tempfile.mkdtemp())
        self.addCleanup(a.recycle_path, root)
        for album, pairs in albums.items():
            d = root / "Gouge Away" / album
            d.mkdir(parents=True)
            extensions = [".flac", ".lrc", ".flac.bak.20261124.replaced-by-chatgpt.bak"]
            for old, _ in pairs:
                for ext in extensions:
                    (d / (old + ext)).touch()
            audit = a.BatchAudit(d)
            audit.files = list(d.iterdir())
            audit.audit_redundant_album_artist_filenames()
            rows = {Path(r["before"]).name: Path(r["after"]).name
                    for f in audit.findings for r in f.details.get("renames", [])}
            for old, new in pairs:
                for ext in extensions:
                    self.assertEqual(rows.get(old + ext, old + ext), new + ext)
            for f in audit.findings:
                if f.details.get("renames"):
                    a.apply_redundant_album_artist_filename_group(d, {"path": ".", "details": f.details})
            audit = a.BatchAudit(d)
            audit.files = list(d.iterdir())
            audit.audit_redundant_album_artist_filenames()
            self.assertFalse(audit.findings, (album, audit.findings))

    def test_edit_key(self):
        self.assertEqual(a.prompt_for_action_scope("Rename?", False, False,
                         key_reader=lambda: "e", allow_edit_name=True), "edit_name")

    def test_edit_group_with_one_audio_family(self):
        root = Path(tempfile.mkdtemp())
        self.addCleanup(a.recycle_path, root)
        d = root / "Gouge Away" / "2023 - Idealized"
        d.mkdir(parents=True)
        for ext in (".flac", ".lrc"):
            (d / ("Gouge Away_Idealized_0101_Idealized" + ext)).touch()
        audit = a.BatchAudit(d)
        audit.files = list(d.iterdir())
        audit.audit_redundant_album_artist_filenames()
        finding = audit.findings[0].as_dict()
        finding["code"] = "R1"
        keys = iter("ey")
        a.interactive_apply({"resolved_root": str(d), "findings": [finding]}, False,
                            key_reader=lambda: next(keys), input_reader=lambda _: "1_Custom.flac")
        self.assertTrue((d / "1_Custom.flac").is_file())
        self.assertTrue((d / "1_Custom.lrc").is_file())
