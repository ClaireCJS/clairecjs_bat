from pafplayer_v416_edit import edit, sub, replace_file, ROOT

def update(s):
    s=sub(s,'PLAYER_BUILD_ID                 = "2026-09-09-v408-shuffle-loop-state-clarity"','PLAYER_BUILD_ID                 = "2026-09-15-v416-timestamped-timelines-and-todos"')
    s=sub(s,'PROGRAM_RELEASE_LABEL           = "V400"','PROGRAM_RELEASE_LABEL           = "V416"')
    s=sub(s,'# CHAT ARTIFACT BUILD: 2026-09-14-V416-TIMELINE-TODOS-AND-KARAOKE-SPACING','# CHAT ARTIFACT BUILD: 2026-09-15-V416-TIMELINE-TODOS-AND-KARAOKE-SPACING')
    s=sub(s,'            positive_flux = 0.0\n        state["spectrum"]', '            positive_flux = sum(normalized) / n\n        state["spectrum"]')
    s=sub(s,'        return {"seconds": max(0.0, seconds), "at": at,','        return {"seconds": seconds, "at": at,')
    s=sub(s,'        if key in {" ", "\\x00"} and ctrl and not alt:', '        if ctrl and not alt and (key == " " or (key == "\\x00" and _windows_key_down(0x20))):')
    s=sub(s,'self.suppress_until = now + 0.20','self.suppress_until = now + 1.0')
    s=sub(s,'            while not lastfm_now_playing_finished.wait(0.05):\n                if abort_requested.is_set():\n                    return','''            # Artwork/lyrics must not wait indefinitely for a network scrobble.
            # The detached native analyzer no longer needs the historical
            # unbounded Last.fm startup gate.
            lastfm_now_playing_finished.wait(0.05)
            if abort_requested.is_set():
                return''')
    s=sub(s,'    merged.update({str(phrase): str(glyph) for phrase, glyph in SEMANTIC_PHRASES.items()})','    merged.update({word: emojimax_replacement_for_key(word) for word in EMOJIMAX_BASE_SUFFIX})\n    merged.update({str(phrase): str(glyph) for phrase, glyph in SEMANTIC_PHRASES.items()})')
    # Keep Chafa off the paint thread. Quantize once per image and cell geometry;
    # saturation autoslides scale its cached colors without relaunching Chafa.
    s=sub(s,'def chafa_symbol_art_cells(grid, columns, rows):','def _render_chafa_symbol_art_cells(grid, columns, rows):')
    i=s.index('def _render_chafa_symbol_art_cells')
    s=s[:i]+'''_CHAFA_SYMBOL_CACHE = {}
_CHAFA_SYMBOL_PENDING = set()
_CHAFA_SYMBOL_LOCK = threading.Lock()


def chafa_symbol_art_cells(grid, columns, rows):
    key = (id(grid), columns, rows, terminal_cell_pixel_size_nonintrusive())
    with _CHAFA_SYMBOL_LOCK:
        cached = _CHAFA_SYMBOL_CACHE.get(key)
        if cached is not None and cached[0] is grid:
            return cached[1]
        if key in _CHAFA_SYMBOL_PENDING:
            return ()
        _CHAFA_SYMBOL_PENDING.add(key)
    def prepare():
        try:
            result = _render_chafa_symbol_art_cells(grid, columns, rows)
            with _CHAFA_SYMBOL_LOCK:
                if len(_CHAFA_SYMBOL_CACHE) >= 4:
                    _CHAFA_SYMBOL_CACHE.pop(next(iter(_CHAFA_SYMBOL_CACHE)))
                _CHAFA_SYMBOL_CACHE[key] = (grid, result)
            # Discard the temporary ordinary-glyph fallback when Chafa is ready.
            _VISUALIZER_ART_DETAIL_GRID_CACHE.clear()
            _VISUALIZER_ART_CELL_STYLE_CACHE.clear()
        finally:
            with _CHAFA_SYMBOL_LOCK:
                _CHAFA_SYMBOL_PENDING.discard(key)
    threading.Thread(target=prepare, name="paf-chafa-symbols", daemon=True).start()
    return ()


'''+s[i:]
    s=sub(s,'chafa_symbol_art_cells(scaled, terminal_width, source_rows)', 'chafa_symbol_art_cells(grid, terminal_width, source_rows)')
    s=sub(s,'                cells.append(chafa_cells[row][column])', '''                fg, bg, glyph = chafa_cells[row][column]
                cells.append((tuple(round(c * strength_step / 1000) for c in fg),
                              tuple(round(c * strength_step / 1000) for c in bg), glyph))''')
    # A live audio binding lets Tk schedule even while an owner-side prompt is open.
    i=s.index('    def set_playback_position(self, position: float,')
    s=s[:i]+'''    def set_playback_clock(self, process, origin, speed, started, end=None):
        with self._lock:
            self._audio_clock_binding = (process, origin, speed, started, end)

    def set_karaoke_timeline(self, entries, **options):
        """Deliver every future cue before its deadline, once per source revision."""
        with self._lock:
            current = getattr(self, "_karaoke_timeline", None)
            if current is None or current[0] is not entries:
                self._karaoke_timeline = (entries, tuple(entries), dict(options))
            else:
                self._karaoke_timeline = (current[0], current[1], dict(options))

    def advance_karaoke_timeline(self):
        with self._lock:
            timeline = getattr(self, "_karaoke_timeline", None)
        if timeline is not None:
            self.update_karaoke_frame(karaoke_frame_at(timeline[1], self.playback_position()), **timeline[2])

'''+s[i:]
    s=sub(s,'    def playback_position(self) -> float:\n        with self._lock:\n', '''    def playback_position(self) -> float:
        with self._lock:
            binding = getattr(self, "_audio_clock_binding", None)
            if binding is not None and getattr(self, "_playback_running", False):
                process, origin, speed, started, end = binding
                live = origin + audio_segment_elapsed(process, time.monotonic(), started, speed,
                    getattr(process, "playback_started_at", False) is None)
                return min(end, live) if end is not None else live
''')
    s=sub(s,'if self._playback_running else 0.0','if getattr(self, "_playback_running", False) else 0.0')
    s=sub(s,'        def process_commands() -> None:\n            try:', '        def process_commands() -> None:\n            try:\n                self.advance_karaoke_timeline()')
    s=sub(s,'            segment_was_recorded = False\n','''            if external_album_art_window is not None:
                external_album_art_window.set_playback_clock(process, position, speed, segment_started, playback_end)
            segment_was_recorded = False
''')
    s=sub(s,'external_album_art_window.update_karaoke_frame(\n                        shared_karaoke_frame(displayed_position),','external_album_art_window.set_karaoke_timeline(\n                        lyrics,')
    s=sub(s,'external_album_art_window.update_karaoke_frame(\n                                shared_karaoke_frame(position),','external_album_art_window.set_karaoke_timeline(\n                                lyrics,')
    # Adapt tests whose old assertions describe deliberately changed behavior.
    s=sub(s,'self.assertEqual("rammstein.com/", compact_url_display_text("http://www.rammstein.com/"))','self.assertEqual("rammstein.com", compact_url_display_text("http://www.rammstein.com/"))')
    s=sub(s,'self.assertIn("(drcs_enabled or web_server is not None)", source)','self.assertIn("(drcs_enabled or web_server is not None or progress_bar_enabled)", source)')
    s=sub(s,'self.assertIn("Shift+INS = Windows file picker", source)','self.assertIn("Shift+Enter jumps", source)\n        self.assertIn("Shift+INS files", source)')
    s=sub(s,'self.assertIn("while not lastfm_now_playing_finished.wait(0.05)", source)','self.assertIn("lastfm_now_playing_finished.wait(0.05)", source)')
    s=sub(s,'self.assertIn("external_album_art_window.set_playback_position(displayed_position)", source)','self.assertIn("external_album_art_window.set_playback_position(displayed_position, speed=", source)')
    return s

edit(update)
p=ROOT/'test_play_audio_file_v416.py'
replace_file(p,p.read_text(encoding='utf-8').replace('p.PLAYER_DEFAULT_SETTINGS','p.PLAYER_SETTING_DEFAULTS'))
