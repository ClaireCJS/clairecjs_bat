# PAFPlayer V768 — event-driven remote lock-screen updates

## What changed

- Removed recurring remote tray status polling. Clients register a callback endpoint with the active master and receive playback-change notifications.
- The master sends each change to one root client. Clients relay the small event through a binary phone tree, so the master does not contact every machine for every song or transport update.
- After an event, each client fetches the complete current-track payload, including the lyric timeline, then advances its lock-screen clock and lyrics locally.
- Track/artist, pause/resume/stop, speed, and seek changes refresh the local timestamp anchor. Callback registrations persist so active clients can be re-anchored after a master restart.
- Corrected seek detection to compare consecutive published playback samples, preventing normal playback progress from triggering repeat notifications.

## Network behavior

There are no per-second or periodic client-to-master status requests. Startup registration and one full payload fetch happen once; playback changes are event driven. The master sends the notification through one client, and each client fetches its own full payload on the event.

## Validation

Source and bundled-module syntax/parity checks are recorded in the handoff. No runtime network test was run from this environment.
