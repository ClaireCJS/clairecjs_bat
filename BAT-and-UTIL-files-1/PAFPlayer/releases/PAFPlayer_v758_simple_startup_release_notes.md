# PAFPlayer V758 — recover simple-preview startup

Observed logs showed recent V757 simple launches taking approximately 31–33 seconds to start the decoder. The preview registry contained 18 entries, with only the main process still alive at inspection. Requests to exited peers were adding serial refused-connection delays. No fatal exception was present for these launches in the inspected error log.

The coordinator now verifies process liveness before connecting and archives exited registrations, preserving collisions and avoiding permanent deletion. It traces focus discovery, skipped dead peers, pause requests, acknowledgements and readiness without logging authentication tokens. Only contacted peers receive heartbeat/release requests.

Overlapping preview startups give priority to the newest preview. An older preview can acknowledge being silent before it has a decoder, then wait for the newer preview without both startup threads waiting for queued pause actions. A new simple preview starts unpaused and preserves the main player's saved pause preference.

Tests cover dead registration batches with zero connection attempts, native process liveness, overlapping startups, original pause restoration, disabled-web transport acknowledgement, preview startup/persistence state, archive collisions, diagnostic redaction and existing simple-mode/interrupt regressions. Live music was not interrupted for testing. Existing main-player endpoints remain compatible; restart a failing preview using the updated active file.
