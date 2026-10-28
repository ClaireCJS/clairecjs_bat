"""PAFPlayer-specific opt-in library, repair, review and web workflows.

This is application code, not a general ClaireCJS utility library. Imports are
side-effect free: no watchers, uploads or integrations start merely on import.
"""
from __future__ import annotations
import argparse
import base64
import codecs
from collections import deque
import contextlib
from datetime import datetime, timezone
import difflib
import hashlib
import html
import io
import json
import os
from pathlib import Path
import queue
import re
import secrets
import shutil
import socket
import statistics
import subprocess
import threading
import time
import unicodedata
from urllib.parse import urlsplit, unquote
import uuid

TRUSTED_MACHINES = ('thailog', 'demona', 'wyvern', 'goliath')
MAX_FILE_BYTES = 100 * 1024 * 1024
MAX_UPLOAD_BYTES = 512 * 1024 * 1024
MAX_SCAN_FILES = 25000
MAX_OUTWARD_LEVELS = 4
UPLOAD_TTL_SECONDS = 86400


def unique(path):
    path = Path(path); candidate = path; index = 0
    while candidate.exists():
        index += 1; candidate = path.with_name(f'{path.stem} ({index}){path.suffix}')
    return candidate


def digest(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''): value.update(block)
    return value.hexdigest()


def replace_bytes(path, data):
    """Verified sibling backup, exclusive staging file, then atomic replacement."""
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True); backup = None
    if path.exists():
        backup = unique(path.with_name(path.name + datetime.now().strftime('.bak.%Y%m%d%H%M.replaced-by-chatgpt.bak')))
        shutil.copy2(path, backup)
        if digest(path) != digest(backup): raise OSError('Replacement backup verification failed')
    stage = unique(path.with_name(path.name + f'.{uuid.uuid4().hex}.tmp'))
    with stage.open('xb') as stream:
        stream.write(data); stream.flush(); os.fsync(stream.fileno())
    os.replace(stage, path)
    return str(backup) if backup else None


def write_json(path, value):
    return replace_bytes(path, (json.dumps(value, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))


def read_json(path, default):
    try: return json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError): return default


def recycle(path):
    """Never fall back to unlink/rmtree if the OS Recycle Bin is unavailable."""
    from send2trash import send2trash
    send2trash(str(Path(path).resolve()))


def policy_default(environment=None):
    env = os.environ if environment is None else environment
    return str(env.get('USERNAME', env.get('USER',''))).casefold() == 'claire' or str(env.get('COMPUTERNAME',env.get('HOSTNAME',''))).casefold() in TRUSTED_MACHINES


def pathkey(path): return os.path.normcase(str(Path(path).resolve()))


def normalized_name(path):
    return re.sub(r'[^\w]+', '', unicodedata.normalize('NFKC',Path(path).stem).casefold()).lstrip('0123456789')


def supported_file(path, extensions):
    path = Path(path)
    if path.suffix.casefold() not in extensions or path.name.startswith(('.', '~')): return False
    if any(part.startswith('.') for part in path.parts): return False
    if re.search(r'(?i)(\.bak|\.tmp|\.part|\.download|\.crdownload)(\.|$)',path.name): return False
    try:
        stat = path.stat()
        if getattr(stat,'st_file_attributes',0) & (2 | 4 | 0x400): return False
        return path.is_file() and not path.is_symlink()
    except OSError: return False


def scan_media(roots, extensions, recursive=False):
    seen=set(); count=0
    for raw in roots:
        root=Path(raw).expanduser().resolve()
        if not root.is_dir(): continue
        iterator = root.rglob('*') if recursive else root.iterdir()
        try:
            for item in iterator:
                count+=1
                if count>MAX_SCAN_FILES: return
                if supported_file(item,extensions):
                    # Do not escape through directory junctions/symlinks.
                    resolved=item.resolve()
                    if not resolved.is_relative_to(root): continue
                    key=pathkey(resolved)
                    if key not in seen: seen.add(key); yield resolved
        except (PermissionError,FileNotFoundError): continue


