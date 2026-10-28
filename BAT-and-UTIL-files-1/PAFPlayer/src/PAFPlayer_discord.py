"""Opt-in Discord Rich Presence through desktop IPC or the Social SDK helper."""
import base64
from bisect import bisect_right
import ipaddress
import json
import math
import os
from pathlib import Path
import re
import struct
import subprocess
import threading
import time
import uuid
from urllib.parse import urlsplit


def application_id(runtime):
    value = str(runtime.settings.get('discord_application_id', '')).strip()
    if not re.fullmatch(r'\d{17,20}', value):
        raise ValueError('Enter the Application ID from a Discord Developer Portal application')
    return value


def _presence_text(value, limit=128):
    return re.sub(r'[\x00-\x1f\x7f\s]+', ' ', str(value or '')).replace('@', '＠').strip()[:limit]


def discord_lag_seconds(value):
    """Validate the requested real-time lead without accepting NaN or infinity."""
    if type(value) is bool:
        raise ValueError('Discord lag must be a number from 0 to 5 seconds')
    try:
        seconds = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError('Discord lag must be a number from 0 to 5 seconds') from exc
    if not math.isfinite(seconds) or not 0 <= seconds <= 5:
        raise ValueError('Discord lag must be a number from 0 to 5 seconds')
    return round(seconds, 2)


def discord_lyric_at(state, lag_seconds, now_epoch=None):
    """Choose the lyric that will be displayed after the configured lead time."""
    current = str(state.get('lyric') or '')
    if lag_seconds <= 0 or state.get('paused') or not state.get('playing'):
        return current
    timeline = state.get('lyric_timeline')
    if not isinstance(timeline, (list, tuple)) or not timeline:
        return current
    try:
        position = float(state.get('lyric_position_seconds', state.get('position_seconds', 0)))
        speed = float(state.get('speed', 1))
        offset = float(state.get('karaoke_offset_seconds', 0))
        epoch = float(state.get('lyric_clock_epoch', 0))
        clock = time.time() if now_epoch is None else float(now_epoch)
        if not all(math.isfinite(value) for value in (position, speed, offset, epoch, clock)):
            return current
        # Status is published every 200 ms. Cap clock extrapolation if playback
        # stalls so a stale snapshot cannot run many lyrics into the future.
        age = max(0.0, min(0.5, clock - epoch)) if epoch > 0 else 0.0
        target = max(0.0, position + (age + lag_seconds) * max(0.0, speed) + offset)
        index = bisect_right(timeline, target, key=lambda cue: float(cue[0])) - 1
        return str(timeline[index][1] or '') if index >= 0 else ''
    except (IndexError, TypeError, ValueError):
        return current


def _public_cover_url(value):
    """Accept only an uncredentialed, public HTTPS image address from tags."""
    url=str(value or '').strip()
    if not url or len(url)>300: return ''
    try:
        parts=urlsplit(url)
        host=(parts.hostname or '').casefold()
        if (parts.scheme.casefold()!='https' or not host or not parts.path or
                parts.username or parts.password or parts.port or parts.query or parts.fragment or
                any(char.isspace() or ord(char)<32 for char in url)): return ''
        try:
            if not ipaddress.ip_address(host).is_global: return ''
        except ValueError:
            if ('.' not in host or host=='localhost' or
                    host.endswith(('.local','.lan','.home','.internal','.test','.invalid','.example'))): return ''
    except ValueError:
        return ''
    return url


def _cover_asset(runtime, tags, path):
    """Use only explicit public art or an exact MusicBrainz release cover."""
    cache_key=(str(path) if path is not None else '',
               tuple(sorted((str(key),str(value)) for key,value in tags.items())))
    cached=getattr(runtime,'_discord_cover_cache',None)
    if cached is not None and cached[0]==cache_key:return cached[1]
    sources=[tags]
    probe=getattr(runtime.app,'probe_audio_raw_tags',None)
    if path is not None and callable(probe):
        try:sources.append(probe(path) or {})
        except (OSError,ValueError):pass
    merged={re.sub('[^a-z0-9]','',str(key).casefold()):value
            for source in sources if isinstance(source,dict) for key,value in source.items()}
    for key in ('albumarturl','artworkurl','coverarturl','coverimageurl'):
        url=_public_cover_url(merged.get(key))
        if url:
            runtime._discord_cover_cache=(cache_key,url)
            return url
    for key in ('musicbrainzalbumid','musicbrainzreleaseid'):
        value=str(merged.get(key,'')).strip()
        if re.fullmatch(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}',value):
            url='https://coverartarchive.org/release/'+str(uuid.UUID(value))+'/front-500'
            runtime._discord_cover_cache=(cache_key,url)
            return url
    runtime._discord_cover_cache=(cache_key,'')
    return ''


