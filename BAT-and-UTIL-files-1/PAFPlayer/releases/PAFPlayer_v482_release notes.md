# PAFPlayer V482

Based on V481; retains bass-while-locked and floating-title-duration changes.

- Fixed-row console painting explicitly reasserts no-wrap after visualizer
  transports restore wrapping. Normal teardown restores wrapping.
- Skip undecodable artwork variants when Pillow is available. The reported
  Dethklok TV edit now uses its healthy sidecar instead of repeatedly trying its
  damaged embedded APIC. Audio files and metadata are unchanged.
- Windows media integration can optionally append the current timed lyric to
  the title. Added its checkbox under Windows / Lock Screen · Experimental.
- Lyric changes reuse unchanged artwork thumbnails. Missing-dependency messages
  point to installation documentation.
- Artist, title, lyric and artwork were successfully read back from an actual
  temporary Windows SMTC session. Lock-screen visibility remains Windows-owned
  and still needs user visual verification after restart.

The single-file numbered snapshot is
`PAFPlayer_v482_fixed_rows_and_windows_lyrics.py` in this directory.

Validation: eight focused tests pass, including a 240-frame private-console
replay using the exact track's lyrics. The original song-specific runaway
scrolling was not fully reproduced; do not interpret this defensive repair as
a conclusive end-to-end fix. See `docs/console-rendering-v482.md` for evidence
and remaining verification, and `docs/windows-lock-screen.md` for setup.
