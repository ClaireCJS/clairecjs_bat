"""A Windows tray-only client and native tag viewer for another PAFPlayer host."""
from __future__ import annotations

import base64
import ctypes
from ctypes import wintypes
import hashlib
import io
import json
import os
from pathlib import Path
import queue
import re
import subprocess
import sys
import threading
import time
from types import SimpleNamespace
from urllib.parse import urlencode, urlsplit
from urllib.error import HTTPError
from urllib.request import Request, build_opener, ProxyHandler
import webbrowser


class RemoteTrayAppSettings:
    """Player-settings adapter persisted per remote endpoint in roaming AppData."""
    PROGRAM_VERSION = 'remote'

    def __init__(self, label, config_root=None):
        base = config_root or (Path(os.environ.get('APPDATA') or os.environ.get('LOCALAPPDATA')
                                    or Path.home()) / 'PAFPlayer' / 'RemoteTray')
        key = hashlib.sha256(label.casefold().encode('utf-8')).hexdigest()[:24]
        self.path = Path(base) / ('tray-' + key + '.json')
        self._lock = threading.RLock()
        self._server_preferences = None

    def load_player_settings(self):
        from PAFPlayer_workflows import read_json
        value = read_json(self.path, {})
        return value if isinstance(value, dict) else {}

    def save_player_settings(self, updates):
        from PAFPlayer_workflows import write_json
        if not isinstance(updates, dict):
            raise ValueError('Remote tray settings update must be an object')
        with self._lock:
            value = self.load_player_settings()
            value.update(updates)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            write_json(self.path, value)

    def presentation_options(self):
        saved = self.load_player_settings().get('PresentationOptions', {})
        if not isinstance(saved, dict): saved = {}
        mode = saved.get('artwork_lyrics', 'server')
        return {'inherit': bool(saved.get('inherit', True)),
                'artwork_lyrics': mode if mode in ('server', 'on', 'off') else 'server'}

    def set_presentation_option(self, name, value):
        if not ((name == 'inherit' and type(value) is bool)
                or (name == 'artwork_lyrics' and value in ('server', 'on', 'off'))):
            raise ValueError('Unknown remote presentation choice')
        with self._lock:
            saved = self.presentation_options()
            saved[name] = value
            self.save_player_settings({'PresentationOptions': saved})

    def set_server_preferences(self, value):
        from PAFPlayer_tray_options import validated_preferences
        with self._lock:
            self._server_preferences = validated_preferences(value)

    def presentation_key(self):
        with self._lock:
            from PAFPlayer_tray_options import validated_preferences
            options = self.presentation_options()
            values = (self._server_preferences if options['inherit'] and self._server_preferences is not None
                      else validated_preferences(self.load_player_settings().get('RendererPreferences', {})))
            return json.dumps([options, values], sort_keys=True)

    def install_player_preference_backend(self, app_module):
        """Redirect the real popup renderer's registry contract to this endpoint JSON."""
        def query(name):
            with self._lock:
                from PAFPlayer_tray_options import portable_preference
                options = self.presentation_options()
                if str(name) == app_module.EXTERNAL_ALBUM_ART_KARAOKE_ENABLED_VALUE and options['artwork_lyrics'] != 'server':
                    return int(options['artwork_lyrics'] == 'on'), 4
                inherited = options['inherit'] and self._server_preferences is not None and portable_preference(str(name))
                records = self._server_preferences if inherited else self.load_player_settings().get('RendererPreferences', {})
                record = records.get(str(name))
            if not isinstance(record, dict) or 'value' not in record:
                raise OSError('Remote renderer preference is not set')
            return record['value'], int(record.get('type', 1))

        def set_value(name, value_type, value):
            with self._lock:
                settings = self.load_player_settings()
                values = settings.setdefault('RendererPreferences', {})
                if not isinstance(values, dict):
                    values = settings['RendererPreferences'] = {}
                values[str(name)] = {'type': int(value_type), 'value': value}
                from PAFPlayer_tray_options import portable_preference
                options = self.presentation_options()
                if str(name) == app_module.EXTERNAL_ALBUM_ART_KARAOKE_ENABLED_VALUE:
                    options['artwork_lyrics'] = 'on' if value else 'off'
                    settings['PresentationOptions'] = options
                elif portable_preference(str(name)):
                    options['inherit'] = False
                    settings['PresentationOptions'] = options
                self.path.parent.mkdir(parents=True, exist_ok=True)
                from PAFPlayer_workflows import write_json
                write_json(self.path, settings)
            return True

        def delete(name):
            with self._lock:
                settings = self.load_player_settings()
                values = settings.get('RendererPreferences', {})
                if not isinstance(values, dict) or str(name) not in values:
                    return
                values.pop(str(name), None)
                from PAFPlayer_workflows import write_json
                write_json(self.path, settings)

        app_module.ensure_pafplayer_registry_migrated = lambda: None
        app_module.paf_registry_query_value = query
        app_module.paf_registry_set_value = set_value
        app_module.paf_registry_delete_value = delete

    def options(self):
        from PAFPlayer_tray_machine import OPTION_DEFAULTS
        saved = self.load_player_settings().get('MachineOptions', {})
        return {name: bool(saved.get(name, default)) if isinstance(saved, dict) else bool(default)
                for name, default in OPTION_DEFAULTS.items()}

    def set_option(self, name, enabled):
        from PAFPlayer_tray_machine import OPTION_VALUES
        if name not in OPTION_VALUES or type(enabled) is not bool:
            raise ValueError('Unknown tray machine option')
        with self._lock:
            settings = self.load_player_settings()
            values = settings.setdefault('MachineOptions', {})
            if not isinstance(values, dict):
                values = settings['MachineOptions'] = {}
            values[name] = enabled
            from PAFPlayer_workflows import write_json
            self.path.parent.mkdir(parents=True, exist_ok=True)
            write_json(self.path, settings)

    def recent_download_folder(self):
        """Prefer the most recent destination that still exists on this computer."""
        folders = self.load_player_settings().get('DownloadFolders', [])
        if isinstance(folders, list):
            for raw in folders[:12]:
                if isinstance(raw, str) and Path(raw).is_dir():
                    return Path(raw)
        return Path.home() / 'Downloads' if (Path.home() / 'Downloads').is_dir() else Path.home()

    def remember_download_folder(self, folder):
        with self._lock:
            settings = self.load_player_settings()
            folders = settings.get('DownloadFolders', [])
            if not isinstance(folders, list):
                folders = []
            folder = str(Path(folder).resolve())
            settings['DownloadFolders'] = [folder] + [
                raw for raw in folders if isinstance(raw, str) and raw.casefold() != folder.casefold()
            ][:9]
            self.path.parent.mkdir(parents=True, exist_ok=True)
            from PAFPlayer_workflows import write_json
            write_json(self.path, settings)

    def wallpaper_lease(self):
        value = self.load_player_settings().get('WallpaperLease', {})
        return (str(value.get('original', '')), str(value.get('applied', ''))) if isinstance(value, dict) else ('', '')

    def save_wallpaper_lease(self, original, applied):
        self.save_player_settings({'WallpaperLease': {'original': str(original), 'applied': str(applied)}})


