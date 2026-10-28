# PAFPlayer changelog

# Detailed release history

This retrospective index covers V1–V570, followed by the current V571 documentation release. Original detailed entries are retained. The 241 formerly filename-only entries were checked against archived code: 239 have a source diff against the nearest earlier full snapshot, one is the earliest surviving source, and one is an integration script rather than a full player build. Version-specific tests and changed code informed the summaries; they are historical inferences, not runtime validation. Gaps and internal-version conflicts remain identified rather than assigned invented behavior.

Archive filename/internal-version conflicts: V57→V56, V60→V59, V62→V61, V63→V61, V189→V120, V195→V192, one V199 snapshot→V120, and V415→V414. These filenames alone do not establish the named release.

## V571 — October 17, 2026

Replace 241 filename-derived history entries with specific descriptions inferred from archived source changes and version-specific regression checks. Record the source-comparison evidence, identify source-only version gaps, and state when a file is an integration script or only a version-marker change. Playback behavior is unchanged. [Release notes](releases/PAFPlayer_v571_code_verified_release_history_release_notes.md).

## V570 — October 17, 2026

Reconstruct the historical release index from surviving archived source, release notes, and replacement backups. Preserve existing detailed descriptions, identify ambiguous labels and gaps, and organize root backups and generated reports. Playback behavior is unchanged. [Release notes](releases/PAFPlayer_v570_release_history_reconstruction_release_notes.md).

## V569 — October 16, 2026

Fix the tray lyric popup's repeated `ctypes.ArgumentError` while paused.
Wallpaper queries assigned a string parameter type to the shared Windows API
wrapper, while tray placement passed a rectangle. Give popup and wallpaper
calls private typed wrappers; preserve pointer-sized window/GDI handles and
one shared paint-structure type. Release popup window classes on close.
Contain lyric popup failures and retry on changed content or disable/re-enable,
without repeatedly throwing from the timer callback on the same paused lyric.

116 focused and relevant regression tests passed, including real Windows
popup painting and resource checks under the conflicting legacy signature.
An older track-details test fixture now supplies the existing runtime app
settings interface; its assertions remain unchanged. Both real MonkeyMote
clients and lyrics were confirmed working by the user on V568; protocol code
is unchanged. Manual full-player V569 restart verification remains outstanding.
[Release notes](releases/PAFPlayer_v569_tray_popup_api_isolation_release_notes.md).

## V568 — October 16, 2026

Support up to eight simultaneous MonkeyMote clients with independent sessions
and a synchronized command gate. Add the MonkeyMote web tab, enabled by default,
confirmed permanent disable, editable live port and session/permanent choices.
Add --monkeymote-port; preserve legacy JSON configuration, saved preference IDs
and official-owner-only commands. Bind a replacement port before retiring the
old listener; retain pause acknowledgments across local changes between polls.
Return an empty correlated list for unsupported artist/genre Details drill-down.
The user verified V567 Details and Lyrics on the real iPad. V568 multiple-device
and web behavior has focused automated checks; physical two-device testing is
still pending. No full library browsing or automatic discovery is added.
[Release notes](releases/PAFPlayer_v568_monkeymote_multiple_clients_release_notes.md).

## V567 — October 16, 2026

Add read-only MonkeyMote Details for selected future playlist members, bounded
metadata caching, proactive lyric-text publication, and loopback-only bounded
protocol diagnostics. Prefix the opt-in listener announcement with 💰.
The iPad verified V566 controls, queue order/selection, artwork, and backlog
prevention; V567 future-track Details and Lyrics still require its restart test.
[Release notes](releases/PAFPlayer_v567_monkeymote_details_lyrics_release_notes.md).

## V566 — October 16, 2026

Publish the active upcoming playback sequence and notify MonkeyMote when it
changes. Resolve phone selection to its originally displayed track, prioritize
that track through the official play-next/transport path, and suppress repeated
transport commands until the prior transition is acknowledged. Add current
cover transfer. These behaviors were verified on the user's iPad; the initial
lyric response did not display there, leading to V567 follow-up work.
[Release notes](releases/PAFPlayer_v566_monkeymote_queue_media_release_notes.md).

## V565 — October 16, 2026

Introduce an opt-in home-network MonkeyMote Winamp compatibility listener,
manual host/port connection, playback status and controls, and current playlist.
The user's real MonkeyMote Music Remote HD iPad connected and controlled the
official player. Follow-up testing exposed stale order/selection and repeated
transport backlog, addressed in V566. Android remains unverified.
[Release notes](releases/PAFPlayer_v565_monkeymote_manual_control_release_notes.md).

## V564 — October 15, 2026

Add a narrow open remote-control API for mobile remotes and homescreen widgets:
status, pause, resume, and toggle-pause. No secret or account setup is
required; existing browser control routes remain unchanged. [Release notes](releases/PAFPlayer_v564_remote_control_api_release_notes.md).

## V563 — October 15, 2026

Replace the tray-only client's simplified floating-lyric label with the exact
`ExternalAlbumArtWindow` floating renderer used by the player. Remote state now
drives that shared renderer's lyric, progress, track identity, playback clock,
animation phase, and running/paused state. Its unchanged preference API is
redirected per server to the tray's roaming AppData JSON rather than the local
player registry.
[Release notes](releases/PAFPlayer_v563_shared_remote_floating_renderer_release_notes.md).

## V562 — October 15, 2026

Add **Reload tray from updated PAFPlayer.py** to the remote tray's right-click
menu. Reload relinquishes tray ownership, closes its overlays and connections,
then replaces the process from the current single-file player on disk. Permit
only one tray-only client per Windows logon, make callback diagnostics optional
for the intentionally small remote runtime, and correct 64-bit native window
handle declarations during popup shutdown. Remote icon and tooltip choices now
persist per server under roaming AppData instead of a portable sidecar.
[Release notes](releases/PAFPlayer_v562_tray_reload_single_instance_release_notes.md).

## V561 — October 15, 2026

Replace proactive Windows lyric notifications with PAFPlayer's own bright,
click-through lyric tooltip above the notification-area icon. It updates when
the sung line changes, requires no mouse hover, never activates or covers the
tray icon, and works for both official and remote tray clients.
[Release notes](releases/PAFPlayer_v561_tray_lyric_tooltip_release_notes.md).

## V560 — October 15, 2026

Color the HUD `Play:` label bright yellow while paused and bright red after
Stop, while retaining its original green during playback. Prewarm the first
three lyric lines before audio starts so the first sung cue does not pay cold
Emojimaxx/Unicode layout costs. Remote tray clients now toggle local floating
lyrics with Ctrl+Alt+F and local album art with Ctrl+Alt+A, synchronize at one
heartbeat per second while overlays are active, extrapolate against server
timestamps between heartbeats, and download the lyric timeline only when its
revision changes.
[Release notes](releases/PAFPlayer_v560_transport_hud_and_remote_overlays_release_notes.md).

## V559 — October 15, 2026

Make Ctrl+C/Ctrl+Break a genuinely immediate console reset: restore the ANSI/DEC
terminal state (including the character-set reset used by the pentagram display),
kill the active decoder without a wait, and exit directly instead of entering
tray, web-server, media-session, and GUI shutdown joins.
[Release notes](releases/PAFPlayer_v559_instant_console_break_release_notes.md).

## V558 — October 15, 2026

Reduce recurring work across the player, tray, library search, and Web Config:
debounce superseded whole-library reconciliation walks, coalesce tray registry
reads, throttle mouse-move snapshots for the album-art hover card, and retain the
200-icon web gallery DOM/canvases between status polls instead of rebuilding them.
[Release notes](releases/PAFPlayer_v558_global_responsiveness_optimizations_release_notes.md).

## V557 — October 15, 2026

Give J and QQ the same indexed song-selection dialog with deliberately different
scopes: J is restricted to current-playlist members, while QQ searches the broad
known music catalog (`everything.m3u`, its fallback index, and live library
reconciliation). Selecting a song already in the playlist now queues it next
instead of reporting that it is already present.
[Release notes](releases/PAFPlayer_v557_scoped_j_and_qq_song_dialogs_release_notes.md).

## V556 — October 15, 2026

Make the lyric tray option proactively publish a Windows notification whenever
a new lyric is displayed, with no mouse hover required. Keep playlist visit
history synchronized when the shuffle cooldown substitutes a candidate, so a
triple-left click returns to the track that actually just played.
[Release notes](releases/PAFPlayer_v556_lyric_notifications_and_previous_history_release_notes.md).

## V555 — October 15, 2026

Render native tray-chooser previews at the icon renderer's intended 32×32 size,
so symbols are centered and fully visible before selection. Decode packed
notification-area callback events through `LOWORD(lParam)`, restoring the
deliberate 0.666-second full-information album-art hover on newer Windows shells.
[Release notes](releases/PAFPlayer_v555_tray_preview_and_hover_repair_release_notes.md).

## V554 — October 15, 2026

Place every ordinary single/base key—including arrow and navigation keys—before
F1–F10 in key-ordered Help, while retaining all modifiers on the base key's
line. Make the console playlist browser poll for decoder completion instead of
blocking indefinitely in `getwch`, so reaching EOF closes the view and advances
to the next playlist track normally.
[Release notes](releases/PAFPlayer_v554_key_order_and_live_playlist_progression_release_notes.md).

## V553 — October 15, 2026

Keep tray right-click responsive by rendering 20 genuine type previews instead
of allocating 200 GDI bitmaps synchronously before opening the menu, and contain
menu errors inside the tray thread. Turning Test Tone off now immediately
repaints the normal controls row, removing its instructions.
[Release notes](releases/PAFPlayer_v553_responsive_tray_and_tone_hud_release_notes.md).

## V552 — October 15, 2026

Add Fav/Def controls to Playback **Channels**. Correct locked-session detection
by testing whether Windows permits switching to the returned input desktop;
the previous handle-only check could mistake the secure lock desktop for an
unlocked session and therefore leave the bass shelf unchanged.
[Release notes](releases/PAFPlayer_v552_channel_marks_and_locked_bass_detection_release_notes.md).

## V551 — October 15, 2026

Replace the recolor-heavy tray gallery with 20 distinct icon types and 10
independent colorways (200 combinations), arranged as type → color in the
native menu. Fix saved styles above the old 20-icon limit reverting during the
two-second tray refresh. Add the persistent, opt-in **Full info on tooltip**
menu setting; a stationary 0.666-second hover opens the click-through album-art
and track-information card.
[Release notes](releases/PAFPlayer_v551_tray_icon_matrix_and_full_hover_release_notes.md).

## V550 — October 14, 2026

Change floating-lyrics hit testing from the lyric image's rectangular bounds
to its actual painted glyph pixels. Transparent padding, letter/line gaps, and
empty window space now click through, while Ctrl and explicit edit mode retain
whole-window interaction.
[Release notes](releases/PAFPlayer_v550_floating_glyph_click_through_release_notes.md).

## V549 — October 14, 2026

Make the explicit `--bass-reduction-while-locked=on|off` form permanently
update the saved checkbox while retaining bare switches as session-only
overrides. Add `--default-bass-reduction-percent-while-locked=0..100` to set
the restore-default percentage; its factory value remains 50%.
[Release notes](releases/PAFPlayer_v549_persistent_bass_cli_defaults_release_notes.md).

## V548 — October 14, 2026

Make Bass Reduction while Locked audible through the default buffered WaveOut
renderer by applying its low-shelf filter before channel expansion. Add
validated, session-only CLI overrides for enabling/disabling the feature and
selecting a 0–100% reduction amount.
[Release notes](releases/PAFPlayer_v548_locked_bass_runtime_and_cli_release_notes.md).

## V547 — October 14, 2026

Spell out `Repeat track` in the console HUD whenever single-track repeat is
active. While Test Tone mode is active, replace the normal controls row with
the selected tone's live values and concise keyboard/mouse instructions.
[Release notes](releases/PAFPlayer_v547_console_loop_and_tone_hud_release_notes.md).

## V546 — October 14, 2026

Remove the over-eager `entire` and `powder` Emojimaxx substitutions, and change
the singular `secret` substitution from a padlock to 🤫 for a clearer lyrical
meaning. [Release notes](releases/PAFPlayer_v546_emojimaxx_clarity_release_notes.md).

## V545 — October 14, 2026

Guarantee that the alternate key-ordered help view places A–Z before F1–F10,
then all remaining keys. Make native and Web Config tray-icon selections
reliable by tracking the requested style until the tray thread applies it,
acknowledging web changes, and re-adding the notification icon if Explorer
rejects an in-place refresh.
[Release notes](releases/PAFPlayer_v545_help_sort_and_tray_refresh_release_notes.md).

## V544 — October 14, 2026

Expand the native tray picker to 50 pictorial choices in five compact columns,
add an alternate alphabetic/function-key console-help view toggled by a bare
modifier, make `Shift+F2` the preferred previous karaoke treatment key, and
replace Discord channel webhooks with local Discord profile Rich Presence.
The progress demo now spells out every temporary setting it demonstrates.
[Release notes](releases/PAFPlayer_v544_profile_help_and_tray_gallery_release_notes.md).

## V543 — October 14, 2026

Make `F2` rename the current audio file and optionally repair its exact path in
the current and neighboring playlists, with live HUD progress and verified
playlist backups. Reorganize and clarify Web Config, reverse live-log order,
confirm global-hotkey disabling, eliminate the literal `\\n\\n` fragment, and
keep tray-hover callback failures in the logfile instead of the console.
[Release notes](releases/PAFPlayer_v543_rename_and_web_config_release_notes.md).

## V542 — October 14, 2026

Complete the Test Tone TODO: add a native-output tone studio to Speaker
Expansion Matrix, `Ctrl+T` mode switching, held arrow/mouse editing, five
patterns, unlimited simultaneous independently editable tones, tone selection
and creation gestures, and named save/load sets with dated console previews.
[Release notes](releases/PAFPlayer_v542_test_tone_studio_release_notes.md).

## V541 — October 14, 2026

Add a 20-design tray-icon gallery to Web Config and the native right-click
menu, persist the selected design, and apply changes without restarting.
Make the artwork hover deliberate, non-overlapping, and click-through so it
cannot obstruct tray interaction. [Release notes](releases/PAFPlayer_v541_tray_icon_gallery_and_safe_hover_release_notes.md).

## V540 — October 14, 2026

Add working favorite/default controls for exact Playback Device selections and
Bar artwork blend modes. Repair the rejected **Auto-set to tallest** web action.
Replace the Floating Lyrics **EMX cfg** caption with a tooltip-equipped 🌐 link
to its Web Config section. Add a dedicated Discord setup help page that explains
secure webhook creation and the important distinction between channel webhook
posts and Discord profile Rich Presence. [Release notes](releases/PAFPlayer_v540_web_choice_marks_and_discord_help_release_notes.md).

## V539 — October 13, 2026

Repair the changelog's release ordering so all version entries appear in
reverse numerical chronology, newest first. Entries that share a version remain
together with the newer dated entry first. [Release notes](releases/PAFPlayer_v539_reverse_chronological_changelog_release_notes.md).

## V538 — October 13, 2026

Move the **Beat visual timing correction** millisecond value to an editable box
on the right of its slider, add an easy ±15 ms snap-to-zero zone, and make `0 ms`
the default. Phase-lock progress-bar beat lookup to the canonical millisecond
source timestamp shared by lyrics, spectrum, and playback progress, retaining
live spectrum only as a startup fallback. [Release notes](releases/PAFPlayer_v538_timestamped_progress_beats_release_notes.md).

## V537 — October 13, 2026

Make playlist resume bookmarks durable during playback: save the selected track
before decoder startup and checkpoint its playhead about every two seconds. This
fixes Ctrl+C/Ctrl+Break exits bypassing the prior save-on-`stopped` path and
relaunching on an unrelated shuffled song. [Release notes](releases/PAFPlayer_v537_durable_playlist_resume_release_notes.md).

## V536 — October 13, 2026

Restore adaptive progress-bar flashing during ordinary file playback by consuming
the current spectrum instead of depending exclusively on the precomputed beat
timeline. Color-intensity flashes now decay spatially behind the playhead instead
of coloring every filled cell identically. Repair 0-based Artwork Seaming
favorite/default validation. Rename **Tallest** to **Set to tallest** and add a
persistent **Auto-set to tallest** visualizer-row control that follows terminal
geometry changes. [Release notes](releases/PAFPlayer_v536_progress_reactivity_and_auto_rows_release_notes.md).

## V535 — October 13, 2026

Resume near-end playlist bookmarks fifteen seconds before the end instead of
restarting the track. Playlist bookmarks now remember their queue successor, so
if the bookmarked file disappears before the next launch, playback continues at
that next track (legacy bookmarks use the first remaining playlist entry). Add a
persisted **Fresh shuffle after** hour control to Web Config's Playback section;
the five-hour default remains unchanged. [Release notes](releases/PAFPlayer_v535_playlist_resume_and_shuffle_lifetime_release_notes.md).

## V534 — October 13, 2026

Add `--simulated-playlist-run PLAYLIST`, a three-minute audio-free stress run of
the real history shuffle, rotating queue, and bounded recent-track selection
core. Simulated visits remain process-local, progress is shown every ten seconds,
and a detailed JSON pass/fail audit is saved under `tests\reports`. The optional
`--simulated-playlist-seconds=N` override supports quick diagnostics and tests.
The simulator exposed an adjacent-album-alias hole, so launch cooldown visits now
persist both literal path and Artist+Song identity; alternate album copies are
rejected immediately rather than waiting for earned play history.
[Release notes](releases/PAFPlayer_v534_simulated_playlist_run_release_notes.md).