def public_activity(runtime):
    server=runtime.server
    if not server: return None,'Waiting for player'
    snapshot=getattr(server,'discord_snapshot',server.snapshot)
    state=snapshot(); track=state.get('track') or {}; tags=state.get('metadata') or state.get('tags') or {}
    if not isinstance(tags,dict): tags={}
    path=state['_audio_path'] if '_audio_path' in state else server.current_audio()
    private=bool(state.get('private')) or any('private' in str(tags.get(key,'')).casefold() for key in ('Genre','Comment','genre','comment'))
    if path and ('[private]' in str(path).casefold() or 'private' in [part.casefold() for part in path.parts]): private=True
    if private: return None,'Private track: profile activity cleared'
    if not runtime.settings.get('discord_share_local_titles'): return None,'Local titles are private; sharing is disabled'
    if not (state.get('playing') or state.get('paused')) or state.get('transport_stopped'):
        return None,'Stopped; profile activity cleared'
    title=str(track.get('title') or tags.get('Song') or tags.get('Title') or 'Untitled track')
    artist=str(track.get('artist') or tags.get('Act') or tags.get('Artist') or '')
    # Never fall back to a filename/path or transmit a local playback URL.
    album=_presence_text(tags.get('Album') or tags.get('album'))
    year=str(tags.get('Year') or tags.get('year') or tags.get('Date') or tags.get('date') or '').strip()
    year=year[:4] if re.match(r'^\d{4}(?:\D|$)',year) else ''
    # Discord owns the application name. Its two activity lines contain only
    # opted-in song metadata and the currently displayed lyric, respectively.
    parts=['🎵 '+_presence_text(title,40)]
    if artist:parts.append('👩‍🎤 '+_presence_text(artist,32))
    if album:parts.append('💿 '+_presence_text(album,28)+((' ('+year+')') if year else ''))
    try: lag=discord_lag_seconds(runtime.settings.get('discord_lag_seconds',0))
    except ValueError: lag=0.0
    lyric=_presence_text(discord_lyric_at(state,lag),126)
    activity={'details':' · '.join(parts)[:128],
              'state':'🎤 '+(lyric or '♪'),'instance':False}
    cover=_cover_asset(runtime,tags,path)
    if cover:
        activity['assets']={'large_image':cover,'large_text':_presence_text((album+' ('+year+')') if album and year else album or title)}
    return activity,'Ready'


class DiscordIPC:
    def __init__(self,client_id): self.client_id=client_id; self.pipe=None
    def _write(self,opcode,payload):
        data=json.dumps(payload,separators=(',',':')).encode('utf-8')
        self.pipe.write(struct.pack('<II',opcode,len(data))+data)
    def connect(self):
        self.close()
        for index in range(10):
            try:
                self.pipe=open(r'\\?\pipe\discord-ipc-'+str(index),'r+b',buffering=0)
                self._write(0,{'v':1,'client_id':self.client_id}); return
            except OSError: self.close()
        raise ConnectionError('Discord desktop IPC was not found; start Discord and try again')
    def set_activity(self,activity):
        if self.pipe is None: self.connect()
        self._write(1,{'cmd':'SET_ACTIVITY','args':{'pid':os.getpid(),'activity':activity},'nonce':uuid.uuid4().hex})
    def close(self):
        if self.pipe:
            try:self.pipe.close()
            except OSError:pass
        self.pipe=None


