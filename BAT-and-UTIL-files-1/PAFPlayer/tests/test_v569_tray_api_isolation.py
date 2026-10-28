"""Regression coverage for shared ctypes prototypes and paused lyric retries."""
import ctypes
from ctypes import wintypes
import io
import os
from pathlib import Path
import sys
import types
import unittest
from unittest import mock
import uuid

import PAFPlayer_tray as tray
import PAFPlayer_tray_hover as hover
import PAFPlayer_tray_machine as machine


class LyricRetryTests(unittest.TestCase):
    def controller(self):
        runtime = types.SimpleNamespace(log=mock.Mock())
        controller = tray.TrayController(runtime, types.SimpleNamespace(owns=lambda: True), click_window=.4)
        controller._visible = True
        controller._lyric_bubble = mock.Mock()
        return controller

    def test_paused_unchanged_lyric_is_only_shown_once(self):
        controller = self.controller()
        for _ in range(100):
            controller._sync_lyric_bubble('The same paused line')
        controller._lyric_bubble.show.assert_called_once_with('The same paused line')
        controller.runtime.log.assert_not_called()

    def test_native_failure_does_not_escape_or_repeat_until_line_changes(self):
        controller = self.controller()
        controller._lyric_bubble.show.side_effect = ctypes.ArgumentError('argument 3: wrong type')
        for _ in range(100):
            controller._sync_lyric_bubble('Paused line')
        self.assertEqual(controller._lyric_bubble.show.call_count, 1)
        self.assertEqual(controller.runtime.log.call_count, 1)
        controller._lyric_bubble.show.side_effect = None
        controller._sync_lyric_bubble('Next line')
        self.assertEqual(controller._lyric_bubble.show.call_count, 2)

    def test_toggle_off_then_on_retries_same_line(self):
        controller = self.controller()
        controller._lyric_bubble.show.side_effect = OSError('Temporary native error')
        controller._sync_lyric_bubble('Line')
        controller._sync_lyric_bubble('')
        controller._lyric_bubble.hide.assert_called_once_with()
        controller._lyric_bubble.show.side_effect = None
        controller._sync_lyric_bubble('Line')
        self.assertEqual(controller._lyric_bubble.show.call_count, 2)

    def test_hidden_tray_hides_bubble_and_contains_hide_and_log_failures(self):
        controller = self.controller()
        controller._sync_lyric_bubble('Line')
        controller._visible = False
        controller._lyric_bubble.hide.side_effect = OSError('Cannot hide')
        controller.runtime.log.side_effect = OSError('Cannot log')
        for _ in range(100):
            controller._sync_lyric_bubble('Line')
        controller._lyric_bubble.hide.assert_called_once_with()
        self.assertEqual(controller._lyric_bubble.show.call_count, 1)