## V533 — October 13, 2026

Revalidate shuffle candidates whose per-path history was cached as “Never,” allowing shared Artist+Song history to enforce the three-hour cooldown across duplicate album, EP, and single copies.

## V532

Removed both `stripe` and `stripes` Emojimaxx substitutions so those words remain plain text.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v532_emojimaxx remove_stripes_release_notes.md`, `PAFPlayer_v532_emojimaxx remove_stripes.py`.

## V531

Removed the misleading `stripes` Emojimaxx substitution while retaining the separate singular `stripe` mapping.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v531_emojimaxx remove_stripes_release_notes.md`, `PAFPlayer_v531_emojimaxx remove_stripes.py`.

## V530 — October 12, 2026

Put elapsed/total time at the end of the lock-screen title row, reserve the second row for `🎤` lyrics, and optionally append `v530` after album/year. Existing enabled lock-screen users receive the version display once during migration; new/default configurations leave it off. When PAFPlayer is playing, its Windows media card now reclaims focus after Chrome has remained paused or stopped for 60 seconds, without interrupting actively playing Chrome media.

## V529 — October 12, 2026

Ship a versioned V529 lock-screen companion so first run detects and upgrades V528 without renewed elevation while the existing signing certificate remains trusted. Apply a subtle 2%-of-lyric-font rightward optical correction to Emojimaxx solution labels in Web Karaoke, Floating Lyrics, and Artwork Lyrics. [Release notes](releases/PAFPlayer_v529_lockscreen_auto_upgrade_and_solution_centering_release_notes.md).

## V528 — October 12, 2026

Embed the signed lock-screen MSIX, certificate, installer, and integration in the single-file player. Add `--install-lockscreen` and read-only `--check-lockscreen`; normal first run attempts the same guarded installation once per Windows user. [Release notes](releases/PAFPlayer_v528_single_file_lock_screen_installer_release_notes.md).

## V527 — reused version identifier

Two distinct historical entries use V527; both are retained below.

### V527 — October 13, 2026

Preserve the visible space after the `cut` Emojimaxx scissors glyph in Windows Terminal by adding the same terminal-only safety treatment used for other glyphs with inaccurate cell advances. [Release notes](releases/PAFPlayer_v527_cut_emojimaxx_spacing_release_notes.md).

### V527 — October 12, 2026

Move the canonical lock-screen Python module into `lockscreen/src` and update the installer, diagnostics, bundle synchronizer, and regression tests to use its new source location. Runtime behavior remains embedded in the single-file player. [Release notes](releases/PAFPlayer_v527_lock_screen_source_layout_release_notes.md).

## V526 — reused version identifier

Two distinct historical entries use V526; both are retained below.

### V526 — October 13, 2026

Remove the `sneak`/`sneaked`/`sneaking` Emojimaxx substitutions and clarify repeat-mode labels as `Repeat track`, `Repeat current folder`, `Repeat playlist`, and `Repeat OFF`. [Release notes](releases/PAFPlayer_v526_sneak_and_repeat_labels_release_notes.md).

### V526 — October 11, 2026

Rearrange lock-screen detailed status as artist/title, playback counter with current lyric, and album with optional year. Use an en dash between artist and title. [Release notes](releases/PAFPlayer_v526_lock_screen_lyric_clock_album_year_release_notes.md).

## V525 — October 11, 2026

Remove the `fund` and `talent` Emojimaxx substitutions. No active Emojimaxx TODO entries remain. [Release notes](releases/PAFPlayer_v525_emojimaxx_fund_talent_removal_release_notes.md).

## V524 — October 11, 2026

Fix tray-only hover-window startup after the main tray module configured `RegisterClassW` with its own ctypes structure. Enable the three-hour shuffle cooldown at selection time, searching one bounded queue rotation for a non-recent alternative and falling back safely for short/all-recent playlists. [Release notes](releases/PAFPlayer_v524_tray_hover_and_adaptive_shuffle_cooldown_release_notes.md).

## V523

household tray controls and native hover card.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v523_networked tray_controls_release_notes.md`, `PAFPlayer_v523_networked tray_controls.py`.

## V522

household tray controls.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v522_networked tray_controls_release_notes.md`, `PAFPlayer_v522_networked tray_controls.py`.

## V521

responsive audio controls.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v521_responsive audio_controls_release_notes.md`, `PAFPlayer_v521_responsive audio_controls.py`.

## V520

lock-screen album and playback counter.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v520_lock screen_album_and_counter_release_notes.md`, `PAFPlayer_v520_lock screen_album_and_counter.py`.

## V519

leaner visualizer output and earlier lock-screen lyrics.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v519_lean visualizer_and_early_lock_lyrics_release_notes.md`, `PAFPlayer_v519_lean visualizer_and_early_lock_lyrics.py`.

## V518

stable lock-screen lyric updates.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v518_lockscreen stable_lyrics_release_notes.md`, `PAFPlayer_v518_lockscreen stable_lyrics.py`.

## V517 — October 8, 2026

Remove the `goddamn` Emojimaxx substitution. [Release notes](releases/PAFPlayer_v517_emojimaxx_goddamn_removal_release_notes.md).

## V516 — October 8, 2026

Remove the low-value `answer`, `job`, `creep`, `halo`, and `speck` Emojimaxx substitutions, and replace the `guys` handshake sequence with a people-group symbol. No exact `lightly` mapping existed. [Release notes](releases/PAFPlayer_v516_emojimaxx_cleanup_release_notes.md).

## V515

managed lock-screen publisher.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v515_managed lockscreen_release_notes.md`, `PAFPlayer_v515_managed lockscreen.py`.

## V514

lock-screen background registration.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v514_lockscreen background_registration_release_notes.md`, `PAFPlayer_v514_lockscreen background_registration.py`.

## V513

versioned lock-screen app name.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v513_lockscreen versioned_name_release_notes.md`, `PAFPlayer_v513_lockscreen versioned_name.py`.

## V512

visible native lock-screen status.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v512_lockscreen visible_status_release_notes.md`, `PAFPlayer_v512_lockscreen visible_status.py`.

## V511

A replacement backup declares this version internally, but no dedicated release snapshot or release note was found. Its specific changes remain unknown.

Evidence: `PAFPlayer.py.bak.202610071348.replaced-by-chatgpt.bak` in `C:\BAT\PAFPlayer\releases`.

## V510

lock-screen identity, badges and activation diagnostics.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v510_lockscreen identity_and_badges_release_notes.md`, `PAFPlayer_v510_lockscreen identity_and_badges.py`.

## V509

lock-screen activation diagnostics.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v509_lockscreen activation_release_notes.md`, `PAFPlayer_v509_lockscreen activation.py`.

## V508 — October 6, 2026

Add a guided Windows 10 lock-screen companion installer that validates the signed package and bundled x64 dependencies, prompts before certificate trust, installs in the interactive user's account, and verifies registration. Provide a portable bundle and archive superseded lock-screen setup files and build output. [Release notes](releases/PAFPlayer_v508_lockscreen_installer_release_notes.md).

## V507 — October 5, 2026

Enlarge the screensaver settings window; add per-machine sign-in on normal fullscreen exit; require a one-second key or mouse-button hold, two key hits, or two seconds of pointer motion to dismiss. Player Close requests a normal sidecar exit so the sign-in setting can take effect. [Release notes](releases/PAFPlayer_v507_screensaver_exit_and_sign_in_release_notes.md).

## V506 — October 5, 2026

Apply the saved Floating Lyrics title duration at startup, retain changes through track transitions, and use 25 seconds when no preference exists. [Release notes](releases/PAFPlayer_v506_floating_title_persistence_release_notes.md).

## V505 — October 5, 2026

Add a packaged Windows 10 lock-screen companion with a detailed-status declaration, official-instance status verification, and a 15-minute background refresh task. The signed package awaits certificate trust and registration on this machine. [Release notes](releases/PAFPlayer_v505_lock_screen_companion_release_notes.md).

## V504

options on each tray computer.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v504_machine tray_options_release_notes.md`, `PAFPlayer_v504_machine tray_options.py`.

## V503

household tray clients and native tag viewer.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v503_remote tray_native_tag_viewer_release_notes.md`, `PAFPlayer_v503_remote tray_native_tag_viewer.py`.

## V502

web progress lyric hover.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v502_progress lyric_hover_release_notes.md`, `PAFPlayer_v502_progress lyric_hover.py`.

## V501

Floating Lyrics title duration persistence.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v501_floating lyrics_title_duration_persistence_release_notes.md`, `PAFPlayer_v501_floating lyrics_title_duration_persistence.py`.

## V500

tray double-click Play/Pause.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v500_tray double_click_release_notes.md`, `PAFPlayer_v500_tray double_click.py`.

## V499

Windows tray icon.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v499_tray release_notes.md`, `PAFPlayer_v499_windows tray.py`.

## V498

Focused solution-distance range.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v498_release notes.md`, `PAFPlayer_v498_solution distance_fifty_percent_range.py`.

## V497

Signed solution distance percentages.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v497_release notes.md`, `PAFPlayer_v497_signed solution_distance_percent.py`.

## V496 — October 4, 2026

Fix floating cues disappearing whenever an Emojimaxx solution is present; isolate solution rendering errors from the lyric. Add Artwork and Floating Lyrics solution controls to Web Config and place each surface's Emojimaxx settings on its own row. [Release notes](releases/PAFPlayer_v496_release_notes.md).

## V495 — October 4, 2026

Bound Ctrl+Break shutdown when the artwork GUI thread stalls, keep fast aborts during track transitions, and fix Web queue status reads during startup. [Release notes](releases/PAFPlayer_v495_release_notes.md).

## V494 — October 4, 2026

Add independent Floating, Web, and Artwork Lyrics solution size, distance, over/under, color, opacity, and lyric-color inheritance controls. Split mixed-coverage emoji runs for font fallback. Shorten queue lock sections implicated in slow track handoffs. [Release notes](releases/PAFPlayer_v494_release_notes.md).

## V493

track handoff profiling.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v493_release notes.md`, `PAFPlayer_v493_track handoff_profiling.py`.

## V492 — October 4, 2026

Align floating teeny answers with mixed-font lyrics, fall back to Segoe UI Symbol for missing emoji-font glyphs, and save only changed settings at track handoff. [Release notes](releases/PAFPlayer_v492_release_notes.md).

## V491

Removed the nonexistent EmojiMaxx configuration buttons from the web Artwork and Floating Lyrics sections while retaining the real controls.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v491_release notes.md`.

## V490

Floating teeny solutions.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v490_release notes.md`, `PAFPlayer_v490_floating teeny_solutions.py`.

## V489

Volume keys and bass-lock persistence.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v489_release notes.md`, `PAFPlayer_v489_volume keys_bass_lock_persistence.py`.

## V488

Console volume entry.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v488_release notes.md`, `PAFPlayer_v488_console volume_entry.py`.

## V487

Restored the intermediate half-scrolled frame during sequential Console Karaoke line changes by matching the scroll step to its 5 Hz refresh cadence.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v487_release notes.md`.

## V486 — October 1, 2026

Fuse exact luma artwork composition, reduce Ghost Frames allocations, cache lyric fonts and restart floating color pacing on cue changes. Short actual-terminal renderer tests reached 59.7/89.8/118.5 FPS at 60/90/120 targets; sustained full-player results remain unverified. Sandbox-only release. [Validation and limits](releases/PAFPlayer_v486_release_notes.md).

## V485 — October 1, 2026

Accelerate artwork-cell composition and native delta encoding without changing visual settings; use high-resolution frame pacing on Windows Python 3.10. Avoid audio restarts for inactive bass preferences and reduce bass-settings registry polling. The actual-terminal, real-spectrum renderer benchmark reached 59.9/85.2/91.9 FPS at 60/90/120 targets; full-player post-restart throughput is not yet verified. [Release notes and validation](releases/PAFPlayer_v485_release_notes.md).

## V484

Restored the intermediate half-scrolled frame during sequential Console Karaoke line changes by matching the scroll step to its 5 Hz refresh cadence.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v484_release notes.md`, `PAFPlayer_v484_instant_ctrl_break_cleanup.py`.

## V483

Reorganized web Playback rows: Volume leads the second row; bass boost/reduce has its own row; locked-bass reduction has its own checkbox-and-slider row.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v483_release notes.md`.

## V482

Based on V481; retains bass-while-locked and floating-title-duration changes.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v482_release notes.md`, `PAFPlayer_v482_fixed rows_and_windows_lyrics.py`.

## V481

Added a functioning Bass Reduction while Locked checkbox with a dependent 0–100% reduction slider.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v481_release notes.md`.

## V480

keep playing after current-track removal.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v480_release notes.md`.

## V479

Floating Lyrics center-button chrome fix.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v479_release notes.md`.

## V478

quiet web visualizer initialization.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v478_release notes.md`, `PAFPlayer_v478_floating lyrics_center_over_visualizer.py`.

## V477

web visualizer toggle interaction.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v477_release notes.md`.

## V476

direct screensaver bridge launch.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v476_release notes.md`, `PAFPlayer_v476_next track_title_seconds.py`.

## V475

preserve console output during shutdown.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v475_release notes.md`, `PAFPlayer_v475_web error_reporting.py`.

## V474 — September 29, 2026

Added an optional standalone visual screensaver with timed lyrics, artist/title, artwork brightness and local Show/Close controls. Default off; keeps existing configuration IDs. Separate process, bounded polling/images and Windows preview support. [Architecture and manual checks](screensaver/README.md); [release validation](releases/PAFPlayer_v474_release_notes.md).

## V473

A replacement backup declares this version internally, but no dedicated release snapshot or release note was found. Its specific changes remain unknown.

Evidence: `PAFPlayer.py.bak.202609291554.replaced-by-chatgpt.bak` in `C:\BAT\PAFPlayer\releases`.

## V472

The surviving V472 file is a one-time integration script, not a full player snapshot. It embeds the visual screensaver module into V471, adds screensaver web routes and activity tracking, and updates the program version after checking and backing up the starting source. The resulting V472 source is not present in this archive.

Evidence: `PAFPlayer_v472_integrate.py` in `C:\BAT\PAFPlayer\releases`; not a full source snapshot.

## V471

live screen-lock bass transition.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v471_release notes.md`, `PAFPlayer_v471_before visual_screensaver.py`.

## V470

persistent Discord and sleep bass controls.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v470_release notes.md`, `PAFPlayer_v470_persistent_discord_and_bass_comfort.py`.

## V469

Reorganized the web control surface: Playlist and Tags appear before Console.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v469_release notes.md`, `PAFPlayer_v469_control_organization_and_rainbow_range.py`.

## V468

Made the web Tags section functional with an explicit Expand all tags.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v468_release notes.md`, `PAFPlayer_v468_web_tags_expander_and_artwork_rendering.py`.

## V467

Fixed the web Progress Bar control crash. progress_color_mode is now shared.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v467_release notes.md`, `PAFPlayer_v467_progress_control_stability_and_choice_cycle_layout.py`.

## V466

Sandbox fresh playlist start.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v466_release notes.md`, `PAFPlayer_v466_sandbox fresh_playlist_start.py`.

## V465

Progress controls and labels.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v465_release notes.md`, `PAFPlayer_v465_progress controls_and_labels.py`.

## V464

Choice controls restored.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v464_release notes.md`, `PAFPlayer_v464_choice controls_restored.py`.

## V463

Progress colors and HUD cleanup.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v463_release notes.md`, `PAFPlayer_v463_progress colors_and_hud_cleanup.py`.

## V462

Web controls and tags.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v462_release notes.md`, `PAFPlayer_v462_web controls_and_tags.py`.

## V461

configurable floating-track introduction.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v461_release notes.md`, `PAFPlayer_v461_configurable floating_track_intro.py`.

## V460

instant abort and floating-track introductions.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v460_release notes.md`, `PAFPlayer_v460_instant abort_and_floating_track_intro.py`.

## V459 — September 28, 2026

Preserve complete song endings at slower playback speeds by applying the native decoder's duration limit to source audio before tempo processing. Faster bounded segments also stop at their requested source end. Includes V458's memory and regression repairs. Verified with real decoded ending tones and natural-completion/drain tests; the full-suite report retains historical failures explicitly. [Validation and limits](PAFPlayer_v459_release_notes.md).

## V458 — September 28, 2026

Bound cover-art retention and coalesce stale popup presentation work to prevent session growth. Repair partial console writes, noninteractive history reports, release identity, and legacy entry-point routing. Add full-suite discovery and on-demand memory diagnostics. The release notes report accelerated retention/frame measurements and the remaining historical test failures explicitly. [Validation and limits](PAFPlayer_v458_release_notes.md).

## V457

Bundled feature modules into the single-file player through an import finder and loader, allowing the archived release to run without separate feature files.

Evidence: compared V456→V457 archived source; added `_PAFBundledFeatures`, `find_spec`, `create_module`.

## V456 — September 25, 2026

Released the work already started from the V455 TODO pass: queue editing and single-instance handoff, managed drops/uploads, guided repair, folder monitoring, render books, teeny EmojiMaxx solutions, redacted live logs, opt-in Discord and CUDA experiments, Windows media settings (off by default), DCC backup/path reporting, cursor cleanup, throb persistence, and web/artwork polish. Thirty-three focused tests pass. Sixty TODO entries were completed/verified; 21 untouched entries remain. GPU acceleration and Windows lock-screen appearance require optional backends and are not claimed as live-verified. [Changes, commands, and validation limits](PAFPlayer_v456_release_notes.md).

