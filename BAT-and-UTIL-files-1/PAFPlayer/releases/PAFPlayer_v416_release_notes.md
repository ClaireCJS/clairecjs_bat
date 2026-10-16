# PAFPlayer V416 — timestamped playback and TODO release

Built September 20, 2026 from the canonical V414 workspace source. The saved V415 experiment did not contain the newest held-seek logic, so it was not used as the base. The previously installed C:\BAT player was V401. The release identity, build ID and versioned snapshot `play_audio_file_v416_timestamped_timelines_and_external_media.py` now agree on V416.

## Why the progress bar could beat after the music stopped

Parts of the synchronization system already existed: source-time spectrum analysis, a shared console karaoke frame, and a browser lyric timeline. They were not one complete advance-delivery system. Browser spectrum frames were sent as current snapshots, then passed through a worker and smoothing. The progress pulse could fall back to the previous spectrum frame, and its adaptive detector counted a falling energy edge as motion. A decaying pulse could also survive silence.

V416 changes the following:

- The buffered Windows audio renderer reads the output device's consumed-sample position. The isolated audio worker publishes timestamped clock samples every 20 ms. Source position includes the segment origin and playback speed; configured leading device-calibration silence is subtracted. The first selected output is the reference when several outputs are active.
- The console spectrum, karaoke, and progress beat select data by that source position. All five beat detectors are computed ahead on the analyzer thread. Missing data and genuine silence produce zero pulse; renderer delays cannot replay old beats. A seek selects the new timestamp directly.
- Analysis works up to 12 source seconds ahead. `/api/timeline` sends available future spectrum samples with source frame indexes, frame rate, speed and a clock anchor, covering roughly four playback seconds per response. The browser selects the due sample during animation and bypasses the old temporal smoothing for file playback. Requests refresh every 150 ms while visible.
- Browser lyrics receive the cue timeline and prefetch upcoming styled text. Popup/floating lyrics now receive the entire cue timeline, and their GUI loop reads the audio clock independently. The HTTP timeline endpoint also reads that clock independently when the console is occupied by a menu.
- Pause, seek, track replacement and stop update or clear the corresponding timeline state. Browser status metadata continues updating even while the timeline supplies the newer clock anchor.
- Native clock reads and device closure share a lock. A muted hardware test exposed that race; the final consumed position is now retained safely after closure.

This schedules presentation against audio rather than against packet arrival. It does not remove terminal painting time, browser display refresh, or latency beyond the Windows output device. The explicitly selected legacy FFplay backend still has an estimated clock because it exposes no consumed-sample counter. Live microphone/loopback input remains live and cannot be pre-sent. Cold analysis or a long network interruption yields missing/blank visual frames instead of replaying stale beats; up to four seconds of already delivered browser frames can bridge a short interruption.

The clock handling follows Microsoft's [playback-position guidance](https://learn.microsoft.com/en-us/windows/win32/multimedia/retrieving-the-current-playback-position) and [waveOutGetPosition contract](https://learn.microsoft.com/en-us/windows/win32/api/mmeapi/nf-mmeapi-waveoutgetposition), including drivers returning samples, milliseconds, or bytes.

## The circled-number spacing bug

The Windows Terminal substitution layer already added two ordinary safety spaces after generated negative circled digits such as `❷`. With the source word separator, the resulting run was three spaces. The current sung line passed through `wrap_to_cells`, which used `split()` and joined words with a single space. That destroyed the safety spaces. Previous and next lines took a different path and retained them.

The wrapper now preserves those spaces, includes them in wrapping/centering width, and still normalizes tabs/newlines so they cannot escape a terminal row. It does not guess another glyph width or add more padding. Renderer tests cover every digit 1–9, several typography styles, every color treatment, exact-fit/wrapped cases, and literal symbols. Generated `up` keeps its Windows Terminal-only safety space; literal arrows and `play` get no additional space. These are rendered-text/width checks, not a screenshot measurement of the user's active Windows Terminal font.

