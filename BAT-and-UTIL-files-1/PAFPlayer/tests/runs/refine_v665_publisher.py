from pathlib import Path
p=Path(__file__).with_name('publish_v665_dj_sleep.py');s=p.read_text(encoding='utf8')
old='text=once(text,anchor,new)\nold="for(const k of keys)'
new="new=new.replace('\\n','\\\\n')\ntext=once(text,anchor,new)\nold=\"for(const k of keys)"
assert s.count(old)==1;s=s.replace(old,new,1)
target=p.with_name('publish_v665_dj_sleep_v2.py');assert not target.exists();target.write_text(s,encoding='utf8');print(target)
