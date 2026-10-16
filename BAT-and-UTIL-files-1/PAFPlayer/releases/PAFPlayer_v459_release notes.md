# PAFPlayer V459 — September 28, 2026

## Complete song endings

Fixed early endings during ordinary automatic next-song transitions in the
buffered/native playback path. FFmpeg previously received a source-duration
limit after its input, where it limited output time after tempo processing.
At 0.9× speed this discarded roughly the last 10% of a song. The running player's
decoder command was confirmed to use that combination. At faster speeds, the
same mistake could play beyond an explicitly bounded source segment.

The duration limit now applies to input decoding, before tempo processing.
Existing seek positions, ReplayGain, channel mixing, sample formats and device
buffer-drain behavior are preserved. Relative to V458, the only production
function changed is `matrixmixer_inspired_ffmpeg_command`, plus release metadata.

## Actual decoded audio

A generated 50-second recording has a distinct 1429-Hz tone in its final second.
The test decodes actual PCM using the production FFmpeg command without opening
an audio device. At 0.9×, V458 emitted 50.000 seconds and lost the ending tone;
V459 emits 55.551 seconds and preserves it (55.556 expected). At 0.5×, the output
changed from 50.000 to 99.982 seconds and the ending tone is retained. Normal and
faster speeds also preserve the ending. Seeking into the final ten seconds works,
and a faster bounded segment stops at its requested source end.

Eleven new regression tests pass: eight real decode scenarios, including the
7.1/96-kHz/24-bit output format, and three completion/drain guards. These verify
that decoder EOF does not report completion while PCM is still draining, natural
close does not reset the device, and all output endpoints finish before advancing.
No production drain logic needed changing. Actual listening on the user's audio
hardware was not performed, and the running player was not interrupted.

## Includes the completed memory repairs

V458's cover cache limits (24 entries and 64 MiB), coalesced popup updates,
partial-console-write repair, legacy launcher synchronization, history-report
repair, and on-demand runtime diagnostics are included. The accelerated cover
workload stopped growing at 24 MiB instead of retaining 512 MiB; stalled popup
title work stayed at one command instead of 100,000. Sampled rendered frames were
identical to the baseline. Full measurements and limits are in the included
[V458 release notes](PAFPlayer_v458_release_notes.md). Hours of real playback with
console, artwork popup and floating lyrics together still require observation
after restart; the accelerated measurements do not certify every FPS slowdown.

## Full regression run

**898 distinct tests: 843 passed,
47 failed assertions, and
8 errors. The complete historical suite is not green.**

All 32 new V458/V459 tests pass. No previously passing method became non-passing
relative to the full V458 audit. The 55 remaining historical methods
already failed before these releases; they include UI/render/source contracts
and old version-identity expectations. They are tracked for reconciliation,
not blanket-skipped or assumed harmless. The runner reports a failure exit code.
Each remaining method is listed below; JSON results contain the tracebacks.

Run `python -B -X utf8 run_PAFPlayer_tests.py` for the complete isolated suite.
Run `python -B -X utf8 pafplayer_v459_decode_check.py PAFPlayer.py NEW_DIRECTORY`
for the 50-second decode experiment; its output directory must not already exist.

## Installation

Restart PAFPlayer to load V459. This release updates `C:\BAT\PAFPlayer.py` after
a verified sibling backup; V458 already updated the compatibility launcher.
The ZIP includes exact tested inputs, release notes, results and measurements.
The installation report records every changed path and checksum.

## Remaining historical failures

