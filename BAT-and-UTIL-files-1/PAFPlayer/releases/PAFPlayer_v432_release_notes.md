# PAFPlayer V432 — artwork delta-background safety

- Fixed one-frame bright/default-color cells in artwork blackness and artwork-bar visualizer layers.
- Semantic-cell transport stores foreground color and glyph only; it cannot safely repaint a cell whose artwork layer also supplies a background color.
- With artwork bars or blackness active, PAFPlayer now uses row-delta/full-frame transport, which sends foreground and background together. Ordinary non-artwork spectrum rendering may still use semantic-cell transport.
