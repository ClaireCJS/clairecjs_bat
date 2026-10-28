# MonkeyMote manual control — V569

The optional Winamp-protocol adapter lets the existing **MonkeyMote Music Remote
HD** iPad app connect manually. No new mobile app, Winamp installation, Bonjour,
or plug-in DLL is needed at runtime. Android uses the vendor's generic
MonkeyMote Music Remote app; Android interoperability remains unverified.
The separate foobar2000 iOS app is not the target protocol.

## Enable and connect

Compatibility is **enabled by default** in V568. The original official player
binds TCP **19371** on the private IPv4 interface used by Windows' default route,
restricted to that interface's actual subnet. If no suitable private interface
can be determined, it binds loopback only; the web tab shows the actual address.
Use this on your trusted home network, not guest/shared Wi-Fi.

The **MonkeyMote** tab near the bottom of the web configuration contains
**Enable MonkeyMote compatibility**, the editable port, listener status, and
connected-client count. Settings can be changed from the player computer.
Unchecking offers **This run only**, **Save for future runs**, or **Cancel**;
saving a disabled choice requires an additional explicit confirmation. Checking
it enables the listener and saves that choice. A port edit offers the same three
choices. Binding succeeds before the old listener is retired; an occupied port
or failed preference save preserves the previous listener and saved values.
Clients must reconnect with their updated port after a successful port change.

`--monkeymote-port=19372` (or `--monkeymote-port 19372`) selects a different TCP
port for the current run; valid ports are 1024–65535. It does not change HTTP 666.
Saved web choices override the legacy JSON's enabled/port values; an explicit
CLI port overrides both for that run. Other existing preference/config IDs stay
unchanged. Preferences use the existing workflow settings file and verified
replacement-backup helper. Session-only choices do not write preferences.

`--monkeymote-config FILE` remains supported for a fixed home IPv4 address,
trusted subnet and optional ASCII password (up to 128 characters). A JSON
`enabled: false` still disables launch unless a later saved web choice enables
it. Omitting the JSON now uses the enabled default, unless disabled in saved
preferences. The host and subnet must be specific and consistent; wildcard and
public binds are rejected. An optional password must match the mobile profile.

For this computer, `monkeymote/home-test.json` explicitly enables
`192.168.0.17:19371` for clients in `192.168.0.0/24`, with no password. It is not
automatically loaded. From PowerShell, after closing the old player:

```powershell
python -B "C:\codex\clairevironment\bat\PAFPlayer\PAFPlayer.py" --monkeymote-config "C:\codex\clairevironment\bat\PAFPlayer\monkeymote\home-test.json" "YOUR MUSIC FILE OR PLAYLIST"
```

Replace the final argument with your existing music file/playlist. A second
ordinary launch forwards music to the existing owner; it cannot turn this
listener on inside an already-running older player. `--instance` and tray-only
processes cannot start this listener. Even later ownership promotion of an
explicit instance does not enable it. Do not add `--instance` to this command.

In MonkeyMote HD add a **manual Winamp** connection, host `192.168.0.17`, port
`19371`, and the matching password. Host/port can differ from the browser remote's
HTTP port (normally 666). Windows Firewall may need a rule restricted to the
chosen subnet and Private profile. This release does not change firewall rules,
router settings, or advertise automatic discovery.

## Feature summary

- **Simultaneous multiple MonkeyMote clients: up to 8 phones/tablets at once**,
  with independent authentication, playlist selection, metadata caches,
  heartbeats and request limits. A stalled client does not block another.
- Current track title, artist, album, genre, elapsed/duration, playing/paused/stopped state.
- Play/resume, pause toggle, previous, next, and absolute volume from 0–100%.
- Current playlist, up to 5,000 entries, using filenames as labels; select then play.
- Volume above PAFPlayer's 100% is displayed as 100%; MonkeyMote cannot select amplification above 100%.
- The list begins with the current song, then explicit play-next requests or
  forward visit history, then the active queue. It refreshes when that sequence
  changes, including completion of the background shuffle. Duplicate slots stay.
