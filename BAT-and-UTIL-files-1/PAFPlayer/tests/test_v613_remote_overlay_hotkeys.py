"""V613 tray-only overlay hotkeys and portable per-server settings."""

import inspect
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PAFPlayer_remote_overlay import RemoteOverlays
from PAFPlayer_remote_tray import RemoteHotkeys, RemoteTrayAppSettings, run_tray_only
from PAFPlayer_tray_machine import TrayMachineEffects


class RemoteOverlayHotkeyTests(unittest.TestCase):
    def test_ctrl_alt_and_shift_alias_request_local_show_not_server_control(self):
        keys = RemoteHotkeys()
        for letter, action in (('a', 'art_show'), ('f', 'floating_show')):
            for shift in (False, True):
                keys.sample(lambda _code: False, now=1)
                pressed = {keys.VK['ctrl'], keys.VK['alt'], keys.VK[letter]}
                if shift:
                    pressed.add(keys.VK['shift'])
                self.assertEqual([('local', action, 100.0)],
                                 keys.sample(lambda code: code in pressed, now=2, epoch=100))
        self.assertIn('overlays.show(floating=action == \'floating_show\')',
                      inspect.getsource(run_tray_only))

    def test_show_is_idempotent_and_saved_for_this_server(self):
        with tempfile.TemporaryDirectory() as folder:
            settings = RemoteTrayAppSettings('musicbox:666', folder)
            machine = TrayMachineEffects(None, mock.Mock(), lambda: None,
                                         remote=True, settings=settings)
            overlays = RemoteOverlays(mock.Mock(), machine)
            with mock.patch.object(overlays, 'start'):
                self.assertTrue(overlays.show(floating=False))
                self.assertTrue(overlays.show(floating=False))
                self.assertTrue(overlays.show(floating=True))
            self.assertEqual([('foreground', False), ('foreground', False),
                              ('foreground', True)],
                             [overlays._requests.get_nowait() for _ in range(3)])
            saved = RemoteTrayAppSettings('MUSICBOX:666', folder).options()
            self.assertTrue(saved['remote_album_art'])
            self.assertTrue(saved['remote_floating_lyrics'])
            self.assertFalse(RemoteTrayAppSettings('other:666', folder).options()['remote_album_art'])

    def test_copying_server_json_restores_portable_choices_on_another_computer(self):
        with tempfile.TemporaryDirectory() as old, tempfile.TemporaryDirectory() as new:
            before = RemoteTrayAppSettings('musicbox:666', old)
            before.set_option('remote_album_art', True)
            before.set_option('remote_floating_lyrics', True)
            before.set_option('remote_hotkeys', False)
            after = RemoteTrayAppSettings('MUSICBOX:666', new)
            after.path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(before.path, after.path)
            self.assertEqual(before.options(), after.options())
            self.assertEqual(before.path.name, after.path.name)
            self.assertFalse(RemoteTrayAppSettings('other:666', new).options()['remote_album_art'])


if __name__ == '__main__':
    unittest.main()
