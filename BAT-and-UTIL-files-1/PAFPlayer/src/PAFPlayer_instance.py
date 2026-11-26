"""Per-user single-instance ownership and acknowledged, validated loopback handoff."""
from PAFPlayer_workflows import *
import ctypes
import math
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def resolve_request(runtime, targets, *, regex=None, filelist=None):
    app=runtime.app; paths=[]; playlist=None
    if regex is not None:
        pattern=re.compile(regex,re.I)
        source=Path(filelist or runtime.music_library_playlist_path()).resolve()
        if source.is_file():
            text,_,_=decode_playlist(source)
            candidates=[]
            for line in text.splitlines():
                raw=line.strip()
                if not raw or raw.startswith('#'): continue
                path=Path(raw);path=path if path.is_absolute() else source.parent/path
                candidates.append(path)
        else:
            print('PAFPlayer workflow warning: Music collection filelist does not exist: '+str(source)+'; searching the current folder outward, indexed tracks, and configured music folders.')
            candidates=[Path(raw) for raw in runtime.catalog_paths(search_from=Path.cwd(),include_outward=True)]
        for path in candidates:
            if pattern.search(str(path).replace('\\','/')):
                if not supported_file(path,app.AUDIO_EXTENSIONS): raise ValueError('Regex matched a missing/unsupported file: '+str(path))
                paths.append(str(path.resolve()))
        if not paths: raise ValueError('Regex matched no songs in available music library sources')
    else:
        for target in targets:
            path=Path(target).expanduser().resolve()
            if path.is_dir():
                found=sorted(scan_media([path],app.AUDIO_EXTENSIONS,False),key=lambda p:(p.name.casefold(),str(p)))
                if not found: raise ValueError('Folder contains no supported audio: '+str(path))
                paths.extend(str(p) for p in found)
            elif path.suffix.casefold() in app.PLAYLIST_EXTENSIONS:
                if len(targets)!=1: raise ValueError('Pass one playlist at a time')
                if not path.is_file(): raise ValueError('Playlist does not exist: '+str(path))
                # Reuse the application's playlist semantics and relative resolution.
                found=app.load_playlist(path,show_progress=False)
                if not found: raise ValueError('Playlist contains no playable songs: '+str(path))
                paths.extend(str(p.resolve()) for p in found);playlist=str(path)
            elif supported_file(path,app.AUDIO_EXTENSIONS): paths.append(str(path))
            else: raise ValueError('Media target does not exist or is unsupported: '+str(path))
    # A playlist is an ordered sequence of slots; the same file may appear
    # more than once intentionally. Standalone targets and regex results keep
    # their existing deduplication behavior.
    if playlist is None:
        paths=list(dict.fromkeys(paths))
    if not paths: raise ValueError('No media targets supplied')
    if len(paths)>25000: raise ValueError('At most 25,000 tracks per handoff')
    return {'paths':paths,'playlist':playlist}


