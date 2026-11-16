from pathlib import Path
import datetime,hashlib,shutil
root=Path(__file__).resolve().parents[2]
def once(s,a,b):
    assert s.count(a)==1,(a,s.count(a));return s.replace(a,b,1)
def replace(path,data,archive):
    name=path.name+datetime.datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak');b=path.with_name(name);i=0
    while b.exists():i+=1;b=path.with_name(name[:-4]+f' ({i}).bak')
    shutil.copy2(path,b);assert hashlib.sha256(path.read_bytes()).digest()==hashlib.sha256(b.read_bytes()).digest()
    path.write_text(data,encoding='utf8',newline='');dest=archive/b.name;i=0
    while dest.exists():i+=1;dest=archive/(b.stem+f' ({i})'+b.suffix)
    shutil.move(str(b),str(dest))
src=root/'src/PAFPlayer_dj.py';dj=src.read_text(encoding='utf8')
dj=once(dj,"    if isinstance(exc, urllib.error.HTTPError): result['http_status'] = int(exc.code)\n    return result", "    if isinstance(exc, urllib.error.HTTPError): result['http_status'] = int(exc.code)\n    else:\n        status = getattr(exc, 'status_code', None)\n        if type(status) is int and 100 <= status <= 599: result['http_status'] = status\n    return result")
dj=once(dj,"        except (OSError, TypeError, ValueError): pass\n\n\ndef dialogue", "        except (OSError, TypeError, ValueError): self.path = None\n\n\ndef dialogue")
dj=once(dj,"return {'settings':dict(self.options),'stage':self.stage, 'history_count':len(self.history), 'tracks_since_commentary':self.count,", "return {'settings':dict(self.options),'stage':self.stage, 'history_count':len(self.history), 'tracks_since_commentary':self.count, 'log_available':self.log.path is not None,")
player=root/'PAFPlayer.py';lines=player.read_text(encoding='utf8').splitlines(keepends=True);idx=[i for i,line in enumerate(lines) if line.startswith("_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = ")];assert len(idx)==1
lines[idx[0]]="_PAF_BUNDLED_SOURCES['PAFPlayer_dj'] = "+repr(dj)+'\n';text=''.join(lines)
old="    rows = ['AI DJ: ' + ('on' if enabled else 'off') + (' · ' + clean(stage) if stage else '')]\n    if error:"
new="    rows = ['AI DJ: ' + ('on' if enabled else 'off') + (' · ' + clean(stage) if stage else '')]\n    log = getattr(controller, 'log', None)\n    if log is not None and not log.path: rows.append('DJ diagnostic log unavailable; check folder permissions.')\n    if error:"
text=once(text,old,new);compile(dj,str(src),'exec');compile(text,str(player),'exec')
replace(src,dj,root/'backups');replace(player,text,root/'releases');replace(root/'releases/PAFPlayer_v660_dj_diagnostics.py',text,root/'releases')
print('Added log availability reporting and safe WebSocket status codes.')
