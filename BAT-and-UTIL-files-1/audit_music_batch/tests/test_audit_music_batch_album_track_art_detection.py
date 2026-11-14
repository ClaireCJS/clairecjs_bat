import unittest
from pathlib import Path

import audit_music_batch as audit


class AlbumTrackArtDetectionTests(unittest.TestCase):
    def test_years_in_title_do_not_make_track_numbered(self):
        audio = Path("Jane's Addiction - Imminent Redemption (2024) [first new single with original lineup in 34 years].flac")
        self.assertFalse(audit.is_album_track_filename(audio))
        self.assertEqual(audio.stem, audit.exported_art_sidecar_stem(audio, 3))

    def test_leading_track_number_still_uses_album_cover(self):
        audio = Path("01_Machine Messiah.flac")
        self.assertTrue(audit.is_album_track_filename(audio))
        self.assertEqual("cover", audit.exported_art_sidecar_stem(audio, 3))


if __name__ == "__main__":
    unittest.main()
