# PAFPlayer V476 — fractional next-track title duration

The Floating Lyrics next-track title control now uses seconds instead of milliseconds.

- Label: `Display song title for first X seconds`
- Supports fractional values such as `0.25` and `2.5` seconds.
- The selected value is shown in the control label.
- Existing millisecond persistence is retained for backward compatibility.

Validation: Python compilation and the V476 focused regression tests passed.

Changed file:

- `../PAFPlayer.py`
