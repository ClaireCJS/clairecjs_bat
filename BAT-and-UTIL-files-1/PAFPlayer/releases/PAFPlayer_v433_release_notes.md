# PAFPlayer V433 — restore artwork transport performance

- Reverted V432's forced row-delta transport for artwork visualizer layers.
- The forced row comparison/build path reduced FPS. Artwork rendering returns to its prior transport selection and performance profile.
- The white-cell investigation remains separate; this release intentionally restores performance without retaining the incorrect transport restriction.
