# PAFPlayer V604 — single-file project layout

The project root now has one launchable Python file, `PAFPlayer.py`. Its twenty
matching editable feature modules moved to `src/`; the release copy still
bundles them and launches without those source files. The root `PAFPlayer.md`
is now a short overview pointing to the full documentation. The changelog and
TODO live in `docs/`, and the regression runner lives in `tests/`.

Screensaver source and builder moved into `screensaver/src/` and
`screensaver/tools/`; the installed `.scr` and active configuration remain
where the player looks for them. Historical lock-screen build and test staging,
probes, backup sources, and old release scripts moved into
`lockscreen/archive/`. Current lock-screen implementation inputs remain in
place, while tests and asset generation tools have their own subfolders.

The existing portable Developer's Choice profile, playlist, and Last.fm
setup marker remain in the project root because they may be active user data.
This release does not change or migrate their settings. Nothing was permanently
deleted.

The project rules now require a root-layout audit for every release and define
future first-run installation destinations: `C:\BAT\PAFPlayer` when `C:\BAT`
exists, then a versioned folder and timestamped fallback when occupied;
otherwise `%LOCALAPPDATA%\PAFPlayer` with the same collision handling.
Automatic self-installation is not part of V604.

See [distribution and project layout](../docs/distribution-layout.md) and
[the changelog](../docs/PAFPlayer_changelog.md).
