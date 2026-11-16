# PAFPlayer V666 — Force DJ through sleep

`#djforce` overrides scheduled and lock-screen sleep through generation and playback. Automatic commentary still sleeps. New default casts contain one woman and one man; existing saved selections are preserved. For the default cast, Piper automatically downloads a second voice when needed; if unavailable, it uses the first voice and reports a warning. Explicitly configured voice models remain unchanged.

Verification: 65 focused tests passed, including forced generation and playback during sleep and mocked Piper voice download/selection. Twenty-eight bundled modules compiled and matched editable sources; the release matches the active player. Browser sleep controls and warning checks passed. Live download of the second voice was not tested. [Test report](../tests/reports/v666-dj-force-checks-20261112.json).
