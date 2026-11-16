"""Opt-in, session-only touchpad for controlling the player computer."""
import ctypes
import json
import math
import os
import secrets
import threading
import time
from urllib.parse import urlsplit

PAGE = r'''<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>PAFPlayer mouse</title>
<style>
*{box-sizing:border-box}body{margin:0;padding:12px;background:#10151f;color:#edf5ff;font:16px system-ui,sans-serif}
main{max-width:760px;margin:auto}h1{margin:.2em 0;font-size:1.4rem}
.buttons{display:flex;gap:10px;margin:10px 0}.buttons button{flex:1;min-height:64px;font-size:1.1rem;font-weight:700}
button{border:1px solid #7099ba;border-radius:9px;background:#213951;color:white;padding:10px;touch-action:manipulation}
button:disabled{opacity:.45}button:active{background:#42698b}
#pad{height:min(58vh,500px);min-height:260px;border:2px solid #78c6e5;border-radius:14px;background:linear-gradient(145deg,#243d51,#142531);touch-action:none;user-select:none;-webkit-user-select:none;display:flex;align-items:center;justify-content:center;color:#b7d4e3;text-align:center}
#pad.disabled{opacity:.45}input{font:20px monospace;max-width:10em;padding:8px;background:#172533;color:white;border:1px solid #86b5cf;border-radius:5px}
.pair{display:flex;gap:8px;align-items:center;flex-wrap:wrap}.note{color:#bdcbd8;font-size:.9rem}#status{min-height:1.5em;color:#ffcf75}
</style></head><body><main><h1>🖱️ PAFPlayer mouse</h1>
<div class="buttons"><button id="left" disabled>Left click</button><button id="right" disabled>Right click</button></div>
<div class="pair"><label for="code">Host pairing code</label><input id="code" type="password" inputmode="numeric" pattern="[0-9]*" maxlength="8" autocomplete="off"><button id="pair">Connect</button></div>
<p id="status" role="status">On the host, start PAFPlayer with --remote-mouse and enter its pairing code here.</p>
<div id="pad" class="disabled">Move one finger here to move the host pointer</div>
<p class="note">This controls the host pointer and clicks. Use only on a trusted network; this HTTP connection is not encrypted. Closing this page disconnects it.</p>
<script>
let code='',tracking=false,lastX=0,lastY=0,dx=0,dy=0,sending=false,requestGeneration=0;
const pad=document.getElementById('pad'),status=document.getElementById('status'),left=document.getElementById('left'),right=document.getElementById('right');
function connected(on){left.disabled=!on;right.disabled=!on;pad.classList.toggle('disabled',!on)}
async function send(path,body,activeCode=code){
 const response=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-PAF-Mouse-Code':activeCode},body:JSON.stringify(body),cache:'no-store'});
 if(!response.ok){let msg='Connection failed';try{msg=(await response.json()).error||msg}catch(e){}throw Error(msg)}
}
document.getElementById('pair').addEventListener('click',async()=>{
 const candidate=document.getElementById('code').value.trim();if(!/^\d{8}$/.test(candidate)){status.textContent='Enter the eight-digit code shown on the host.';return}
 try{await send('/api/paf-mouse/pair',{},candidate);requestGeneration++;code=candidate;document.getElementById('code').value='';connected(true);status.textContent='Connected. Move your finger on the touchpad.'}
 catch(e){code='';connected(false);status.textContent=e.message}
});
async function click(button){if(!code)return;try{await send('/api/paf-mouse/control',{action:'click',button})}catch(e){code='';connected(false);status.textContent=e.message}}
left.addEventListener('click',()=>click('left'));right.addEventListener('click',()=>click('right'));
pad.addEventListener('pointerdown',e=>{if(!code||tracking)return;tracking=true;lastX=e.clientX;lastY=e.clientY;pad.setPointerCapture(e.pointerId);e.preventDefault()});
pad.addEventListener('pointermove',e=>{if(!tracking||!code)return;dx+=e.clientX-lastX;dy+=e.clientY-lastY;lastX=e.clientX;lastY=e.clientY;e.preventDefault()});
function stop(){tracking=false}pad.addEventListener('pointerup',stop);pad.addEventListener('pointercancel',stop);window.addEventListener('blur',stop);
setInterval(async()=>{if(!code||sending||(!dx&&!dy))return;const mx=Math.max(-150,Math.min(150,Math.round(dx))),my=Math.max(-150,Math.min(150,Math.round(dy)));dx-=mx;dy-=my;if(!mx&&!my)return;sending=true;const gen=requestGeneration;try{await send('/api/paf-mouse/control',{action:'move',dx:mx,dy:my})}catch(e){if(gen===requestGeneration){code='';connected(false);status.textContent=e.message}}finally{sending=false}},35);
</script></main></body></html>'''


