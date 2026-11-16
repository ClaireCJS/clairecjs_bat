# PAFPlayer V718 — tray-only startup options

Released November 14, 2026.

`--tray-only` now accepts explicit positive and negative startup flags for all local tray menu settings: Floating Lyrics, Album Art, sung-lyric tooltip, album-art wallpaper, and hotkey capture. `--art-lyrics=server|on|off` selects inherited or explicit lyrics in the local artwork window.

Example: `PAFPlayer.py --tray-only music-pc:666 --floating-lyrics --album-art --art-lyrics=on`

Options are forwarded through detached startup, saved with per-server preferences on this computer, and remain editable in the tray menu. They do not change settings on the remote player.

See [Windows tray controls](../docs/windows-tray.md#tray-only-clients-on-other-windows-computers) and the [main manual](../docs/README.md).
