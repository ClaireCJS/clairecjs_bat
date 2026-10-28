# V580 remote artwork and tray verification

Use the V580 single-file player on both computers. This keeps the remote renderer
and the server's appearance export at the same version. The server remains the
official playback owner; `--instance` must not be used for this test.

1. Play a song with artwork and timed lyrics on the server using `--no-tray` if
   testing on the same Windows computer. Use the existing `--web-port=PORT` if
   changing port 666; `--web-host=127.0.0.1` limits a local test to loopback.
2. Start `python PAFPlayer.py --tray-only HOST:PORT` on the listener. The shell
   should return while the icon remains. Open **Options…** from its context menu.
3. Enable artwork and Floating Lyrics. Enable **Follow the server's artwork
   and lyric appearance**. Both windows should stay visible and show timed
   lyrics with the server's coloring/treatment. Change a server appearance
   setting and verify the remote copy follows within about two seconds.
4. Change **Lyrics over album artwork** to Off, then On, then Use server setting.
   The artwork and floating window should remain available independently.
5. Open each native appearance editor. Local edits should clear Follow and be
   retained across reconnect/restart. Center each window using Options.
6. Close/reopen Options while lyrics animate. Hide/re-enable artwork, pause and
   resume, and change songs. No strobe, accumulated intro timers, stale art, or
   Tk shutdown errors should appear. Existing Save current music file remains.
7. Exit the tray and verify no later console output, overlay windows, or running
   client remains. A second launch should work. `--foreground` is available when
   collecting diagnostics; logs otherwise stay under the per-user RemoteTray folder.

Automated checks use an isolated silent WAV, timed lyric sidecar and generated
cover with two real Python processes. Tk event samples verify visibility,
inherited modes and lyric contents; they are not screenshots or proof of
physical remote-machine rendering. Native Options is opened and closed and
local lyric overrides are exercised. The detached-launch probe measures parent
return before an actual native tray child exits. No live household queue is used.

See [Steam checks](steam.md#manual-verification) for game-driven load reduction.
