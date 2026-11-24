# PAFPlayer V745 — local lock-screen clocks

V744 explicitly reduced the playback counter to five-second steps. V745 restores one-second ticks on the host and remote trays. Host status now extrapolates its cached audio timestamp before selecting lyrics, so the Windows companion does not depend on a newly published render frame for each tick.

Remote lock-screen selection uses the already-cached timestamped lyric timeline with a bounded 30-second extrapolation window, replacing the shared artwork clock's four-second cap for this consumer. Paused and stopped clocks do not advance; duration clamps the position. A detected disconnect or changed official owner rejects the cached session. The bridge makes no master-server calls per cue or tick. Background transport heartbeats remain necessary to learn about seeks, pauses, and track changes.

Restart the host player and reload the updated tray-only file on THAILOG. The signed V530 companion package remains unchanged. This fixes Python status timing; Windows tile rendering latency still needs observation on the actual locked client.

Focused checks exercise the real host HTTP endpoint, one-second boundaries, cached host and remote clock advancement, pause, owner/disconnect rejection, and source/bundle parity. No audio playback, Windows locking, package installation, or deployment to C:\BAT was performed.
