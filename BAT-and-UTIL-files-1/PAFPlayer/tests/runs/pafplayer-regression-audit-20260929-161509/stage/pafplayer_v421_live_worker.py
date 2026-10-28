from pafplayer_v416_edit import ROOT,replace_file,sub
f=ROOT/'pafplayer_v421_live_player_check.py'
s=f.read_text(encoding='utf-8')
s=sub(s, 'original_stop = p.stop_process', '''original_stop = p.stop_process
original_launch = p.launch_matrixmixer_inspired_renderer
workers = []
def launch(*args, **kwargs):
    process, command = original_launch(*args, **kwargs)
    workers.append(process)
    return process, command''')
s=sub(s, "        phase[0] = 3\n        return p.STOP", "        assert len(workers) >= 2 and workers[-1].poll() is None, 'Resumed audio worker is not running'\n        phase[0] = 3\n        return p.STOP")
s=sub(s, "        stack.enter_context(mock.patch.object(p, 'stop_process', side_effect=stop_audio))", "        stack.enter_context(mock.patch.object(p, 'stop_process', side_effect=stop_audio))\n        stack.enter_context(mock.patch.object(p, 'launch_matrixmixer_inspired_renderer', side_effect=launch))")
s=sub(s, "    assert len(stopped) >= 2 and stopped[-1]['before'] is None, stopped\n", '')
replace_file(f,s)