- `PAFPlayer.PlayWaveFileTests.test_v106_metadata_tails_fill_existing_rows_before_adding_lines` (failure)
- `PAFPlayer.PlayWaveFileTests.test_v109_alt3_is_live_persistent_state_across_track_handoff` (failure)
- `PAFPlayer.PlayWaveFileTests.test_v111_insert_is_multiselect_play_next_and_resets_speed` (failure)
- `PAFPlayer.PlayWaveFileTests.test_v169_bride_riot_screenshot_justifies_every_free_semantic_colon_pair` (failure)
- `PAFPlayer.PlayWaveFileTests.test_v170_art_window_focus_transparency_zoom_and_plasma_contract` (failure)
- `PAFPlayer.PlayWaveFileTests.test_v175_unfocused_art_has_no_canvas_or_native_border` (failure)
- `PAFPlayer.PlayWaveFileTests.test_v179_black_dresses_album_and_url_use_same_colon_when_slack_exists` (failure)
- `PAFPlayer.PlayWaveFileTests.test_v180_playback_publishes_emphasis_progress_to_external_lyrics` (failure)
- `PAFPlayer.PlayWaveFileTests.test_v183_equal_spacing_preserves_existing_semantic_colon_anchors` (failure)
- `PAFPlayer.PlayWaveFileTests.test_v192_floating_overlay_is_content_sized_and_drag_stable` (failure)
- `PAFPlayer.PlayWaveFileTests.test_v192_resize_preserves_floating_center_and_artwork_rectangle` (failure)
- `PAFPlayer.PlayWaveFileTests.test_v229_web_art_is_capped_and_transport_precedes_visualizer` (failure)
- `PAFPlayer.PlayWaveFileTests.test_v238_playlist_browser_and_web_queue_contract` (failure)
- `PAFPlayer.PlayWaveFileTests.test_v238_web_rainbow_title_glow_art_cycle_and_player_order` (failure)
- `PAFPlayer.PlayWaveFileTests.test_v248_cursive_fix_is_in_web_karaoke_not_experimental_bottom` (failure)
- `PAFPlayer.PlayWaveFileTests.test_v263_release_identity_split_hud_profiler_and_geometry_contract` (failure)
- `PAFPlayer.PlayWaveFileTests.test_v264_web_is_demand_driven_cached_and_browser_animation_is_throttled` (failure)
- `PAFPlayer.PlayWaveFileTests.test_v319_composer_anchors_right_and_comment_is_equidistant` (failure)
- `PAFPlayer.PlayWaveFileTests.test_v319_restores_off_but_keeps_two_unclear_emojimax_removals` (failure)
- `PAFPlayer.PlayWaveFileTests.test_v331_frequency_warp_compacts_low_end_and_repeats_feedback` (failure)
- `PAFPlayer.PlayWaveFileTests.test_v368_floating_animation_backs_off_while_editor_is_opaque` (failure)
- `PAFPlayer.PlayWaveFileTests.test_v380_renderer_switches_charset_per_hybrid_cell_only` (failure)
- `PAFPlayer.PlayWaveFileTests.test_v67_playback_start_history_never_synchronously_selects` (failure)
- `PAFPlayer.PlayWaveFileTests.test_v71_last_heard_tail_still_uses_album_column_when_comment_occupies_row2` (failure)
- `PAFPlayer.PlayWaveFileTests.test_v76_playlist_analysis_table_uses_full_paths_and_wraps_console_rows` (failure)
- `PAFPlayer.PlayWaveFileTests.test_v78_both_fresh_rebuild_sites_preserve_history_order_source` (failure)
- `PAFPlayer.PlayWaveFileTests.test_v87_nonidle_album_art_uses_weighted_sampling_and_real_crossfade_source` (failure)
- `PAFPlayer.PlayWaveFileTests.test_v87_playlist_browser_rows_use_distinct_path_and_brighter_filename_colors` (failure)
- `PAFPlayer.PlayWaveFileTests.test_v91_recent_shuffle_unknown_cache_performs_one_targeted_history_query` (failure)
- `PAFPlayer.PlayWaveFileTests.test_v91_shuffle_transition_calls_three_hour_guard_after_resume_successor` (failure)
- `PAFPlayer.PlayWaveFileTests.test_v96_web_album_art_mouse_contract_is_prev_next_middle_fullsize` (failure)
- `PAFPlayer.V265BrowserOwnedVisualizerRegressionTests.test_v265_web_visualizer_is_browser_owned_and_gated` (failure)
- `test_play_audio_file_v394_rendering.RenderingEquivalence.test_artwork_bank_changes_and_cursor_fence_settings` (failure)
- `test_play_audio_file_v394_rendering.RenderingEquivalence.test_background_modes_resize_crop_and_brightness` (subtest-failure)
- `test_play_audio_file_v394_rendering.RenderingEquivalence.test_every_fill_boundary_including_rounding_ties` (subtest-failure)
- `test_play_audio_file_v394_rendering.RenderingEquivalence.test_fallbacks_and_layer_changes` (subtest-failure)
- `test_play_audio_file_v397_bar_art_performance.BarArtworkEquivalence.test_bar_art_modes_and_geometry` (subtest-failure)
- `test_play_audio_file_v401_bar_art.BatchedBarArtwork.test_edge_blend_rounding_resize_and_crop` (subtest-failure)
- `test_play_audio_file_v401_bar_art.BatchedBarArtwork.test_fallbacks_and_layer_changes` (failure)
- `test_play_audio_file_v401_bar_art.BatchedBarArtwork.test_full_output_and_captures_match` (subtest-failure)
- `test_play_audio_file_v401_bar_art.BatchedBarArtwork.test_warm_full_cells_do_not_use_scalar_blends` (failure)
- `test_play_audio_file_v402_audio_ui.ControlsTests.test_labels_controls_and_recovery_actions` (failure)
- `test_play_audio_file_v416.BufferedWebAndArtworkTests.test_artwork_choices_and_real_gap_cleanup` (failure)
- `test_play_audio_file_v430.V430ConsoleTransportTests.test_large_real_windows_console_text_is_bounded_and_flushed` (error)
- `test_play_audio_file_v430.V430ConsoleTransportTests.test_redirected_output_keeps_the_short_write_fast_path` (error)
- `test_play_audio_file_v430.V430ConsoleTransportTests.test_surrogate_pair_is_not_split_at_a_chunk_boundary` (error)
- `test_play_audio_file_v430.V430EmojimaxTests.test_final_cleanup_removes_requested_exact_word_mappings` (error)
- `test_play_audio_file_v443.ConsoleSafety.test_escape_final_byte_and_dcs_boundaries` (error)
- `test_play_audio_file_v443.ConsoleSafety.test_native_failure_never_replays_an_accepted_prefix` (error)
- `test_play_audio_file_v443.ConsoleSafety.test_native_partial_writes_and_non_bmp_units` (error)
- `test_play_audio_file_v443.ConsoleSafety.test_native_unicode_private_console` (failure)
- `test_play_audio_file_v443.ConsoleSafety.test_overlay_survives_each_complete_frame_commit` (error)
- `test_play_audio_file_v443.HalfCellArtwork.test_uniform_art_reduces_color_commands` (failure)
- `test_play_audio_file_v444_console_rows.ConsoleRowRepair.test_entire_v427_program_is_unchanged_outside_console_writer_and_version` (failure)
- `test_play_audio_file_v445.ArtworkApplicability.test_rendering_and_row_fix_are_identical_to_v444` (failure)
