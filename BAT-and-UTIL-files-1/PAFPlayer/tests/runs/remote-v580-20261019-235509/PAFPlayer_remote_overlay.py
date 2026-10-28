"""Optional presentation windows on a tray-only computer.

Only the verified remote server supplies song state. Its published audio timestamp
and measured server clock offset drive lyrics independently on every client.
"""
from __future__ import annotations

import gc
import queue
from bisect import bisect_right
import sys
import threading
import time

from PAFPlayer_remote_tray import synchronized_position


def lyric_at(state, epoch, offset=0.0):
    timeline = state.get('lyric_timeline') or []
    if not isinstance(timeline, list) or not timeline:
        return str(state.get('lyric') or '')
    at = synchronized_position(state, epoch, offset) + float(state.get('karaoke_offset_seconds') or 0)
    try:
        index = bisect_right(timeline, at, key=lambda row: float(row[0])) - 1
        return str(timeline[index][1] or '') if index >= 0 else ''
    except (ValueError, TypeError, IndexError):
        return str(state.get('lyric') or '')


class RemoteOverlays:
    def __init__(self, server, machine):
        self.server, self.machine = server, machine
        self.stop = threading.Event()
        self.thread = None
        self._last_art = None
        self._art_bytes = None
        self._art_lock = threading.Lock()
        self._lyric_enabled = None
        self._lyric_track_key = None
        self._art_enabled = None
        self._presentation_key = None
        self._requests = queue.Queue(maxsize=16)
        self._fetch_wake = threading.Event()
        self._wanted_art = None
        self._fetch_thread = None

    def start(self):
        if self.thread and self.thread.is_alive(): return
        self.thread = threading.Thread(target=self._thread_entry, name='paf-remote-overlays', daemon=True)
        self.thread.start()

    def _thread_entry(self):
        try:
            self._run()
        finally:
            # Drop this thread's Tk closure cycles here, after the lyric renderer
            # has finished destroying its separate interpreter on its own thread.
            gc.collect()

    def _refresh_lyrics(self, lyric_renderer, state, enabled, epoch, *, artwork=False):
        """Reconcile transport frequently, but publish track/visibility transitions once."""
        if enabled != self._lyric_enabled:
            # Absolute state avoids queuing alternating toggles while Tk is busy.
            lyric_renderer.set_floating_lyrics_enabled(enabled)
            self._lyric_enabled = enabled
        if not enabled and not artwork:
            return
        connected = self.server.connected
        position = synchronized_position(state, epoch, self.server.clock_offset)
        running = bool(connected and state.get('playing')
                       and not state.get('paused') and not state.get('transport_stopped'))
        speed = float(state.get('speed') or 1.0) if running else 0.0
        lyric_renderer.set_playback_running(running)
        lyric_renderer.set_playback_position(position, speed=speed)
        lyric_renderer.set_spectrum_ready_for_art_karaoke(True)
        tags = state.get('metadata') or {}
        track = state.get('track') or {}
        artist = tags.get('Artist') or tags.get('artist') or ''
        title = tags.get('Song') or tags.get('title') or track.get('filename') or ''
        key = (self.server.owner_identity, track.get('path'), artist, title) if connected else None
        if key != self._lyric_track_key:
            self._lyric_track_key = key
            lyric_renderer.update_track_identity(artist, title)
        lyric_renderer.update_lyric(
            lyric_at(state, epoch, self.server.clock_offset) if connected else 'PAFPlayer disconnected',
            float(state.get('lyric_progress') or 0.0),
            emojimax=bool(state.get('karaoke_emojimax')),
            decensor_floating=bool(state.get('decensor_floating_lyrics')),
            **({'decensor_artwork': bool(state.get('decensor_artwork_lyrics'))} if artwork else {}),
        )

    def options(self, tray, stop_event):
        self.start()
        try: self._requests.put_nowait(('options', (tray, stop_event)))
        except queue.Full: pass

    def configure(self, target):
        self.start()
        try: self._requests.put_nowait(('configure', target))
        except queue.Full: pass

    def center(self, floating):
        self.start()
        try: self._requests.put_nowait(('center', bool(floating)))
        except queue.Full: pass

    def _fetch_art(self):
        """One download worker, one latest result; superseded covers are discarded."""
        while not self.stop.is_set():
            self._fetch_wake.wait(.5)
            self._fetch_wake.clear()
            with self._art_lock:
                request = self._wanted_art
            if not request:
                continue
            key, count = request
            variants = []
            total = 0
            for index in range(min(8, max(0, count))):
                with self._art_lock:
                    stale = request != self._wanted_art
                if stale or self.stop.is_set(): break
                try: data = self.server.image(int(key[1]), index)
                except Exception: data = None
                if data:
                    total += len(data)
                    if total > 64 * 1024 * 1024: break
                    variants.append(data)
            with self._art_lock:
                if request == self._wanted_art:
                    self._art_bytes = (key, variants)
                    self._wanted_art = None

    def _run(self):
        app = sys.modules.get('PAFPlayer') or sys.modules['__main__']
        renderer = app.ExternalAlbumArtWindow(enabled=False)
        renderer.set_web_interface_url(self.server.url)
        settings = self.machine.settings
        self._fetch_thread = threading.Thread(target=self._fetch_art, name='paf-remote-art-fetch', daemon=True)
        self._fetch_thread.start()
        check_settings_at = 0.0
        try:
            while not self.stop.is_set():
                state = self.server.snapshot() if self.server.connected else {}
                now = time.monotonic()
                if now >= check_settings_at:
                    check_settings_at = now + .5
                    settings.set_server_preferences(state.get('remote_presentation'))
                    key = settings.presentation_key()
                    if key != self._presentation_key:
                        self._presentation_key = key
                        renderer.reload_remote_presentation()
                lyric_on = bool(self.machine.options.get('remote_floating_lyrics'))
                art_on = bool(self.machine.options.get('remote_album_art'))
                if self._art_enabled is True and art_on and not renderer.enabled:
                    # Closing the native popup should also uncheck its tray option.
                    self.machine.toggle('remote_album_art')
                    art_on = False
                if art_on != self._art_enabled:
                    if art_on: self._last_art = object()  # Retry covers discarded while the popup was off.
                    renderer.set_enabled(art_on)
                    self._art_enabled = art_on
                self._refresh_lyrics(renderer, state, lyric_on, time.time(), artwork=art_on)
                art_key = (self.server.owner_identity, state.get('art_generation')) if self.server.connected else None
                if art_on and art_key != self._last_art:
                    self._last_art = art_key
                    renderer.update_remote_artwork([])
                    with self._art_lock:
                        self._art_bytes = None
                        self._wanted_art = (art_key, int(state.get('art_count') or 0)) if art_key else None
                    self._fetch_wake.set()
                with self._art_lock:
                    pending, self._art_bytes = self._art_bytes, None
                if art_on and pending and pending[0] == art_key:
                    renderer.update_remote_artwork(pending[1])
                try: action, value = self._requests.get_nowait()
                except queue.Empty: pass
                else:
                    if action == 'options': renderer.open_tray_options(value[0], self, value[1])
                    elif action == 'configure': renderer.open_karaoke_color_configurator(value)
                    elif action == 'center': renderer.bring_to_center(floating=value)
                self.stop.wait(.05)
        finally:
            renderer.close()
            self._fetch_wake.set()
            self._fetch_thread.join(timeout=6)

    def close(self):
        self.stop.set()
        self._fetch_wake.set()
        if self.thread and self.thread is not threading.current_thread(): self.thread.join(timeout=15)
