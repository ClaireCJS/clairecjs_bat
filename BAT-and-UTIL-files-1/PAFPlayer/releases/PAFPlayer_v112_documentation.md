# PAFPlayer V112 — user-owned artwork geometry and optional HUD details

**Build ID:** `2026-08-09-user-owned-art-geometry-and-hud-details-v112`

## Behavior changes

- The artwork popup's current position is captured before idle initialization or drift. Once the user moves it, art refreshes, foreground raises, idle transitions, hide/show cycles, later tracks, and later sessions preserve that location.
- Artwork resizing is free-form by default. Holding Ctrl while resizing enforces a 1:1 square; releasing Ctrl restores free-form resizing.
- New or rotated artwork never takes ownership of popup size. Complete images are contained in the existing drawable rectangle with black letterboxing and no cropping.
- Effective display tags merge the exact pair `instrumental` plus `instrumentals` into `instrumental(s)`. The synthesized tag is rendered 25% brighter, while source attribute files remain unchanged.
- Compact `?`/F1 Help now places `Tags:` directly below `Last play:` and then draws a divider before ReplayGain, playlist context, and controls.
- `Ctrl+Alt+/` persistently toggles three main-HUD rows—ReplayGain, playlist, and effective tags. The visualizer gives up exactly those rows while enabled and regains them when disabled.

## Compatibility notes

- The saved artwork geometry format remains compatible with prior releases. The historical manual-size marker may remain in existing settings but no longer gives source pixels control of window dimensions.
- Ctrl+Alt+/ is focus-only, matching ordinary console controls; the existing Ctrl+Alt+Up/Down volume hotkeys remain global.
- The incomplete note “The lyrics over artwork” supplied with the change request did not specify a new lyric behavior, so the existing three-way lyrics modes and over-art rendering are preserved unchanged.

## Verification

The embedded suite now contains 360 tests, including V112 contracts for release identity, effective-tag merging, persisted HUD-detail state, user-owned artwork geometry, and non-cropping letterboxing. Release gates also compile both script names, parse the embedded browser JavaScript, validate all manual image links, enforce the manual/changelog structure, verify byte identity and SHA-256 manifests, test ZIP integrity, and compile the scripts again after archive extraction.
