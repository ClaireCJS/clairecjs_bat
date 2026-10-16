# PAFPlayer V517 — live lock-screen lyric lines

The companion's five-second polling could miss lyric lines. More importantly,
its ordinary hello read did not keep PAFPlayer's status active, so closing the web
player could leave the published lyric stale or blank while track text worked.

V517 uses a local-only compact hello query to keep the existing 200 ms status
cadence active without browser spectrum work. Both publisher modes poll at
250 ms and submit changed lines immediately. Unchanged tile/badge content renews
at 30 seconds; lyric changes do not repeatedly update the playing badge. The
shared HTTP client has bounded responses/timeouts and requests never overlap.
Offline reads clear stale lyrics and slow retries. No audio function changed.

Launch the V517 player after upgrading its signed 517.0.0.0 companion. The
Recovery family, App ID and configuration IDs are unchanged. The top detailed
status slot displays lyrics; bottom quick-status slots display only badges.
The running V516 music session was not restarted. Older player hello envelopes
remain readable, but the browser-closed freshness fix requires V517.

138 focused tests passed (61 C#, 77 Python), including real local HTTP, no-browser
status activity, identity/access restrictions, line changes, pauses, backward
seeks, gaps, offline clearing, retry and expiry renewal. Compilation, full MSIX
validation, both signatures and interactive activation/publication passed.
Windows accepted a real official-player tile and badge under the interactive
account. New lyric timing has not been visually checked while locked.

This is line-by-line text. The existing 200 ms state cadence plus 250 ms poll can
add about 450 ms before Windows/network delay; word highlighting and exact
render timing are not promised. Timed lyrics must already be available.

On October 9 the user confirmed native status works; a read-only check reports
EnableLUA=1. The October 8 rejection report is retained as historical evidence.
This release did not change UAC, playback or play_audio_file.py. Verified backups
precede replacements; earlier release artifacts remain intact. No literal
C:\BAT paths were created, modified or deleted.

See [the guide](../docs/windows-lock-screen.md) for architecture and manual checks.
