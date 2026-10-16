# PAFPlayer V478 — quiet web visualizer initialization

Fixed a webpage initialization issue that sent artwork bars/blackness
autoslide settings to PAFPlayer every time the page started or stopped. The
webpage now applies those controls locally during initialization without
posting configuration changes.

Artwork colorslide settings are sent only after the user changes the related
controls. The web visualizer’s existing checkbox and double-click toggle are
unchanged.

Validation: Python compilation and focused source checks passed for the
read-only initialization path and user-change send path.

Changed files:

- `../PAFPlayer.py`
- `../docs/web-visualizer.md`