- Selecting a row uses the path from the list actually sent to that phone; the
  official session checks current membership and puts it first in play-next,
  then queues Next and Play. Reordering cannot silently select a different song.
- Future-track Details reads only the selected member's existing metadata probe;
  a 16-entry, 30-second cache bounds repeated lookups. Missing tags fall back to
  the filename. No playback command is sent by Details.
- Repeated transport presses are ignored while a prior command awaits execution
  and published playback acknowledgment, with a minimum 350 ms interval. Volume
  continues to use the player's existing latest-value coalescing.
- Current cover preview is a cached JPEG up to 1024 pixels per side, converted
  on the network worker. The original image is unchanged.
- Lyric text uses the current published timeline (up to 256 KiB); V567 sends it
  on connection and track/timeline changes as well as on request. This is plain
  text, not a claim of timed highlighting or karaoke support in MonkeyMote.

The sequence is a view of the active queue, not a change to shuffle semantics.
Uniform random mode chooses at transition time and has no predetermined future
order. Missing files, newly earned recent-play cooldown exclusions, repeat modes,
and subsequent user edits can change what actually plays. The phone updates
when PAFPlayer publishes the resulting queue; it does not scan or pre-decide
future cooldown/file-existence outcomes on the playback thread.

Library browsing, saved-playlist management, ratings, shuffle/repeat changes,
seeking, stop, artwork for noncurrent tracks, equalizer, and widgets are not implemented.
Artist/genre Details arrows now receive a correlated empty list instead of an
unanswered request. This is a timeout fix, not artist/genre library browsing;
real-iPad verification of this empty-result behavior is pending. Other
unsupported requests do not become arbitrary player commands. Empty saved-list
responses are provided when requested; no music library is scanned or exported.
Technical bitrate/sample-rate fields are omitted. Metadata strings are UTF-8,
limited to 255 bytes per field, with embedded NULs removed.

## Ownership, playback isolation, and security

The adapter runs an accept worker and at most eight client workers inside the
official PAFPlayer process. Each client has independent cached views and reuses one shared bounded JPEG
conversion/cache; all clients
share one synchronized transport gate. Pause acknowledgments are retained across
local pause/resume changes between phone polls, preventing a permanently blocked
command gate.
It holds a reference to that exact instance object and identity, rechecking
ownership for incoming messages and status reads. It never acquires a mutex,
launches another player, promotes itself, or discovers a replacement owner.
Basic commands go through `PAFWebServer.enqueue_action`, the same queue used by
the browser/tray controls. Selecting a track uses a narrow membership-checked play-next callback
followed by the same queued Next and Play commands. No socket writes, artwork
conversion, tag scanning, or library work run on the audio thread.

Status reads copy only small published fields; the playlist reader copies
in-memory membership under the playlist lock, formats it outside that lock,
and caches labels for one second. Idle status refresh is
once per second per client. At most eight active mobile connections, 4 KiB
incoming-frame bounds, 30 messages/second per client, short socket timeouts,
and authentication/idle deadlines
bound work. A stalled or disconnected phone does not stop playback.

Only a specific RFC1918 home IPv4 bind address (or loopback) and a
matching allowed subnet are accepted; wildcard/public binds and
allow-all subnets are rejected. A private address alone does not establish
trust: use the subnet of your trusted home devices, not guest Wi-Fi, shared
networks, or an Internet port forward.

**MonkeyMote's transport is not encrypted, even with a password.** Its legacy
authentication is an MD5 challenge response, not TLS or strong modern channel
authentication. Traffic reveals metadata and controls; captured exchanges can
permit offline password guessing. Use a unique password and trusted LAN only.
The config contains that password in plaintext, so keep it private. This
adapter does not expose PAFPlayer's broader browser API to the network.

