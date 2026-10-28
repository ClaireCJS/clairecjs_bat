# PAFPlayer V616 installed guide

Run `python PAFPlayer.py --readiness-check` to see every prerequisite. For a tray-only computer, add `--tray-only` to that check.

Run `python PAFPlayer.py --help` for all playback options and controls. Use `python PAFPlayer.py --tray-only HOST:PORT` for a remote household tray.

Web Configuration is available at the address printed when the player starts. The single-file player bundles its feature modules; FFmpeg, Python packages, and optional Windows integrations are checked separately.

Your playlists and saved settings are not copied or replaced by first-run setup. An existing PAFPlayer folder is preserved; each new installation gets its own folder.