def server_address(value):
    """Accept host:port (or an HTTP URL) without credentials or URL paths."""
    raw = str(value or '').strip()
    if not raw:
        raise ValueError('--tray-only requires a PAFPlayer hostname and port')
    parsed = urlsplit(raw if '://' in raw else 'http://' + raw)
    try:
        port = 666 if parsed.port is None else parsed.port
        host = parsed.hostname
    except ValueError as exc:
        raise ValueError('Invalid PAFPlayer server address') from exc
    if (parsed.scheme != 'http' or not host or parsed.username or parsed.password
            or parsed.path not in ('', '/') or parsed.query or parsed.fragment
            or not 1 <= port <= 65535):
        raise ValueError('Use a plain HTTP hostname and port, such as machineservername:666')
    display_host = '[' + host + ']' if ':' in host else host
    return 'http://' + display_host + ':' + str(port) + '/', display_host + ':' + str(port)


def last_server_path():
    return Path(os.environ.get('APPDATA') or os.environ.get('LOCALAPPDATA') or Path.home()) / 'PAFPlayer' / 'RemoteTray' / 'last-server.json'


def parse_enqueue_arguments(arguments):
    """Keep drive-letter paths as hints; the official player resolves them."""
    address=None; selectors=[]; index=0
    while index<len(arguments):
        arg=arguments[index]
        if arg in ('--server','--regex'):
            if index+1>=len(arguments): raise ValueError(arg+' needs a value')
            value=arguments[index+1]; index+=2
            if arg=='--server':
                if address is not None: raise ValueError('Specify one --server')
                address=value
            else: selectors.append({'kind':'regex','pattern':value})
            continue
        if arg.startswith('--server='):
            if address is not None: raise ValueError('Specify one --server')
            address=arg.partition('=')[2]; index+=1; continue
        if arg.startswith('re:'):
            selectors.append({'kind':'regex','pattern':arg[3:]}); index+=1; continue
        if arg.startswith('-'): raise ValueError('Unknown enqueue option: '+arg)
        path=Path(arg).expanduser()
        # Parentheses and brackets occur in ordinary song names. Require a
        # stronger signal before treating an unmounted client path as regex.
        looks_regex=(arg.startswith('^') or arg.endswith('$') or
                     bool(re.search(r'(\.\*|\.\+|\\[dDsSwW]|[|*?]|\{\d+(?:,\d*)?\})',arg)))
        if not path.exists() and looks_regex:
            selectors.append({'kind':'regex','pattern':arg})
        elif path.is_dir():
            from PAFPlayer_workflows import scan_media
            app=sys.modules.get('PAFPlayer') or sys.modules['__main__']
            found=list(scan_media([path],app.AUDIO_EXTENSIONS,False))
            if not found: raise ValueError('Folder contains no supported audio: '+str(path))
            selectors.extend({'kind':'path','value':str(item),'size':item.stat().st_size} for item in found)
        elif path.is_file() and path.suffix.casefold() in ('.m3u','.m3u8','.pls'):
            from PAFPlayer_workflows import playlist_rows
            selectors.extend({'kind':'path','value':row['path']} for row in playlist_rows(path)[3])
        else:
            item={'kind':'path','value':str(path.resolve()) if path.is_file() else arg}
            if path.is_file(): item['size']=path.stat().st_size
            selectors.append(item)
        index+=1
    if not selectors: raise ValueError('Usage: PAFPlayer --enqueue [--server HOST:PORT] FILE|re:PATTERN ...')
    if len(selectors)>5000: raise ValueError('At most 5000 enqueue selectors')
    return address,selectors


def enqueue_receipt(answer, *, server=None):
    """Separate play-next count from newly created playlist membership."""
    count=int(answer.get('queued',0))
    action=str(answer.get('message') or 'Queued next')
    if server: action+=' on '+server
    noun='track' if count==1 else 'tracks'
    detail=''
    if 'added_to_playlist' in answer and 'already_in_playlist' in answer:
        added=int(answer['added_to_playlist']);existing=int(answer['already_in_playlist'])
        detail=(f' ({added} new playlist '+('entry' if added==1 else 'entries')+
                f'; {existing} already in playlist)')
    return f'{action} — {count} {noun}{detail}.'


def _enqueue_color_enabled():
    if os.environ.get('NO_COLOR') or not sys.stdout.isatty(): return False
    if os.name!='nt': return True
    try:
        import msvcrt
        handle=msvcrt.get_osfhandle(sys.stdout.fileno())
        mode=wintypes.DWORD()
        kernel=ctypes.windll.kernel32
        if not kernel.GetConsoleMode(handle,ctypes.byref(mode)): return False
        return bool(kernel.SetConsoleMode(handle,mode.value|4))
    except (AttributeError,OSError,ValueError): return False


def format_enqueue_matches(paths, *, limit=None, color=False):
    """Keep each folder heading once while retaining original match numbers."""
    palette=((112,214,241),(134,232,187),(251,206,138),
             (226,165,220),(171,191,251),(241,181,154))
    groups={}
    for index,raw in enumerate(paths[:limit] if limit is not None else paths,1):
        path=Path(raw)
        folder=''.join(ch if ch>=' ' and ch!='\x7f' else '?' for ch in str(path.parent))
        name=''.join(ch if ch>=' ' and ch!='\x7f' else '?' for ch in path.name)
        groups.setdefault(folder,[]).append((index,name))
    lines=[]
    for folder,items in groups.items():
        lines.append(folder)
        for index,name in items:
            if color:
                red,green,blue=palette[(index-1)%len(palette)]
                name=f'\x1b[38;2;{red};{green};{blue}m{name}\x1b[0m'
            lines.append(f'  {index:>3}. {name}')
    return '\n'.join(lines)


