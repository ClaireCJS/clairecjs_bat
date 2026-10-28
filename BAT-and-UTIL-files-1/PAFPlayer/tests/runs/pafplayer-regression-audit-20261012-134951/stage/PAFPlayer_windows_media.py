"""Optional Windows SMTC publishing. Off until explicitly enabled; no audio owner.

Uses Microsoft's MediaPlayer.SystemMediaTransportControls with automatic command
management disabled. Windows chooses which shell/lock-screen surfaces show it.
Optional PyWinRT projections are loaded only when enabled.
"""
from PAFPlayer_workflows import *
from datetime import timedelta
import asyncio

DEFAULTS={'enabled':False,'artwork':True,'source':'primary','brightness':100,
          'play_pause':True,'previous_next':True,'seeking':True,'title_format':'artist-song',
          'album':True,'timeline':True}


def settings(runtime):
    result=dict(DEFAULTS);result.update(runtime.settings.get('windows_media',{}));return result


def presentation(state,options):
    track=state.get('track') or {};tags=state.get('metadata') or state.get('tags') or {}
    if not isinstance(tags,dict): tags={}
    song=str(track.get('title') or tags.get('Song') or tags.get('Title') or '')
    artist=str(track.get('artist') or tags.get('Act') or tags.get('Artist') or '')
    joined=' — '.join(x for x in (artist,song) if x)
    title={'artist-song':joined,'song-artist':' — '.join(x for x in (song,artist) if x),'song':song,'paf-artist-song':'PAFPlayer: '+joined}[options['title_format']]
    return {'title':title,'artist':artist,'album':str(track.get('album') or tags.get('Album') or '') if options['album'] else '',
            'position':max(0,float(state.get('position_seconds',0) or 0)), 'duration':max(0,float(state.get('duration_seconds',0) or 0))}


def artwork_bytes(runtime,options):
    if not options['artwork'] or options['source']=='none': return None
    server=runtime.server
    if not server: return None
    data=server.art_snapshot()[0]
    if options['source']=='current' and getattr(runtime,'current_artwork',None): data=runtime.current_artwork
    if not data: return None
    from PIL import Image,ImageEnhance,ImageOps
    with Image.open(io.BytesIO(data)) as source:
        image=ImageOps.contain(source.convert('RGB'),(600,600))
    image=ImageEnhance.Brightness(image).enhance(options['brightness']/100)
    out=io.BytesIO();image.save(out,format='PNG');return out.getvalue()


