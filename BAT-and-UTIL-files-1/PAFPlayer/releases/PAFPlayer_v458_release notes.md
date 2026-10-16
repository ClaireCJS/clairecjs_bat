# PAFPlayer V458 — September 28, 2026

## Changes

Cover artwork previously remained cached for every visited track. The cache now
keeps at most 24 entries and 64 MiB of compressed payload, evicting matching source
metadata too. Cache hits refresh recency; missing-art lookups are bounded; a cover
larger than the cache budget still displays without being retained in this cache.

Popup titles and loaded artwork now use one latest-value mailbox per kind.
Obsolete loader results are discarded before enqueueing. Existing lyric
coalescing remains in place, and the Tk command loop yields after 32 commands.
Ordered control requests remain queued normally. No renderer colors, glyphs,
compositing equations, lyric polling rates, or audio parameters were changed.

Also fixed the history-report crash when progress bars are disabled, completed
partial console writes without repeating accepted prefixes, and synchronized
release metadata. The legacy `play_audio_file.py` now executes its sibling
`PAFPlayer.py`, preventing old launchers/tests from silently loading V447.
The canonical program retains its self-contained bundled feature modules.

## Retention and rendering evidence

| Accelerated workload | V457 | V458 |
|---|---:|---:|
| 512 tracks, independent 1-MiB covers | 512 MiB cached | 24 MiB cached |
| 100,000 titles with GUI consumer stalled | 100,000 commands | 1 command |
| 2,400 moving frames, first 400 median | 11.715 ms | 10.852 ms |
| Same workload, final 400 median | 11.423 ms | 10.776 ms |

The workload used 200 columns × 32 rows, Twin DRCS, Signal Aurora, background
and bar artwork, detail 9, blend 1, and 64% bar opacity. Sampled complete frame
payloads were byte-identical between releases. Renderer memory reached a stable
working range in the measured run. Full raw measurements and the reproducible
soak script are included. These tests reproduced two retention defects; they do
not prove that those defects explain every observed long-session slowdown.

The accelerated test does not replace hours of real playback with console,
artwork popup, and floating lyrics together. It excludes actual Tk painting and
terminal transport. Real audio stuttering and end-to-end 60 FPS are not certified.
An older high-memory Python process exited before its identity could be verified;
its memory consumption is not used as proof about PAFPlayer.

## Full regression run

**887 distinct tests: 832 passed,
47 failed assertions, and
8 errors. The full historical suite is not green.**

All 21 new V458 tests pass, including concurrent cache users, oversized artwork,
latest-title/artwork behavior, partial writes, the legacy entry point, native
memory counters, and a real local HTTP diagnostics request. All current V456
workflow/release/integration tests pass. The existing native console-row behavior
tests pass. Compared with the audited V457 run, none of the previously passing
test methods became non-passing. Confirmed defects were repaired; 26 historical
expectations/fixtures were reconciled with already-approved behavior, including
wildcard learned tags, literal duplicate playlist slots, current arrows, the
loudness offset/deadband/fallback, audible media detection, and startup source
acknowledgement. Tests were not blanket-skipped or marked expected failures.

The remaining 55 methods already failed in the V457 audit. They
include old HUD and GUI/source-string contracts, historical renderer comparisons,
rollback-era console helpers, and frozen version/whole-program identity checks.
Their age does not prove every failure harmless; full reconciliation remains
tracked in TODO. Each remaining method is listed below and its traceback remains
in the included JSON. The test runner returns a failure exit status accordingly.

Run `python -B -X utf8 run_PAFPlayer_tests.py` from the project/release root.
It discovers all 671 embedded methods plus standalone player modules, tests
SHA-verified copies in isolated staging, and preserves results and fixtures.
The separate filelist-generator project's pytest configuration is untouched.

## On-demand diagnosis after restart

Open `http://127.0.0.1:666/api/runtime-diagnostics` for process private/working-set
memory, uptime, thread count, artwork payload/count, popup backlog, function-cache
sizes, and collection counts. The endpoint collects counters only when requested;
it does not walk the heap, force garbage collection, or add a playback poller.
It reports aggregate counts without track filenames. An already running process
must be restarted to load these fixes, even if its version label already says V458.

## Publishing

The release ZIP contains the tested canonical program, compatibility launcher,
test inputs/runner, diagnostics/stress evidence, and documentation. Installation
updates `C:\BAT\PAFPlayer.py` and `C:\BAT\play_audio_file.py` after verified
sibling backups. `paf.bat` already targets the canonical program and is unchanged.
The installation report records each affected C:\BAT path and checksum.

The next active investigation is the reported loss of approximately the final
five seconds of songs. V458 does not claim to fix that separate issue.

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