class _EnqueueProgress:
    def __init__(self,message):
        self.message=message;self.stop=threading.Event();self.thread=None
        self.tty=bool(sys.stdout.isatty())

    def __enter__(self):
        if not self.tty:
            print(self.message,flush=True)
            return self
        sys.stdout.write('\r'+self.message+' |')
        sys.stdout.flush()
        def animate():
            frames='/-\\';index=0
            while not self.stop.is_set():
                sys.stdout.write('\r'+self.message+' '+frames[index%len(frames)])
                sys.stdout.flush();index+=1
                self.stop.wait(.2)
        self.thread=threading.Thread(target=animate,name='paf-enqueue-status',daemon=True)
        self.thread.start()
        return self

    def __exit__(self,*_exc):
        self.stop.set()
        if self.thread:
            self.thread.join(timeout=.5)
            sys.stdout.write('\r'+' '*(len(self.message)+3)+'\r')
            sys.stdout.flush()


def confirm_enqueue_matches(count, *, input_fn=None, stdin=None):
    """A large resolved request needs an interactive, explicit yes."""
    stream=sys.stdin if stdin is None else stdin
    if stream is None or not stream.isatty():
        print(f'PAFPlayer: {count} matches need confirmation in an interactive terminal; nothing was queued.',file=sys.stderr)
        return False
    if input_fn is None: input_fn=input
    while True:
        answer=input_fn(f'Enqueue all {count} tracks? [Y]es / [L]ist all / [N]o (default): ').strip().casefold()
        if answer in ('y','yes'): return True
        if answer in ('','n','no'): return False
        if answer in ('l','list'): return 'list'
        print('Please enter Y, L, or N.')


def run_enqueue(arguments, *, placement=None):
    commit_started=False
    try:
        if placement not in (None,'after_current','end'):
            raise ValueError('Enqueue placement must be after_current or end')
        address,selectors=parse_enqueue_arguments(arguments)
        # The owner searches from the invoking shell's folder when its full
        # library filelist is absent. A remote-only path is ignored there.
        selectors[0]['origin_dir']=str(Path.cwd())
        placement_request={'placement':placement} if placement is not None else {}
        needs_preview=any(item['kind']=='regex' for item in selectors) or len(selectors)>20
        status=('PAFPlayer: Searching the official player library for matches…'
                if needs_preview else 'PAFPlayer: Resolving and enqueueing on the official player…')
        instance=None;server=None;identity=None
        def send(payload, *, preview=False):
            if instance is not None:
                return instance.forward(payload,timeout=120) if preview else instance.forward(payload)
            body=json.dumps({'identity':identity,**payload}).encode('utf-8')
            request=Request(server.url.rstrip('/')+'/api/remote-enqueue',data=body,
                            headers={'Content-Type':'application/json'},method='POST')
            try:
                with server._opener.open(request,timeout=120 if preview else 30) as response:
                    result=json.loads(response.read(8*1024*1024))
            except HTTPError as exc:
                raise ValueError(json.loads(exc.read(65536)).get('error','Remote enqueue failed')) from None
            if not result.get('ok'): raise ValueError(result.get('error','Remote enqueue failed'))
            return result
        with _EnqueueProgress(status):
            if address is None:
                from PAFPlayer_workflows import read_json, get_runtime
                from PAFPlayer_instance import Instance
                app=sys.modules.get('PAFPlayer') or sys.modules['__main__']
                instance=Instance(get_runtime(app))
                if instance.acquire():
                    instance.close();instance=None
                    address=os.environ.get('PAFPLAYER_SERVER') or read_json(last_server_path(),{}).get('address')
            if instance is None:
                if not address:
                    raise ValueError('No official player here or remembered remote server; use --server HOST:PORT')
                server=RemoteServer(address)
                identity,_=server.hello(include_timeline=False)
            if needs_preview:
                answer=send({'selectors':selectors,'preview_only':True},preview=True)
            else:
                commit_started=True
                answer=send({'selectors':selectors,**placement_request})
        if needs_preview:
            matches=answer.get('matches');token=answer.get('preview_token')
            if (not isinstance(matches,list) or not 0<len(matches)<=5000
                    or any(not isinstance(path,str) for path in matches)
                    or not isinstance(token,str)):
                raise ValueError('Official player returned an invalid enqueue preview')
            print(f'PAFPlayer: Search matched {len(matches)} '+('track' if len(matches)==1 else 'tracks')+':')
            color=_enqueue_color_enabled()
            print(format_enqueue_matches(matches,limit=20 if len(matches)>20 else None,color=color))
            if len(matches)>20:
                print(f'Showing the first 20 of {len(matches)} tracks.')
                while True:
                    choice=confirm_enqueue_matches(len(matches))
                    if choice=='list':
                        print(format_enqueue_matches(matches,color=color))
                        continue
                    if not choice:
                        print('PAFPlayer: Enqueue cancelled; nothing was queued.')
                        return 1
                    break
            noun='track' if len(matches)==1 else 'tracks'
            with _EnqueueProgress(f'PAFPlayer: Queueing {len(matches)} selected {noun}…'):
                commit_started=True
                answer=send({'preview_token':token,**placement_request})
        print('PAFPlayer: '+enqueue_receipt(answer,server=server.label if server else None))
        return 0
    except (OSError,ValueError,KeyError,EOFError,KeyboardInterrupt) as exc:
        if isinstance(exc,(EOFError,KeyboardInterrupt)):
            print('PAFPlayer enqueue: interrupted; check the official queue before retrying.' if commit_started
                  else 'PAFPlayer enqueue: cancelled; nothing was queued.',file=sys.stderr)
            return 1
        detail='; the request may have completed, so check the queue before retrying' if commit_started and isinstance(exc,OSError) else ''
        print('PAFPlayer enqueue: '+str(exc)+detail,file=sys.stderr)
        return 2


