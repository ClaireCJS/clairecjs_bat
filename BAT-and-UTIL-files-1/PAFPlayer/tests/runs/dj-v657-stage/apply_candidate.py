from pathlib import Path
from datetime import datetime
import ast,hashlib
root=Path(__file__).resolve().parents[3];stage=Path(__file__).parent
player=root/'PAFPlayer.py';original=player.read_bytes();release=(root/'releases/PAFPlayer_v656_hash_command_foundation.py').read_bytes()
assert original==release,'Active player changed since staging; refusing replacement'
tree=ast.parse(original.decode('utf8'));bundles={}
for n in tree.body:
 if isinstance(n,ast.Assign):
  for t in n.targets:
   if isinstance(t,ast.Name) and t.id=='_PAF_BUNDLED_SOURCES':bundles.update(ast.literal_eval(n.value))
   elif isinstance(t,ast.Subscript) and isinstance(t.value,ast.Name) and t.value.id=='_PAF_BUNDLED_SOURCES':bundles[ast.literal_eval(t.slice)]=ast.literal_eval(n.value)
for name in ('PAFPlayer_workflows','PAFPlayer_web_workflows'):
 assert (root/'src'/f'{name}.py').read_text(encoding='utf8')==bundles[name],f'{name} changed since staging'
def write(rel,data,archive):
 p=root/rel;old=p.read_bytes();stamp=datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');base=p.with_name(p.name+stamp);backup=base;n=0
 while backup.exists() or (root/archive/backup.name).exists():
  n+=1;backup=base.with_name(f'{base.stem} ({n}){base.suffix}')
 with backup.open('xb') as f:f.write(old)
 assert hashlib.sha256(backup.read_bytes()).digest()==hashlib.sha256(old).digest()
 assert p.read_bytes()==old,'Concurrent change; refusing replacement'
 p.write_bytes(data);assert p.read_bytes()==data
 target=root/archive/backup.name;assert not target.exists();backup.rename(target)
 print('Modified:',p,'Backup:',target)
for dest,src in [('src/PAFPlayer_dj.py','PAFPlayer_dj_candidate_v7.py'),('src/PAFPlayer_workflows.py','PAFPlayer_workflows_candidate.py'),('src/PAFPlayer_web_workflows.py','PAFPlayer_web_workflows_candidate.py')]:
 write(dest,(stage/src).read_bytes(),'src/backups')
assert player.read_bytes()==original
write('PAFPlayer.py',(stage/'PAFPlayer_candidate_v10.py').read_bytes(),'releases')
