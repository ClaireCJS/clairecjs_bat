from pafplayer_v416_edit import edit, sub

def update(s):
    s = sub(s, 'SPECTRUM_ANALYSIS_AHEAD_SECONDS   = 2.5', 'SPECTRUM_ANALYSIS_AHEAD_SECONDS   = 12.0')
    s = sub(s, '"v26-agc-two-bin-analysis",', '"v416-silence-safe-timeline",')
    i = s.index('class MatrixMixerInspiredWaveOutProcess:')
    s = s[:i] + '''class _MMTimeValue(ctypes.Union):
    _fields_ = [("value", ctypes.c_uint32), ("smpte", ctypes.c_byte * 8)]


class _MMTime(ctypes.Structure):
    _fields_ = [("wType", ctypes.c_uint32), ("u", _MMTimeValue)]


def audio_segment_elapsed(process, now: float, started: float, speed: float, waiting=False) -> float:
    """Source seconds from the device clock, with a bounded IPC extrapolation.

    Legacy FFplay exposes no consumed-sample counter and retains its startup
    estimate. Buffered audio never substitutes time since decode/queue for time
    actually consumed by the output device.
    """
    sample = getattr(process, "playback_clock", None)
    if isinstance(sample, dict) and sample.get("seconds") is not None:
        age = max(0.0, float(now) - float(sample["at"]))
        advance = min(age, 0.15, max(0.0, float(sample.get("queued_seconds", 0.0))))
        return max(0.0, float(sample["seconds"]) + advance) * speed
    return 0.0 if waiting else max(0.0, float(now) - float(started)) * speed


''' + s[i:]
    s = sub(s, '        w.waveOutGetErrorTextW.argtypes', '''        w.waveOutGetPosition.argtypes = [ctypes.c_void_p, ctypes.POINTER(_MMTime), ctypes.c_uint32]
        w.waveOutGetPosition.restype = ctypes.c_uint32
        w.waveOutGetErrorTextW.argtypes''')
    i = s.index('    @property\n    def queued_audio_ms', s.index('class MatrixMixerInspiredWaveOutProcess:'))
    s = s[:i] + '''    @property
    def playback_clock(self) -> dict[str, float] | None:
        if self._playback_started_at is None or not self._wave_handle:
            return None
        stamp = _MMTime()
        stamp.wType = 2  # TIME_SAMPLES; drivers may return MS or bytes instead.
        at = time.monotonic()
        if self._winmm.waveOutGetPosition(self._wave_handle, ctypes.byref(stamp), ctypes.sizeof(stamp)):
            return None
        divisor = {1: 1000.0, 2: float(self.sample_rate),
                   4: float(self.sample_rate * self.channels * (self.container_bits // 8))}.get(stamp.wType)
        if divisor is None:
            return None
        # Unwrap the driver's DWORD counter for long uninterrupted sessions.
        previous_type, previous_raw, wraps = getattr(self, "_clock_counter", (stamp.wType, 0, 0))
        raw = int(stamp.u.value)
        if previous_type == stamp.wType and previous_raw - raw > 0x80000000:
            wraps += 1
        elif previous_type != stamp.wType:
            wraps = 0
        self._clock_counter = (stamp.wType, raw, wraps)
        seconds = (raw + wraps * 0x100000000) / divisor - self.initial_delay_ms / 1000.0
        return {"seconds": max(0.0, seconds), "at": at,
                "queued_seconds": self.queued_audio_ms / 1000.0}

''' + s[i:]
    s = sub(s, '            meters = matrix_output_levels_snapshot()\n            send({', '''            meters = matrix_output_levels_snapshot()
            # The first selected endpoint is the timing reference. Its optional
            # leading calibration silence is already removed by playback_clock.
            clock_sample = getattr(processes[0], "playback_clock", None) if processes else None
            send({
                "clock": clock_sample if isinstance(clock_sample, dict) else None,''')
    s = sub(s, '            stop.wait(0.02 if started is None else 0.1)', '            stop.wait(0.02)')
    s = sub(s, '                if "queued_ms" in message:', '''                if isinstance(message.get("clock"), dict):
                    self._clock_sample = message["clock"]
                if "queued_ms" in message:''')
    i = s.index('    @property\n    def audio_health', s.index('class IsolatedWaveOutProcess:'))
    s = s[:i] + '''    @property
    def playback_clock(self):
        return getattr(self, "_clock_sample", None)

''' + s[i:]
    s = sub(s, '                elapsed = 0.0 if buffered_clock_waiting else max(0.0, now - segment_started) * speed', '                elapsed = audio_segment_elapsed(process, now, segment_started, speed, buffered_clock_waiting)')
    s = sub(s, '        live = position + max(0.0, monotonic() - segment_started) * PLAYBACK_SPEEDS[speed_index]', '        live = position + audio_segment_elapsed(process, monotonic(), segment_started, PLAYBACK_SPEEDS[speed_index], getattr(process, "playback_started_at", False) is None)')
    s = sub(s, '\n                        lyric_clock_epoch=time.time(),', '\n                        lyric_clock_epoch=time.time() - max(0.0, monotonic() - now),')
    # Same source clock for cached beats, independent of paint cadence and seeks.
    i = s.index('\ndef write_console(text: str)')
    s = s[:i] + '''
class ProgressBeatTimeline:
    """Precompute all five detectors off the render thread, indexed by source PTS."""
    def __init__(self):
        self.states = [{} for _ in PROGRESS_BEAT_DETECTOR_NAMES]
        self.samples = bytearray()
        self.fps = SPECTRUM_ANALYSIS_FPS

    def append(self, data: bytes, width: int, fps: int):
        self.fps = fps
        batch = bytearray()
        for offset in range(0, len(data) - width + 1, width):
            levels = data[offset:offset + width]
            for index, state in enumerate(self.states):
                batch.append(round(255 * progress_beat_pulse(levels, state, 1.0 / fps, index + 1)))
        self.samples.extend(batch)

    def at(self, position: float, detector: int) -> float:
        index = max(0, int(position * self.fps)) * len(self.states) + detector - 1
        return self.samples[index] / 255.0 if 0 <= index < len(self.samples) else 0.0

''' + s[i:]
    s = sub(s, '    progress_beat_state: dict[str, object] = {"baseline": 0.0, "pulse": 0.0}', '    progress_beat_timeline = ProgressBeatTimeline()\n    progress_beat_state: dict[str, object] = {"baseline": 0.0, "pulse": 0.0}')
    s = sub(s, '            progress_beat_pulse(progress_levels, progress_beat_state, beat_delta, progress_beat_detector)\n            if progress_beat_reactive', '''            (progress_beat_pulse(progress_levels, progress_beat_state, beat_delta, progress_beat_detector)
             if desired_live_mode else progress_beat_timeline.at(current_position, progress_beat_detector))
            if progress_beat_reactive''')
    s = sub(s, '                accumulated.extend(chunk_data)', '                progress_beat_timeline.append(bytes(chunk_data), width, fps)\n                accumulated.extend(chunk_data)')
    s = sub(s, '''                    if len(chunk_data) >= width:
                        last_frame = bytes(chunk_data[-width:])
                    else:
                        last_frame = bytes(width)''', '                    last_frame = bytes(width)')
    # Cached files still need off-thread pulse preparation; no repeated FFT.
    s = sub(s, '            offset = 0.0\n            accumulated = bytearray()', '''            if cached_spectrum is not None:
                data, width, fps = cached_spectrum
                chunk_bytes = width * fps * 3
                for start in range(0, len(data), chunk_bytes):
                    if abort_requested.is_set():
                        return
                    progress_beat_timeline.append(data[start:start + chunk_bytes], width, fps)
                return
            offset = 0.0
            accumulated = bytearray()''')
    s = sub(s, 'if (drcs_enabled or web_server is not None) and cached_spectrum is None and not disable_spectrum_analyzer:', 'if (drcs_enabled or web_server is not None or progress_bar_enabled) and not disable_spectrum_analyzer:')
    return s

edit(update)