class RemoteServer:
    """One fixed, verified HTTP target; no local playback or IPC ownership."""
    def __init__(self, address):
        self.url, self.label = server_address(address)
        self.enabled = True
        self._httpd = None
        self._opener = build_opener(ProxyHandler({}))
        self._lock = threading.RLock()
        self._state = {}
        self.connected = False
        self.owner_identity = ''
        self.last_error = 'Connecting…'
        self.stop_event = threading.Event()
        self._thread = None
        self.on_change = None
        # A timestamped playback anchor lets local overlays run smoothly between
        # heartbeats. One reconciliation per second is enough to correct drift
        # without repeatedly transferring the complete lyric timeline.
        self.poll_interval = 1.0
        self.clock_offset = 0.0
        self._lyric_timeline = []
        self._lyric_timeline_revision = -1

    def _read(self, path, *, timeout=3, limit=24 * 1024 * 1024):
        request = Request(self.url.rstrip('/') + path,
                          headers={'Accept': 'application/json', 'Cache-Control': 'no-store'})
        with self._opener.open(request, timeout=timeout) as response:
            data = response.read(limit + 1)
            if len(data) > limit:
                raise ValueError('PAFPlayer response exceeded the viewer limit')
            return data

    def json(self, path, *, timeout=3):
        return json.loads(self._read(path, timeout=timeout).decode('utf-8'))

    def image(self, generation, index):
        query = urlencode({'generation': generation, 'index': index})
        return self._read('/api/track-details/art?' + query, timeout=5, limit=20 * 1024 * 1024)

    def wallpaper(self, generation, width, height):
        if not self.connected or not self.owner_identity:
            return None
        if int(str(self.snapshot().get('version') or 'V0')[1:]) < 504:
            raise ValueError('Album-art wallpaper requires a V504 or newer player server')
        query = urlencode({'generation': generation, 'width': width, 'height': height,
                           'identity': self.owner_identity})
        return self._read('/api/track-details/wallpaper?' + query, timeout=7, limit=10 * 1024 * 1024)

    def snapshot(self):
        with self._lock:
            return dict(self._state)

    def _verify_status(self, value):
        if (not isinstance(value, dict) or str(value.get('program', '')).casefold() != 'pafplayer'
                or not re.fullmatch(r'V\d+', str(value.get('version', '')))):
            raise ValueError('The target did not identify itself as PAFPlayer')
        if int(str(value['version'])[1:]) < 503:
            raise ValueError('The target PAFPlayer must be V503 or newer for the tag viewer')
        return value

    def hello(self, *, include_timeline=True):
        sent = time.time()
        greeting = self._verify_status(self.json(
            '/api/remote-tray/hello?' + urlencode({
                'timeline': '1' if include_timeline else '0',
            })
        ))
        received = time.time()
        if isinstance(greeting.get('server_epoch'), (int, float)):
            self.clock_offset = float(greeting['server_epoch']) - (sent + received) / 2
        identity = greeting.get('identity')
        if not greeting.get('official') or not isinstance(identity, str) or not identity:
            raise ValueError('The target is not the official active PAFPlayer instance')
        state = self._verify_status(greeting.get('state'))
        if state['version'] != greeting['version']:
            raise ValueError('PAFPlayer changed owner during the status request')
        revision = int(state.get('lyric_timeline_revision') or 0)
        if isinstance(state.get('lyric_timeline'), list):
            self._lyric_timeline = state['lyric_timeline']
            self._lyric_timeline_revision = revision
        elif include_timeline:
            self._lyric_timeline = []
            self._lyric_timeline_revision = revision
            state['lyric_timeline'] = self._lyric_timeline
        elif revision == self._lyric_timeline_revision:
            state['lyric_timeline'] = self._lyric_timeline
        return identity, state

    def poll_once(self):
        try:
            identity, state = self.hello(include_timeline=False)
            revision = int(state.get('lyric_timeline_revision') or 0)
            if identity != self.owner_identity or revision != self._lyric_timeline_revision:
                identity, state = self.hello(include_timeline=True)
            with self._lock:
                changed = (not self.connected or self.owner_identity != identity
                           or self._state.get('version') != state.get('version'))
                self._state = state
                self.owner_identity = identity
                self.connected = True
                self.last_error = ''
        except Exception as exc:
            with self._lock:
                changed = self.connected or self.last_error != str(exc)
                self.connected = False
                self.owner_identity = ''
                self.last_error = str(exc)
        if changed and self.on_change:
            self.on_change()
        return self.connected

    def start_polling(self):
        if self._thread and self._thread.is_alive():
            return
        def run():
            while not self.stop_event.is_set():
                self.poll_once()
                self.stop_event.wait(self.poll_interval)
        self._thread = threading.Thread(target=run, name='paf-remote-tray-heartbeat', daemon=True)
        self._thread.start()

    def command(self, action, issued_at=None, expected_identity=None):
        if action not in ('previous', 'next', 'pause', 'stop', 'volume_up', 'volume_down',
                          'volume_mute', 'seek_forward', 'seek_back', 'seek_forward_fast',
                          'seek_back_fast', 'art_foreground', 'floating_foreground',
                          'floating_toggle'):
            raise ValueError('Unknown remote tray action')
        if (not self.connected or not self.owner_identity
                or (expected_identity is not None and expected_identity != self.owner_identity)):
            return False
        try:
            query = urlencode({'action': action, 'identity': self.owner_identity,
                               'client_epoch': '%.6f' % (time.time() if issued_at is None else issued_at)})
            answer = self.json('/api/remote-tray/action?' + query)
            return bool(answer.get('accepted'))
        except Exception:
            self.poll_once()
            return False

    def enqueue_dropped_paths(self, targets):
        """Resolve client paths on the official server, even with different drives."""
        _address, selectors = parse_enqueue_arguments([str(path) for path in targets])
        identity, _state = self.hello(include_timeline=False)
        body = json.dumps({'identity': identity, 'selectors': selectors}).encode('utf-8')
        request = Request(
            self.url.rstrip('/') + '/api/remote-enqueue', data=body,
            headers={'Content-Type': 'application/json'}, method='POST',
        )
        try:
            with self._opener.open(request, timeout=30) as response:
                answer = json.loads(response.read(8 * 1024 * 1024))
        except HTTPError as exc:
            raise ValueError(json.loads(exc.read(65536)).get('error', 'Remote enqueue failed')) from None
        if not answer.get('ok'):
            raise ValueError(answer.get('error', 'Remote enqueue failed'))
        return answer

    def current_file_ticket(self):
        """Bind a Save As request to one official owner and one logical play."""
        identity, state = self.hello(include_timeline=False)
        track = state.get('track') or {}
        path = str(track.get('path') or '')
        filename = str(track.get('filename') or '')
        visit = int(state.get('track_visit') or 0)
        if not path or not filename or filename != Path(filename).name or visit < 1:
            raise ValueError('No current source audio file is available')
        return identity, path, visit, filename

    def download_current(self, ticket, destination, progress=None, cancelled=None):
        """Save a complete verified transfer; never overwrite an existing file."""
        identity, path, visit, _filename = ticket
        destination = Path(destination)
        if not destination.parent.is_dir():
            raise ValueError('The destination folder does not exist')
        if destination.exists():
            raise FileExistsError('The selected destination already exists; choose another name')
        if self.current_file_ticket() != ticket:
            raise ValueError('The official instance or current track changed before transfer')
        query = urlencode({'identity': identity, 'path': path, 'visit': visit})
        request = Request(self.url.rstrip('/') + '/api/remote-tray/download?' + query,
                          headers={'Accept': 'application/octet-stream', 'Cache-Control': 'no-store'})
        part = None
        try:
            with self._opener.open(request, timeout=30) as response:
                expected = int(response.headers.get('Content-Length', '-1'))
                if expected < 0:
                    raise ValueError('The server omitted the source file length')
                for index in range(1000):
                    candidate = destination.with_name(destination.name +
                        ('' if index == 0 else ' (' + str(index) + ')') + '.download')
                    try:
                        output = candidate.open('xb')
                        part = candidate
                        break
                    except FileExistsError:
                        continue
                else:
                    raise FileExistsError('Too many unfinished downloads in this folder')
                received = 0
                with output:
                    while received < expected:
                        if cancelled is not None and cancelled.is_set():
                            raise InterruptedError('Download cancelled')
                        chunk = response.read(min(128 * 1024, expected - received))
                        if not chunk:
                            raise ValueError('The source changed or the transfer ended early')
                        output.write(chunk)
                        received += len(chunk)
                        if progress is not None:
                            progress(received, expected)
            if cancelled is not None and cancelled.is_set():
                raise InterruptedError('Download cancelled')
            if self.current_file_ticket() != ticket:
                raise ValueError('The official instance or current track changed during transfer')
            if destination.exists():
                raise FileExistsError('The selected destination now exists; it was not overwritten')
            # Windows MoveFile fails if the destination appears between the check
            # and rename. The tray-only client is Windows-only.
            os.rename(part, destination)
            part = None
            return destination
        except Exception as exc:
            if part is not None and part.exists():
                try:
                    from send2trash import send2trash
                    send2trash(str(part))
                except Exception as recycle_error:
                    raise RuntimeError(str(exc) + '; partial transfer retained at ' + str(part)
                                       + ' because recycling failed: ' + str(recycle_error)) from exc
            raise

    def close(self):
        self.stop_event.set()
        if self._thread and self._thread is not threading.current_thread():
            self._thread.join(timeout=3)