The [vendor download/security notes](https://www.monkeymote.com/download) describe
the lack of encryption. The [vendor connection guidance](https://www.monkeymote.com/support)
documents TCP 19371/Bonjour, and [manual profiles](https://www.monkeymote.com/using)
support host/port/password. Advertisement alone cannot implement the protocol.

## Evidence and manual verification

The user's real iPad MonkeyMote Music Remote HD connected to a sample-data
protocol probe, displayed the sample track and elapsed time, stayed connected
for over 30 seconds, and displayed both sample playlist tracks. Server traces
recorded real transport/selection requests and heartbeat acknowledgements.
The first probe exposed missing heartbeat/modern-playlist responses; those were
implemented from the installed plug-in's code. Sample elapsed time initially
wobbled; repeated half-second updates were reduced to once per second.

The user then verified actual V565 PAFPlayer playback controls on the iPad.
V566 real-device feedback confirms upcoming playlist order, selecting a track,
current artwork preview, and suppression of repeated-command backlog. V566's
future-track Details and Lyrics tab did not work. The user subsequently
confirmed **both Details and Lyrics work in V567**. In V568 the user confirmed
**two simultaneous real mobile clients connected successfully**, using the
legacy `--monkeymote-config` option, and subsequently confirmed the Lyrics pane
works. The second device platform was not specified. Live web settings pass
emulated-client/HTTP/UI tests; physical port-change verification remains pending.
V569 fixes an independent tray popup API collision; MonkeyMote protocol code
is unchanged from V568.
Android, password-protected real-device sessions, timed highlighting, and
long-duration use remain unverified.

For focused troubleshooting, the active official player exposes read-only
`http://127.0.0.1:666/api/monkeymote/diagnostics`. This endpoint is loopback-only.
It returns at most 128 in-memory events (message/request numbers, command result,
media byte counts); it records no song text, passwords, challenges, or filenames.
Heartbeat receive noise is omitted. It does not write a trace file or accept
commands. The endpoint is unavailable when MonkeyMote is disabled.

1. Launch the new official player using the command above. Confirm the startup
   message reports the MonkeyMote host/port. Keep the old sample probe stopped.
2. Connect manually on the iPad. Compare title, artist, elapsed/duration and
   upcoming playlist with actual Next transitions. Observe the counter for at least 30 seconds.
3. Pause and resume, listening to actual audio. Try Next, Previous and volume.
   Select a playlist entry and check the song that actually plays. Tap Next
   repeatedly during a transition and confirm it does not build a skip backlog.
4. Change tracks locally and edit queue order; verify the phone refreshes. Open
   current cover preview, future-track Details, and the Lyrics tab on a song
   with lyrics. Disconnect/reconnect and verify no repeated commands.
5. Close the owner. The listener should disappear. An explicit `--instance`
   must not inherit it, even if it later becomes the owner. Relaunch without a
   JSON: compatibility defaults on unless a saved disabled choice exists.
6. Connect a second device while the first stays connected. Control from each,
   leave both open for several minutes, and check that a playlist selection on
   one device cannot replace the other device's selection. Disconnect one; the
   other must keep working. Repeated Next must not build a shared backlog.
7. In the web MonkeyMote tab, change to a free port with **This run only**;
   reconnect both devices using that port. Try an occupied port: the previous
   listener must keep working. Save a port choice, restart and verify it persists.
   Try Cancel, session-only disable, cancelled permanent disable, and confirmed
   permanent disable; restart to verify the saved choice, then re-enable.
8. Try a wrong password and a client outside the allowed subnet; neither may
   control playback. Repeat with Android before claiming Android compatibility.

Run `python -B -X utf8 monkeymote/research/verify.py` for isolated focused and
related tests. Reports go directly under `tests/reports`; fixtures are retained
under `tests/runs`. These tests include an emulated TCP client and are distinct
from real-device evidence. Research probe scripts are test tools, not startup
components. No proprietary DLL is required or bundled in the release copy.

Windows interface lookup uses [GetIpAddrTable / MIB_IPADDRROW](https://learn.microsoft.com/en-us/windows/win32/api/ipmib/ns-ipmib-mib_ipaddrrow_xp)
to read the actual interface mask; it sends no discovery datagrams. Bonjour and
other automatic discovery remain unimplemented. Default-route private IP
selection does not certify network trust; use the explicit configuration when
VPNs, multiple LANs, or different trusted ranges are involved.
