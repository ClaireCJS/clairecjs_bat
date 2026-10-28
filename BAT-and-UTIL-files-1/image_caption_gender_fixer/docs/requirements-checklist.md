# Requirements and acceptance evidence

Scope: Windows CPython 3.10 x64, local PNG/JPEG caption correction, the bundled
offline dependencies, and the required review/history/transaction/session/undo
workflow. Animated/multiframe and unvalidated formats are explicitly deferred as
permitted by the specification. Photographic repair and font/style inference are
best-effort and remain subject to review; uncertainty is not labeled proof.

The consolidated specification is `implementation-specification.txt`. The user’s 2026-10-27 request supersedes its Chafa preview and blanket junction refusal; see `pafplayer-preview.md`. The latest
installed test run and canonical-location checks are recorded in
`releases/review-workflow-20261028.md`. Earlier release reports describe their own
checkpoints and must not be mistaken for current acceptance results.

| Spec | Implementation/evidence | Status |
| ---: | --- | --- |
| 1 | Canonical C:\BAT\image_caption_gender_fixer; only launcher + README at root; relative resources; own-installation target refusal; relocation/root tests | Implemented; installed check in release report |
| 2 | Verified original backups, non-overwriting collision names, Recycle Bin only, developer replacement backups, full per-operation C:\BAT disclosure | Implemented; Windows transaction/recycle tests |
| 3 | Primary/admin commands, literal wildcards/paths/end-of-options, flags, read-only/dry-run protection, explicit protected decisions | Implemented; CLI, maintenance, contracts tests |
| 4 | Local stdlib coordinator, fast OCR/native inpainting, one worker, downscale/eco, no telemetry, no normal network, crop repair + composite; --ocr/--ocr-only/-o prefetch to hidden folder-local .ocr with content/model/engine/quality validation and normal initial-OCR reuse | Implemented; real OCR/render, cache rename/invalidation/interruption and network-guarded tests |
| 5 | Unchanged bundled clairecjs_utils.claire_progressbar with rainbow default, interactive-only progress | Implemented; bundled import and source-hash check |
| 6 | Actual private packages/DLLs/native tools/data, ABI rejection, isolated selection, consent repair, complete offline archive, ready publication, restart/relocation | Implemented; real offline rebuild + moved-tree imports; network/install orchestration mocked |
| 7 | Both PAFPlayer terminal Twin DRCS using current read-only detail/seam settings and persistent floating artwork following the last render; installed sibling source preferred, attributed copy fallback; full captions and JSON/redirect/no-preview gates | Implemented; actual sibling DRCS definitions, no external encoder on the selected profile, settings precedence, floating lifecycle, resizing and caption tests |
| 8 | Magic-aware discovery, wildcard/literal deduplication, opt-in recursion/hidden/system; explicit directory junctions resolved to physical targets; linked files/unknown providers refused; recursive junction children skipped | Implemented; real junction/loop/install-alias and CLI/filesystem tests |
| 9 | Descending stages, normalized longest/literal/scope/user/order precedence, Unicode/case, bounded regex/output, cycles, provenance, intermediate stages | Implemented; rules tests and normalized-tie/cascade tests |
| 10 | UTF-8 JSONL rules, explicit saves, notes/IDs, profiles, scoped exclusions + enable/disable, conjunction semantics, original-span protection, malformed-record quarantine | Implemented; rule/profile/exclusion/invalid-byte tests |
| 11 | First render before optional OCR correction; corrected text/grouping/bounds/rotation; rematch/rerender/reapprove; no silent learned rule; blocked-render adjustment path | Implemented; real post-render OCR correction and blocked-approval tests |
| 12 | Three confidence levels; texture/face/edge/seam/fit/OCR uncertainty; only explicit level-1 bypass | Implemented; photo, face warning, alias and level-gate tests |
| 13 | One composite approval per image, per-region controls, skip/cancel/defer/pause, no approval of blocked proposal, no --yes bypass | Implemented; multi-region, cancel/resume, no-match, blocked render tests |
| 14 | Glyph-focused masks, effects/directional/protection controls, fill/gradient/Telea/Navier/patch comparison, adjacent ownership-tracked crops, explicit label | Implemented; actual repair/comparison and unaffected-pixel tests; no neural model selected |
| 15 | Ranked normal/bold/italic installed-font approximations; color/alpha/outline/shadow/blur/rotation/tracking controls; honest style uncertainty | Implemented as best-effort; rendering/edge/style-control tests; exact font/photographic perfection not promised |
| 16 | Full styled-alpha measurement, bounds/protected-neighbor checks, safe expansion/shift/tracking/approx. 20% shrink, manual blocked-fit workflow | Implemented; each-edge, no-fit, outline/shadow, and adjustment tests |
| 17 | Decoding/dimensions/frame/orientation/ICC/DPI/alpha checks, targeted OCR, source-absence checks, face/edge/seam warnings, lossless outside-region equality | Implemented; real PNG/JPEG, metadata/orientation/alpha tests; animation explicitly deferred |
| 18 | Durable intent, source identity/hash + approved-stage hash under leases, exact same-volume non-overwriting preservation/publish, history before completion | Implemented; commit/rollback/history-ack/source/stage mutation/capacity tests |
| 19 | Exact suffix/backup/archive/preview/marker/hash detection; folder history authoritative; observed-history-derived cache | Implemented; renamed folder/file/product tests; optional perceptual hashing is not enabled |
| 20 | Exact hidden unencrypted .history.icgf, relative records, schema/checksum/order/transitions, corrupt-tail retention, raw backup | Implemented; history, folder-move, corrupt-tail, backup, recovery tests |
| 21 | Numbered old-job selection/inspect/retain/new/forget; retry/help and confirmed one/all queue recycling; machine IDs remain available for JSON/explicit resume; reanalysis/reapproval, canceled-item resume; synchronous launcher and repair restart preserve console ownership and child exit code | Implemented; numbered/help/retry/all-job session tests plus actual parent-wait and batch-alias tests |
| 22 | Adjacent UUID images, intent/identity/hash ownership callbacks, known-only cleanup, retained partial/changed artifacts, comparison ownership | Implemented; image/cleanup/forget tests |
| 23 | Unambiguous active undo, backup verification, corrected archive first, exact original restoration, durable idempotent undo, collision safety | Implemented; actual undo and all durable undo-boundary recovery tests |
| 24 | Ask/keep/recycle + run/future preferences; reset/show; modified corrected archive protected; failed recycling retained | Implemented; preference paths, changed-archive and real recycle tests |
| 25 | Source/state capacity checks, access/lease/lock/reparse/network/collision guards, extended Windows kernel paths, no cross-volume copy/delete | Implemented; capacity, contention, mutation, collision, long-Unicode-path tests |
| 26 | Crash-safe journals/state, history reconciliation, exact recovery, local redacted logs/crash reports, OS-released locks, retained orphan state staging | Implemented; fault-boundary, process-death lock, privacy and state-staging tests |
| 27 | One-object JSON, stderr diagnostics, no ANSI/prompt/preview, explicit per-image results/IDs, stable exit codes | Implemented; contracts/selection/cancel/maintenance tests |
| 28 | Version/schema map, UTC events/local backup names, UUIDs, read-only explain with product/ambiguity/provisional-fit reasons | Implemented; version/ABI/explain/product tests |
| 29 | Pure/Windows/mock/native/generated-image/actual Tk gallery/undo/recovery/repair/relocation layers; test fixtures outside installation | Implemented; exact installed suite count and timing in latest release report |
| 30 | README, recovery/state design, JSON contract, dependency provenance/licensing, bundle reconstruction, troubleshooting/uninstall | Implemented; delivered docs and source notices |
| 31 | Success only after original preservation + verified approved output + durable folder event; unsafe/uncertain cases retain/ask/defer | Implemented; transaction and human-review gates verified |
| 32 | Installed root/help/version/doctor/dry-run/offline/caller-CWD checks, actual process and alias lifetime, source/deletion audit, full C:\BAT path disclosure | Final evidence in latest release report |

