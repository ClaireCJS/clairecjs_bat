# PAFPlayer V592 — Discord Social SDK connection

Released October 21, 2026.

Web Config → Discord integration can now select the original local Discord
Desktop IPC connection or an authenticated Discord Social SDK connection.
Older saved settings continue to use Desktop IPC. Social SDK mode does not
silently fall back to IPC when its helper is unavailable.

The Social SDK helper is a separate Windows C++ process. It uses Discord's
OAuth authorization, refreshes credentials, stores access and refresh tokens
in Windows Credential Manager, and publishes Rich Presence through the SDK's
connected client. Discord Desktop does not need to run for this route. The
existing private-track, stopped-playback, and explicit local-title-sharing
rules still control what is published. The web status indicates missing SDK
files and connection results. Normal shutdown clears activity and stops the
helper. The single-file bundle now includes the current web Save handler so
the entered Application ID is actually sent.

**External prerequisite:** Discord Social SDK has not yet been enabled for
this PAFPlayer application. Its official Windows C++ headers, import library,
and DLL were unavailable during this release. The helper source and build
configuration are provided, but it could not be built or tested against a
real Discord account. The Developer Portal process may require Discord to
accept PAFPlayer as an eligible application. See
[`docs/discord-integration.md`](../docs/discord-integration.md) and
[`discord_social/README.md`](../discord_social/README.md).
The release also includes
[`PAFPlayer_v592_discord_social_sdk_helper_sources.zip`](PAFPlayer_v592_discord_social_sdk_helper_sources.zip)
with the C++ helper source and build instructions. Licensed SDK files are not
included.

Validation: focused Python transport tests, source/bundle parity, Python AST
parsing, and web JavaScript syntax checks passed. Native compilation, OAuth,
token refresh, and live profile updates remain unverified until the official
SDK download is available.
