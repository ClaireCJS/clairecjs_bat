# PAFPlayer V431 — ANSI-safe visualizer chunking

- Fixed a V430 console-output regression that split long visualizer payloads inside ANSI/VT control sequences.
- A split `ESC[48;2;…m` color command rendered its `;48;2…m` suffix as visible text and corrupted the DRCS frame.
- Console chunks now preserve complete CSI, DCS, OSC, charset, and DEC line-rendition sequences; an oversized control sequence is deliberately written whole.
- Verified with focused SGR and oversized-DRCS chunk-boundary checks.