def scan_media_outward(start, extensions):
    """Search the launch folder, then each parent's unvisited sibling branches."""
    root=Path(start).expanduser().resolve()
    if not root.is_dir(): return
    seen=set(); previous=None; examined=0
    for _level in range(MAX_OUTWARD_LEVELS+1):
        for current,folders,names in os.walk(root,followlinks=False):
            current=Path(current)
            safe=[]
            for name in sorted(folders,key=str.casefold):
                examined+=1
                if examined>MAX_SCAN_FILES: return
                directory=current/name
                if directory==previous or name.startswith('.') or directory.is_symlink(): continue
                try:
                    if getattr(directory.stat(),'st_file_attributes',0) & (2|4|0x400): continue
                except OSError: continue
                safe.append(name)
            folders[:]=safe
            for name in sorted(names,key=str.casefold):
                examined+=1
                if examined>MAX_SCAN_FILES: return
                path=current/name
                if supported_file(path,extensions):
                    resolved=path.resolve()
                    if not resolved.is_relative_to(root): continue
                    key=pathkey(resolved)
                    if key not in seen:
                        seen.add(key);yield resolved
        if root==root.parent: return
        previous=root;root=root.parent


def build_master_playlist(destination, roots, extensions):
    """Create a missing everything.m3u from complete music roots, atomically."""
    destination=Path(destination)
    if destination.is_file(): return {'created':False,'count':0}
    if destination.exists(): raise ValueError('Master playlist destination exists but is not a file: '+str(destination))
    valid=[]
    for raw in roots:
        if not raw: continue
        root=Path(raw).expanduser().resolve()
        if root.is_dir() and root!=root.parent and root not in valid: valid.append(root)
    if not valid: raise ValueError('No existing music-library root is available to build everything.m3u')
    destination.parent.mkdir(parents=True,exist_ok=True)
    stage=unique(destination.with_name(destination.name+'.'+uuid.uuid4().hex+'.building'))
    count=0;seen=set();errors=[]
    try:
        with stage.open('x',encoding='utf-8',newline='\n') as stream:
            stream.write('#EXTM3U\n')
            for root in valid:
                for current,folders,names in os.walk(root,followlinks=False,onerror=errors.append):
                    safe=[]
                    for name in folders:
                        directory=Path(current)/name
                        try:
                            attrs=getattr(directory.stat(),'st_file_attributes',0)
                            if not name.startswith('.') and not directory.is_symlink() and not attrs & (2|4|0x400):
                                safe.append(name)
                        except OSError as exc: errors.append(exc)
                    folders[:]=sorted(safe,key=str.casefold)
                    for name in sorted(names,key=str.casefold):
                        path=Path(current)/name
                        if not supported_file(path,extensions): continue
                        resolved=path.resolve()
                        if not resolved.is_relative_to(root): continue
                        key=pathkey(resolved)
                        if key in seen: continue
                        seen.add(key)
                        stream.write(str(resolved)+'\n');count+=1
            if errors: raise OSError('Music-library scan could not read every folder: '+str(errors[0]))
            stream.flush();os.fsync(stream.fileno())
        try:
            # Windows rename refuses an existing destination. Elsewhere a hard
            # link provides the same exclusive publish semantics.
            if os.name=='nt': os.rename(stage,destination)
            else:
                os.link(stage,destination)
                recycle(stage)
        except FileExistsError:
            recycle(stage)
            return {'created':False,'count':0}
        return {'created':True,'count':count}
    except Exception:
        if stage.exists(): recycle(stage)
        raise