## V455

Reorganized the web configuration into tabs and adjusted artwork controls and beat-timing presentation; the added regression check covers the tab layout and those controls.

Evidence: compared V454→V455 archived source; tests `test_v455_web_tabs_artwork_controls_and_beat_polish`.

## V454

Made Ctrl+Break restore the console cursor promptly and skip shutdown waits that delayed interruption; close paths received the same cleanup handling.

Evidence: compared V453→V454 archived source; added `close`, `close`, `close`; tests `test_v454_ctrl_break_restores_cursor_and_skips_slow_shutdown_waits`.

## V453

Expanded the web configuration tabs and frequency-warp presets, with additional layout and control polish; the diff includes a dedicated web-tab regression check.

Evidence: compared V452→V453 archived source; added `stored_lastfm_username`, `set_stored_lastfm_username`, `lastfm_profile_url`; tests `test_v453_web_tabs_frequency_warp_and_polish_contract`.

## V452

Added guarded, bidirectional loudness matching for external media so PAFPlayer volume can track external playback without an unsafe feedback loop.

Evidence: compared V450→V452 archived source; added `loudness_match_volume`, `loudness_fallback_volume`, `safety_duck`; tests `test_v452_external_media_loudness_match_is_guarded_and_bidirectional`.

## V451

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V450

Curated EmojiMaxx cow and lotus substitutions; the archived source adds a regression check for the selected replacements.

Evidence: compared V448→V450 archived source; added `_paf_registry_location`, `_paf_registry_path`, `_paf_registry_query_new_only`; tests `test_v450_emojimaxx_cow_and_lotus_curation`.

## V449

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V448

Reordered web playback controls into the requested rows. This archived source still used the pre-migration registry values; it is the last comparable snapshot before the registry change.

Evidence: compared V447→V448 archived source; tests `test_v448_web_playback_controls_have_requested_row_order`.

## V447

Fixed native audio endpoint mute probing to read the mute state without invoking SetMute; a regression check guards that read-only behavior.

Evidence: compared V445→V447 archived source; added `normalized_learned_title_selector`, `hud_play_song_anchor`, `align_hud_value_anchors`; tests `test_v447_native_audio_probe_reads_mute_without_calling_setmute`.

## V446

Added Global Config profiles and Developer’s Choice, corrected the console Pause/Unpause message, and made `PAFPlayer.py` the canonical source.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v446_release_notes.md`.

## V445

V445 — Pause reasons and artwork-detail applicability.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v445_release_notes.md`, `PAFPlayer_v445_pause_reasons_artwork_controls.py`.

## V444

V444 — V427 plus the console row-alignment fix only.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v444_release_notes.md`, `PAFPlayer_v444_v427_console_row_fix_only.py`.

## V443

Half-cell artwork performance and console stability.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v443_release_notes.md`, `PAFPlayer_v443_halfcell_artwork_native_console.py`.

## V442

Scheduled console-overlay painting.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v442_release_notes.md`, `PAFPlayer_v442_scheduled_console_overlay_painting.py`.

## V441

Atomic DRCS console chunks.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v441_release_notes.md`, `PAFPlayer_v441_atomic_drcs_console_chunks.py`.

## V440

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V439

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V438

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V437

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V436

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V435

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V434

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V433

restore artwork transport performance.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v433_release_notes.md`, `PAFPlayer_v433_restore_artwork_transport_performance.py`.

## V432

artwork delta-background safety.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v432_release_notes.md`, `PAFPlayer_v432_artwork_delta_background_safety.py`.

## V431

ANSI-safe visualizer chunking.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v431_release_notes.md`, `PAFPlayer_v431_ansi_safe_console_chunking_last_beore_v437_which-was_stable-but-didn’t-save.py`.

## V430 — September 22, 2026

Completed the active TODO list: removed the requested low-value Emojimaxx word substitutions, corrected `ladies` to use a distinct feminine mapping, and bounded/flushed large Unicode writes to real Windows console streams so half-block artwork cannot become replacement characters. Binary terminal payloads and optional direct writes now preserve all bytes across partial writes; adapters that return `None` after accepting text no longer abort playback. Eight new focused regressions plus the prior V416/V429 checks pass. [Details and validation limits](play_audio_file_v430_release_notes.md).

## V429 — September 22, 2026

Added the missing circled ten (❿) to Windows Terminal's generated-number spacing rule, fixing the unprotected gap in `ten of`. Extended the former 1–9 regression through 10 and added screenshot-phrase/wrapping/color tests; 13 focused checks pass. Preserves V428. [Details and verification limits](play_audio_file_v429_release_notes.md).

## V428

fast Ctrl+Break shutdown.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v428_release_notes.md`, `PAFPlayer_v428_fast_ctrl_break_shutdown.py`.

## V427

attribute-rule alternation repair.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v427_release_notes.md`, `PAFPlayer_v427_attribute_trailing_alternation.py`.

## V426

audible VLC resume.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v426_release_notes.md`, `PAFPlayer_v426_audible_vlc_resume.py`.

## V425

Filtered a Nest camera's ‘Live video from your Nest camera’ media session out of the active-audio monitor. The media probe now reads each session title before deciding whether its app family should count, and the HUD-row handling is adjusted with that exclusion.

Evidence: compared V424→V425 archived source.

## V424

compact HUD diagnostics.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v424_release_notes.md`, `PAFPlayer_v424_compact_hud_diagnostics.py`.

## V423

paused HUD controls and asynchronous console feedback.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v423_release_notes.md`, `PAFPlayer_v423_hud_pause_reasons_async_feedback.py`.

## V422

external-media pause reasons.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v422_release_notes.md`, `PAFPlayer_v422_external_media_pause_reasons.py`.

## V421 — September 21, 2026

Restored immediate manual Play/Space after automatic pause. Already-playing background applications are ignored at startup; overrides apply only to current applications and expire independently after inactivity, so newly started VLC can still interrupt an overridden Chrome video. Retains automatic 15-second fade and manual Pause/Stop ownership. 51 focused tests and real-worker manual-resume validation passed. [Details and detection limits](play_audio_file_v421_release_notes.md).

## V420 — September 21, 2026

Removed the Play/resume bypass that could disable external-media priority indefinitely while a browser stayed active. Enabled automatic pause now keeps competing media in priority; manual Pause/Stop ownership and the configured fade remain. Added decision diagnostics and verified actual audio-worker shutdown with live Chrome and VLC. Preserves V419's album-art spacing repair. [Validation and behavior](play_audio_file_v420_release_notes.md).

## V419

album-art emoji spacing.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v419_release_notes.md`, `PAFPlayer_v419_album_art_emoji_spacing.py`.

## V418 — September 21, 2026

Fixed browser detection's dependency on a failing helper: native Windows audio/Winamp monitoring now works independently, while an optional media-session reader provides silent-playback state. Audible tabs override conflicting paused-tab reports. Added helper diagnostics, stale-feed handling and Edge application-ID recognition; preserved manual pause ownership and the 15-second fade. [Details and live validation](play_audio_file_v418_release_notes.md).

## V417 — September 21, 2026

Added WAWI-compatible GET/HEAD transport URLs and legacy state output for the existing Winamp BAT scripts. Stop now resets and waits for Play without closing the web session. Filename clicks open Explorer locally and download remotely; a small adjacent download button always saves the original audio. See [release notes](play_audio_file_v417_release_notes.md) for setup, exact semantics, and validation.

## V416 — September 20, 2026

Completed the saved TODO pass; added consumed-sample playback clocks, future browser spectrum delivery and independent popup cue scheduling; eliminated stale/silence beat pulses; preserved Windows Terminal safety spaces through sung-line wrapping; retained rapid/held seeks; clarified J/Insert selection behavior; curated EmojiMaxx; corrected control icons/URL display; added persisted artwork seam strategies 0–5; and added read-only external-media detection with automatic pause/resume, manual-pause ownership, and a persisted 15-second audio fade setting. See [detailed release notes](play_audio_file_v416_release_notes.md) for decisions and validation limits.


This changelog was reconstructed from the recoverable project artifacts: the illustrated comprehensive manual and documentation archive through V30; the V97 source/supplement; the V100–V110 app-and-docs releases and canonical merged manuals; V111–V112 source/tests/docs; embedded regression contracts that preserve behavior from earlier releases; and the recovered visual-reference assets. It does not invent change details for release numbers that have no standalone or embedded evidence.

## V415

The V416 release notes refer to a saved V415 experiment. The archived file named V415 still declares V414 internally, so V415 behavior and release status remain unverified.

Evidence: `PAFPlayer_v415_up_windows_terminal_spacing.py` in `C:\BAT\PAFPlayer\releases`; `PAFPlayer_v416_release_notes.md`.

## V414

Added explicit repeat and shuffle play-order modes, including Repeat 1, Repeat Folder, Repeat playlist, Sequential, history shuffle, random shuffle, and Repeat OFF. Added actions to cycle modes forward, backward, or by double action, with bounded saved mode values.

Evidence: compared V413→V414 archived source.

## V413

Added a Repeat transport button and a playback-speed selector to the web interface. The repeat state is reflected in the button, and changing speed dispatches the existing web-set action.

Evidence: compared V412→V413 archived source.

## V412

Removed extra control and status redraws from the volume restart path, reducing work done during a volume adjustment.

Evidence: compared V411→V412 archived source.

## V411

Carried the current DRCS and Sixel enable state into visualizer transitions so a transition uses the live state rather than a stale captured value.

Evidence: compared V410→V411 archived source.

## V410

Kept visualizer command-line choices session-only and added a Ctrl+Alt+V visualizer toggle to both character and asynchronous key handling, with a latch that prevents duplicate actions while held.

Evidence: compared V409→V410 archived source.

## V409

Reduced pause/resume audio-start latency by capping the buffer used on resume at 50 ms while leaving normal launches on their configured buffer.

Evidence: compared V408→V409 archived source.

## V408

Made shuffle and repeat state visible and unambiguous: the web transport uses distinct active styling, the console announces the resulting enabled/disabled state, and the help/status display shows both modes.

Evidence: compared V407→V408 archived source; added `announce_loop_state`; tests `test_v408_shuffle_loop_web_console_and_help_state_clarity`.

## V407

Centralized detection of command-line preference overrides and kept those values in runtime settings only. Saving through the web interface no longer writes temporary CLI choices into global preferences.

Evidence: compared V406→V407 archived source; added `command_line_player_setting_override_keys`; tests `test_v407_all_cli_preference_overrides_are_session_only`.

## V406

Kept --no-visualizers and related visualizer command-line overrides temporary for the current run, using a runtime settings merge rather than persisting them.

Evidence: compared V405→V406 archived source; added `merge_runtime_player_settings`; tests `test_v406_visualizer_cli_overrides_are_not_persisted`.

## V405

lyric control labels.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v405_lyric_control_labels_report.md`, `PAFPlayer_v405_lyric_control_labels.py`.

## V404

floating lyrics speed and sync.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v404_floating_lyrics_speed_and_sync_report.md`, `PAFPlayer_v404_floating_lyrics_speed_and_sync.py`.

## V403

Changed the default visualizer/karaoke compositing mode to the legacy layout, validated the saved mode range, and regrouped web controls into their playback and visualizer sections.

Evidence: compared V402→V403 archived source.

## V402

Moved buffered stereo and MatrixMixer playback into a separate audio worker process; added bar-opacity controls and native popup placement recovery.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v402_verification_report.md`, `PAFPlayer_v402_isolated_audio_and_window_recovery.py`.

## V401

V401 visualizer bar artwork performance.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v401_performance_report.md`, `PAFPlayer_v401_batched_bar_artwork_colors_VISUALIZER_AT_59FPS_EVEN_WITH_BAR_ARTWORK_ON!!!!_RELEASE.py`.

## V400

Expanded help output to resolve named/default audio endpoints, depth and multi-output options, and to wrap long playlist details cleanly.

Evidence: compared V399→V400 archived source; added `windows_default_render_device_name`, `_IMMDevice`, `_IMMDeviceEnumerator`; tests `test_v400_help_output_resolves_devices_depth_multioutput_and_wraps_playlist`.

## V399

Changed EmojiMaxx directional replacements to the requested heavy arrows.

Evidence: compared V398→V399 archived source; tests `test_v399_emojimaxx_uses_requested_heavy_directional_arrows`.

## V398

Added one Windows Terminal safety cell after EmojiMaxx glyphs written through the console path to prevent adjacent text from visually crowding them.

Evidence: compared V397→V398 archived source; added `windows_terminal_emojimax_replacement`; tests `test_v398_write_emojimaxx_gets_one_windows_terminal_safety_cell`.

## V397

Added a faster artwork-color lookup for visualizer bars so the 60 fps bar path can reuse its color result.

Evidence: compared V396→V397 archived source; added `artwork_bar_color`.

## V396

Highlighted the experimental cursive-fix control in the web karaoke section with its own color treatment so it remains visually distinct.

Evidence: compared V395→V396 archived source.

## V395

Made a missing playlist produce a warning and tightened floating-lyrics animation safety and render debouncing, reducing work on the playback path.

Evidence: compared V394→V395 archived source; added `floating_lyrics_animation_is_safe`, `floating_lyrics_render_debounce_ms`, `publish_notice`.

## V394

