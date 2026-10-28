# PAFPlayer V610 — Discord presence verification

The requested Discord Rich Presence layout was already present in V595. Focused
tests now verify `🎵 Song · 👩‍🎤 Artist · 💿 Album (YYYY)` on the first activity
line and `🎤 Lyric` or `🎤 ♪` on the second. They cover both Desktop IPC and
Social SDK publication, lyric changes without animation-frame updates, absent
metadata, long text, paused and stopped playback, and privacy clearing. The
`PAFPlayer` application name remains controlled by Discord.

This release repairs three older test files that looked for feature sources in
the project root after the V604 move to `src/`. It does not change Discord
publication behavior or saved settings. Social SDK live validation still
requires Discord's official SDK and a real-account test. Whip glyph appearance
and Windows lock-screen panel behavior still require physical-client checks.
