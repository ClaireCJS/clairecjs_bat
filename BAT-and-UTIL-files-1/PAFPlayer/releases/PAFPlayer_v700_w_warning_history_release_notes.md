# PAFPlayer V700 release notes

## Change

- Removed the lowercase `w` keyboard binding for the SIXEL visualizer.
- Kept `Shift+W` as the dedicated warning-history screen shortcut.
- The SIXEL visualizer remains available through its other controls and configuration paths.

## Verification

- The active `PAFPlayer.py` and this release's source snapshot are syntax-checked.
- The embedded V700 HUD warning-history test confirms `Shift+W` opens the warning screen and lowercase `w` is unassigned.

## Scope

This release changes only keyboard discoverability for the SIXEL visualizer and
warning-history screen. It does not remove the SIXEL implementation itself.
