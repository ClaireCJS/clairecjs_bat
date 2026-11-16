# PAFPlayer V665 — DJ sleep schedule

DJ settings include an hourly sleep time, sunrise or hourly wake time, default US ZIP 22312, and a sleep-on-screen-lock checkbox mirrored in Windows Lock Screen settings. Sleep blocks new/forced jobs and prepared interruptions; active commentary stops and DJ-owned music pauses resume. Custom ZIP lookups run in the background and are cached; unavailable sunrise uses a visible 7am fallback. Times use the player’s local time zone.

The two free hosted DJ providers and the previous OpenAI credit warning remain available. The default sleep setting is never and the default sleep-on-lock setting is off.

Verification: 58 focused tests passed, including seven sleep tests; all 28 bundled modules compiled and matched editable sources, and the release matched the active player. Browser checks passed for sleep controls, synchronized lock settings, and the OpenAI credit warning. [Test report](../tests/reports/v665-dj-sleep-checks-20261112.json).
