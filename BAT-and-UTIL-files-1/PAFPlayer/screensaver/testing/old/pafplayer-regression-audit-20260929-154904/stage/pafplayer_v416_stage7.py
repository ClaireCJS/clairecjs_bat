from pafplayer_v416_edit import edit, sub


def transform(s):
    s = sub(s, '        gap, word = match.groups()\n        proposal', '        gap, word = match.groups()\n        gap = re.sub(r"[\\r\\n\\t\\f\\v]+", " ", gap)\n        proposal')
    s = sub(s, '    if ARTWORK_SEAM_STRATEGY in {1, 4} and glyph:\n        return True', '    if ARTWORK_SEAM_STRATEGY in {1, 4} and glyph:\n        # While Chafa prepares, the fallback may still contain DRCS bytes.\n        return not (len(glyph) == 1 and 0x21 <= ord(glyph) <= 0x7E)')
    s = sub(s, '  <div class="control-grid" id="artworkSeamControls"></div>\n', '')
    s = sub(s, '<div class="toggle-grid" id="brokenControls"></div></div>', '<div class="toggle-grid" id="brokenControls"></div><div class="control-grid" id="artworkSeamControls"></div></div>')
    s = sub(s, '   if(age>1)return new Uint8Array(0);', '   if(age>4)return new Uint8Array(0);') if '   if(age>1)return' in s else sub(s, '  if(age>1)return new Uint8Array(0);', '  if(age>4)return new Uint8Array(0);')
    s = sub(s, 'speed:t.speed,playing:t.playing,at:received};', 'speed:t.speed,paused:!t.playing,playing:t.playing,at:received,validUntil:received+4000};')
    s = sub(s, '  if(t.source===\'stopped\'){spectrumTarget=[];spectrumCurrent=[];webClockSample.playing=false;}', '  if(t.source===\'stopped\'){spectrumTarget=[];spectrumCurrent=[];webClockSample.playing=false;webLyricTimeline=[];renderWebLyric(\'\');}')
    s = sub(s, 'if(sample.playing&&!sample.paused)position+=Math.max(0,now-sample.at)/1000', 'if(sample.playing&&!sample.paused)position+=Math.max(0,Math.min(now,sample.validUntil??now)-sample.at)/1000')
    old = '  if(clockReceivedAt-lastTimelineClockAt>500)webClockSample={position:Number(s.position_seconds||0)+clockAdvance,lyricPosition:Number(s.lyric_position_seconds??s.position_seconds??0)+clockAdvance,duration:Number(s.duration_seconds||0),progress:Number(s.progress||0),speed:Number(s.speed||1),paused:!!s.paused,playing:!!s.playing,karaokeOffset:Number(s.karaoke_offset_seconds||0),at:clockReceivedAt};'
    new = '''  // Status owns metadata even while the newer timeline owns the clock anchor.
  webClockSample={...webClockSample,duration:Number(s.duration_seconds||0),progress:Number(s.progress||0),karaokeOffset:Number(s.karaoke_offset_seconds||0)};
  if(clockReceivedAt-lastTimelineClockAt>500)webClockSample={...webClockSample,position:Number(s.position_seconds||0)+clockAdvance,lyricPosition:Number(s.lyric_position_seconds??s.position_seconds??0)+clockAdvance,speed:Number(s.speed||1),paused:!!s.paused,playing:!!s.playing,at:clockReceivedAt,validUntil:clockReceivedAt+4000};'''
    s = sub(s, old, new)
    s = sub(s, '    def publish_timeline(self, timeline, position, speed, sampled_at, *, playing=True, live=False, ui_start=0.0):', '''    def bind_timeline_clock(self, process, origin, speed, started, end, timeline_source):
        # HTTP readers follow audio independently when the console opens a menu.
        self._timeline_clock_binding = (process, origin, speed, started, end, timeline_source)

    def publish_timeline(self, timeline, position, speed, sampled_at, *, playing=True, live=False, ui_start=0.0):''')
    s = sub(s, '''        data, width, fps = timeline
        # Stalled owners cannot leave a browser animating an old track forever.
        age = max(0.0, time.monotonic() - at)
        position += min(age, 0.25) * speed if playing else 0.0
        playing = playing and age < 0.5''', '''        now = time.monotonic()
        binding = getattr(self, "_timeline_clock_binding", None)
        if binding is not None and playing:
            process, origin, speed, started, end, timeline_source = binding
            waiting = getattr(process, "playback_started_at", False) is None
            position = origin + audio_segment_elapsed(process, now, started, speed, waiting)
            if end is not None:
                position = min(end, position)
            playing = not waiting and process.poll() is None and (end is None or position < end)
            timeline = timeline_source()
        else:
            # Older publishers have no independent audio clock: bound their drift.
            age = max(0.0, now - at)
            position += min(age, 0.25) * speed if playing else 0.0
            playing = playing and age < 0.5
        data, width, fps = timeline''')
    s = sub(s, '            self._current_audio = path\n            self._state.update({', '            self._current_audio = path\n            self._timeline_sample = None\n            self._timeline_clock_binding = None\n            self._state.update({')
    s = sub(s, '    def finish_track(self, result: str) -> None:\n        self._timeline_sample = None', '    def finish_track(self, result: str) -> None:\n        self._timeline_clock_binding = None\n        self._timeline_sample = None')
    s = sub(s, '            self._current_audio = path\n            self._current_has_art = None', '            if self._current_audio != path:\n                self._karaoke_timeline = None\n                self._audio_clock_binding = None\n                self._playback_position = 0.0\n                self._playback_clock_speed = 0.0\n            self._current_audio = path\n            self._current_has_art = None')
    s = sub(s, '                external_album_art_window.set_playback_clock(process, position, speed, segment_started, playback_end)\n            segment_was_recorded', '                external_album_art_window.set_playback_clock(process, position, speed, segment_started, playback_end)\n            if web_server is not None:\n                web_server.bind_timeline_clock(process, position, speed, segment_started, playback_end, lambda: drcs_timeline)\n            segment_was_recorded')
    s = sub(s, '("INS/Q / Shift+INS", "add + queue next / multi-file picker")', '("J/INS/Q / Shift+INS", "Enter queues; Shift+Enter jumps / files")')
    s = sub(s, 'usage_line("INS / Q", "add audio to active playlist and queue it next using indexed word-any-order search + Tab completion")', 'usage_line("J / INS / Q", "search audio: Enter queues selected songs; Shift+Enter jumps; Ctrl+Space selects multiple rows")')
    s = sub(s, 'Playlist editing: INS or Q searches/adds/queues next;', 'Playlist editing: J/INS/Q searches; Enter queues, Shift+Enter jumps, Ctrl+Space selects;')
    return s


edit(transform)
