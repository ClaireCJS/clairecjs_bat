# PAFPlayer V442 — Scheduled console-overlay painting

- Fixes the console visualizer feedback popup being repainted on every spectrum tick.
- Replaces per-character dither fade with complete three-row fade states, removing scattered white glyphs over artwork and bars.
- Popup work now runs only for its initial state, each of 16 fade states, and removal; spectrum rendering is no longer tied to popup repaint frequency.
