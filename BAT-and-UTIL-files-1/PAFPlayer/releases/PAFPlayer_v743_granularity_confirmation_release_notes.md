# PAFPlayer V743 — console granularity confirmation

Released November 20, 2026.

Shift+F4 now requests a console granularity change instead of changing it immediately. The prompt names the triggering shortcut or menu sequence, requires Y and then C, expires after 30 seconds, and allows cancellation with N or Escape. Playback and visualizer service continue while the prompt is open. Shift+F4 is no longer polled globally when another application has focus. Console favorite/default restoration, saved granularity defaults, reset, and undo paths also require confirmation when applicable; web settings are unchanged.

Restored the playlist-editor close notice to 30 seconds.

## Checks and limitations

The focused 39-test run passed, covering the confirmation, V742 simple-mode splash, playlist shortcuts, and V646–V650 karaoke/render-stall protections. All 35 embedded modules compiled and matched their source files. Source and release copy are byte-identical.

A read-only 45-second diagnostic of the running V737 instance captured no lyric transitions because playback was paused throughout. The V650 artwork resize tests pass and the optimization remains present, but these checks cannot establish the cause of the reported visualizer hitch or prove it has been fixed. Restart into V743 and capture a sample during affected playback to investigate it further.

No deployment or synchronization to C:\BAT was performed.
