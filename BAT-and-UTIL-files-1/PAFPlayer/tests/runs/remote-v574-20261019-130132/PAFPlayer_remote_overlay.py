"""Optional presentation windows on a tray-only computer.

Only the verified remote server supplies song state. Its published audio timestamp
and measured server clock offset drive lyrics independently on every client.
"""
from __future__ import annotations

import base64
import gc
from bisect import bisect_right
import io
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

    def _refresh_lyrics(self, lyric_renderer, state, enabled, epoch):
        """Reconcile transport frequently, but publish track/visibility transitions once."""
        if enabled != self._lyric_enabled:
            # Absolute state avoids queuing alternating toggles while Tk is busy.
            lyric_renderer.set_floating_lyrics_enabled(enabled)
            self._lyric_enabled = enabled
        if not enabled:
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
        )

    def _run(self):
        app = sys.modules.get('PAFPlayer') or sys.modules['__main__']
        # This is the player's renderer itself—not a tray-specific imitation.
        lyric_renderer = app.ExternalAlbumArtWindow(enabled=False)
        lyric_renderer.set_web_interface_url(self.server.url)
        try:
            import tkinter as tk
            root = tk.Tk()
        except Exception:
            lyric_renderer.close(fast=True)
            return
        root.withdraw()
        art = tk.Toplevel(root)
        art.title('PAFPlayer album art — this computer')
        art.attributes('-topmost', True)
        art.geometry('430x475+140+160')
        art.configure(bg='#171e28')
        art_label = tk.Label(art, bg='#171e28', fg='white')
        art_label.pack(fill='both', expand=True, padx=12, pady=12)
        caption = tk.Label(art, bg='#171e28', fg='white', font=('Segoe UI', 11))
        caption.pack(fill='x', padx=12, pady=8)
        art.protocol('WM_DELETE_WINDOW', lambda: self.machine.toggle('remote_album_art'))
        picture = None
        def refresh():
            nonlocal picture
            if self.stop.is_set():
                root.destroy()
                return
            lyric_on = self.machine.options.get('remote_floating_lyrics', False)
            art_on = self.machine.options.get('remote_album_art', False)
            if art_on and art.state() != 'normal': art.deiconify()
            if not art_on and art.state() != 'withdrawn': art.withdraw()
            state = self.server.snapshot() if self.server.connected else {}
            self._refresh_lyrics(lyric_renderer, state, lyric_on, time.time())
            if art_on:
                tags = state.get('metadata') or {}
                track = state.get('track') or {}
                caption.configure(text='%s — %s' % (tags.get('Artist') or tags.get('artist') or '—',
                                    tags.get('Song') or tags.get('title') or track.get('filename') or '—'))
                key = (self.server.owner_identity, state.get('art_generation')) if self.server.connected else None
                if key != self._last_art:
                    self._last_art = key
                    picture = None
                    art_label.configure(image='', text='Loading artwork…' if key else 'PAFPlayer disconnected')
                    if key and state.get('art_count'):
                        def fetch(expected):
                            try: data = self.server.image(int(expected[1]), 0)
                            except Exception: data = None
                            with self._art_lock:
                                if self._last_art == expected: self._art_bytes = (expected, data)
                        threading.Thread(target=fetch, args=(key,), daemon=True).start()
                with self._art_lock:
                    pending, self._art_bytes = self._art_bytes, None
                if pending and pending[0] == key and pending[1]:
                    try:
                        from PIL import Image, ImageTk
                        img = Image.open(io.BytesIO(pending[1]))
                        img.thumbnail((390, 390))
                        picture = ImageTk.PhotoImage(img, master=root)
                    except ImportError:
                        picture = tk.PhotoImage(data=base64.b64encode(pending[1]).decode('ascii'), master=root)
                    except Exception:
                        picture = None
                    art_label.configure(image=picture if picture else '', text='' if picture else 'Artwork unavailable')
            root.after(50, refresh)
        art.withdraw()
        root.after(0, refresh)
        try: root.mainloop()
        finally:
            lyric_renderer.close()
            try: root.destroy()
            except Exception: pass

    def close(self):
        self.stop.set()
        if self.thread and self.thread is not threading.current_thread(): self.thread.join(timeout=12)
