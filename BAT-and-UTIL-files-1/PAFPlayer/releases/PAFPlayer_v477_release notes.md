# PAFPlayer V477 — web visualizer toggle interaction

Removed the internal implementation wording `browser-owned raw spectrum` from
the webpage. The toolbar now presents the user-facing label **Live spectrum**.

Double-clicking the web visualizer canvas now toggles the web visualizer on or
off. The existing checkbox remains available and both controls use the same
state and server update path. Turning the visualizer off keeps the web player
controls and configuration usable while hiding the visualizer canvas.

Validation: Python compilation and focused source checks passed for the new
label, removal of the implementation wording, canvas tooltip, and shared
double-click toggle handler.

Changed files:

- `../PAFPlayer.py`
- `../docs/web-visualizer.md`
