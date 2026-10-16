# PAFPlayer V402 verification

Date: 2026-09-08. Python 3.10.9 / NumPy 2.2.6 on the user's Windows machine.

## Changes

- Buffered stereo and MatrixMixer multichannel playback now run in a separate audio worker process. FFmpeg PCM goes directly to WaveOut inside that worker; artwork and Tk rendering cannot hold its Python GIL. The worker and decoder request above-normal process priority; the WaveOut pump requests Pro Audio MMCSS with high thread priority.
- The requested audio reservoir is honored at high sample rates instead of being capped at seven blocks. Multiple outputs retain their common start barrier and relative latency compensation. Stop, seek/restart, natural EOF, decoder/device failure and loss of the owner pipe are handled; shutdown closes the pipes and owned decoder processes. Worker health includes queued milliseconds and detected empty-queue underruns in `/api/status`.
- Cursive fix is red and labeled `Cursive fix (broken)`. The section title is `Artwork Pop-Up`. Bar artwork blend uses the standard blue visualizer styling and no EXP badge.
- New persistent `Bar opacity` slider immediately follows Bar artwork blend. 0% preserves the prior blend exactly; 100% uses solid palette-colored bars; intermediate values retain artwork underneath stronger bars. It works in all three blend modes and the optional NumPy/scalar paths.
- Both popup sections have `Bring to center` immediately after `Bring to top`. Recovery chooses the foreground window's monitor (primary fallback), fits oversized windows within its work area, restores visibility, and saves placement. Floating lyrics open in their visible editor so empty lyrics can still be located. Native Windows positioning handles negative desktop coordinates; floating resize/drag operations retain those signed coordinates.

## Playback verification

The reported file, `T:\mp3\Voiid\2019 - Drool (EP)\4_Durry Mouth.flac`, is 44.1 kHz / 16-bit stereo, about 162.279 seconds. Full FFmpeg decoding completed successfully without decode errors.

The audio stress test used an eight-second excerpt, muted in FFmpeg before any physical output, on the default WaveOut endpoint at 7.1 / 96 kHz / 24-bit. The owner interpreter was deliberately blocked four times for 900 ms with a GIL-holding native call. Each post-stall status sample reported about 341 ms queued and zero underruns. Natural completion returned exit code 0. The stress test passed both before and after the lifecycle refinements.

Four additional muted native-device cases passed: an 80 ms track shorter than the preroll target (44.1 kHz stereo), stopping a playing worker, starting another excerpt at 60 seconds, and closing the owner pipe while playing. Stop and owner-EOF cleanup completed in about 46-47 ms after the request; all cases returned 0 and closed both status/control pipes.

These are decoder, queue-health and lifecycle checks. The song was not auditioned audibly end to end in V402, and zero reported queue underruns does not rule out every possible hardware/driver dropout.

## Rendering and UI verification

- All 12 V402 tests pass: isolated output ownership and failure cleanup, shared multi-output start barrier/delays, buffer duration at 96/192 kHz and larger buffer requests, stop-barrier release, control schema/actions, recovery queue and monitor geometry/native positioning, opacity endpoints/midpoints, and NumPy/scalar exact output equivalence.
- All 12 V394/V397/V401 rendering test groups pass, retaining the V401 bar-art acceleration and exact prior output at 0% added opacity.
- Of 57 selected existing audio/window/control regressions, 53 pass. The remaining four also fail in the unchanged V401 release: `test_v170_art_window_focus_transparency_zoom_and_plasma_contract`, `test_v192_floating_overlay_is_content_sized_and_drag_stable`, `test_v192_resize_preserves_floating_center_and_artwork_rectangle`, and `test_v263_release_identity_split_hud_profiler_and_geometry_contract`. The obsolete multi-output source assertion was updated to check the barrier in its new worker location; the bar-art dependency assertion includes the new slider.
- A temporary local browser preview visually confirmed the red cursive control, shortened artwork heading, both center buttons in order, blue blend control without EXP, and adjacent opacity slider. The preview was closed afterward. Native multi-monitor placement was checked with mocked Windows calls; the live user's popup windows were not moved during verification.
- A 30-frame interleaved renderer timing check at 200 columns x 32 rows, artwork detail 9, gave median 13.91 ms at 0% opacity and 13.80 ms at 35%. P95 was 22.75/22.98 ms. This small comparison shows no material extra blend cost in that case; it measures ANSI generation, excludes terminal I/O, and is not an end-to-end FPS claim.

## Files and use

Restart PAFPlayer from the updated workspace `play_audio_file.py` to load V402; an already running V401 process cannot acquire these changes. Refresh its browser page after restarting. Try 25-40% Bar opacity as a starting point for stronger bars with visible artwork.

Version snapshot: play_audio_file_v402_isolated_audio_and_window_recovery.py

Main and snapshot SHA-256: EAEC01C15C87CB91A491897582D3DF368EFE82F2C447D56637EDFD5FE4B867D1

Verified sibling replacement backups were created before every overwrite. The original main source for this operation is `play_audio_file.py.bak.202609081134.replaced-by-chatgpt.bak`. Existing V401 release files and the user's intervening emoji edit were preserved. No files under `C:\BAT` were changed. No package installations were required.

Reproduce from this workspace:

```powershell
& 'C:\ProgramData\anaconda3\python.exe' -B -X utf8 test_play_audio_file_v402_audio_ui.py
& 'C:\ProgramData\anaconda3\python.exe' -B -X utf8 test_play_audio_file_v402_audio_ui.py --audio-stress
& 'C:\ProgramData\anaconda3\python.exe' -B -X utf8 test_play_audio_file_v402_audio_ui.py --audio-lifecycle
& 'C:\ProgramData\anaconda3\python.exe' -B -X utf8 -m unittest test_play_audio_file_v394_rendering test_play_audio_file_v397_bar_art_performance test_play_audio_file_v401_bar_art
```
