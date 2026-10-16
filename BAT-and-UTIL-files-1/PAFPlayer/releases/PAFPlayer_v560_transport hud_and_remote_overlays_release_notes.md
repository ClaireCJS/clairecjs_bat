# PAFPlayer V560 — transport HUD and remote overlays

- `Play:` is green while playing, bright yellow while paused, and bright red
  after Stop.
- The first lyric neighborhood is prepared before decoder launch, avoiding
  cold Emojimaxx and Unicode-layout work at the first cue.
- Remote Ctrl+Alt+F toggles floating lyrics on the tray computer.
- Remote Ctrl+Alt+A toggles its local album-art popup.
- Remote overlays use timestamp extrapolation plus a one-second drift-correction
  heartbeat.
- Complete lyric timelines transfer only when their revision changes; artwork
  remains generation-cached.
- The single-file bundler now includes the remote tray, overlay, and machine
  modules so portable builds receive these changes.

See [the V560 implementation note](../docs/remote-overlays-and-lyric-startup-v560.md).
