from pathlib import Path
root=Path(__file__).resolve().parents[2]
source=root/'tests/runs/publish_v671_dj_variety_v2.py';target=root/'tests/runs/publish_v671_dj_variety_v3.py'
s=source.read_text(encoding='utf8')
anchor="s=once(s,\"        self.commentary=[];self.talk_log_error=''\","
extra='''s=once(s,"        self.history=deque(maxlen=100);self.count=0;self.serial=0;self.working=None", "        self.history=deque(maxlen=100);self.track_numbers=deque(maxlen=100);self.track_seq=0;self.last_spoken_track_id=0;self.ready_through=0;self.count=0;self.serial=0;self.working=None")
s=once(s,"            self.history.append({'artist':str(artist or '')[:300],'title':str(title or '')[:300]});self.count+=1", "            self.history.append({'artist':str(artist or '')[:300],'title':str(title or '')[:300]});self.track_seq+=1;self.track_numbers.append(self.track_seq);self.count+=1")
s=once(s,"            history=list(self.history)\\n            if current:", "            history=list(self.history);new_track_count=sum(1 for number in self.track_numbers if number>self.last_spoken_track_id);through=self.track_seq\\n            if current:")
'''
assert s.count(anchor)==1;s=s.replace(anchor,extra+anchor,1)
a="min(len(history),self.count+(1 if current else 0))";b="min(len(history),new_track_count+(1 if current else 0))";assert s.count(a)==1;s=s.replace(a,b,1)
a="self.ready=result;self.ready_dialogue=list(published[-1]) if published else None;";b="self.ready=result;self.ready_through=through;self.ready_dialogue=list(published[-1]) if published else None;";assert s.count(a)==1;s=s.replace(a,b,1)
a="            if self.ready_dialogue:\n                self.recent_dialogues.append";b="            self.last_spoken_track_id=max(self.last_spoken_track_id,self.ready_through)\n            if self.ready_dialogue:\n                self.recent_dialogues.append";assert s.count(a)==1;s=s.replace(a,b,1)
with target.open('x',encoding='utf8',newline='') as f:f.write(s)
print('Prepared track-aware publisher.')
