"""Regression tests for predicting the track prepared before playlist handoff."""
from pathlib import Path
import unittest
from unittest.mock import patch

import PAFPlayer as player


class SuccessorPredictionTests(unittest.TestCase):
    def setUp(self):
        self.a = Path("A.flac")
        self.b = Path("B.flac")
        self.c = Path("C.flac")
        self.d = Path("D.flac")
        self.alive = patch.object(Path, "is_file", return_value=True)
        self.alive.start()
        self.addCleanup(self.alive.stop)

    def test_shuffle_rotates_current_before_picking_next(self):
        order = [self.a, self.b, self.c]
        predicted = player.predict_playlist_successor_for_prefetch(
            order, self.a, shuffled=True, is_recent=lambda _: False)
        self.assertEqual(self.b, predicted)
        self.assertEqual([self.a, self.b, self.c], order)

    def test_shuffle_cooldown_chooses_same_safe_candidate_as_handoff(self):
        predicted = player.predict_playlist_successor_for_prefetch(
            [self.a, self.b, self.c], self.a, shuffled=True,
            is_recent=lambda track: track == self.b)
        self.assertEqual(self.c, predicted)

    def test_manual_queue_precedes_resume_and_history(self):
        predicted = player.predict_playlist_successor_for_prefetch(
            [self.a, self.b, self.c], self.a, shuffled=True,
            manual_queue=[self.d], resume_successor=self.c,
            forward_visit=self.b, is_recent=lambda _: True)
        self.assertEqual(self.d, predicted)

    def test_resume_precedes_forward_visit(self):
        predicted = player.predict_playlist_successor_for_prefetch(
            [self.a, self.b, self.c], self.a, shuffled=False,
            resume_successor=self.c, forward_visit=self.b)
        self.assertEqual(self.c, predicted)

    def test_forward_visit_precedes_unshuffled_neighbor(self):
        predicted = player.predict_playlist_successor_for_prefetch(
            [self.a, self.b, self.c], self.a, shuffled=False,
            forward_visit=self.c)
        self.assertEqual(self.c, predicted)

    def test_unshuffled_neighbor_and_empty_order(self):
        self.assertEqual(self.b, player.predict_playlist_successor_for_prefetch(
            [self.a, self.b, self.c], self.a, shuffled=False))
        self.assertIsNone(player.predict_playlist_successor_for_prefetch(
            [], self.a, shuffled=False))


if __name__ == "__main__":
    unittest.main()
