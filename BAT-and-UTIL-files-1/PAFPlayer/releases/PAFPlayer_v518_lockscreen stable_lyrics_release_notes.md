# PAFPlayer V518 — stable lock-screen lyric updates

Released 2026-10-10; build `2026-10-09-v518-lockscreen-stable-lyrics`.

V517 renewed the badge independently of detailed text. The Windows trace showed
those badge-only arrivals removing detailed status until the next lyric tile,
including an approximately eight-second absence. V518 always submits the badge
and text together, with text last, and renews both on the same deadline.

The requested layout now shows artist — song, previous lyric and current lyric.
Blank rows use nonempty placeholders. The compact V518 endpoint supplies the
actual preceding cue, including a brief cue that fell between 250 ms polls;
older players fall back to the previously observed line. Gaps, track changes,
seeks and lyric offsets are covered. Exact word timing and every arbitrarily
short cue are not guaranteed: Windows coalesces updates and owns the layout.

The signed companion is installed as **PAFPlayer Lock Screen V518**. The package
family, app ID and configuration IDs remain unchanged. Launch the V518 player
for the full previous-cue improvement. The top detailed-status slot displays
lyrics; an optional bottom quick-status slot shows only the playback badge.

## Validation

148 focused tests passed (67 C#, 81 Python). Python/C# compilation, full MakeAppx
validation, executable/MSIX signatures, pinned artifact checks, interactive
activation/publication and background COM registration passed. The live official
server was also verified as V518 on October 10 with previous-cue context present.
The main player function/class ASTs are unchanged from its pre-edit backup.

In the real V518 manual lock cycle, Windows recorded 32 text updates, with one
brief explicit clear during the installation's standalone-to-managed handoff.
After the publisher settled, 23 updates had no detailed-status removal. This is
renderer evidence, not visual proof that all clock movement or missed lines are
gone. A restart/handoff may still briefly clear the status. The manual visual
checks in the [guide](../docs/windows-lock-screen.md) remain outstanding.

The existing full-suite baseline is not represented as all-passing: the earlier
678-test V514/V515 comparison had identical 614 passes, 51 failures and 13 errors.
This release ran focused tests and checked unchanged main-player function bodies.
Git status could not be used because the local repository reports `bad object HEAD`;
source backups, AST comparisons and release hashes provided the verification.

## Files and compatibility

- Active source and descriptive release copy contain the same V518 player.
- The release package and bundle include the signed companion; no private key.
- Docs and immutable manual snapshot describe the new behavior and limitations.
- All replacements have verified backups; V516/V517 release hashes remain intact.
- No UAC changes, playback commands or `play_audio_file.py` edits were made.
- **No literal `C:\BAT` paths were created, modified or deleted.**

Reports are directly under `tests/reports`, including
`v518-badge-disappearance-evidence.json`, `v518-lock-cycle-analysis.json`, and
`v518-publication-2aeb83518a4741b8a98a3433a90b0636.json`.
