"""Optional visual sidecar bridge. No audio, GUI, image decoding or polling here."""
from __future__ import annotations
import ipaddress
import json
from pathlib import Path
import re
import subprocess
import sys
import threading
import uuid
from urllib.parse import parse_qs, urlsplit

DEFAULTS = {'enabled': False, 'brightness': 50}
MAX_ART_BYTES = 16 * 1024 * 1024


def settings(runtime):
    saved = runtime.settings.get('visual_screensaver', {})
    if not isinstance(saved, dict): saved = {}
    brightness = saved.get('brightness', 50)
    if type(brightness) is not int or not 0 <= brightness <= 100: brightness = 50
    return {'enabled': saved.get('enabled') is True, 'brightness': brightness}


def clean_text(value, limit):
    text = re.sub(r'\x1b\[[0-?]*[ -/]*[@-~]', '', str(value or '')[:limit * 8])
    return ''.join(c for c in text if c in '\n\t' or ord(c) >= 32)[:limit]


class Controller:
    def __init__(self, runtime, owner):
        self.runtime, self.owner = runtime, owner
        self.session = uuid.uuid4().hex
        self.close_revision = 0
        self.process = None
        self.lock = threading.RLock()

    def executable(self):
        local = Path(self.runtime.app.__file__).resolve().with_name('PAFPlayer.scr')
        development = local.parent / 'screensaver/PAFPlayer.scr'
        for candidate in (development, local):
            if candidate.is_file(): return candidate
        return Path('C:/BAT/PAFPlayer.scr')

    def snapshot(self):
        options = settings(self.runtime)
        value = dict(protocol=1, player_version=self.runtime.app.PROGRAM_VERSION, session=self.session, close_revision=self.close_revision,
                     enabled=options['enabled'], brightness=options['brightness'],
                     title='', lyric='', status='Disabled', art_revision='', has_art=False)
        if not options['enabled']: return value
        # Copy only small fields. Never copy a lyric timeline, decode artwork,
        # query the filesystem, or mark the expensive browser spectrum active.
        with self.owner._lock:
            state = self.owner._state
            track = state.get('track') or {}
            tags = state.get('metadata') or {}
            playing = bool(state.get('playing')) and not state.get('transport_stopped')
            paused = bool(state.get('paused')) and not state.get('transport_stopped')
            artist = track.get('artist') or tags.get('Act') or tags.get('Artist') or ''
            title = track.get('title') or tags.get('Song') or tags.get('Title') or track.get('filename') or ''
            lyric = state.get('lyric', '') if state.get('lyric_timeline') else ''
            revision = f'{self.session}-{self.owner._art_worker_generation}-{self.owner._art_generation}'
            art = self.owner._art_variants[0] if self.owner._art_variants else None
        value.update(status='Paused' if paused else 'Playing' if playing else 'Stopped')
        if playing or paused:
            value.update(title=' — '.join(filter(None, (clean_text(artist, 500), clean_text(title, 500)))),
                         lyric=clean_text(lyric, 2000), art_revision=revision,
                         has_art=bool(art and len(art) <= MAX_ART_BYTES))
        return value

    def artwork(self, revision):
        if not settings(self.runtime)['enabled']: return None, 'application/octet-stream'
        with self.owner._lock:
            expected = f'{self.session}-{self.owner._art_worker_generation}-{self.owner._art_generation}'
            if revision != expected or not self.owner._art_variants: return None, 'application/octet-stream'
            data = self.owner._art_variants[0]
            mime = self.owner._art_variant_mimes[0]
        if len(data) > MAX_ART_BYTES: return None, 'application/octet-stream'
        return data, mime

    def configure(self, payload):
        if set(payload) - {'enabled', 'brightness'}: raise ValueError('Unknown screensaver setting')
        options = settings(self.runtime)
        if 'enabled' in payload:
            if type(payload['enabled']) is not bool: raise ValueError('enabled must be a checkbox value')
            options['enabled'] = payload['enabled']
        if 'brightness' in payload:
            if type(payload['brightness']) is not int or not 0 <= payload['brightness'] <= 100:
                raise ValueError('brightness must be an integer from 0 to 100')
            options['brightness'] = payload['brightness']
        with self.runtime.lock:
            old = self.runtime.settings.get('visual_screensaver')
            saved = dict(old) if isinstance(old, dict) else {}
            self.runtime.settings['visual_screensaver'] = dict(saved, **options)
            try: self.runtime.save_settings()
            except Exception:
                if old is None: self.runtime.settings.pop('visual_screensaver', None)
                else: self.runtime.settings['visual_screensaver'] = old
                raise
        if not options['enabled']: self.close()
        return options

    def show(self):
        with self.lock:
            if not settings(self.runtime)['enabled']: raise ValueError('Enable the visual screensaver first')
            if self.process is not None and self.process.poll() is None: return
            executable = self.executable()
            if not executable.is_file(): raise ValueError('PAFPlayer.scr is missing; run build_PAFPlayer_screensaver.py')
            self.process = subprocess.Popen(
                [str(executable), '/s', f'/port:{self.owner.port}', f'/close-revision:{self.close_revision}'],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)
                              | getattr(subprocess, 'BELOW_NORMAL_PRIORITY_CLASS', 0),
            )

    def close(self):
        with self.lock:
            self.close_revision += 1
            # Let the sidecar observe close_revision and exit normally. A forced
            # termination would skip its optional Windows sign-in lock.


def controller(owner):
    runtime = owner.workflows
    with runtime.lock:
        if not hasattr(owner, '_visual_screensaver'):
            owner._visual_screensaver = Controller(runtime, owner)
        return owner._visual_screensaver


