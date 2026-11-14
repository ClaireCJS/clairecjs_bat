import contextlib
import io
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest import TestCase, mock

import audit_music_batch as audit


class ReviewControlsTests(TestCase):
    def test_backfill_refreshes_observed_sidecar_for_later_folder_actions(self):
        root = Path(tempfile.mkdtemp(prefix="audit-backfill-snapshot-"))
        findings = []
        for stem in ("first", "second"):
            audio = root / f"{stem}.flac"
            audio.write_bytes(b"audio")
            audio.with_suffix(".lrc").write_text("[00:01.00]lyric\n")
            srt = audio.with_suffix(".srt")
            srt.write_text("old\n")
            os.utime(srt, (10, 10))
            findings.append({
                "category": "newer_lrc_needs_srt_backfill", "path": audio.name,
                "code": stem, "severity": "safe_fix", "message": "Newer LRC",
                "suggestion": "Backfill", "details": {},
            })
        observed = {str(path.resolve()): audit.action_file_state(path) for path in root.iterdir()}

        def convert(command, **_kwargs):
            lrc = Path(command[2])
            srt = lrc.with_suffix(".srt")
            srt.write_text("new\n")
            os.utime(srt, (20, 20))
            return mock.Mock(returncode=0, stdout="done", stderr="")

        with mock.patch.object(audit, "lrc2srt_executable", return_value=root / "lrc2srt.py"), \
             mock.patch.object(audit.subprocess, "run", side_effect=convert), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            result = audit.interactive_apply({
                "resolved_root": str(root), "findings": findings,
                "_observed_files": observed,
            }, False, key_reader=mock.Mock(return_value="y"))
        self.assertEqual(result["applied_codes"], "firstsecond", result)
        self.assertNotIn("RECHECK REQUIRED", output.getvalue())

    def test_newer_lrc_verifies_locally_and_skips_duplicate(self):
        root = Path(tempfile.mkdtemp(prefix="audit-newer-lrc-"))
        audio = root / "song.flac"
        audio.write_bytes(b"fixture")
        finding = {"category": "newer_lrc_needs_srt_backfill", "path": audio.name,
                   "code": "a", "severity": "safe_fix", "message": "Newer LRC",
                   "suggestion": "Backfill", "details": {}}
        def convert(path):
            path.with_suffix(".srt").write_text("1\n00:00:01,000 --> 00:00:02,000\nfixture\n")
            return [f"backfilled_srt:{path.with_suffix('.srt')}"]
        key = mock.Mock(return_value="y")
        with mock.patch.object(audit, "backfill_srt_from_lrc", side_effect=convert) as converter, mock.patch.object(audit, "audit_categories_by_path", side_effect=AssertionError("No full scan allowed")), contextlib.redirect_stdout(io.StringIO()):
            result = audit.interactive_apply({"resolved_root": str(root), "findings": [finding, {**finding, "code": "b"}]}, False, key_reader=key)
        self.assertEqual(result["applied_codes"], "a", result)
        self.assertEqual(result["skipped_codes"], "b", result)
        self.assertEqual(converter.call_count, 1)
        self.assertEqual(key.call_count, 1)

    def test_redraw_repeats_current_renderer_without_editing(self):
        for paired in (False, True):
            renderer, comparison, generator, editor = (mock.Mock() for _ in range(4))
            keys = iter(["r", "R", "n"])
            with contextlib.redirect_stdout(io.StringIO()):
                result = audit.waveform_review_choice(
                    Path("wave.jpg"), Path("song.mp3"), use_color=False,
                    key_reader=lambda: next(keys), preview_renderer=renderer,
                    comparison_preview_renderer=comparison, comparison_active=paired,
                    waveform_generator=generator, audio_editor=editor,
                )
            self.assertEqual(result, ("fine", 0, Path("song.mp3")))
            self.assertEqual((comparison if paired else renderer).call_count, 3)
            generator.assert_not_called()
            editor.assert_not_called()
        for color in (True, False):
            self.assertIn("Redraw", audit.waveform_review_choices(color))

    def test_extracted_art_always_is_scoped_to_passed_memory(self):
        memory = {}
        renderer = mock.Mock(return_value="test")
        with contextlib.redirect_stdout(io.StringIO()), mock.patch.object(audit, "image_resolution", return_value="10x10"):
            self.assertTrue(audit.artwork_review_choice(
                Path("a.jpg"), label="art", use_color=False,
                key_reader=lambda: "a", preview_renderer=renderer,
                approval_memory=memory,
            ))
            reader = mock.Mock(side_effect=AssertionError("must not prompt again"))
            self.assertTrue(audit.artwork_review_choice(
                Path("b.jpg"), label="art", use_color=False,
                key_reader=reader, preview_renderer=renderer,
                approval_memory=memory,
            ))
        self.assertEqual(renderer.call_count, 1)
        self.assertTrue(memory["always"])
        self.assertNotIn("Always", audit.artwork_review_choices(False))
        self.assertIn("Always", audit.artwork_review_choices(True, allow_always=True))

    def test_first_failed_waveform_does_not_abort_queue(self):
        paths = [Path("bad.flac"), Path("good.flac")]
        def generate(path, **kwargs):
            if path == paths[0]:
                raise RuntimeError("Cannot determine format of input after EOF")
            return Path("good.jpg"), None, None
        with mock.patch.object(audit, "generate_waveform_jpeg", side_effect=generate), ThreadPoolExecutor(1) as pool:
            futures, rendered = audit.prioritized_waveform_render_futures(
                paths, pool, Path("staging"), acceptable_silence_seconds=5,
            )
            self.assertNotIn(paths[0], rendered)
            self.assertIsInstance(futures[paths[0]].exception(), RuntimeError)
            self.assertEqual(futures[paths[1]].result()[0], Path("good.jpg"))

    def test_redirected_headings_are_single_line(self):
        with contextlib.redirect_stdout(io.StringIO()):
            lines = audit.double_height_gradient_section("Waveform review", True, ((1, 2, 3), (4, 5, 6)))
        self.assertEqual(len(lines), 1)

    def test_decoder_details_stay_out_of_console(self):
        with contextlib.redirect_stdout(io.StringIO()) as output, mock.patch.object(audit, "batch_event") as event:
            audit.print_file_error(Path("bad.flac"), RuntimeError("Cannot determine format after EOF\nsecret verbose diagnostic"), "Waveform unavailable", False)
        self.assertIn("Audio could not be decoded", output.getvalue())
        self.assertNotIn("secret", output.getvalue())
        self.assertIn("secret", event.call_args.kwargs["error"])
