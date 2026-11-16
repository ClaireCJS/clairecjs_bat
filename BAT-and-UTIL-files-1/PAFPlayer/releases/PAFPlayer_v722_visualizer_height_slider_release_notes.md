# PAFPlayer V722 — visualizer-height slider

Released November 14, 2026.

## Changes

- Expand the Console Visualizer height slider to a flexible 420–760 px-class desktop control instead of the generic 210 px range.
- Preserve the locally selected row count while the pointer is dragging and while the server is acknowledging the change.
- Stop stale status polling from snapping the range thumb back to an older row count.
- Turn off **Auto-set to tallest** when the user manually adjusts the height.
- Retain a compact responsive layout on narrower screens.

## Verification

A headless-Chrome interaction test verifies the rendered width, stale-status
resistance during and immediately after dragging, automatic-mode disengagement,
server acknowledgement, and later legitimate server updates.