V394 console visualizer performance.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v394_performance_report.md`, `PAFPlayer_v394_console_visualizer_VISUALIZER_60FPS_RELEASE_CANDIDATE.py`.

## V393

Moved selected DRCS twin-glyph table construction out of the per-cell path and into one per-frame build for the console artwork visualizer.

Evidence: compared V392→V393 archived source.

## V392

Added --simple and --light as lightweight-run presets that disable console and popup artwork, the web server, the now-playing sidecar, and visualizers for the current launch.

Evidence: compared V391→V392 archived source.

## V391

Added --no-chafa-album-art-in-console to suppress the pre-play Chafa artwork grid while retaining popup artwork, web artwork, and visualizers. The same source also adjusts several EmojiMaxx mappings.

Evidence: compared V390→V391 archived source.

## V390

Kept EmojiMaxx numbers out of unsupported chess-symbol glyphs, preserved spacing in compound replacements, and used spare HUD cells to align metadata colons.

Evidence: compared V389→V390 archived source; added `align_label_to_reference_if_close`; tests `test_v390_emojimax_numbers_avoid_unsupported_chess_symbol_block_and_keep_compound_spacing`, `test_v390_dead_kennedys_hud_uses_spare_cells_for_obvious_colon_alignment`.

## V389

Staged a new microtile DRCS bank with its first target frame in one atomic terminal transaction, avoiding visible cells being redefined mid-transition.

Evidence: compared V388→V389 archived source; added `atomic_drcs_frame_transition_payload`; tests `test_v389_drcs_bank_and_first_target_frame_commit_atomically`, `test_v389_microtile_detail_changes_stage_drcs_instead_of_redefining_visible_cells`.

## V388

Added web controls for artwork and floating-lyrics window order, including bring-to-front and persistent topmost settings.

Evidence: compared V387→V388 archived source; added `art_topmost`, `set_art_topmost`, `bring_floating_to_foreground`; tests `test_v388_web_lyric_window_controls_are_four_buttons_in_requested_order`, `test_v388_art_and_floating_topmost_web_contract`.

## V387

Prioritized local artwork fallbacks by cover/folder/disc/band names and made floating-lyrics animation safer; Ctrl+Home/End no longer arms an unrelated visualizer overlay.

Evidence: compared V386→V387 archived source; added `floating_lyrics_animation_interval_ms`, `ensure_floating_color_animation`; tests `test_v387_local_art_fallback_priority_matches_cover_folder_disc_band_other`, `test_v387_ctrl_end_and_home_do_not_arm_visualizer_overlay`.

## V386

Added web controls for floating-lyrics topmost state and a separate visualizer bar-artwork switch with its dependency reflected in the UI.

Evidence: compared V385→V386 archived source; added `floating_topmost`, `set_floating_topmost`; tests `test_v386_floating_lyrics_web_topmost_control_contract`, `test_v386_visualizer_bar_artwork_is_dedicated_switch_and_dependency`.

## V385

Persisted the visualizer overlay-message switch, enabled by default, and curated EmojiMaxx replacements by removing shovel and using sunrise for daylight.

Evidence: compared V384→V385 archived source; tests `test_v385_visualizer_overlay_messages_is_visualizer_control_default_on_and_persisted`, `test_v385_emojimaxx_removes_shovel_and_uses_sunrise_for_daylight`.

## V384

Split visualizer layer switches from alert controls, added an alert master control, and separated artwork-detail choices from the broken/experimental section.

Evidence: compared V383→V384 archived source; tests `test_v384_console_visualizer_layer_switches_and_alert_master_contract`, `test_v384_visualizer_art_detail_split_and_broken_section_bottom_contract`.

## V383

Grouped exact artwork-detail modes before approximate ones and spent adaptive 2×4 DRCS slots on glyphs needed by the current artwork for smoother transitions.

Evidence: compared V382→V383 archived source; added `art_detail_is_seamless_adaptive`, `art_detail_active_drcs_codebook`, `_art_detail_fixed_drcs_char_by_mask`; tests `test_v383_exact_art_detail_modes_are_grouped_before_approximate_modes`, `test_v383_adaptive_seamless_2x4_spends_drcs_slots_on_current_artwork`.

## V382

Added selectable/favorite microtile detail modes with explicit default markings; adaptive exact modes avoid substituting a merely near mask for a requested mask.

Evidence: compared V381→V382 archived source; added `art_detail_is_adaptive_exact`, `art_detail_uses_unicode_glyphs`, `_resample_art_detail_samples`; tests `test_v382_microtile_dropdown_order_labels_default_and_marks`, `test_v382_adaptive_exact_modes_never_use_nearest_wrong_mask`.

## V381

Placed an absolute cursor fence after each hybrid Unicode artwork cell to keep the next cell aligned, and removed interaction feedback from the help overlay.

Evidence: compared V380→V381 archived source; added `append_cell_glyph`; tests `test_v381_hybrid_unicode_cells_get_absolute_next_column_fences`, `test_v381_help_overlay_has_no_interaction_feedback_box`.

## V380

Added hybrid Unicode/DRCS artwork-detail modes and a glyph pool able to emit either representation while preserving exact selections.

Evidence: compared V379→V380 archived source; added `art_detail_is_hybrid`, `art_detail_base_mode`, `art_detail_drcs_layout_mode`; tests `test_v380_hybrid_art_detail_modes_are_exposed_and_exact`, `test_v380_hybrid_pool_can_emit_both_unicode_and_drcs`.

## V379

Expanded microtile artwork detail to seven density choices and packed their masks into fixed-cell DRCS glyphs.

Evidence: compared V378→V379 archived source; added `_normalize_art_detail_layout_mode`, `art_detail_geometry`, `art_detail_horizontal_subcells`; tests `test_v379_microtile_detail_has_seven_selectable_density_modes`, `test_v379_all_art_detail_modes_use_fixed_cell_drcs`.

## V378

Completed the dense-art soft-font codebook and constrained mask approximation to at most one subcell, keeping DRCS cells safe for terminal rendering.

Evidence: compared V377→V378 archived source; added `define_twin_visualizer_drcs_patterns`, `twin_drcs_char_for_layout`, `_canonical_dense_art_mask`; tests `test_v378_dense_art_soft_font_is_complete_and_cell_safe`, `test_v378_dense_art_mask_codebook_is_never_more_than_one_subcell_wrong`.

## V377

Switched to the normal Unicode character set only for dense-art modes that actually emit Unicode mosaics, leaving pure DRCS modes in their expected set.

Evidence: compared V376→V377 archived source; added `art_detail_uses_unicode_glyphs`, `append_cell_glyph`; tests `test_v377_dense_art_modes_use_normal_unicode_charset`, `test_v377_dense_art_renderer_switches_charset_only_for_unicode_mosaics`.

## V376

Made row-delta artwork repaints use absolute, wrap-safe positioning; retained multi-art strip tiling and removed dither work from the hot path.

Evidence: compared V374→V376 archived source; tests `test_v376_row_delta_artwork_repaint_is_wrap_safe_and_absolute`, `test_v376_keeps_multi_art_strip_tiling_and_removes_hotpath_dither`.

## V375

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V374

Published offset-adjusted karaoke cue deadlines with artwork frames and prepared the next artwork cue early without advancing the other lyric surfaces.

Evidence: compared V373→V374 archived source; added `artwork_karaoke_render_lead_seconds`, `_calibrate_artwork_karaoke_render_lead`; tests `test_v374_karaoke_frame_exposes_offset_adjusted_cue_deadlines`, `test_v374_artwork_prepares_next_cue_without_advancing_other_surfaces`.

## V373

Added a solid octant artwork-detail mode and RGB dithering that breaks up flat quantization bands in dense artwork.

Evidence: compared V372→V373 archived source; added `art_octant_char`, `_art_detail_dither_quantize_rgb`; tests `test_v373_octant_mode_is_solid_not_braille_and_maps_all_masks`, `test_v373_art_detail_dither_breaks_flat_32_step_bands`.

## V372

Added a native vector path for large artwork-window lyrics, logarithmic font fitting, and cached Pillow fonts to reduce 4K text-rendering cost.

Evidence: compared V371→V372 archived source; added `candidate`, `candidate`, `measure`; tests `test_v372_large_artwork_lyrics_have_native_vector_fast_path`, `test_v372_font_fitting_is_logarithmic_and_pillow_fonts_are_cached`.

## V371

Fixed smooth-audio settings ownership in play_audio_file and passed those settings from main dispatch to the renderer.

Evidence: compared V370→V371 archived source; tests `test_v371_play_audio_file_owns_smooth_audio_settings`, `test_v371_main_dispatch_passes_smooth_audio_settings`.

## V370

Reconciled track duration metadata, compacted URL display without losing its link target, and used available HUD space rather than a separate URL row where possible.

Evidence: compared V369→V370 archived source; added `_mutagen_duration_seconds`, `_reconcile_mp3_duration`, `compact_url_display_text`; tests `test_v370_url_display_hides_implied_scheme_and_www_but_keeps_link_target`, `test_v370_rammstein_hud_uses_spare_space_instead_of_a_separate_url_row`.

## V369

Used a global count for plural EmojiMaxx substitutions and adjusted the stereo waveOut format/command path for smoother audio playback.

Evidence: compared V368→V369 archived source; added `_emojimax_plural_singular_key`, `_emojimax_existing_plural_repeat_count`, `emojimax_replacement_for_key`; tests `test_v369_plural_emojimax_uses_global_count`, `test_v369_stereo_waveout_format_and_command`.

## V368

Kept floating-window outer geometry fixed in edit mode, stopped a focus loop, and added a foreground fail-safe when focus is lost.

Evidence: compared V367→V368 archived source; added `floating_window_is_foreground`, `cancel_floating_focus_watch`, `floating_focus_watch`; tests `test_v368_floating_edit_mode_preserves_outer_geometry_and_avoids_focus_loop`, `test_v368_floating_focus_loss_has_foreground_fail_safe`.

## V367

Curated EmojiMaxx symbols and spacing, including circled-number safety cells, while refining HUD alignment and floating-window controls.

Evidence: compared V366→V367 archived source; added `save_player_setting_value`, `hud_metadata_label_colons_by_row`, `hud_metadata_label_colons`; tests `test_v367_emojimaxx_curated_remove_planets_and_add_shine`, `test_v367_circled_number_terminal_spacing_has_two_generated_safety_cells`.

## V366

Expanded the EmojiMaxx CLI preview into three stages, adjusted floating-lyrics sizing controls, and kept dense Album/Comment HUD rows right-aligned.

Evidence: compared V365→V366 archived source; added `load_external_floating_lyrics_autosize`, `save_external_floating_lyrics_autosize`, `load_external_floating_lyrics_font_scale`; tests `test_v366_emojimaxx_cli_preview_has_three_stages_and_resets_every_normal_row`, `test_v366_freezepop_one_cell_album_comment_alignment_keeps_album_value_right_edge`.

## V365

Extended the EmojiMaxx CLI preview to print both the normal substituted lyric and a double-height karaoke preview using the terminal's upper/lower line sequences.

Evidence: compared V364→V365 archived source.

## V364

Pruned the early EmojiMaxx survey mappings so the reviewed words remain literal lyric text instead of receiving uncertain substitutions.

Evidence: compared V363→V364 archived source.

## V363

The compared source changes release identity strings only; no playback or UI code change is visible in the surviving V362→V363 diff. Its ‘extended release summary’ title cannot be verified from this source alone.

Evidence: compared V362→V363 archived source.

## V362

full --emojimaxx terminal preview.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v362_documentation.md`, `PAFPlayer_v362_recycled_v108_historical_manual.py`.

## V361

Rendered eighteen as two circled digit glyphs and removed the unwanted ‘seem’ EmojiMaxx replacement.

Evidence: compared V360→V361 archived source; tests `test_v361_removes_seem_and_uses_two_circled_digits_for_eighteen`.

## V360

The compared source changes release identity strings only; no command-line parser or help-text change is visible in the surviving V359→V360 diff.

Evidence: compared V359→V360 archived source.

## V359

Added an EmojiMaxx command-line preview that takes one text argument, prints the transformed text, and exits without starting playback.

Evidence: compared V358→V359 archived source; tests `test_v359_emojimaxx_cli_preview_prints_and_exits`, `test_v359_emojimaxx_cli_preview_requires_one_text_argument`.

## V358

Extended enclosed-number handling through fifty, including the reviewed eighteen glyph, and removed the unwanted ‘seem’ replacement.

Evidence: compared V357→V358 archived source; tests `test_v358_removes_seem_and_uses_enclosed_eighteen`.

## V357

Applied user-reviewed EmojiMaxx survey curation for entries 001–020 and recorded rejected mappings so they do not return accidentally.

Evidence: compared V356→V357 archived source; added `_v357_rejected_emojimax_mapping`; tests `test_v357_survey_curation_and_requested_emojimax_replacements`.

## V356

Made the web karaoke line auto-expand for the anniversary presentation and added readable descriptions for Unicode survey sequences.

Evidence: compared V355→V356 archived source; added `describe_unicode_sequence`; tests `test_v356_anniversary_auto_expand_and_unicode_survey_descriptions`.

## V355

Inserted the circled-number spacing workaround only for Windows Terminal substitutions, avoiding extra spaces in unrelated lyric text.

Evidence: compared V354→V355 archived source; added `windows_terminal_emojimax_spacing_enabled`, `windows_terminal_emojimax_replacement`; tests `test_v355_circled_number_bugfix_space_is_terminal_and_substitution_only`.

## V354

Changed the pause action's on-screen interaction label to ‘Pause’ when the pause toggle is pressed.

Evidence: compared V353→V354 archived source.

## V353

Anchored the final HUD field to the right edge whenever there is room, while preserving the minimum gap from the preceding field.

Evidence: compared V352→V353 archived source.

## V352

Included Album among the HUD metadata fields allowed to anchor at the right edge of a row.

Evidence: compared V351→V352 archived source.

## V351

Treated circled-number symbols as text-width glyphs during HUD/lyric cell measurement instead of letting them take emoji-width spacing.

Evidence: compared V350→V351 archived source.

## V350

Closed the all-tags view when navigation or natural track completion changes the active track, instead of carrying the old tag panel into the next track.

Evidence: compared V349→V350 archived source.

## V349

Added continuous volume adjustment while a volume key is held: repeat begins after about 320 ms and continues every 85 ms until release.

Evidence: compared V348→V349 archived source.

## V348

Stopped toggling the native Tk artwork-window style on focus changes. Keeping the HWND style stable prevents focus and position bounce, while the transparent wrapper still supplies the focus border.

Evidence: compared V347→V348 archived source.

## V347

Added alignment of HUD labels to reference columns. The archived filename flags this artwork-window build as unusable; the source diff alone does not establish a safe release.

Evidence: compared V346→V347 archived source; added `align_label_to_reference`.

## V346

Added popup focus chrome that can be set without relying on implicit window-state changes, alongside popup-control adjustments.

Evidence: compared V345→V346 archived source; added `set_native_focus_chrome`.

## V345

Centered Song between Act and a right-side metadata field, and Genre between Year and a right-side field, when the HUD row has enough space.

Evidence: compared V344→V345 archived source.

## V344

Routed web actions for popup karaoke through the playback action queue so the owner applies them in order.

Evidence: compared V343→V344 archived source; tests `test_v344_popup_karaoke_web_actions_reach_the_playback_queue`.

## V343

Restored natural left-to-right placement for ordinary metadata rows. Only selected tail fields take the right edge, avoiding large gaps in wide terminals.

Evidence: compared V342→V343 archived source.

## V342

Suppressed a startup interaction notice for web requests that lock or unlock artwork-color autoslide; the setting action still runs.

Evidence: compared V341→V342 archived source.

## V341

Made the album-art karaoke toggle a hard gate for artwork lyrics: when disabled, the current artwork lyric is cleared rather than rendered through an old state.

Evidence: compared V340→V341 archived source.

## V340

Delayed the visualizer interaction overlay for four seconds after startup and suppressed its notice for the dismiss action.

Evidence: compared V339→V340 archived source.

## V339

Removed the automatic EmojiMaxx substitution of ‘shocked’ with the surprised-face symbol.

Evidence: compared V338→V339 archived source.

## V338

Rendered floating karaoke lyrics immediately on the synchronization path instead of only scheduling a later floating-window render.

Evidence: compared V337→V338 archived source.

## V337

Shortened web karaoke status polling to 200 ms so browser lyrics follow the shared playback clock more closely.

Evidence: compared V336→V337 archived source.

## V336

Persisted the album-art popup karaoke enable switch and added helpers to apply its current state.

Evidence: compared V335→V336 archived source; added `load_external_album_art_karaoke_enabled`, `save_external_album_art_karaoke_enabled`, `artwork_karaoke_enabled`.

## V335

Added live web sections for artwork and floating lyrics, including controls that open their local configurators.

Evidence: compared V334→V335 archived source; added `lyrics_mode`, `open_karaoke_color_configurator`, `set_artwork_karaoke_enabled`; tests `test_v335_web_artwork_and_floating_sections_have_live_controls_and_config_actions`.

## V334

Made a missing playlist a warning followed by a clean return rather than an unhandled playback failure.

Evidence: compared V333→V334 archived source; tests `test_v334_missing_playlist_is_a_warning_and_clean_return`.

## V333

Moved decensor controls into the web sections for the windows they affect.

Evidence: compared V332→V333 archived source; tests `test_v333_web_decensor_controls_follow_their_destination_sections`.

## V332

Made the removal of the EmojiMaxx ‘forget’ mapping explicit and reversible.

Evidence: compared V331→V332 archived source; tests `test_v332_forget_emojimax_removals_are_explicit_and_reversible`.

## V331

Compacted the low end of the frequency warp and repeated the interaction feedback while the setting changes.

Evidence: compared V330→V331 archived source; tests `test_v331_frequency_warp_compacts_low_end_and_repeats_feedback`.

## V330

Suppressed track artwork for live visualizer inputs while retaining the user's stored artwork preferences for ordinary tracks.

Evidence: compared V329→V330 archived source; added `visualizer_track_artwork_allowed`; tests `test_v330_live_inputs_suppress_track_artwork_without_losing_settings`.

## V329

Added an HUD layout survey limited to colored placement algorithms so alternative arrangements can be compared without changing other presentation behavior.

Evidence: compared V328→V329 archived source; added `_hud_survey_fields`, `_hud_survey_render_field`, `_hud_survey_partition_fields`; tests `test_v329_hud_survey_compares_colored_placement_algorithms_only`.

## V328

Added a paged emoji-word survey with word/color listings and an export path for reviewing replacements.

Evidence: compared V327→V328 archived source; added `emojimax_live_substitutions_by_glyph`, `emoji_symbol_survey_log_path`, `build_emoji_symbol_survey`; tests `test_v328_emoji_survey_lists_words_colors_pages_and_exports`.

## V327

Curated EmojiMaxx 16-symbol mappings and added an interaction-feedback box with survey aliases.

Evidence: compared V326→V327 archived source; added `interaction_feedback_box_rows`, `start_interaction_visual_feedback`, `interaction_feedback_label`; tests `test_v327_emoji16_curations_box_cells_and_survey_aliases`.

## V326

Changed HUD row finalization to anchor each completed row's last field, with survey support for placement choices.

Evidence: compared V325→V326 archived source; added `finalize_hud_layout_rows`, `field_cells`, `colon_locations`; tests `test_v326_completed_hud_rows_anchor_their_last_field`.

## V325

Restored the normal terminal character set while drawing the volume feedback box border, preventing the bottom border glyphs from inheriting the visualizer's soft-font state.

Evidence: compared V324→V325 archived source.

## V324

Capped the EmojiMaxx symbol set to retain the most useful common replacements instead of allowing hundreds of low-value substitutions.

Evidence: compared V323→V324 archived source.

## V323

Preserved internal spaces in learned extra-tag values rather than collapsing distinct tag text.

Evidence: compared V322→V323 archived source; tests `test_v323_learned_extra_tag_preserves_internal_spaces`.

## V322

Added a callable emoji-symbol survey and removed or adjusted selected EmojiMaxx mappings.

Evidence: compared V321→V322 archived source; added `run_emoji_symbol_survey`.

## V321

Removed four reviewed EmojiMaxx associations that produced unwanted lyric substitutions.

Evidence: compared V320→V321 archived source; tests `test_v321_removes_four_requested_emojimaxx_associations`.

## V320

Added a red HUD alert when the active track lacks ReplayGain data, with a setting to disable that alert.

Evidence: compared V319→V320 archived source; tests `test_v320_missing_replaygain_is_a_disableable_red_hud_alert`.

## V319

Changed volume feedback so the readout blinks three times and the visualizer briefly throbs; adjusted karaoke fading and retained only the reviewed EmojiMaxx removals.

Evidence: compared V318→V319 archived source; added `feedback_rgb`, `volume_visualizer_brightness_factor`, `start_volume_visual_feedback`; tests `test_v319_restores_off_but_keeps_two_unclear_emojimax_removals`, `test_v319_volume_readout_blinks_three_times_and_visualizer_throbs`.

## V318

Made the volume readout inverse-blink exactly twice after an adjustment.

Evidence: compared V317→V318 archived source; added `volume_inverse_blink_phase`, `volume_status`; tests `test_v318_volume_readout_inverse_blinks_exactly_twice`.

## V317

Counted a short track played cleanly from start to end as a full play for local history and scrobbling even when its reported duration is bad; rejected three unclear EmojiMaxx substitutions.

