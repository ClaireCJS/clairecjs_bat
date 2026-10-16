# PAFPlayer V180 — dual lyric destinations + independent lettering profiles

**Build ID:** `2026-08-12-dual-lyric-coloring-controls-v180`

## Changes

- Restores simultaneous GUI lyric display with a three-way artwork-window control: **Over Artwork → Floating → Both**. Both renders the same current cue in both destinations.
- Replaces the old coloring-name control with conditional **🔡** (over-art) and **🔠** (floating) buttons. Each opens the same 15-style configurator for that destination.
- Artwork and floating lyrics now have independently persisted style profiles: **Enabled**, **Default**, **Favorite**, per-style **Palette**, per-style **Speed**, and per-style **Timed emphasis**.
- Removes the old TV/Show selector. The hero preview always demonstrates the currently Enabled style.
- Palette controls are readonly comboboxes; **Up/Down** cycles palettes immediately while focus remains in the dropdown.
- Adds a persistent **0.25×–4.00×** animation-speed slider to every style.
- Adds **Timed emphasis** to every style. Cue progress drives a soft left-to-right MiniLyrics-like sung highlight; explicit cue ends, following cue starts, and untimed-line fallback durations are supported.
- The V180 lyric-mode value uses a new registry key so the old Off/Artwork/Floating setting can be migrated safely. Legacy Off/Artwork migrate to Artwork; legacy Floating migrates to Floating.
- While a lettering configurator is open, expensive external visual animation remains reserved for the configurator, but the latest lyric and emphasis progress continue to be tracked so enabled destinations catch up immediately on close.

## Persistence

Artwork and floating lyrics retain separate registry/settings values for mode, favorites, default, palettes, speeds and timed-emphasis masks under `HKCU\Software\ClaireCJS\play_audio_file`.

## Verification

- Python compilation: passed.
- Embedded regression suite: **406 tests run, 2 skipped, 0 failures**.
- New V180 coverage verifies the three lyric destinations, independent artwork/floating profiles, conditional 🔡/🔠 controls, Enabled/Default/Favorite semantics, keyboard palette cycling, speed sliders, timed-emphasis cue progress, and playback publication of emphasis progress.
- The two skips are the existing Windows-only Winamp messaging checks.

Live Windows/Tk rendering still benefits from the normal smoke check for focus/chrome, simultaneous floating+over-art display, and the feel of the timed emphasis sweep.
