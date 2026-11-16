# PAFPlayer V644 — keep “bigger” as text

Released November 5, 2026.

Removed the “bigger” → 🦣 mapping from Emojimaxx and added it to the explicit
removal list. “Bigger” and “BIGGER” also remain text, including punctuation.
No other word mappings or configuration IDs changed.

Verified six cases through plain/popup, console, and web lyric rendering;
four existing curation tests pass with no skips. Python compilation and all
27 embedded-module/source parity checks pass. “Biggest” retains its mapping.
[Test report](../tests/reports/v644-checks-20261105-195223.json).

Restart PAFPlayer and any remote tray client using an older copy to load V644.
The active player was not interrupted. The release is a new, hash-verified copy;
required backups were verified before replacements. The project, lockscreen,
and screensaver root audits found no obsolete files requiring cleanup.
No files were deleted. No literal C:\BAT paths changed.

Source SHA-256: `df254a38b04578414ebfc2740f9cdb03abad26eec04b25d7a94cddf9ade79a58`.
