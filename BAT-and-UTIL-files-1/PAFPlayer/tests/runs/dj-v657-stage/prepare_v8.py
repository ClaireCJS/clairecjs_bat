from pathlib import Path
p=Path(__file__).parent/'PAFPlayer_candidate_v7.py';s=p.read_text(encoding='utf8');old="PLAYER_BUILD_ID                = '2026-11-11-v655-idle-behavior-motion'";new="PLAYER_BUILD_ID                = '2026-11-11-v657-experimental-ai-dj'";assert s.count(old)==1;s=s.replace(old,new,1);compile(s,'candidate','exec')
with (p.parent/'PAFPlayer_candidate_v8.py').open('x',encoding='utf8',newline='\n') as f:f.write(s)
