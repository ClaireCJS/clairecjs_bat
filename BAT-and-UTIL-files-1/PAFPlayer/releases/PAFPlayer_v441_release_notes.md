# PAFPlayer V441 — Atomic DRCS console chunks

- Fixes the visualizer writer's 4,096-character boundary handling: it now recognizes a DCS sequence that began earlier in the chunk and extends past that boundary.
- Keeps the 4,159-character downloadable DRCS font definition in one console write, preventing a split soft-font definition from producing transient bright/block glyphs.
- Retains V433's fast artwork transport; this change does not force row-delta or full-frame rendering.