class RemoteHotkeys:
    """Edge-triggered transport keys and bounded auto-repeat volume controls."""
    VK = {'ctrl': 0x11, 'alt': 0x12, 'shift': 0x10, 'pause_key': 0x13, 'win_l': 0x5B,
          'win_r': 0x5C, 'c': 0x43, 'a': 0x41, 'f': 0x46,
          'up': 0x26, 'down': 0x28, 'media_prev': 0xB1,
          'media_next': 0xB0, 'media_pause': 0xB3, 'media_stop': 0xB2,
          'volume_up': 0xAF, 'volume_down': 0xAE, 'volume_mute': 0xAD}

    def __init__(self):
        self.held = set()
        self.repeat_at = {}

    def sample(self, down, now=None, epoch=None):
        now = time.monotonic() if now is None else now
        epoch = time.time() if epoch is None else epoch
        pressed = {name for name, code in self.VK.items() if down(code)}
        new = pressed - self.held
        self.held = pressed
        chord = 'ctrl' in pressed and 'alt' in pressed
        transport_modifier = 'ctrl' in pressed or 'alt' in pressed
        shift = 'shift' in pressed
        events = []
        def fire(target, action): events.append((target, action, epoch))
        if 'c' in new and ('win_l' in pressed or 'win_r' in pressed): fire('server', 'pause')
        if chord:
            # Remote-tray presentation belongs to this computer. Shift remains
            # an alias, but is no longer required to toggle either local overlay.
            if 'f' in new: fire('local', 'floating_show')
            if 'a' in new: fire('local', 'art_show')
            for key, action in (('up', 'volume_up'), ('down', 'volume_down')):
                if key in pressed and now >= self.repeat_at.get(key, 0):
                    fire('server', action)
                    self.repeat_at[key] = now + (.32 if key in new else .085)
                if key not in pressed: self.repeat_at.pop(key, None)
        # Some keyboards report Pause and Media Play/Pause in the same poll.
        # Send one toggle, otherwise two requests would cancel one another.
        if 'pause_key' in new or 'media_pause' in new:
            fire('server', 'pause')
        for key, action in (('media_stop', 'stop'), ('volume_mute', 'volume_mute')):
            if key in new: fire('server', action)
        if 'media_prev' in new: fire('server', 'previous' if transport_modifier else 'seek_back_fast' if shift else 'seek_back')
        if 'media_next' in new: fire('server', 'next' if transport_modifier else 'seek_forward_fast' if shift else 'seek_forward')
        for key, action in (('volume_up', 'volume_up'), ('volume_down', 'volume_down')):
            if key in pressed and now >= self.repeat_at.get(key, 0):
                fire('server', action)
                self.repeat_at[key] = now + (.32 if key in new else .085)
            if key not in pressed: self.repeat_at.pop(key, None)
        return events


def synchronized_position(state, local_epoch, clock_offset=0.0):
    """Advance the published audio clock using the server's measured wall clock."""
    try:
        position = float(state.get('lyric_position_seconds') or state.get('position_seconds') or 0)
        if state.get('playing') and not state.get('paused'):
            elapsed = max(0.0, min(4.0, local_epoch + clock_offset - float(state['lyric_clock_epoch'])))
            position += elapsed * float(state.get('speed') or 1)
        return max(0.0, position)
    except (KeyError, TypeError, ValueError):
        return 0.0


class RemoteTrayIdentity:
    """Owns only this client's icon, never the server's official mutex."""
    def owns(self):
        return True


def launch_viewer(address):
    """Give Tk its own main thread and process without creating another tray."""
    url, _label = server_address(address)
    app_module = sys.modules.get('PAFPlayer') or sys.modules['__main__']
    app_file = Path(app_module.__file__).resolve()
    executable = Path(sys.executable)
    flags = 0
    if os.name == 'nt' and executable.name.casefold() == 'python.exe':
        pythonw = executable.with_name('pythonw.exe')
        if pythonw.is_file():
            executable = pythonw
        else:
            flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    return subprocess.Popen([str(executable), str(app_file), '--tag-viewer', url],
                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, creationflags=flags)


