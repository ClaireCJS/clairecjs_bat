from pafplayer_v416_edit import edit, sub


def transform(s):
    s = s.replace('2026-09-15-V416-TIMELINE-TODOS-AND-KARAOKE-SPACING', '2026-09-20-V416-TIMELINE-TODOS-EXTERNAL-MEDIA')
    s = s.replace('2026-09-15-v416-timestamped-timelines-and-todos', '2026-09-20-v416-timelines-todos-external-media')
    s = sub(s, '    "ArtworkSeamStrategy": 0,', '    "ArtworkSeamStrategy": 0,\n    "ExternalMediaAutoPause": int(EXTERNAL_MEDIA_AUTO_PAUSE),\n    "ExternalMediaResumeFadeSeconds": int(EXTERNAL_MEDIA_RESUME_FADE_SECONDS),')
    s = sub(s, '    guard_winamp: bool | None = None,', '    guard_winamp: bool | None = None,\n    external_media_controller: PAFExternalPlaybackCoordinator | None = None,')
    s = sub(s, '    winamp_paused_by_preview = pause_playing_winamp() if manage_winamp else False', '''    # V416 yields to newly started media instead of repeatedly pausing Winamp.
    winamp_paused_by_preview = False
    owns_external_media_controller = external_media_controller is None
    if external_media_controller is None:
        monitor = PAFExternalMediaMonitor().start() if os.name == "nt" and process_factory is subprocess.Popen and key_action_reader is read_windows_key_action else None
        external_media_controller = PAFExternalPlaybackCoordinator(monitor)''')
    s = sub(s, '''                if not disable_winamp_enforcement and guard_winamp and now - last_winamp_enforcement >= 0.5:
                    if pause_playing_winamp() and manage_winamp:
                        winamp_paused_by_preview = True
                    last_winamp_enforcement = now
''', '')
    s = sub(s, '''                        if PREVENT_WINAMP_PAUSE_WHEN_WE_ARE_PAUSED:
                            if not disable_winamp_enforcement and guard_winamp and paused_now - last_winamp_enforcement >= 0.5:
                                if pause_playing_winamp() and manage_winamp:
                                    winamp_paused_by_preview = True
                                last_winamp_enforcement = paused_now
''', '')
    s = sub(s, '''            if not winamp_paused_by_session:
                winamp_paused_by_session = pause_playing_winamp()
''', '')
    # One coordinator follows track transitions; direct API calls own a local one.
    s = sub(s, '    winamp_paused_by_session = False', '    winamp_paused_by_session = False\n    external_media_controller = PAFExternalPlaybackCoordinator(PAFExternalMediaMonitor().start())')
    s = sub(s, '                manage_winamp=False,\n                guard_winamp=True,', '                manage_winamp=False,\n                guard_winamp=True,\n                external_media_controller=external_media_controller,')
    s = sub(s, '        resume_winamp_if_paused_by_preview(winamp_paused_by_session)', '        external_media_controller.close()\n        resume_winamp_if_paused_by_preview(winamp_paused_by_session)')
    s = sub(s, '        resume_winamp_if_paused_by_preview(winamp_paused_by_preview)', '        if owns_external_media_controller:\n            external_media_controller.close()\n        resume_winamp_if_paused_by_preview(winamp_paused_by_preview)')
    # Preserve automatic ownership across a paused track change/startup latch.
    s = sub(s, '                if startup_pause_pending:\n', '                startup_pause_transition = startup_pause_pending\n                if startup_pause_pending:\n')
    s = sub(s, '                if action == WEB_PLAY:\n', '''                if not startup_pause_transition:
                    action = external_media_controller.filter_action(action, False, now)
                if action == EXTERNAL_MEDIA_PAUSE:
                    set_transient_notice("Paused for other media", "⏸ Paused for " + ", ".join(external_media_controller.last_snapshot.get("active", ())), 5.0)
                    action = PAUSE_TOGGLE
                if action == WEB_PLAY:
''')
    s = sub(s, '                        if paused_action == WEB_PAUSE:\n', '''                        paused_action = external_media_controller.filter_action(paused_action, True, paused_now)
                        if paused_action == EXTERNAL_MEDIA_RESUME:
                            set_transient_notice("Other media finished", f"▶ Resuming with {EXTERNAL_MEDIA_RESUME_FADE_SECONDS}s fade-in", 5.0)
                            paused_action = PAUSE_TOGGLE
                        if paused_action == WEB_PAUSE:
''')
    # The envelope is applied to PCM/filter output, never by volume/restart steps.
    s = sub(s, '    replaygain_info: ReplayGainInfo | None,\n):\n    """Launch the opt-in WaveOut', '    replaygain_info: ReplayGainInfo | None,\n    resume_fade: tuple[float, float] | None = None,\n):\n    """Launch the opt-in WaveOut')
    s = sub(s, '    requested = list(output_device_indexes or [output_device_index])', '    command = apply_external_resume_fade(command, resume_fade)\n    requested = list(output_device_indexes or [output_device_index])')
    s = sub(s, '            speed = PLAYBACK_SPEEDS[speed_index]\n            buffered_waveout_active', '            speed = PLAYBACK_SPEEDS[speed_index]\n            resume_fade = external_media_controller.fade_arguments()\n            fade_segment_start = external_media_controller.fade_elapsed\n            buffered_waveout_active')
    s = sub(s, '                        end_seconds=playback_end, replaygain_info=replaygain_info,\n                        target_buffer_ms=', '                        end_seconds=playback_end, replaygain_info=replaygain_info,\n                        resume_fade=resume_fade,\n                        target_buffer_ms=')
    s = sub(s, '                append_pafplayer_trace(\n                    "ffplay.launch",', '                command = apply_external_resume_fade(command, resume_fade)\n                append_pafplayer_trace(\n                    "ffplay.launch",')
    s = sub(s, '                elapsed = audio_segment_elapsed(process, now, segment_started, speed, buffered_clock_waiting)', '                elapsed = audio_segment_elapsed(process, now, segment_started, speed, buffered_clock_waiting)\n                external_media_controller.advance_fade(fade_segment_start, elapsed / max(0.01, speed))')
    # Settings persist, take effect while paused, and use existing Undo/default flow.
    s = sub(s, '        global ARTWORK_SEAM_STRATEGY\n', '        global ARTWORK_SEAM_STRATEGY, EXTERNAL_MEDIA_AUTO_PAUSE, EXTERNAL_MEDIA_RESUME_FADE_SECONDS\n        EXTERNAL_MEDIA_AUTO_PAUSE = bool(settings.get("ExternalMediaAutoPause", EXTERNAL_MEDIA_AUTO_PAUSE))\n        EXTERNAL_MEDIA_RESUME_FADE_SECONDS = max(0, min(120, int(settings.get("ExternalMediaResumeFadeSeconds", EXTERNAL_MEDIA_RESUME_FADE_SECONDS))))\n')
    s = sub(s, '        global ART_COLOR_VISUALIZER_BAR_OPACITY, ARTWORK_SEAM_STRATEGY\n', '        global ART_COLOR_VISUALIZER_BAR_OPACITY, ARTWORK_SEAM_STRATEGY, EXTERNAL_MEDIA_AUTO_PAUSE, EXTERNAL_MEDIA_RESUME_FADE_SECONDS\n')
    s = sub(s, '    global ART_COLOR_VISUALIZER_BAR_OPACITY, ARTWORK_SEAM_STRATEGY\n', '    global ART_COLOR_VISUALIZER_BAR_OPACITY, ARTWORK_SEAM_STRATEGY, EXTERNAL_MEDIA_AUTO_PAUSE, EXTERNAL_MEDIA_RESUME_FADE_SECONDS\n    EXTERNAL_MEDIA_AUTO_PAUSE = bool(persisted_settings.get("ExternalMediaAutoPause", EXTERNAL_MEDIA_AUTO_PAUSE))\n    EXTERNAL_MEDIA_RESUME_FADE_SECONDS = max(0, min(120, int(persisted_settings.get("ExternalMediaResumeFadeSeconds", EXTERNAL_MEDIA_RESUME_FADE_SECONDS))))\n')
    s = sub(s, '            "ArtworkSeamStrategy": ARTWORK_SEAM_STRATEGY,', '            "ArtworkSeamStrategy": ARTWORK_SEAM_STRATEGY,\n            "ExternalMediaAutoPause": int(EXTERNAL_MEDIA_AUTO_PAUSE),\n            "ExternalMediaResumeFadeSeconds": EXTERNAL_MEDIA_RESUME_FADE_SECONDS,')
    s = sub(s, "                'ArtworkSeamStrategy': ARTWORK_SEAM_STRATEGY,", "                'ArtworkSeamStrategy': ARTWORK_SEAM_STRATEGY,\n                'ExternalMediaAutoPause': int(EXTERNAL_MEDIA_AUTO_PAUSE),\n                'ExternalMediaResumeFadeSeconds': EXTERNAL_MEDIA_RESUME_FADE_SECONDS,")
    s = sub(s, '        elif key == "artwork_seam_strategy":', '''        elif key == "external_media_auto_pause":
            EXTERNAL_MEDIA_AUTO_PAUSE = bool(value)
            save_player_setting_value("ExternalMediaAutoPause", int(EXTERNAL_MEDIA_AUTO_PAUSE))
        elif key == "external_media_resume_fade_seconds":
            EXTERNAL_MEDIA_RESUME_FADE_SECONDS = max(0, min(120, value))
            save_player_setting_value("ExternalMediaResumeFadeSeconds", EXTERNAL_MEDIA_RESUME_FADE_SECONDS)
        elif key == "artwork_seam_strategy":''')
    s = sub(s, '        "artwork_seam_strategy": (0, 5),', '        "artwork_seam_strategy": (0, 5),\n        "external_media_auto_pause": (0, 1),\n        "external_media_resume_fade_seconds": (0, 120),')
    s = sub(s, '    schema["selects"].append({"key": "artwork_seam_strategy",', '''    schema["sliders"].append({"key": "external_media_resume_fade_seconds", "label": "Automatic resume fade-in", "min": 0, "max": 120, "step": 1, "suffix": "s", "theme": "playback", "tooltip": "Fade from silence to your selected volume after other media finishes. Default 15 seconds; 0 disables the fade. Applies to the next automatic resume."})
    schema["toggles"].append({"key": "external_media_auto_pause", "label": "Pause for VLC, Winamp and browser media", "web_key": "external_media_auto_pause", "theme": "playback", "tooltip": "Let other media take priority, including YouTube. Resume only a pause made automatically; manual Pause stays paused. Manual Play overrides the current interruption."})
    schema["selects"].append({"key": "artwork_seam_strategy",''')
    s = sub(s, "['output_device','output_rate','output_bit_depth','speed_index','output_channels','balance','visualizer_input_source'].includes(item.key)", "['external_media_resume_fade_seconds','output_device','output_rate','output_bit_depth','speed_index','output_channels','balance','visualizer_input_source'].includes(item.key)")
    s = sub(s, "const playbackKeys=['shuffle','loop','mm_inspired_renderer_enabled'];", "const playbackKeys=['external_media_auto_pause','shuffle','loop','mm_inspired_renderer_enabled'];")
    s = sub(s, '                        artwork_seam_strategy=ARTWORK_SEAM_STRATEGY,', '                        artwork_seam_strategy=ARTWORK_SEAM_STRATEGY,\n                        **external_media_controller.status(),')
    s = sub(s, '                                paused=True,\n                                position_seconds=playback_ui_position(position),', '                                paused=True,\n                                **external_media_controller.status(),\n                                position_seconds=playback_ui_position(position),')
    s = sub(s, '            "progress_beat_detector": 1,', '            "external_media_auto_pause": bool(EXTERNAL_MEDIA_AUTO_PAUSE),\n            "external_media_resume_fade_seconds": EXTERNAL_MEDIA_RESUME_FADE_SECONDS,\n            "progress_beat_detector": 1,')
    s = sub(s, "   const playState=s.paused?'Paused':s.playing?'Playing':'Stopped';", "   const playState=s.external_media_auto_paused?'Paused for '+(s.external_media_active||[]).join(', '):s.paused?'Paused':s.playing?'Playing':'Stopped';") if "   const playState=" in s else sub(s, "  const playState=s.paused?'Paused':s.playing?'Playing':'Stopped';", "  const playState=s.external_media_auto_paused?'Paused for '+(s.external_media_active||[]).join(', '):s.paused?'Paused':s.playing?'Playing':'Stopped';")
    return s


edit(transform)
