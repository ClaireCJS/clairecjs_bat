from pafplayer_v416_edit import edit, sub

def update(s):
    i = s.index('def read_windows_key_action()')
    s = s[:i] + '''GLOBAL_SEEK_PREFIX = "global-seek-seconds:"
_GLOBAL_SEEK_CAPTURE = None


def seek_seconds_for_action(action):
    if action in SEEK_SECONDS:
        return SEEK_SECONDS[action]
    if isinstance(action, str) and action.startswith(GLOBAL_SEEK_PREFIX):
        try:
            value = float(action[len(GLOBAL_SEEK_PREFIX):])
            return value if math.isfinite(value) else None
        except ValueError:
            pass
    return None


class GlobalSeekCapture:
    """Capture physical presses/releases while the playback owner restarts audio.

    Only this thread samples the two global seek chords. It never consumes
    msvcrt text, so searchable menus retain ownership of their normal input.
    """
    def __init__(self):
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
        self.pending = 0.0
        self.direction = 0
        self.repeat_at = 0.0
        self.suppress_until = 0.0

    def sample(self, direction, now):
        with self.lock:
            if direction:
                self.suppress_until = now + 0.20
                if direction != self.direction:
                    self.pending += 5.0 * direction
                    self.repeat_at = now + 0.25
                elif now >= self.repeat_at:
                    repeats = 1 + int((now - self.repeat_at) / 0.085)
                    self.pending += 5.0 * direction * repeats
                    self.repeat_at += 0.085 * repeats
            self.direction = direction

    def drain(self):
        with self.lock:
            value, self.pending = self.pending, 0.0
            return value

    def run(self):
        while not self.stop_event.is_set():
            chord = _windows_key_down(0x11) and _windows_key_down(0x12)
            direction = (int(_windows_key_down(0x27)) - int(_windows_key_down(0x25))) if chord else 0
            self.sample(direction, time.monotonic())
            self.stop_event.wait(0.005)

    def start(self):
        threading.Thread(target=self.run, name="paf-global-seek", daemon=True).start()
        return self

    def close(self):
        self.stop_event.set()


''' + s[i:]
    s = sub(s, '    ctrl_down = _windows_key_down(0x11)\n    alt_down', '''    if _GLOBAL_SEEK_CAPTURE is not None:
        delta = _GLOBAL_SEEK_CAPTURE.drain()
        if delta:
            return GLOBAL_SEEK_PREFIX + str(delta)
    ctrl_down = _windows_key_down(0x11)
    alt_down''')
    s = sub(s, '        for virtual_key, scan_character, action in global_arrow_bindings:\n', '        for virtual_key, scan_character, action in global_arrow_bindings:\n            if _GLOBAL_SEEK_CAPTURE is not None and action in {SEEK_BACK_5, SEEK_FORWARD_5}:\n                continue\n')
    s = sub(s, '        deadline = _ASYNC_EXTENDED_SUPPRESS_ONCE.get(extended)', '''        if (_GLOBAL_SEEK_CAPTURE is not None and extended in {"K", "M", "s", "t"}
                and (ctrl_down and alt_down or time.monotonic() < _GLOBAL_SEEK_CAPTURE.suppress_until)):
            return None
        deadline = _ASYNC_EXTENDED_SUPPRESS_ONCE.get(extended)''')
    s = sub(s, '        resume_after_pause = False\n', '''        global _GLOBAL_SEEK_CAPTURE
        if key_action_reader is read_windows_key_action and os.name == "nt":
            _GLOBAL_SEEK_CAPTURE = GlobalSeekCapture().start()
        resume_after_pause = False
''', count=1) if s.count('        resume_after_pause = False\n') == 1 else s
    # Match whole lines, excluding the more-indented reset following launch.
    if 'global _GLOBAL_SEEK_CAPTURE\n' not in s[s.index('def play_audio_file('):]:
        s = sub(s, '\n        resume_after_pause = False\n', '''
        global _GLOBAL_SEEK_CAPTURE
        if key_action_reader is read_windows_key_action and os.name == "nt":
            _GLOBAL_SEEK_CAPTURE = GlobalSeekCapture().start()
        resume_after_pause = False
''')
    s = sub(s, '        abort_requested.set()\n        stop_process(process)', '''        abort_requested.set()
        if _GLOBAL_SEEK_CAPTURE is not None:
            _GLOBAL_SEEK_CAPTURE.close()
            _GLOBAL_SEEK_CAPTURE = None
        stop_process(process)''')
    s = sub(s, '                if action in SEEK_SECONDS:', '                if (seek_delta := seek_seconds_for_action(action)) is not None:')
    s = sub(s, 'position + elapsed + SEEK_SECONDS[action],', 'position + elapsed + seek_delta,')
    s = sub(s, '                    }[action]\n                    show_status(position, indicator)', '                    }.get(action, "⏪" if seek_delta < 0 else "⏩")\n                    resume_after_pause = True  # Use the short preroll for interactive seeks, too.\n                    progress_beat_state.clear()\n                    show_status(position, indicator)')
    s = sub(s, '                        if paused_action in SEEK_SECONDS:', '                        if (seek_delta := seek_seconds_for_action(paused_action)) is not None:')
    s = s.replace('position + SEEK_SECONDS[paused_action]', 'position + seek_delta').replace('"⏪" if SEEK_SECONDS[paused_action] < 0 else "⏩"', '"⏪" if seek_delta < 0 else "⏩"')
    # Picker selection mode is explicit; Enter's queue behavior stays compatible.
    s = sub(s, '    quit_callback=None,\n) -> Path | None:', '    quit_callback=None,\n    jump_state: list[bool] | None = None,\n) -> Path | tuple[Path, ...] | None:')
    s = sub(s, '    query = ""\n    selected = 0', '    query = ""\n    selected_paths: list[Path] = []\n    selected = 0')
    s = sub(s, '➕ Add to playlist — type words; Enter adds; Esc cancels; Shift+INS = Windows file picker', '➕ J/Insert — Enter enqueues; Shift+Enter jumps; Ctrl+Space selects; Esc cancels; Shift+INS files')
    s = sub(s, '            marker = "➤" if index == selected else " "', '            marker = ("➤" if index == selected else " ") + ("☑" if path in selected_paths else " ")')
    s = sub(s, '        if key in {"\\r", "\\n"}:\n            return matches[selected] if matches else None', '''        if key in {"\\r", "\\n"}:
            if shift and matches:
                if jump_state is not None:
                    jump_state[0] = True
                return matches[selected]
            return tuple(selected_paths) if selected_paths else (matches[selected] if matches else None)
        if key in {" ", "\\x00"} and ctrl and not alt:
            if matches:
                path = matches[selected]
                if path in selected_paths:
                    selected_paths.remove(path)
                else:
                    selected_paths.append(path)
            continue''')
    s = sub(s, '                    return picked[0]', '                    return picked')
    s = sub(s, '        picked = (\n            traditional_windows_audio_file_picker', '        jump_selection = [False]\n        picked = (\n            traditional_windows_audio_file_picker')
    s = sub(s, '                    quit_callback=abort_requested.set,', '                    quit_callback=abort_requested.set,\n                    jump_state=jump_selection,')
    s = sub(s, '        added_paths: list[Path] = []\n        for selected_path', '''        if jump_selection[0] and playlist_jump_state is not None:
            target = selected[0]
            if not target.is_file():
                set_transient_warning("Selected file is missing", seconds=5.0)
                return False
            playlist_jump_state[0] = target
            speed_index = PLAYBACK_SPEEDS.index(1.0)
            if speed_index_state is not None:
                speed_index_state[0] = speed_index
            return False
        added_paths: list[Path] = []
        for selected_path''')
    # Handle jumps on the owner, including Q -> same picker, both paused and live.
    s = sub(s, '                    if speed_changed:\n', '''                    if playlist_jump_state is not None and playlist_jump_state[0] is not None:
                        record_segment(current_prompt_position())
                        stop_process(process)
                        return finish_playback(PLAYLIST_JUMP_RESULT)
                    if speed_changed:
''')
    s = sub(s, '                        add_track_via_insert(False)\n                    elif choice', '''                        add_track_via_insert(False)
                        if playlist_jump_state is not None and playlist_jump_state[0] is not None:
                            record_segment(current_prompt_position())
                            stop_process(process)
                            return finish_playback(PLAYLIST_JUMP_RESULT)
                    elif choice''')
    s = sub(s, '                            if choice == "q": add_track_via_insert(False)', '''                            if choice == "q":
                                add_track_via_insert(False)
                                if playlist_jump_state is not None and playlist_jump_state[0] is not None:
                                    return finish_playback(PLAYLIST_JUMP_RESULT)''')
    s = sub(s, '                                initial_quit_q_presses=(1 if paused_action == PLAYLIST_ADD_SEARCH_Q else 0),\n                            )', '''                                initial_quit_q_presses=(1 if paused_action == PLAYLIST_ADD_SEARCH_Q else 0),
                            )
                            if playlist_jump_state is not None and playlist_jump_state[0] is not None:
                                return finish_playback(PLAYLIST_JUMP_RESULT)''')
    return s

edit(update)
