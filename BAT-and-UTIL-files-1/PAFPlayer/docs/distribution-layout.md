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

## Private Python runtime and first-run install location (V728)

On Windows, running a loose `PAFPlayer.py` stages and verifies a separate
installed copy before launching it. `python PAFPlayer.py --install` requests
that installation explicitly. A development checkout and a copy with an
installation marker run in place. The installer uses `C:\util\PAFPlayer` if
`C:\util` exists. If that folder already exists, it uses
`C:\util\PAFPlayer_v{version}`. If that also exists, it uses
`C:\util\PAFPlayer_v{version}_YYYYMMDDHHMMSS`; preserve any further collision
with the project's ` (1)`, ` (2)` naming rule. On a machine without `C:\util`,
use the same sequence under `%LOCALAPPDATA%`.

The installer leaves the source and every existing destination unchanged. It
copies the single-file player, launcher, pinned package manifest, and any
prebuilt `runtime/` folder into a staging directory, verifies the player
SHA-256 and syntax, writes a sidecar guide and install marker, then publishes
the new folder. `pafplayer.bat` selects `runtime/python.exe` when available.
Without it, the launcher falls back to the registered Python 3 launcher. Failed
required checks stop launch and leave the verified copy available for repair.
No playlist, saved configuration, or active profile is migrated or rewritten.

Build the private runtime on 64-bit Windows with
`python -B tools/build_private_runtime.py`. The builder downloads the official
Python 3.12.10 distribution with Tcl/Tk support, installs the exact versions listed in
`requirements-core.txt` into `runtime/Lib/site-packages`, checks their imports,
and records the installer hash. It refuses to replace an existing runtime. It
requires internet access unless `--python-installer` points to an already
downloaded official Python installer. Build the runtime before running
the self-installer to include it in the installed copy. This keeps core
PAFPlayer packages independent of packages installed in a user's personal
Python. Qwen/Piper model runtimes and weights remain optional components.

Run `pafplayer.bat --readiness-check` to select the private runtime, or run
`python PAFPlayer.py --readiness-check` from any copy to print every
read-only prerequisite check, including optional warnings and the installed
copy integrity marker. The bundle check inspects the file being checked, so a
syntactically valid Python file without PAFPlayer's bundled modules fails.
Player readiness requires both `ffmpeg` and `ffplay`; playback starts through
`ffplay`. Use `--readiness-check --tray-only` for a remote tray client; it does
not require local audio output, FFmpeg, Pillow, or Recycle Bin support. The
last two may still improve optional tag-viewer artwork and cleanup behavior.
The misspelled
`--readyness-check` works as an alias and prints the correct spelling.
