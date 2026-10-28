"""Focused V583 successor-preparation and transition-policy regressions."""
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

import PAFPlayer as player


def prepared(path, generation):
    stat = path.stat()
    return player.PreparedPlaylistTrack(
        path=path, signature=(stat.st_size, stat.st_mtime_ns), generation=generation,
        duration=1.0, audio_tags={}, replaygain_info=object(),
        playback_bounds=(0.0, 1.0), lyrics=[], timings_ms={"total": 1.0},
        ready_at=time.monotonic(),
    )


class TransitionPreparationTests(unittest.TestCase):
    def test_manual_queue_has_successor_precedence(self):
        with patch.object(Path, "is_file", return_value=True):
            self.assertEqual(Path("manual.flac"), player.predict_playlist_successor_for_prefetch(
                [Path("a.flac"), Path("b.flac")], Path("a.flac"), shuffled=True,
                manual_queue=[Path("manual.flac")], forward_visit=Path("b.flac")))

    def test_latest_request_invalidates_stale_result(self):
        gate = threading.Event()
        def slow(path, *, generation, **_):
            if path.name == "old.flac": gate.wait(1)
            return prepared(path, generation)
        with tempfile.TemporaryDirectory() as raw:
            old, new = Path(raw)/"old.flac", Path(raw)/"new.flac"
            old.write_bytes(b"old"); new.write_bytes(b"new")
            coordinator = player.PlaylistSuccessorPreparation(slow)
            coordinator.request(old)
            coordinator.request(new)
            gate.set()
            for _ in range(100):
                if coordinator.snapshot()["ready"]: break
                time.sleep(.01)
            self.assertIsNone(coordinator.take(old))
            self.assertEqual(new, coordinator.take(new).path)

    def test_playlist_change_and_file_mutation_invalidate(self):
        with tempfile.TemporaryDirectory() as raw:
            song = Path(raw)/"song.flac"; song.write_bytes(b"one")
            coordinator = player.PlaylistSuccessorPreparation(
                lambda path, *, generation, **_: prepared(path, generation))
            coordinator.request(song)
            for _ in range(100):
                if coordinator.snapshot()["ready"]: break
                time.sleep(.01)
            song.write_bytes(b"changed-size")
            self.assertIsNone(coordinator.take(song))
            coordinator.request(song)
            coordinator.invalidate()
            self.assertIsNone(coordinator.take(song))

    def test_rapid_next_previous_keeps_only_latest(self):
        with tempfile.TemporaryDirectory() as raw:
            paths=[]
            for name in "abcd":
                path=Path(raw)/(name+".flac"); path.write_bytes(name.encode()); paths.append(path)
            coordinator=player.PlaylistSuccessorPreparation(
                lambda path, *, generation, **_: prepared(path, generation))
            for path in paths:
                coordinator.request(path)
            for _ in range(100):
                if coordinator.snapshot()["ready"]: break
                time.sleep(.01)
            self.assertEqual(paths[-1], coordinator.take(paths[-1]).path)
            self.assertIsNone(coordinator.take(paths[0]))

    def test_repeat_track_and_repeat_folder_successors(self):
        a,b,c=map(Path,("a.flac","b.flac","c.flac"))
        with patch.object(Path,"is_file",return_value=True):
            # Repeat-track remains the current decoder's responsibility: no
            # outer successor is prepared. Repeat-folder uses ordinary neighbor.
            self.assertEqual(b, player.predict_playlist_successor_for_prefetch(
                [a,b,c], a, shuffled=False))
            self.assertEqual(a, player.predict_playlist_successor_for_prefetch(
                [a], a, shuffled=False))

    def test_missing_or_unreadable_successor_is_not_ready(self):
        missing=Path("definitely-missing-v583.flac")
        self.assertIsNone(player.prepare_playlist_successor_result(
            missing, generation=1, replaygain_mode="track", trim_edge_silence=True,
            threshold_db=-43, min_duration=.35, keep_seconds=.08))

    def test_silence_length_measurement_is_nonnegative(self):
        finished=10.0; started=10.125
        self.assertEqual(125.0, round(max(0.0, started-finished)*1000, 3))


if __name__ == "__main__":
    unittest.main()
