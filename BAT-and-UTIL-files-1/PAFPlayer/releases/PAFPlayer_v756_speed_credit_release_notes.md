# PAFPlayer V756 — clear speed confirmation and minor credit warnings

The X menu distinguishes the active Playing speed from the typed Pending value until Enter. Applying a custom multiplier clears the stale menu in both normal and simple mode; simple mode repaints only its reserved rows without a full-screen clear. Exact custom speed continues through decoder restarts and across tracks.

Historical OpenAI credit exhaustion remains in Web Warnings and DJ diagnostic logs. The HUD/help list escalates it only when DJs are enabled, OpenAI participates in the configured text/speech chain, and the latest generation has failed without a ready fallback. Severity checks use local job state and perform no network requests or key-file reads.

Validation covers 1.333 reaching the decoder, menu dismissal without clearing the screen, warning severity combinations, Web Warnings retention, nonblocking warnings, and existing simple-mode, interrupt, speed and preview-focus regressions. No live provider calls or user playback interruption were needed.