def enqueue_selectors(runtime, selectors, *, allow_direct=False):
    """Use existing owner-local files directly; resolve other hints in its library."""
    if not isinstance(selectors,list) or not 0<len(selectors)<=5000:
        raise ValueError('Supply 1 to 5000 media names or regular expressions')
    known=None; searched_outward=False
    result=[]
    for selector in selectors:
        if not isinstance(selector,dict): raise ValueError('Invalid enqueue selector')
        kind=selector.get('kind')
        if kind=='path' and allow_direct:
            raw=selector.get('value')
            size=selector.get('size')
            if isinstance(raw,str) and Path(raw).is_absolute() and supported_file(raw,runtime.app.AUDIO_EXTENSIONS):
                candidate=Path(raw)
                if size is None or (type(size) is int and size>=0 and candidate.stat().st_size==size):
                    result.append(str(candidate.resolve()))
                    continue
        if known is None:
            library_path=getattr(runtime,'music_library_playlist_path',lambda: None)()
            if library_path is not None and not Path(library_path).is_file():
                print('PAFPlayer enqueue warning: Music collection filelist does not exist: '+str(library_path)+'; searching the launch folder outward, indexed tracks, and configured music folders.')
            origin=selectors[0].get('origin_dir')
            if origin is not None and (not isinstance(origin,str) or len(origin)>4096):
                raise ValueError('Invalid enqueue search folder')
            known=runtime.catalog_paths()
        if kind=='regex':
            pattern=selector.get('pattern')
            if not isinstance(pattern,str) or not pattern or len(pattern)>256:
                raise ValueError('Regular expression must contain 1 to 256 characters')
            try: compiled=re.compile(pattern,re.I)
            except re.error as exc: raise ValueError('Invalid regular expression: '+str(exc)) from exc
            matches=[path for path in known if compiled.search(path.replace('\\','/'))]
            if not matches and not searched_outward and library_path is not None and not Path(library_path).is_file():
                known=runtime.catalog_paths(search_from=origin,include_outward=True)
                searched_outward=True
                matches=[path for path in known if compiled.search(path.replace('\\','/'))]
            if not matches:
                if getattr(runtime,'master_build_pending',False):
                    raise ValueError('Regular expression has no indexed matches yet; everything.m3u is building in the background')
                if not known: raise ValueError('No searchable music library: load a playlist or configure a library playlist')
                raise ValueError('Regular expression matched no songs in the player library: '+pattern)
        elif kind=='path':
            raw=selector.get('value')
            if not isinstance(raw,str) or not raw or len(raw)>4096: raise ValueError('Invalid media name')
            parts=[piece.casefold() for piece in raw.replace('\\','/').split('/') if piece and not piece.endswith(':')]
            if not parts: raise ValueError('Invalid media name')
            size=selector.get('size')
            if size is not None and (type(size) is not int or size<0): raise ValueError('Invalid media size')
            candidates=[path for path in known if Path(path).name.casefold()==parts[-1]
                        and (size is None or Path(path).stat().st_size==size)]
            if not candidates and not searched_outward and library_path is not None and not Path(library_path).is_file():
                known=runtime.catalog_paths(search_from=origin,include_outward=True)
                searched_outward=True
                candidates=[path for path in known if Path(path).name.casefold()==parts[-1]
                            and (size is None or Path(path).stat().st_size==size)]
            if not candidates: raise ValueError('No player-library file matches: '+parts[-1])
            def suffix_score(path):
                target=[part.casefold() for part in path.replace('\\','/').split('/') if part]
                score=0
                for a,b in zip(reversed(parts),reversed(target)):
                    if a!=b: break
                    score+=1
                return score
            ranked=[(suffix_score(path),path) for path in candidates]
            best=max(score for score,_ in ranked)
            matches=[path for score,path in ranked if score==best]
            if len(matches)!=1:
                raise ValueError('Ambiguous player-library filename: '+parts[-1]+'; supply parent folders or a unique regex')
        else: raise ValueError('Unknown enqueue selector')
        result.extend(matches)
        if len(result)>5000: raise ValueError('Enqueue request matched more than 5000 tracks; narrow the search')
    return list(dict.fromkeys(result))


def prepare_enqueue_preview(runtime, selectors, *, allow_direct=False):
    """Resolve once on the owner; a short-lived token commits those exact paths."""
    matches=enqueue_selectors(runtime,selectors,allow_direct=allow_direct)
    if sum(len(path.encode('utf-8'))+4 for path in matches)>4*1024*1024:
        raise ValueError('Enqueue preview is too large; narrow the search')
    token=secrets.token_urlsafe(24)
    now=time.monotonic()
    with runtime.lock:
        previews=getattr(runtime,'enqueue_previews',None)
        if previews is None:
            previews={};runtime.enqueue_previews=previews
        for old,record in list(previews.items()):
            if now-record['created']>600: previews.pop(old,None)
        while len(previews)>=8:
            previews.pop(next(iter(previews)))
        previews[token]={'created':now,'paths':matches}
    return {'preview_token':token,'matches':matches,'count':len(matches)}