Evidence: compared V316→V317 archived source; added `playback_ranges_cover_from_start`, `is_short_track_full_play`, `record_segment`; tests `test_v317_clean_full_short_play_logs_and_scrobbles_despite_bad_duration`, `test_v317_rejects_three_unclear_emojimax_substitutions`.

## V316

Recorded a clean natural end of malformed short audio in local history without treating it as a Last.fm scrobble.

Evidence: compared V315→V316 archived source; tests `test_v316_clean_eof_logs_malformed_short_audio_without_scrobbling`.

## V315

Added extra spacing after a sung circled number in the current double-height lyric line so Windows Terminal does not visually glue the number to the following word. Adjacent lyric lines retain their original spacing.

Evidence: compared V314→V315 archived source.

## V314

Cached shuffle metadata across process-cache resets and invalidated it when needed; rows with the same known filename identity avoid redundant metadata probes.

Evidence: compared V313→V314 archived source; added `playlist_shuffle_metadata_cache_path`, `_load_playlist_shuffle_metadata_cache`, `save_playlist_shuffle_metadata_cache`; tests `test_v314_same_identity_filename_rows_need_no_metadata_probe`, `test_v314_shuffle_metadata_cache_survives_process_cache_reset_and_invalidates`.

## V313

Accepted either Claire audio-processing API version attribute and parsed its numeric value defensively, improving compatibility with older helper modules.

Evidence: compared V312→V313 archived source.

## V312

Emojimaxx verb removals.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v312_emojimaxx_removals.md`, `PAFPlayer_v312_HUGE_ULTRA_SPEEDUPOPTIMIZATION_CODEX.py`.

## V311

Added dependency lookup and compatibility checks for Claire utility modules while carrying forward artwork motion, frozen-state, and learned-glyph work from the intervening snapshots. The archived predecessor gap prevents attributing every carried-forward change to V311 alone.

Evidence: compared V308→V311 archived source; added `clairecjs_dependency_search_dirs`, `_load_clairecjs_module_from_path`, `_clairecjs_dependency_api_ok`.

## V310

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V309

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V308

Unified shuffle-history identity resolution: bulk history can use Artist/Title when a filename bucket is missing, and the newest safe source wins when records disagree.

Evidence: compared V307→V308 archived source; added `playlist_history_resolve_authoritative_loaded`; tests `test_v308_bulk_history_uses_artist_title_when_filename_bucket_is_missing`, `test_v308_authoritative_history_uses_newest_safe_identity_source`.

## V307

Placed never-played tracks in bucket zero and known play dates into ten age deciles; recent-avoidance is disabled by default.

Evidence: compared V305→V307 archived source; tests `test_v307_recent_avoidance_is_disabled_by_default`, `test_v307_never_is_bucket_zero_and_known_dates_get_ten_deciles`.

## V306

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V305

Added an experimental choice for how cover-art detail blends into filled visualizer bars: legacy color mix, luminance detail, or a hybrid.

Evidence: compared V304→V305 archived source.

## V304

Repaired structured Last.fm history aliases only when Album and track-number evidence confirms a polluted pipeline suffix, avoiding unsafe Artist/Title merges.

Evidence: compared V303→V304 archived source; added `_playlist_history_track_number_hint`, `_playlist_history_polluted_suffix_matches_current_track`, `playlist_history_repair_polluted_lastfm_alias`; tests `test_v304_structured_lastfm_alias_repairs_pipeline_album_track_pollution`, `test_v304_structured_lastfm_alias_requires_album_and_track_proof`.

## V303

Added tenths-of-a-second karaoke offset controls and history-database merge/archival helpers; the diff also adjusts EmojiMaxx spacing.

Evidence: compared V302→V303 archived source; added `set_karaoke_display_offset_tenths`, `adjust_karaoke_display_offset_tenths`, `_history_companion_is_fully_merged`.

## V302

Shared karaoke state and playlist last-play dates with the browser while persisting floating-lyrics position independently of edit-window size.

Evidence: compared V301→V302 archived source; added `format_playlist_browser_last_played`, `_ensure_playlist_browser_history_worker`, `worker`; tests `test_v302_shared_karaoke_playlist_date_and_floating_position_contract`.

## V301

Published MatrixMixer meter levels from the final PCM output for web polling, stabilized justified floating lyrics, and repaired playlist-history handling.

Evidence: compared V300→V301 archived source; added `matrixmixer_pcm_channel_peaks`, `publish_matrix_output_levels`, `remove_matrix_output_levels`; tests `test_v301_matrix_live_levels_are_final_pcm_and_web_polled`, `test_v301_floating_lyrics_are_stable_justified_and_baseline_aligned`.

## V300

Made MatrixMixer factory reset section-scoped with a save prompt and added priority loading of a preferred emoji font across output surfaces.

Evidence: compared V299→V300 archived source; added `preferred_custom_emoji_font_path`, `_install_preferred_private_emoji_font`, `_remove_preferred_private_emoji_font`; tests `test_v300_matrix_factory_reset_is_section_scoped_and_save_prompted`, `test_v300_preferred_emoji_font_priority_and_surfaces`.

## V299

Reset incremental visualizer transport when karaoke reclaims the screen, made F5 a true transport redraw, and kept shuffle state continuous on the V266-derived trunk.

Evidence: compared V298→V299 archived source; tests `test_v299_karaoke_reclaim_resets_incremental_visualizer_transport`, `test_v299_f5_redraw_is_a_true_transport_repair_without_profiler_work`.

## V298

Added an A/B switch for prequantized Twin DRCS rendering so the visualizer path can be compared without changing the normal mode by default.

Evidence: compared V297→V298 archived source; added `_twin_drcs_tap_sequence_step`; tests `test_v298_twin_drcs_prequantize_ab_toggle_contract`.

## V297

Added a runtime Ctrl+Z undo stack and fast visualizer paths intended to preserve output while reducing generation cost; the regression check covers both.

Evidence: compared V295→V297 archived source; added `_visualizer_mode_geometry`, `observe_runtime_settings_for_undo`, `undo_last_runtime_change`; tests `test_v297_ctrl_z_operator_removal_megamix_and_zero_loss_fastpath_contract`.

## V296

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V295

Salvaged nonvisual features onto the V266-derived trunk, including playlist-history scoring, monochrome EmojiMaxx handling, and low-rate detection of edits to the active playlist. The archive gap prevents assigning every carried-forward change solely to V295.

Evidence: compared V293→V295 archived source; added `emojimax_monochrome_safe_replacement`, `emojimax_plain_with_solutions`, `playlist_history_scores`.

## V294

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V293

Restored the V266 visualizer's generation-only governor budget and related renderer settings after the intervening experimental branch.

Evidence: compared V291→V293 archived source; added `_v293_v266_visualizer_restoration_selftest`.

## V292

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V291

Applied visualizer persistence/brightness every display frame while keeping expensive palette changes slower, and wrote related semantic rows coherently to reduce tearing.

Evidence: compared V290→V291 archived source; added `_visualizer_scale_rgb_per_frame_cached`, `write_coherent_semantic_rows`; tests `test_v291_per_frame_persistence_and_tear_safe_semantic_rows`.

## V290

Placed the album-art title in its own row above popup controls and curated popup EmojiMaxx behavior; continued playlist-worker adjustments.

Evidence: compared V289→V290 archived source; tests `test_v290_emojimax_curations`, `test_v290_album_art_title_has_its_own_row_above_controls`.

## V289

Kept playlist startup from waiting for history shuffle, added popup EmojiMaxx/monochrome controls, and carried the V285 semantic visualizer repair behavior.

Evidence: compared V287→V289 archived source; tests `test_v289_playlist_startup_never_waits_for_history_shuffle`, `test_v289_popup_emoji_controls_and_monochrome_filter`.

## V288

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V287

Made playlist startup independent of history-shuffle completion and exposed popup EmojiMaxx and monochrome filters while refining semantic presentation.

Evidence: compared V286→V287 archived source; added `emojimax_monochrome_safe_replacement`, `emojimax_plain_with_solutions`, `load_external_album_art_popup_emojimax`; tests `test_v287_playlist_startup_never_waits_for_history_shuffle`, `test_v287_popup_emoji_controls_and_monochrome_filter`.

## V286

Replaced periodic replay of cached semantic rows with authoritative transition bootstraps, aligned HUD colons, and corrected selected EmojiMaxx night/plural mappings.

Evidence: compared V285→V286 archived source; tests `test_v286_semantic_transport_uses_authoritative_bootstraps_not_periodic_cached_replay`, `test_v286_night_emojimax_is_city_at_night_and_plural_suffix`.

## V285

Hardened playlist-history identity checks so a unique filename does not override conflicting Artist/Title evidence; added a semantic-row repair path.

Evidence: compared V284→V285 archived source; added `playlist_history_tag_is_usable`, `playlist_history_resolve_filename_candidates`, `native_probe`; tests `test_v285_unique_filename_never_overrides_conflicting_artist_title`, `test_v285_legacy_duration_one_is_unknown_not_identity_evidence`.

## V284

Compiled artwork lookup tables for the visualizer and made NumPy/CUDA acceleration optional, asynchronous after the first snapshot, and output-equivalent to the existing renderer.

Evidence: compared V283→V284 archived source; added `_visualizer_art_array_backend`, `compiled_art_backend_label`, `_visualizer_unpack_compiled_art_cell`; tests `test_v284_precompiled_art_lut_is_output_exact_and_geometry_lookup_only`, `test_v284_art_lut_compiler_is_async_after_first_snapshot_and_cuda_optional`.

## V283

Added source-aware multichannel handling that preserves native 5.1 and synthesizes only missing 7.1 rear channels, plus progressive history shuffle and native metadata probing. The archived build notes visualizer banding.

Evidence: compared V282→V283 archived source; added `find_progressive_history_start_candidate`, `_infer_standard_channel_layout`, `_native_audio_metadata_probe`; tests `test_v283_release_defaults_to_semantic_without_auto_diagnostic`, `test_v283_native_51_is_preserved_and_only_missing_71_rears_are_synthesized`.

## V282

Changed history shuffle from 15% groups to global ten-percent deciles, placing never-played items oldest, and reloaded file-backed playlists when their source signature changed.

Evidence: compared V281→V282 archived source; added `history_decile_shuffle_from_scores`, `playlist_source_signature`, `first_load_status`; tests `test_v282_history_shuffle_is_global_deciles_with_never_oldest`, `test_v282_build_shuffle_uses_ten_percent_buckets_not_fifteen`.

## V281

Added a compiled artwork-color mixer with an F8 toggle and lazy scaling of only accessed art cells; repaired visualizer bootstrap after leaving the playlist view.

Evidence: compared V280→V281 archived source; added `_visualizer_scale_art_rgb_cached`, `_LazyScaledArtRow`, `__init__`; tests `test_v281_compiled_art_mixer_f8_and_playlist_exit_bootstrap_contract`, `test_v281_lazy_art_grid_scales_only_accessed_cells`.

## V280

Isolated transport benchmarks from mode-change settling, removed the unwanted ‘always’ EmojiMaxx substitution, and kept web artwork navigation from moving its background.

Evidence: compared V279→V280 archived source; added `center_middle_hud_pair_in_gap`, `locate`, `resolve_artwork_pillow_emoji_font`; tests `test_v280_emojimax_always_is_hard_removed`, `test_v280_web_art_navigation_does_not_move_background`.

## V279

Made the rendering benchmark report persistent, extended collection and log migration, and interleaved artwork-style refreshes for smoother visualizer cadence. The archived build still notes banding.

Evidence: compared V278→V279 archived source; added `migrate_legacy_pafplayer_log_directory`, `pafplayer_rendering_report_log_path`, `append_pafplayer_rendering_report`; tests `test_v279_profiler_dump_long_collection_and_log_migration_contract`, `test_v279_artwork_style_refresh_is_interleaved_for_smoother_cadence`.

## V278

Served web status only when clients need it and changed visualizer deadline pacing to reduce jitter; the source adds a focused lazy-web/smooth-pacing regression check.

Evidence: compared V277→V278 archived source; added `wait_for_visualizer_deadline`, `_refresh_status_json_locked`, `flush_status_if_client_active`; tests `test_v278_lazy_web_and_smooth_pacing_contract`.

## V277

Protected the transport benchmark from shuffle work, constrained quality choices, and gave Act/Song visual feedback its own light cadence while updating color deltas.

Evidence: compared V276→V277 archived source; added `bar_color_at`, `update_cell`, `playlist_shuffle_blocks_transport_benchmark`; tests `test_v277_shuffle_safe_benchmark_and_quality_safe_mode_set`, `test_v277_act_song_throb_has_independent_lightweight_cadence`.

## V276

Added a native Windows waitable timer for 120 Hz visualizer pacing and bounded color-update frequency when frame rate drops, with quality-safe transport modes.

Evidence: compared V275→V276 archived source; added `boost_current_visualizer_thread_priority`, `revert_visualizer_thread_priority`, `create_visualizer_waitable_timer`; tests `test_v276_quality_safe_color_and_native_timer`.

## V275

Replaced the visualizer worker's imprecise event wait with a coarse sleep followed by a short deadline spin for 120 Hz pacing. Synchronized profiler totals between worker and owner threads, kept the profiler open until Escape, and refreshed benchmark progress between samples.

Evidence: compared V274→V275 archived source; added `wait_for_visualizer_deadline`, `refresh_transport_benchmark_hud_between_samples`; tests `test_v275_precise_scheduler_persistent_report_and_benchmark_progress`.

## V274

Moved visualizer rendering onto a dedicated thread, enabled finer Windows timer resolution for the worker, and made profiler collection cumulative and explicit.

Evidence: compared V273→V274 archived source; added `enable_visualizer_timer_resolution`, `_restore_timer_resolution`, `enable_visualizer_python_thread_cadence`; tests `test_v274_dedicated_visualizer_thread_and_timer_resolution`, `test_v274_profiler_collection_is_explicit`.

## V273

Bootstrapped semantic rendering at defined geometry-frame boundaries and capped profiler pages to visible rows. The archived build reports faster output but visible banding.

Evidence: compared V272→V273 archived source; tests `test_v273_color_snapshot_bootstraps_by_geometry_frames`, `test_v273_profiler_pages_are_visibility_capped`.

## V272

Added exact incremental Twin DRCS artwork rendering with a cached microtile container and split the profiler into terminal-sized pages.

Evidence: compared V271→V272 archived source; added `_incremental_artwork_twin_rows`, `background_at`, `cell_for`; tests `test_v272_artwork_incremental_twin_is_exact_and_microtile_container_is_cached`, `test_v272_profiler_is_terminal_paged`.

## V271

Moved the visualizer toward incremental 120 Hz frames, added artwork-color autoslide controls on Ctrl+B, kept Ctrl+U for URL choice, and updated F1 help accordingly.

Evidence: compared V270→V271 archived source; added `save_art_color_autoslide_enabled_states`, `next_art_color_autoslide_state`, `_visualizer_height_plan`; tests `test_v271_ctrl_b_autoslide_ctrl_u_url_chooser`, `test_v271_ctrl_u_url_ctrl_b_autoslide_and_f1_help`.

## V270

Isolated the web gateway in a separate process and attributed complete visualizer frame time in the profiler, including transport and waiting costs.

Evidence: compared V269→V270 archived source; added `_paf_shared_bytes_write`, `_paf_shared_bytes_read`, `_paf_web_gateway_process`; tests `test_v270_gateway_process_isolation_contract`, `test_v270_profiler_has_full_frame_attribution`.

## V269

Expanded transport profiling with observation and cost metrics and isolated web startup more carefully; --no-webserver avoids creating an alias server object. The archived build notes an unresolved visual feel.

Evidence: compared V268→V269 archived source; added `_pin_current_web_thread`, `setup`, `serve_web`; tests `test_v269_rich_transport_results_include_observation_and_cost_metrics`, `test_v269_no_webserver_alias_is_true_no_server_object`.

## V268

Made the transport benchmark wait for live spectrum data, run candidate modes in forward and reverse order, and show a second profiler row for benchmark results.

Evidence: compared V267→V268 archived source; added `_average_transport_samples`, `_finish_visualizer_transport_autotune`, `cycle_visualizer_transport_mode`; tests `test_v268_transport_benchmark_waits_for_spectrum_and_runs_forward_reverse`, `test_v268_profiler_has_transport_benchmark_second_row`.

## V267

Added faster parser-light row transport choices for a 60 fps visualizer target and made the physical Ctrl+Alt+F profiler hotkey reliable.

Evidence: compared V266→V267 archived source; added `V267SixtyFpsTransportRegressionTests`; tests `test_v267_ctrl_alt_f_physical_profiler_chord_is_reliable`, `test_v267_autotune_includes_parser_light_row_transports`.

## V266

Restored a transport-independent visualizer governor that budgets generation work rather than terminal write time, with real transport-mode choices. The archived release was marked a candidate after earlier speed/banding regressions.

Evidence: compared V265→V266 archived source; added `write_visualizer_console`, `reset_visualizer_transport_cache`, `set_visualizer_transport_mode`; tests `test_v266_restores_transport_independent_governor_and_real_transport_choices`.

## V265

Made the browser own its visualizer rendering and gated its updates to active clients so console rendering does not have to drive an idle web view.

Evidence: compared V264→V265 archived source; added `_stylize_karaoke_with_emojimax_uncached`, `_lyrics_are_timed`, `web_visualizer_active`; tests `test_v265_web_visualizer_is_browser_owned_and_gated`.

## V264

Cached and throttled browser status/spectrum updates on demand, reducing contention with the console visualizer while keeping direct transport POST actions immediate.

Evidence: compared V263→V264 archived source; added `_encode_json_bytes`, `_refresh_status_json_locked`, `_refresh_spectrum_json_locked`; tests `test_v264_web_is_demand_driven_cached_and_browser_animation_is_throttled`.

## V263

Split heavy karaoke and HUD updates from the higher-rate spectrum schedule, added profiler measurements, and constrained idle artwork motion to one monitor.

Evidence: compared V262→V263 archived source; added `external_album_art_idle_monitor_for_rect`, `external_album_art_idle_safe_outer_rect`, `neighboring_entry`; tests `test_v263_release_identity_split_hud_profiler_and_geometry_contract`, `test_v263_idle_art_dance_never_straddles_monitor_seam`.

## V262

Exposed semantic visualizer cells for delta-cell transport without changing full-frame output and moved geometry toward a five-second maintenance cadence.

Evidence: compared V261→V262 archived source; added `_resample_visualizer_values`; tests `test_v262_release_identity_and_five_second_geometry_contract`, `test_v262_twin_renderer_exposes_semantic_cells_without_changing_full_output`.

## V261

Restored a lower-cost visualizer hot loop after a throughput regression, with a dedicated regression check for the active render path.

Evidence: compared V260→V261 archived source; tests `test_v261_visualizer_throughput_hot_loop_contract`.

## V260

Applied the longest matching EmojiMaxx phrase first so a shorter mapping cannot consume text meant for a longer replacement.

Evidence: compared V259→V260 archived source; added `_emojimax_phrase_items`; tests `test_v260_emojimaxx_longest_substitution_wins`.

## V259

Added an F5 live-fps HUD and let Windows input polling go dormant when idle; rolled back a direct high-rate terminal write path that had regressed measured output.

Evidence: compared V258→V259 archived source; added `toggle_fps_hud`, `roll_fps_hud`, `fps_hud_ansi`; tests `test_v259_f5_live_fps_and_auto_input_dormancy_contract`.

## V258

Added a direct fast path for visualizer spectrum writes and adjusted karaoke autosizing, while ordinary HUD writes still use the normal console path.

Evidence: compared V257→V258 archived source; tests `test_v258_visualizer_fast_path_and_karaoke_autosize_contract`.

## V257

Bound Alt+F to the floating-lyrics action with a key latch that prevents repeated toggles from one press.

Evidence: compared V256→V257 archived source; tests `test_v257_alt_f_floating_lyrics_contract`.

## V256

Added shuffle/performance profiling and steadier idle-art positioning, together with saved per-output latency settings for multi-output playback.

Evidence: compared V254→V256 archived source; added `output_device_identity`, `normalize_multi_output_latency_ms`, `load_multi_output_latencies_ms`; tests `test_v256_shuffle_perf_and_idle_origin_contract`.

## V255

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V254

readable web karaoke and selectable floating lyrics.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v254_documentation.md`, `PAFPlayer_v254_readable_web_and_selectable_floating_lyrics.py`.