## Saved TODO decisions and controls

Every finite item in `PAFPlayer_TODO.md` has been implemented or reviewed in this release.

- Removed the listed unsuitable substitutions, including `yelling`, `broke`, `flicking`, generic face/confront/encounter/stuck families, and single/double/multipliers through decuple. These removals are enforced after imported mapping tables.
- Set `grew` → 🌱, `person` → 👤, and both `30`/`thirty` → ㉚. Kept `wish`, `pray`, and `broken` → 💔.
- `praying`, `speaking`, `talking`, `licking`, and `worshipping` derive from their base mapping plus the retained suffix. `flicking` stays removed. Removed `teenage`; the other reviewed age words were already unmapped except `kid` and `child`, whose recognizable child mappings were retained.
- `J` aliases Insert. Enter enqueues the focused or selected songs; Shift+Enter jumps to the focused song. Ctrl+Space selects multiple search results. Shift+Insert retains every selection from the Windows file picker. Help and prompt wording match these actions.
- A dedicated key sampler retains rapid Ctrl+Alt+Left/Right taps and held repeats while the playback controller is restarting audio. Deltas accumulate and use the shorter seek preroll. Audio still restarts for a seek; this does not introduce a separate seamless decoder.
- HUD URLs omit a display-only trailing slash while links retain their original target.
- Shuffle uses symbol then history/random indicator. Repeat uses loop symbol then folder/playlist indicator. Existing shared state continues driving labels, tooltips and enabled/disabled styling.

## Automatic pause for other media and gentle resume

Enabled by default. When VLC, Winamp, or browser media such as YouTube starts playing, PAF pauses at its current source position. When all detected competing playback stops or pauses, PAF waits for 1.5 seconds of confirmed inactivity, then resumes from the held position with a 15-second fade from silence to the selected volume.

The source defaults are `EXTERNAL_MEDIA_AUTO_PAUSE = True`, `EXTERNAL_MEDIA_RESUME_FADE_SECONDS = 15`, and `EXTERNAL_MEDIA_RESUME_QUIET_SECONDS = 1.5` near the top of `play_audio_file.py`. In the web interface, **Playback → Pause for VLC, Winamp and browser media** enables/disables the feature; **Automatic resume fade-in** persists a duration from 0 to 120 seconds. Zero means immediate full-volume automatic resume. A changed duration applies to the next automatic resume.

- Winamp is queried with its read-only playback-state IPC. Windows system media sessions supply actual transport states for integrated VLC/browser players. Windows audio-session streaming state is the fallback, across every active output endpoint. Merely running a process does not count as playback, and quiet passages within a running stream do not count as completion.
- Browser detection includes other media in Chrome, Edge, Firefox, Brave, Vivaldi, Opera, LibreWolf and Waterfox as well as YouTube. Windows media-session identity does not reliably expose a site's URL, so this is intentionally a browser-media feature, not a YouTube-only URL matcher. Muted media can still be detected when its browser publishes playback state; a browser that publishes neither a media session nor a running audio stream cannot be detected by these APIs.
- Only an automatically imposed pause is automatically released. Manual Pause stays paused. Pressing the web Pause button during an automatic hold converts it to a manual hold. Explicit Play (or the pause-toggle while paused) overrides the current interruption; detection rearms after the competing media has gone quiet.
- Multiple players hold PAF until all are inactive. A failed/stale monitor does not silently release an automatic hold. The Playback section shows monitor trouble and the automatic-pause/fade state. Disabling the feature releases its automatic hold, while preserving manual pauses.
- The old behavior that repeatedly paused Winamp has been removed from PAF's playback/session loops. PAF never sends pause, play, or stop commands to the competing applications for this feature.
- The envelope is processed in the audio filter after speed conversion. Fifteen seconds means fifteen audible seconds at any playback speed. The selected volume and ReplayGain remain intact. Output/volume/seek restarts continue the existing envelope, and the coordinator survives playlist track changes. An automatic hold is not saved as a manual pause for the next PAF launch.
- One hidden read-only Windows helper runs per PAF session and exits with it. It uses built-in Windows PowerShell/.NET, not an additional Python package or a browser extension.

