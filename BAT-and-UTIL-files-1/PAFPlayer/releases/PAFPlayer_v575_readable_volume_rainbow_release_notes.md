# PAFPlayer V575 release notes

## Readable console volume rainbow

The compact volume icon and percentage now retain their rainbow identity while
dark blue and violet foreground colors are raised to a minimum readable
luminance. This prevents the volume from disappearing into the dark console
HUD at low-contrast points in the rainbow cycle.

## Validation

- Python compilation succeeded.
- Focused regression tests verify all 101 whole-percent volume levels meet the
  minimum luminance and preserve the existing progress-label brightness guard.
