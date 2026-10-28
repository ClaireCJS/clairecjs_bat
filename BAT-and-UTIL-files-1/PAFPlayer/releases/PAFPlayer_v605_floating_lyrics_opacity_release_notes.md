# PAFPlayer V605 — Floating Lyrics opacity

Released October 23, 2026.

- Web Configuration → Floating Lyrics has a 10–100% whole-window opacity slider. Changes apply to the running lyric window and save as the global default. An unset value is 100%.
- `--floating-lyrics-opacity=45` changes the current run only. An already running official instance receives this command through its authenticated local single-instance handoff. It can accompany a track filename. It does not rewrite the saved opacity.
- `--default-floating-lyrics-opacity=75` saves the default for future runs. With no other arguments, it saves and exits without starting playback. Both options accept `=VALUE` or a space before the value; malformed or out-of-range values are rejected.
- If both options are present, the session value applies now and the saved default applies on later runs. An explicit `--instance` launch applies its session value to that instance and does not seize the official player's ownership.
- The floating window's positioning and edit controls remain fully visible while editing; the selected opacity returns afterward. The separate Emojimaxx answer opacity is unchanged.

Verification: focused V605 tests cover parsing, saved-default precedence, registry mapping, the web slider/action range, renderer command routing, and authenticated handoff. JavaScript syntax, Python syntax, bundled-source parity, and relevant existing tests were also checked. Windows Tk accepted both chroma-key transparency and the requested alpha setting in a hidden-window check. Visual shell composition was not evaluated during actual playback.
