# Console and artwork controls, adaptive layout — 2026-10-29

ICGF now starts its floating artwork independently of terminal image rendering,
keeps pending review decisions when the popup is hidden, and can recover a stopped
preview worker. While a console menu or text field is waiting, Ctrl+A restores
artwork without activation; Ctrl+Alt+A explicitly requests foreground activation.
The shortcuts are local to ICGF's console, and use the modifiers in the Windows
input event rather than their later state.

Review and adjustment console menus adapt to one through four columns, retaining
colored defaults and grouping shared disabled-action reasons. Artwork provides
the same review actions, submenus and prefilled value fields. Every adjustment
continues to require a fresh rendered proposal before approval. Caption drafts
survive hiding, reopening and resizing. Double-click artwork opens the exact
displayed file in the Windows default image viewer.

The artwork layout compares image space for bottom and side arrangements using
the current image aspect ratio, window dimensions and measured button sizes.
Square images can use the full available height with captions and two banks of
buttons in the side gutters. Wide images retain bottom controls when that permits
a larger displayed image. Active adjustment menus use the same layout system.

Displayed artwork keys activate buttons outside text fields, including I for
Ignore, Y for Approve, A for Add substitution, E for Regenerate and H for Help.
F2 opens Rename; Delete opens the separate Recycle confirmation. Keys in captions,
entries and separate dialogs remain text input. Disabled buttons cannot be
activated by a key. Approve-and-pause and Skip-and-pause actions were removed.

Changed caption text pulses its background while retaining its font, foreground
color, line breaks and character positions. Automatic preview changes retain
the native activation guard; explicit mouse/keyboard actions can activate controls.

Restart existing ICGF processes to load the update. This release does not alter
OCR models, packages or cache policy. No user image or queue was changed by the
deployment; tests use isolated generated fixtures. The user's complete initial
popup failure could not be reproduced from available logs, but terminal-render
failures can no longer prevent GUI startup and preview errors retain diagnostics.

## Validation

- Initial complete installed regression run: 377 passed, including all relocation checks.
- Adaptive layout and artwork regressions before final deployment: 53 passed.
- Final complete installed regression run: 387 passed, zero failures, errors or skips.
- Final suite duration: 153.071 seconds.
- Test report: `C:\codex\clairevironment\release-output\image-caption-gender-fixer\adaptive-20261029\installed-results-82b6199ee5b5418d8e5468c3725ab865.xml`.
- Native Windows input records verify both console shortcuts in an isolated hidden console.
- GUI tests verify passive reopening, explicit foreground request, failed-worker recovery,
  menu parity, prefilled field completion, draft preservation, resize behavior, side-bank
  bounds, adjustment-menu bounds, disabled-action hotkeys and identical pulsing text positions.
- Default-viewer calls are mocked during tests; no external viewer was launched.
- All deployed files and replacement backups were verified by SHA-256.
- The project root still contains only the launcher and README as regular files.

## Every affected C:\BAT path

Sibling replacement backups were created and verified before replacing content.
README sibling backups were then moved into runtime/backups/implementation to
preserve the minimal project root. No item was permanently deleted.

- **Created**: `C:\BAT\image_caption_gender_fixer\docs\releases\console-artwork-layout-20261029.md`
- **Modified**: `C:\BAT\image_caption_gender_fixer\README.md`
- **Created; moved to `C:\BAT\image_caption_gender_fixer\runtime\backups\implementation\README.md.bak.202610291003.replaced-by-chatgpt.bak`**: `C:\BAT\image_caption_gender_fixer\README.md.bak.202610291003.replaced-by-chatgpt.bak`
- **Created; moved to `C:\BAT\image_caption_gender_fixer\runtime\backups\implementation\README.md.bak.202610291100.replaced-by-chatgpt.bak`**: `C:\BAT\image_caption_gender_fixer\README.md.bak.202610291100.replaced-by-chatgpt.bak`
- **Created**: `C:\BAT\image_caption_gender_fixer\runtime\backups\implementation\README.md.bak.202610291003.replaced-by-chatgpt.bak`
- **Created**: `C:\BAT\image_caption_gender_fixer\runtime\backups\implementation\README.md.bak.202610291100.replaced-by-chatgpt.bak`
- **Modified**: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\adjustment_menu.py`
- **Created**: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\adjustment_menu.py.bak.202610291003.replaced-by-chatgpt.bak`
- **Created**: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\adjustment_menu.py.bak.202610291100.replaced-by-chatgpt.bak`
- **Created**: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\artwork_layout.py`
- **Modified**: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\cli.py`
- **Created**: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\cli.py.bak.202610291003.replaced-by-chatgpt.bak`
- **Created**: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\cli.py.bak.202610291100.replaced-by-chatgpt.bak`
- **Created**: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\console_input.py`
- **Modified**: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\floating_artwork.py`
- **Created**: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\floating_artwork.py.bak.202610291003.replaced-by-chatgpt.bak`
- **Modified**: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\paf_album_art.py`
- **Created**: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\paf_album_art.py.bak.202610291003.replaced-by-chatgpt.bak`
- **Created**: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\paf_album_art.py.bak.202610291100.replaced-by-chatgpt.bak`
- **Created and subsequently modified**: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\popup_controls.py`
- **Created**: `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\popup_controls.py.bak.202610291100.replaced-by-chatgpt.bak`
- **Created**: `C:\BAT\image_caption_gender_fixer\tests\integration\test_adaptive_artwork_layout.py`
- **Created and subsequently modified**: `C:\BAT\image_caption_gender_fixer\tests\integration\test_console_popup_parity.py`
- **Created**: `C:\BAT\image_caption_gender_fixer\tests\integration\test_console_popup_parity.py.bak.202610291100.replaced-by-chatgpt.bak`
- **Created**: `C:\BAT\image_caption_gender_fixer\tests\integration\test_native_artwork_shortcuts.py`
- **Modified**: `C:\BAT\image_caption_gender_fixer\tests\integration\test_review_refinements.py`
- **Created**: `C:\BAT\image_caption_gender_fixer\tests\integration\test_review_refinements.py.bak.202610291100.replaced-by-chatgpt.bak`
