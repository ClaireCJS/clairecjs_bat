# PAFPlayer V710 — AI DJ wake/sleep and karaoke expansion

Released November 13, 2026.

## Changes

- Add **Wake now** and **Sleep now** beside **Talk Now!** in AI DJ configuration.
- Add `#djwake`/`#wakedj` and `#djsleep`/`#sleepdj`/`#sleeping`/`#bed`/`#bedtime`/`#sleepy`/`#sleep`.
- Keep manual wake/sleep as a session override, leaving saved sleep hours intact.
- Cancel pending or current DJ commentary when manual sleep begins.
- Let auto-expanded Web Karaoke claim the full grid row after configuration is hidden, then restore its saved height when configuration returns.

## Verification

Focused controller, command-routing, HTML, browser-layout, embedded-source,
syntax, and release-identity checks are recorded in the V710 test run.

## Limitations

Manual wake/sleep resets when PAFPlayer restarts. This is deliberate: the
persistent sleep schedule remains the source of truth for later sessions.
