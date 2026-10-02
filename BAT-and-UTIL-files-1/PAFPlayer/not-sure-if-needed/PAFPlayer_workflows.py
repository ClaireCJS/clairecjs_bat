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
        self.index=read_json(self.root/'library.json',{})
        self.uploads=read_json(self.root/'uploads.json',{})
        self.monitor=None; self.server=None; self.queue_bridge=None; self.queue_read=None
        self.upload_lock=threading.RLock()
        self.lock=threading.RLock(); self.token=secrets.token_urlsafe(32); self.events=deque(maxlen=1000); self.sequence=0
        self.jobs={}; self.tasks=queue.Queue(maxsize=8); self.worker=None; self.stop_event=threading.Event()
        from PAFPlayer_windows_media import Bridge
        self.windows_media=Bridge(self)
        self.repair_previews={}; self.queue_history=deque(maxlen=30); self.benchmark=None

    def log(self,event,**fields):
        self.app.append_pafplayer_trace(event,**fields)

    def save_index(self): write_json(self.root/'library.json',self.index)

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
