from pafplayer_v416_edit import ROOT, edit, sub, replace_file

def transform(s):
    s = sub(s, '        self.acknowledged_sources = set()\n', '        self.acknowledged_sources = set()\n        self.last_confirmed_sources = set()\n')
    s = sub(s, '        # Existing background media is not a new interruption.', '''        if known:
            self.last_confirmed_sources = sources.copy()
        else:
            self.last_confirmed_sources.update(sources)
        # Existing background media is not a new interruption.''')
    s = sub(s, '        if requests_play:\n            self.acknowledged_sources.update(sources)', '        if requests_play:\n            self.acknowledged_sources.update(sources if known else self.last_confirmed_sources)')
    return s
edit(transform)
path = ROOT / 'test_play_audio_file_v417.py'
s = path.read_text(encoding='utf-8')
needle = '        controller = p.PAFExternalPlaybackCoordinator('
start = s.index('    def test_stop_cancels_automatic_resume')
end = s.index('\n', s.index(needle, start))
s = s[:end] + '\n        controller.last_snapshot = {"known": True, "active": ()}\n        controller.filter_action(None, False, 0)' + s[end:]
replace_file(path, s)
path = ROOT / 'test_play_audio_file_v421.py'
s = path.read_text(encoding='utf-8')
s = sub(s, '        self.assertFalse(self.player.auto_paused)\n\n    def test_manual_pause', '        self.assertFalse(self.player.auto_paused)\n        self.assertIsNone(self.tick(3, ("VLC",)))\n\n    def test_manual_pause')
replace_file(path, s)
