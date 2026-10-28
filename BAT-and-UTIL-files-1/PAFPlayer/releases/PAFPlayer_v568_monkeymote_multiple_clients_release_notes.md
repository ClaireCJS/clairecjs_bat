# V568 — MonkeyMote multiple clients and live settings

October 16, 2026

The previous listener served a connection inline in its accept loop, preventing
a second phone/tablet from authenticating until the first disconnected. V568
uses up to eight independent client workers with bounded authentication, idle
and rate limits, per-client playlist tokens and one shared synchronized command
gate. Artwork conversion is shared and bounded. Only the original official
PAFPlayer instance can receive or configure MonkeyMote commands.

## Changes

- Simultaneous multiple MonkeyMote clients (up to eight).
- MonkeyMote tab near the bottom of web configuration; compatibility enabled by
  default, with explicit confirmation to save a permanent disabled choice.
- Displays listening address, current port and connection count. Default TCP
  port 19371; CLI --monkeymote-port=PORT overrides the port for the current run.
- Edit the port during playback; popup choices: This run only / Save for future
  runs / Cancel. Bind/save failures leave the old listener and saved preferences
  intact. A successful port switch disconnects phones, which must reconnect.
- Existing --monkeymote-config JSON remains supported. Saved enabled/port values
  override JSON, then an explicit CLI port overrides the saved port for one run.
  Preference IDs elsewhere are preserved. Default binding uses the private
  default-route IPv4 address and real subnet mask, with loopback fallback.
- Retain pause-state acknowledgments so local pause/resume between phone polls
  cannot permanently block later MonkeyMote transport commands.
- Artist/genre Details drill-down gets a correlated empty response instead of
  no response. This does not implement full library browsing.
- Main documentation summary and MonkeyMote guide include simultaneous clients,
  all settings, limitations, and a two-device manual verification procedure.

## Verification and limits

81 focused and related tests passed: codec/handshake, multi-client real TCP with
emulated MonkeyMote clients, stalled peers, eight-client cap, shared command gate,
shared cover conversion, shutdown/ownership loss, port handoff and bind failure,
saved settings/backup/restart, HTTP security, queue/tray/remote controls and key
playback-order regressions. Seven executed JavaScript UI flows passed. Python
compilation passed for changed code/test tools and all 21 bundled modules.
A separate active-client disable/re-enable check also successfully rebound the
same port on this Windows computer. Tests ran in isolated retained fixtures;
no live playback commands or persistent player settings were changed.

This was the focused suite, not the entire historical regression suite. A
previously documented unrelated workflow HTTP fixture failure remains outside
this suite (monkeymote-baseline-http.log). The current feature endpoint and
security paths have their own passing checks.

Real iPad evidence from V565–V567 covers connection, playback controls, current
track, queue order/selection, current cover, future-track Details, and Lyrics.
V568 simultaneous physical devices, port-switch UI in a live browser, and empty
artist/genre result rendering still need the user's restart test. Android,
password-protected physical-device sessions, and long-duration multi-device use
remain unverified. See docs/monkeymote.md for the step-by-step checks.

Manual connections only; no Bonjour discovery. MonkeyMote transport remains
unencrypted even with a password: trusted home subnet only, no Internet port
forwarding. Full library browsing, saved-playlist editing, ratings, seek/stop,
noncurrent artwork, equalizer, and widgets remain unsupported. The listener does
not change Windows Firewall or router settings. An explicit --instance process
cannot inherit the listener or promote itself into MonkeyMote control.

## Publication

The workspace PAFPlayer.py and this release are identical single-file builds.
Every replaced project file has a verified backup; main-source backups are in
releases, changelog backups in backups, and documentation backups in docs.
No existing release artifact was overwritten. The user restored PAFPlayer.py to
the project during this work; the old releases directory was absent, so a new
releases directory now holds this release and required new source backups.
No literal C:\BAT paths were created, modified, copied, moved, or deleted.
play_audio_file.py, live music, installed plug-ins, UAC and firewall were untouched.

Reports:
- tests/reports/monkeymote-checks-20261016-164930.json
- tests/reports/monkeymote-v568-artifact-checks-20261016-1650.json
- tests/reports/monkeymote-v568-change-inventory-20261016.md
