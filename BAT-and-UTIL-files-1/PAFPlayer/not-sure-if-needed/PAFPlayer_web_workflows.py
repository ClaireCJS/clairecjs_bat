"""HTTP and queue integration for PAFPlayer's opt-in workflows."""
from __future__ import annotations
from PAFPlayer_workflows import *


def missing_playlist_paths(runtime,playlist):
    if not playlist: return []
    try:
        stat=Path(playlist).stat(); signature=(str(playlist),stat.st_size,stat.st_mtime_ns)
        cached=getattr(runtime,'missing_playlist_cache',None)
        if cached and cached[0]==signature: return cached[1]
        _,_,_,rows=playlist_rows(playlist)
        missing=[row['path'] for row in rows if not Path(row['path']).is_file()]
        runtime.missing_playlist_cache=(signature,missing)
        return missing
    except (OSError,ValueError): return []


def queue_snapshot(runtime):
    state=runtime.queue_read() if runtime.queue_read else {'entries':[], 'next':[], 'current':None, 'playlist':None, 'reason':'No active playlist'}
    state=dict(state)
    state['revision']=hashlib.sha256(json.dumps(state,sort_keys=True,default=str).encode()).hexdigest()[:20]
    return state


def edit_queue(runtime,payload):
    if not runtime.queue_bridge: raise ValueError('Open a playlist before editing its queue')
    # The playback bridge owns its own lock for a read/compare/write transaction.
    return runtime.queue_bridge(payload)


def calculate_queue_edit(runtime,state,payload):
    revision=hashlib.sha256(json.dumps(state,sort_keys=True,default=str).encode()).hexdigest()[:20]
    if payload.get('revision')!=revision: raise ValueError('CONFLICT: queue changed; refresh and retry')
    old=json.loads(json.dumps(state)); entries=list(state['entries']); next_up=list(state['next']); op=payload.get('op'); selected=list(dict.fromkeys(payload.get('paths',[])))
    if len(selected)>5000: raise ValueError('Too many selected tracks')
    if op not in ('add','load','undo','save') and any(x not in entries for x in selected): raise ValueError('Selection is no longer in the playlist')
    if op=='undo':
        if not runtime.queue_history: raise ValueError('Nothing to undo')
        change=runtime.queue_history[-1]
        if change['after']!=revision: raise ValueError('CONFLICT: queue changed since last edit; undo would overwrite newer changes')
        restored=change['before']; runtime.queue_history.pop(); return restored
    if op=='save':
        name=str(payload.get('name','queue.m3u8'))
        if Path(name).name!=name or not re.fullmatch(r'[\w .()-]{1,90}\.m3u8?',name,re.I): raise ValueError('Use a simple .m3u or .m3u8 filename')
        destination=unique(runtime.root/'playlists'/name)
        destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_bytes(('#EXTM3U\n'+'\n'.join(entries)+'\n').encode('utf-8'))
        runtime.log('queue.saved',path=str(destination),tracks=len(entries)); return dict(state,saved_path=str(destination))
    if op in ('add','load'):
        if op=='load': entries=[];next_up=[];state=dict(state,playlist=payload.get('playlist'))
        for raw in selected:
            if not supported_file(raw,runtime.app.AUDIO_EXTENSIONS): raise ValueError('Unsupported or missing media')
            if raw not in entries: entries.append(raw)
        next_up=selected+[x for x in next_up if x not in selected]
    elif op=='remove': entries=[x for x in entries if x not in selected]; next_up=[x for x in next_up if x not in selected]
    elif op in ('next','after-current'):
        next_up=selected+[x for x in next_up if x not in selected]
    elif op in ('top','bottom','move'):
        remaining=[x for x in entries if x not in selected]
        at=0 if op=='top' else len(remaining) if op=='bottom' else max(0,min(len(remaining),int(payload.get('index',0))))
        entries=remaining[:at]+selected+remaining[at:]
    elif op=='replace':
        replacements=payload.get('replacements',{})
        for before,after in replacements.items():
            if before not in entries or Path(before).exists() or not supported_file(after,runtime.app.AUDIO_EXTENSIONS): raise ValueError('Repair selection is stale or invalid')
        entries=[replacements.get(x,x) for x in entries]; next_up=[replacements.get(x,x) for x in next_up]
    else: raise ValueError('Unknown queue operation')
    result=dict(state,entries=entries,next=next_up)
    if 'missing' in result: result['missing']=[x for x in entries if not Path(x).is_file()]
    after=hashlib.sha256(json.dumps(result,sort_keys=True,default=str).encode()).hexdigest()[:20]
    runtime.queue_history.append({'before':old,'after':after,'time':time.time(),'operation':op,'added':[x for x in entries if x not in old['entries']],'removed':[x for x in old['entries'] if x not in entries]})
    runtime.log('queue.edit',operation=op,count=len(selected))
    return result