def consume_enqueue_preview(runtime, token):
    if not isinstance(token,str) or not re.fullmatch(r'[A-Za-z0-9_-]{32}',token):
        raise ValueError('Invalid enqueue preview token')
    with runtime.lock:
        record=getattr(runtime,'enqueue_previews',{}).pop(token,None)
    if record is None or time.monotonic()-record['created']>600:
        raise ValueError('Enqueue preview expired; search again')
    paths=record['paths']
    if any(not supported_file(path,runtime.app.AUDIO_EXTENSIONS) for path in paths):
        raise ValueError('A matched audio file changed or disappeared; search again')
    return paths


def decode_playlist(path):
    data=Path(path).read_bytes()
    for bom,codec in ((codecs.BOM_UTF8,'utf-8'),(codecs.BOM_UTF16_LE,'utf-16-le'),(codecs.BOM_UTF16_BE,'utf-16-be')):
        if data.startswith(bom): return data[len(bom):].decode(codec),codec,bom
    try: return data.decode('utf-8'),'utf-8',b''
    except UnicodeDecodeError: return data.decode('cp1252'),'cp1252',b''


def playlist_rows(path):
    text,codec,bom=decode_playlist(path); rows=[]
    for index,line in enumerate(text.splitlines(keepends=True)):
        raw=line.rstrip('\r\n'); stripped=raw.strip()
        if not stripped or stripped.startswith(('#',';','[')): continue
        prefix=''
        if Path(path).suffix.casefold()=='.pls':
            m=re.match(r'(File\d+=)(.*)',raw,re.I)
            if not m: continue
            prefix,stripped=m.groups()
        elif '=' in stripped and Path(path).suffix.casefold() not in ('.m3u','.m3u8'): continue
        candidate=Path(stripped)
        if not candidate.is_absolute(): candidate=Path(path).parent/candidate
        rows.append({'line':index,'raw':stripped,'path':str(candidate.resolve()),'prefix':prefix})
    return text,codec,bom,rows


def repair_candidates(app, missing, roots, *, recursive=False, evidence=None):
    """Conservative ranking: filename similarity alone never promises identity."""
    missing=Path(missing); evidence=evidence or {}; ranked=[]
    roots=[missing.parent]+list(roots)
    for item in scan_media(roots,app.AUDIO_EXTENSIONS,recursive):
        norm=normalized_name(item); target=normalized_name(missing)
        ratio=difflib.SequenceMatcher(None,target,norm).ratio()
        if ratio<.45: continue
        facts=[]; score=ratio*.48
        if norm==target: facts.append('normalized filename matches'); score+=.12
        if item.suffix.casefold()==missing.suffix.casefold(): score+=.06; facts.append('extension matches')
        stat=item.stat()
        if evidence.get('size')==stat.st_size: score+=.12; facts.append('size matches')
        ranked.append({'path':str(item),'score':score,'evidence':facts,'size':stat.st_size,'mtime_ns':stat.st_mtime_ns})
    ranked.sort(key=lambda x:(-x['score'],x['path'].casefold()))
    for candidate in ranked[:30]:
        path=Path(candidate['path'])
        try:
            duration=app.probe_duration_seconds(path); candidate['duration']=duration
            if evidence.get('duration') and duration is not None and abs(duration-float(evidence['duration']))<=1:
                candidate['score']+=.12; candidate['evidence'].append('duration matches within 1 second')
            if evidence.get('tags'):
                tags=app.probe_audio_tags(path)
                matches=[key for key,value in evidence['tags'].items() if value and str(tags.get(key,'')).casefold()==str(value).casefold()]
                if matches: candidate['score']+=min(.08,len(matches)*.04); candidate['evidence'].append('metadata matches: '+', '.join(matches))
            if evidence.get('sha256') and evidence['sha256']==digest(path):
                candidate['score']=1.; candidate['evidence'].append('SHA-256 identity matches')
        except Exception as exc: candidate['evidence'].append('optional probe unavailable: '+type(exc).__name__)
        candidate['confidence']='high' if candidate['score']>=.90 else 'ambiguous'
        candidate['score']=round(min(1.,candidate['score']),4)
    return sorted(ranked[:30],key=lambda x:-x['score'])[:15]


