# PAFPlayer V421 — manual Play wins

September 21, 2026. Build `2026-09-21-v421-manual-play-override`.

V420 gave detected external playback unconditional priority and refused manual Play. This was incorrect: it trapped the user in an automatic hold whenever background media remained active.

V421 treats the first observed media state as the background baseline. Those already-active applications do not interrupt startup. A newly active application pauses PAFPlayer. Play (including the Winamp-compatible URL) or Space while paused resumes immediately and acknowledges currently active applications, preventing an immediate repeat pause. Acknowledgements are per application; an acknowledged Chrome video cannot hide a newly started VLC player. Each application's acknowledgement expires after that application is confirmed inactive for 1.5 seconds, independently of the other applications. Unknown monitor data neither expires an acknowledgement nor blocks manual Play.

Automatic holds resume after the interrupting applications finish and the quiet interval passes, even if acknowledged background media continues. The automatic fade remains 15 seconds by default and configurable in web playback settings. Manual Play is immediate. Manual Pause and Stop still cancel automatic resumption. Web help now explains Play correctly, and status exposes `external_media_acknowledged` for diagnosis.

Detection currently groups sources by application: it does not distinguish a second Chrome tab while another Chrome tab is acknowledged. A browser must become inactive before that browser can interrupt again. This is not a per-tab timestamp or media identity implementation.

Validation: 51 focused tests passed across V421, updated V420 control/player-loop tests, V416 external media, V418 detectors, and V417 transport/downloads. Existing tests now establish an idle baseline before simulating newly started media; assertions requiring Play to remain blocked were replaced with the corrected behavior. The full-loop test verifies manual Play, a subsequent VLC interruption while Chrome continues, automatic fade, and manual hold.

A separate muted real-player test used live native detection of Chrome and VLC, an explicitly injected idle baseline, and real IsolatedWaveOutProcess workers. It verified worker shutdown on automatic pause, restart after Play, and continued playback with both external applications still active. Report: `pafplayer_v421_live_player_check.json`. Test-harness timing/post-Stop assertions were corrected before the passing run; no user's media app was controlled. The historical full suite was not rerun.

Preserves the earlier timing, karaoke, emoji, downloads and transport changes. Restart PAFPlayer and confirm V421 to load this correction; an already-running V420 process is unchanged.
