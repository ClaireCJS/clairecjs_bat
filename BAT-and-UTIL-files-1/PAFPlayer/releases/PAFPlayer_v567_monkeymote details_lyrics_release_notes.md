# PAFPlayer V567 — MonkeyMote

October 16, 2026.

Future-track Details now responds to request 1 for the selected published
playlist index, checks live membership, and uses PAFPlayer's read-only metadata
probe. At most 16 results are cached for 30 seconds. Details never sends a
playback command. Lyrics now publish on connection and track/timeline changes,
as well as on request; the response contains plain text, not timed karaoke.
The listening announcement now begins with 💰.

A loopback-only /api/monkeymote/diagnostics endpoint exposes at most 128 recent
in-memory protocol events without song text, filenames, passwords or challenges.
There is no continuous trace-file write. It rejects non-loopback requests and
becomes unavailable when the listener is disabled or loses official ownership.

67 focused and relevant existing tests passed, covering actual emulated sockets,
handshake, fragmentation, request formats, queue order/invalidation/selection,
repeated-button pressure, cached media, future-track details, diagnostic endpoint
access, official-owner restrictions, legacy tray/browser controls and playlist
rotation/history/resume. Python compilation passed. Tests are not a full-suite
claim: an unrelated workflow HTTP-status test also failed on the untouched
baseline (HTTP 500); its retained baseline report documents that pre-existing
failure. Live registry/log writes from tests were blocked by the existing test
guard; fixtures were isolated and preserved.

Real-device status: the user verified V566 core controls, order/selection,
artwork and backlog prevention. V567 Details and Lyrics await the user's restart
and iPad test. At release preparation the official HTTP endpoint still reported
V566. Do not call the Lyrics tab fixed until the user verifies it.

See [setup, security and manual verification](../docs/monkeymote.md).
The Winamp wire format was recovered from the locally installed signed plug-in;
no proprietary DLL is a runtime dependency or included in this release copy.

Manual connection is IPv4 only, one client, opt-in, restricted to the configured
home subnet, with no Bonjour discovery or firewall changes. MonkeyMote transport
is unencrypted even with its legacy password challenge. Do not expose it to the
Internet or untrusted Wi-Fi. Android/password-protected device sessions remain
unverified. Library/search, saved-playlist management, ratings, seek, stop,
shuffle/repeat editing, equalizer, future-track artwork, widgets and timed lyric
highlighting are unsupported. The view is capped at 5,000 entries. Uniform random
mode and later cooldown/file-availability decisions cannot be predicted as a
fixed future sequence.

No literal C:\BAT paths were created, modified, copied, moved, or deleted.
