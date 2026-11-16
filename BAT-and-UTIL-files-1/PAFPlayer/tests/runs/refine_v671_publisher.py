from pathlib import Path
root=Path(__file__).resolve().parents[2]
source=root/'tests/runs/publish_v671_dj_variety.py';target=root/'tests/runs/publish_v671_dj_variety_v2.py'
s=source.read_text(encoding='utf8')
line='s=once(s,"self.serial+=1;self.forced=False;self.ready=None;self.stage=\'\'\\n        self.cancel_playback()", "self.serial+=1;self.forced=False;self.ready=None;self.ready_dialogue=None;self.stage=\'\'\\n        self.cancel_playback()")'
assert s.count(line)==2
replacement='s=s.replace("self.serial+=1;self.forced=False;self.ready=None;self.stage=\'\'", "self.serial+=1;self.forced=False;self.ready=None;self.ready_dialogue=None;self.stage=\'\'")'
s=s.replace(line,replacement,1).replace(line,'',1)
with target.open('x',encoding='utf8',newline='') as out:out.write(s)
print('Prepared corrected publisher.')
