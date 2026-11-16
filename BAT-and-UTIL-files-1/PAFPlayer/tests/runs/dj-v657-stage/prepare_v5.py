from pathlib import Path
import ast
h=Path(__file__).parent;d=(h/'PAFPlayer_dj_candidate_v3.py').read_text(encoding='utf8')
d=d.replace("[exe,'--model',model,'--output_file',str(path)]","[exe,'-m',model,'-f',str(path)]")
d=d.replace("    def start(self,forced=False):", "    def start(self,forced=False,current=None):")
d=d.replace("            if not self.history:\n                self.forced=False;self.error='Play a track first';return False", "            if not self.history and not current:\n                self.forced=False;self.error='Play a track first';return False")
d=d.replace("            history=list(self.history)[-self.options['history']:];opts=dict(self.options);self.error='';self.stage='Preparing'", "            history=list(self.history)\n            if current:history.append({'artist':str(current.get('artist',''))[:300],'title':str(current.get('title',''))[:300]})\n            history=history[-self.options['history']:];opts=dict(self.options);self.error='';self.stage='Preparing'")
compile(d,'dj','exec')
with (h/'PAFPlayer_dj_candidate_v4.py').open('x',encoding='utf8',newline='\n') as f:f.write(d)
s=(h/'PAFPlayer_candidate_v4.py').read_text(encoding='utf8')
old="                        if dj_controller.start(True): set_transient_notice('AI DJ: preparing or ready', seconds=3.0)"
new="""                        heard_current = bool(played_ranges) or (not prompt_paused_state[0] and current_prompt_position() - position >= 3.0)
                        current = {'artist': audio_tags.get('Artist', ''), 'title': audio_tags.get('Song', '') or audio_path.stem} if heard_current else None
                        if dj_controller.start(True, current=current): set_transient_notice('AI DJ: preparing or ready', seconds=3.0)"""
assert s.count(old)==1;s=s.replace(old,new,1)
old='sizes depend on your selections. PAFPlayer does not overwrite existing installations.'
new='for example, en_US-lessac-medium downloads a 63.2 MB model plus its small JSON configuration; Piper and dependencies are additional. PAFPlayer does not overwrite existing installations.'
assert s.count(old)==1;s=s.replace(old,new,1)
tree=ast.parse(s);v=next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Subscript) and isinstance(t.value,ast.Name) and t.value.id=='_PAF_BUNDLED_SOURCES' and ast.literal_eval(t.slice)=='PAFPlayer_dj' for t in n.targets))
lines=s.splitlines(keepends=True);line=lines[v.lineno-1].encode('utf8');lines[v.lineno-1]=(line[:v.col_offset]+repr(d).encode('utf8')+line[v.end_col_offset:]).decode('utf8');s=''.join(lines);compile(s,'candidate','exec')
with (h/'PAFPlayer_candidate_v5.py').open('x',encoding='utf8',newline='\n') as f:f.write(s)
t=(h/'test_playback_candidate_v4.py').read_text(encoding='utf8').replace('PAFPlayer_candidate_v4.py','PAFPlayer_candidate_v5.py')
with (h/'test_playback_candidate_v5.py').open('x',encoding='utf8',newline='\n') as f:f.write(t)
t=(h/'test_providers_candidate.py').read_text(encoding='utf8').replace('PAFPlayer_dj_candidate_v3.py','PAFPlayer_dj_candidate_v4.py').replace("args.index('--output_file')", "args.index('-f')").replace("args.index('--model')", "args.index('-m')")
with (h/'test_providers_candidate_v2.py').open('x',encoding='utf8',newline='\n') as f:f.write(t)