class Instance:
    def __init__(self,runtime):
        self.runtime=runtime;self.handle=None;self.httpd=None;self.thread=None
        self.path=runtime.root/'instance.json'
        self.identity=secrets.token_hex(8)
        self._owner_thread=None
        self._claim_thread=None
        self._stop_claim=threading.Event()

    def owns(self):
        return bool(self.handle and self._owner_thread in {thread.ident for thread in threading.enumerate()})

    def acquire(self):
        if os.name!='nt': return True
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.CreateMutexW.argtypes=[ctypes.c_void_p,ctypes.c_bool,ctypes.c_wchar_p];kernel.CreateMutexW.restype=ctypes.c_void_p
        name='Local\\PAFPlayer-'+hashlib.sha256(str(self.runtime.root.resolve()).casefold().encode()).hexdigest()[:24]
        self.handle=kernel.CreateMutexW(None,True,name)
        error=ctypes.get_last_error()
        if not self.handle: raise OSError(error,'Cannot acquire PAFPlayer instance ownership')
        if error==183:
            kernel.CloseHandle.argtypes=[ctypes.c_void_p];kernel.CloseHandle(self.handle);self.handle=None;return False
        self._owner_thread=threading.get_ident()
        return True

    def watch_for_claim(self,on_claim):
        """An explicit instance can become official only after winning the same mutex."""
        if os.name!='nt' or self.handle or self._claim_thread: return
        def run():
            try:
                while not self._stop_claim.wait(.5):
                    if self.acquire():
                        try:
                            self.start()
                            if not self._stop_claim.is_set(): on_claim()
                        except Exception as exc:
                            self.runtime.log('tray.claim-error',reason=type(exc).__name__)
                            if self.httpd:
                                self.httpd.shutdown();self.httpd.server_close();self.httpd=None
                            self._release_mutex()
                            continue
                        break
                self._stop_claim.wait()
            finally:
                self._release_mutex()
        self._claim_thread=threading.Thread(target=run,name='paf-instance-claim',daemon=True)
        self._claim_thread.start()

    def forward(self,request,*,timeout=60):
        descriptor=read_json(self.path,{})
        port=descriptor.get('port');token=descriptor.get('token')
        if not isinstance(port,int) or not 1<=port<=65535 or not isinstance(token,str): raise ValueError('Existing PAFPlayer is still starting; retry shortly')
        data=json.dumps(request).encode()
        req=urllib.request.Request(f'http://127.0.0.1:{port}/handoff',data=data,headers={'Content-Type':'application/json','X-PAF-Instance':token})
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            with opener.open(req,timeout=timeout) as response: result=json.loads(response.read(8*1024*1024))
        except urllib.error.HTTPError as exc:
            raise ValueError(json.loads(exc.read(65536)).get('error','Handoff rejected')) from None
        except TimeoutError:
            if request.get('preview_only'):
                raise ValueError('Library search timed out; nothing was queued. Narrow the regex or retry') from None
            raise ValueError('The official player is still resolving this request; it may finish. Check its queue before retrying') from None
        except OSError:
            raise ValueError('Could not reach the official player command listener; playback was not started in this process') from None
        if not result.get('ok'): raise ValueError(result.get('error','Handoff rejected'))
        return result

    def start(self):
        owner=self;token=secrets.token_urlsafe(32)
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args): pass
            def do_POST(self):
                try:
                    if self.path!='/handoff' or self.headers.get('Origin') or not secrets.compare_digest(self.headers.get('X-PAF-Instance',''),token): raise PermissionError('Unauthorized handoff')
                    self.connection.settimeout(10);length=int(self.headers.get('Content-Length','0'))
                    if not 0<length<=8*1024*1024: raise ValueError('Invalid handoff size')
                    data=json.loads(self.rfile.read(length))
                    if not isinstance(data,dict): raise ValueError('Invalid handoff request')
                    if 'dj_test_snapshot' in data:
                        if data != {'dj_test_snapshot':True}: raise ValueError('Invalid DJ test playlist request')
                        from PAFPlayer_web_workflows import queue_snapshot
                        snapshot=queue_snapshot(owner.runtime)
                        entries=snapshot.get('entries',[])
                        if not entries: raise ValueError('No playlist is open in the running player')
                        status=200;value={'ok':True,'queued':0,'entries':entries,'message':'Playlist snapshot'}
                    elif 'seek_seconds' in data:
                        if set(data)!={'seek_seconds'}: raise ValueError('Seek request cannot include media paths')
                        seconds=data['seek_seconds']
                        if isinstance(seconds,bool) or not isinstance(seconds,(int,float)) or not math.isfinite(seconds): raise ValueError('Invalid seek timestamp')
                        bridge=getattr(owner.runtime,'seek_bridge',None)
                        if bridge is None or not bridge(float(seconds)): raise ValueError('Player is not accepting seeks yet')
                        status=200;value={'ok':True,'queued':0,'message':'Seek requested'}
                    elif 'randomize' in data and set(data)=={'randomize'}:
                        if data['randomize'] is not True: raise ValueError('Invalid randomize request')
                        bridge=getattr(owner.runtime,'randomize_bridge',None)
                        deadline=time.monotonic()+15
                        while not callable(bridge) and time.monotonic()<deadline:
                            time.sleep(.05)
                            bridge=getattr(owner.runtime,'randomize_bridge',None)
                        if not callable(bridge): raise ValueError('Player playlist is still starting; retry shortly')
                        outcome=bridge()
                        status=200;value={'ok':True,'queued':0,**outcome}
                    elif 'preview_only' in data:
                        if set(data)!={'selectors','preview_only'} or data['preview_only'] is not True:
                            raise ValueError('Invalid enqueue preview request')
                        from PAFPlayer_workflows import prepare_enqueue_preview
                        preview=prepare_enqueue_preview(owner.runtime,data['selectors'],allow_direct=True)
                        status=200;value={'ok':True,**preview}
                    else:
                        if 'randomize' in data and (data['randomize'] is not True or not data.get('playlist')):
                            raise ValueError('Randomize with media requires one playlist')
                        if 'randomize' in data and set(data) != {'paths', 'playlist', 'randomize'}:
                            raise ValueError('Invalid playlist randomize request')
                        if 'randomize' in data and not isinstance(data['playlist'], str):
                            raise ValueError('Invalid playlist randomize request')
                        warning=None
                        opacity=data.get('floating_opacity')
                        if opacity is not None:
                            if type(opacity) is not int or not 10<=opacity<=100: raise ValueError('Floating Lyrics opacity must be 10..100 percent')
                            if not callable(getattr(owner.runtime,'opacity_bridge',None)): raise ValueError('Floating Lyrics is not accepting opacity commands yet')
                        if 'preview_token' in data:
                            if not set(data)<= {'preview_token','placement'}:
                                raise ValueError('Invalid enqueue preview commit')
                            from PAFPlayer_workflows import consume_enqueue_preview
                            paths=consume_enqueue_preview(owner.runtime,data['preview_token'])
                        elif 'selectors' in data:
                            if not set(data)<= {'selectors','placement'}: raise ValueError('Enqueue selectors cannot change playback options')
                            paths=enqueue_selectors(owner.runtime,data['selectors'],allow_direct=True)
                        else: paths=data.get('paths',[])
                        if not isinstance(paths,list) or len(paths)>25000: raise ValueError('Invalid media list')
                        if paths:
                            if any(not supported_file(x,owner.runtime.app.AUDIO_EXTENSIONS) for x in paths): raise ValueError('Media changed or disappeared before handoff')
                            if data.get('randomize'):
                                bridge=getattr(owner.runtime,'randomize_bridge',None)
                                if not callable(bridge): raise ValueError('Player playlist is still starting; request was not accepted; retry shortly')
                            if not owner.runtime.queue_bridge:
                                deadline=time.monotonic()+15
                                while not owner.runtime.queue_bridge and time.monotonic()<deadline:
                                    time.sleep(.05)
                            if not owner.runtime.queue_bridge:
                                raise ValueError('Player queue is still starting; request was not accepted; retry shortly')
                            from PAFPlayer_web_workflows import queue_snapshot,edit_queue,enqueue_placement
                            placement=enqueue_placement(owner.runtime,data.get('placement')) if 'selectors' in data or 'preview_token' in data else None
                            before=queue_snapshot(owner.runtime)
                            existing={os.path.normcase(path) for path in before.get('entries',[])}
                            already_in_playlist=sum(os.path.normcase(path) in existing for path in paths)
                            result=edit_queue(owner.runtime,{'op':'load' if data.get('playlist') else 'add','paths':paths,'playlist':data.get('playlist'),'revision':before['revision'],**({'placement':placement} if placement else {})},source='another PAFPlayer')
                            revision=result['revision']
                            if data.get('randomize'):
                                try:
                                    outcome=bridge()
                                    if outcome.get('warning'): warning=outcome['message']
                                except Exception as exc:
                                    warning=str(exc)
                        elif set(data)!={'floating_opacity'}: raise ValueError('Invalid media list')
                        else: revision=None;already_in_playlist=0
                        if opacity is not None and not owner.runtime.opacity_bridge(opacity): raise ValueError('Floating Lyrics is not accepting opacity commands yet')
                        status=200;value={'ok':True,'queued':len(paths),'message':('Playlist loaded, but not randomized: '+str(warning) if warning else 'Loaded and randomized playlist' if data.get('randomize') else 'Loaded playlist' if data.get('playlist') else 'Queued at end' if placement=='end' else 'Queued next') if paths else 'Floating Lyrics opacity set for this run','revision':revision,
                                          'already_in_playlist':already_in_playlist,
                                          'added_to_playlist':len(paths)-already_in_playlist}
                        if warning: value['warning']=True
                except Exception as exc: status=400;value={'error':str(exc)}
                body=json.dumps(value).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
        self.httpd=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.thread=threading.Thread(target=self.httpd.serve_forever,kwargs={'poll_interval':.2},name='paf-instance',daemon=True);self.thread.start()
        write_json(self.path,{'pid':os.getpid(),'port':self.httpd.server_port,'token':token,'identity':self.identity})

    def _release_mutex(self):
        if self.handle:
            kernel=ctypes.WinDLL('kernel32',use_last_error=True)
            kernel.ReleaseMutex.argtypes=[ctypes.c_void_p];kernel.CloseHandle.argtypes=[ctypes.c_void_p]
            kernel.ReleaseMutex(self.handle);kernel.CloseHandle(self.handle);self.handle=None
            self._owner_thread=None

    def close(self):
        self._stop_claim.set()
        if self._claim_thread and self._claim_thread is not threading.current_thread():
            self._claim_thread.join(timeout=3)
        if self.httpd:
            self.httpd.shutdown();self.httpd.server_close();self.httpd=None
        if self._owner_thread==threading.get_ident(): self._release_mutex()


