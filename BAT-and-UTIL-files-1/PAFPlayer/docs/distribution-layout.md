# Distribution and project layout

The launchable Windows player is `PAFPlayer.py`. Its feature modules are bundled
into that file, so a release copy does not need the editable `src/*.py` files.
Those sources stay in `src/` for development and are synchronized with
`tests/sync_embedded_modules.py`. Run the regression runner from
`tests/run_PAFPlayer_tests.py`.

The project root keeps `PAFPlayer.py`, the short `PAFPlayer.md` pointer, and
project instructions. Existing live data sidecars remain beside the player:
`PAFPlayer.dcc` is the portable Developer's Choice profile,
`changerrecent.m3u` may be an active playlist, and the Last.fm setup marker
controls whether the setup prompt repeats. Relocating any of these requires a
separate migration of the saved paths and behavior; this cleanup does not reset
them. Historical backups are in `backups/`, release copies in `releases/`,
and full documentation in `docs/`.

The screensaver's installed `PAFPlayer.scr` and its active configuration stay
at `screensaver/`; editable source is in `screensaver/src/` and its builder is
in `screensaver/tools/`. The lock-screen project keeps its build inputs at
`lockscreen/`, while current tests and asset tooling are in subfolders and
historical staging, probes, and release tools are under `lockscreen/archive/`.

## First-run self-install location (V606)

On Windows, running a loose `PAFPlayer.py` stages and verifies a separate
installed copy before launching it. `python PAFPlayer.py --install` requests
that installation explicitly. A development checkout and a copy with an
installation marker run in place. The installer uses `C:\BAT\PAFPlayer` if
`C:\BAT` exists. If that folder already exists, it uses
`C:\BAT\PAFPlayer_v{version}`. If that also exists, it uses
`C:\BAT\PAFPlayer_v{version}_YYYYMMDDHHMMSS`; preserve any further collision
with the project's ` (1)`, ` (2)` naming rule. On a machine without `C:\BAT`,
use the same sequence under `%LOCALAPPDATA%`.

The installer leaves the source and every existing destination unchanged. It
copies the single-file player into a staging directory, checks its SHA-256 and
syntax, writes a short sidecar guide and install marker, then publishes the
new folder. It checks playback prerequisites before launching the installed
copy. Failed required checks stop launch and leave the verified copy available
for repair. No playlist, saved configuration, or active profile is migrated or
rewritten. Automatic setup covers the application folder structure; Python,
FFmpeg, required packages, and optional lock-screen/screensaver integrations
may still need separate setup. This remains Python source, not a standalone
executable.

Run `python PAFPlayer.py --readiness-check` from any copy to print every
read-only prerequisite check, including optional warnings and the installed
copy integrity marker. The bundle check inspects the file being checked, so a
syntactically valid Python file without PAFPlayer's bundled modules fails.
Player readiness requires both `ffmpeg` and `ffplay`; playback starts through
`ffplay`. Use `--readiness-check --tray-only` for a remote tray client; it does
not require local audio output, FFmpeg, Pillow, or Recycle Bin support. The
last two may still improve optional tag-viewer artwork and cleanup behavior.
The misspelled
`--readyness-check` works as an alias and prints the correct spelling.
