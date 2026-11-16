from pathlib import Path
import ast
h=Path(__file__).parent;d=(h/'PAFPlayer_dj_candidate_v5.py').read_text(encoding='utf8')
d=d.replace("self.options=settings({**self.options,**patch},changed);self.serial+=1;self.ready=None;self.forced=False", "self.options=settings({**self.options,**patch},changed);self.serial+=1;self.ready=None;self.forced=False;self.error=''")
d=d.replace("if not forced and (not self.options['enabled'] or self.count<max(1,self.options['interval']-1) or self.attempted==self.count):return False", "if not forced and (self.error or not self.options['enabled'] or self.count<max(1,self.options['interval']-1) or self.attempted==self.count):return False")
d=d.replace("'piper_available':bool((self.options['piper_executable'] and Path(self.options['piper_executable']).is_file()) or shutil.which('piper'))}", "'piper_available':bool((self.options['piper_executable'] and Path(self.options['piper_executable']).is_file()) or shutil.which('piper')),\n            'piper_voices_found':sum(Path(x.strip()).is_file() for x in self.options['piper_voices'].splitlines() if x.strip())}")
compile(d,'dj','exec')
with (h/'PAFPlayer_dj_candidate_v6.py').open('x',encoding='utf8',newline='\n') as f:f.write(d)
s=(h/'PAFPlayer_candidate_v6.py').read_text(encoding='utf8')
s=s.replace("d.piper_available?'Piper executable configured or found':'Piper executable not detected',!local?", "d.piper_available?'Piper executable found':'Piper executable not detected',String(d.piper_voices_found||0)+' Piper voice model files found',!local?")
tree=ast.parse(s);v=next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Subscript) and isinstance(t.value,ast.Name) and t.value.id=='_PAF_BUNDLED_SOURCES' and ast.literal_eval(t.slice)=='PAFPlayer_dj' for t in n.targets))
lines=s.splitlines(keepends=True);line=lines[v.lineno-1].encode('utf8');lines[v.lineno-1]=(line[:v.col_offset]+repr(d).encode('utf8')+line[v.end_col_offset:]).decode('utf8');s=''.join(lines);compile(s,'candidate','exec')
with (h/'PAFPlayer_candidate_v7.py').open('x',encoding='utf8',newline='\n') as f:f.write(s)
for old,new in [('test_playback_candidate_v5_next.py','test_playback_final.py'),('test_providers_candidate_v2_next.py','test_providers_final.py'),('test_realtime_candidate.py','test_realtime_final.py'),('test_web_candidate.py','test_web_final.py'),('check_candidate_web.py','check_web_final.py')]:
 t=(h/old).read_text(encoding='utf8').replace('PAFPlayer_candidate_v6.py','PAFPlayer_candidate_v7.py').replace('PAFPlayer_candidate_v4.py','PAFPlayer_candidate_v7.py').replace('PAFPlayer_dj_candidate_v5.py','PAFPlayer_dj_candidate_v6.py')
 with (h/new).open('x',encoding='utf8',newline='\n') as f:f.write(t)
