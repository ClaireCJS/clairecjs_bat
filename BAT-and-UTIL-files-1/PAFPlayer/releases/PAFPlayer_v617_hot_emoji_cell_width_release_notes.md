# PAFPlayer V617 — hot emoji spacing in lyrics

The Emojimaxx replacement for `hot` now includes the Unicode emoji-presentation
selector (`♨️`). The bare hot-springs symbol measured as one console cell while
Windows Terminal could paint it across two, visually swallowing the space before
the next character. `Too hot & too fast` now renders as `Too ♨️ & too fast`.
The source lyric's spacing remains intact; no artificial padding is added.
Console rainbow and per-character hashed treatments also color the emoji and
its presentation selector as one cluster, without putting an ANSI escape
between them.

Focused regression tests cover the console path with and without Windows
Terminal compatibility, two-cell width, colored output, and the plain/web
phrase path.
