"""Focused border cursors and custom maximize/restore on a real Tk header."""
import contextlib
import threading
import unittest
from types import SimpleNamespace
from unittest import mock

import PAFPlayer as app
import test_v642_artwork_chrome as chrome


class WindowControlTests(unittest.TestCase):
    tearDown = chrome.HeaderTests.tearDown

    def setUp(self):
        chrome.HeaderTests.setUp(self)
        self.rect = (100, 100, 800, 400)
        self.monitors = [(0, 0, 1920, 1040, True, 'primary'),
                         (-1920, -200, 0, 880, False, 'left')]
        self.owner = SimpleNamespace(_lock=threading.Lock(), _native_rect_transient=False)
        self.ns.update(windows_window_rect=lambda _: self.rect,
                       external_album_art_monitor_work_areas=lambda: self.monitors,
                       external_album_art_idle_monitor_for_rect=app.external_album_art_idle_monitor_for_rect,
                       clamp_external_album_art_geometry=app.clamp_external_album_art_geometry,
                       _parse_external_album_art_geometry=app._parse_external_album_art_geometry,
                       clear_native_aspect_constraint=mock.Mock(), save_geometry_now=mock.Mock(),
                       end_idle_art_routine=mock.Mock())
        self.ns['self'] = self.owner
        def move(hwnd, rect):
            self.rect = tuple(rect)
            return True
        self.ns['windows_set_window_rect'] = mock.Mock(side_effect=move)
        self.button = self.state['artwork_maximize_button']

    def motion(self, x, y):
        self.root.event_generate('<Motion>', x=x-100, y=y-100, rootx=x, rooty=y)
        self.root.update_idletasks()
        return self.root.cget('cursor')

    def test_all_eight_edges_use_windows_resize_cursors_and_interior_resets(self):
        cases = [(100, 200, 'size_we'), (799, 200, 'size_we'),
                 (400, 100, 'size_ns'), (400, 399, 'size_ns'),
                 (100, 100, 'size_nw_se'), (799, 399, 'size_nw_se'),
                 (799, 100, 'size_ne_sw'), (100, 399, 'size_ne_sw')]
        for x, y, cursor in cases:
            with self.subTest(x=x, y=y):
                self.assertEqual(cursor, self.motion(x, y))
                self.assertEqual('', self.motion(400, 200))
        self.assertEqual('', self.motion(99, 200))

    def test_focus_hides_only_button_and_border_without_reflow(self):
        before = self.root.geometry(), self.state['identity_label'].winfo_width()
        self.assertTrue(self.button.winfo_ismapped())
        self.assertEqual('size_we', self.motion(100, 200))
        self.ns['hide_focus_chrome_immediately']()
        self.root.update_idletasks()
        self.assertFalse(self.button.winfo_ismapped())
        self.assertEqual('', self.root.cget('cursor'))
        self.assertEqual('', self.motion(100, 200))
        self.assertEqual('#010203', self.root.cget('background'))
        self.assertTrue(self.state['artwork_web_button'].winfo_ismapped())
        self.assertEqual(before, (self.root.geometry(), self.state['identity_label'].winfo_width()))
        self.ns['apply_focus_chrome'](); self.root.update_idletasks()
        self.assertTrue(self.button.winfo_ismapped())

    def test_maximize_uses_work_area_and_restores_exact_normal_rectangle(self):
        original = self.rect
        self.button.invoke()
        self.assertEqual((0, 0, 1920, 1040), self.rect)
        self.assertTrue(self.state['chrome_maximized'])
        self.assertTrue(self.owner._native_rect_transient)
        self.assertEqual('❐', self.button.cget('text'))
        self.assertEqual('', self.motion(0, 0))
        self.ns['hide_focus_chrome_immediately']()
        self.ns['apply_focus_chrome']()
        self.button.invoke()
        self.assertEqual(original, self.rect)
        self.assertFalse(self.state['chrome_maximized'])
        self.assertFalse(self.owner._native_rect_transient)
        self.assertEqual('□', self.button.cget('text'))

    def test_secondary_monitor_negative_coordinates_and_removed_monitor_restore(self):
        original = self.rect = (-1700, -100, -1000, 300)
        self.button.invoke()
        self.assertEqual((-1920, -200, 0, 880), self.rect)
        self.button.invoke()
        self.assertEqual(original, self.rect)
        self.button.invoke()
        self.monitors = self.monitors[:1]
        self.button.invoke()
        x, y, right, bottom = self.rect
        self.assertGreaterEqual(x, 0); self.assertGreaterEqual(y, 0)
        self.assertLessEqual(right, 1920); self.assertLessEqual(bottom, 1040)
        self.assertEqual((700, 400), (right-x, bottom-y))

    def test_failed_window_move_preserves_state_and_restore_target(self):
        original = self.rect
        self.ns['windows_set_window_rect'].side_effect = None
        self.ns['windows_set_window_rect'].return_value = False
        self.button.invoke()
        self.assertFalse(self.state['chrome_maximized'])
        self.assertNotIn('chrome_restore_rect', self.state)
        self.assertFalse(self.owner._native_rect_transient)
        self.assertEqual(original, self.rect)

    def test_maximized_save_keeps_the_normal_geometry_and_placement(self):
        normal = self.rect
        self.button.invoke()
        self.ns.update(current_geometry=lambda: '1920x1040+0+0',
                       save_external_album_art_geometry=mock.Mock(),
                       save_external_album_art_placement=mock.Mock())
        chrome.functions(self.ns, 'save_geometry_now')
        self.ns['save_geometry_now']()
        self.ns['save_external_album_art_geometry'].assert_called_once_with('700x300+100+100')
        self.assertEqual(normal, self.ns['save_external_album_art_placement'].call_args.args[0])
        self.assertEqual(normal, self.owner._outer_rect_snapshot)

    def test_resize_drag_holds_diagonal_cursor_until_released(self):
        self.root.event_generate('<ButtonPress-1>', x=699, y=299, rootx=799, rooty=399)
        self.assertEqual('size_nw_se', self.root.cget('cursor'))
        self.root.event_generate('<B1-Motion>', x=600, y=240, rootx=700, rooty=340)
        self.assertEqual('size_nw_se', self.root.cget('cursor'))
        self.root.event_generate('<ButtonRelease-1>', x=100, y=100, rootx=200, rooty=200)
        self.assertEqual('', self.root.cget('cursor'))
        self.assertNotIn('chrome_drag', self.state)


if __name__ == '__main__':
    unittest.main()
