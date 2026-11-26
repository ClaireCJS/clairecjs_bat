# PAFPlayer V759 — preserve the main player's paused state

A simple preview must not start an already paused/stopped main player. Preview-owned pause/restoration now uses transport intents resolved on the audio owner thread against the current pause leases. A queued restore is cancelled when a newer preview takes over; a final guard checks again immediately before committing resume. Explicit user Pause/Stop revokes any preview-owned restoration. Stale Play and automatic external-media resume cannot restart a lease-held player.

Only a player that the preview actually paused can be automatically restored after the last preview releases it. Main-player pause state, stopped state and preview priority remain separate from official instance ownership. Diagnostic events record lease ownership, manual holds, blocked resumes and approved restoration without authentication tokens.

Restart the main player once, and use fresh previews, to load the receiver-side changes. Updating the file alone cannot replace the playback loop in an already running process.

Validation: 29 focused tests passed, covering prepaused players, multiple previews, lease expiry, explicit Pause/Stop, delayed restoration, a new lease between restore selection and commit, late pause acknowledgement, native peer liveness, overlapping startup, disabled-web transport acknowledgement, source/bundle parity and existing simple-mode rendering. Live music was not interrupted during validation.
