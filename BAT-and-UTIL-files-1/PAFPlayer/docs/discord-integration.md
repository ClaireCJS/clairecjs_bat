# Discord integration

PAFPlayer can publish the current song on your personal Discord profile. It
does not post to a server channel. The integration remains opt-in, and local
titles, artists, albums, and lyrics are sent only when you enable that separate
checkbox.
Private tracks, stopped playback, and disabled sharing clear the activity.
File paths, local playback URLs, and OAuth tokens are never included in the
activity.

The first activity line is `🎵 Song · 👩‍🎤 Artist · 💿 Album (YYYY)` when all
tags are available. Missing fields are omitted. The second line is the lyric
currently displayed by PAFPlayer, `🎤 Lyric`, or exactly `🎤 ♪` when there is
no lyric. With a positive Discord lag adjustment, this line previews the lyric
that PAFPlayer will display after that many seconds. Pausing retains the
current track and lyric; stopping clears the
activity. Animation progress does not trigger another Discord update: the
lyric line changes when its selected text changes. Long metadata and lyrics
are shortened to fit Discord's two 128-character lines. Discord controls the
separate application name, which remains `PAFPlayer`.

V610 verifies this layout against both Discord publication paths, including
the no-lyric fallback, track changes, paused and stopped playback, privacy
clearing, truncation, and lyric-change-only updates. This is a local payload
and transport test; the Social SDK still needs its official download and a
real-account connection before that path can be called live-verified.

## Correct delayed lyric updates

Web Config → **Discord integration** has a **Discord lag** slider and editable
seconds field to its right. The setting ranges from 0 to 5 seconds and defaults
to 0. If Discord shows lyrics about 1.5 seconds late, enter **1.5** and save.
PAFPlayer uses the timed lyric timeline and the current playback speed to
submit each new lyric that much earlier. The official player refreshes Discord
on a 200 ms cadence, including when no browser is open. It sends a compact
lyric clock in that case, without building the whole browser status payload.
Only changed lyric text produces a new activity update; a quiet gap shows
`🎤 ♪`. Paused playback does not preview future lyrics. The lag value is saved
with the existing Discord integration settings and applies to both Desktop IPC
and Social SDK publication.

This adjustment compensates for observed display delay; Discord controls when
the updated activity actually appears and may vary between devices or
connections. Lyrics without a usable timeline continue using the currently
displayed line.

Discord can show cover art when the audio file has an exact MusicBrainz release
ID with a front cover in the public Cover Art Archive, or an explicit public
HTTPS cover-art URL tag. PAFPlayer sends that public image address as Discord's
large image and the album/year as its hover text. A local embedded image or
folder cover alone cannot be fetched by Discord and is not uploaded or exposed
through the household web server. An absent or unavailable public cover leaves
Discord's normal application icon. Cover availability depends on the public
source and Discord's image fetching; it can differ from PAFPlayer's local art.

## Choose a connection

- **Automatic: Discord Desktop, then Social SDK** tries the local Desktop
  connection first. If Desktop is unavailable, the Social SDK helper takes over
  when installed and authorized. PAFPlayer checks for Desktop again periodically
  and switches back when it returns. Only one connection publishes activity at
  a time; this avoids competing updates to the same Discord profile. You can
  authorize the SDK while Desktop is running so it is ready for later fallback.
- **Discord Desktop on this computer** uses the existing local named-pipe
  Rich Presence connection. Discord Desktop must run beside PAFPlayer. Saved
  installations without a connection choice continue using this method.
- **Discord Social SDK** uses an authorized Discord account and a persistent
  SDK connection. Discord Desktop does not need to run. PAFPlayer must have
  Internet access, the official Windows Social SDK helper must be installed,
  and you must connect your account in the web configuration once.

All three choices remain available. Automatic mode makes both paths usable
without sending duplicate updates. Existing Desktop-only and SDK-only choices
are preserved. The Web Config status always reports the current connection,
but setup instructions appear only while Discord integration is enabled and
the selected connection is not working. They disappear after a connection is
healthy. A stopped or private track intentionally clears its activity and does
not by itself count as a connection failure.

The Application ID identifies your Developer Portal application. It does not
authenticate your personal account. The Social SDK connection uses Discord's
OAuth authorization with the `openid` and `sdk.social_layer_presence` scopes.
PAFPlayer keeps its access and refresh tokens in Windows Credential Manager
under `PAFPlayer/DiscordSocial/<Application ID>`, separate from JSON settings,
logs, release copies, and the web page. **Forget local Discord authorization**
removes that stored credential and disconnects the helper. Disabling profile
activity clears the presence and stops the helper, while retaining the
credential so you can enable it again without repeating OAuth.

## Set up the Social SDK route

1. In the [Discord Developer Portal](https://discord.com/developers/applications),
   select the application whose ID you entered in PAFPlayer. Discord's guide
   requires a Developer Team, `http://127.0.0.1/callback` as a desktop OAuth2
   redirect, and **Public Client** for this local OAuth flow.
2. Open **Discord Social SDK → Getting Started** for that application and
   submit accurate details about PAFPlayer as a music player. Discord controls
   whether the Social SDK is enabled and offers the C++ download. Do not
   describe PAFPlayer as a game if the form requires a game.
3. Download the official Windows C++ SDK from **Discord Social SDK → Downloads**.
   Follow [the helper build instructions](../discord_social/README.md) to put
   `PAFPlayerDiscordSocial.exe` and `discord_partner_sdk.dll` in
   `PAFPlayer/discord_social`.
4. In Web Config → **Discord integration**, choose **Automatic** or
   **Discord Social SDK only**,
   enter the Application ID, set your title-sharing preference, check
   **Display the current song**, and **Save Discord profile choice**.
5. Click **Connect Discord account**. Discord opens an authorization flow in
   a browser. Approve it for the account whose profile should show playback.
   The status field reports connection and publication results.

If the helper is missing, PAFPlayer says so when the SDK path is needed and
keeps playback working. SDK-only mode does not silently fall back to Desktop
IPC. Automatic mode uses Desktop while it is available and reports both
setup options when neither path can work; it never publishes via a webhook. The
Social SDK route cannot be live-verified until Discord enables the SDK for the
application and its official Windows download is built locally.

Discord's current [Social SDK setup guide](https://docs.discord.com/developers/discord-social-sdk/getting-started/using-c%2B%2B)
and [Rich Presence guide](https://docs.discord.com/developers/discord-social-sdk/development-guides/setting-rich-presence)
describe the authenticated connection and update calls. The Social SDK is
presented primarily for games; availability for PAFPlayer depends on Discord's
Developer Portal process.