def authorized(handler,owner,runtime, *, mutating=False):
    host=handler.headers.get('Host','')
    parsed=urlsplit('http://'+host)
    names={'localhost','127.0.0.1','::1',socket.gethostname().casefold(),socket.getfqdn().casefold()}
    try: names.update(x[4][0].casefold() for x in socket.getaddrinfo(socket.gethostname(),None))
    except OSError: pass
    if owner.host not in ('0.0.0.0','::',''): names.add(owner.host.casefold())
    if parsed.hostname not in names or parsed.port!=owner.port: raise PermissionError('Invalid server address')
    origin=handler.headers.get('Origin')
    if origin and urlsplit(origin).netloc.casefold()!=host.casefold(): raise PermissionError('Cross-origin request rejected')
    if handler.headers.get('Sec-Fetch-Site')=='cross-site': raise PermissionError('Cross-site request rejected')
    local=handler._client_is_local()
    if not local and not runtime.settings.get('remote_uploads'): raise PermissionError('Remote workflows are disabled in Security')
    if mutating and not secrets.compare_digest(handler.headers.get('X-PAF-Workflow-Token',''),runtime.token): raise PermissionError('Workflow pairing token required')
    return local


def safe_filename(value,extensions):
    name=unquote(str(value))
    if not name or len(name)>180 or name!=Path(name).name or re.search(r'[<>:"/\\|?*\x00-\x1f]',name) or name.endswith((' ','.')): raise ValueError('Unsafe filename')
    if name.split('.')[0].upper() in {'CON','PRN','AUX','NUL',*(f'COM{i}' for i in range(1,10)),*(f'LPT{i}' for i in range(1,10))}: raise ValueError('Reserved filename')
    if Path(name).suffix.casefold() not in extensions: raise ValueError('Unsupported media type')
    return name


def cleanup_uploads(runtime,now=None):
    now=time.time() if now is None else now; root=(runtime.root/'uploads').resolve(); changed=False
    playing=str(runtime.server.current_audio()) if runtime.server and runtime.server.current_audio() else ''
    queue_state=queue_snapshot(runtime); in_use=set(queue_state['entries'])|set(queue_state['next'])|{playing}
    for key,info in list(runtime.uploads.items()):
        path=Path(key).resolve()
        if now-info['created']<UPLOAD_TTL_SECONDS or str(path) in in_use: continue
        if path.parent!=root: continue
        if path.exists(): recycle(path)
        runtime.uploads.pop(key); runtime.index.pop(pathkey(path),None); changed=True
    if changed: write_json(runtime.root/'uploads.json',runtime.uploads); runtime.save_index()


