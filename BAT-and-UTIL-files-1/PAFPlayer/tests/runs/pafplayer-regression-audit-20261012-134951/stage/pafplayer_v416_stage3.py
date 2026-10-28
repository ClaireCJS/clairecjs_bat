from pafplayer_v416_edit import edit, sub

def update(s):
    s = sub(s, '        self._spectrum_raw_bytes = b""\n        self._spectrum_raw_sequence = 0', '        self._spectrum_raw_bytes = b""\n        self._timeline_sample = None\n        self._spectrum_raw_sequence = 0')
    i = s.index('    def publish_spectrum_raw(self, spectrum)')
    s = s[:i] + '''    def publish_timeline(self, timeline, position, speed, sampled_at, *, playing=True, live=False, ui_start=0.0):
        # Immutable tuple publication; HTTP slicing/encoding never holds up audio.
        self._timeline_sample = (timeline, float(position), float(speed), float(sampled_at),
                                 bool(playing), bool(live), float(ui_start))

    def timeline_snapshot(self) -> dict[str, object]:
        sample = self._timeline_sample
        if sample is None:
            return {"source": "stopped", "frames": "", "playing": False}
        timeline, position, speed, at, playing, live, ui_start = sample
        data, width, fps = timeline
        # Stalled owners cannot leave a browser animating an old track forever.
        age = max(0.0, time.monotonic() - at)
        position += min(age, 0.25) * speed if playing else 0.0
        playing = playing and age < 0.5
        first = max(0, int(position * fps) - 1)
        last = min(len(data) // max(1, width), first + int(max(4.0, 4.0 * speed) * fps) + 2)
        return {"source": "live" if live else "track", "position": position,
                "ui_start": ui_start, "speed": speed, "playing": playing,
                "clock_epoch": time.time(), "start_frame": first, "fps": fps, "width": width,
                "frames": base64.b64encode(data[first * width:last * width] if not live else b"").decode("ascii")}

''' + s[i:]
    s = sub(s, '                if path == "/api/spectrum":', '''                if path == "/api/timeline":
                    owner.note_client_activity()
                    self._json(200, owner.timeline_snapshot())
                    return
                if path == "/api/spectrum":''')
    s = sub(s, '    def finish_track(self, result: str) -> None:\n', '    def finish_track(self, result: str) -> None:\n        self._timeline_sample = None\n        self._spectrum_raw_bytes = b""\n')
    # Publish the clock before potentially slow terminal / art work.
    s = sub(s, '                if external_album_art_window is not None:\n                    external_album_art_window.set_playback_position(displayed_position)', '''                if web_server is not None:
                    web_server.publish_timeline(drcs_timeline, displayed_position, speed, now,
                        playing=not buffered_clock_waiting, live=bool(live_visualizer_capture_mode(visualizer_input_source, False)),
                        ui_start=playback_start)
                if external_album_art_window is not None:
                    external_album_art_window.set_playback_position(displayed_position, speed=0.0 if buffered_clock_waiting else speed, sampled_at=now)''')
    # The pause loop has its own monotonic epoch and can use live microphone input.
    s = sub(s, '                        if web_server is not None and web_server.web_visualizer_active(paused_now)', '''                        if web_server is not None:
                            web_server.publish_timeline(drcs_timeline, position, 0.0, paused_now,
                                playing=False, live=bool(live_visualizer_capture_mode(visualizer_input_source, True)), ui_start=playback_start)
                        if web_server is not None and web_server.web_visualizer_active(paused_now)''')
    start = s.index('    def set_playback_position(self, position: float)')
    end = s.index('    def start_idle_routine', start)
    s = s[:start] + '''    def set_playback_position(self, position: float, *, speed: float = 0.0, sampled_at: float | None = None) -> None:
        """Publish a source-time anchor so Tk can meet deadlines between owner paints."""
        with self._lock:
            self._playback_position = max(0.0, float(position))
            self._playback_clock_speed = float(speed)
            self._playback_clock_at = time.monotonic() if sampled_at is None else sampled_at

    def playback_position(self) -> float:
        with self._lock:
            age = min(0.25, max(0.0, time.monotonic() - getattr(self, "_playback_clock_at", time.monotonic())))
            speed = getattr(self, "_playback_clock_speed", 0.0) if self._playback_running else 0.0
            return float(self._playback_position) + age * speed

''' + s[end:]
    # Future bytes arrive in one batch. At paint time choose source PTS, not the
    # newest network response or a FIFO of delayed worker frames.
    marker = 'function drawSpectrum(now){'
    i = s.index(marker)
    s = s[:i] + '''let spectrumTimeline=null,lastTimelineClockAt=-Infinity;
function timelineSpectrumAt(now){
  const t=spectrumTimeline;if(!t||t.source!=='track')return null;
  const age=Math.max(0,now-t.at)/1000;
  if(age>1)return new Uint8Array(0);
  const position=t.position+(t.playing?age*t.speed:0);
  const frame=position*t.fps-t.start_frame,index=Math.floor(frame),count=t.raw.length/t.width;
  if(index<0||index>=count)return new Uint8Array(0);
  const next=Math.min(count-1,index+1),blend=frame-index,result=new Uint8Array(t.width);
  for(let i=0;i<t.width;i++)result[i]=Math.round(t.raw[index*t.width+i]*(1-blend)+t.raw[next*t.width+i]*blend);
  return result;
}
async function timelineTick(){
 try{
  const requested=performance.now(),r=await fetch('/api/timeline',{cache:'no-store'}),t=await r.json(),received=performance.now();
  const serverNow=Number(r.headers.get('X-PAF-Server-Time')||t.clock_epoch||0);
  const transit=Math.min(.25,Math.max(0,serverNow-Number(t.clock_epoch||serverNow))+(received-requested)/2000);
  const raw=Uint8Array.from(atob(t.frames||''),c=>c.charCodeAt(0));
  t.position=Number(t.position||0)+(t.playing?transit*Number(t.speed||0):0);t.at=received;t.raw=raw;
  spectrumTimeline=t;
  if(t.source!=='live'&&t.source!=='stopped'){
   webClockSample={...webClockSample,position:Math.max(0,t.position-Number(t.ui_start||0)),lyricPosition:t.position,speed:t.speed,playing:t.playing,at:received};
   lastTimelineClockAt=received;
  }
  if(t.source==='stopped'){spectrumTarget=[];spectrumCurrent=[];webClockSample.playing=false;}
 }catch(e){}
 setTimeout(timelineTick,document.hidden?1000:150);
}

''' + s[i:]
    s = sub(s, '  const target=spectrumTarget||[];if(spectrumCurrent.length!==target.length)spectrumCurrent=target.slice();', '''  const scheduled=timelineSpectrumAt(now);
  if(scheduled!==null){
    spectrumTarget=browserSpectrumProcess(scheduled,spectrumOutputBins,Math.max(1,Number(latestState.visualizer_mode||1)),!!latestState.frequency_warp_enabled);
    spectrumCurrent=spectrumTarget.slice();
  }
  const target=spectrumTarget||[];if(spectrumCurrent.length!==target.length)spectrumCurrent=target.slice();''')
    s = sub(s, '  webClockSample={position:Number(s.position_seconds||0)', '  if(clockReceivedAt-lastTimelineClockAt>500)webClockSample={position:Number(s.position_seconds||0)')
    s = sub(s, " if(!webVisualizerEnabled || document.hidden){setTimeout(spectrumTick", " if(spectrumTimeline?.source==='track' || !webVisualizerEnabled || document.hidden){setTimeout(spectrumTick")
    # Start alongside the existing browser poll, exactly once.
    s = sub(s, 'async function spectrumTick(){', 'timelineTick();\nasync function spectrumTick(){')
    return s

edit(update)
