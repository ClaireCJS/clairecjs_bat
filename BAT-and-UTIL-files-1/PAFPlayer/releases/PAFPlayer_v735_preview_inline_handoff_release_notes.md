# PAFPlayer V735 — preview inline handoff

PAFPlayer now recognizes `PAFPLAYER_SIMPLE=1` as a launcher-safe equivalent of
`--simple`. This prevents batch-variable expansion from accidentally starting
the full visualizer/title UI during audio previews.
