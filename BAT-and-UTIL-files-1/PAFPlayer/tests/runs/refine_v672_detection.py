from pathlib import Path
import ast,datetime,hashlib,shutil
root=Path(__file__).resolve().parents[2]
def once(s,a,b):assert s.count(a)==1,(a[:80],s.count(a));return s.replace(a,b,1)
def replace(p,data,archive):
 name=p.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');b=p.with_name(name);i=0
 while b.exists():i+=1;b=p.with_name(name[:-4]+f' ({i}).bak')
 shutil.copy2(p,b);assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest()
 p.write_text(data,encoding='utf8',newline='');dest=archive/b.name;i=0
 while dest!=b and dest.exists():i+=1;dest=archive/(b.stem+f' ({i})'+b.suffix)
 if dest!=b:shutil.move(str(b),str(dest))
src=root/'src/PAFPlayer_dj.py';s=src.read_text(encoding='utf8')
s=once(s,"    exe=(configured_exe if configured_exe and Path(configured_exe).is_file() else '') or shutil.which('piper')\n    if (configured_exe and not Path(configured_exe).is_file())", "    configured_found=(configured_exe if configured_exe and Path(configured_exe).is_file() else shutil.which(configured_exe) if configured_exe else None)\n    exe=configured_found or shutil.which('piper')\n    if (configured_exe and not configured_found)")
s=once(s,"exe_ok=bool((custom_exe and Path(custom_exe).is_file()) or shutil.which('piper'))", "exe_ok=bool((custom_exe and (Path(custom_exe).is_file() or shutil.which(custom_exe))) or shutil.which('piper'))")
s=once(s,"if self.options['piper_executable'] and not Path(self.options['piper_executable']).is_file():missing.insert(0,self.options['piper_executable'])", "if self.options['piper_executable'] and not (Path(self.options['piper_executable']).is_file() or shutil.which(self.options['piper_executable'])):missing.insert(0,self.options['piper_executable'])")
s=once(s,"'piper_voices_found':sum(Path(x.strip()).is_file() for x in self.options['piper_voices'].splitlines() if x.strip()) + (1 if private and not self.options['piper_voices'].strip() else 0)", "'piper_voices_found':sum(Path(x).is_file() for x in configured) or (int(bool(private))+int(bool(male)))")
compile(s,str(src),'exec');p=root/'PAFPlayer.py';lines=p.read_text(encoding='utf8').splitlines(keepends=True);idx=[i for i,l in enumerate(lines) if l.startswith("_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = ")];assert len(idx)==1;lines[idx[0]]="_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = "+repr(s)+'\n';text=''.join(lines)
text=once(text,'id="dj_women" type="number" min="0" max="10" value="2"','id="dj_women" type="number" min="0" max="10" value="1"')
text=once(text,'id="dj_men" type="number" min="0" max="10" value="0"','id="dj_men" type="number" min="0" max="10" value="1"')
text=once(text,'id="dj_voices" value="marin,coral,cedar,sage,shimmer,alloy,ash,ballad,echo,verse"','id="dj_voices" value="marin,cedar,coral,sage,shimmer,alloy,ash,ballad,echo,verse"')
compile(text,str(p),'exec');replace(src,s,root/'backups');replace(p,text,root/'releases');replace(root/'releases/PAFPlayer_v672_piper_startup.py',text,root/'releases')
print('Improved executable and automatic voice detection.')
