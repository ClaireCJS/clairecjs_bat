from pathlib import Path
import datetime,hashlib,shutil,ast
root=Path.cwd()
def backup(p,folder):
 stamp=datetime.datetime.now().strftime('%Y%m%d%H%M');base=p.name+'.bak.'+stamp+'.replaced-by-chatgpt';b=p.with_name(base+'.bak');n=0
 while b.exists(): n+=1;b=p.with_name(base+f' ({n}).bak')
 shutil.copy2(p,b);assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest()
 dest=root/folder/b.name;dest.parent.mkdir(exist_ok=True,parents=True)
 while dest.exists(): n+=1;dest=dest.with_name(base+f' ({n}).bak')
 b.rename(dest)
p=root/'src/PAFPlayer_playback_focus.py';backup(p,'src/backups');s=p.read_text(encoding='utf-8-sig')
s=s.replace('                except (OSError, ValueError, KeyError):\n                    # Old descriptors',"                except TimeoutError as exc:\n                    raise RuntimeError('Timed out waiting for another PAFPlayer to pause; preview has not started.') from exc\n                except (OSError, ValueError, KeyError):\n                    # Old descriptors")
s=s.replace('        # Keep expired registry entries: no permanent deletion of user files.',"        if hasattr(self, 'descriptor') and self.descriptor.exists():\n            retired = self.root / 'retired'\n            retired.mkdir(exist_ok=True)\n            target = retired / self.descriptor.name\n            suffix = 0\n            while target.exists():\n                suffix += 1\n                target = retired / (self.descriptor.stem + ' (%d).json' % suffix)\n            self.descriptor.rename(target)")
p.write_text(s,encoding='utf-8')
p=root/'tests/test_v755_preview_focus.py';backup(p,'tests/backups');s=p.read_text(encoding='utf-8-sig').replace("self.tmp=tempfile.TemporaryDirectory(prefix='paf-focus-',ignore_cleanup_errors=True)","self.fixture=Path(tempfile.mkdtemp(prefix='v755-focus-',dir=Path('tests/runs').resolve()))").replace('Path(self.tmp.name)','self.fixture');p.write_text(s,encoding='utf-8')
p=root/'PAFPlayer.py';backup(p,'releases');s=p.read_text(encoding='utf-8');lines=s.splitlines(keepends=True)
for i,line in enumerate(lines):
 if line.startswith('_PAF_BUNDLED_SOURCES = '):
  d=ast.literal_eval(line.split(' = ',1)[1]);d['PAFPlayer_playback_focus']=(root/'src/PAFPlayer_playback_focus.py').read_text(encoding='utf-8');lines[i]='_PAF_BUNDLED_SOURCES = '+repr(d)+'\n';break
s=''.join(lines);compile(s,str(p),'exec');p.write_text(s,encoding='utf-8')
old=root/'PAFPlayer.py.bak.202611211028.replaced-by-chatgpt.bak';dest=root/'releases'/old.name
if old.exists():
 n=0
 while dest.exists(): n+=1;dest=root/'releases'/(old.stem+f' ({n})'+old.suffix)
 old.rename(dest)
print('Refined timeout handling, archived inactive peer registrations and root backup; bundled source matches.')
