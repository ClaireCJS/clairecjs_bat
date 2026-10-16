# PAFPlayer V538 — timestamped progress beats

Released October 13, 2026.

- **Beat visual timing correction** now keeps its label static and presents an
  editable millisecond textbox to the right of the slider.
- The slider snaps to `0` inside a ±15 ms center zone. Typed values retain
  one-millisecond precision across the supported -250 through +500 ms range.
- The default correction is now `0 ms`.
- Beat-reactive progress rendering now selects analyzer energy using the same
  canonical, millisecond-quantized source timestamp used by lyrics, spectrum,
  and progress position. Live levels are only a fallback until the timestamped
  analyzer sample becomes available.
