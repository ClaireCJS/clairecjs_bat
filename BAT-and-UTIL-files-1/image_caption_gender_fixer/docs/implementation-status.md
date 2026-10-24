# Release status: 0.2.0

This supersedes the earlier in-progress implementation checkpoint. The supported
local Windows CPython 3.10 x64 PNG/JPEG workflow is implemented, including private
dependencies, OCR/render/review, safe transactions, hidden folder history,
session pause/resume/forget, exact undo, and crash recovery. The installation is
`C:\BAT\image_caption_gender_fixer`; root files are only the launcher and README.

The requirement-by-requirement evidence is in `requirements-checklist.md`.
Actual installed-location tests, hashes, smoke checks, and every affected C:\BAT
path are recorded in `releases/completion-20261024.md`. The installed verification
record is authoritative; earlier release reports describe earlier checkpoints.

The completion pass added or strengthened:

- Safe blocked-render adjustment instead of a forced failure or unsafe approval.
- Context/phrase/original-occurrence exclusions across the complete cascade,
  profile and exclusion IDs/administration, global opt-in positive rules, malformed
  byte/record quarantine, bounded matching/output, and intermediate rule traces.
- Resumable cancellation, selected-profile retention, JSON decision IDs, durable
  session validation, mixed committed/uncommitted session forgetting.
- Actual offline package reconstruction followed by relocation, clear ABI
  rejection, early isolation from unrelated global imports, and terminal-preserving
  restart after a verified package switch.
- Source identity and approved-stage hash checks under Windows leases, rename
  identity checks, local-state capacity checks, extended Unicode paths, and
  committed-history/filesystem consistency before recovery acknowledgement.
- All durable undo-boundary recovery paths; preserved partial atomic-state
  staging is reported separately instead of hiding a recoverable canonical journal.
- Actual repair comparisons, numbered masks, approximate bold/italic font
  candidates, local face/edge/seam warnings, and bounded manual style controls.
- Lossless outside-region/alpha checks, ICC/DPI preservation, baked orientation,
  nested EXIF dimension handling, reserved-marker collision refusal, and output
  extensions based on actual format.
- Read-only bundle-hash doctor checks, selected repaired-tree inspection,
  provisional read-only explain, redacted local operation/crash diagnostics,
  complete README/recovery/JSON/dependency/license documentation.

The automatic setup-download cleanup remains: verified redundant archives are
recycled after installation/repair or processing startup; working dependencies
and the offline repair archive are kept. Recycled items still consume drive space
in the Recycle Bin until it is emptied separately.

No real user image is used in tests. Tests perform no internet installations.
Download/control paths are mocked; installed OCR, Windows file APIs, image
processing, undo, lock death, package reconstruction, and relocation are exercised
with actual local components and generated disposable data.

Deliberate limits remain those allowed by the specification: uncertain font/style
and photographic repair require review; faces/edges are heuristics; animation and
unvalidated formats defer; JPEG is lossy; the interpreter is not bundled; remote
filesystem guarantees and cross-computer live jobs/undo are not promised.
No neural model, font installation, telemetry, or image upload is introduced.
