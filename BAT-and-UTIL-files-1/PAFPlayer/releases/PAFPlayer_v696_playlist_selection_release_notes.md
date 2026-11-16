# PAFPlayer V696 — Playlist multi-selection

Shift-click selects a range and Ctrl-click toggles individual rows. The editor preserves the selected rows and range anchor across metadata, column, and current-track refreshes. Dragging selected rows moves them together while preserving their relative order; this changes the session order, consistent with the existing single-row drag. Playing, tag editing and removing require a single selected track, and the editor does not silently apply those commands to only one of several selected rows.

Verification covers real Windows Tk modifier clicks, a current-track refresh, selection-anchor preservation, grouped dragging and duplicate-aware selection mapping; the existing playlist, lifecycle and bundle parity tests also run.
