from pathlib import Path
import contextlib
import io
import tempfile
import unittest
from unittest import mock

import audit_music_batch as audit


class ReplayGainBakeProvenanceTests(unittest.TestCase):
    def test_signature_bound_database_record_skips_only_unchanged_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audio = root / "song.flac"
            database = root / "bakes.sqlite3"
            audio.write_bytes(b"original")
            store = audit.ReplayGainBakeStore(database)
            store.record(audio, -3.5)
            self.assertTrue(store.is_baked(audio))
            audio.write_bytes(b"changed")
            self.assertFalse(store.is_baked(audio))

    def test_candidates_exclude_file_with_durable_bake_provenance(self) -> None:
        paths = [Path("new.flac"), Path("already-baked.flac")]
        with mock.patch.object(
            audit, "waveform_replaygain_factor", return_value=0.5
        ), mock.patch.object(
            audit, "replaygain_bake_is_recorded",
            side_effect=lambda path, **_kwargs: path.name.startswith("already"),
        ):
            self.assertEqual([paths[0]], audit.replaygain_bake_candidates(paths))

    def test_batch_prompt_requires_key_and_list_returns_to_prompt(self) -> None:
        keys = iter(("\r", "l", "y"))
        output = io.StringIO()
        with mock.patch.object(audit, "invalid_key_beep") as beep, \
             contextlib.redirect_stdout(output):
            accepted = audit.prompt_for_replaygain_batch_bake(
                [Path("one.flac"), Path("two.mp3")],
                threshold_text="±0.05 dB", use_color=False,
                key_reader=lambda: next(keys),
            )
        self.assertTrue(accepted)
        beep.assert_called_once()
        rendered = output.getvalue()
        self.assertIn("Y=Yes / N=No / L=List files", rendered)
        self.assertIn("one.flac", rendered)
        self.assertIn("two.mp3", rendered)
        self.assertEqual(2, rendered.count("Bake ReplayGain into the audio data"))

    def test_multiple_embedded_art_exports_only_preferred_front(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audio = root / "01_Song.flac"
            front = b"\xff\xd8\xfffront"
            with mock.patch.object(
                audit, "embedded_pictures",
                return_value=[
                    (b"\xff\xd8\xffback", "image/jpeg", 4, "Back"),
                    (front, "image/jpeg", 3, "Front"),
                    (b"\xff\xd8\xffbooklet", "image/jpeg", 5, "Booklet"),
                ],
            ):
                exports = audit.export_art_sidecars(audio)
            self.assertEqual([str(root / "cover.jpg")], exports)
            self.assertEqual(front, (root / "cover.jpg").read_bytes())

    def test_rejecting_newly_exported_art_is_accepted_by_change_guard(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audio = root / "Song.flac"
            audio.write_bytes(b"audio")
            guard = audit.ActionChangeGuard(root)
            recycled = root / "mock-recycle-bin"
            recycled.mkdir()

            def fake_send2trash(value: str) -> None:
                source = Path(value)
                source.rename(recycled / source.name)

            with mock.patch.object(audit, "_ACTIVE_CHANGE_GUARD", guard), \
                 mock.patch.object(
                     audit, "embedded_pictures",
                     return_value=[(b"\xff\xd8\xfffront", "image/jpeg", 3, "Front")],
                 ):
                actions = [
                    f"exported_art:{path}"
                    for path in audit.export_art_sidecars(audio)
                ]
                with mock.patch.object(audit, "send2trash", fake_send2trash), \
                     contextlib.redirect_stdout(io.StringIO()):
                    approved = audit.review_extracted_art_sidecars(
                        actions, use_color=False, key_reader=lambda: "n",
                        preview_renderer=lambda *_args, **_kwargs: "preview",
                        audio_path=audio,
                    )
            self.assertFalse(approved)
            self.assertTrue(any(item.startswith("recycled_rejected_art:") for item in actions))
            self.assertEqual([], [path.name for path in root.glob("*.jpg")])
            self.assertTrue((recycled / "Song.rejected-by-username.jpg").is_file())

    def test_multiple_embedded_art_exports_only_front_as_one_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audio = root / "01_Song.flac"
            front = b"\xff\xd8\xfffront"
            back = b"\xff\xd8\xffback"
            with mock.patch.object(
                audit, "embedded_pictures",
                return_value=[(back, "image/jpeg", 4, "Back"),
                              (front, "image/jpeg", 3, "Front")],
            ):
                exports = audit.export_art_sidecars(audio)
            self.assertEqual([str(root / "cover.jpg")], exports)
            self.assertEqual(front, (root / "cover.jpg").read_bytes())
            self.assertEqual(["cover.jpg"], [path.name for path in root.glob("*.jpg")])


if __name__ == "__main__":
    unittest.main()
