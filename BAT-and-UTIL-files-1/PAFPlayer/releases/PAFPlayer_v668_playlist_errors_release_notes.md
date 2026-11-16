# PAFPlayer V668 — Playlist Errors tab

Missing playlist entries are recorded silently, including missing entries encountered while searching for a playable successor. The web configuration includes an Errors tab with the existing current-session list, and the error badge opens it. Other playback errors retain their configured alerts.

Verification: missing-entry tests and existing error reliability tests passed. Browser checks verified that Errors displays the session list and Warnings remains last. Nine JavaScript blocks and 28 bundled modules passed checks; the release matches the active player. [Test report](../tests/reports/v668-playlist-errors-checks-20261112.json).