def receive_upload(handler,runtime):
    if not runtime.settings.get('remote_uploads'): raise PermissionError('Uploads are disabled in Security')
    name=safe_filename(handler.headers.get('X-File-Name',''),runtime.app.AUDIO_EXTENSIONS)
    length=int(handler.headers.get('Content-Length','0'))
    if length<=0 or length>MAX_FILE_BYTES: raise ValueError('Upload must be between 1 byte and 100 MiB')
    root=runtime.root/'uploads'; root.mkdir(parents=True,exist_ok=True)
    with runtime.upload_lock:
        cleanup_uploads(runtime)
        # Include incomplete/invalid files in the quota until explicitly recycled.
        if sum(x.stat().st_size for x in root.iterdir() if x.is_file())+length>MAX_UPLOAD_BYTES: raise ValueError('Managed upload quota (512 MiB) exceeded')
        destination=unique(root/name); handler.connection.settimeout(15)
        try:
            with destination.open('xb') as stream:
                remaining=length
                while remaining:
                    block=handler.rfile.read(min(remaining,65536))
                    if not block: raise ValueError('Incomplete upload')
                    stream.write(block); remaining-=len(block)
            # A supported extension alone is not validation of media contents.
            executable=runtime.app.ffprobe_executable()
            if not executable: raise ValueError('FFprobe is required to validate uploads')
            result=subprocess.run([str(executable),'-v','error','-select_streams','a','-show_entries','stream=codec_type','-of','json',str(destination)],capture_output=True,timeout=12,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            if result.returncode or not json.loads(result.stdout).get('streams'): raise ValueError('File contains no decodable audio stream')
        except Exception:
            if destination.exists(): recycle(destination)
            raise
        key=str(destination.resolve()); runtime.uploads[key]={'created':time.time(),'bytes':length}
        runtime.index[pathkey(destination)]={'path':key,'size':length,'source':'uploaded'}
        write_json(runtime.root/'uploads.json',runtime.uploads); runtime.save_index()
        runtime.log('upload.accepted',bytes=length)
        state=queue_snapshot(runtime)
        if runtime.queue_bridge: edit_queue(runtime,{'op':'add','paths':[key],'revision':state['revision']})
        return {'ok':True,'queued':bool(runtime.queue_bridge),'path':key,'filename':name}


def repair_preview(runtime,payload):
    playlist=payload.get('playlist'); queue_state=queue_snapshot(runtime)
    if playlist:
        playlist=Path(playlist).resolve()
        if playlist.suffix.casefold() not in ('.m3u','.m3u8','.pls'): raise ValueError('Repair supports M3U, M3U8 and PLS playlists')
        _,_,_,rows=playlist_rows(playlist); paths=[r['path'] for r in rows]; fingerprint=digest(playlist)
    else: paths=queue_state['entries']; fingerprint=None
    roots=payload.get('roots',[])+runtime.settings.get('library_roots',[])
    missing=[x for x in paths if not Path(x).is_file()]
    items=[]
    for path in missing[:100]:
        evidence=runtime.index.get(pathkey(path),{})
        items.append({'missing':path,'candidates':repair_candidates(runtime.app,path,roots,recursive=bool(payload.get('recursive')),evidence=evidence)})
    token=uuid.uuid4().hex
    result={'id':token,'items':items,'playlist':str(playlist) if playlist else None,'hash':fingerprint,'queue_revision':queue_state['revision'],'created':time.time(),'truncated':len(missing)>100}
    runtime.repair_previews[token]=result
    for key,old in list(runtime.repair_previews.items()):
        if time.time()-old['created']>1800: runtime.repair_previews.pop(key)
    return result


def apply_repair(runtime,payload):
    with getattr(runtime,"queue_transaction_lock",runtime.lock):
        return _apply_repair_locked(runtime,payload)


def _apply_repair_locked(runtime,payload):
    preview=runtime.repair_previews.get(str(payload.get('id')))
    if not preview or time.time()-preview['created']>1800: raise ValueError('Repair preview expired')
    chosen={}
    for item in preview['items']:
        selected=payload.get('approved',{}).get(item['missing'])
        if not selected: continue
        match=next((x for x in item['candidates'] if x['path']==selected),None)
        if not match: raise ValueError('Replacement was not a previewed candidate')
        stat=Path(selected).stat()
        if stat.st_size!=match['size'] or stat.st_mtime_ns!=match['mtime_ns']: raise ValueError('Candidate changed; preview again')
        if Path(item['missing']).exists(): raise ValueError('Original path now exists; preview again')
        chosen[item['missing']]=match
    dry=bool(payload.get('dry_run',True)); result={'changes':chosen,'dry_run':dry}
    if not payload.get('playlist_only') and not dry and chosen:
        if queue_snapshot(runtime)['revision']!=preview['queue_revision']:
            raise ValueError('CONFLICT: queue changed; preview repairs again before writing anything')
    if preview['playlist']:
        result=rewrite_playlist(runtime.app,preview['playlist'],chosen,expected_hash=preview['hash'],dry_run=dry)
    if not payload.get('playlist_only') and not dry and chosen:
        edit_queue(runtime,{'op':'replace','revision':preview['queue_revision'],'replacements':{old:new['path'] for old,new in chosen.items()}})
        if not preview['playlist']:
            for old,new in chosen.items(): runtime.log('repair.approved',old_path=old,replacement_path=new['path'],confidence=new['confidence'],evidence=new['evidence'],timestamp=datetime.now(timezone.utc).isoformat())
    return result


def handle(handler,owner,path):
    """Return True only for endpoints owned by this module."""
    if not path.startswith('/api/workflows/'): return False
    runtime=owner.workflows; operation=path.removeprefix('/api/workflows/')
    try:
        local=authorized(handler,owner,runtime,mutating=handler.command=='POST')
        if handler.command=='GET':
            if operation=='status':
                data={'settings':runtime.settings,'local':local,'token':runtime.token if local else None,'queue':queue_snapshot(runtime),'history':[{'time':x['time'],'operation':x['operation'],'added':x['added'],'removed':x['removed']} for x in runtime.queue_history], 'monitor':{'paused':runtime.monitor.paused,'roots':runtime.monitor.roots,'mode':runtime.monitor.mode,'actions':list(runtime.monitor.actions)} if runtime.monitor else None,'index':{k:{'source':v.get('source'),'filename':Path(k).name} for k,v in runtime.index.copy().items()},'discord':getattr(runtime,'discord_status','Disabled'),'windows_media':{'settings':__import__('PAFPlayer_windows_media').settings(runtime),'status':runtime.windows_media.status}}
            elif operation.startswith('job/'):
                data=runtime.jobs.get(operation.split('/')[-1],{'state':'missing'})
            elif operation=='logs':
                from urllib.parse import parse_qs
                query=parse_qs(handler.path.partition('?')[2]); after=int(query.get('after',['0'])[0]); level=query.get('level',[''])[0]; category=query.get('category',[''])[0]; search=query.get('search',[''])[0].casefold()
                # Bound work and bandwidth per poll; paused clients do not poll.
                records=list(runtime.events)
                data={'cursor':runtime.sequence,'records':[x for x in records if x['id']>after and (not level or x['level']==level) and (not category or x['category']==category) and (not search or search in x['message'].casefold())][-200:]}
            else: raise ValueError('Unknown workflow endpoint')
            handler._json(200,data); return True
        if operation=='upload': handler._json(200,receive_upload(handler,runtime)); return True
        length=int(handler.headers.get('Content-Length','0'))
        if not 0<length<=262144: raise ValueError('JSON request too large or empty')
        handler.connection.settimeout(15)
        payload=json.loads(handler.rfile.read(length).decode('utf-8'))
        if not isinstance(payload,dict): raise ValueError('Expected JSON object')
        if operation=='settings':
            if not local: raise PermissionError('Only the player computer can change Security or library roots')
            if 'remote_uploads' in payload: runtime.settings['remote_uploads']=bool(payload['remote_uploads'])
            if 'library_roots' in payload:
                roots=payload['library_roots']
                if not isinstance(roots,list) or len(roots)>20: raise ValueError('At most 20 library roots')
                if any(not Path(x).is_dir() for x in roots): raise ValueError('Library roots must be existing directories')
                runtime.settings['library_roots']=[str(Path(x).resolve()) for x in roots]
            runtime.save_settings(); data={'ok':True}
        elif operation=='queue':
            if payload.get('op') in ('add','load'): raise PermissionError('Use validated drops or library imports to add media')
            data=edit_queue(runtime,payload)
        elif operation=='resolve-drop':
            if not local: raise PermissionError('Local file matching is available only on the player computer')
            files=payload.get('files',[])
            if len(files)>1000: raise ValueError('Drop at most 1000 files at a time')
            def resolve():
                state=queue_snapshot(runtime); known=set(state['entries'])|set(runtime.index)
                roots=runtime.settings.get('library_roots',[])
                known.update(str(x) for x in scan_media(roots,runtime.app.AUDIO_EXTENSIONS,True))
                resolved=[]; unresolved=[]
                for item in files:
                    matches=[]
                    for raw in known:
                        path=Path(raw)
                        if path.name.casefold()==str(item.get('name','')).casefold() and path.is_file() and path.stat().st_size==item.get('size'): matches.append(str(path.resolve()))
                    matches=list(dict.fromkeys(matches))
                    if len(matches)==1: resolved+=matches
                    else: unresolved.append({'name':item.get('name'),'reason':'ambiguous' if matches else 'not indexed'})
                if resolved: edit_queue(runtime,{'op':'add','paths':resolved,'revision':state['revision']})
                return {'queued':len(resolved),'unresolved':unresolved}
            data=runtime.submit(resolve)
        elif operation=='library':
            search=str(payload.get('search','')).casefold().strip()
            if not search: raise ValueError('Enter a library filename search')
            matches=[{'path':v['path'],'filename':Path(v['path']).name} for v in runtime.index.copy().values()
                     if search in Path(v.get('path','')).name.casefold() and Path(v.get('path','')).is_file()][:200]
            if payload.get('preview'): data={'items':matches}
            else:
                allowed={x['path'] for x in matches}; approved=payload.get('approved',[])
                if not approved or any(x not in allowed for x in approved): raise ValueError('Library selection changed; preview again')
                data=edit_queue(runtime,{'op':'add','paths':approved,'revision':queue_snapshot(runtime)['revision']})
        elif operation=='repair-preview':
            if not local and payload.get('playlist'): raise PermissionError('Remote repair is limited to the active queue')
            if not local: payload['roots']=[]
            data=runtime.submit(lambda:repair_preview(runtime,payload))
        elif operation=='repair-apply': data=runtime.submit(lambda:apply_repair(runtime,payload))
        elif operation=='monitor':
            if not local: raise PermissionError('Folder monitoring is local only')
            op=payload.get('op')
            if op=='start':
                roots=payload.get('roots',[])
                if not roots or len(roots)>20 or any(not Path(x).is_dir() for x in roots): raise ValueError('Choose 1–20 existing directories')
                mode=payload.get('mode','index')
                if mode not in ('index','playlist','library'): raise ValueError('Invalid monitor mode')
                if mode=='playlist' and (not payload.get('playlist') or Path(payload['playlist']).suffix.casefold() not in ('.m3u','.m3u8')): raise ValueError('Choose an M3U/M3U8 destination playlist')
                if runtime.monitor: runtime.monitor.close()
                runtime.monitor=FolderMonitor(runtime,roots,mode,payload.get('playlist'),bool(payload.get('recursive'))); runtime.monitor.start()
                runtime.settings['monitor']={'roots':roots,'mode':mode,'playlist':payload.get('playlist'),'recursive':bool(payload.get('recursive'))}; runtime.save_settings()
                data={'ok':True}
            elif not runtime.monitor: raise ValueError('No monitor configured')
            elif op=='pause': runtime.monitor.paused=True; runtime.settings.setdefault('monitor',{})['paused']=True; runtime.save_settings(); data={'ok':True}
            elif op=='resume': runtime.monitor.paused=False; runtime.settings.setdefault('monitor',{})['paused']=False; runtime.save_settings(); runtime.monitor.wake.set(); data={'ok':True}
            elif op=='scan': data=runtime.submit(lambda:runtime.monitor.scan(dry_run=bool(payload.get('dry_run'))))
            else: raise ValueError('Unknown monitor operation')
        elif operation=='windows-media':
            if not local: raise PermissionError('Windows integration settings are local only')
            data=runtime.windows_media.configure(payload)
        elif operation=='discord':
            if not local: raise PermissionError('Discord configuration is local only')
            from PAFPlayer_discord import configure
            data=configure(runtime,payload)
        else: raise ValueError('Unknown workflow operation')
        handler._json(200,data)
    except PermissionError as exc: handler._json(403,{'error':str(exc)})
    except (ValueError,OSError,TimeoutError,queue.Full) as exc: handler._json(409 if 'CONFLICT:' in str(exc) else 400,{'error':str(exc)})
    except Exception as exc:
        runtime.log('workflow.error',reason=type(exc).__name__); handler._json(500,{'error':'Workflow failed; see local PAFPlayer log'})
    return True
