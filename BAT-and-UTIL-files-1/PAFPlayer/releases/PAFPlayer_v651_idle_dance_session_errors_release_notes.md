# PAFPlayer V651 release notes

V651 adds two persistent controls to Web Config's Experimental section:

- **Idle artwork dance timeout**: 0–3600 seconds; 0 disables automatic dance.
- **Window-dance range**: 0–50% of the owning monitor; 0 holds the window still.

Both settings affect the current artwork window immediately and are used for
the main artwork and related-art gallery collision footprints. Existing
monitor-edge guards remain in force.

Missing, empty, and unreadable playback entries accepted by the existing
deduplicated `ErrorAlerts` path are now also retained in a 250-entry,
session-only memory ledger. A **⚠** badge appears beside the web song title
when the ledger is nonempty. Its **Click for errors** tooltip opens `/errors`,
which lists newest errors first and refreshes once per second. Restarting the
player clears the list; no new error-history file is written.

Verification:

- `python tests\test_v651_idle_dance_session_errors.py -v` — 4 passed.
- Existing V86 idle-art default and monitor-safety tests — 2 passed.
- Python source syntax compilation — passed.
- Editable-module/single-file bundle parity — passed.
