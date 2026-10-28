# PAFPlayer V597 — Discord lyric lag adjustment

Web Config → **Discord integration** now offers a **Discord lag** slider with
an editable seconds field to its right. It accepts 0–5 seconds, defaults to 0,
and saves with the existing Discord integration settings. For a measured
1.5-second Discord display delay, enter 1.5 and save.

Both Discord Desktop IPC and Social SDK now choose lyric text from PAFPlayer's
timed cue list at the playback position plus the selected lead time. Playback
speed and the existing karaoke display offset are respected. Pausing keeps the
current lyric; a cue gap displays `🎤 ♪`. Metadata, privacy, stopped-playback
clearing, and the two-line activity format retain their prior behavior.

The Discord publisher checks for lyric changes every 200 ms instead of every
two seconds. When no browser or screensaver client is active, the playback
owner updates only Discord's lyric clock without serializing a full browser
status response. Animation frames do not generate activity updates; the
Desktop IPC path retains its existing 15-second keepalive.

Focused tests cover lookahead, playback speed and offset, pause, private-track
clearing, malformed settings, persistence, and the browser-free clock update.
Discord controls when an activity appears on other devices, so the setting is
a calibration control rather than a guaranteed display timestamp.
