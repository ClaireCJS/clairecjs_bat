from pathlib import Path
import ast,hashlib,shutil,io,unittest
import PAFPlayer as app
root=Path.cwd()
notes=root/'releases/PAFPlayer_v757_smooth_idle_artwork_release_notes.md';assert not notes.exists()
notes.write_text('# PAFPlayer V757 — smoother idle artwork animation\n\nPosition-only dance Configure events no longer schedule image resampling, border suppression, title updates or placement saves. The native window still moves without activating or changing Z-order. Actual user resizing retains the normal rendering path.\n\nAnimation targets 60 Hz using monotonic deadlines; callback work is subtracted from the next delay and missed frames are skipped without catch-up bursts. Existing subpixel/time-based motion keeps its speed, bounds, beat reaction and origin restoration. The main dance reuses the existing monitor-watcher snapshot. When not dancing, idle detection polls at 100 ms rather than animation rate.\n\n`art.idle.pacing` diagnostic summaries report measured FPS, longest callback gap, longest callback work and extra-window count every ten seconds while dancing. These measurements are needed to assess residual jitter on the affected display; automated tests do not establish actual compositor smoothness. Restart PAFPlayer to load this release.\n\nValidation includes extracted real Configure/scheduler callbacks, missed-frame pacing, unchanged motion speed across 30/60/120 Hz, monitor-safe bounds, gallery layout and existing beat behavior. An unrelated historical V653 test still expects the removed experimental schema flag; that stale assertion is recorded separately from animation tests.\n',encoding='utf-8')
release=root/'releases/PAFPlayer_v757_smooth_idle_artwork.py';assert not release.exists();shutil.copy2(root/'PAFPlayer.py',release)
assert hashlib.sha256(release.read_bytes()).digest()==hashlib.sha256((root/'PAFPlayer.py').read_bytes()).digest()
for file in (root/'PAFPlayer.py',release):ast.parse(file.read_text(encoding='utf-8-sig'))
suite=unittest.TestSuite()
suite.addTests(unittest.defaultTestLoader.loadTestsFromName('test_v757_idle_pacing'))
for method in ('test_music_step_uses_bounded_progress_pulse','test_artwork_consumes_progress_bar_beat_value_without_analyzer','test_stale_music_pulse_stops_music_driven_motion'):
 suite.addTests(unittest.defaultTestLoader.loadTestsFromName('test_v653_idle_art_music_dance.V653IdleArtworkMusicDanceTests.'+method))
for method in ('test_configurable_dance_range_remains_monitor_safe','test_zero_dance_range_holds_origin'):
 suite.addTests(unittest.defaultTestLoader.loadTestsFromName('test_v651_idle_dance_session_errors.V651IdleDanceAndSessionErrorTests.'+method))
for method in ('test_v86_idle_art_drift_box_is_tiny_and_monitor_safe','test_v87_idle_gallery_allocator_avoids_player_and_other_dance_areas','test_v87_idle_gallery_refuses_slots_when_pafplayer_occupies_monitor','test_v243_manual_idle_uses_current_native_four_corners_without_track_reload','test_v249_idle_main_dance_uses_native_outer_rect_origin_and_movement','test_v263_idle_art_dance_never_straddles_monitor_seam'):
 suite.addTest(app.PlayWaveFileTests(method))
stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
app.set_post_playback_output(False)
report=stream.getvalue()+'\nSyntax and release-copy SHA256 checks passed. Root audit: PAFPlayer root retains active implementation, data and Qwen shim; lockscreen/screensaver roots retain native inputs and active runtime assets. No C:\\BAT changes.\nSeparate stale-test failure: V653 test_checkbox_is_experimental_persistent_and_web_settable expects an experimental schema key that is absent from the current schema; no schema behavior was changed in V757.\nActual visual smoothness on the user display was not measured.\n'
path=root/'tests/reports/v757-idle-pacing-checks.txt';assert not path.exists();path.write_text(report,encoding='utf-8');print(report)
raise SystemExit(not result.wasSuccessful())