def rewrite_playlist(app, playlist, replacements, *, expected_hash=None, dry_run=False):
    playlist=Path(playlist)
    if expected_hash and digest(playlist)!=expected_hash: raise ValueError('Playlist changed; preview repairs again')
    text,codec,bom,rows=playlist_rows(playlist); lines=text.splitlines(keepends=True); changes=[]
    for row in rows:
        replacement=replacements.get(row['path'])
        if not replacement: continue
        target=Path(replacement['path'])
        if not supported_file(target,app.AUDIO_EXTENSIONS): raise ValueError('Replacement is not a supported existing media file')
        old=lines[row['line']]; ending=old[len(old.rstrip('\r\n')):]
        # Encode before touching disk: a legacy playlist cannot silently lose characters.
        lines[row['line']]=row['prefix']+str(target.resolve())+ending
        changes.append({'old_path':row['path'],'replacement_path':str(target.resolve()),'confidence':replacement.get('confidence','approved'), 'evidence':replacement.get('evidence',[]),'timestamp':datetime.now(timezone.utc).isoformat()})
    data=bom+''.join(lines).encode(codec)
    backup=None
    if changes and not dry_run:
        if expected_hash and digest(playlist)!=expected_hash: raise ValueError('Playlist changed during repair')
        backup=replace_bytes(playlist,data)
        for change in changes: app.append_pafplayer_trace('repair.approved',**change)
    return {'changes':changes,'backup':backup,'dry_run':dry_run}


class FolderMonitor:
    def __init__(self,runtime,roots,mode='index',playlist=None,recursive=False):
        self.runtime=runtime; self.roots=[str(Path(x).resolve()) for x in roots]; self.mode=mode; self.playlist=playlist; self.recursive=recursive
        self.paused=False; self.stop_event=threading.Event(); self.wake=threading.Event(); self.thread=None
        self.pending={}; self.actions=deque(maxlen=200); self.lock=threading.RLock()
        scope=hashlib.sha256(json.dumps([sorted(self.roots),mode,str(playlist),recursive]).encode()).hexdigest()[:16]
        self.state_path=runtime.root/('monitor-state-'+scope+'.json'); self.state=read_json(self.state_path,{})

    def record(self,kind,**fields):
        event={'time':time.time(),'kind':kind,**fields}; self.actions.append(event); self.runtime.log('monitor.'+kind,**fields)

    def scan(self, *, dry_run=False, now=None):
        now=time.monotonic() if now is None else now; result=[]; changed=False
        with self.lock:
            files=list(scan_media(self.roots,self.runtime.app.AUDIO_EXTENSIONS,self.recursive))
            identities={tuple(v.get('identity',[])):k for k,v in self.state.items() if v.get('identity')}
            for path in files:
                try:
                    stat=path.stat(); key=pathkey(path); signature=[stat.st_size,stat.st_mtime_ns]; identity=[stat.st_dev,stat.st_ino]
                    if self.state.get(key,{}).get('signature')==signature: continue
                    old=self.pending.get(key)
                    if old is None or old[0]!=signature:
                        self.pending[key]=(signature,now)
                        if dry_run: result.append({'path':str(path),'action':'pending-stability','mode':self.mode})
                        continue
                    if now-old[1]<2.: continue
                    renamed=identities.get(tuple(identity)); kind='rename' if renamed and renamed!=key else 'import'
                    action={'path':str(path),'action':kind,'mode':self.mode}; result.append(action)
                    if dry_run: continue
                    # Probe only stable files, outside the audio/render thread.
                    entry={'path':str(path),'signature':signature,'identity':identity,'size':stat.st_size,'duration':self.runtime.app.probe_duration_seconds(path),'tags':self.runtime.app.probe_audio_tags(path),'sha256':digest(path),'source':'monitored'}
                    if self.mode=='playlist':
                        if not self.playlist: raise ValueError('Playlist monitor mode requires --monitor-playlist')
                        self.runtime.append_playlist(self.playlist,path)
                    elif self.mode=='library': self.runtime.index[key]=entry
                    # Index mode also records searchable metadata, without adding membership.
                    self.runtime.index[key]=dict(entry,library_member=self.mode=='library')
                    if renamed and renamed!=key: self.state.pop(renamed,None); self.runtime.index.pop(renamed,None)
                    self.state[key]={'signature':signature,'identity':identity}; self.pending.pop(key,None); changed=True
                    self.record(kind,path=str(path),previous=renamed,mode=self.mode)
                except Exception as exc: self.record('error',path=str(path),reason=str(exc))
            if changed:
                write_json(self.state_path,self.state); self.runtime.save_index()
            if not result: self.record('scan',supported_files=len(files),result='No stable changes; temporary, hidden and backup files ignored')
        return result

    def start(self):
        def run():
            while not self.stop_event.is_set():
                if not self.paused:
                    try: self.scan()
                    except Exception as exc: self.record('error',reason=str(exc))
                self.wake.wait(2); self.wake.clear()
        self.thread=threading.Thread(target=run,name='paf-folder-monitor',daemon=True); self.thread.start()

    def close(self): self.stop_event.set(); self.wake.set()


