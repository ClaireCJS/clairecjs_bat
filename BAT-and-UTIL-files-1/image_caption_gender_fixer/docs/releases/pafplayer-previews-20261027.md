# ICGF 0.3.0: PAFPlayer Twin DRCS, floating artwork, captions and shell lifetime

Release validation: 2026-10-27, Windows CPython 3.10 x64.

Terminal previews now use the installed sibling PAFPlayer Twin DRCS graphics definitions and current artwork settings. A persistent floating window follows the last rendered image, ending on the complete proposal while the console requests review. Complete detected/proposed captions preserve unchanged words and lines.

The isolated launcher and repair restart use a waiting child process. The batch aliases explicitly select console Python and propagate its final status. The original launcher used os.execv on Windows and the wrappers relied on .py associations; both could return the shell before processing ended.

Explicit directory junctions resolve to physical paths before discovery and journaling. A read-only check of the actual C:\new user folder found 543 recognized images for no argument, dot and star, and 516 for *.jpg; its filename/size/mtime inventory was unchanged. Linked files, unknown reparse providers, recursive junction children and installation aliases retain their protections.

## PAFPlayer source and current preferences

Installed source: `C:\bat\PAFPlayer\PAFPlayer.py`, version `V628`, SHA-256 `fc6e7301f3aef7515be171bdccf62f2ed30a11581f24280b372e90f90de49e97`.

Current settings: `DrcsEnabled=1`, `VisualizerGranularity=3`, `DrcsArtMicrotileDetailModeV370=9`, `DrcsArtBarMicrotileDetailModeV370=9`, `ArtworkSeamStrategy=5`.
Detail: 2×4 octant hybrid (8 subcells — 100% exact — Unicode mosaics ON; Unicode+DRCS); subcells `[2, 4]`; bank layout `3`.

PAFPlayer defaults, sibling .dcc and HKCU visualizer preferences are read without writes or migrations. Graphics definitions load without starting the player. Attributed copies retain source hashes and per-definition origins: V567 GUI copies and V628 DRCS fallback. The preferred installed source is live; another task updated PAFPlayer during this work. ICGF did not modify PAFPlayer, its settings, registry or shared Claire utilities.

The selected 2x Twin DRCS / 2x4 octant hybrid profile uses PAFPlayer font banks, quantization and cell styling, with no Chafa or SIXEL encoder call. Old bundled Chafa payload and legacy helper definitions remain preserved. The terminal must support PAFPlayer-style downloadable glyphs; terminal-byte tests establish protocol output, not visual quality in every terminal.

## Validation and limits

- Final complete installed suite: **190 passed**, no warnings, 69.427 seconds. Evidence: `installed-results-3fb8b1a7bbc747dd97e4fa13d0d1069e.xml` copied below.
- Real installed-source binding, generated OCR/render/commit/undo/recovery fixtures, parent wait/exit propagation, explicit junctions, full captions, transparent-source preservation, read-only settings precedence and DRCS output with subprocess encoders forbidden.
- Real Tk window resizing, PhotoImage reuse, hide/close/error handling, non-daemon worker ownership, delayed redraw acknowledgement and joined shutdown. The installed run first caught a fixed-delay resize-test assumption; both the check and production acknowledgement now wait for completed rendering. Tcl-owning references are released on their owner thread; unraisable Tk warnings are treated as test failures.
- Live PTY smoke: actual OCR, Twin DRCS bytes, floating proposal and console review; skip returned application status 10, source hash unchanged, no history or remaining owned previews, floating worker closed. PowerShell reports nonzero native status as wrapper exit 1; the recorded application status is 10.
- Version/help/doctor and the real icgf.bat alias passed; all 2,022 bundle files verified. Their before/after installation hashes were identical. Root regular files remain only README.md and image_caption_gender_fixer.py.
- Existing resumable user sessions preserved: 2; pending transactions: 0. Real user images were never edited by validation.
- Package download/installer controls remain mocked. No new dependency download/installation was needed. OCR, photographic repair and font matching remain best effort and require review. JSON, redirected output and --no-preview suppress the image displays; full captions remain available. Three audit headers from earlier diagnostic App initialization are retained and disclosed below.

## Release evidence

- `pafplayer-previews-20261027-tests.xml`
- `pafplayer-previews-20261027-smoke.json`
- `pafplayer-previews-20261027-acceptance.json`
- `pafplayer-previews-20261027-junctions.json`