def handle(handler, owner, path):
    if not path.startswith('/api/screensaver/'): return False
    try:
        if not ipaddress.ip_address(handler.client_address[0]).is_loopback:
            raise PermissionError('Visual screensaver is local only')
        control = controller(owner)
        operation = path.removeprefix('/api/screensaver/')
        if handler.command in ('GET', 'HEAD'):
            if operation == 'state':
                if settings(owner.workflows)['enabled']: owner.note_screensaver_activity()
                handler._json(200, control.snapshot())
            elif operation == 'art':
                revision = parse_qs(urlsplit(handler.path).query).get('revision', [''])[0]
                data, mime = control.artwork(revision)
                handler._send(200 if data else 404, data or b'', mime)
            else: handler._json(404, {'error': 'Unknown screensaver endpoint'})
            return True
        if handler.command != 'POST': raise ValueError('Unsupported method')
        from PAFPlayer_web_workflows import authorized
        authorized(handler, owner, owner.workflows, mutating=True)
        length = int(handler.headers.get('Content-Length', '0'))
        if not 0 < length <= 2048: raise ValueError('Invalid screensaver request size')
        handler.connection.settimeout(2)
        payload = json.loads(handler.rfile.read(length).decode('utf-8'))
        if not isinstance(payload, dict): raise ValueError('Expected a JSON object')
        if operation == 'settings': control.configure(payload)
        elif operation == 'show': control.show()
        elif operation == 'close': control.close()
        else: raise ValueError('Unknown screensaver operation')
        handler._json(200, control.snapshot())
    except PermissionError as exc: handler._json(403, {'error': str(exc)})
    except (ValueError, OSError) as exc: handler._json(400, {'error': str(exc)})
    except Exception:
        handler._json(503, {'error': 'Visual screensaver unavailable; playback continues'})
    return True


HTML = '''
<div class="group" id="visualScreensaverSection"><h3>Visual Screensaver</h3>
<p>A separate PAFPlayer.scr display. Show opens it now; Windows Screen Saver Settings control idle activation and sign-in. This does not replace the Windows lock screen.</p>
<div class="workflow-tools">
<label><input type="checkbox" id="visualScreensaverEnabled" disabled>Enable visual screensaver</label>
<label>Artwork brightness <input id="visualScreensaverBrightness" type="range" min="0" max="100" value="50" disabled><output id="visualScreensaverBrightnessValue">50%</output></label>
<button id="visualScreensaverShow" disabled>Show screensaver</button><button id="visualScreensaverClose" disabled>Close screensaver</button>
</div><p id="visualScreensaverStatus" role="status">Loading local screensaver settings…</p></div>
'''
SCRIPT = r'''
<script>(()=>{
 const $=id=>document.getElementById(id),enabled=$('visualScreensaverEnabled'),brightness=$('visualScreensaverBrightness'),show=$('visualScreensaverShow'),close=$('visualScreensaverClose');let busy=false,initialized=false,token='';
 function apply(v){enabled.checked=v.enabled;brightness.value=v.brightness;$('visualScreensaverBrightnessValue').textContent=v.brightness+'%';enabled.disabled=false;brightness.disabled=!v.enabled;show.disabled=!v.enabled;close.disabled=!v.enabled;$('visualScreensaverStatus').textContent=v.enabled?'Enabled · '+v.status:'Disabled'}
 async function poll(){if(busy)return;try{const r=await fetch('/api/screensaver/state',{cache:'no-store'}),v=await r.json();if(!r.ok)throw new Error(v.error);apply(v);initialized=true}catch(e){$('visualScreensaverStatus').textContent=String(e)}}
 async function post(op,payload={}){if(busy||!initialized)return;busy=true;try{if(!token){const r=await fetch('/api/workflows/status'),v=await r.json();if(!r.ok||!v.local||!v.token)throw new Error('Use the controls on the player computer');token=v.token}const r=await fetch('/api/screensaver/'+op,{method:'POST',headers:{'Content-Type':'application/json','X-PAF-Workflow-Token':token},body:JSON.stringify(payload)}),v=await r.json();if(!r.ok)throw new Error(v.error);apply(v)}catch(e){$('visualScreensaverStatus').textContent=String(e)}finally{busy=false}}
 enabled.onchange=()=>post('settings',{enabled:enabled.checked});brightness.oninput=()=>{$('visualScreensaverBrightnessValue').textContent=brightness.value+'%'};brightness.onchange=()=>post('settings',{brightness:Number(brightness.value)});show.onclick=()=>post('show');close.onclick=()=>post('close');poll();setInterval(()=>{if(!document.hidden&&document.activeElement!==brightness)poll()},3000);
})();</script>
'''


def augment(page):
    return page.replace('<div class="group section-global-config" id="globalConfigSection">',
                        HTML + '<div class="group section-global-config" id="globalConfigSection">', 1).replace('</body>', SCRIPT + '</body>', 1)


def main(argv=None):
    """Launch the compiled screensaver when this bridge is run directly.

    PAFPlayer imports this file as a bridge module; direct execution used to
    silently do nothing because the real GUI lives in the compiled .scr.
    Arguments are passed through to the .scr, with normal screen-saver mode
    and the player endpoint as useful defaults.
    """
    source = Path(__file__).resolve()
    executable = source.with_name('PAFPlayer.scr')
    if not executable.is_file():
        print(
            f'{executable} is missing. Run build_PAFPlayer_screensaver.py first.',
            file=sys.stderr,
        )
        return 2
    forwarded = list(sys.argv[1:] if argv is None else argv)
    if not forwarded:
        forwarded = ['/s', '/port:666']
    return subprocess.call([str(executable), *forwarded])


if __name__ == '__main__':
    raise SystemExit(main())