def _remote_mutex(_label):
    """One tray-only client per Windows logon; the kernel releases crashes safely."""
    kernel32 = ctypes.windll.kernel32
    kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
    kernel32.CreateMutexW.restype = wintypes.HANDLE
    kernel32.GetLastError.restype = wintypes.DWORD
    name = 'Local\\PAFPlayerRemoteTray'
    handle = kernel32.CreateMutexW(None, True, name)
    if not handle:
        raise OSError('Could not create the remote-tray mutex')
    if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        kernel32.CloseHandle(handle)
        return None
    return handle


def run_remote_save_dialog(server, settings, stop_event):
    """Keep Tk on the tray-only main thread and stream on a worker."""
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    root = tk.Tk()
    root.withdraw()
    try:
        ticket = server.current_file_ticket()
        destination = filedialog.asksaveasfilename(
            parent=root, title='Save current music file',
            initialdir=str(settings.recent_download_folder()), initialfile=ticket[3],
            confirmoverwrite=False,
        )
        if not destination:
            return
        target = Path(destination)
        if target.exists():
            messagebox.showerror('PAFPlayer', 'That file already exists. Choose a different name.', parent=root)
            return
        updates = queue.SimpleQueue()
        cancelled = threading.Event()
        root.title('PAFPlayer file transfer')
        root.geometry('480x130')
        root.resizable(False, False)
        label = ttk.Label(root, text='Saving ' + ticket[3])
        label.pack(fill='x', padx=14, pady=(15, 9))
        meter = ttk.Progressbar(root, mode='determinate', maximum=1000)
        meter.pack(fill='x', padx=14)
        details = ttk.Label(root, text='Connecting…')
        details.pack(fill='x', padx=14, pady=9)
        root.deiconify()
        result = {'error': None, 'path': None}
        def worker():
            try:
                result['path'] = server.download_current(
                    ticket, target, progress=lambda done, total: updates.put(('progress', done, total)),
                    cancelled=cancelled)
                settings.remember_download_folder(target.parent)
            except Exception as exc:
                result['error'] = str(exc)
            finally:
                updates.put(('finished', 0, 0))
        thread = threading.Thread(target=worker, name='paf-remote-file-save', daemon=True)
        thread.start()
        def poll():
            if stop_event.is_set():
                cancelled.set()
            finished = False
            while True:
                try:
                    kind, done, total = updates.get_nowait()
                except queue.Empty:
                    break
                if kind == 'finished':
                    finished = True
                else:
                    meter['value'] = round(1000 * done / max(1, total))
                    details.configure(text=f'{done / 1048576:.1f} / {total / 1048576:.1f} MiB')
            if finished:
                root.quit()
            else:
                root.after(100, poll)
        root.protocol('WM_DELETE_WINDOW', lambda: (cancelled.set(), details.configure(text='Cancelling…')))
        root.after(100, poll)
        root.mainloop()
        if result['error']:
            messagebox.showerror('PAFPlayer file transfer', result['error'], parent=root)
        elif result['path']:
            messagebox.showinfo('PAFPlayer file transfer', 'Saved ' + str(result['path']), parent=root)
    except Exception as exc:
        messagebox.showerror('PAFPlayer file transfer', str(exc), parent=root)
    finally:
        root.destroy()