Validation covers competing players, brief gaps, manual ownership, overrides, monitor failure, configurable duration, native and legacy filter plumbing, and an actual player-loop pause/resume preserving its seek position. A real FFmpeg-decoded 16-second sine confirmed near-zero initial amplitude, half final amplitude at 7.5 seconds, and full selected gain at 15 seconds. Native Windows media-session and audio-session enumeration both passed outside the sandbox; the audio-session fallback and helper shutdown also passed inside it. No interactive Winamp/YouTube session was started or interrupted during testing.

The probe uses Microsoft's [system media-session API](https://learn.microsoft.com/en-us/uwp/api/windows.media.control.globalsystemmediatransportcontrolssessionmanager?view=winrt-26100) and [audio-session playback states](https://learn.microsoft.com/en-us/windows/win32/api/audiopolicy/nf-audiopolicy-iaudiosessioncontrol-getstate).

## Artwork seam experiments

The persisted `ArtworkSeamStrategy` selector is at the bottom of **Broken experimental** in the web UI. New installations default to 0.

| Value | Implemented experiment |
| --- | --- |
| 0 | Existing rendering, no seam experiment. |
| 1 | Full-cell color blocks with one-column overlap. |
| 2 | Fill isolated dark cells between bright neighboring cells. This can also fill a real one-cell dark detail. |
| 3 | Prefer the existing retained SIXEL artwork layer when Chafa is available. Terminal bitmap erasure/compositing behavior still matters. |
| 4 | Chafa symbol output using the measured terminal cell aspect ratio. Work is asynchronous and cached; the existing rendering remains visible while it prepares. |
| 5 | Quantize artwork consistently into the downloaded DRCS bank; use native fallback when no bank is available. |

Thin dividers can come from glyph ink not reaching cell bounds, aspect-ratio sampling, dark quantization cells, or a charset/cursor-advance mismatch. These strategies exercise those separate mechanisms; they do not establish that all seams on the user's font are cured. The Chafa strategy uses its documented [symbol and font-ratio controls](https://hpjansson.org/chafa/man/). Its actual ANSI output and parser were tested with the installed binary. DRCS fallback bytes keep their proper charset during asynchronous preparation.

## Validation

- 56 focused and existing audio/UI/rendering tests passed (32 V416 behavior/integration tests plus 24 established audio/rendering checks).
- A real FFmpeg analysis of two generated bursts detected the first at 0.467 seconds (the expected 30 Hz analysis resolution), the final nonzero frame at 1.600 seconds, and zero spectrum/pulse at 2 seconds across all five detectors.
- Node checked the embedded browser JavaScript and exercised timestamp selection, speed, pause, expiry, future-frame delivery, and status metadata arriving after the timeline.
- Muted native playback produced 150 monotonic clock samples and completed normally. A separate EOF stress check ran 12 short muted tracks with four concurrent readers, 4,002 samples, and no access violations; the final clock was retained.
- The final 656-test historical run reported 46 failures and 5 errors, versus 51 failures and 5 errors in the original V414 baseline. One extra full-suite failure was a global subprocess-call-count test; it passed immediately when run alone (0.005 seconds). The earlier frozen V416 run had 45 failures/5 errors and no added failing test names. The suite is not fully green. Reports and hashes are recorded in the release manifest.

Run `play_audio_file.py --version` and `play_audio_file.py --which-script` to identify the active copy. An already-running Python player must be restarted to load this release. For a direct terminal comparison, run `play_audio_file.py --emojimaxx "1 2 3 4 5 6 7 8 9 up play"`.
