"""Per-user single-instance ownership and acknowledged, validated loopback handoff."""
from PAFPlayer_workflows import *
import ctypes
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def resolve_request(runtime, targets, *, regex=None, filelist=None):
    app=runtime.app; paths=[]; playlist=None
    if regex is not None:
        pattern=re.compile(regex,re.I)
        source=Path(filelist or app.AUDIO_CATALOG_FALLBACK).resolve()
        if not source.is_file(): raise ValueError('Music collection filelist does not exist: '+str(source))
        text,_,_=decode_playlist(source)
        for line in text.splitlines():
            raw=line.strip()
            if not raw or raw.startswith('#'): continue
            path=Path(raw);path=path if path.is_absolute() else source.parent/path
            if pattern.search(str(path).replace('\\','/')):
                if not supported_file(path,app.AUDIO_EXTENSIONS): raise ValueError('Regex matched a missing/unsupported file: '+str(path))
                paths.append(str(path.resolve()))
        if not paths: raise ValueError('Regex matched no songs in '+str(source))
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
    paths=list(dict.fromkeys(paths))
    if not paths: raise ValueError('No media targets supplied')
    if len(paths)>25000: raise ValueError('At most 25,000 tracks per handoff')
    return {'paths':paths,'playlist':playlist}


class Instance:
    def __init__(self,runtime):
        self.runtime=runtime;self.handle=None;self.httpd=None;self.thread=None
        self.path=runtime.root/'instance.json'

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
        return True

    def forward(self,request):
        descriptor=read_json(self.path,{})
        port=descriptor.get('port');token=descriptor.get('token')
        if not isinstance(port,int) or not 1<=port<=65535 or not isinstance(token,str): raise ValueError('Existing PAFPlayer is still starting; retry shortly')
        data=json.dumps(request).encode()
        req=urllib.request.Request(f'http://127.0.0.1:{port}/handoff',data=data,headers={'Content-Type':'application/json','X-PAF-Instance':token})
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            with opener.open(req,timeout=15) as response: result=json.loads(response.read(65536))
        except urllib.error.HTTPError as exc:
            raise ValueError(json.loads(exc.read(65536)).get('error','Handoff rejected')) from None
        except OSError: raise ValueError('Existing PAFPlayer is not accepting commands yet; retry instead of starting competing playback') from None
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
                    data=json.loads(self.rfile.read(length));paths=data.get('paths',[])
                    if not isinstance(paths,list) or not 0<len(paths)<=25000: raise ValueError('Invalid media list')
                    if any(not supported_file(x,owner.runtime.app.AUDIO_EXTENSIONS) for x in paths): raise ValueError('Media changed or disappeared before handoff')
                    if not owner.runtime.queue_bridge: raise ValueError('Player queue is starting; retry shortly')
                    from PAFPlayer_web_workflows import queue_snapshot,edit_queue
                    result=edit_queue(owner.runtime,{'op':'load' if data.get('playlist') else 'add','paths':paths,'playlist':data.get('playlist'),'revision':queue_snapshot(owner.runtime)['revision']})
                    status=200;value={'ok':True,'queued':len(paths),'message':'Loaded playlist' if data.get('playlist') else 'Queued next','revision':result['revision']}
                except Exception as exc: status=400;value={'error':str(exc)}
                body=json.dumps(value).encode();self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
        self.httpd=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.thread=threading.Thread(target=self.httpd.serve_forever,kwargs={'poll_interval':.2},name='paf-instance',daemon=True);self.thread.start()
        write_json(self.path,{'pid':os.getpid(),'port':self.httpd.server_port,'token':token})

    def close(self):
        if self.httpd:
            self.httpd.shutdown();self.httpd.server_close();self.httpd=None
        if self.handle:
            kernel=ctypes.WinDLL('kernel32',use_last_error=True)
            kernel.ReleaseMutex.argtypes=[ctypes.c_void_p];kernel.CloseHandle.argtypes=[ctypes.c_void_p]
            kernel.ReleaseMutex(self.handle);kernel.CloseHandle(self.handle);self.handle=None
