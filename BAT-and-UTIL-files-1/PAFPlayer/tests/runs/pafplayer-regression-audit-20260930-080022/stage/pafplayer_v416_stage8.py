from pafplayer_v416_edit import edit, sub


def transform(s):
    s = sub(s, '        self._wave_handle = ctypes.c_void_p()\n        self._winmm', '        self._wave_handle = ctypes.c_void_p()\n        self._wave_handle_lock = threading.RLock()\n        self._last_playback_clock = None\n        self._winmm')
    s = sub(s, '''            if self._stop.is_set():
                with contextlib.suppress(Exception):
                    self._winmm.waveOutReset(self._wave_handle)
            with contextlib.suppress(Exception):
                self._winmm.waveOutClose(self._wave_handle)
            self._wave_handle = ctypes.c_void_p()''', '''            self._close_waveout()''')
    s = sub(s, '''    @property
    def playback_clock(self) -> dict[str, float] | None:
        if self._playback_started_at is None or not self._wave_handle:
            return None''', '''    def _close_waveout(self) -> None:
        # WinMM may dereference a freed handle if GetPosition overlaps Close.
        with getattr(self, "_wave_handle_lock", contextlib.nullcontext()):
            with contextlib.suppress(OSError):
                self._sample_playback_clock()
            if self._stop.is_set():
                with contextlib.suppress(Exception):
                    self._winmm.waveOutReset(self._wave_handle)
            with contextlib.suppress(Exception):
                self._winmm.waveOutClose(self._wave_handle)
            self._wave_handle = ctypes.c_void_p()
            if getattr(self, "_last_playback_clock", None) is not None:
                self._last_playback_clock = {**self._last_playback_clock, "queued_seconds": 0.0}

    @property
    def playback_clock(self) -> dict[str, float] | None:
        with getattr(self, "_wave_handle_lock", contextlib.nullcontext()):
            try:
                return self._sample_playback_clock()
            except OSError:
                return getattr(self, "_last_playback_clock", None)

    def _sample_playback_clock(self) -> dict[str, float] | None:
        if self._playback_started_at is None or not self._wave_handle:
            return getattr(self, "_last_playback_clock", None)''')
    s = sub(s, '''        return {"seconds": seconds, "at": at,
                "queued_seconds": self.queued_audio_ms / 1000.0}''', '''        self._last_playback_clock = {"seconds": seconds, "at": at,
                "queued_seconds": self.queued_audio_ms / 1000.0}
        return self._last_playback_clock''')
    s = sub(s, '''        with contextlib.suppress(Exception):
            self._winmm.waveOutReset(self._wave_handle)
        with contextlib.suppress(Exception):
            self._ffmpeg.''', '''        with getattr(self, "_wave_handle_lock", contextlib.nullcontext()):
            with contextlib.suppress(Exception):
                self._winmm.waveOutReset(self._wave_handle)
        with contextlib.suppress(Exception):
            self._ffmpeg.''', count=2)
    return s


edit(transform)