## V253

Added live visualizer inputs from what-you-hear and microphone capture, with an auto-pause policy and bounded mixing/silence handling.

Evidence: compared V252→V253 archived source; added `_ensure_pyaudiowpatch`, `live_pcm_spectrum_levels`, `live_visualizer_capture_mode`; tests `test_v253_release_identity_and_three_layer_coloring_model`, `test_v253_live_visualizer_input_selector_and_auto_pause_contract`.

## V252

Expanded web title and multi-output controls, artwork profiles, EmojiMaxx synchronization, and related hotkeys in one combined release.

Evidence: compared V251→V252 archived source; added `lastfm_profile_url`, `output_devices_from_mask`, `output_devices_mask`; tests `test_v252_release_identity_and_three_layer_coloring_model`, `test_v252_combined_web_title_multi_output_art_profiles_and_hotkeys`.

## V251

Added web karaoke tooltips and checkerboard layout, extended artwork-color autoslide timing, and kept autoslide control local to the console.

Evidence: compared V250→V251 archived source; added `_art_color_autoslide_triangle`, `art_color_visualizer_effective_strengths`, `emojimax_plain_with_solutions`; tests `test_v251_web_karaoke_checkerboard_tooltips_and_help_contract`, `test_v251_autoslide_contract_is_console_local_and_extended_interval`.

## V250

Kept web artwork from covering the resize gutter and added a microtile opt-out group with matching CLI control; this archived build was labeled a beta candidate.

Evidence: compared V249→V250 archived source; tests `test_v250_web_art_resize_gutter_never_overlays_artwork`, `test_v250_microtile_opt_out_group_and_cli_contract`.

## V249

Merged companion playlist-history databases forked by filename, backfilled legacy rows into the full Artist/Title identity table, and refined idle/table progress.

Evidence: compared V248→V249 archived source; added `playlist_history_companion_database_paths`, `_playlist_history_database_signature`, `merge_playlist_history_companion_databases`; tests `test_v249_history_companion_filename_fork_merges_artist_song_history`, `test_v249_active_database_legacy_rows_are_backfilled_into_full_identity_table`.

## V248

Removed an obsolete last-play regex option and made plain last-play search Unicode-casefolded and insensitive to smart-quote differences.

Evidence: compared V247→V248 archived source; added `history_search_match`, `fake_page`; tests `test_v248_obsolete_last_play_regex_option_is_removed`, `test_v248_last_played_plain_search_is_unicode_casefold_and_quote_insensitive`.

## V247

Made web progress dropdowns update the active owner state through its action queue; kept their diagnostic mode available only for tests.

Evidence: compared V246→V247 archived source; added `append_web_progress_control_diagnostic`; tests `test_v247_progress_web_dropdowns_mutate_live_owner_state`, `test_v247_progress_control_diagnostic_is_test_only_and_queue_visible`.

## V246

Corrected 7.1 MatrixMixer channel ordering so muting back speakers uses the native PCM channel positions.

Evidence: compared V245→V246 archived source; tests `test_v246_7_1_back_only_mute_uses_native_pcm_channel_order`.

## V245

Blended bar microtiles at the requested strength over the live visualizer bar color instead of replacing it with an incorrectly weighted result.

Evidence: compared V244→V245 archived source; added `_visualizer_blend_bar_art_cached`, `colored_cell`; tests `test_v245_bar_microtiles_blend_exact_requested_strength_over_live_bar_color`.

## V244

Applied web MatrixMixer edits through the native speaker-mapped renderer and made the bar-microtile switch explicit and reflected in status.

Evidence: compared V243→V244 archived source; tests `test_v244_matrix_web_apply_uses_native_speaker_mapped_renderer`, `test_v244_bar_microtile_checkbox_is_explicit_and_roundtrips_status`.

## V243

Reorganized web controls for progress, autoslide, and playlists, and made manual idle motion use the current four screen corners without reloading the track.

Evidence: compared V242→V243 archived source; tests `test_v243_web_layout_progress_autoslide_playlist_and_unique_actions`, `test_v243_manual_idle_uses_current_native_four_corners_without_track_reload`.

## V242

Applied MatrixMixer coefficient and final-mute edits live, and drove progress activity from cached visualizer levels with an adaptive demo path.

Evidence: compared V241→V242 archived source; tests `test_v242_matrix_final_mute_filter_is_valid_and_coefficients_are_live`, `test_v242_progress_uses_cached_visualizer_levels_and_adaptive_demo`.

## V241

Matched play-history identities across case, smart quotes, and duration differences; imported Artist/Title history becomes a normal playback fallback. The same source adds multimonitor and web-persistence work.

Evidence: compared V240→V241 archived source; added `_choice_marks_fallback_path`, `_load_choice_marks_fallback`, `_save_choice_marks_fallback`; tests `test_v241_history_identity_folds_case_smart_quotes_and_duration`, `test_v241_imported_artist_song_history_is_normal_playback_fallback`.

## V240

Saved popup geometry from the native window origin and a signal-safe snapshot so placement survives exit and restart.

Evidence: compared V239→V240 archived source; added `windows_tk_geometry_from_hwnd`; tests `test_v240_popup_geometry_uses_native_origin_and_signal_safe_snapshot`.

## V239

Made last-play search cover complete Artist/Title history, rescaled artwork across all visible rows when the visualizer is truncated, and refined autoslide, geometry, and web transport.

Evidence: compared V238→V239 archived source; added `_ensure_playlist_full_identity_table`, `playlist_history_mark_artist_title_played`, `playlist_history_backfill_full_identities_from_csv`; tests `test_v239_last_played_searches_complete_artist_and_title_history`, `test_v239_truncated_visualizer_rescales_art_to_all_visible_rows`.

## V238

Added a MatrixMixer factory layout with side-surround channels and future Atmos slots, plus web matrix playback and experimental controls.

Evidence: compared V237→V238 archived source; added `_normalize_mm_mutes`, `active_matrixmixer_mutes`, `save_active_matrixmixer_matrices`; tests `test_v238_matrix_factory_uses_side_surrounds_sub_unity_and_future_atmos`, `test_v238_web_matrix_playback_and_experimental_control_contract`.

## V237

Added resizable web splitters, output-depth/background controls, and semantic style mapping for browser karaoke.

Evidence: compared V236→V237 archived source; added `stylize_web_karaoke_text`, `trans`, `spaced`; tests `test_v237_web_splitters_output_depth_and_background_contract`, `test_v237_web_karaoke_semantic_style_mapping`.

## V236

Resized the web layout to reserve a larger lyric area, added a dedicated Web Karaoke section with its own enable switch and controls, and placed autoslide and lyric actions alongside it.

Evidence: compared V235→V236 archived source.

## V235

Added MatrixMixer subwoofer crossover profiles and guarded registry writes, with web layout and geometry changes. The archived build is marked buggy, so these are implementation changes rather than verified working behavior.

Evidence: compared V234→V235 archived source; added `_safe_winreg_set_value`, `_normalize_mm_crossover`, `_factory_matrix_profile_payload`; tests `test_v235_matrix_profiles_have_default_and_crossovers`, `test_v235_output_expansion_respects_sub_crossover`.

## V234

Added opt-in progress beats and DRCS microtile artwork using spare soft-font slots, exposed through web controls. The archived build is marked buggy.

Evidence: compared V233→V234 archived source; added `art_microtile_drcs_char`, `define_art_microtile_drcs_patterns`, `_art_microtile_quantize_cached`; tests `test_v234_progress_beat_and_drcs_microtiles_are_opt_in_web_controls`, `test_v234_drcs_microtiles_use_spare_soft_font_slots`.

## V233

Added a web editor for MatrixMixer, history, and audio settings; it normalizes matrix coefficients and preserves front-channel identity.

Evidence: compared V231→V233 archived source; added `_matrix_factory`, `_normalize_upmix_matrix`, `_matrix_to_jsonable`; tests `test_v233_web_configuration_matrix_marks_and_compact_layout_contract`, `test_v233_matrix_editor_normalizes_coefficients_and_keeps_front_identity`.

## V232

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V231

Cached scaled artwork for each track and geometry instead of recomputing static color transforms inside the visualizer's per-cell path.

Evidence: compared V230→V231 archived source; added `_visualizer_scaled_art_grid`.

## V230

Buffered short MMInspo pipe reads until a complete audio block is available and added master switches for console karaoke and progress sections in the web UI.

Evidence: compared V229→V230 archived source; added `matrixmixer_read_pcm_block`, `_configure_kernel32`, `_configure_avrt`; tests `test_v230_mminspo_accumulates_short_pipe_reads_into_real_audio_blocks`, `test_v230_web_console_karaoke_and_progress_have_master_switches`.

## V229

Kept the two artwork samples in Twin DRCS blackness cells, capped browser artwork work, and ordered transport before visualizer controls in the compact web layout.

Evidence: compared V228→V229 archived source; tests `test_v229_web_art_is_capped_and_transport_precedes_visualizer`, `test_v229_twin_drcs_blackness_keeps_two_art_samples`.

## V228

Added experimental MMInspo audio rendering with WAVEFORMATEXTENSIBLE channel masks and a PCM command, plus matching web and visualizer controls.

Evidence: compared V226→V228 archived source; added `_MMGUID`, `_MMWaveFormatEx`, `_MMWaveFormatExtensible`; tests `test_v228_mminspo_waveformatextensible_masks_and_pcm_command`, `test_v228_web_mminspo_and_visualizer_control_contract`.

## V227

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V226

Constrained the web document title to the Act/Title heading with cover credit rather than letting it expand into a long multi-line heading.

Evidence: compared V225→V226 archived source; tests `test_v226_web_document_title_is_single_line_act_title_with_cover_credit`.

## V225

Added HDMI PCM routing and stereo-copy pan filters for multichannel output, along with web karaoke controls. The archived test also checks the Act/Title document heading.

Evidence: compared V224→V225 archived source; added `_stereo_copy_pan_filter`, `paf_web_choice_value_is_valid`, `paf_web_choice_default_value`; tests `test_v225_web_document_title_is_single_line_act_title_with_cover_credit`.

## V224

Made direct web controls resilient to status polling by tracking a pending user change for up to 2.5 seconds. Poll updates no longer immediately snap a newly changed control back to its old value.

Evidence: compared V223→V224 archived source.

## V223

Tried a shared artwork/karaoke compositor that can apply separate background strengths to karaoke rows and visualizer rows. The archived experiment is marked broken; the source diff establishes the implementation attempt, not a working release.

Evidence: compared V222→V223 archived source.

## V222

Switched fitted cover art from bilinear resize to Lanczos and cached an edge-aware unsharp-mask pass for the console artwork grid.

Evidence: compared V221→V222 archived source.

## V221

Reduced the browser analyzer to 48 bins and made karaoke-owned artwork rows use delta-row updates. Also preserved natural art-strip alignment when the strip already fills the width.

Evidence: compared V220→V221 archived source.

## V220

Cached ANSI foreground/background sequences for tall Twin DRCS visualizer rows to reduce repeated terminal-string construction.

Evidence: compared V219→V220 archived source; added `_visualizer_ansi_fg_bg_cached`.

## V219

Built a multi-artwork strip from each cover's fitted natural width, then tiled the strip only when it was narrower than the console area.

Evidence: compared V218→V219 archived source.

## V218

Added a tall visualizer layout and an alternate HUD action on Ctrl+Alt+H. The renderer also uses row-independent colors when available.

Evidence: compared V217→V218 archived source.

## V217

Expanded the console artwork colormap from one cover to as many as four embedded artwork variants, fitting each panel to the terminal cell aspect ratio.

Evidence: compared V216→V217 archived source.

## V216

Saved visualizer row count, top-row truncation, artwork coloring, and karaoke-expansion choices as player settings. Karaoke expansion now defaults off.

Evidence: compared V215→V216 archived source.

## V215

Changed the web grid so the karaoke lyric area can occupy the full content width rather than sharing the narrower left column.

Evidence: compared V214→V215 archived source.

## V214

Widened the web controls layout and split Console Visualizer and Console Karaoke into visible groups. Renamed artwork saturation controls and added a cover-art visualizer demo action.

Evidence: compared V213→V214 archived source.

## V213

Fitted cover art using the actual terminal cell aspect ratio and reserved karaoke background rows in the artwork-colored visualizer when those modes are active.

Evidence: compared V212→V213 archived source.

## V212

Added a live karaoke display offset that shifts lyric lookup without altering audio or lyric files. The web transport exposes K−/K+ buttons and shows the active offset.

Evidence: compared V211→V212 archived source.

## V211

Made console cover art fit vertically and tile across the available width. Replaced the demo dropdown with a reversible Cover Demo button that restores the prior artwork-color settings.

Evidence: compared V210→V211 archived source.

## V210

Repaired the web control builder's JavaScript selection logic by replacing a nested conditional with explicit control-group branches.

Evidence: compared V209→V210 archived source.

## V209

Split experimental artwork coloring into independent checkboxes for blackness, bars, karaoke sides, and karaoke text, with matching web-control state and aspect-aware tiling.

Evidence: compared V208→V209 archived source.

## V208

Sampled artwork background color for console cover compositing so the image can bleed into unused visualizer cells.

Evidence: compared V207→V208 archived source; added `artwork_background`.

## V207

Grouped web configuration controls into Playback, Visualizer, Karaoke, and Progress sections with distinct colors and separate hosts for each control type.

Evidence: compared V206→V207 archived source.

## V206

Expanded and regrouped command-line help into playback history, karaoke, and progress sections, with more room for explanations and defaults.

Evidence: compared V205→V206 archived source.

## V205

Added experimental web controls for artwork color source, strength, and cover demos, and split the configuration page into Visualizer and Karaoke groups.

Evidence: compared V204→V205 archived source.

## V204

Added a configurable web-interface URL link and default-choice handling for artwork and web controls.

Evidence: compared V203→V204 archived source; added `set_web_interface_url`.

## V203

Added an experimental album-art color grid that maps cover colors onto visualizer geometry.

Evidence: compared V202→V203 archived source; added `album_art_visualizer_color_grid`.

## V202

Changed the artwork lyrics-mode control to switch between artwork-enabled and floating-lyrics modes, save the selected mode, and expose a command to reveal the floating lyrics window.

Evidence: compared V201→V202 archived source.

## V201

- Split web visualizer selection into pattern and treatment controls.
- Grouped SIXEL, DRCS, album-art visualizer, karaoke expansion, and related experimental toggles under “Experimental / broken”.
- Kept status chips on one line with horizontal scrolling and reclaimed two unused terminal rows for visualizer height.

