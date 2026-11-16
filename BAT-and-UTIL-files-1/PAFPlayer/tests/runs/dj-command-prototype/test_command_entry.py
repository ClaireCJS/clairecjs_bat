import unittest
from command_entry import CommandEntry

class Tests(unittest.TestCase):
    def test_timeout_and_normal_keys(self):
        p = CommandEntry()
        self.assertEqual((False, None), p.feed('d', 0))
        self.assertEqual((True, None), p.feed('#', 0))
        for i, c in enumerate('DJforce'):
            self.assertEqual((True, None), p.feed(c, .1 * (i + 1)))
        self.assertIsNone(p.expire(2.19))
        self.assertEqual('djforce', p.expire(2.2))
        self.assertIsNone(p.expire(3))
    def test_edit_submit_cancel(self):
        p = CommandEntry()
        for c in '#djx\b': p.feed(c, 0)
        self.assertEqual((True, 'dj'), p.feed('\r', .1))
        p.feed('#', 1); p.feed('d', 1); p.feed('\x1b', 1)
        self.assertEqual((False, None), p.feed('j', 1))
    def test_expiration_preserves_next_shortcut(self):
        p = CommandEntry()
        p.feed('#', 0); p.feed('d', .1); p.feed('j', .2)
        self.assertEqual((False, 'dj'), p.feed('x', 2))
    def test_empty_timeout_and_bounded_input(self):
        p = CommandEntry(); p.feed('#', 0)
        self.assertIsNone(p.expire(2))
        p.feed('#', 3)
        for _ in range(100): p.feed('a', 3)
        self.assertEqual(32, len(p.feed('\r', 3)[1]))

if __name__ == '__main__': unittest.main()
