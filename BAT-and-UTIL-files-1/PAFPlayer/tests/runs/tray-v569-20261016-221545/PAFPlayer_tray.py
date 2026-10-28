"""Windows notification-area control owned by the verified PAFPlayer instance."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
import threading
import time
import webbrowser

CLICK_WINDOW_SECONDS = 0.50
TRAY_ICON_MENU_BASE = 1100
TRAY_ICON_TYPES = (
    ('play', 'Play'), ('bars', 'Spectrum'), ('disc', 'Disc'), ('wave', 'Wave'),
    ('note', 'Music note'), ('pause', 'Pause'), ('stop', 'Stop'), ('heart', 'Heart'),
    ('star', 'Star'), ('bolt', 'Lightning'), ('headphones', 'Headphones'),
    ('mic', 'Microphone'), ('speaker', 'Speaker'), ('equalizer', 'Equalizer'),
    ('vinyl', 'Vinyl'), ('diamond', 'Diamond'), ('pentagram', 'Pentagram'),
    ('shuffle', 'Shuffle'), ('repeat', 'Repeat'), ('music', 'Beamed notes'),
)
TRAY_ICON_COLORS = (
    ('violet', 'Violet', '#6d28d9', '#ffffff'), ('blue', 'Blue', '#2563eb', '#ffffff'),
    ('cyan', 'Cyan', '#0891b2', '#ecfeff'), ('green', 'Green', '#059669', '#ecfdf5'),
    ('rose', 'Rose', '#e11d48', '#fff1f2'), ('amber', 'Amber', '#d97706', '#fffbeb'),
    ('lime', 'Lime', '#4d7c0f', '#f7fee7'), ('indigo', 'Indigo', '#4338ca', '#eef2ff'),
    ('pink', 'Pink', '#be185d', '#fdf2f8'), ('mono', 'Monochrome', '#27272a', '#fafafa'),
)
TRAY_ICON_STYLES = tuple(
    (color_key + '-' + type_key, color_label + ' ' + type_label, background, foreground, type_key)
    for type_key, type_label in TRAY_ICON_TYPES
    for color_key, color_label, background, foreground in TRAY_ICON_COLORS
)
TRAY_ICON_CATALOG = tuple(
    {'id': index, 'key': key, 'label': label, 'background': background,
     'foreground': foreground, 'motif': motif}
    for index, (key, label, background, foreground, motif) in enumerate(TRAY_ICON_STYLES)
)


def icon_style(value):
    try: return max(0, min(len(TRAY_ICON_STYLES) - 1, int(value)))
    except (TypeError, ValueError): return 0


def icon_catalog():
    return TRAY_ICON_CATALOG


def tray_icon_pixels(style, size=32):
    """Return bottom-up BGRA pixels and a 1-bit transparency mask for CreateIcon."""
    _key, _label, background, foreground, motif = TRAY_ICON_STYLES[icon_style(style)]
    def rgb(value): return tuple(int(value[i:i + 2], 16) for i in (1, 3, 5))
    bg, fg = rgb(background), rgb(foreground)
    pixels = [[(0, 0, 0, 0) for _x in range(size)] for _y in range(size)]
    center, radius = (size - 1) / 2, size * .46
    for y in range(size):
        for x in range(size):
            if (x - center) ** 2 + (y - center) ** 2 <= radius ** 2:
                pixels[y][x] = (*bg, 255)
    def put(x, y, color=fg):
        if 0 <= x < size and 0 <= y < size: pixels[y][x] = (*color, 255)
    if motif == 'play':
        for x in range(11, 24):
            half = max(0, 7 - abs(x - 16))
            for y in range(16 - half, 17 + half): put(x, y)
    elif motif == 'bars':
        for x, height in ((8, 9), (13, 17), (18, 13), (23, 21)):
            for xx in range(x, x + 3):
                for y in range(26 - height, 26): put(xx, y)
    elif motif == 'disc':
        for y in range(7, 25):
            for x in range(7, 25):
                distance = (x - center) ** 2 + (y - center) ** 2
                if 25 <= distance <= 78: put(x, y)
        for y in range(14, 18):
            for x in range(14, 18): put(x, y)
    elif motif == 'wave':
        heights = (4, 8, 13, 18, 12, 7, 4)
        for index, height in enumerate(heights):
            x = 7 + index * 3
            for y in range(16 - height // 2, 17 + height // 2): put(x, y)
    elif motif == 'note':
        for x in range(17, 20):
            for y in range(8, 23): put(x, y)
        for x in range(18, 25):
            for y in range(8, 11): put(x, y)
        for cx, cy in ((13, 23), (20, 21)):
            for y in range(cy - 3, cy + 3):
                for x in range(cx - 4, cx + 3):
                    if ((x - cx) / 4) ** 2 + ((y - cy) / 3) ** 2 <= 1: put(x, y)
    elif motif == 'pause':
        for x in tuple(range(10, 14)) + tuple(range(19, 23)):
            for y in range(9, 24): put(x, y)
    elif motif == 'stop':
        for x in range(10, 23):
            for y in range(10, 23): put(x, y)
    elif motif in ('heart', 'diamond', 'bolt', 'star'):
        shapes = {
            'heart': ((16,25),(6,15),(9,8),(16,11),(23,8),(26,15)),
            'diamond': ((16,6),(26,16),(16,26),(6,16)),
            'bolt': ((18,5),(8,18),(15,18),(12,27),(25,13),(18,13)),
            'star': ((16,5),(19,12),(27,12),(21,17),(23,25),(16,20),(9,25),(11,17),(5,12),(13,12)),
        }
        points = shapes[motif]
        for y in range(5, 28):
            hits=[]
            for (x1,y1),(x2,y2) in zip(points, points[1:]+points[:1]):
                if (y1 <= y < y2) or (y2 <= y < y1): hits.append(round(x1+(y-y1)*(x2-x1)/(y2-y1)))
            if len(hits)>=2:
                for x in range(min(hits),max(hits)+1): put(x,y)
    elif motif in ('equalizer', 'music'):
        heights = (7,16,11,20,13) if motif == 'equalizer' else (5,17,8,20,6)
        for index,height in enumerate(heights):
            for x in range(7+index*4,10+index*4):
                for y in range(26-height,26): put(x,y)
    elif motif in ('headphones', 'mic', 'speaker'):
        if motif == 'headphones':
            for y in range(8,23):
                for x in range(7,26):
                    d=(x-center)**2+(y-center)**2
                    if 65 <= d <= 100 and y < 17: put(x,y)
            for x in tuple(range(6,11))+tuple(range(22,27)):
                for y in range(16,25): put(x,y)
        elif motif == 'mic':
            for y in range(7,20):
                for x in range(12,21):
                    if (x-center)**2/20+(y-13)**2/48 <= 1: put(x,y)
            for x in range(9,24): put(x,20)
            for y in range(18,25): put(16,y)
            for x in range(12,21): put(x,25)
        else:
            for x in range(7,12):
                for y in range(12,21): put(x,y)
            for y in range(8,25):
                edge=round(12+abs(y-16)*.55)
                for x in range(12,23-edge+12): put(x,y)
    elif motif == 'vinyl':
        for y in range(5, 28):
            for x in range(5, 28):
                distance = (x - center) ** 2 + (y - center) ** 2
                if distance <= 118 and (distance >= 12 or distance <= 3): put(x, y)
    else:
        # Compact line symbols for pentagram, shuffle and repeat.
        if motif == 'pentagram':
            points=((16,5),(23,26),(5,12),(27,12),(9,26),(16,5))
        elif motif == 'shuffle':
            points=((6,10),(11,10),(22,22),(27,22),(23,18),(27,22),(23,26),(27,22),(22,10),(11,22),(6,22))
        else:
            points=((7,12),(23,12),(20,9),(24,12),(20,15),(24,20),(8,20),(11,17))
        for (x1,y1),(x2,y2) in zip(points,points[1:]):
            steps=max(abs(x2-x1),abs(y2-y1),1)
            for step in range(steps+1): put(round(x1+(x2-x1)*step/steps),round(y1+(y2-y1)*step/steps))
    xor = bytearray(); mask = bytearray()
    for row in reversed(pixels):
        bits = 0
        for x, (red, green, blue, alpha) in enumerate(row):
            xor.extend((blue, green, red, alpha))
            if not alpha: bits |= 1 << (7 - (x % 8))
            if x % 8 == 7: mask.append(bits); bits = 0
    return bytes(xor), bytes(mask)


def create_tray_icon(style, size=32):
    if os.name != 'nt': return None
    xor, mask = tray_icon_pixels(style, size)
    user32, kernel32 = ctypes.windll.user32, ctypes.windll.kernel32
    user32.CreateIcon.argtypes = [wintypes.HINSTANCE, ctypes.c_int, ctypes.c_int,
                                  ctypes.c_byte, ctypes.c_byte, ctypes.c_void_p, ctypes.c_void_p]
    user32.CreateIcon.restype = wintypes.HICON
    return user32.CreateIcon(kernel32.GetModuleHandleW(None), size, size, 1, 32,
                             ctypes.create_string_buffer(mask), ctypes.create_string_buffer(xor))


def create_menu_bitmap(style, size=32):
    """Create a correctly oriented BGRA bitmap for a native menu item."""
    if os.name != 'nt': return None
    xor, _mask = tray_icon_pixels(style, size)
    gdi32 = ctypes.windll.gdi32
    gdi32.CreateBitmap.argtypes = [ctypes.c_int, ctypes.c_int, wintypes.UINT,
                                   wintypes.UINT, ctypes.c_void_p]
    gdi32.CreateBitmap.restype = wintypes.HBITMAP
    return gdi32.CreateBitmap(size, size, 1, 32, ctypes.create_string_buffer(xor))


def parse_options(arguments):
    """Remove session-only tray/instance switches before the playback parser."""
    remaining, override, explicit = [], None, False
    for argument in arguments:
        if argument == '--tray': override = True
        elif argument == '--no-tray': override = False
        elif argument == '--instance': explicit = True
        else: remaining.append(argument)
    return remaining, override, explicit


def enabled(saved, override=None):
    return bool(saved.get('TrayIconEnabled', 1)) if override is None else override


def configure(runtime, payload):
    if not payload or not set(payload) <= {'enabled', 'icon_style', 'full_info_tooltip'}:
        raise ValueError('Expected tray enabled, icon_style, and/or full_info_tooltip values')
    changes = {}
    if 'enabled' in payload:
        if type(payload['enabled']) is not bool: raise ValueError('Expected a tray enabled checkbox value')
        changes['TrayIconEnabled'] = int(payload['enabled'])
    if 'icon_style' in payload:
        if type(payload['icon_style']) is not int or not 0 <= payload['icon_style'] < len(TRAY_ICON_STYLES):
            raise ValueError('Unknown tray icon style')
        changes['TrayIconStyle'] = payload['icon_style']
    if 'full_info_tooltip' in payload:
        if type(payload['full_info_tooltip']) is not bool:
            raise ValueError('Expected a full-info tooltip checkbox value')
        changes['TrayFullInfoTooltip'] = int(payload['full_info_tooltip'])
    runtime.app.save_player_settings(changes)
    if getattr(runtime, 'tray', None): runtime.tray.refresh()
    if getattr(runtime, 'tray', None): return runtime.tray.status()
    saved = runtime.app.load_player_settings()
    return {'enabled': enabled(saved), 'saved_enabled': enabled(saved), 'override': None,
            'owner': 'another instance', 'visible': False, 'instance': 'additional',
            'icon_style': icon_style(saved.get('TrayIconStyle', 0)), 'icon_styles': icon_catalog()}


HTML = '''
<div class="group" id="trayIconSection"><h3>Windows tray icon</h3>
<p>One icon follows the official PAFPlayer instance. Triple-left-click: previous track. Triple-right-click: next track. Double-click either button: Play/Pause after the click window. A single right-click opens the menu after the click window.</p>
<label><input id="trayIconEnabled" type="checkbox" disabled> Enable tray icon by default</label>
<p><strong>Tray icon:</strong></p><div id="trayIconGallery" class="tray-icon-gallery" role="radiogroup" aria-label="Tray icon"></div>
<style>.tray-icon-gallery{display:grid;grid-template-columns:repeat(auto-fill,minmax(132px,1fr));gap:.45rem}.tray-icon-choice{display:flex;align-items:center;gap:.45rem;text-align:left;padding:.4rem;border:1px solid #666;border-radius:.45rem;background:transparent;color:inherit}.tray-icon-choice[aria-checked="true"]{outline:2px solid #8b5cf6;border-color:transparent}.tray-icon-choice canvas{width:28px;height:28px;image-rendering:auto}</style>
<p id="trayIconStatus" role="status">Loading tray status…</p></div>
'''
SCRIPT = r'''
<script>(()=>{
 const box=document.getElementById('trayIconEnabled'),gallery=document.getElementById('trayIconGallery'),status=document.getElementById('trayIconStatus');let token='',busy=false,current=-1,catalogSignature='',iconButtons=new Map();
 function draw(canvas,item){const c=canvas.getContext('2d'),s=32;c.clearRect(0,0,s,s);c.fillStyle=item.background;c.beginPath();c.arc(16,16,15,0,Math.PI*2);c.fill();c.fillStyle=item.foreground;if(item.motif==='play'){c.beginPath();c.moveTo(11,8);c.lineTo(25,16);c.lineTo(11,24);c.closePath();c.fill()}else if(item.motif==='bars'){[9,17,13,21].forEach((h,i)=>c.fillRect(7+i*6,27-h,3,h))}else if(item.motif==='disc'){c.lineWidth=5;c.strokeStyle=item.foreground;c.beginPath();c.arc(16,16,8,0,Math.PI*2);c.stroke();c.beginPath();c.arc(16,16,2,0,Math.PI*2);c.fill()}else if(item.motif==='wave'){[4,8,13,18,12,7,4].forEach((h,i)=>c.fillRect(6+i*3,16-h/2,2,h))}else if(item.motif==='note'){c.fillRect(17,7,3,16);c.fillRect(19,7,7,3);c.beginPath();c.ellipse(14,23,5,3,0,0,Math.PI*2);c.fill();c.beginPath();c.ellipse(21,21,5,3,0,0,Math.PI*2);c.fill()}else{const symbols={pause:'Ⅱ',stop:'■',heart:'♥',star:'★',bolt:'ϟ',headphones:'Ω',mic:'●',speaker:'◀',equalizer:'▥',vinyl:'◎',diamond:'◆',pentagram:'☆',shuffle:'⤨',repeat:'↻',music:'♫'};c.font='bold 21px Segoe UI Symbol';c.textAlign='center';c.textBaseline='middle';c.fillText(symbols[item.motif]||'♪',16,17)}}
 async function save(change){busy=true;try{const r=await fetch('/api/workflows/tray',{method:'POST',headers:{'Content-Type':'application/json','X-PAF-Workflow-Token':token},body:JSON.stringify(change)}),v=await r.json();if(!r.ok)throw Error(v.error);show(v);status.textContent='Setting saved · '+status.textContent}catch(e){status.textContent=String(e)}finally{busy=false}}
 function show(v){box.checked=!!v.saved_enabled;box.disabled=false;const previous=current;current=v.icon_style,items=v.icon_styles||[],signature=items.map(x=>x.id+':'+x.label+':'+x.background+':'+x.foreground).join('|');if(signature!==catalogSignature){catalogSignature=signature;iconButtons=new Map();const fragment=document.createDocumentFragment();items.forEach(item=>{const b=document.createElement('button'),c=document.createElement('canvas'),t=document.createElement('span');b.type='button';b.className='tray-icon-choice';b.setAttribute('role','radio');b.title='Use '+item.label+' tray icon';c.width=c.height=32;draw(c,item);t.textContent=item.label;b.append(c,t);b.onclick=()=>save({icon_style:item.id});iconButtons.set(item.id,b);fragment.append(b)});gallery.replaceChildren(fragment)}if(previous!==current||signature!==catalogSignature)for(const [id,b] of iconButtons)b.setAttribute('aria-checked',String(id===current));else{const old=iconButtons.get(previous),now=iconButtons.get(current);if(old)old.setAttribute('aria-checked','false');if(now)now.setAttribute('aria-checked','true')}status.textContent=v.override===null?'Tray preference loaded':'Command-line override active for this run'}
 async function poll(){if(busy)return;try{const r=await fetch('/api/workflows/status',{cache:'no-store'}),v=await r.json();if(!r.ok)throw Error(v.error);if(v.local)token=v.token;show(v.tray);if(!v.local)box.disabled=true}catch(e){status.textContent=String(e)}}
 box.onchange=()=>save({enabled:box.checked});
 poll();setInterval(()=>{if(!document.hidden)poll()},3000);
})();</script>
'''

CONTROL_HTML = '''
<div class="group" id="controlSection"><h3>⌨️ Global hotkeys</h3>
<label><input id="controlHotkeysEnabled" type="checkbox" disabled> Enable Windows control hotkeys on this player</label>
<p>Ctrl+Alt+Up/Down adjusts volume; Ctrl+Alt+A brings album art forward; Ctrl+Alt+F controls floating lyrics; Win+C pauses or resumes. Media keys work while another window is active. On tray-only computers, these keys relay actions to this player; Ctrl+Shift+Alt+F/A instead toggle lyrics/art windows on that computer.</p>
<p id="controlHotkeysStatus" role="status">Loading control setting…</p></div>
'''
CONTROL_SCRIPT = r'''
<script>(()=>{const box=document.getElementById('controlHotkeysEnabled'),status=document.getElementById('controlHotkeysStatus');let token='',busy=false;
async function poll(){if(busy)return;try{const r=await fetch('/api/workflows/status',{cache:'no-store'}),v=await r.json();if(!r.ok)throw Error(v.error);token=v.local?v.token:'';box.checked=!!v.control.hotkeys_enabled;box.disabled=!v.local;status.textContent=v.local?'Current player state':'Change this on the player computer'}catch(e){status.textContent=String(e)}}
box.onchange=async()=>{if(!box.checked&&!confirm('Turn off PAFPlayer global hotkeys? Keyboard controls outside the player will stop working.')){box.checked=true;return}busy=true;try{const r=await fetch('/api/workflows/control',{method:'POST',headers:{'Content-Type':'application/json','X-PAF-Workflow-Token':token},body:JSON.stringify({hotkeys_enabled:box.checked})}),v=await r.json();if(!r.ok)throw Error(v.error);box.checked=!!v.hotkeys_enabled;status.textContent='Setting saved'}catch(e){status.textContent=String(e);await poll()}finally{busy=false}};poll();setInterval(()=>{if(!document.hidden)poll()},3000)})();</script>
'''

def augment(page):
    return page.replace('<div class="group section-global-config" id="globalConfigSection">',
                        HTML + CONTROL_HTML + '<div class="group section-global-config" id="globalConfigSection">', 1).replace('</body>', SCRIPT + CONTROL_SCRIPT + '</body>', 1)


class ClickSequence:
    """Count button releases; Windows double-click messages are deliberately ignored."""
    def __init__(self, window=CLICK_WINDOW_SECONDS):
        self.window = window
        self.button = None
        self.count = 0
        self.last = 0.0

    def click(self, button, now):
        if button != self.button or now - self.last > self.window:
            self.button, self.count = button, 0
        self.count += 1
        self.last = now
        if self.count == 3:
            self.button, self.count = None, 0
            return 'previous' if button == 'left' else 'next'
        return None

    def expire(self, now):
        if self.button is None or now - self.last + 1e-9 < self.window:
            return None
        action = 'pause' if self.count == 2 else 'menu' if self.button == 'right' and self.count == 1 else None
        self.button, self.count = None, 0
        return action


class TrayController:
    WM_TRAY = 0x8000 + 41
    WM_SYNC = 0x8000 + 42
    WM_TIMER = 0x0113
    WM_CLOSE = 0x0010
    WM_DESTROY = 0x0002
    WM_LBUTTONUP = 0x0202
    WM_RBUTTONUP = 0x0205
    WM_MOUSEMOVE = 0x0200
    NIM_ADD, NIM_MODIFY, NIM_DELETE = 0, 1, 2
    NIF_MESSAGE, NIF_ICON, NIF_TIP = 1, 2, 4

    def __init__(self, runtime, instance, override=None, *, click_window=CLICK_WINDOW_SECONDS):
        self.runtime, self.instance, self.override = runtime, instance, override
        if os.name == 'nt' and click_window == CLICK_WINDOW_SECONDS:
            click_window = max(.35, min(.9, ctypes.windll.user32.GetDoubleClickTime() / 1000))
        self.clicks = ClickSequence(click_window)
        self._lock = threading.RLock()
        self._thread = None
        self._hwnd = None
        self._visible = False
        self._closing = False
        self._ready = threading.Event()
        self._taskbar_created = 0
        self._machine = None
        self._hover = None
        self._lyric_bubble = None
        self._hover_art_key = None
        self._requested_icon_style = None
        self._icon_applied = threading.Event()
        self._last_tray_lyric = ''
        self._settings_cache = {}
        self._settings_cache_at = 0.0
        self._last_hover_request_at = 0.0

    def _sync_lyric_bubble(self, lyric):
        """Contain optional popup failures; never rethrow into the Win32 callback."""
        if not self._lyric_bubble:
            return
        lyric = lyric if self._visible else ''
        if lyric == self._last_tray_lyric:
            return
        # Mark attempted content before calling native code. A paused lyric must
        # not repeatedly fail/log every timer tick; a changed line can try again.
        self._last_tray_lyric = lyric
        try:
            if lyric:
                self._lyric_bubble.show(lyric)
            else:
                self._lyric_bubble.hide()
        except Exception as exc:
            self._log('tray.hover.error', operation='lyric',
                      reason=type(exc).__name__, message=str(exc)[:240])

    def _log(self, event, **fields):
        """Tray callbacks must never throw merely because a small client runtime has no logger."""
        logger = getattr(self.runtime, 'log', None)
        if callable(logger):
            try:
                logger(event, **fields)
            except Exception:
                pass

    def attach_machine_options(self, *, remote=False, settings=None):
        if self._machine is None:
            from PAFPlayer_tray_machine import TrayMachineEffects
            self._machine = TrayMachineEffects(self.runtime.server, self.instance, self.refresh,
                                               remote=remote, settings=settings)
        return self._machine

    def wants_icon(self):
        # The registry is the existing global player setting store. A CLI
        # override never writes to it and remains effective for this run.
        return enabled(self._player_settings(), self.override)

    def _player_settings(self):
        """Coalesce registry reads made by one tray status/sync cycle."""
        now = time.monotonic()
        with self._lock:
            if self._settings_cache and now - self._settings_cache_at < 0.5:
                return self._settings_cache
        loader = getattr(self.runtime.app, 'load_player_settings', None)
        loaded = dict(loader() if loader else {})
        with self._lock:
            self._settings_cache = loaded
            self._settings_cache_at = now
        return loaded

    def _invalidate_settings_cache(self):
        with self._lock:
            self._settings_cache = {}
            self._settings_cache_at = 0.0

    def selected_icon_style(self):
        with self._lock:
            requested = self._requested_icon_style
        if requested is not None:
            return requested
        return icon_style(self._player_settings().get('TrayIconStyle', 0))

    def full_info_tooltip_enabled(self):
        return bool(self._player_settings().get('TrayFullInfoTooltip', 0))

    def set_full_info_tooltip(self, enabled_value):
        self.runtime.app.save_player_settings({'TrayFullInfoTooltip': int(bool(enabled_value))})
        self._invalidate_settings_cache()
        if not enabled_value and self._hover:
            self._hover.hide()
        self.refresh()
        return True

    def set_icon_style(self, value):
        value = icon_style(value)
        self.runtime.app.save_player_settings({'TrayIconStyle': value})
        self._invalidate_settings_cache()
        with self._lock:
            self._requested_icon_style = value
            self._icon_applied.clear()
        self.refresh()
        # Web Config calls arrive off the tray thread, so wait briefly until the
        # shell has accepted the replacement before reporting success.
        if threading.current_thread() is not self._thread:
            self._icon_applied.wait(1.5)
        return True

    def status(self):
        with self._lock:
            return {'enabled': self.wants_icon(), 'saved_enabled': enabled(self._player_settings()),
                    'icon_style': self.selected_icon_style(), 'icon_styles': icon_catalog(),
                    'override': self.override, 'owner': 'official' if self.instance.owns() else 'another instance',
                    'visible': self._visible, 'instance': 'official' if self.instance.owns() else 'additional'}

    def start(self):
        if os.name != 'nt' or not self.instance.owns(): return False
        with self._lock:
            if self._closing: return False
            if self._thread and self._thread.is_alive():
                self.refresh()
                return True
            self._ready.clear()
            self._thread = threading.Thread(target=self._run, name='paf-tray', daemon=True)
            self._thread.start()
        self._ready.wait(2)
        if self._hwnd and self._machine:
            self._machine.start()
        return bool(self._hwnd)

    def refresh(self):
        self._invalidate_settings_cache()
        if self._hwnd and os.name == 'nt':
            ctypes.windll.user32.PostMessageW(self._hwnd, self.WM_SYNC, 0, 0)

    def close(self):
        with self._lock:
            self._closing = True
            hwnd, thread = self._hwnd, self._thread
        if hwnd and os.name == 'nt': ctypes.windll.user32.PostMessageW(hwnd, self.WM_CLOSE, 0, 0)
        if thread and thread is not threading.current_thread(): thread.join(timeout=3)
        if self._machine:
            self._machine.close()

    def dispatch(self, action):
        """Every action is local to the mutex owner and its own playback queue."""
        if not self.instance.owns() or self._closing: return False
        if action.startswith('machine_') and self._machine:
            return self._machine.toggle(action.removeprefix('machine_'))
        if action.startswith('icon_style_'):
            try: return self.set_icon_style(int(action.removeprefix('icon_style_')))
            except ValueError: return False
        if action == 'full_info_tooltip':
            return self.set_full_info_tooltip(not self.full_info_tooltip_enabled())
        server = self.runtime.server
        if action in ('previous', 'next', 'pause'):
            if not server: return False
            mapping = {'previous': self.runtime.app.PREVIOUS_FILE,
                       'next': self.runtime.app.NEXT_FILE,
                       'pause': self.runtime.app.PAUSE_TOGGLE}
            return server.enqueue_action(mapping[action])
        if action == 'exit':
            if not server: return False
            server.enqueue_tray_exit()
            return True
        if action == 'web':
            if server and server.enabled and server._httpd:
                webbrowser.open(server.url)
                return True
            self._message('Web configuration is disabled for this run.')
            return False
        if action == 'details':
            if server and server.enabled and server._httpd:
                from PAFPlayer_remote_tray import launch_viewer
                launch_viewer(server.url)
                return True
            self._message('The tag viewer requires the web server to be enabled for this run.')
            return False
        if action == 'folder':
            path = server.current_audio() if server else None
            if path and path.parent.is_dir():
                os.startfile(str(path.parent))
                return True
            return False
        if action == 'about':
            message = 'PAFPlayer ' + self.runtime.app.PROGRAM_VERSION + '\nOfficial instance (PID ' + str(os.getpid()) + ')'
            if self._machine and self._machine.last_error:
                message += '\nDesktop option: ' + self._machine.last_error
            self._message(message)
            return True
        return False

    def tooltip_text(self):
        return 'PAFPlayer ' + self.runtime.app.PROGRAM_VERSION + ' · official PID ' + str(os.getpid())

    def menu_items(self, state):
        label = 'Play' if state.get('paused') else 'Pause'
        folder = bool(self.runtime.server and self.runtime.server.current_audio())
        return [(1, label, 'pause', True), (2, 'Previous track', 'previous', True),
                (3, 'Next track', 'next', True), (4, 'Open web configuration', 'web', True),
                (5, 'Open tag viewer', 'details', True),
                (6, ('✓ ' if self.full_info_tooltip_enabled() else '○ ') + 'Full info on tooltip', 'full_info_tooltip', True),
                (7, ('✓ ' if self._machine and self._machine.options['lyrics_tooltip'] else '○ ') + 'Show sung lyrics above tray', 'machine_lyrics_tooltip', True),
                (8, ('✓ ' if self._machine and self._machine.options['album_wallpaper'] else '○ ') + 'Album art desktop wallpaper', 'machine_album_wallpaper', True),
                (9, 'Open current track folder', 'folder', folder),
                (10, 'About / version', 'about', True), (11, 'Exit PAFPlayer', 'exit', True)]

    def poll_hotkeys(self):
        """Tray-only overrides this without blocking the Win32 message pump."""
        return None

    def _refresh_hover_art(self, state):
        if not self._hover: return
        key = (getattr(self.runtime.server, 'owner_identity', ''),
               state.get('art_generation'), state.get('art_count'))
        if key == self._hover_art_key: return
        self._hover_art_key = key
        self._hover.set_bitmap(None)
        if not state.get('art_count'): return
        def fetch():
            try:
                server = self.runtime.server
                if hasattr(server, 'wallpaper'):
                    data = server.wallpaper(int(state['art_generation']), 320, 240)
                else:
                    from PAFPlayer_track_details import wallpaper_bitmap
                    art, _mime = server.art_snapshot_at_generation(int(state['art_generation']), 0)
                    data = wallpaper_bitmap(art, 320, 240) if art else None
                if self._hover_art_key == key and self._hover:
                    self._hover.set_bitmap(data)
            except (OSError, ValueError, TypeError): pass
        threading.Thread(target=fetch, name='paf-tray-hover-art', daemon=True).start()

    def _message(self, text):
        if os.name == 'nt':
            user32 = ctypes.windll.user32
            user32.MessageBoxW.argtypes = [wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.UINT]
            user32.MessageBoxW(self._hwnd, text, 'PAFPlayer', 0)

    def _run(self):
        user32, shell32, kernel32 = ctypes.windll.user32, ctypes.windll.shell32, ctypes.windll.kernel32
        LRESULT = ctypes.c_ssize_t
        WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)

        class WNDCLASSW(ctypes.Structure):
            _fields_ = [('style', wintypes.UINT), ('lpfnWndProc', WNDPROC), ('cbClsExtra', ctypes.c_int),
                        ('cbWndExtra', ctypes.c_int), ('hInstance', wintypes.HINSTANCE), ('hIcon', wintypes.HICON),
                        ('hCursor', wintypes.HANDLE), ('hbrBackground', wintypes.HANDLE),
                        ('lpszMenuName', wintypes.LPCWSTR), ('lpszClassName', wintypes.LPCWSTR)]

        class NOTIFYICONDATAW(ctypes.Structure):
            _fields_ = [('cbSize', wintypes.DWORD), ('hWnd', wintypes.HWND), ('uID', wintypes.UINT),
                        ('uFlags', wintypes.UINT), ('uCallbackMessage', wintypes.UINT), ('hIcon', wintypes.HICON),
                        ('szTip', wintypes.WCHAR * 128), ('dwState', wintypes.DWORD), ('dwStateMask', wintypes.DWORD),
                        ('szInfo', wintypes.WCHAR * 256), ('uTimeoutOrVersion', wintypes.UINT),
                        ('szInfoTitle', wintypes.WCHAR * 64), ('dwInfoFlags', wintypes.DWORD),
                        ('guidItem', ctypes.c_byte * 16), ('hBalloonIcon', wintypes.HICON)]

        shell32.Shell_NotifyIconW.argtypes = [wintypes.DWORD, ctypes.POINTER(NOTIFYICONDATAW)]
        shell32.Shell_NotifyIconW.restype = wintypes.BOOL
        kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
        kernel32.GetModuleHandleW.restype = wintypes.HINSTANCE
        user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        user32.LoadIconW.argtypes = [wintypes.HINSTANCE, wintypes.LPCWSTR]
        user32.DefWindowProcW.restype = LRESULT
        user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
        user32.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR,
                                           wintypes.DWORD, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                           wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, ctypes.c_void_p]
        user32.CreateWindowExW.restype = wintypes.HWND
        user32.LoadIconW.restype = wintypes.HICON
        user32.AppendMenuW.argtypes = [wintypes.HMENU, wintypes.UINT, ctypes.c_size_t, wintypes.LPCWSTR]
        user32.SetForegroundWindow.argtypes = [wintypes.HWND]
        user32.RegisterWindowMessageW.argtypes = [wintypes.LPCWSTR]
        user32.GetCursorPos.argtypes = [ctypes.POINTER(wintypes.POINT)]
        user32.SetTimer.argtypes = [wintypes.HWND, ctypes.c_size_t, wintypes.UINT, ctypes.c_void_p]
        user32.KillTimer.argtypes = [wintypes.HWND, ctypes.c_size_t]
        user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
        user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
        user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
        user32.TrackPopupMenuEx.argtypes = [wintypes.HMENU, wintypes.UINT, ctypes.c_int, ctypes.c_int,
                                            wintypes.HWND, ctypes.c_void_p]
        user32.DestroyMenu.argtypes = [wintypes.HMENU]
        user32.DestroyWindow.argtypes = [wintypes.HWND]
        user32.CreatePopupMenu.restype = wintypes.HMENU
        user32.TrackPopupMenuEx.restype = wintypes.UINT
        selected_style = self.selected_icon_style()
        icon = create_tray_icon(selected_style)
        icon_owned = bool(icon)
        if not icon:
            icon = user32.LoadIconW(None, ctypes.cast(ctypes.c_void_p(32516), wintypes.LPCWSTR))  # fallback
        name = 'PAFPlayerTray-' + str(os.getpid())
        notify = NOTIFYICONDATAW()
        notify.cbSize = ctypes.sizeof(notify)
        notify.uID = 1
        notify.uFlags = self.NIF_MESSAGE | self.NIF_ICON | self.NIF_TIP
        notify.uCallbackMessage = self.WM_TRAY
        notify.hIcon = icon
        notify.szTip = self.tooltip_text()[:127]
        self._taskbar_created = user32.RegisterWindowMessageW('TaskbarCreated')

        last_sync = 0.0
        def sync():
            nonlocal last_sync, icon, icon_owned, selected_style
            last_sync = time.monotonic()
            should_show = self.instance.owns() and not self._closing and self.wants_icon()
            wanted_style = self.selected_icon_style()
            force_icon_refresh = self._requested_icon_style is not None
            if wanted_style != selected_style or force_icon_refresh:
                replacement = create_tray_icon(wanted_style)
                if replacement:
                    old, old_owned = icon, icon_owned
                    icon, icon_owned, selected_style = replacement, True, wanted_style
                    notify.hIcon = icon
                    if self._visible and not shell32.Shell_NotifyIconW(self.NIM_MODIFY, ctypes.byref(notify)):
                        # Explorer can discard a modify while rebuilding its tray.
                        # Re-add this exact icon instead of silently keeping stale art.
                        shell32.Shell_NotifyIconW(self.NIM_DELETE, ctypes.byref(notify))
                        self._visible = bool(shell32.Shell_NotifyIconW(self.NIM_ADD, ctypes.byref(notify)))
                    if old_owned: user32.DestroyIcon(old)
                    with self._lock:
                        self._requested_icon_style = None
                        self._icon_applied.set()
            tip = self.tooltip_text()[:127]
            if notify.szTip != tip:
                notify.szTip = tip
                if self._visible:
                    shell32.Shell_NotifyIconW(self.NIM_MODIFY, ctypes.byref(notify))
            lyric_tooltip = bool(self._machine and self._machine.options['lyrics_tooltip'])
            lyric = self._machine.tooltip_lyric().strip() if lyric_tooltip else ''
            self._sync_lyric_bubble(lyric)
            if should_show and not self._visible:
                self._visible = bool(shell32.Shell_NotifyIconW(self.NIM_ADD, ctypes.byref(notify)))
            elif not should_show and self._visible:
                shell32.Shell_NotifyIconW(self.NIM_DELETE, ctypes.byref(notify))
                self._visible = False
                self._sync_lyric_bubble('')

        def menu():
            if not self.instance.owns() or not self._visible: return
            popup = user32.CreatePopupMenu()
            menu_bitmaps = []
            try:
                state = self.runtime.server.snapshot() if self.runtime.server else {}
                items = self.menu_items(state)
                for number, title, _action, active in items:
                    checked = title.startswith('✓ ')
                    checkable = checked or title.startswith('○ ')
                    flags = (0 if active else 0x0002) | (0x0008 if checked else 0)
                    user32.AppendMenuW(popup, flags, number, title[2:] if checkable else title)
                    if number == 4:
                        chooser = user32.CreatePopupMenu()
                        current = self.selected_icon_style()
                        for type_index, (_type_key, type_label) in enumerate(TRAY_ICON_TYPES):
                            colors = user32.CreatePopupMenu()
                            for color_index, (_color_key, color_label, _background, _foreground) in enumerate(TRAY_ICON_COLORS):
                                index = type_index * len(TRAY_ICON_COLORS) + color_index
                                flags = 0x0008 if index == current else 0
                                user32.AppendMenuW(colors, flags, TRAY_ICON_MENU_BASE + index, color_label)
                            # Rendering 200 GDI previews synchronously made the
                            # tray message pump appear hung before the popup was
                            # shown. One preview per genuine icon type retains a
                            # pictorial chooser; its color submenu stays instant.
                            user32.AppendMenuW(chooser, 0x0010, int(colors), type_label)
                            preview_index = type_index * len(TRAY_ICON_COLORS) + (current % len(TRAY_ICON_COLORS))
                            bitmap = create_menu_bitmap(preview_index)
                            if bitmap:
                                class MENUITEMINFOW(ctypes.Structure):
                                    _fields_ = [('cbSize', wintypes.UINT), ('fMask', wintypes.UINT),
                                                ('fType', wintypes.UINT), ('fState', wintypes.UINT),
                                                ('wID', wintypes.UINT), ('hSubMenu', wintypes.HMENU),
                                                ('hbmpChecked', wintypes.HBITMAP), ('hbmpUnchecked', wintypes.HBITMAP),
                                                ('dwItemData', ctypes.c_size_t), ('dwTypeData', wintypes.LPWSTR),
                                                ('cch', wintypes.UINT), ('hbmpItem', wintypes.HBITMAP)]
                                info = MENUITEMINFOW(); info.cbSize = ctypes.sizeof(info)
                                info.fMask = 0x00000080; info.hbmpItem = bitmap
                                user32.SetMenuItemInfoW(chooser, type_index, True, ctypes.byref(info))
                                menu_bitmaps.append(bitmap)
                        user32.AppendMenuW(popup, 0x0010, int(chooser), 'Choose tray icon')
                position = wintypes.POINT()
                user32.GetCursorPos(ctypes.byref(position))
                user32.SetForegroundWindow(notify.hWnd)
                selected = user32.TrackPopupMenuEx(popup, 0x0100 | 0x0002, position.x, position.y, notify.hWnd, None)
                user32.PostMessageW(notify.hWnd, 0, 0, 0)
                actions = {number: action for number, _title, action, _active in items}
                actions.update({TRAY_ICON_MENU_BASE + index: 'icon_style_' + str(index)
                                for index in range(len(TRAY_ICON_STYLES))})
                if selected in actions: self.dispatch(actions[selected])
            finally:
                user32.DestroyMenu(popup)
                for bitmap in menu_bitmaps:
                    ctypes.windll.gdi32.DeleteObject(bitmap)

        @WNDPROC
        def wndproc(hwnd, message, wparam, lparam):
            if message == self.WM_TRAY:
                # Shell_NotifyIcon may pack the event in LOWORD(lParam) after
                # negotiating newer NOTIFYICON versions.  Comparing the whole
                # pointer-sized value made hover silently stop on those shells.
                event = int(lparam) & 0xFFFF
                if (event == self.WM_MOUSEMOVE and self._visible and self._hover
                        and self.full_info_tooltip_enabled()):
                    try:
                        hover_now = time.monotonic()
                        if hover_now - self._last_hover_request_at >= 0.10:
                            self._last_hover_request_at = hover_now
                            state = self.runtime.server.snapshot() if self.runtime.server else {}
                            self._hover.request(state)
                            self._refresh_hover_art(state)
                    except Exception as exc:
                        self._log('tray.hover.error', operation='mousemove',
                                  reason=type(exc).__name__, message=str(exc)[:240])
                if event in (self.WM_LBUTTONUP, self.WM_RBUTTONUP):
                    if self._hover:
                        try: self._hover.hide()
                        except Exception as exc:
                            self._log('tray.hover.error', operation='hide',
                                      reason=type(exc).__name__, message=str(exc)[:240])
                    action = self.clicks.click('left' if event == self.WM_LBUTTONUP else 'right', time.monotonic())
                    if action: self.dispatch(action)
                return 0
            if message == self.WM_SYNC:
                sync(); return 0
            if message == self.WM_TIMER:
                self.poll_hotkeys()
                if self._hover and self.full_info_tooltip_enabled():
                    try: self._hover.tick()
                    except Exception as exc:
                        self._log('tray.hover.error', operation='timer',
                                  reason=type(exc).__name__, message=str(exc)[:240])
                action = self.clicks.expire(time.monotonic())
                if action == 'menu':
                    try: menu()
                    except Exception as exc:
                        self._log('tray.menu.error', reason=type(exc).__name__, message=str(exc)[:240])
                elif action == 'pause': self.dispatch('pause')
                if time.monotonic() - last_sync >= 2: sync()
                return 0
            if message == self._taskbar_created:
                self._visible = False; sync(); return 0
            if message == self.WM_CLOSE:
                user32.DestroyWindow(hwnd)
                return 0
            if message == self.WM_DESTROY:
                if self._visible: shell32.Shell_NotifyIconW(self.NIM_DELETE, ctypes.byref(notify))
                if self._hover: self._hover.close(); self._hover = None
                if self._lyric_bubble: self._lyric_bubble.close(); self._lyric_bubble = None
                if icon_owned: user32.DestroyIcon(icon)
                self._visible = False
                user32.KillTimer(hwnd, 1)
                user32.PostQuitMessage(0)
                return 0
            return user32.DefWindowProcW(hwnd, message, wparam, lparam)

        klass = WNDCLASSW()
        klass.lpfnWndProc = wndproc
        klass.hInstance = kernel32.GetModuleHandleW(None)
        klass.lpszClassName = name
        if not user32.RegisterClassW(ctypes.byref(klass)):
            self._ready.set(); return
        hwnd = user32.CreateWindowExW(0, name, name, 0, 0, 0, 0, 0, None, None, klass.hInstance, None)
        if not hwnd:
            self._ready.set(); return
        notify.hWnd = hwnd
        self._hwnd = hwnd
        try:
            from PAFPlayer_tray_hover import HoverCard, LyricBubble
            self._hover = HoverCard(hwnd, notify.uID, name)
            self._lyric_bubble = LyricBubble(hwnd, notify.uID, name)
        except Exception as exc:
            self._hover = None
            self._log('tray.hover.error', operation='create',
                      reason=type(exc).__name__, message=str(exc)[:240])
        user32.SetTimer(hwnd, 1, 50, None)
        sync()
        self._ready.set()
        message = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(message))
            user32.DispatchMessageW(ctypes.byref(message))
        self._hwnd = None