class Runtime:
    def __init__(self,app,root=None):
        self.app=app; self.root=Path(root) if root else app.global_config_profiles_path().parent/'workflows'
        self.settings=read_json(self.root/'settings.json',{})
        if not isinstance(self.settings,dict): self.settings={}
        self.settings.setdefault('remote_uploads',policy_default())
        self.settings.setdefault('library_roots',[])
        self.settings.setdefault('music_library_playlist',str(getattr(app,'AUDIO_CATALOG_PRIMARY',Path(r'C:\mp3\lists\everything.m3u'))))
        self.settings.setdefault('enqueue_placement','after_current')
        self.index=read_json(self.root/'library.json',{})
        self.uploads=read_json(self.root/'uploads.json',{})
        self.monitor=None; self.server=None; self.queue_bridge=None; self.queue_read=None
        self.upload_lock=threading.RLock()
        self.lock=threading.RLock(); self.token=secrets.token_urlsafe(32); self.events=deque(maxlen=1000); self.sequence=0
        self._hud_activity=None
        self.jobs={}; self.tasks=queue.Queue(maxsize=8); self.worker=None; self.stop_event=threading.Event()
        from PAFPlayer_windows_media import Bridge
        self.windows_media=Bridge(self)
        self.repair_previews={}; self.enqueue_previews={}; self.queue_history=deque(maxlen=30); self.benchmark=None

    def log(self,event,**fields):
        self.app.append_pafplayer_trace(event,**fields)

    def note_external_activity(self, message, seconds=5):
        """Show a short, path-free account of an external queue/control action."""
        label=' '.join(str(message).split())[:100]
        with self.lock:
            self._hud_activity=(label,time.monotonic()+max(.1,min(float(seconds),15)))

    def hud_activity(self):
        with self.lock:
            active=self._hud_activity
            if active and time.monotonic()<active[1]: return active[0]
            self._hud_activity=None
            return None

    def save_index(self): write_json(self.root/'library.json',self.index)

    def music_library_playlist_path(self):
        """One remembered source for regex search, catalog, and background build."""
        return Path(self.settings.get('music_library_playlist') or getattr(self.app,'AUDIO_CATALOG_PRIMARY',Path(r'C:\mp3\lists\everything.m3u'))).expanduser()

    def ensure_master_playlist(self, extra_paths=()):
        """Schedule a one-time missing master-list build outside playback."""
        destination=self.music_library_playlist_path()
        if destination.is_file(): return False
        with self.lock:
            if getattr(self,'master_build_pending',False): return False
            self.master_build_pending=True
        def build():
            try:
                roots=[getattr(self.app,'AUDIO_CATALOG_LIBRARY_ROOT',None)]
                roots+=list(self.settings.get('library_roots',[]))
                if not any(raw and Path(raw).is_dir() for raw in roots):
                    for raw in extra_paths:
                        parent=Path(raw).parent
                        ancestor=parent.parent
                        roots.append(ancestor if ancestor!=ancestor.parent else parent)
                try: result=build_master_playlist(destination,roots,self.app.AUDIO_EXTENSIONS)
                except Exception as exc:
                    self.log('library.master-build-error',reason=str(exc))
                    raise
                self.log('library.master-built',count=result['count'],created=result['created'])
                return result
            finally:
                with self.lock: self.master_build_pending=False
        try: self.submit(build)
        except ValueError:
            with self.lock: self.master_build_pending=False
            self.log('library.master-build-busy')
            return False
        return True

    def catalog_paths(self, search_from=None, include_outward=False):
        """Combine indexed tracks and filelist, with optional bounded fallback."""
        with self.lock:
            candidates={str(value.get('path') or key) for key,value in self.index.items()
                        if isinstance(value,dict)}
        master=self.music_library_playlist_path()
        if master.is_file():
            try: candidates.update(row['path'] for row in playlist_rows(master)[3])
            except (OSError,UnicodeError,ValueError): pass
        else:
            if include_outward:
                origin=Path(search_from) if search_from and Path(search_from).is_dir() else Path.cwd()
                candidates.update(str(path) for path in scan_media_outward(origin,self.app.AUDIO_EXTENSIONS))
            roots=[getattr(self.app,'AUDIO_CATALOG_LIBRARY_ROOT',None)]
            roots.extend(self.settings.get('library_roots',[]))
            roots=[root for root in roots if root and Path(root).is_dir()]
            if roots:
                candidates.update(str(path) for path in scan_media(roots,self.app.AUDIO_EXTENSIONS,True))
        if self.queue_read:
            state=self.queue_read()
            candidates.update(state.get('entries') or [])
            candidates.update(state.get('next') or [])
        return sorted((path for path in candidates if supported_file(path,self.app.AUDIO_EXTENSIONS)),key=str.casefold)

    def observe_playlist(self, playlist, entries):
        """Index playlist and neighboring music without blocking the audio thread."""
        def discover():
            paths=[Path(raw).resolve() for raw in entries]
            added=0
            with self.lock:
                for path in paths:
                    if supported_file(path,self.app.AUDIO_EXTENSIONS):
                        key=pathkey(path)
                        if key not in self.index:
                            self.index[key]={'path':str(path),'source':'playlist','library_member':True}
                            added+=1
            roots=set()
            configured=[getattr(self.app,'AUDIO_CATALOG_LIBRARY_ROOT',None)]
            configured+=list(getattr(self,'settings',{}).get('library_roots',[]))
            library_roots=[]
            for raw in configured:
                if raw:
                    root=Path(raw).resolve()
                    if root.is_dir() and root!=root.parent: library_roots.append(root)
            for path in paths:
                parent=path.parent.parent
                eligible=[root for root in library_roots if path.is_relative_to(root)]
                if eligible: roots.add(min(eligible,key=lambda root:len(root.parts)))
                elif parent != parent.parent and parent.is_dir(): roots.add(parent)
            for path in scan_media(sorted(roots,key=str),self.app.AUDIO_EXTENSIONS,True):
                with self.lock:
                    key=pathkey(path)
                    if key not in self.index:
                        self.index[key]={'path':str(path),'source':'nearby-playlist','library_member':True}
                        added+=1
            if added:
                with self.lock: self.save_index()
            return len(self.index)
        try: self.submit(discover)
        except ValueError: self.log('library.discovery-busy',playlist=str(playlist))
        instance=getattr(self,'instance',None)
        if instance is None or instance.owns(): self.ensure_master_playlist(entries)

    def save_settings(self): write_json(self.root/'settings.json',self.settings)

    def append_playlist(self,playlist,path):
        playlist=Path(playlist)
        with self.lock:
            if playlist.suffix.casefold() not in ('.m3u','.m3u8'): raise ValueError('Monitor playlist must be M3U or M3U8')
            if playlist.exists():
                text,codec,bom,rows=playlist_rows(playlist)
                if any(pathkey(row['path'])==pathkey(path) for row in rows): return False
            else: text,codec,bom='', 'utf-8', b''
            newline='\r\n' if '\r\n' in text else '\n'
            if text and not text.endswith(('\r','\n')): text+=newline
            replace_bytes(playlist,bom+(text+str(Path(path).resolve())+newline).encode(codec))
            return True

    def start(self):
        if self.worker: return
        def run():
            while not self.stop_event.is_set():
                try: job_id,fn=self.tasks.get(timeout=.5)
                except queue.Empty: continue
                self.jobs[job_id]={'state':'running'}
                try: self.jobs[job_id]={'state':'done','result':fn()}
                except Exception as exc:
                    self.jobs[job_id]={'state':'error','error':str(exc)}; self.log('workflow.error',reason=type(exc).__name__)
        self.worker=threading.Thread(target=run,name='paf-workflows',daemon=True); self.worker.start()

    def submit(self,fn):
        self.start(); job_id=uuid.uuid4().hex
        if len(self.jobs)>100:
            for key in list(self.jobs):
                if self.jobs[key].get('state') in ('done','error'): self.jobs.pop(key)
                if len(self.jobs)<=80: break
        self.jobs[job_id]={'state':'queued'}
        try: self.tasks.put_nowait((job_id,fn))
        except queue.Full: self.jobs.pop(job_id); raise ValueError('Background queue is full; retry later')
        return {'job':job_id}

    def activate(self):
        """Restore explicitly saved integration choices only for a playback session."""
        if getattr(self,'maintenance',None): return
        instance=getattr(self,'instance',None)
        if instance is None or instance.owns(): self.ensure_master_playlist()
        self.windows_media.start()
        if self.settings.get("discord_enabled"):
            from PAFPlayer_discord import Publisher
            self.discord=Publisher(self);self.discord.start()
        config=self.settings.get('monitor')
        if config and not self.monitor:
            self.monitor=FolderMonitor(self,config['roots'],config.get('mode','index'),config.get('playlist'),config.get('recursive',False))
            self.monitor.paused=bool(config.get('paused',False));self.monitor.start()
        def maintain():
            while not self.stop_event.wait(60):
                try:
                    from PAFPlayer_web_workflows import cleanup_uploads
                    with self.upload_lock: cleanup_uploads(self)
                except Exception as exc:self.log('upload.cleanup-error',reason=type(exc).__name__)
        self.maintenance=threading.Thread(target=maintain,name='paf-managed-cleanup',daemon=True);self.maintenance.start()

    def close(self):
        self.stop_event.set()
        if getattr(self,'discord',None): self.discord.close()
        self.windows_media.close()
        if self.monitor: self.monitor.close()
        if self.benchmark: self.benchmark.close()
        if getattr(self,"instance",None): self.instance.close()


def redact(value):
    text=str(value)
    if re.search(r'(?i)upload',text): return text.split(' ',1)[0]+' [uploaded-file details redacted]'
    text=re.sub(r'(?i)("(?:token|password|secret|authorization|webhook|filename)"\s*:\s*)"[^"\n]*"',r'\1"[redacted]"',text)
    text=re.sub(r'https?://\S+','[URL redacted]',text,flags=re.I)
    text=re.sub(r'(?i)(token|password|secret|authorization|webhook)\s*[=:]\s*[^\s,}]+',r'\1=[redacted]',text)
    text=re.sub(r'(?i)(?:[A-Z]:[\\/]|\\\\)[^\r\n"<>]*','[path redacted]',text)
    text=re.sub(r'(?i)(?:/[^\s/]+){2,}','[path redacted]',text)
    return text[:2000]


_runtimes={}
def get_runtime(app):
    key=id(app)
    if key not in _runtimes: _runtimes[key]=Runtime(app)
    return _runtimes[key]
