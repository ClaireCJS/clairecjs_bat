# PAFPlayer V723 — tray-only startup options

Released November 15, 2026.

Tray-only clients accept startup switches for local Floating Lyrics and Album Art, all tray menu boolean settings, topmost state for either or both windows, lyric display over artwork, and whether appearance follows the server. Example:

```powershell
PAFPlayer.py --tray-only music-pc:666 --floating-lyrics --floating-lyrics-always-on-top --album-art --art-lyrics
```

The settings are saved on this computer for that server. Flags pass through detached startup, and the tray menu can change the saved values afterward. Reload now reuses the resolved server address, so both an explicitly named server and a LAN-discovered server continue to work. The remote player’s settings are not changed.

See [Windows tray controls](../docs/windows-tray.md#tray-only-clients-on-other-windows-computers) and the [main manual](../docs/README.md).
