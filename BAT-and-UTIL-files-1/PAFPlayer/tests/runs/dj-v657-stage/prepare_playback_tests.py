from pathlib import Path
p=Path(__file__).parent/'test_playback_candidate_v2.py';s=p.read_text(encoding='utf8')
s=s.replace("def take(self):self.prepared=False;return ['test.wav']", "def take(self):self.prepared=False;self.forced=False;return ['test.wav']")
s=s.replace('def run_case(self,manual_pause):',"def run_case(self,manual_pause,initial=False,skip=False):")
s=s.replace("dj=FakeDJ();clock=[100.];paused=[False];commands=[];once=[False]", "dj=FakeDJ();dj.forced=initial;clock=[100.];paused=[initial];commands=[];once=[False]")
s=s.replace("if paused[0] and not once[0]:\n    once[0]=True\n    if manual_pause:return p.WEB_PAUSE\n    dj.play_done=True;return None", "if paused[0] and not once[0]:\n    if initial and not dj.played:return None\n    once[0]=True\n    if skip:return p.NEXT_FILE\n    if manual_pause:return p.WEB_PAUSE\n    dj.play_done=True;return None")
s=s.replace("if (manual_pause and once[0]) or len(commands)>=2:return p.STOP", "if ((manual_pause or initial) and once[0]) or len(commands)>=2:return p.STOP")
s=s.replace("initially_paused=initial,", "initially_paused=initial,") if 'initially_paused=initial,' in s else s.replace('now_playing_targets=[],paused_state=paused,', 'now_playing_targets=[],initially_paused=initial,paused_state=paused,')
anchor="if __name__=='__main__':unittest.main()"
s=s.replace(anchor,""" def test_forced_playback_while_paused_never_resumes_music(self):
  result,dj,commands,paused=self.run_case(False,initial=True);self.assertEqual('stopped',result);self.assertTrue(dj.played);self.assertEqual(1,len(commands))
 def test_skip_stops_commentary_without_restart(self):
  result,dj,commands,paused=self.run_case(False,skip=True);self.assertEqual(p.NEXT_FILE,result);self.assertTrue(dj.cancelled);self.assertEqual(1,len(commands))
"""+anchor)
compile(s,str(p),'exec')
with (p.parent/'test_playback_candidate_v3.py').open('x',encoding='utf8',newline='\n') as f:f.write(s)
