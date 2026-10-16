# PAFPlayer V469

- Reorganized the web control surface: Playlist and Tags appear before Console
  Karaoke; the tabs scroll to their sections; the duplicate Broken Experimental
  area is folded into Experimental; and Discord now follows it as **Experimental
  Discord**.
- Moved Beat visual timing correction into Progress Bar, and Artwork seaming plus
  Adaptive frequency allocation into Console Visualizer. Granularity no longer
  carries an EXP designation.
- Added Discord onboarding: paste a Discord HTTPS webhook URL into the web UI for
  the current run. The UI explains how to copy it from Discord and never writes
  the secret to disk. Persistent setup remains `PAFPLAYER_DISCORD_WEBHOOK`.
- Claire integrations now activate only for user `claire` or the named machines
  DEMONA, WYVERN, GOLIATH, THAILOG, FIRE, HELL, STORM, and MAGIC. Mark learned is
  hidden in the web UI when integrations are unavailable or the track is learned.
- Extended the standard rainbow through a visible magenta segment.