def launch_background_tray(address):
    from PAFPlayer_workflows import unique
    app = sys.modules.get('PAFPlayer') or sys.modules['__main__']
    app_file = str(Path(app.__file__).resolve())
    settings = RemoteTrayAppSettings(address)
    folder = settings.path.parent / 'logs'
    folder.mkdir(parents=True, exist_ok=True)
    log = unique(folder / (time.strftime('tray-%Y%m%d-%H%M%S') + '.log'))
    environment = dict(os.environ, PAFPLAYER_TRAY_BACKGROUND='1')
    with log.open('xb') as output:
        process = subprocess.Popen(
            [sys.executable, '-B', app_file, '--tray-only', address, '--foreground'],
            stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT,
            close_fds=True, env=environment,
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
    print('PAFPlayer tray starting in background (PID ' + str(process.pid) + ').')
    print('Tray diagnostics: ' + str(log))
    return 0


def run_tray_only(arguments):
    arguments = list(arguments)
    foreground = '--foreground' in arguments
    if foreground:
        arguments.remove('--foreground')
    if len(arguments) != 1:
        print('Usage: PAFPlayer --tray-only HOST:PORT [--foreground]', file=sys.stderr)
        return 2
    if os.name != 'nt':
        print('The tray-only client requires Windows.', file=sys.stderr)
        return 2
    try:
        server = RemoteServer(arguments[0])
        if not foreground:
            return launch_background_tray(server.label)
        mutex = _remote_mutex(server.label)
    except (ValueError, OSError) as exc:
        print('PAFPlayer: ' + str(exc), file=sys.stderr)
        return 2
    if mutex is None:
        print('PAFPlayer: a tray-only client is already running in this Windows session.')
        return 0
    from PAFPlayer_tray import TrayController
    stop = threading.Event()
    reload_requested = threading.Event()
    commands = queue.Queue(maxsize=64)
    save_requests = queue.Queue(maxsize=1)
    hotkeys = RemoteHotkeys()
    def send_commands():
        while not stop.is_set():
            try: action, epoch, identity = commands.get(timeout=.2)
            except queue.Empty: continue
            server.command(action, epoch, identity)
    threading.Thread(target=send_commands, name='paf-remote-controls', daemon=True).start()

    class RemoteTrayController(TrayController):
        def poll_hotkeys(self):
            if not self._machine or not self._machine.options.get('remote_hotkeys', True): return
            user32 = ctypes.windll.user32
            for target, action, epoch in hotkeys.sample(lambda code: bool(user32.GetAsyncKeyState(code) & 0x8000)):
                if target == 'local':
                    overlays.show(floating=action == 'floating_show')
                else:
                    if server.connected:
                        try: commands.put_nowait((action, epoch, server.owner_identity))
                        except queue.Full: pass

        def tooltip_text(self):
            state = 'connected' if server.connected else 'disconnected'
            base = 'PAFPlayer remote · ' + server.label + ' · ' + state
            lyric = self._machine.tooltip_lyric() if self._machine else ''
            return base + (' · ' + lyric if lyric else '')

        def menu_items(self, state):
            active = server.connected
            save_available = active and int(str(state.get('version') or 'V0')[1:]) >= 577
            label = 'Play' if state.get('paused') else 'Pause'
            return [(1, label, 'pause', active), (2, 'Previous track', 'previous', active),
                    (3, 'Next track', 'next', active), (4, 'Open web configuration', 'web', active),
                    (5, 'Open tag viewer', 'details', True),
                    (15, 'Options…', 'options', True),
                    (14, 'Save current music file…', 'save_current', save_available),
                    (6, ('✓ ' if self._machine and self._machine.options['lyrics_tooltip'] else '○ ') + 'Show sung lyrics above tray', 'machine_lyrics_tooltip', True),
                    (7, ('✓ ' if self._machine and self._machine.options['album_wallpaper'] else '○ ') + 'Album art desktop wallpaper', 'machine_album_wallpaper', True),
                    (8, ('✓ ' if self._machine and self._machine.options.get('remote_hotkeys', True) else '○ ') + 'Capture control hotkeys here', 'machine_remote_hotkeys', True),
                    (9, ('✓ ' if self._machine and self._machine.options.get('remote_floating_lyrics') else '○ ') + 'Floating lyrics on this computer', 'machine_remote_floating_lyrics', True),
                    (10, ('✓ ' if self._machine and self._machine.options.get('remote_album_art') else '○ ') + 'Album art window on this computer', 'machine_remote_album_art', True),
                    (11, 'Reload tray from updated PAFPlayer.py', 'reload', True),
                    (12, 'Server / version', 'about', True), (13, 'Exit this tray', 'exit', True)]

        def dispatch(self, action):
            if self._closing:
                return False
            if action.startswith('icon_style_') or action == 'full_info_tooltip':
                return super().dispatch(action)
            if action == 'options':
                overlays.options(self, stop)
                return True
            if action.startswith('machine_') and self._machine:
                name = action.removeprefix('machine_')
                changed = self._machine.toggle(name)
                if changed and name in ('remote_floating_lyrics', 'remote_album_art') and self._machine.options.get(name):
                    overlays.start()
                return changed
            if action in ('previous', 'next', 'pause', 'stop', 'volume_up', 'volume_down',
                          'volume_mute', 'seek_forward', 'seek_back', 'seek_forward_fast',
                          'seek_back_fast', 'art_foreground', 'floating_foreground'):
                if not server.connected: return False
                try: commands.put_nowait((action, time.time(), server.owner_identity))
                except queue.Full: return False
                return True
            if action == 'details':
                launch_viewer(server.url)
                return True
            if action == 'save_current':
                if not server.connected:
                    return False
                try:
                    save_requests.put_nowait(True)
                    return True
                except queue.Full:
                    return False
            if action == 'web':
                webbrowser.open(server.url)
                return True
            if action == 'about':
                version = server.snapshot().get('version') or 'disconnected'
                message = 'PAFPlayer tray-only client\nServer: ' + server.label + '\nServer version: ' + str(version)
                if self._machine and self._machine.last_error:
                    message += '\nDesktop option: ' + self._machine.last_error
                self._message(message)
                return True
            if action == 'exit':
                stop.set()
                return True
            if action == 'reload':
                reload_requested.set()
                stop.set()
                return True
            return False

    runtime = SimpleNamespace(server=server, log=lambda *_args, **_fields: None,
                              app=RemoteTrayAppSettings(server.label))
    app_module = sys.modules.get('PAFPlayer') or sys.modules['__main__']
    runtime.app.install_player_preference_backend(app_module)
    tray = RemoteTrayController(runtime, RemoteTrayIdentity(), override=True,
                               drop_callback=server.enqueue_dropped_paths,
                               drop_reader=app_module.windows_dropped_paths)
    tray.attach_machine_options(remote=True, settings=runtime.app)
    from PAFPlayer_remote_overlay import RemoteOverlays
    overlays = RemoteOverlays(server, tray._machine)
    if (tray._machine.options.get('remote_floating_lyrics')
            or tray._machine.options.get('remote_album_art')):
        overlays.start()
    server.on_change = tray.refresh
    server.start_polling()
    try:
        if not tray.start():
            print('PAFPlayer: could not create the remote tray icon.', file=sys.stderr)
            return 1
        from PAFPlayer_workflows import read_json, write_json
        remembered=read_json(last_server_path(),{})
        if remembered.get('address')!=server.label:
            write_json(last_server_path(),{'address':server.label})
        while not stop.is_set() and tray._thread and tray._thread.is_alive():
            try:
                save_requests.get(timeout=.25)
            except queue.Empty:
                continue
            run_remote_save_dialog(server, runtime.app, stop)
        return 0
    except KeyboardInterrupt:
        return 0
    finally:
        stop.set()
        overlays.close()
        tray.close()
        server.close()
        kernel32 = ctypes.windll.kernel32
        kernel32.ReleaseMutex(mutex)
        kernel32.CloseHandle(mutex)
        if reload_requested.is_set():
            app_module = sys.modules.get('PAFPlayer') or sys.modules['__main__']
            app_file = str(Path(app_module.__file__).resolve())
            try:
                if os.environ.get('PAFPLAYER_TRAY_BACKGROUND') == '1':
                    launch_background_tray(arguments[0])
                else:
                    os.execv(sys.executable, [sys.executable, app_file, '--tray-only', arguments[0], '--foreground'])
            except OSError as exc:
                print('PAFPlayer: tray reload failed: ' + str(exc), file=sys.stderr)


def run_viewer(arguments):
    """Run a native Tk inspector; this mode never creates a tray or plays audio."""
    if len(arguments) != 1:
        print('Usage: PAFPlayer --tag-viewer machineservername:666', file=sys.stderr)
        return 2
    try:
        server = RemoteServer(arguments[0])
        import tkinter as tk
        from tkinter import ttk
    except (ValueError, ImportError) as exc:
        print('PAFPlayer tag viewer: ' + str(exc), file=sys.stderr)
        return 2
    root = tk.Tk()
    root.title('PAFPlayer tags · ' + server.label)
    root.geometry('980x700')
    root.minsize(650, 460)
    heading = ttk.Frame(root, padding=10)
    heading.pack(fill='x')
    title = ttk.Label(heading, text='Current track · ' + server.label, font=('Segoe UI', 14, 'bold'))
    title.pack(side='left')
    status = ttk.Label(root, text='Connecting to PAFPlayer…', padding=(10, 0))
    status.pack(fill='x')
    book = ttk.Notebook(root)
    book.pack(fill='both', expand=True, padx=10, pady=10)
    frames = {name: ttk.Frame(book) for name in ('Overview', 'Tags', 'Lyrics', 'Artwork', 'Technical')}
    for name, frame in frames.items():
        book.add(frame, text=name)

    def text_tab(frame):
        widget = tk.Text(frame, wrap='word', state='disabled', font=('Consolas', 10))
        bar = ttk.Scrollbar(frame, command=widget.yview)
        widget.configure(yscrollcommand=bar.set)
        widget.pack(side='left', fill='both', expand=True)
        bar.pack(side='right', fill='y')
        return widget

    overview = text_tab(frames['Overview'])
    lyrics = text_tab(frames['Lyrics'])
    artwork = text_tab(frames['Artwork'])
    technical = text_tab(frames['Technical'])
    columns = ('source', 'key', 'value')
    tags = ttk.Treeview(frames['Tags'], columns=columns, show='headings')
    for name, width in (('source', 90), ('key', 230), ('value', 550)):
        tags.heading(name, text=name.title())
        tags.column(name, width=width, stretch=True)
    tag_bar = ttk.Scrollbar(frames['Tags'], command=tags.yview)
    tags.configure(yscrollcommand=tag_bar.set)
    tags.pack(side='left', fill='both', expand=True)
    tag_bar.pack(side='right', fill='y')
    tag_detail = tk.Text(frames['Tags'], height=5, wrap='word', state='disabled')
    tag_detail.pack(side='bottom', fill='x')
    tag_rows = []
    def selected_tag(_event=None):
        selection = tags.selection()
        if not selection:
            return
        index = tags.index(selection[0])
        if index < len(tag_rows):
            fill(tag_detail, str(tag_rows[index][2]))
    tags.bind('<<TreeviewSelect>>', selected_tag)
    images = []
    current_identity = ['', -1]
    loading = [False]
    updates = queue.Queue()

    def fill(widget, value):
        widget.configure(state='normal')
        widget.delete('1.0', 'end')
        widget.insert('end', value)
        widget.configure(state='disabled')

    def show(data, art_bytes):
        images.clear()
        file = data.get('file') or {}
        if not data.get('available'):
            status.configure(text=data.get('message') or 'No current track')
            for widget in (overview, lyrics, artwork, technical):
                fill(widget, 'No current track.')
            tags.delete(*tags.get_children())
            tag_rows.clear()
            fill(tag_detail, '')
            current_identity[:] = ['', int(data.get('art_generation') or 0)]
            return
        name = str(file.get('name') or 'Current track')
        status.configure(text=name + ' · ' + server.label)
        current_identity[:] = [str(file.get('path') or ''), int(data.get('art_generation') or 0)]
        facts = [('File', name), ('Path', file.get('path', '')),
                 ('Size', f"{int(file.get('size_bytes') or 0):,} bytes"),
                 ('Modified UTC', file.get('modified_utc', '')),
                 ('Duration', str(data.get('duration_seconds') or 'Unknown') + ' seconds')]
        fill(overview, '\n'.join(f'{key}: {value}' for key, value in facts))
        tags.delete(*tags.get_children())
        tag_rows.clear()
        for row in data.get('tags') or []:
            tag_rows.append(row)
            tags.insert('', 'end', values=tuple(str(value) for value in row[:3]))
        fill(tag_detail, '')
        cues = []
        for cue in data.get('lyrics') or []:
            start = float(cue.get('start') or 0)
            end = cue.get('end')
            marker = f'{start:.2f}s' + (f'–{float(end):.2f}s' if end is not None else '')
            cues.append(marker + '\n' + str(cue.get('text') or ''))
        fill(lyrics, (str(data.get('lyric_source') or '') + '\n\n' if cues else '') +
             ('\n\n'.join(cues) if cues else 'No lyrics were found.'))
        fill(technical, (str(data.get('technical_error') or '') + '\n\n' if data.get('technical_error') else '') +
             json.dumps(data.get('technical') or {}, ensure_ascii=False, indent=2))
        artwork.configure(state='normal')
        artwork.delete('1.0', 'end')
        for index, blob in enumerate(art_bytes):
            try:
                from PIL import Image, ImageTk
                with Image.open(io.BytesIO(blob)) as original:
                    image = original.copy()
                image.thumbnail((600, 450))
                photo = ImageTk.PhotoImage(image, master=root)
            except (ImportError, OSError, ValueError):
                try:
                    photo = tk.PhotoImage(data=base64.b64encode(blob).decode('ascii'), master=root)
                except tk.TclError:
                    artwork.insert('end', f'Image {index + 1} is unavailable (install Pillow for JPEG artwork).\n\n')
                    continue
            images.append(photo)
            artwork.insert('end', f'Image {index + 1} of {len(art_bytes)}\n')
            artwork.image_create('end', image=photo)
            artwork.insert('end', '\n\n')
        if not art_bytes:
            artwork.insert('end', 'No artwork is available for this track.')
        artwork.configure(state='disabled')

    def refresh():
        if loading[0]:
            return
        loading[0] = True
        status.configure(text='Reading ' + server.label + '…')
        def worker():
            try:
                server.hello()
                data = server.json('/api/track-details', timeout=12)
                art = []
                for index in range(max(0, int(data.get('art_count') or 0))):
                    try:
                        art.append(server.image(int(data['art_generation']), index))
                    except Exception:
                        pass
                updates.put(('details', data, art, None))
            except Exception as exc:
                updates.put(('details', None, [], str(exc)))
        threading.Thread(target=worker, name='paf-tag-viewer-load', daemon=True).start()

    def complete(data, art, error):
        loading[0] = False
        if error:
            status.configure(text='Could not reach ' + server.label + ': ' + error)
        else:
            show(data, art)

    def poll():
        def worker():
            try:
                _identity, state = server.hello()
                identity = [str((state.get('track') or {}).get('path') or ''),
                            int(state.get('art_generation') or 0)]
                if identity != current_identity:
                    updates.put(('refresh', None, None, None))
            except Exception:
                updates.put(('disconnected', None, None, None))
        threading.Thread(target=worker, name='paf-tag-viewer-poll', daemon=True).start()
        root.after(3000, poll)

    def drain_updates():
        try:
            while True:
                kind, data, art, error = updates.get_nowait()
                if kind == 'details':
                    complete(data, art, error)
                elif kind == 'refresh':
                    refresh()
                elif kind == 'disconnected':
                    status.configure(text='Disconnected from ' + server.label)
        except queue.Empty:
            pass
        root.after(100, drain_updates)

    ttk.Button(heading, text='Refresh', command=refresh).pack(side='right')
    refresh()
    root.after(3000, poll)
    root.after(100, drain_updates)
    root.mainloop()
    return 0
