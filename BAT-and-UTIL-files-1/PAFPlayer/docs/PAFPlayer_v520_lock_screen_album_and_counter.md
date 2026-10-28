# PAFPlayer V520 manual — lock-screen album and playback counter

Released 2026-10-10. Build `2026-10-10-v520-lock-screen-album-playback-counter`.

The detailed lock-screen status now requests three rows:

1. Artist — song
2. `1:01 / 2:00 · Album name`
3. Current timed lyric

The album/counter row replaces the previous-lyric row when those fields are available.
An older player without either field keeps the previous/current lyric layout.
The small quick-status badge still shows playing, paused, idle or offline: Windows
supports numbers or preset glyphs there, not arbitrary time/album text.

Elapsed/total time comes directly from the player's existing status, with no second
playback clock. The counter changes at whole seconds; lyric changes still publish
immediately at the next poll. Pause freezes elapsed time, seeking updates it, and
offline status drops stale album/time. Unknown time is `--:--`; hours are supported.
Long album names cannot push the counter past the 120-code-unit text limit. Windows
may truncate the row further.

V519's leaner artwork console output and 250 ms lock-only lyric lead are retained.
The counter is not shifted by that lead. V519's identical-frame benchmark reduced
output bytes by 42–64%; actual in-game FPS still needs comparison.

## Validation

- 183 focused checks passed: 84 C# formatter/publication checks, 86 Python
  endpoint/lifecycle/installer/tray checks, and 13 renderer/native-fallback checks.
- Python compilation, C# compilation, full MakeAppx validation, EXE/MSIX signatures,
  pinned artifact checks, and interactive activation/publication passed.
- The V520 companion submitted real notifications as DEMONA\Claire, session 1;
  background registration/access and COM activation passed. This verifies Windows
  accepted publication, not that the new layout was visible while locked.
- All main-player function/class ASTs and native encoder data match V519. Only
  version constants and the bundled lock-screen endpoint changed in PAFPlayer.py.
- The preceding V519 comparison ran all 678 embedded tests on V518 and V519: each
  had 614 passes, 51 failures and 13 errors, with identical failing/error identities.
  That full comparison was not rerun for V520's compact-field/formatter change.
  The pre-existing failures and separate legacy floating-mask fixture error remain
  documented in [V519 verification](performance-v519.md).

Reports are under `tests/reports`: `v520-source-scope.json`,
`v520-status-updater-20261010065911.txt`, `v520-regressions-20261010065956.txt`,
`v520-renderer-20261010070041.txt`, and
`v520-publication-93e1c268701142ecb3f06d197afaa7c1.json`.

## Load and verify

Relaunch PAFPlayer using V520 when ready. The running V518 session was left playing;
it cannot provide album/counter fields until relaunched. The V520 companion is
installed, with the same Recovery package family, app ID and configuration IDs.
Choose **PAFPlayer Lock Screen V520** in the top detailed-status slot. A bottom
quick-status slot is optional for the playing/paused/offline icon.

Play a track with an album tag and timed lyrics, close the web browser, and lock
Windows for a minute. Confirm elapsed/total time advances, album/current lyric are
visible, and lyric gaps do not collapse the status area. Check pause/resume, a
backward seek, a new album, unknown duration and disabling the feature using normal
player controls. Compare visualizer responsiveness while gaming after relaunch.
Windows controls presentation and can coalesce fast updates; not every short cue
is guaranteed a visible frame. Actual locked-screen appearance and game-loaded FPS
remain unverified by the agent.

See the [lock-screen guide](windows-lock-screen.md).
Verified backups precede replacements. V519 and older release artifacts are intact.
No playback commands were sent; UAC and play_audio_file.py were not changed.
**No literal C:\BAT paths were created, modified or deleted.**

For historical comprehensive coverage, see the [main manual](../PAFPlayer.md).
