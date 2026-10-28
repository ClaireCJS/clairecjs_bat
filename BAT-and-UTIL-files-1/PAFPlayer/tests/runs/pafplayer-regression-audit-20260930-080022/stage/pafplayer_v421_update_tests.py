from pafplayer_v416_edit import ROOT, replace_file, sub

path = ROOT / 'test_play_audio_file_v416_external_media.py'
s = path.read_text(encoding='utf-8')
s = sub(s, '        return p.PAFExternalPlaybackCoordinator(monitor), monitor', '        controller = p.PAFExternalPlaybackCoordinator(monitor)\n        controller.filter_action(None, False, 0)\n        return controller, monitor')
s = sub(s, 'test_explicit_play_keeps_other_media_priority', 'test_explicit_play_overrides_current_media')
s = sub(s, '        self.assertIsNone(controller.filter_action(p.WEB_PLAY, True, 2))\n        self.assertEqual(p.EXTERNAL_MEDIA_PAUSE, controller.filter_action(None, False, 3))', '        self.assertEqual(p.WEB_PLAY, controller.filter_action(p.WEB_PLAY, True, 2))\n        self.assertIsNone(controller.filter_action(None, False, 3))')
replace_file(path, s)

path = ROOT / 'test_play_audio_file_v418.py'
s = path.read_text(encoding='utf-8')
s = sub(s, '        controller = p.PAFExternalPlaybackCoordinator(None)\n', '        controller = p.PAFExternalPlaybackCoordinator(None)\n        controller.last_snapshot = {"known": True, "active": ()}\n        controller.filter_action(None, False, 0)\n', 2)
replace_file(path, s)

path = ROOT / 'test_play_audio_file_v420.py'
s = path.read_text(encoding='utf-8')
s = sub(s, '        self.player = p.PAFExternalPlaybackCoordinator(self.monitor)\n', '        self.player = p.PAFExternalPlaybackCoordinator(self.monitor)\n        self.player.filter_action(None, False, 0)\n')
s = sub(s, 'test_redundant_play_while_playing_does_not_bypass_priority', 'test_redundant_play_acknowledges_current_media')
s = sub(s, 'self.assertEqual(p.EXTERNAL_MEDIA_PAUSE, self.player.filter_action(p.WEB_PLAY, False, 1))', 'self.assertEqual(p.WEB_PLAY, self.player.filter_action(p.WEB_PLAY, False, 1))')
s = sub(s, 'test_resume_stays_held_and_new_vlc_cannot_be_ignored', 'test_resume_overrides_chrome_but_new_vlc_cannot_be_ignored')
s = sub(s, '            self.assertIsNone(self.player.filter_action(action, True, 2))\n            self.assertTrue(self.player.auto_paused)', '            self.assertEqual(action, self.player.filter_action(action, True, 2))\n            self.assertFalse(self.player.auto_paused)')
s = sub(s, 'test_only_disabling_setting_allows_simultaneous_playback', 'test_disabling_setting_allows_new_media_until_reenabled')
s = sub(s, "        self.monitor.value['active'] = ('VLC',)\n        self.assertEqual(p.WEB_PLAY, self.player.filter_action(p.WEB_PLAY, True, 1, enabled=False))", "        self.assertEqual(p.WEB_PLAY, self.player.filter_action(p.WEB_PLAY, True, 1, enabled=False))\n        self.monitor.value['active'] = ('VLC',)")
s = sub(s, 'test_play_after_manual_pause_arms_resume_after_media_finishes', 'test_play_after_manual_pause_immediately_resumes')
s = sub(s, '        self.assertIsNone(self.player.filter_action(p.WEB_PLAY, True, 2))', '        self.assertEqual(p.WEB_PLAY, self.player.filter_action(p.WEB_PLAY, True, 2))')
s = sub(s, '        self.assertEqual(p.EXTERNAL_MEDIA_RESUME, self.player.filter_action(None, True, 5))\n        self.assertEqual((15, 0), self.player.fade_arguments())', '        self.assertIsNone(self.player.filter_action(None, False, 5))\n        self.assertIsNone(self.player.fade_arguments())')
s = sub(s, "        monitor.value['active'] = ('chrome',)\n        coordinator = p.PAFExternalPlaybackCoordinator(monitor)", "        coordinator = p.PAFExternalPlaybackCoordinator(monitor)\n        coordinator.filter_action(None, False, 0)\n        monitor.value['active'] = ('chrome',)")
s = sub(s, "                self.assertTrue(paused[0], 'Play incorrectly released the automatic hold')\n                self.assertEqual(1, len(commands))", "                self.assertFalse(paused[0], 'Play must release the automatic hold')\n                self.assertEqual(2, len(commands))")
s = sub(s, '                return p.PAUSE_TOGGLE\n            if phase[0] == 2:', '                return None\n            if phase[0] == 2:')
s = sub(s, "'Space incorrectly released the automatic hold'", "'New VLC playback must interrupt after Chrome override'")
s = sub(s, "                monitor.value['active'] = ()\n                phase[0] = 3", "                monitor.value['active'] = ('chrome',)\n                phase[0] = 3")
s = sub(s, 'phase[0] == 3 and len(commands) == 2', 'phase[0] == 3 and len(commands) == 3')
s = sub(s, "' '.join(commands[1])", "' '.join(commands[2])")
s = sub(s, 'self.assertIsNotNone(processes[1].poll())', 'self.assertIsNotNone(processes[2].poll())')
s = sub(s, '        self.assertEqual(2, len(commands))\n        self.assertEqual(5, phase[0])', '        self.assertEqual(3, len(commands))\n        self.assertEqual(5, phase[0])')
replace_file(path, s)