@unittest.skipUnless(os.name == 'nt', 'Requires real Windows APIs')
class NativeApiTests(unittest.TestCase):
    def setUp(self):
        self.shared = ctypes.windll.user32.SystemParametersInfoW
        self.original = self.shared.argtypes, self.shared.restype
        self.addCleanup(self.restore_shared)
        self.shared.argtypes = [wintypes.UINT, wintypes.UINT, wintypes.LPWSTR, wintypes.UINT]
        self.shared.restype = wintypes.BOOL

    def restore_shared(self):
        self.shared.argtypes, self.shared.restype = self.original

    def test_exact_reported_collision_reproduced_and_private_query_succeeds(self):
        rect = wintypes.RECT()
        with self.assertRaisesRegex(ctypes.ArgumentError, 'argument 3'):
            self.shared(0x0030, 0, ctypes.byref(rect), 0)
        work = hover._work_area()
        self.assertGreater(work.right, work.left)
        self.assertGreater(work.bottom, work.top)
        self.assertIsNot(hover._native()[0].SystemParametersInfoW, self.shared)
        self.assertIs(self.shared.argtypes[2], wintypes.LPWSTR)

    def test_read_wallpaper_does_not_mutate_shared_prototype(self):
        self.shared.argtypes = [wintypes.UINT, wintypes.UINT, ctypes.c_void_p, wintypes.UINT]
        expected = list(self.shared.argtypes)
        self.assertIsInstance(machine.current_wallpaper(), str)
        self.assertEqual(self.shared.argtypes, expected)

    def test_wallpaper_setter_uses_private_function_without_setting_real_wallpaper(self):
        private = mock.Mock(return_value=1)
        library = mock.MagicMock()
        library.__getitem__.return_value = private
        expected = list(self.shared.argtypes)
        with mock.patch.object(machine.ctypes, 'WinDLL', return_value=library):
            machine.set_wallpaper('test-only.bmp')
        library.__getitem__.assert_called_once_with('SystemParametersInfoW')
        self.assertEqual(private.call_args.args[:3], (0x0014, 0, 'test-only.bmp'))
        self.assertEqual(self.shared.argtypes, expected)

    def test_work_area_failure_surfaces_as_os_error(self):
        native = mock.Mock()
        native.SystemParametersInfoW.return_value = 0
        with mock.patch.object(hover, '_native', return_value=(native, None, None, None)):
            with self.assertRaises(OSError):
                hover._work_area()

    def test_native_windows_alternate_paints_without_callback_errors_or_resource_leak(self):
        # Real HWNDs/HDCs and actual WM_PAINT dispatch; no player instance is started.
        user = ctypes.WinDLL('user32', use_last_error=True)
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        user.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        user.SendMessageW.restype = ctypes.c_ssize_t
        user.IsWindowVisible.argtypes = [wintypes.HWND]
        user.IsWindowVisible.restype = wintypes.BOOL
        user.IsWindow.argtypes = [wintypes.HWND]
        user.IsWindow.restype = wintypes.BOOL
        user.GetGuiResources.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        user.GetGuiResources.restype = wintypes.DWORD
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        process = kernel.GetCurrentProcess()
        callbacks = []
        previous_hook = sys.unraisablehook
        sys.unraisablehook = lambda item: callbacks.append(str(item.exc_value))
        self.addCleanup(setattr, sys, 'unraisablehook', previous_hook)
        # Windows creates process-wide drawing objects on the first real paint.
        # Warm both complete painting paths before testing subsequent cycles.
        before = None
        owner = 'PAFTest-' + uuid.uuid4().hex
        handles = []
        for cycle in range(4):
            bubble = hover.LyricBubble(None, 1, owner)
            card = hover.HoverCard(None, 1, owner)
            try:
                self.assertTrue(bubble.hwnd)
                self.assertTrue(card.hwnd)
                handles.extend((bubble.hwnd, card.hwnd))
                from PIL import Image
                bmp = io.BytesIO()
                Image.new('RGB', (8, 8), (20, 100, 200)).save(bmp, format='BMP')
                card.set_bitmap(bmp.getvalue())
                for index in range(12):
                    bubble.show('PAFPlayer tray regression test')
                    card.show({'metadata': {'Artist': 'Tray test', 'Song': 'API isolation'}})
                    self.assertTrue(user.IsWindowVisible(bubble.hwnd))
                    self.assertTrue(user.IsWindowVisible(card.hwnd))
                    user.SendMessageW(bubble.hwnd, 0x000F, 0, 0)
                    user.SendMessageW(card.hwnd, 0x000F, 0, 0)
                bubble.hide()
                card.hide()
                self.assertFalse(user.IsWindowVisible(bubble.hwnd))
                self.assertFalse(user.IsWindowVisible(card.hwnd))
            finally:
                bubble.close()
                card.close()
            resources = [user.GetGuiResources(process, kind) for kind in (0, 1)]
            if before is None:
                before = resources
            else:
                self.assertEqual(resources, before, 'No GDI/USER growth after each close')
        self.assertFalse(callbacks, callbacks)
        self.assertTrue(all(not user.IsWindow(hwnd) for hwnd in handles))
        after = [user.GetGuiResources(process, kind) for kind in (0, 1)]
        self.assertEqual(after, before, 'Popup windows/fonts/brushes/classes must be released')


class BundleTests(unittest.TestCase):
    def test_release_embeds_fixed_external_tray_sources(self):
        import PAFPlayer as player
        root = Path(__file__).resolve().parents[1]
        for name in ('PAFPlayer_tray', 'PAFPlayer_tray_hover', 'PAFPlayer_tray_machine'):
            self.assertEqual(player._PAF_BUNDLED_SOURCES[name], (root / 'src' / (name + '.py')).read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
