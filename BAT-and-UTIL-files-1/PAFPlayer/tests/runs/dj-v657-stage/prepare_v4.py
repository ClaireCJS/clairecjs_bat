from pathlib import Path
p=Path(__file__).parent/'PAFPlayer_candidate_v3.py';s=p.read_text(encoding='utf8')
a='if action in ({STOP, QUIT_Q, PAUSE_TOGGLE, WEB_PLAY, WEB_PAUSE, WEB_STOP} | NAVIGATION_ACTIONS) and dj_controller.forced:'
b='if not startup_pause_transition and action in ({STOP, QUIT_Q, PAUSE_TOGGLE, WEB_PLAY, WEB_PAUSE, WEB_STOP} | NAVIGATION_ACTIONS) and dj_controller.forced:'
assert s.count(a)==1;s=s.replace(a,b,1);compile(s,str(p),'exec')
with (p.parent/'PAFPlayer_candidate_v4.py').open('x',encoding='utf8',newline='\n') as f:f.write(s)
t=(p.parent/'test_playback_candidate_v3.py').read_text(encoding='utf8').replace('PAFPlayer_candidate_v3.py','PAFPlayer_candidate_v4.py')
with (p.parent/'test_playback_candidate_v4.py').open('x',encoding='utf8',newline='\n') as f:f.write(t)
