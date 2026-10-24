from pathlib import Path
import contextlib
import io
import tempfile
import unittest
from unittest import mock

import audit_music_batch as audit


class FollowupAuditFixTests(unittest.TestCase):
    def test_punk_menu_accepts_a_typed_genre(self) -> None:
        finding = {
            "details": {
                "genres": ["Grime", "Hip Hop", "Pop Punk"],
                "genre_components": ["Grime", "Hip Hop", "Pop Punk"],
            }
        }
        with contextlib.redirect_stdout(io.StringIO()):
            selected = audit.prompt_for_punk_genre_selection(
                finding,
                use_color=False,
                input_reader=lambda _prompt: "Riot Grrrl",
            )
        self.assertEqual("Riot Grrrl", selected)

    def test_scope_prompt_offers_folder_no_and_remembered_file_no(self) -> None:
        options = audit.action_scope_options(
            False,
            False,
            allow_folder=True,
            allow_stop_folder=True,
        )
        self.assertIn("S=Not for This Folder", options)
        self.assertIn("R=No, Remember This File", options)

    def test_json_cleanup_scope_prompt_offers_audio_rename(self) -> None:
        options = audit.action_scope_options(
            True,
            False,
            allow_rename_audio=True,
        )
        self.assertIn("E=Rename Audio", options)

    def test_single_filename_normalization_shows_aligned_before_after(self) -> None:
        finding = {
            "category": "filename_marker_style",
            "path": (
                "Gang Of Four - Where The Nightingale Sings "
                "(Redux By 3D feat. Nova Twins) (2021).flac"
            ),
            "details": {
                "proposed_name": (
                    "Gang Of Four - Where The Nightingale Sings "
                    "(Redux By 3D feat Nova Twins) (2021).flac"
                )
            },
        }
        lines = audit.finding_target_lines(
            finding,
            use_color=False,
            terminal_columns=240,
        )
        rendered = "\n".join(lines)
        self.assertIn("Before filename", rendered)
        self.assertIn("After filename", rendered)
        self.assertIn("feat. Nova Twins", rendered)
        self.assertIn("feat Nova Twins", rendered)
        self.assertEqual(1, rendered.count("feat. Nova Twins"))

    def test_backups_never_prompt_and_follow_an_approved_filename_rename(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "01_Song (feat. Guest).flac"
            backup = root / (
                "01_Song (feat. Guest).flac.bak.202609090000."
                "replaced-by-chatgpt.bak"
            )
            source.write_bytes(b"live file")
            backup.write_bytes(b"historical backup")
            report = audit.BatchAudit(root).audit()
            marker_findings = [
                finding
                for finding in report["findings"]
                if finding["category"] == "filename_marker_style"
            ]
            self.assertEqual([source.name], [finding["path"] for finding in marker_findings])
            actions = audit.apply_finding(
                root,
                marker_findings[0],
                use_color=False,
            )
            destination = root / "01_Song (feat Guest).flac"
            moved_backup = root / (
                "01_Song (feat Guest).flac.bak.202609090000."
                "replaced-by-chatgpt.bak"
            )
            self.assertTrue(destination.is_file())
            self.assertTrue(moved_backup.is_file())
            self.assertFalse(source.exists())
            self.assertFalse(backup.exists())
            self.assertEqual(b"historical backup", moved_backup.read_bytes())
            self.assertTrue(moved_backup.name.casefold().endswith(".bak"))
            self.assertIn(f"renamed_backup:{moved_backup}", actions)

    def test_remembered_no_expires_when_the_file_changes(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            target = root / "01_Song.flac"
            target.write_bytes(b"original")
            store = audit.RememberedNoStore(root / "remembered.sqlite3")
            store.remember_no("all_caps_album_title", target)
            self.assertTrue(store.is_remembered_no("all_caps_album_title", target))
            target.write_bytes(b"changed content")
            self.assertFalse(store.is_remembered_no("all_caps_album_title", target))

    def test_grouped_rename_refreshes_missing_sources_instead_of_failing(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "1_Song.flac").write_bytes(b"already renamed elsewhere")
            finding = {
                "path": ".",
                "details": {
                    "renames": [
                        {"before": "01 - Song.flac", "after": "1_Song.flac"}
                    ]
                },
            }
            actions = audit.apply_redundant_album_artist_filename_group(root, finding)
        self.assertEqual(["unchanged:grouped_rename_sources_refreshed"], actions)

    def test_packed_disc_track_prefixes_normalize_single_and_multi_disc_sets(self) -> None:
        single = [
            Path("0101 - Choose Your Fighter.flac"),
            Path("0105 - Antagonist.flac"),
        ]
        profile = audit.packed_disc_track_profile(single)
        self.assertIsNotNone(profile)
        self.assertEqual(
            "5_Antagonist.flac",
            audit.capitalized_album_filename_proposal(
                "0105 - Antagonist.flac",
                5,
                packed_track_profile=profile,
            ),
        )
        multi = [
            Path("0105 - First Disc.flac"),
            Path("0210 - Second Disc.flac"),
        ]
        multi_profile = audit.packed_disc_track_profile(multi)
        self.assertIsNotNone(multi_profile)
        self.assertEqual(
            "1_05_First Disc.flac",
            audit.capitalized_album_filename_proposal(
                "0105 - First Disc.flac",
                15,
                packed_track_profile=multi_profile,
            ),
        )
        self.assertEqual(
            "2_10_Second Disc.flac",
            audit.capitalized_album_filename_proposal(
                "0210 - Second Disc.flac",
                15,
                packed_track_profile=multi_profile,
            ),
        )

    def test_redundant_single_disc_prefixes_become_two_digit_tracks(self) -> None:
        files = [
            Path(f"1_{track:02d}{' ' if track % 2 else '_'}Track {track}.flac")
            for track in range(1, 14)
        ]
        profile = audit.single_disc_track_prefix_profile(files)
        self.assertIsNotNone(profile)
        self.assertEqual(
            "01_Be Somebody.flac",
            audit.capitalized_album_filename_proposal(
                "1_01_Be Somebody.flac",
                13,
                single_disc_track_profile=profile,
            ),
        )
        self.assertEqual(
            "13_Power Out.flac",
            audit.capitalized_album_filename_proposal(
                "1_13_Power Out.flac",
                13,
                single_disc_track_profile=profile,
            ),
        )

    def test_json_audio_rename_keeps_both_files_when_filename_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            audio = root / "1_01 Be Somebody.flac"
            sidecar = root / "1_01 Be Somebody.json"
            audio.write_bytes(b"audio")
            sidecar.write_text("{}", encoding="utf-8")
            with mock.patch.object(audit, "recycle_path") as recycle, contextlib.redirect_stdout(io.StringIO()):
                actions = audit.prompt_for_json_audio_rename(
                    sidecar,
                    use_color=False,
                    input_reader=lambda _prompt: audio.name,
                )
            self.assertEqual([], actions)
            self.assertTrue(audio.is_file())
            self.assertTrue(sidecar.is_file())
            recycle.assert_not_called()

    def test_json_audio_rename_moves_family_then_recycles_json(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            audio = root / "1_01 Be Somebody.flac"
            sidecar = root / "1_01 Be Somebody.json"
            matching_lrc = root / "1_01 Be Somebody.lrc"
            audio.write_bytes(b"audio")
            sidecar.write_text("{}", encoding="utf-8")
            matching_lrc.write_text("lyrics", encoding="utf-8")
            renamed_audio = root / "01_Be Somebody.flac"
            renamed_json = root / "01_Be Somebody.json"
            renamed_lrc = root / "01_Be Somebody.lrc"
            with mock.patch.object(
                audit,
                "migrate_waveform_review_cache_path",
                return_value=[],
            ), mock.patch.object(
                audit,
                "recycle_path",
                side_effect=lambda path: Path(path),
            ) as recycle, contextlib.redirect_stdout(io.StringIO()):
                actions = audit.prompt_for_json_audio_rename(
                    sidecar,
                    use_color=False,
                    input_reader=lambda _prompt: renamed_audio.name,
                )
            self.assertTrue(renamed_audio.is_file())
            self.assertTrue(renamed_lrc.is_file())
            self.assertTrue(renamed_json.is_file())
            self.assertFalse(audio.exists())
            self.assertFalse(matching_lrc.exists())
            recycle.assert_called_once_with(renamed_json)
            self.assertTrue(any(action.startswith("renamed_audio:") for action in actions))

    def test_preflight_renames_folder_art_notes_and_incomplete_marker(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            album = root / "2022 - Example (incomplete)"
            album.mkdir()
            (album / "folder.jpg").write_bytes(b"jpeg")
            (album / "album.nfo").write_text("notes", encoding="utf-8")
            _normalized_root, actions = audit.normalize_batch_preflight_paths(root)
            normalized = root / "2022 - Example [incomplete]"
            self.assertTrue(normalized.is_dir())
            self.assertTrue((normalized / "cover.jpg").is_file())
            self.assertTrue((normalized / "readme.txt").is_file())
            self.assertTrue(any(action.startswith("renamed_folder:") for action in actions))

    def test_audio_rename_migrates_waveform_approval_and_pair_cache(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "01_Old.flac"
            destination = root / "1_New.flac"
            source.write_bytes(b"unchanged audio")
            store = audit.WaveformApprovalStore(root / "approvals.sqlite3")
            store.approve(source)
            cache_root = root / "waveforms"
            with mock.patch.object(audit, "waveform_staging_root", return_value=cache_root):
                old_before, old_after = audit.replaygain_bake_waveform_cache_paths(source)
                old_before.parent.mkdir(parents=True)
                old_before.write_bytes(b"before")
                old_after.write_bytes(b"after")
                source.rename(destination)
                actions = audit.migrate_waveform_review_cache_path(
                    source,
                    destination,
                    approval_store=store,
                )
                new_before, new_after = audit.replaygain_bake_waveform_cache_paths(destination)
            self.assertTrue(store.is_approved(destination))
            self.assertTrue(new_before.is_file())
            self.assertTrue(new_after.is_file())
            self.assertTrue(any(action.startswith("migrated_waveform_approval:") for action in actions))

    def test_xml_and_json_are_prompted_cleanup_categories(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "metadata.json").write_text('{"source": "test"}', encoding="utf-8")
            (root / "metadata.xml").write_text("<root><source>test</source></root>", encoding="utf-8")
            report = audit.BatchAudit(root).audit()
        categories = {finding["category"] for finding in report["findings"]}
        self.assertIn("json_sidecar", categories)
        self.assertIn("xml_sidecar", categories)


if __name__ == "__main__":
    unittest.main(verbosity=2)
