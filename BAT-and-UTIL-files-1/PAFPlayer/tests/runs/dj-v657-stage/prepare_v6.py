from pathlib import Path
import ast
h=Path(__file__).parent;d=(h/'PAFPlayer_dj_candidate_v4.py').read_text(encoding='utf8')
d=d.replace('marin,coral,cedar,sage,shimmer,alloy,ash,ballad,echo,fable,nova,onyx,verse','marin,coral,cedar,sage,shimmer,alloy,ash,ballad,echo,verse')
d=d.replace("          'ballad', 'echo', 'fable', 'nova', 'onyx', 'verse')", "          'ballad', 'echo', 'verse')")
compile(d,'dj','exec')
with (h/'PAFPlayer_dj_candidate_v5.py').open('x',encoding='utf8',newline='\n') as f:f.write(d)
s=(h/'PAFPlayer_candidate_v5.py').read_text(encoding='utf8')
s=s.replace('marin,coral,cedar,sage,shimmer,alloy,ash,ballad,echo,fable,nova,onyx,verse','marin,coral,cedar,sage,shimmer,alloy,ash,ballad,echo,verse')
s=s.replace('plus its small JSON configuration; Piper and dependencies are additional.', 'plus its small JSON configuration; download both files together. Piper and dependencies are additional.')
tree=ast.parse(s);v=next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Subscript) and isinstance(t.value,ast.Name) and t.value.id=='_PAF_BUNDLED_SOURCES' and ast.literal_eval(t.slice)=='PAFPlayer_dj' for t in n.targets))
lines=s.splitlines(keepends=True);line=lines[v.lineno-1].encode('utf8');lines[v.lineno-1]=(line[:v.col_offset]+repr(d).encode('utf8')+line[v.end_col_offset:]).decode('utf8');s=''.join(lines);compile(s,'candidate','exec')
with (h/'PAFPlayer_candidate_v6.py').open('x',encoding='utf8',newline='\n') as f:f.write(s)
for base in ('test_playback_candidate_v5.py','test_providers_candidate_v2.py'):
 t=(h/base).read_text(encoding='utf8').replace('PAFPlayer_candidate_v5.py','PAFPlayer_candidate_v6.py').replace('PAFPlayer_dj_candidate_v4.py','PAFPlayer_dj_candidate_v5.py')
 new=base.replace('.py','_next.py')
 with (h/new).open('x',encoding='utf8',newline='\n') as f:f.write(t)
