# V446 — Global Config, Developer’s Choice, and the PAFPlayer filename

September 23, 2026. Based on V445.

- The console visualizer interaction message now says `Pause` when playback is
  running and `Unpause` when the pause key/button resumes playback.
- The bottom of the web Choices pane now has a **Global Config** section.
  Named profiles include the complete player-settings snapshot, web UI
  preferences, MatrixMixer configuration, app registry-backed choices, and the
  live web state needed to restore toggles while the current session is open.
- Ordinary profiles persist in the user's local PAFPlayer profile store.
- When `USERNAME=claire` and `COMPUTERNAME` is `demona`, `wyvern`, `thailog`,
  or `goliath`, **Developer’s Choice** can be saved/loaded as the portable
  `PAFPlayer.dcc` sidecar beside the canonical app. Existing sidecars are backed
  up before replacement.
- `PAFPlayer.py` is now the canonical source. `play_audio_file.py` is a
  compatibility launcher that runs the canonical file when present and carries
  a compressed frozen V446 fallback for legacy installations that only have the
  old filename.
- The V429 Windows Terminal regression is now correct for all negative circled
  digits, including `❿`.

Validation:

`py -3 -m unittest -q test_play_audio_file_v446.py test_play_audio_file_v445.py test_play_audio_file_v429.py test_play_audio_file_v416.py`

passed 32 tests with the project’s Windows Terminal test environment enabled.
`PAFPlayer.py` and the compatibility launcher also compile/import successfully.