def other_player_running():
    """Inspect same-session player processes, including older and explicit instances."""
    if os.name != 'nt': return False
    import re
    from ctypes import wintypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    psapi = ctypes.WinDLL('psapi', use_last_error=True)
    query = ctypes.WinDLL('ntdll').NtQueryInformationProcess
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE,wintypes.DWORD,wintypes.LPWSTR,ctypes.POINTER(wintypes.DWORD)]
    query.argtypes = [wintypes.HANDLE,ctypes.c_int,ctypes.c_void_p,wintypes.ULONG,ctypes.POINTER(wintypes.ULONG)]
    query.restype = ctypes.c_long
    class UnicodeString(ctypes.Structure):
        _fields_ = [('length',wintypes.USHORT),('maximum',wintypes.USHORT),('buffer',ctypes.c_void_p)]
    pids = (wintypes.DWORD * 16384)(); used = wintypes.DWORD()
    if not psapi.EnumProcesses(pids,ctypes.sizeof(pids),ctypes.byref(used)): return True
    own_session = wintypes.DWORD()
    if not kernel.ProcessIdToSessionId(os.getpid(),ctypes.byref(own_session)): return True
    for pid in pids[:used.value // ctypes.sizeof(wintypes.DWORD)]:
        if not pid or pid == os.getpid(): continue
        session = wintypes.DWORD()
        if not kernel.ProcessIdToSessionId(pid,ctypes.byref(session)) or session.value != own_session.value: continue
        handle = kernel.OpenProcess(0x1000,False,pid)
        if not handle: continue
        try:
            path = ctypes.create_unicode_buffer(32768); size = wintypes.DWORD(len(path))
            if not kernel.QueryFullProcessImageNameW(handle,0,path,ctypes.byref(size)): continue
            name = Path(path.value).name.casefold()
            if name == 'pafplayer.exe': return True
            if name not in ('python.exe','pythonw.exe','pypy.exe','pypy3.exe'): continue
            needed = wintypes.ULONG()
            query(handle,60,None,0,ctypes.byref(needed))
            if not 0 < needed.value <= 1024*1024: return True
            data = ctypes.create_string_buffer(needed.value)
            if query(handle,60,data,len(data),ctypes.byref(needed)) < 0: return True
            value = UnicodeString.from_buffer(data)
            start = ctypes.addressof(data)
            if not value.buffer or not start <= value.buffer <= start+len(data)-value.length: return True
            command = ctypes.wstring_at(value.buffer,value.length//2)
            if re.search(r'(?i)(?:^|[\\/"\s])pafplayer(?:_v[0-9]+[^\\/"\s]*)?\.py(?:["\s]|$)',command): return True
        finally:
            kernel.CloseHandle(handle)
    return False
