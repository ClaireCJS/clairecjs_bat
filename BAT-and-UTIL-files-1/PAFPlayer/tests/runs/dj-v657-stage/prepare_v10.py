from pathlib import Path
h=Path(__file__).parent;p=h/'PAFPlayer_candidate_v9.py';s=p.read_text(encoding='utf8')
old="""        dj_controller.track_changed()
        if local_eligible or full_play_completion:"""
new="""        if result in {'stopped', STOP, QUIT_Q}:
            dj_controller.cancel_request()
        else:
            dj_controller.track_changed()
        if local_eligible or full_play_completion:"""
assert s.count(old)==1;s=s.replace(old,new,1)
old='''    finally:
        dj_controller.cancel_playback()
        _INLINE_RENAME_CURSOR_SUFFIX = ""'''
new='''    finally:
        if screen_closed: dj_controller.cancel_playback()
        else: dj_controller.cancel_request()
        _INLINE_RENAME_CURSOR_SUFFIX = ""'''
assert s.count(old)==1;s=s.replace(old,new,1);compile(s,'candidate','exec')
with (h/'PAFPlayer_candidate_v10.py').open('x',encoding='utf8',newline='\n') as f:f.write(s)
for old,new in [('test_playback_final_v2.py','test_playback_final_v3.py'),('test_web_final_v2.py','test_web_final_v3.py'),('check_web_final_v2.py','check_web_final_v3.py')]:
 t=(h/old).read_text(encoding='utf8').replace('PAFPlayer_candidate_v9.py','PAFPlayer_candidate_v10.py')
 with (h/new).open('x',encoding='utf8',newline='\n') as f:f.write(t)
