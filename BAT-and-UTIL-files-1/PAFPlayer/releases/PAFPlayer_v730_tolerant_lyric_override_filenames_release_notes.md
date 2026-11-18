# PAFPlayer V730 — tolerant lyric override filenames

- `--use_lrc`, `--use_srt`, and `--use_txt` now accept any filename.
- A final `.maybe` is stripped before attempting to read the file.
- The declared option selects parsing, independent of the remaining filename.
- Missing or unverifiable files produce a press-any-key warning, then playback
  continues and attempts the requested first-track preview.
