# PAFPlayer V429 — circled ten in Windows Terminal

September 22, 2026. Build `2026-09-22-v429-circled-ten-terminal-spacing`.

The screenshot's `all ❿of My ...` collision exposed an omitted glyph: the terminal-only Emojimaxx spacing set ended at ❾, although ten/10/tens map to ❿. The existing test also stopped at nine. Windows Terminal therefore received only the source separator after ❿, without the safety cells used for the other negative circled numbers.

The compatibility set now includes ❿. It receives the same two generated safety cells plus the original word separator, before wrapping, centering and coloring. Sung, scrolling and neighboring lines share this substitution path. The correction is scoped to generated Windows Terminal replacements; literal circled numbers, web/Tk lyrics, existing compound-number spacing and other glyph rules retain their behavior. This release builds on V428 and preserves its shutdown fix and intervening changes.

Validation: the new regression reproduced the screenshot phrase and failed on the original implementation specifically for ten. After the correction, 13 focused tests passed. Coverage includes ten/10/tens, all ten negative circled glyphs across three text styles, sung/neighbor parity, wrapping at exact cell boundaries, all karaoke color treatments, literal glyphs, other surfaces, and existing tens compounds. The older every-digit regression now includes ten. Source compilation passed. No live Windows Terminal pixel comparison was available in this session; these checks verify emitted text and cell accounting, not the user's font rasterization. The full historical suite was not rerun.

Restart PAFPlayer and confirm V429 to load the correction.
