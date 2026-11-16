from pathlib import Path
from datetime import datetime
import hashlib
root=Path(__file__).resolve().parents[3];p=root/'tests/test_v657_dj_web.py';old=p.read_bytes();s=old.decode('utf8');assert s.count("path=root/'PAFPlayer.py'")==1;s=s.replace("path=root/'PAFPlayer.py'", "path=Path(__file__).resolve().parents[1]/'PAFPlayer.py'",1)
b=p.with_name(p.name+datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak'));base=b;n=0
while b.exists() or (root/'tests/backups'/b.name).exists():n+=1;b=base.with_name(f'{base.stem} ({n}){base.suffix}')
with b.open('xb') as f:f.write(old)
assert hashlib.sha256(b.read_bytes()).digest()==hashlib.sha256(old).digest();assert p.read_bytes()==old
p.write_bytes(s.encode('utf8'));b.rename(root/'tests/backups'/b.name)
