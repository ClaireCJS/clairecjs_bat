from pathlib import Path
import ast
h=Path(__file__).parent;p=h/'PAFPlayer_dj_candidate_v2.py';dj=p.read_text(encoding='utf8')
dj=dj.replace("    def record(self,artist,title):", "    def record(self,artist,title,prepare=True):")
dj=dj.replace("        self.start(False)\n\n    def start(self,forced=False):", "        if prepare:self.start(False)\n\n    def start(self,forced=False):")
dj=dj.replace("        with self.lock:\n            if forced:self.forced=True\n            if self.ready or self.working is not None:return True", "        with self.lock:\n            if self.play_thread and self.play_thread.is_alive():return True\n            if forced:self.forced=True\n            if self.ready or self.working is not None:return True")
dj=dj.replace("'piper_available':bool(self.options['piper_executable'] or shutil.which('piper'))", "'piper_available':bool((self.options['piper_executable'] and Path(self.options['piper_executable']).is_file()) or shutil.which('piper'))")
compile(dj,str(p),'exec')
with (h/'PAFPlayer_dj_candidate_v3.py').open('x',encoding='utf8',newline='\n') as f:f.write(dj)
p=h/'PAFPlayer_candidate_v2.py';s=p.read_text(encoding='utf8')
s=s.replace("dj_controller.record(audio_tags.get('Artist', ''), audio_tags.get('Song', '') or audio_path.stem)","dj_controller.record(audio_tags.get('Artist', ''), audio_tags.get('Song', '') or audio_path.stem, prepare=result not in {'stopped', STOP, QUIT_Q})")
needle="                if action is None and not startup_pause_transition and dj_controller.due():\n"
insert="                if action in ({STOP, QUIT_Q, PAUSE_TOGGLE, WEB_PLAY, WEB_PAUSE, WEB_STOP} | NAVIGATION_ACTIONS) and dj_controller.forced:\n                    dj_controller.cancel_request()\n"
assert s.count(needle)==1;s=s.replace(needle,insert+needle,1)
tree=ast.parse(s);value=next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Subscript) and isinstance(t.value,ast.Name) and t.value.id=='_PAF_BUNDLED_SOURCES' and ast.literal_eval(t.slice)=='PAFPlayer_dj' for t in n.targets))
lines=s.splitlines(keepends=True);line=lines[value.lineno-1].encode('utf8');lines[value.lineno-1]=(line[:value.col_offset]+repr(dj).encode('utf8')+line[value.end_col_offset:]).decode('utf8');s=''.join(lines)
compile(s,str(p),'exec')
with (h/'PAFPlayer_candidate_v3.py').open('x',encoding='utf8',newline='\n') as f:f.write(s)
print('staged cancellation improvements')
