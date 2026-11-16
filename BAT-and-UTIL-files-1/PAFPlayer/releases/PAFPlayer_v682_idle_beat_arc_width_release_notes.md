# PAFPlayer V682 — Idle beat-arc width

Released November 12, 2026.

The **Speed bump — beat arc** idle-artwork pattern now uses a compact,
independently configurable horizontal width. Its default total travel is
100 pixels instead of consuming the full monitor-relative wander range.

The **Idle Behavior** tab includes a persistent **Beat arc width** numeric
spinner with native up/down arrows. Accepted values are 10–1000 px in 10 px
steps. Changes apply immediately to the active main artwork and related-art
windows. Monitor-safe movement bounds remain the final clamp, so an arc may be
narrower when its starting position is close to a monitor edge.

Focused verification covers the 100 px path width, numeric web-control schema,
existing boundary reversal, return-to-origin, and the other idle patterns.