class Bridge:
    def __init__(self,runtime):
        self.runtime=runtime;self.thread=None;self.stop=threading.Event();self.active=False;self.backend=None
        self.status={'state':'Disabled','reason':'Experimental; enable to check Windows support','title':'','brightness':None}

    def configure(self,payload):
        options=settings(self.runtime)
        for key in DEFAULTS:
            if key not in payload: continue
            value=payload[key]
            if isinstance(DEFAULTS[key],bool):
                if not isinstance(value,bool): raise ValueError('Expected a checkbox value for '+key)
            elif key=='brightness': value=max(0,min(100,int(value)))
            options[key]=value
        if options['source'] not in ('primary','current','none') or options['title_format'] not in ('artist-song','song-artist','song','paf-artist-song'): raise ValueError('Invalid Windows display option')
        self.runtime.settings['windows_media']=options;self.runtime.save_settings();self.start()
        return {'settings':options,'status':self.status}

    def command(self,name,position=None):
        options=settings(self.runtime);server=self.runtime.server
        if not options['enabled'] or not server: return
        app=self.runtime.app
        if name in ('play','pause') and options['play_pause']: server.enqueue_action(app.WEB_PLAY if name=='play' else app.WEB_PAUSE)
        elif name in ('previous','next') and options['previous_next']: server.enqueue_action(app.PREVIOUS_FILE if name=='previous' else app.NEXT_FILE)
        elif name=='seek' and options['seeking'] and options['timeline']:
            duration=float(server.snapshot().get('duration_seconds') or 0)
            if duration>0: server.enqueue_action(app.WEB_SEEK_RATIO_PREFIX+str(max(0,min(1,float(position)/duration))))

    def connect(self):
        from winrt.windows.media.playback import MediaPlayer
        from winrt.windows.media import MediaPlaybackType,MediaPlaybackStatus,SystemMediaTransportControlsTimelineProperties,SystemMediaTransportControlsButton
        from winrt.windows.storage.streams import InMemoryRandomAccessStream,DataWriter,RandomAccessStreamReference
        player=MediaPlayer();player.command_manager.is_enabled=False
        controls=player.system_media_transport_controls
        mapping={SystemMediaTransportControlsButton.PLAY:'play',SystemMediaTransportControlsButton.PAUSE:'pause',SystemMediaTransportControlsButton.NEXT:'next',SystemMediaTransportControlsButton.PREVIOUS:'previous'}
        button=controls.add_button_pressed(lambda sender,args:self.command(mapping.get(args.button,'')))
        seek=controls.add_playback_position_change_requested(lambda sender,args:self.command('seek',args.requested_playback_position.total_seconds()))
        self.backend=(player,controls,MediaPlaybackType,MediaPlaybackStatus,SystemMediaTransportControlsTimelineProperties,InMemoryRandomAccessStream,DataWriter,RandomAccessStreamReference,button,seek)

    def tick(self):
        options=settings(self.runtime)
        if not options['enabled']:
            if self.backend:self.backend[1].is_enabled=False
            self.active=False;self.status={'state':'Disabled','reason':'Windows integration is off','title':'','brightness':None};return
        if not self.backend:self.connect()
        player,c,types,statuses,timeline_type,stream_type,writer_type,reference_type,*_=self.backend
        server=self.runtime.server
        if not server:return
        state=server.snapshot();value=presentation(state,options)
        c.is_enabled=True;c.is_play_enabled=options['play_pause'];c.is_pause_enabled=options['play_pause']
        c.is_next_enabled=options['previous_next'];c.is_previous_enabled=options['previous_next']
        c.playback_status=statuses.PAUSED if state.get('paused') else statuses.PLAYING if state.get('playing') else statuses.STOPPED
        signature=(value['title'],value['artist'],value['album'],options['source'],options['artwork'],options['brightness'],getattr(self.runtime,'current_artwork_revision',0))
        if signature!=getattr(self,'signature',None):
            updater=c.display_updater;updater.type=types.MUSIC
            updater.music_properties.title=value['title'];updater.music_properties.artist=value['artist'];updater.music_properties.album_title=value['album']
            data=artwork_bytes(self.runtime,options)
            if data:
                async def thumbnail():
                    stream=stream_type();writer=writer_type(stream);writer.write_bytes(data);await writer.store_async();writer.detach_stream();stream.seek(0)
                    return reference_type.create_from_stream(stream),stream
                reference,self.stream=asyncio.run(thumbnail());updater.thumbnail=reference
            else:updater.thumbnail=None
            updater.update();self.signature=signature
        timeline=timeline_type();duration=value['duration'] if options['timeline'] else 0
        timeline.start_time=timedelta(0);timeline.end_time=timedelta(seconds=duration)
        timeline.min_seek_time=timedelta(0);timeline.max_seek_time=timedelta(seconds=duration if options['seeking'] else 0)
        timeline.position=timedelta(seconds=min(duration,value['position']));c.update_timeline_properties(timeline)
        self.active=True;self.status={'state':'Active','reason':'Published to Windows; shell decides lock-screen visibility','title':value['title'],'brightness':options['brightness'] if options['artwork'] and options['source']!='none' else None}

    def start(self):
        if self.thread:return
        def run():
            try:
                while not self.stop.is_set() and not self.runtime.stop_event.is_set():
                    try:self.tick()
                    except Exception as exc:
                        self.active=False
                        self.status={'state':'Unavailable','reason':'Optional PyWinRT Windows.Media and Storage.Streams packages are not installed' if isinstance(exc,ImportError) else type(exc).__name__+': '+str(exc)[:160],'title':'','brightness':None}
                        if self.backend:
                            with contextlib.suppress(Exception):self.backend[1].is_enabled=False
                    self.stop.wait(1)
            finally:
                if self.backend:
                    with contextlib.suppress(Exception):
                        self.backend[1].is_enabled=False;self.backend[1].remove_button_pressed(self.backend[-2]);self.backend[1].remove_playback_position_change_requested(self.backend[-1]);self.backend[0].close()
        self.thread=threading.Thread(target=run,name='paf-windows-media',daemon=True);self.thread.start()

    def close(self):
        self.stop.set()
        if self.thread:self.thread.join(timeout=1.5)
