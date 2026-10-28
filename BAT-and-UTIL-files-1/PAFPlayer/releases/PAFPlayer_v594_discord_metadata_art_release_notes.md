# PAFPlayer V594 — Discord profile metadata and public cover art

The Discord activity now reads `👩‍🎤 Artist · 🎤 Song` and `💿 Album (YYYY)`
when those tags exist. Paused playback adds `⏸`. Long values are shortened to
fit Discord's two activity lines while keeping both artist and song recognizable.

PAFPlayer sends a large cover image and album/year hover text when it finds an
explicit public HTTPS cover URL or an exact MusicBrainz release ID whose front
cover is available from the Cover Art Archive. Both Discord Desktop IPC and the
Social SDK helper receive these fields. Public URLs exclude local addresses,
credentials, and query tokens. No local art or media file is uploaded. Songs
with only embedded/folder artwork continue to use Discord's application icon.

The Social SDK helper source accepts the image fields, but cannot be built or
live-tested until Discord enables the SDK and supplies its Windows package.
Desktop IPC behavior is covered by focused tests; final artwork rendering
depends on Discord and the public art source.
