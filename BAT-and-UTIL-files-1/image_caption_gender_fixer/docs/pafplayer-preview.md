# PAFPlayer terminal and floating artwork in ICGF 0.3.0

Review displays both terminal Twin DRCS images and a persistent floating image window.
The floating window follows the last image rendered and ends on the complete
proposal while the console asks for approval, skip, defer, OCR/style changes,
pause, or cancellation. Its complete caption pane preserves unchanged lines and
can be scrolled/copied. The same captions print in the console. OCR remains an
estimate to verify against the source image.

## Installed sibling code first

The expected installation is `C:\BAT\PAFPlayer\PAFPlayer.py`, found relative to
the tool as `..\PAFPlayer\PAFPlayer.py`. Runtime reads this trusted local Python
source and loads the named artwork definitions and their graphics dependencies.
It does not import/start the player or execute its
top-level startup, integration, registry, playback, or main code.

`doctor` reports whether the actual backend is `installed-pafplayer` or the
attributed `internal-pafplayer-copy` fallback, together with source path, version,
SHA-256, and fallback reason. Missing/incompatible sibling code uses the preserved
copies; no PAFPlayer download/installation or source modification is attempted.

GUI definitions loaded from PAFPlayer are:

- `external_album_art_monitor_work_areas`
- `_parse_external_album_art_geometry`
- `clamp_external_album_art_geometry`
- `ExternalAlbumArtWindow._gui_main._pillow_fit_canvas_image`
- `ExternalAlbumArtWindow._gui_main.reuse_or_create_photoimage`

Terminal definitions include `define_all_player_drcs`,
`_visualizer_art_microtiles`, `_visualizer_art_cell_styles`,
`art_detail_geometry`, `choose_art_detail_drcs_layout`, and
`terminal_cell_pixel_size_nonintrusive`, together with their graphics dependency
closure. Their compiled function filenames point to the installed PAFPlayer
source. ICGF supplies a fitted static RGB grid at full brightness, then uses
PAFPlayer's DRCS font banks, artwork quantization and cell styling directly.
Source orientation and alpha are handled in memory; the whole image is contained
within the available terminal rectangle.

`paf_drcs.py` reads PAFPlayer source defaults, `PAFPlayer.dcc` player settings,
then current HKCU visualizer preferences (with legacy-key fallback), in that
precedence order. Registry access uses `KEY_READ`; no setting is written or
migrated. The current saved profile is granularity 3 (**2x Twin DRCS**), black
and bar artwork detail mode 9 (**2x4 subcells**), and seam strategy 5. Doctor's
`preview.artwork_backend.terminal` reports the actual values and their sources.
The selected profile starts no encoder and uses no Chafa or SIXEL output. DRCS
display requires a terminal that supports the same downloadable glyphs used by
PAFPlayer; the floating window also shows the full image independently.

## Attributed internal copies and floating lifecycle

`paf_album_art.py` and `paf_backend.py` explicitly mark copied definitions from
`C:\BAT\PAFPlayer\PAFPlayer.py`, `PROGRAM_VERSION V567`, copied 2026-10-27.
Their headers record its SHA-256; named routines retain original names and line
ranges. `_paf_drcs_copy.py` similarly marks its copied V628 graphics definitions,
source hash and per-definition line ranges; `paf_drcs.py` prefers the live sibling
over that fallback. Legacy SIXEL helpers retained in `paf_backend.py` are not
used by ICGF's terminal preview. `floating_artwork.py` explicitly attributes its non-daemon thread, queue,
shutdown, and owner-thread garbage collection pattern to PAFPlayer's
`ExternalAlbumArtWindow._ensure_started`, `_gui_thread_entry`, and `_gui_main`.
PAFPlayer and shared Claire utilities were not modified.

The pixel pipeline preserves PAFPlayer's monitor-aware window placement,
aspect-preserving Lanczos containment, centered artwork, and stable Pillow/Tk
PhotoImage reuse. ICGF normalizes source orientation in memory, supplies pointer-
safe Win32 monitor signatures, displays alpha against a checkerboard, and adds
caption text. Previewing changes no source image or metadata.

Exactly one GUI owner thread creates, updates, and destroys Tk/ImageTk objects.
The console sends image updates through a queue and waits for each render before
asking for approval. Hiding/closing/Escape hides the window; it neither approves
nor cancels an edit. A subsequent preview may reveal it again. The latest image
remains available from memory even after owned staging files are recycled.
Program shutdown joins the GUI thread before returning control to the shell.

`--no-preview` disables both image outputs while retaining full captions and
console review. JSON and redirected output open no GUI and emit no DRCS/ANSI.
Python 3.10 x64 must include its standard Tcl/Tk component; bundled Pillow supplies
ImageTk. The DRCS artwork path needs no external encoder. Existing bundled Chafa
files remain covered by the unchanged dependency manifest. No new download
or package installation was needed on this machine.

The user's 2026-10-27 request supersedes the original specification's standalone
Chafa-symbol preview and blanket junction refusal. Explicit directory junctions
resolve to physical paths before queuing; linked files, unknown reparse providers,
recursive junction children, and installation aliases retain their protections.
Original backups, folder history, undo, recovery, and mandatory review remain.


## Review workflow update — 2026-10-28

Portrait previews put the detected/proposed captions beside the full-height image.
The passive artwork window now supports Approve, Reject/Skip, Add substitution
with priority and keyboard ordering, and direct editing of the prefilled proposed
caption followed by regeneration. Approval is invalidated by edits and tied to a
single current proposal. Warnings appear in the window and in bright yellow in
the terminal. Console choices are colored and show ENTER defaults; [y] approves,
[a] adds a rule and [e] opens the prefilled caption editor. Detail terminal crops
are one fifth of full preview dimensions. Startup status messages erase in place.

Built-ins add `his wife` → `her wife` and a case-preserving protective `real man`
identity rule. Ordered priorities persist in a single folder-rule append.
OCR uses bounded higher-resolution/grayscale and caption-panel candidates;
cache algorithm 2 requires a one-time refresh of older OCR results. New outputs
use `-genderfixed`; legacy `-gendeerfixed` names receive verified non-overwriting
renames with recoverable journals and history aliases that preserve undo.
See `releases/review-workflow-20261028.md` for validation and file disclosures.
