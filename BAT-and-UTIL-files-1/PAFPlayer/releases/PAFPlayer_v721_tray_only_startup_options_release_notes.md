# PAFPlayer V721 — tray-only startup options

Released November 14, 2026.

Tray-only clients now accept explicit startup flags for local presentation and each boolean option in the tray menu and Options window. These flags configure this computer’s saved preferences for the selected PAFPlayer server; they do not change the remote player. They are forwarded through detached startup. Reload uses the saved settings so subsequent menu choices are not reset.

Example: `PAFPlayer.py --tray-only music-pc:666 --floating-lyrics --floating-lyrics-always-on-top --art-lyrics`

The available flags include local Floating Lyrics and Album Art visibility, full-information and lyric tooltips, album-art wallpaper, remote hotkey capture, per-window or combined always-on-top, artwork lyrics (`--art-lyrics`, `--no-art-lyrics`, or `--art-lyrics=server|on|off`), and server appearance inheritance (`--follow-server-appearance` / `--local-appearance`).

See [Windows tray controls](../docs/windows-tray.md#tray-only-clients-on-other-windows-computers) and the [main manual](../docs/README.md).
