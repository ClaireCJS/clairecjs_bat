from pafplayer_v416_edit import ROOT,replace_file,sub
f=ROOT/'pafplayer_v421_live_player_check.py'
s=f.read_text(encoding='utf-8')
s=sub(s, 'pafplayer_v416_timing_fixture.wav', 'pafplayer_v420_silent_vlc_fixture.wav')
replace_file(f,s)