## V200

- Added centered/tiled cover-art visualizer treatments: cover on black, dim cover beneath bars, and cover masked to bars, selectable with `--album-art-style`.
- Added `--last-played REGEX`, a paginated rainbow audit query over stored track history.

## V199

The V198→V199 source diff changes release identity only. The archived label mentions history and idle fixes, but this source does not show those changes; they may have been in an unarchived intermediate build.

Evidence: compared V198→V199 archived source.

## V198 — history regex query and idle lyric stability

- Added `--last-play-regex REGEX`, a playback-free SQLite query over normalized filename and Artist/Song identity. It reports the newest matching play, or `NEVER` when there is no match; invalid expressions return exit code 2.
- Idle artwork crossfades now replace only the tagged base image and lower it beneath the existing lyric layer. Over-art color animation pauses during idle-gallery rotation, eliminating repeated lyric blink while many images are displayed.

## V197 — stable floating layout and shared-cost rendering optimization

- Floating edit-mode geometry is captured on focus exit, covering native Windows resizing that never reaches the canvas mouse-release binding. The rectangle center remains the compact lyric anchor, and its separately persisted size now governs font scale and line wrapping.
- The coloring destination tabs swap order and use explicit identities: **🎨 Artwork Lyric Coloring** and **☁ Floating Lyric Coloring**.
- The retained SIXEL artwork experiment no longer extracts cover data on every restore. Its encoded 64-color layer is cached by track and terminal geometry, and restore cadence adapts from 2 FPS down to 1 FPS for fullscreen-like areas while the ordinary console visualizer keeps its independent adaptive cadence.
- Animated lyric rendering applies tone controls before enlarging the small pattern tile, uses bilinear expansion, caches glyph runs and 360° shadow masks, and scales animation cadence with mask area. This removes duplicated full-frame work when artwork and floating lyrics are both large.

## V196 — experimental retained-artwork layering

- `Ctrl+Alt+F6` now toggles a separate console-layering experiment. It caches the current cover as static SIXEL, restores it at 2 FPS, and immediately renders the normal DRCS/Unicode spectrum above it.
- This does not reuse the existing single-bitmap album-art spectrum composite. Its purpose is to exercise Windows Terminal's actual image/text layer ordering and compensate for text-cell image erasure by redrawing the retained source cover.
- V196 preserves the V192 floating-lyric placement and artwork-window geometry repairs. The canonical source and build identifiers are now V196.

## V195

An archived file is labeled V195, but its embedded program version is V192. The V195 release contents cannot be established from this snapshot alone.

Evidence: `PAFPlayer_v195_mislabeled_as_192.py` in `C:\BAT\PAFPlayer\releases`.

## V194

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V193

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V192 refinement — compact floating lyric placement and low-rate console continuity

- Floating lyrics now measure on a temporary layout surface but immediately shrink their real transparent window to the exact rendered lyric-and-shadow bounds; idle is a one-pixel transparent window. Saved placement is an exact, unclamped screen X/Y so edge placement is possible, and the floating right-click menu can set that coordinate directly.
- Entering edit chrome rebases the drag anchor after Tk/Windows changes the client origin. The lyric color animation holds while dragging, preventing the renderer from fighting the pointer.
- Opening the lyric-color configurator no longer blanks the console or browser spectrum. Those visualizers retain a two-FPS heartbeat while the configurator is active.
- The experimental, saved-off-by-default frequency warp remains display-only: it leaves the first 55% of display frequencies untouched and monotonically compresses source 70–100% into approximately the last 15% of display width. `Ctrl+Alt+F9` toggles it.

## V191

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V190

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V189

An archived file is labeled V189, but its embedded program version is V120. The V189 release contents cannot be established from this snapshot alone.

Evidence: `PAFPlayer_v189-mislabeled-as-v120_v112player_v124auditor_corrected.py` in `C:\BAT\PAFPlayer\releases`.

## V188

Gave coloring-style controls more table width and made row previews use a consistent height-driven text size.

Evidence: compared V187→V188 archived source; tests `test_v188_coloring_table_gives_extra_width_to_style_controls`, `test_v188_row_samples_use_large_consistent_height_driven_text`.

## V187

Separated each coloring mode's live sample from its controls and kept solid palettes spatially uniform while allowing them to animate over time.

Evidence: compared V186→V187 archived source; added `pillow_measure`; tests `test_v187_solid_palette_is_spatially_solid_but_time_animated`, `test_v187_release_identity`.

## V186

Moved the coloring-configurator header outside the scroller, fixed palette selection behavior, and added a working preview selector.

Evidence: compared V185→V186 archived source; added `pillow_measure`, `choose`, `select_color_config_preview`; tests `test_v186_release_identity`, `test_v186_coloring_header_is_sticky_outside_scroller`.

## V185

Rebuilt the coloring configurator as one aligned five-column table with compact centered row samples and hover tooltips.

Evidence: compared V184→V185 archived source; added `install_tooltip`, `hide_tooltip`, `show_tooltip`; tests `test_v185_coloring_configurator_is_one_shared_five_column_table`, `test_v185_row_samples_are_single_line_centered_and_compact`.

## V184

Made coloring rows compact while giving the sample column flexible width; visible row samples continue animating during scrolling.

Evidence: compared V183→V184 archived source; tests `test_v184_release_identity`, `test_v184_coloring_rows_give_sample_all_flexible_width`.

## V183

Distributed free HUD space more evenly without disturbing established colon anchors; the source also includes artwork topmost state and controls carried across the archive gap.

Evidence: compared V180→V183 archived source; added `spread`, `load_external_album_art_topmost`, `save_external_album_art_topmost`; tests `test_v183_release_identity`, `test_v183_grlwood_dense_row_equalizes_every_free_visible_gap`.

## V182

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V181

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V180

