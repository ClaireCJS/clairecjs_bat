# Recovery and data ownership

Original-image preservation is the first invariant. Rendering creates hidden
adjacent artifacts; it never writes pixels or metadata back into the source.
The original is renamed to the required sibling backup only after final approval.
All candidate image files stay on the source volume. Original and stage leases
exclude writers, and the source identity/hash plus approved stage hash are
checked again before protected renames. Non-overwriting Windows moves verify
hashes and identity; collisions preserve both occupants.

## Conversion state machine

| Durable phase | Expected state | Deterministic interrupted recovery |
| --- | --- | --- |
| prepared | Original and approved stage present | Keep original; mark rollback |
| original_preserved | Original renamed to verified backup | Restore backup without overwrite |
| output_published | Corrected output published; history may lag | Consult authoritative history first; otherwise return output to stage and restore original |
| committed | Output + original backup + folder committed event | Recognize without reprocessing |

Intent is flushed under `runtime/state/transactions` before the first rename.
History is appended/flushed before local completion. If an append reached disk
but acknowledgement failed, published files remain for reconciliation; the tool
does not roll back data already committed in authoritative history.
Reconciliation checks journal/history hashes and actual preserved files, and
stops on ambiguity. Repeated recovery creates no duplicate event.

## Undo state machine

| Phase | Action/recovery |
| --- | --- |
| undo_prepared | Verify backup, corrected image, unoccupied original name, archive destination |
| undo_archived | Corrected → collision-safe undo archive; if interrupted, restore corrected safely |
| undo_restored | Original backup → original; verify bytes, then append undo event |
| undone | History authoritative; local journal can reconcile after verifying the restored original |

Archive disposition happens after restoration/history. Changed corrected content
is retained unless explicitly approved for recycling. Recycling failure retains
the archive. Recovery does not guess permission to recycle an uncertain archive.

## Folder history

`.history.icgf` is UTF-8 JSON Lines with Windows Hidden set. Its schema-1 header
has a random history identity. Records have sequence, previous/checksum chain,
event UUID, transaction UUID, relative filenames, original/corrected hashes,
rules fingerprint/profile, versions, and relevant archive information.
Conversion and undo events are idempotent and transition-validated.

Absolute parent paths and drive letters do not bind history identity. Recognition
therefore survives moving/renaming the containing folder. The derived cache can
be empty, stale, or absent; authoritative local history still works. A checksum
chain detects accidental damage, not an attacker who rewrites valid checksums.

A malformed/partial final record retains the readable prefix and blocks mutation.
No automatic truncation, history deletion, or speculative append occurs. Use:

```powershell
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py history status 'C:\images'
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py history backup 'C:\images'
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py history verify 'C:\images'
python C:\BAT\image_caption_gender_fixer\image_caption_gender_fixer.py recover --dry-run --json
```

Backup copies preserve the entire raw history, including a damaged tail.
Keep journals, backups, corrected files, and raw history together while
investigating. If a tail was manually repaired from established evidence, verify
the resulting history before running mutating recovery. The program does not
authenticate manual repair or guess a missing event from a timestamp.

If history is unavailable, `undo --recover-from-backups TARGET` explicitly lists
the original-backup restoration and requires confirmation. It refuses an occupied
original name and preserves corrected files. This is recovery, not a fabricated
normal undo history. Prefer intact folder history whenever available.

## Sessions and owned artifacts

Session journals are schema-1 plaintext JSON under `runtime/state/sessions`.
Each item has an absolute local target hint, source hash, state, transaction ID,
and exact artifact ownership manifest. A resumed item is reanalyzed and reapproved;
old approval is never reused after proposal changes. Canceled current work is
resumable. Committed images are reconciled through folder history.

Artifacts record intent before creation, identity immediately after exclusive
creation, and hash after completion. Cleanup checks exact path/name, identity,
and hash. Partial/changed/ambiguous artifacts remain visible in diagnostics.
No wildcard cleanup adopts a foreign file. Comparisons use the same ownership
tracking as ordinary masks/crops/staging.

Forgetting first checks for interrupted image transactions, then recycles exact
uncommitted artifacts and the session. Failed recycling leaves the session
discoverable. Committed outputs, original backups, history, rules, preferences,
and pending source files remain. Moved live-job paths need explicit inspection;
the program does not search disks or promise cross-computer job portability.

## Locking, capacity, and filesystem limits

The folder's hidden `.icgf.lock` has an application signature and an OS byte-range
lock. Another installation using that folder coordinates on the same file.
Process death releases the OS lock; no age-only PID stealing or lock deletion
is needed. Read/delete leases allow safe renames while excluding active writers.
Source and local-state volume capacity are checked before protected mutations.
Kernel file/attribute/move APIs use Windows extended path syntax.

Reparse points, occupied destinations, changed content/identity, unavailable
writes, locking failures, and ambiguous state stop the affected operation.
Network paths require explicit permission but cannot inherit an assumed local
durability or Recycle Bin guarantee. Unsupported recycling retains the item.
No `DeleteFile`, unlink/rmtree, shell delete, or copy/delete fallback disposes
of an original image, original backup, or corrected undo archive.

Runtime JSON state is replaced only after application/schema ownership checks;
this ordinary state maintenance is distinct from protected image replacement.
Developer edits to existing project files receive separately verified timestamped
replacement backups, with root-file backups archived under runtime/backups.

Logs under `runtime/logs` contain operation/ID/state/code information without
target paths or OCR/rule content. Sanitized crash reports under
`runtime/crash-reports` omit exception strings and variable values. Nothing is
uploaded. Physical storage failure and deliberate external tampering cannot be
made recoverable by software promises; preserve established evidence.
