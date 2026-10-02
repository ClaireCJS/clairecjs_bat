"""Explicit opt-in Discord webhook publisher; secrets stay in the environment.

Protocol references: https://discord.com/developers/docs/resources/webhook and
https://discord.com/developers/docs/topics/rate-limits . Never logs webhook URLs.
"""
import json
import os
import re
import threading
import time
import urllib.error
import urllib.request


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None


def webhook_url():
    value=os.environ.get('PAFPLAYER_DISCORD_WEBHOOK','').strip()
    if not re.fullmatch(r'https://discord\.com/api(?:/v\d+)?/webhooks/\d+/[\w-]+',value):
        raise ValueError('Set PAFPLAYER_DISCORD_WEBHOOK to a Discord HTTPS webhook URL before enabling')
    return value


def public_content(runtime):
    server=runtime.server
    if not server: return None,'Waiting for player'
    state=server.snapshot(); track=state.get('track') or {}; tags=state.get('metadata') or state.get('tags') or {}
    if not isinstance(tags,dict): tags={}
    path=server.current_audio()
    private=bool(state.get('private')) or any('private' in str(tags.get(key,'')).casefold() for key in ('Genre','Comment','genre','comment'))
    if path and ('[private]' in str(path).casefold() or 'private' in [part.casefold() for part in path.parts]): private=True
    if private: return None,'Private track: not published'
    if not runtime.settings.get('discord_share_local_titles'): return None,'Local titles are private; sharing is disabled'
    if not state.get('playing') or state.get('transport_stopped'): return 'PAFPlayer stopped','Stopped'
    title=str(track.get('title') or tags.get('Song') or tags.get('Title') or 'Untitled track')
    artist=str(track.get('artist') or tags.get('Act') or tags.get('Artist') or '')
    # Never fall back to a filename/path or transmit a local playback URL.
    clean=lambda value: re.sub(r'[\r\n\x00-\x1f]+',' ',value).replace('@','＠')[:180]
    return ('Paused: ' if state.get('paused') else 'Now playing: ')+clean(title)+((' — '+clean(artist)) if artist else ''),'Ready'


class Publisher:
    def __init__(self,runtime):
        self.runtime=runtime; self.stop=threading.Event(); self.last=None; self.message_id=None; self.next_send=0.; self.thread=None
        self.opener=urllib.request.build_opener(NoRedirect())

    def tick(self,now=None):
        now=time.monotonic() if now is None else now
        if not self.runtime.settings.get('discord_enabled'): return
        content,status=public_content(self.runtime); self.runtime.discord_status=status
        if content is None:
            # Clear previously published metadata without exposing the private track.
            if self.message_id and self.last!='PAFPlayer — private playback': content='PAFPlayer — private playback'
            else: return
        if content==self.last or now<self.next_send: return
        self.next_send=now+15
        try:
            url=webhook_url()
            url+=(('/messages/'+self.message_id) if self.message_id else '?wait=true')
            request=urllib.request.Request(url,data=json.dumps({'content':content,'allowed_mentions':{'parse':[]}}).encode(),headers={'Content-Type':'application/json','User-Agent':'PAFPlayer opt-in Now Playing'},method='PATCH' if self.message_id else 'POST')
            with self.opener.open(request,timeout=5) as response:
                data=json.loads(response.read(65536)); self.message_id=str(data.get('id') or self.message_id or '') or None
            self.last=content; self.runtime.discord_status='Connected; last update accepted'
        except urllib.error.HTTPError as exc:
            if exc.code==429:
                try: delay=float(json.loads(exc.read(65536)).get('retry_after',60))
                except Exception: delay=60
                self.next_send=now+max(15,min(86400,delay)); self.runtime.discord_status='Rate limited; waiting before retry'
            else:
                self.next_send=now+60; self.runtime.discord_status=f'Discord rejected request (HTTP {exc.code})'
                if exc.code in (401,403,404):
                    self.runtime.settings['discord_enabled']=False; self.runtime.save_settings()
            self.runtime.log('discord.error',status=self.runtime.discord_status)
        except Exception:
            self.next_send=now+60; self.runtime.discord_status='Connection failed; retrying in 60 seconds'

    def start(self):
        def run():
            while not self.stop.is_set() and not self.runtime.stop_event.is_set():
                self.tick(); self.stop.wait(2)
        self.thread=threading.Thread(target=run,name='paf-discord',daemon=True); self.thread.start()


def configure(runtime,payload):
    enabled=bool(payload.get('enabled',False))
    if enabled: webhook_url()
    runtime.settings['discord_enabled']=enabled
    runtime.settings['discord_share_local_titles']=bool(payload.get('share_local_titles',False))
    runtime.save_settings()
    if enabled and not getattr(runtime,'discord',None): runtime.discord=Publisher(runtime); runtime.discord.start()
    runtime.discord_status='Enabled; waiting for next eligible track' if enabled else 'Disabled'
    return {'ok':True,'status':runtime.discord_status,'secret_configured':bool(os.environ.get('PAFPLAYER_DISCORD_WEBHOOK'))}