## Complete C:\BAT change disclosure

Every affected file is listed below, including verified backups and transient sibling backups moved into the runtime archive. No original file was deleted. Root backups were first created and verified as siblings, then moved to preserve the minimal root. Files created during this release and later updated carry both actions.

| Action | Full path |
| --- | --- |
| Modified | `C:\BAT\icgf.bat` |
| Created, Renamed; moved to `C:\BAT\image_caption_gender_fixer\runtime\backups\launchers\icgf.bat.bak.202610271735.replaced-by-chatgpt.bak` | `C:\BAT\icgf.bat.bak.202610271735.replaced-by-chatgpt.bak` |
| Modified | `C:\BAT\image-caption-gender-fixer.bat` |
| Created, Renamed; moved to `C:\BAT\image_caption_gender_fixer\runtime\backups\launchers\image-caption-gender-fixer.bat.bak.202610271735.replaced-by-chatgpt.bak` | `C:\BAT\image-caption-gender-fixer.bat.bak.202610271735.replaced-by-chatgpt.bak` |
| Modified | `C:\BAT\image_caption_gender_fixer\docs\implementation-status.md` |
| Created | `C:\BAT\image_caption_gender_fixer\docs\implementation-status.md.bak.202610271735.replaced-by-chatgpt.bak` |
| Created | `C:\BAT\image_caption_gender_fixer\docs\implementation-status.md.bak.202610271755.replaced-by-chatgpt.bak` |
| Created, Modified | `C:\BAT\image_caption_gender_fixer\docs\pafplayer-preview.md` |
| Created | `C:\BAT\image_caption_gender_fixer\docs\pafplayer-preview.md.bak.202610271755.replaced-by-chatgpt.bak` |
| Created | `C:\BAT\image_caption_gender_fixer\docs\releases\pafplayer-previews-20261027-acceptance.json` |
| Created | `C:\BAT\image_caption_gender_fixer\docs\releases\pafplayer-previews-20261027-junctions.json` |
| Created | `C:\BAT\image_caption_gender_fixer\docs\releases\pafplayer-previews-20261027-smoke.json` |
| Created | `C:\BAT\image_caption_gender_fixer\docs\releases\pafplayer-previews-20261027-tests.xml` |
| Created | `C:\BAT\image_caption_gender_fixer\docs\releases\pafplayer-previews-20261027.md` |
| Modified | `C:\BAT\image_caption_gender_fixer\docs\requirements-checklist.md` |
| Created | `C:\BAT\image_caption_gender_fixer\docs\requirements-checklist.md.bak.202610271735.replaced-by-chatgpt.bak` |
| Created | `C:\BAT\image_caption_gender_fixer\docs\requirements-checklist.md.bak.202610271755.replaced-by-chatgpt.bak` |
| Modified | `C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py` |
| Created, Renamed; moved to `C:\BAT\image_caption_gender_fixer\runtime\backups\implementation\image_caption_gender_fixer.py.bak.202610271735.replaced-by-chatgpt.bak` | `C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py.bak.202610271735.replaced-by-chatgpt.bak` |
| Modified | `C:\BAT\image_caption_gender_fixer\README.md` |
| Created, Renamed; moved to `C:\BAT\image_caption_gender_fixer\runtime\backups\implementation\README.md.bak.202610271735.replaced-by-chatgpt.bak` | `C:\BAT\image_caption_gender_fixer\README.md.bak.202610271735.replaced-by-chatgpt.bak` |
| Created, Renamed; moved to `C:\BAT\image_caption_gender_fixer\runtime\backups\implementation\README.md.bak.202610271755.replaced-by-chatgpt.bak` | `C:\BAT\image_caption_gender_fixer\README.md.bak.202610271755.replaced-by-chatgpt.bak` |
| Created | `C:\BAT\image_caption_gender_fixer\runtime\backups\implementation\image_caption_gender_fixer.py.bak.202610271735.replaced-by-chatgpt.bak` |
| Created | `C:\BAT\image_caption_gender_fixer\runtime\backups\implementation\README.md.bak.202610271735.replaced-by-chatgpt.bak` |
| Created | `C:\BAT\image_caption_gender_fixer\runtime\backups\implementation\README.md.bak.202610271755.replaced-by-chatgpt.bak` |
| Created | `C:\BAT\image_caption_gender_fixer\runtime\backups\launchers\icgf.bat.bak.202610271735.replaced-by-chatgpt.bak` |
| Created | `C:\BAT\image_caption_gender_fixer\runtime\backups\launchers\image-caption-gender-fixer.bat.bak.202610271735.replaced-by-chatgpt.bak` |
| Created | `C:\BAT\image_caption_gender_fixer\runtime\logs\32991d9d-7444-4927-ba8a-afa6cf5e9236.jsonl` |
| Created | `C:\BAT\image_caption_gender_fixer\runtime\logs\65e18a43-3439-4171-b705-fcf1abd85b03.jsonl` |
| Created | `C:\BAT\image_caption_gender_fixer\runtime\logs\a75a39f5-7221-43ee-a2ba-cc70b8b77fdc.jsonl` |
| Modified | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\__init__.py` |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\__init__.py.bak.202610271735.replaced-by-chatgpt.bak` |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\_paf_drcs_copy.py` |
| Modified | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\cli.py` |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\cli.py.bak.202610271735.replaced-by-chatgpt.bak` |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\cli.py.bak.202610271755.replaced-by-chatgpt.bak` |
| Modified | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\dependencies.py` |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\dependencies.py.bak.202610271735.replaced-by-chatgpt.bak` |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\dependencies.py.bak.202610271755.replaced-by-chatgpt.bak` |
| Created, Modified | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\floating_artwork.py` |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\floating_artwork.py.bak.202610271759.replaced-by-chatgpt.bak` |
| Modified | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\fs.py` |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\fs.py.bak.202610271735.replaced-by-chatgpt.bak` |
| Modified | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\imaging.py` |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\imaging.py.bak.202610271735.replaced-by-chatgpt.bak` |
| Created, Modified | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\paf_album_art.py` |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\paf_album_art.py.bak.202610271755.replaced-by-chatgpt.bak` |
| Created, Modified | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\paf_backend.py` |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\paf_backend.py.bak.202610271755.replaced-by-chatgpt.bak` |
| Created | `C:\BAT\image_caption_gender_fixer\src\image_caption_gender_fixer\paf_drcs.py` |
| Modified | `C:\BAT\image_caption_gender_fixer\tests\integration\test_final_contracts.py` |
| Created | `C:\BAT\image_caption_gender_fixer\tests\integration\test_final_contracts.py.bak.202610271735.replaced-by-chatgpt.bak` |
| Created | `C:\BAT\image_caption_gender_fixer\tests\integration\test_launch_and_junctions.py` |
| Created, Modified | `C:\BAT\image_caption_gender_fixer\tests\integration\test_paf_album_art.py` |
| Created | `C:\BAT\image_caption_gender_fixer\tests\integration\test_paf_album_art.py.bak.202610271755.replaced-by-chatgpt.bak` |
| Created | `C:\BAT\image_caption_gender_fixer\tests\integration\test_paf_album_art.py.bak.202610271759.replaced-by-chatgpt.bak` |
| Created | `C:\BAT\image_caption_gender_fixer\tests\integration\test_paf_drcs.py` |
| Created, Modified | `C:\BAT\image_caption_gender_fixer\tests\integration\test_paf_sibling_and_floating.py` |
| Created | `C:\BAT\image_caption_gender_fixer\tests\integration\test_paf_sibling_and_floating.py.bak.202610271755.replaced-by-chatgpt.bak` |
| Created | `C:\BAT\image_caption_gender_fixer\tests\integration\test_paf_sibling_and_floating.py.bak.202610271759.replaced-by-chatgpt.bak` |
| Modified | `C:\BAT\image_caption_gender_fixer\tests\integration\test_relocation.py` |
| Created | `C:\BAT\image_caption_gender_fixer\tests\integration\test_relocation.py.bak.202610271735.replaced-by-chatgpt.bak` |
| Created | `C:\BAT\image_caption_gender_fixer\tests\integration\test_relocation.py.bak.202610271755.replaced-by-chatgpt.bak` |

Project size before: 483,038,629 bytes. Before adding this report/evidence: 483,490,700 bytes (+452,071); increase includes all verified replacement backups and attributed fallback source. Dependencies were preserved unchanged.
