# PAFPlayer V744 — responsive remote lock screen

Released November 20, 2026.

## Fixed

- The lock-screen status on a tray-only computer no longer drives a complete Windows tile-and-badge publication for every one-second counter tick.
- The decorative elapsed-time counter now advances in five-second steps, cutting redundant notification traffic by about 80 percent during ordinary playback.
- Lyric selection is not quantized: it still uses the full-resolution synchronized playback timestamp, cached lyric timeline, playback speed, karaoke offset, and the existing 250 ms lock-screen lead.
- The same pacing applies to a lock screen published by the main player and to a remote tray lock screen such as Thailog.

## Deployment

Restart or use **Reload tray** on the tray-only computer after updating its single-file `PAFPlayer.py`. The installed V530 Windows companion does not need to be reinstalled and no new certificate/UAC prompt is required.

## Verification

Focused tests cover five-second boundary behavior, remote clock extrapolation, full-resolution lyric selection, pause/seek behavior, and single-file bundled-source parity.

This release removes the identified notification flood. Windows still owns final lock-screen rendering and may impose a smaller platform-dependent display delay.
