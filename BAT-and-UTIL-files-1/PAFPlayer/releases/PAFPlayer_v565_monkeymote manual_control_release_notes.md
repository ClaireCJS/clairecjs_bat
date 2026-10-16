# PAFPlayer V565 — MonkeyMote

October 16, 2026.

Initial manual Winamp-protocol compatibility, opt-in via --monkeymote-config.
The real iPad connected, displayed track/state and controlled Play/Pause,
Previous/Next and volume. Its report exposed incorrect/stale playlist order,
failed selection and repeated-command backlog. Artwork and lyrics were absent.
This copy preserves that tested development version; use V567 or later.

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
