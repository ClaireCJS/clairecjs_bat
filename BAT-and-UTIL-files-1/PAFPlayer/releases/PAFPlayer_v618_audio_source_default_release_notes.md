# PAFPlayer V618 — Playback device default

The Playback tab mirrors the underlying controls. Its Device **Def** radio
previously forwarded only a change event, while the save handler required a
click. The mirror now forwards default-radio clicks to the original control,
and the saved checked state is synchronized after the browser's click completes.
The cloned radio names are distinct, so checking the mirrored mark cannot
uncheck the original one.
Save errors are shown instead of silently leaving the mark unchanged.

The Device chooser and Fav/Def marks now occupy one row. The existing
`OutputDevicesMask` default and `/api/choice-mark` endpoint remain the source
of truth; selecting a default does not immediately change the playing output.

Regression coverage exercises the actual mirrored browser control with a
stubbed API, its saved checked state, its horizontal placement, and the
existing default-setting backend.
