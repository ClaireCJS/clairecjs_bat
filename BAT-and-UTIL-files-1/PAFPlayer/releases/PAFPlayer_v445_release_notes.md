# V445 — Pause reasons and artwork-detail applicability

September 23, 2026. Based on V444, retaining the isolated V427 console row fix.

The `?` help screen now explains every paused state in parentheses:

- `Paused (restored previous pause state)`
- `Paused (hit pause key)`
- `Paused (web pause)` or `Paused (web stop)`
- `Paused (VLC playback detected)` and corresponding detected player names

The reason is retained through idle polling and temporary loss of media-monitor
data, replaced when a manual pause overrides an automatic pause, and cleared
on resume. Already acknowledged background players are excluded from the
automatic pause reason. YouTube is named when the monitor identifies YouTube;
a generic Chrome session remains labelled Chrome rather than guessing its site.
The reason is also available in web status and the pause trace event.

As requested, startup continues to restore the saved pause state. The previous
startup pause could be unexplained because its synthetic pause-toggle was
indistinguishable in the help display from a manually requested pause. It now
has an explicit restoration reason; pause persistence and startup behavior are
otherwise unchanged.

Both artwork cell-detail selectors, including their Fav/Def/cycle controls,
are disabled when Granularity is not `2× Twin DRCS`. A visible explanation says
`Requires Granularity: 2× Twin DRCS.` The selectors become available when that
mode and the corresponding artwork layer are enabled. A forced Unicode
diagnostic renderer gets its own explanation. No granularity or detail value
is changed automatically.

Validation: 27 focused tests passed, covering the real player loop with mocked
audio for all five pause examples, existing manual/automatic media arbitration,
the actual JavaScript control-enablement code, and the native Windows console
row-repair regressions. Full web JavaScript syntax was checked. AST comparisons
confirm that the renderer, console writer, and main startup/settings dispatch
are identical to V444.

Restart PAFPlayer to load V445 and refresh its web page for the updated controls.
