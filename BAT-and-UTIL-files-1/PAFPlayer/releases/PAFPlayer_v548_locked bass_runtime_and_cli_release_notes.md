# PAFPlayer V548 — locked-bass runtime and CLI

- The default buffered WaveOut decoder now applies locked-screen bass reduction
  before speaker/channel expansion.
- Added session-only `--bass-reduction-while-locked` and
  `--no-bass-reduction-while-locked` switches.
- Added `--locked-bass-reduction-percent=0..100`.
- CLI overrides take precedence for the current process without overwriting the
  saved Web Config preference.