class WindowsPointer:
    def __init__(self):
        from ctypes import wintypes
        self.user32=ctypes.WinDLL('user32',use_last_error=True)
        self.point_type=wintypes.POINT
        self.user32.GetCursorPos.argtypes=[ctypes.POINTER(wintypes.POINT)]
        self.user32.GetCursorPos.restype=wintypes.BOOL
        self.user32.SetCursorPos.argtypes=[ctypes.c_int,ctypes.c_int]
        self.user32.SetCursorPos.restype=wintypes.BOOL
        self.user32.GetSystemMetrics.argtypes=[ctypes.c_int]
        self.user32.GetSystemMetrics.restype=ctypes.c_int
        self.user32.mouse_event.argtypes=[wintypes.DWORD,wintypes.DWORD,wintypes.DWORD,wintypes.DWORD,ctypes.c_size_t]

    def move(self, dx, dy):
        p=self.point_type()
        if not self.user32.GetCursorPos(ctypes.byref(p)):raise OSError('Cannot read pointer position')
        x=self.user32.GetSystemMetrics(76);y=self.user32.GetSystemMetrics(77)
        width=self.user32.GetSystemMetrics(78);height=self.user32.GetSystemMetrics(79)
        if width<=0 or height<=0:raise OSError('Cannot determine desktop bounds')
        target_x=max(x,min(x+width-1,p.x+dx));target_y=max(y,min(y+height-1,p.y+dy))
        if not self.user32.SetCursorPos(target_x,target_y):raise OSError('Cannot move pointer')

    def click(self, button):
        down,up=(2,4) if button=='left' else (8,16)
        self.user32.mouse_event(down,0,0,0,0)
        self.user32.mouse_event(up,0,0,0,0)


class RemoteMouse:
    def __init__(self,enabled=False,backend=None):
        self.enabled=bool(enabled and (os.name=='nt' or backend is not None))
        self.code=f'{secrets.randbelow(100000000):08d}' if self.enabled else ''
        self.backend=backend
        self.lock=threading.Lock()
        self.failures={}

    def authorize(self,peer,code):
        now=time.monotonic()
        with self.lock:
            self.failures={k:[t for t in v if now-t<60] for k,v in self.failures.items()}
            self.failures={k:v for k,v in self.failures.items() if v}
            failed=self.failures.get(peer,[])
            if len(failed)>=5:return False,'Too many attempts; wait a minute.'
            valid=isinstance(code,str) and secrets.compare_digest(code,self.code)
            if not valid:
                if peer not in self.failures and len(self.failures)>=256:return False,'Too many clients; try again later.'
                self.failures.setdefault(peer,[]).append(now)
                return False,'Invalid pairing code.'
            self.failures.pop(peer,None)
            return True,''

    def dispatch(self,payload):
        if not isinstance(payload,dict):raise ValueError('Invalid request.')
        if payload.get('action')=='move' and set(payload)=={'action','dx','dy'}:
            dx,dy=payload['dx'],payload['dy']
            if type(dx) is not int or type(dy) is not int or abs(dx)>150 or abs(dy)>150:raise ValueError('Invalid pointer movement.')
            with self.lock:
                if self.backend is None:self.backend=WindowsPointer()
                self.backend.move(dx,dy)
        elif payload.get('action')=='click' and set(payload)=={'action','button'} and payload['button'] in ('left','right'):
            with self.lock:
                if self.backend is None:self.backend=WindowsPointer()
                self.backend.click(payload['button'])
        else:raise ValueError('Invalid pointer action.')


def handle(handler,owner,path):
    if path not in ('/remote-mouse','/api/paf-mouse/pair','/api/paf-mouse/control'):return False
    if path=='/remote-mouse' and handler.command in ('GET','HEAD'):
        handler._send(200,PAGE.encode('utf8'),'text/html; charset=utf-8');return True
    if handler.command!='POST' or path=='/remote-mouse':
        handler._json(405,{'error':'Method not allowed.'});return True
    mouse=owner.remote_mouse
    if not mouse.enabled:
        handler.close_connection=True;handler._json(403,{'error':'Mouse control is off. Start PAFPlayer on the host with --remote-mouse.'});return True
    host=handler.headers.get('Host','')
    origin=handler.headers.get('Origin','')
    parsed=urlsplit(origin)
    if parsed.scheme not in ('http','https') or not host or parsed.netloc.casefold()!=host.casefold() or handler.headers.get('Sec-Fetch-Site')=='cross-site':
        handler.close_connection=True;handler._json(403,{'error':'Cross-site request rejected.'});return True
    try:
        length=int(handler.headers.get('Content-Length','0'))
        if length<2 or length>512 or handler.headers.get('Content-Type','').split(';',1)[0].strip().casefold()!='application/json':raise ValueError('Invalid request.')
        raw=handler.rfile.read(length)
        if len(raw)!=length:raise ValueError('Incomplete request.')
        payload=json.loads(raw)
    except (TypeError,ValueError,UnicodeError):
        handler.close_connection=True;handler._json(400,{'error':'Invalid request.'});return True
    ok,message=mouse.authorize(handler.client_address[0],handler.headers.get('X-PAF-Mouse-Code',''))
    if not ok:
        handler._json(403,{'error':message});return True
    if path.endswith('/pair'):
        if payload!={}:handler._json(400,{'error':'Invalid request.'});return True
        handler._json(200,{'accepted':True});return True
    try:
        mouse.dispatch(payload)
    except (ValueError,OSError):
        handler._json(400,{'error':'Unable to perform that pointer action.'});return True
    handler._json(200,{'accepted':True});return True
