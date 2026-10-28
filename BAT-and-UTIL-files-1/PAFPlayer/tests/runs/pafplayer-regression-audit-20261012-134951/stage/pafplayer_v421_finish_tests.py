from pafplayer_v416_edit import ROOT,replace_file,sub
f=ROOT/'test_play_audio_file_v417.py'
s=f.read_text(encoding='utf-8')
s=sub(s, '        controller.last_snapshot = {"known": True, "active": ()}\n        controller.filter_action(None, False, 0)', '        monitor.snapshot.return_value = {"known": True, "active": ()}\n        controller.filter_action(None, False, 0)\n        monitor.snapshot.return_value = {"known": True, "active": ("VLC",)}')
replace_file(f,s)

# Reuse the real-worker harness with the V421 manual-control assertions.
s=(ROOT/'pafplayer_v420_live_player_check.py').read_text(encoding='utf-8')
s=sub(s, 'controller = p.PAFExternalPlaybackCoordinator(SelectedMedia())', '''controller = p.PAFExternalPlaybackCoordinator(SelectedMedia())
# Establish a known idle baseline before attaching the live native sample, to
# exercise an interruption and real worker restart without controlling apps.
controller.baseline_observed = True''')
s=sub(s, "        assert paused[0] and controller.auto_paused, 'Manual Play bypassed other-media priority'", "        assert not paused[0] and not controller.auto_paused, 'Manual Play did not resume playback'")
s=sub(s, '        phase[0] = 2\n        return p.STOP', '''        phase[0] = 2
        return None
    if phase[0] == 2 and time.monotonic() > deadline - 20:
        assert not paused[0] and not controller.auto_paused, 'Playback was immediately paused again'
        phase[0] = 3
        return p.STOP''')
s=sub(s, "phase[0] == 2, (result, phase)", "phase[0] == 3, (result, phase)")
s=sub(s, "'pafplayer_v420_live_player_check.json'", "'pafplayer_v421_live_player_check.json'")
s=sub(s, "'vlc_isolated_from_other_apps': '--vlc-only' in sys.argv", "'vlc_isolated_from_other_apps': '--vlc-only' in sys.argv, 'baseline': 'idle baseline injected before live monitor', 'manual_play_resumed': True")
replace_file(ROOT/'pafplayer_v421_live_player_check.py',s)