## Deliberate limitations, not silent substitutions

- Windows CPython 3.10 x64 is the supported ABI; the interpreter is not bundled.
- PNG/JPEG are the validated output formats. Animation/multiframe preservation is
  handled by explicit deferral rather than dropping frames.
- Photographic reconstruction, face detection, source style, outlines/shadows,
  and fonts are approximations with manual controls and mandatory uncertainty
  review. Numeric checks cannot certify aesthetics or detect every face/object.
- Lossless unaffected-pixel equality requires no global orientation transform;
  JPEG re-encoding is lossy outside the edited region. Original backups are exact.
- Perceptual hashing/heavy neural inpainting are optional and not selected. There
  is no perceptual auto-skip or automatic neural/font download.
- Network targets require permission and can still be refused when reliable
  locking/renaming/recycling cannot be established. No remote durability claim.
- Folder history moves with the folder. Local live-session absolute hints can
  become stale; cross-computer jobs or undo are not promised.
- Checksums do not authenticate maliciously rewritten history. Corrupt or
  ambiguous states retain evidence and require explicit inspection.
- Dependency download/installer control tests are mocked; actual installed native
  tools, file APIs, OCR/render/undo, offline reconstruction, and relocation are
  exercised separately. Tests never perform a real internet install.
- No physical disk-failure, exhaustive hardware/font combinations, every network
  filesystem, or perfect aesthetic reconstruction is claimed as tested.


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
