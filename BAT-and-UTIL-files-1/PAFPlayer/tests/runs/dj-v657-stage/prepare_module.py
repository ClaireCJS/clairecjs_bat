from pathlib import Path
p=Path(__file__).resolve().parents[3]/'src/PAFPlayer_dj.py'
s=p.read_text(encoding='utf8')
s=s.replace("piper_executable='', piper_voices='', accent='neutral')", "piper_executable='', piper_voices='', accent='neutral',\n                voices='marin,coral,cedar,sage,shimmer,alloy,ash,ballad,echo,fable,nova,onyx,verse')")
s=s.replace("if value['accent'] not in ACCENTS: raise ValueError('Invalid accent')", "if value['accent'] not in ACCENTS: raise ValueError('Invalid accent')\n    choices=[x.strip() for x in str(value['voices']).split(',') if x.strip()]\n    if not choices or len(choices)!=len(set(choices)) or any(x not in VOICES for x in choices): raise ValueError('Invalid OpenAI voices')\n    value['voices']=','.join(choices)")
s=s.replace("f'Use speakers numbered 1 through {opts[\"speakers\"]}, approximately {opts[\"seconds\"]} seconds. '","f'Use speakers numbered 1 through {opts[\"speakers\"]}, approximately {opts[\"seconds\"]} seconds. '\n            f'The requested cast is {opts[\"women\"]} women and {opts[\"men\"]} men. '")
s=s.replace("lines,warning=dialogue(history,opts)","lines,warning=dialogue(history,opts)\n    selected_voices=opts['voices'].split(',')")
s=s.replace("VOICES[(speaker-1)%len(VOICES)]","selected_voices[(speaker-1)%len(selected_voices)]")
s=s.replace("self.error='DJ generation failed: '+type(exc).__name__", "self.error='DJ generation failed; check OpenAI, Ollama, and Piper settings'")
s=s.replace("    def cancel_playback(self):self.play_cancel.set()", "    def track_changed(self):\n        with self.lock:\n            if self.forced:\n                self.serial+=1;self.forced=False;self.ready=None;self.stage=''\n        self.cancel_playback()\n\n    def cancel_playback(self):self.play_cancel.set()")
compile(s,str(p),'exec')
out=Path(__file__).parent/'PAFPlayer_dj_candidate.py'
with out.open('x',encoding='utf8',newline='\n') as f:f.write(s)
print(out)
