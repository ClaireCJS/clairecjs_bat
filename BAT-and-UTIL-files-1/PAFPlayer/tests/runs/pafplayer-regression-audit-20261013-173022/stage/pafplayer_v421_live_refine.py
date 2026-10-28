from pafplayer_v416_edit import ROOT,replace_file,sub
f=ROOT/'pafplayer_v421_live_player_check.py'
s=f.read_text(encoding='utf-8')
s=sub(s, 'paused, phase, stopped = [False], [0], []', 'paused, phase, stopped = [False], [0], []\nresumed_at = [None]')
s=sub(s, '        phase[0] = 2\n        return None', '        phase[0] = 2\n        resumed_at[0] = time.monotonic()\n        return None')
s=sub(s, 'time.monotonic() > deadline - 20', 'time.monotonic() - resumed_at[0] >= 0.75')
s=sub(s, "    report = {'result': result", "    assert len(stopped) >= 2 and stopped[-1]['before'] is None, stopped\n    report = {'result': result")
replace_file(f,s)