🎧 PAFPlayer / play_audio_file.py.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v180_manual.md`, `PAFPlayer_v180_dual_lyric_modes_and_shared_color_controls.py`.

## V179

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V178

Clipped coloring previews to their rows and adapted row-preview scheduling under load without slowing the large hero preview; simplified the artwork border.

Evidence: compared V177→V178 archived source; added `adapt_karaoke_color_config_row_interval`, `pillow_measure`, `color_config_window_is_viewable`; tests `test_v178_release_identity`, `test_v178_row_preview_scheduler_adapts_without_changing_hero_speed`.

## V177

Added twelve karaoke lettering modes for fifteen total and allowed independent, persisted palettes per mode.

Evidence: compared V176→V177 archived source; added `normalize_external_album_art_karaoke_color_palettes`, `load_external_album_art_karaoke_color_palettes`, `save_external_album_art_karaoke_color_palettes`; tests `test_v177_release_identity`, `test_v177_twelve_more_lettering_modes_and_independent_palettes`.

## V176

Made the coloring configurator responsive with a large live hero preview, TV-show style controls, and a maximized layout that uses available space.

Evidence: compared V174→V176 archived source; added `hard_stop_process`, `render_karaoke_color_config_preview`, `truncate_for_measure`; tests `test_v176_coloring_configurator_has_large_live_hero_and_tv_show_controls`, `test_v176_maximized_configurator_expands_stage_and_rows_instead_of_gray_dead_space`.

## V175

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V174

Debounced native album-art border changes to avoid reentrant UI work and persisted the last clean play/pause state, defaulting to playing when absent.

Evidence: compared V173→V174 archived source; added `schedule_native_windows_border_suppression`, `apply_once`; tests `test_v174_release_identity`, `test_v174_album_art_native_border_is_debounced_and_not_reentrant`.

## V173

Changed configurator animation to incremental, cancelable work and restored console focus after Tk artwork startup could steal it.

Evidence: compared V172→V173 archived source; added `next_karaoke_color_config_preview_index`, `catalog_picker_q_sequence_step`, `windows_foreground_window_handle`; tests `test_v173_release_identity`, `test_v173_configurator_animation_is_incremental_and_close_cancels_it`.

## V172

Added a scrollable, persistent karaoke color configurator, 20 Hz web spectrum endpoint, real web pause toggle, and artwork-window chrome controls.

Evidence: compared V171→V172 archived source; added `compact_external_album_art_geometry_to_fitted_image`, `spectrum_snapshot`, `publish_spectrum`; tests `test_v172_release_identity`, `test_v172_karaoke_color_configurator_is_scrollable_live_and_persistent`.

## V171

Persisted multiple favorite karaoke-color modes and one startup default, with controls to mark and select them.

Evidence: compared V170→V171 archived source; added `normalize_external_album_art_karaoke_color_favorites`, `external_album_art_karaoke_color_is_favorite`, `load_external_album_art_karaoke_color_favorites`; tests `test_v171_release_identity`, `test_v171_karaoke_color_favorite_mask_supports_multiple_modes`.

## V170

Added artwork-window focus transparency and zoom controls, plus spatially varied, time-changing plasma karaoke coloring.

Evidence: compared V169→V170 archived source; added `load_external_album_art_lyric_font_scale`, `save_external_album_art_lyric_font_scale`, `load_external_album_art_karaoke_color_mode`; tests `test_v170_release_identity`, `test_v170_art_window_focus_transparency_zoom_and_plasma_contract`.

## V169

Added a smart HUD placement optimizer and toggle that aligns semantic colon pairs when row space permits.

Evidence: compared V168→V169 archived source; added `optimize_hud_field_positions`, `natural_start`, `place`; tests `test_v169_release_identity`, `test_v169_smart_hud_alignment_toggle_and_source_default_contract`.

## V168

Aligned inline Last play with nearby metadata colons using available row width and exposed a toggle for the layout.

Evidence: compared V167→V168 archived source; added `hud_metadata_label_colons`, `aligned_inline_last_play_gap`, `refresh_inline_last_play_alignment`; tests `test_v168_release_identity`, `test_v168_supplied_hud_screenshots_align_inline_last_play_when_spare_width_exists`.

## V167

Recovered Unicode source text from inherited mojibake while retaining single-cell progress-bar glyphs.

Evidence: compared V166→V167 archived source; tests `test_v167_release_identity`, `test_v167_progress_bar_glyphs_are_single_terminal_cells`.

## V166

Replaced progress-bar characters with terminal-safe single-cell glyphs so the bar width remains stable.

Evidence: compared V165→V166 archived source; tests `test_v166_release_identity`, `test_v166_progress_bar_glyphs_are_single_terminal_cells`.

## V165

The V165 source contains a viewport-based HUD anchor that follows terminal resizing, plus floating-lyrics geometry handling. The nearest earlier full snapshot is V119, so the archive cannot isolate which intervening version introduced each part; the archived build is also marked as having title-bar trouble.

Evidence: compared V119→V165 archived source; added `options`, `update_lyric`, `schedule_floating_geometry_save`; tests `test_v165_release_identity`, `test_v165_hud_anchor_tracks_resize_without_scrollback_drift`.

## V164

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V163

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V162

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V161

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V160

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V159

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V158

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V157

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V156

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V155

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V154

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V153

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V152

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V151

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V150

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V149

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V148

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V147

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V146

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V145

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V144

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V143

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V142

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V141

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V140

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V139

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V138

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V137

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V136

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V135

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V134

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V133

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V132

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V131

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V130

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V129

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V128

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V127

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V126

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V125

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V124

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V123

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V122

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V121

No version-specific release artifact or reliable change description was found in the inspected archives. This number may have been unused; no behavior is attributed to it.

## V120

A source snapshot filed under V189 declares `PROGRAM_VERSION = "V120"` internally. Its filename says it was mislabeled, so this is evidence of a V120 code state, not proof of a published V120 release.

Evidence: `PAFPlayer_v189-mislabeled-as-v120_v112player_v124auditor_corrected.py` in `C:\BAT\PAFPlayer\releases`.

## V119

Let the private-screen visualizer adapt frame rate from generation cost without throttling itself on terminal transport time.

Evidence: compared V118→V119 archived source; added `adapt_visualizer_fps`; tests `test_v119_release_identity`, `test_v119_private_screen_visualizer_does_not_self_throttle_on_transport`.

## V118

Moved the player renderer into an alternate terminal screen with fixed coordinates and made floating-lyrics opacity/geometry updates nonblinking.

Evidence: compared V117→V118 archived source; added `enter_player_screen`, `leave_player_screen`; tests `test_v118_alternate_screen_renderer_owns_fixed_coordinates`, `test_v118_floating_geometry_focus_and_nonblinking_opacity_contract`.

## V117

Restored the complete V113 terminal transaction after V114–V116 experiments while keeping persistent floating-lyrics geometry and shared audio bootstrap.

Evidence: compared V116→V117 archived source; added `_claire_helper_raw_url`, `move_to`; tests `test_v117_restores_complete_v113_terminal_transaction`, `test_v117_floating_geometry_and_focus_border_contract`.

## V116

Anchored redraws to the bottom of the visible viewport so reflow does not scroll or delete terminal lines; persisted floating-lyrics geometry and focus border state.

Evidence: compared V115→V116 archived source; added `restore_external_floating_lyrics_geometry`, `remember_floating_geometry_now`, `apply_floating_geometry`; tests `test_v116_bottom_anchored_reflow_never_scrolls_or_deletes_lines`, `test_v116_floating_geometry_and_focus_border_contract`.

## V115

Added a fixed viewport and sectioned adaptive HUD, including the full web-visible processing name, with reflow constrained to owned terminal rows.

Evidence: compared V114→V115 archived source; added `hud_console_processing_name_ansi`, `format_hud_controls_grammar`, `clamp_ui_origin_to_viewport`; tests `test_v115_sectioned_adaptive_hud_and_web_full_name_contract`, `test_v115_reflow_never_scrolls_or_deletes_physical_terminal_lines`.

## V114

Consolidated ReplayGain baking in shared audio processing, hardened Last-play and Last.fm reliability, improved HUD and artwork/lyric windows, completed playlist selection, and added a MiniLyrics-inspired local web view.

Evidence (`C:\BAT\PAFPlayer\releases`): `PAFPlayer_v114_release_notes.md`, `PAFPlayer_v114_shared_replaygain_reliability_art_and_web.py`.

## V113

Separated lyric windows, added an interactive playlist queue browser and tag view, and refined inline Last play/Album/Comment HUD placement.

Evidence: compared V112→V113 archived source; added `playlist_queue_search_matches`, `interactive_playlist_queue_picker`, `gui`; tests `test_v113_release_identity_and_new_key_contract`, `test_v113_inline_last_play_layout_aligns_album_and_separates_comment`.

## V112

Made artwork geometry permanently user-owned, reversed the resize modifier so ordinary resizing is free-form and Ctrl forces 1:1, contained new art in the existing rectangle with black letterboxing, merged singular/plural instrumental display tags, placed Tags directly under Last play in Help, and added a persisted three-row detail HUD on Ctrl+Alt+/.

Preserved executable/regression contracts:

Implementation and rationale details:

- Foreground and track-refresh paths no longer reapply stale geometry to a visible artwork window. Idle initialization synchronously captures the current valid geometry before any transient drift, so idle teardown returns to the user's live location.
- Source-image dimensions are diagnostic only. Neither first decode nor later artwork rotation changes the popup rectangle. Both static render and crossfade frames use contain semantics against a black canvas, preserving the complete image and creating letterbox/pillarbox bars as needed.
- Tk's native aspect constraint is inactive during ordinary resizing. While Ctrl is physically down it is set to exactly 1:1, with an explicit square-snap fallback for builds that ignore the native constraint.
- `merge_attribute_display_tags` changes only presentation: exact case-insensitive `instrumental` and `instrumentals` entries collapse at their earliest list position to synthesized `instrumental(s)`. Renderers multiply that entry's color factor by 1.25 and cap RGB channels normally.
- The Help masthead is repeated on each compact page in the order Last play, Tags, divider, ReplayGain/playlist. The three optional main-HUD rows use the same async attribute snapshot and share row reflow with controls, lyrics, and visualizers.
- `HudDetails` is persisted with ordinary player settings. Enabling it moves the controls/status origin down by exactly three rows; disabling it clears the union of the old/new region and returns those rows to the visualizer.
- The supplied phrase “The lyrics over artwork” contained no requested change, so V112 preserves the existing off/over-art/floating lyric modes rather than guessing at a new contract.

- Effective instrumental tag merge.
- HUD details hotkey and persistence contract.
- User-owned art geometry contract.
- Artwork letterboxes without cropping contract.
- Release identity.

## V111

Queued INS selections to play next, added global Ctrl+Alt+Up/Down volume, reset speed at session/playlist/insert boundaries, froze per-visit Last play, removed duplicate Dir reflow, restored illustrated docs, and made truncation close delimiters.

Preserved executable/regression contracts:

Implementation and rationale details:

- INS and Shift+INS now converge on a manual-next queue. Shift+INS accepts Windows multi-selection; shuffle randomizes the inserted batch/queue order but cannot allow an ordinary shuffle candidate to jump ahead of it.
- A successful insert resets both the live and shared speed indices to 1×. Non-paused playback restarts FFplay at the current source position when that reset changes speed; paused playback resumes at 1×. Process startup and Ctrl+O playlist relaunch also initialize at 1× rather than restoring the prior speed.
- Ctrl+Alt+Up/Down are polled before the focused-console input gate and use a physical-key latch plus buffered-scan suppression, making them genuinely global without double-applying a normal Up/Down step in Windows Terminal.
- The one-third history threshold still writes SQLite, but no longer rebuilds Last play or reflows the current HUD. This preserves the track-start snapshot and removes the stale second `Dir:` row seen after the threshold repaint.
- Plain and ANSI-aware cell truncation track unmatched delimiters. When clipping would leave an opener, the matching closer replaces the final visible cell without exceeding the requested terminal width.
- Documentation history moved to this file. The operational manual contains current behavior only and ends with its 111 one-line summaries; 28 recovered image assets restore real playback, visualizer, karaoke, palette, persistence, history, and geometry coverage.

- Truncation closes open delimiters as last character.
- Last play is a track start snapshot without dir reflow.
- Insert is multiselect play next and resets speed.
- Speed starts at one and playlist relaunch inherits that rule.
- Ctrl alt arrows are global volume hotkeys.
- Release identity.

## V110

Split diagnostics into rotating errors/trace logs and fixed Tk lyric font ownership (`root=` instead of invalid `master=`).

Preserved executable/regression contracts:

## V109

Made Last play lookup pending-aware, wrote local history at 33%, coupled learned to history, and made Alt+3 live across tracks.

Preserved executable/regression contracts:

## V108

Added an immediate recent-visit shuffle ledger, removed stale cache history, and made Alt+3 human-oriented and one-row-per-tag.

Preserved executable/regression contracts:

## V107

Preindexed/cached INS search, kept visualizers live during prompts, made prompts blink, and cleaned Tk shutdown.

Preserved executable/regression contracts:

## V106

Separated artwork decode/lyric errors, added warning-ledger logging, dense metadata tails, foreground art toggle, and media-key modifiers.

Preserved executable/regression contracts:

## V105

Replaced the fragile saved-cursor HUD anchor with absolute viewport rows and isolated lyric layers from cover rendering.

Preserved executable/regression contracts:

## V104

Isolated GUI lyric color animation from full artwork repainting and made empty floating state visibly diagnosable.

Preserved executable/regression contracts:

## V103

Made F5 art-safe, added independent floating-lyrics control, compact Last play packing, header track text, and aspect-fill art updates.

Preserved executable/regression contracts:

## V102

Added conventional artwork controls, native-size-until-resized behavior, and pointer-safe floating-lyric hit testing.

Preserved executable/regression contracts:

## V101

Made art position/DPI ownership persistent, introduced the three-way lyric mode, and separated the web Choices scroller.

## V100

Made `=` reset volume to 100% and playback speed to 1× together.

Preserved executable/regression contracts:

## V99

Intentionally skipped; no V99 release was issued.

## V98

Intentionally skipped; no V98 release was issued.

## V97

Fixed WAV sample-rate timing, enforced MISC exact-stem art, added explicit cover downloads/global base attributes, and refined HUD/history/art behavior.

Preserved executable/regression contracts:

## V96

Unified native/web related artwork and mouse behavior, clickable metadata URLs, taskbar acknowledgement, and colon-safe HUD alignment.

Preserved executable/regression contracts:

## V95

Expanded the web controller with real transport/settings, clickable progress, live analyzer data, large rainbow lyrics, and exact Never display.

Preserved executable/regression contracts:

## V94

Fixed an immediate web-enabled playback crash caused by publishing before the loop timestamp existed.

Preserved executable/regression contracts:

## V93

Added Ctrl+O clean playlist relaunch, VLC art fallback, compact Last play, denser metadata, and faster Artist/Song throbs.

Preserved executable/regression contracts:

## V92

Eliminated duplicate metadata rows, unified layout timing, cleared repaint rows, refined learned timing, and corrected EmojiMaxx low.

Preserved executable/regression contracts:

## V91

Added near-EOF resume safety, multidisc learned selectors, bounded three-hour shuffle avoidance, and branch-audit sentinels.

Preserved executable/regression contracts:

## V90

Made Dir conditional on Play-line fit and restored the localhost web server and clean editor activation.

Preserved executable/regression contracts:

## V89

Hardened next-track distinctness, strict metadata grids, learned-input commit rules, and dense three-field rows.

Preserved executable/regression contracts:

## V88

Added the raw-tag browser, collection aliases, inherited attrib editing, dense Dir/HUD semantics, and 30-second typed-tag idle behavior.

Preserved executable/regression contracts:

## V87

Deduplicated physical path aliases, added the idle artwork gallery/weighted crossfades, and removed filesystem work from playlist browsing.

Preserved executable/regression contracts:

## V86

Added fast playlist INS/DEL/browser editing, idle art, hard redraw/reflow cleanup, catalog search, and extensive HUD/help polish.

Preserved executable/regression contracts:

## V85

Improved editor focus handoff, inherited-learned detection, duplicate avoidance, and automatic attrib editor opening.

Preserved executable/regression contracts:

## V84

Made nearly all modifier-heavy controls focus-only while retaining only deliberately global physical controls.

Preserved executable/regression contracts:

## V83

Added learned extra-tag/removal workflows, robust playlist mutation, art foreground/border behavior, URL errors, and stable Dir rows.

Preserved executable/regression contracts:

## V82

Added full playback-time ReplayGain, unified URL controls, Help on F1, and an exact defaults manager.

Preserved executable/regression contracts:

## V81

Restored persistence bindings and built a numbered URL chooser with All/None/Escape handling.

Preserved executable/regression contracts:

## V80

Finalized physically exact two-line learned records and clean selector character classes.

Preserved executable/regression contracts:

## V79

No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.

Evidence note: no version-specific artifact or embedded regression name was recovered for this number; later cumulative sources remain the only authority.

## V78

Preserved history order through rebuilds, promoted the current track safely, and prevented removed tracks from reappearing.

Preserved executable/regression contracts:

## V77

Added separate progress reporting for history resolution and playlist-analysis generation.

Preserved executable/regression contracts:

## V76

Added the full-path playlist-analysis table, paging, ANSI-free export, and editor handoff.

Preserved executable/regression contracts:

## V75

Added colorful, sorted playlist-history reporting and its usage-level diagnostic.

Preserved executable/regression contracts:

## V74

Made the Tk artwork thread own shutdown and close cleanly even when the GUI never fully started.

Preserved executable/regression contracts:

## V73

Added aspect-aware art resizing, mouse controls, stable origin, playlist counts, and terminal glyph-spacing fixes.

Preserved executable/regression contracts:

## V72

Introduced the persistent external album-art window, monitor-safe geometry, and Alt+A control contract.

Preserved executable/regression contracts:

## V71

Aligned Last play under Album even when optional Comment consumes a competing row.

Preserved executable/regression contracts:

## V70

Made lyric-corpus tooling preserve written output through editor failures and avoid dumping generated code to stdout.

Preserved executable/regression contracts:

## V69

Made learned selectors durable across one/two-digit track prefixes and standardized record separators.

Preserved executable/regression contracts:

## V68

Greatly expanded usage examples and moved keystroke guidance next to playback options.

Preserved executable/regression contracts:

## V67

Added compound timed-lyric selection/parsing, asynchronous history startup, and corrected the Up-arrow vocabulary.

Preserved executable/regression contracts:

## V66

Implemented four karaoke/visualizer compositing modes and corrected expansion/genre behavior.

Preserved executable/regression contracts:

## V65

Made narrow HUD layouts relax alignment before wasting additional terminal rows.

Preserved executable/regression contracts:

## V64

Aligned semantic metadata columns by label rather than arbitrary string position.

Preserved executable/regression contracts:

## V63

Captured resume successors before queue rotation and rejected physical aliases during resumed forward navigation.

Preserved executable/regression contracts:

## V62

The archived file is labeled “resume next successor fix”, but declares V61 internally. Changes attributable specifically to V62 remain unverified.

Evidence: `PAFPlayer_v62_resume_next_successor_fix.py` in `C:\BAT\PAFPlayer\releases`.

## V61

Made visualizer modes genuinely distinct and preserved exact legacy per-column geometry.

Preserved executable/regression contracts:

## V60

Preferred the canonical C:\bat history database and added karaoke/visualizer compositing plus EmojiMaxx and learned-record refinements.

Preserved executable/regression contracts:

## V59

Separated Last.fm Now Playing from earned scrobbling and serialized the per-visit network lifecycle.

Preserved executable/regression contracts:

## V58

No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.

Evidence note: no version-specific artifact or embedded regression name was recovered for this number; later cumulative sources remain the only authority.

## V57

Added embedded-cover extraction/materialization when no usable sidecar cover exists.

## V56

Limited ordinary Last.fm submission to one scrobble per logical visit with explicit duplicate confirmation.

Preserved executable/regression contracts:

## V55

Made learned writes contain only the explicit learned rule and report the exact written result.

Preserved executable/regression contracts:

## V54

Established learned/scrobble hotkeys, standard attrib.lst creation, EmojiMaxx aliases, and clean Done/scrollback behavior.

Preserved executable/regression contracts:

## V53

Prevented forward history repeats and made missing attrib.lst creation safe and non-destructive.

Preserved executable/regression contracts:

## V52

Standardized analyzer launch/logging state and prevented shuffle from selecting the current physical track.

Preserved executable/regression contracts:

## V51

Tested safer FFmpeg launch approaches through theories 46–49, including direct executable resolution and a suspended-process probe without hidden/detached launch flags.

Evidence: compared V50→V51 archived source; added `direct_ffmpeg_executable`, `launch_suspended_ffmpeg_probe`.

## V50

Added FFmpeg child-process detachment diagnostics in theories 41–45, including a suspended-launch probe for comparing Windows startup behavior.

Evidence: compared V49→V50 archived source; added `launch_suspended_ffmpeg_probe`.

## V49

Added analyzer diagnostic theories 36–40 to separate spectrum capture cost from visualizer rendering: disable or delay capture, use dummy levels, discard publication, or render synthetic levels without the analyzer.

Evidence: compared V48→V49 archived source.

## V48

Extended theory-mode range and architecture diagnostics for visualizer/process investigation.

Preserved executable/regression contracts:

## V47

Added window-output and visualizer-frequency diagnostics for theories 25–31, including a measured visualizer origin.

Evidence: compared V46→V47 archived source; added `visualizer_origin`; tests `test_v47_theory_range_and_frequency_diagnostics`.

## V46

Expanded theory diagnostics, ordered help output, and trimmed unused bottom terminal reservation.

Preserved executable/regression contracts:

## V45

No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.

Evidence note: no version-specific artifact or embedded regression name was recovered for this number; later cumulative sources remain the only authority.

## V44

Added diagnostic theories 17–20 for window-query bandwidth and visualizer writes, with ordered help text and bottom-trim checks.

Evidence: compared V43→V44 archived source; added `write_visualizer_console`; tests `test_v44_theory_range_help_order_and_bottom_trim`.

## V43

Deferred filesystem checks for huge playlists and made lexical path identity independent of file existence.

Preserved executable/regression contracts:

## V42

Added renderer theories 13–16 to compare console-window drawing approaches and expose progress-reading behavior.

Evidence: compared V40→V42 archived source; added `reading_progress`.

## V41

No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.

Evidence note: no version-specific artifact or embedded regression name was recovered for this number; later cumulative sources remain the only authority.

## V40

Made large playlist loading report progress in five-percent steps.

Preserved executable/regression contracts:

## V39

Guarded playlist startup so a positional M3U stays in playlist mode instead of falling into the single-track ffplay path.

Evidence: compared V38→V39 archived source; tests `test_v39_theory_range_help_order_and_bottom_trim`.

## V38

Added theory-12 help/layout diagnostics and nonintrusive terminal-cell measurements; the archived diff also tightens majority-play and Last.fm eligibility checks.

Evidence: compared V32→V38 archived source; added `terminal_cell_pixel_size_nonintrusive`, `terminal_display_signature`, `is_majority_play_eligible`; tests `test_v38_theory_range_help_order_and_bottom_trim`.

## V37

No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.

Evidence note: no version-specific artifact or embedded regression name was recovered for this number; later cumulative sources remain the only authority.

## V36

Preferred written-word EmojiMaxx mappings and added renderer diagnostics that remove window-sensitive terminal sequences.

Preserved executable/regression contracts:

## V35

No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.

Evidence note: no version-specific artifact or embedded regression name was recovered for this number; later cumulative sources remain the only authority.

## V34

No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.

Evidence note: no version-specific artifact or embedded regression name was recovered for this number; later cumulative sources remain the only authority.

## V33

No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.

Evidence note: no version-specific artifact or embedded regression name was recovered for this number; later cumulative sources remain the only authority.

## V32

Added hierarchical/permanent attribute rules, extended timed-lyric formats, and verified embedded lyric round-trips.

Preserved executable/regression contracts:

## V31

Corrected compact Help keys, history wording, and top-visualizer crop defaults.

Preserved executable/regression contracts:

## V30

Made multi-row visualizer paints atomic with synchronized output and explicit row advances.

Preserved executable/regression contracts:

## V29

Separated glyph treatment, processing, palette, persistence, fade, and granularity; added Signal Aurora variants and adaptive high-rate painting.

Preserved executable/regression contracts:

## V28

Locked visualizer rows to column one and normalized circled-number spacing around the compact Play header.

Preserved executable/regression contracts:

## V27

Moved shuffle-cache writes off track handoff, made terminal geometry focus-safe, and refined EmojiMaxx vocabulary.

Preserved executable/regression contracts:

## V26

Added display-only AGC, exact-stem sidecar editing, verified history upserts, persistent queue rotation, and three granularity modes.

Preserved executable/regression contracts:

## V25

Added bounded persistence modes, correct analyzer-behind behavior, physical top-row crop, robust SRT parsing, and EmojiMaxx refinements.

Preserved executable/regression contracts:

## V24

Added bootstrap checks and download progress for missing Claire helper modules, along with an initial color-system path.

Evidence: compared V23→V24 archived source; added `_claire_helper_available`, `_bootstrap_download_progress`, `_download_missing_claire_helper`.

## V23

Established the lower-rate visualizer presentation baseline later used to diagnose high-rate tearing.

## V22

Expanded the visual reference set for SIXEL, glyph families, and karaoke treatments.

## V21

No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.

Evidence note: no version-specific artifact or embedded regression name was recovered for this number; later cumulative sources remain the only authority.

## V20

The surviving V20 source adds karaoke centering and a persistent playlist-shuffle cache, plus tag-recovery tests. Because V14–V19 full sources are absent, this comparison cannot isolate every intervening change.

Evidence: compared V13→V20 archived source; added `playlist_shuffle_cache_path`, `load_playlist_shuffle_cache`, `save_playlist_shuffle_cache`.

## V19

Documented real artwork, karaoke, visualizer, metadata, shuffle, fade, and progress behavior with reference plates.

## V18

No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.

Evidence note: no version-specific artifact or embedded regression name was recovered for this number; later cumulative sources remain the only authority.

## V17

No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.

Evidence note: no version-specific artifact or embedded regression name was recovered for this number; later cumulative sources remain the only authority.

## V16

No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.

Evidence note: no version-specific artifact or embedded regression name was recovered for this number; later cumulative sources remain the only authority.

## V15

Made upcoming EmojiMaxx immediate and added OSC-8 clickable URLs without breaking terminal-cell width.

Preserved executable/regression contracts:

## V14

No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.

Evidence note: no version-specific artifact or embedded regression name was recovered for this number; later cumulative sources remain the only authority.

## V13

The earliest surviving full source already includes DRCS and Sixel visualizer actions, album-art visualizer and karaoke overlay controls, and URL extraction from track comments. No earlier full source survives to isolate what V13 introduced.

Evidence: `PAFPlayer_v13_VISUAL_ART_URLS.py` in `C:\BAT\PAFPlayer\releases`; no earlier full source snapshot.

## V12

Separated Artist/Song animation, stabilized lyric-title ownership, EmojiMaxx fading, and real playlist visit history.

Preserved executable/regression contracts:

## V11

No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.

Evidence note: no version-specific artifact or embedded regression name was recovered for this number; later cumulative sources remain the only authority.

## V10

No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.

Evidence note: no version-specific artifact or embedded regression name was recovered for this number; later cumulative sources remain the only authority.

## V9

No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.

Evidence note: no version-specific artifact or embedded regression name was recovered for this number; later cumulative sources remain the only authority.

## V8

No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.

Evidence note: no version-specific artifact or embedded regression name was recovered for this number; later cumulative sources remain the only authority.

## V7

Refined the terminal UI and established regression coverage for the compact live player surface.

## V6

No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.

Evidence note: no version-specific artifact or embedded regression name was recovered for this number; later cumulative sources remain the only authority.

## V5

No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.

Evidence note: no version-specific artifact or embedded regression name was recovered for this number; later cumulative sources remain the only authority.

## V4

No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.

Evidence note: no version-specific artifact or embedded regression name was recovered for this number; later cumulative sources remain the only authority.

## V3

No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.

Evidence note: no version-specific artifact or embedded regression name was recovered for this number; later cumulative sources remain the only authority.

## V2

No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.

Evidence note: no version-specific artifact or embedded regression name was recovered for this number; later cumulative sources remain the only authority.

## V1

No standalone change artifact was recovered; behavior is preserved only cumulatively in later source/manual artifacts.

Evidence note: no version-specific artifact or embedded regression name was recovered for this number; later cumulative sources remain the only authority.

# Artifact provenance

The retrospective pass inspected the workspace changelog and release folder plus numbered source, notes, and replacement backups in `C:\BAT\PAFPlayer\releases`. Existing historical descriptions remain when they contain more information than a filename. Newly generated source-only lines are explicitly identified as filename-derived; missing numbers and conflicting internal versions are not presented as verified releases. The 2026-10-17 V570 change made no playback-behavior change.
