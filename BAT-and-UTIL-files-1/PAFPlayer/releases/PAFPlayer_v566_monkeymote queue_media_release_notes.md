# PAFPlayer V566 — MonkeyMote

October 16, 2026.

The real iPad user confirmed upcoming playlist order, track selection, current
artwork preview and repeated-command backlog prevention work. Future-track
Details and Lyrics were still reported broken. V567 follows up on those.

The listener now sends native current-playlist invalidation, follows the active
shuffle queue and explicit requests/history, pins selections to the displayed
path, and checks live membership before queuing Next/Play. Transport commands
wait for acknowledgment; absolute volume remains coalesced. Artwork is cached
and resized on the optional worker. Plain lyric response 36 was implemented but
its iPad display did not work in this version.

63 focused and related tests passed. A 5,000-track cached refresh benchmark ran
100 iterations: median 2.344 ms, maximum 4.901 ms. This measures worker CPU time,
not live audio latency or long-term device performance.

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
