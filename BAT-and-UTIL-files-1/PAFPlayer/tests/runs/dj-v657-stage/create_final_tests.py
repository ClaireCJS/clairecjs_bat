from pathlib import Path
h=Path(__file__).parent;root=h.parents[2]
items=[('test_playback_final_v3.py','test_v657_dj_playback.py'),('test_providers_final_v2.py','test_v657_dj_providers.py'),('test_realtime_final_v2.py','test_v657_dj_realtime.py'),('test_web_final_v3.py','test_v657_dj_web.py'),('test_cancellation_final.py','test_v657_dj_cancel.py'),('test_force_candidate.py','test_v657_dj_force.py')]
for source,name in items:
 s=(h/source).read_text(encoding='utf8')
 s=s.replace("Path(__file__).resolve().parents[3]","Path(__file__).resolve().parents[1]")
 s=s.replace("Path(__file__).parent/'PAFPlayer_candidate_v10.py'","root/'PAFPlayer.py'")
 s=s.replace("path=Path(__file__).parent/'PAFPlayer_candidate_v10.py'", "path=Path(__file__).resolve().parents[1]/'PAFPlayer.py'")
 s=s.replace("Path(__file__).parent/'PAFPlayer_dj_candidate_v7.py'", "Path(__file__).resolve().parents[1]/'src/PAFPlayer_dj.py'")
 s=s.replace("p=Path(__file__).parent/'PAFPlayer_dj_candidate_v7.py'", "p=Path(__file__).resolve().parents[1]/'src/PAFPlayer_dj.py'")
 s=s.replace("fixture=Path(__file__).parent/'test-tone.wav'", "fixture=root/'tests/runs/dj-v657-stage/test-tone.wav'")
 s=s.replace("h/'test_playback_final.py'", "h/'test_v657_dj_playback.py'")
 s=s.replace("p.play_audio_file(h/'test-tone.wav'", "p.play_audio_file(h/'runs/dj-v657-stage/test-tone.wav'")
 compile(s,name,'exec')
 with (root/'tests'/name).open('x',encoding='utf8',newline='\n') as f:f.write(s)
 print('Created',name)
