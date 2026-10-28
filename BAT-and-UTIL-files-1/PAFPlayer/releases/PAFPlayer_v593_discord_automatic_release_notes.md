# PAFPlayer V593 — Automatic Discord connection and conditional help

Released October 21, 2026.

Discord integration now offers three saved connection choices: Automatic,
Discord Desktop only, and Social SDK only. Existing saved choices keep their
meaning. Automatic prefers the local Discord Desktop IPC connection and uses
the authenticated Social SDK helper if Desktop is unavailable. PAFPlayer
periodically retries Desktop and switches back when it returns. The inactive
connection does not publish, so the two paths do not compete on one profile.

Web Config always reports connection status. It shows actionable setup steps
only when Discord integration is enabled and the connection or title-sharing
choice prevents the expected activity. Instructions disappear when the
connection is healthy. Private and stopped tracks still clear activity by
design. Social SDK account authorization can be prepared while Desktop is
active for later fallback.

The SDK helper now reports explicit connection and authorization states. It
clears presence on shutdown only if it published that presence, avoiding a
cross-transport clear when it was used just for account authorization.

The Social SDK has not been enabled or downloaded for this application. Native
compilation, OAuth, and live profile behavior remain unverified. The existing
Desktop IPC route and Python transport logic were covered by focused tests.
See [Discord integration](../docs/discord-integration.md) for setup and
connection behavior. The release includes the
[native helper sources](PAFPlayer_v593_discord_automatic_helper_sources.zip),
but no licensed Discord SDK binary.
