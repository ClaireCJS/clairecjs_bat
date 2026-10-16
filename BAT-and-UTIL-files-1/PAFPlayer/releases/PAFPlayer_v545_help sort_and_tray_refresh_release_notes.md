# PAFPlayer V545 — help sort and tray refresh

- Key-ordered console help now guarantees A–Z, then F1–F10, then other keys.
- Tray selections are held as pending until the live tray thread applies them.
- Web Config waits for that application acknowledgement before returning.
- If Explorer rejects `NIM_MODIFY`, PAFPlayer re-adds the icon so the chosen
  picture becomes visible without restarting the player.
