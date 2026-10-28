# PAFPlayer V596 — Emoji coloring selector

The Artwork Lyric Coloring and Floating Lyric Coloring windows now show an
**Emoji coloring** dropdown. The official and remote tray **Options…** windows
show the same control. It offers exactly two rendering choices:
**Official color emoji — no additional coloring** and
**Monochrome emoji — {current coloring/treatment name}**. The monochrome label
updates when a pattern treatment, per-letter palette, or solid color mode
changes. The rendering switch applies to both artwork and floating lyrics;
their color treatments stay independent.

The selector uses the existing `ExternalAlbumArtPopupColorEmoji` preference
and the existing lyric coloring mode IDs. The official player saves the
preference globally. A tray-only client's preference is stored in its
per-server presentation profile, and changing it stops server appearance
inheritance until the user re-enables **Follow the server's artwork and lyric
appearance**. The artwork title-bar emoji toggle remains available.

Focused automated tests cover the two labels, dynamic treatment names,
renderer command routing, per-server tray settings, and single-file bundle
parity. Whip Emojimaxx appearance still requires physical remote-client
verification. Discord Social SDK live validation still requires the official
Windows SDK package and a Developer Portal setup.