class SocialSDKProcess:
    """Small authenticated SDK process; OAuth credentials stay inside Windows Credential Manager."""
    def __init__(self, runtime, client_id):
        self.runtime=runtime; self.client_id=client_id; self.process=None
        self.lock=threading.RLock(); self.reader=None
        self.connected=False; self.authorization_required=False; self.authorizing=False
        self.publish_failed=False

    def _executable(self):
        override=getattr(self.runtime,'discord_social_helper_path',None)
        if override is not None: return Path(override)
        app_file=Path(getattr(self.runtime.app,'__file__',__file__)).resolve()
        return app_file.parent/'discord_social'/'PAFPlayerDiscordSocial.exe'

    def running(self):
        return self.process is not None and self.process.poll() is None

    def start(self):
        if self.running(): return
        exe=self._executable()
        if not exe.is_file() or not exe.with_name('discord_partner_sdk.dll').is_file():
            raise FileNotFoundError('Discord Social SDK helper is not installed; build it from the SDK download in discord_social')
        self.process=subprocess.Popen([str(exe),self.client_id],stdin=subprocess.PIPE,
                                      stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                                      text=True,encoding='utf-8',errors='replace',bufsize=1,
                                      creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        self.connected=False; self.authorization_required=False; self.publish_failed=False
        self.reader=threading.Thread(target=self._read_status,name='paf-discord-social-status',daemon=True)
        self.reader.start()

    def _read_status(self):
        process=self.process
        if process is None or process.stdout is None: return
        for raw in process.stdout:
            kind,separator,message=raw.rstrip('\r\n').partition('\t')
            if self.process is process and separator:
                if kind=='STATUS':
                    if message=='Discord profile update failed':self.publish_failed=True
                    elif message in ('Discord profile activity updated','Discord profile activity cleared'):
                        self.publish_failed=False
                    publisher=getattr(self.runtime,'discord',None)
                    if publisher is None or publisher.active_transport!='desktop_ipc':
                        self.runtime.discord_status=re.sub(r'[\x00-\x1f]+',' ',message)[:240]
                elif kind=='STATE':
                    self.connected=message=='READY'
                    self.authorization_required=message=='AUTH_REQUIRED'
                    if message=='AUTHORIZING':self.authorizing=True
                    elif self.connected or self.authorization_required:self.authorizing=False
        if self.process is process:self.connected=False
        if self.process is process and not self.runtime.stop_event.is_set():
            self.runtime.discord_status='Discord Social SDK helper stopped; retrying'

    def send(self,command,*fields):
        self.start()
        with self.lock:
            if not self.running() or self.process.stdin is None:
                raise ConnectionError('Discord Social SDK helper is not running')
            self.process.stdin.write('\t'.join((command,*fields))+'\n')
            self.process.stdin.flush()

    def set_activity(self,activity):
        if activity is None:
            self.send('CLEAR'); return
        encode=lambda value:base64.b64encode(str(value).encode('utf-8')).decode('ascii')
        assets=activity.get('assets') or {}
        self.send('SET',encode(activity['details']),encode(activity['state']),
                  encode(assets.get('large_image','')),encode(assets.get('large_text','')))

    def authorize(self): self.send('AUTHORIZE'); self.authorizing=True
    def forget(self): self.send('FORGET'); self.authorizing=False

    def close(self):
        process=self.process; self.process=None
        self.connected=False; self.authorizing=False
        if process is None: return
        try:
            if process.poll() is None and process.stdin:
                process.stdin.write('STOP\n'); process.stdin.flush()
            process.wait(timeout=3)
        except (OSError,subprocess.TimeoutExpired):
            if process.poll() is None:
                process.terminate()
                try: process.wait(timeout=2)
                except subprocess.TimeoutExpired: process.kill(); process.wait(timeout=2)
        finally:
            for stream in (process.stdin,process.stdout):
                if stream:
                    try: stream.close()
                    except OSError: pass


def social_sdk_available(runtime):
    exe=SocialSDKProcess(runtime,'0'*17)._executable()
    return exe.is_file() and exe.with_name('discord_partner_sdk.dll').is_file()


class Publisher:
    def __init__(self,runtime):
        self.runtime=runtime; self.stop=threading.Event(); self.last=object(); self.thread=None
        self.ipc=None; self.social=None; self.next_retry=0; self.lock=threading.RLock()
        self.active_transport=None; self.desktop_retry_at=0; self.last_ipc_write=0

    def tick(self,now=None):
        with self.lock:self._tick(now)

    def _tick(self,now=None):
        if not self.runtime.settings.get('discord_enabled'): return
        now=time.monotonic() if now is None else now
        if now<self.next_retry:return
        activity,status=public_activity(self.runtime)
        serialized=json.dumps(activity,sort_keys=True)
        try:
            client_id=application_id(self.runtime)
            transport=self.runtime.settings.get('discord_transport','desktop_ipc')
            if transport=='social_sdk':
                self._stop_ipc()
                self._publish_social(client_id,activity,serialized)
            elif transport=='automatic':
                self._tick_automatic(now,client_id,activity,serialized,status)
            else:
                self._stop_social()
                self._publish_ipc(now,client_id,activity,serialized,status)
        except Exception as exc:
            self._stop_ipc(clear=False); self._stop_social()
            self.next_retry=now+(15 if transport=='automatic' else 30)
            safe_message=(str(exc) if isinstance(exc,FileNotFoundError) and
                          'SDK helper is not installed' in str(exc) else
                          str(exc) if isinstance(exc,ConnectionError) and
                          'Discord desktop IPC was not found' in str(exc) else
                          'Discord connection failed ('+type(exc).__name__+'); retrying')
            if transport=='automatic':
                safe_message='Discord Desktop unavailable; '+safe_message
            self.runtime.discord_status=safe_message
            self.runtime.log('discord.profile-error',reason=type(exc).__name__,message=safe_message)

    def _stop_ipc(self,clear=True):
        if self.ipc is None:return
        if clear:
            try:self.ipc.set_activity(None)
            except (OSError,ConnectionError):pass
        self.ipc.close();self.ipc=None
        if self.active_transport=='desktop_ipc':self.active_transport=None
        self.last=object()

    def _stop_social(self):
        if self.social is None:return
        self.social.close();self.social=None
        if self.active_transport=='social_sdk':self.active_transport=None
        self.last=object()

    def _publish_ipc(self,now,client_id,activity,serialized,status):
        if self.ipc is None or self.ipc.client_id!=client_id:
            self._stop_ipc();self.ipc=DiscordIPC(client_id);self.last=object()
        if serialized!=self.last or now-self.last_ipc_write>=15:
            self.ipc.set_activity(activity);self.last=serialized;self.last_ipc_write=now
        self.active_transport='desktop_ipc'
        self.runtime.discord_status='Discord Desktop connected; profile activity updated' if activity else status

    def _publish_social(self,client_id,activity,serialized):
        if self.social is None or self.social.client_id!=client_id:
            self._stop_social();self.social=SocialSDKProcess(self.runtime,client_id);self.last=object()
        if not self.social.running():self.social.start();self.last=object()
        if serialized!=self.last:self.social.set_activity(activity);self.last=serialized
        self.active_transport='social_sdk'

    def _tick_automatic(self,now,client_id,activity,serialized,status):
        if self.active_transport=='desktop_ipc':
            try:
                self._publish_ipc(now,client_id,activity,serialized,status)
                return
            except (OSError,ConnectionError):
                self._stop_ipc(clear=False);self.desktop_retry_at=now+15
        if now>=self.desktop_retry_at:
            candidate=DiscordIPC(client_id)
            try:candidate.connect()
            except (OSError,ConnectionError):
                candidate.close();self.desktop_retry_at=now+15
            else:
                self._stop_social();self._stop_ipc(clear=False)
                self.ipc=candidate;self.last=object()
                try:
                    self._publish_ipc(now,client_id,activity,serialized,status)
                    return
                except (OSError,ConnectionError):
                    self._stop_ipc(clear=False);self.desktop_retry_at=now+15
        self._publish_social(client_id,activity,serialized)

    def start(self):
        if self.thread and self.thread.is_alive():return
        def run():
            while not self.stop.is_set() and not self.runtime.stop_event.is_set():
                self.tick(); self.stop.wait(.2)
            with self.lock:
                self._stop_ipc();self._stop_social()
        self.thread=threading.Thread(target=run,name='paf-discord-profile',daemon=True); self.thread.start()

    def authorize(self):
        with self.lock:return self._authorize()

    def _authorize(self):
        if not self.runtime.settings.get('discord_enabled') or self.runtime.settings.get('discord_transport') not in ('social_sdk','automatic'):
            raise ValueError('Enable Discord Social SDK profile activity and save before connecting your account')
        client_id=application_id(self.runtime)
        if self.social is None or self.social.client_id!=client_id:
            if self.social:self.social.close()
            self.social=SocialSDKProcess(self.runtime,client_id);self.last=object()
        self.social.authorize()
        self.runtime.discord_status='Discord account authorization opened in your browser'
        return {'ok':True,'status':self.runtime.discord_status}

    def forget(self):
        with self.lock:
            if self.runtime.settings.get('discord_transport') not in ('social_sdk','automatic'):
                raise ValueError('Choose the Discord Social SDK connection first')
            if self.social is None:self.social=SocialSDKProcess(self.runtime,application_id(self.runtime))
            self.social.forget()
            self.runtime.discord_status='Local Discord authorization removed'
            return {'ok':True,'status':self.runtime.discord_status}

    def close(self):
        self.stop.set()
        if self.thread and self.thread is not threading.current_thread():self.thread.join(timeout=5)
        with self.lock:
            self._stop_ipc();self._stop_social()


def connection_health(runtime):
    """Safe, actionable web status; instructions are empty while healthy or disabled."""
    enabled=bool(runtime.settings.get('discord_enabled'))
    mode=runtime.settings.get('discord_transport','desktop_ipc')
    publisher=getattr(runtime,'discord',None)
    if publisher is None:
        active=None;desktop=False;social=False;authorization_required=False;authorizing=False;publish_failed=False
    else:
        with publisher.lock:
            active=publisher.active_transport
            desktop=active=='desktop_ipc' and publisher.ipc is not None and publisher.ipc.pipe is not None
            social=(active=='social_sdk' and publisher.social is not None and
                    publisher.social.connected and not publisher.social.publish_failed)
            authorization_required=publisher.social is not None and publisher.social.authorization_required
            authorizing=publisher.social is not None and publisher.social.authorizing
            publish_failed=publisher.social is not None and publisher.social.publish_failed
    working=bool(desktop or social)
    advice=''
    if enabled:
        _,activity_status=public_activity(runtime)
        if activity_status=='Local titles are private; sharing is disabled':
            working=False;advice='Enable Allow titles/artists of local tracks to be shared if you want this song on your Discord profile.'
        elif not working:
            if not re.fullmatch(r'\d{17,20}',str(runtime.settings.get('discord_application_id','')).strip()):
                advice='Enter your Discord Application ID, then save the Discord profile choice.'
            elif mode=='desktop_ipc':
                advice='Start Discord Desktop on this computer, then check that its activity status is enabled.'
            elif active=='social_sdk' and publish_failed:
                advice='The Social SDK profile update failed. Check the Discord application and account authorization, then reconnect.'
            elif not social_sdk_available(runtime):
                prefix='Start Discord Desktop here, or ' if mode=='automatic' else ''
                advice=prefix+'enable Social SDK for your application in the Discord Developer Portal, download its Windows C++ SDK, and build the PAFPlayer helper.'
            elif authorizing:
                advice='Finish the Discord account authorization in your browser.'
            elif authorization_required:
                prefix='Start Discord Desktop here, or ' if mode=='automatic' else ''
                advice=prefix+'select Connect Discord account in this section.'
            else:
                prefix='Start Discord Desktop here, or ' if mode=='automatic' else ''
                advice=prefix+'check the Social SDK connection and Internet access; use Connect Discord account if authorization has expired.'
    return {'enabled':enabled,'working':working,'connection':active or 'none','instructions':advice}


def configure(runtime,payload):
    operation=payload.get('operation','save')
    if operation in ('authorize','forget'):
        publisher=getattr(runtime,'discord',None)
        if publisher is None:raise ValueError('Enable Discord profile activity and save before connecting your account')
        return publisher.authorize() if operation=='authorize' else publisher.forget()
    if operation!='save':raise ValueError('Unknown Discord operation')
    enabled=bool(payload.get('enabled',False))
    app_id=str(payload.get('application_id',runtime.settings.get('discord_application_id',''))).strip()
    if enabled and not re.fullmatch(r'\d{17,20}',app_id): raise ValueError('Enter a valid Discord Application ID before enabling profile activity')
    transport=str(payload.get('transport',runtime.settings.get('discord_transport','desktop_ipc')))
    if transport not in ('desktop_ipc','social_sdk','automatic'):raise ValueError('Choose a supported Discord connection method')
    lag=discord_lag_seconds(payload.get('lag_seconds',runtime.settings.get('discord_lag_seconds',0)))
    runtime.settings['discord_enabled']=enabled
    runtime.settings['discord_application_id']=app_id
    runtime.settings['discord_share_local_titles']=bool(payload.get('share_local_titles',False))
    runtime.settings['discord_transport']=transport
    runtime.settings['discord_lag_seconds']=lag
    runtime.save_settings()
    if enabled and not getattr(runtime,'discord',None): runtime.discord=Publisher(runtime); runtime.discord.start()
    if not enabled and getattr(runtime,'discord',None):runtime.discord.close();runtime.discord=None
    if enabled and getattr(runtime,'discord',None):runtime.discord.last=object();runtime.discord.next_retry=0
    runtime.discord_status=('Enabled; trying Discord Desktop, then Social SDK' if transport=='automatic'
                            else 'Enabled; connect your Discord account' if transport=='social_sdk'
                            else 'Enabled; waiting for Discord Desktop') if enabled else 'Disabled; profile activity cleared'
    return {'ok':True,'status':runtime.discord_status,'application_id':app_id,'lag_seconds':lag}
