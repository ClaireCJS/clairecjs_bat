# audit_music_batch — active installation

The active source is now `C:\BAT\audit_music_batch`. The older sandbox copy is not the development target.

Run `C:\BAT\audit_music_batch.bat` from your music directory, with the same arguments as before. The launcher preserves the working directory and propagates the exit code.

## v165 — safer batches, explicit retries, backup review

- Windows file-range locks now cover overlapping parent/child audit roots; siblings can run independently. Locks are coordinated under this user's TEMP directory and released by Windows on process exit.
- Interactive actions detect changed/deleted source files and folder changes while a proposal is displayed. Stale actions are rejected and can be retried after a fresh audit and approval. This is best-effort protection, not an atomic lock against unrelated programs.
- Folder-level Yes/No, missing-album skips, and selected genres survive an explicitly resumed batch. Starting fresh does not inherit them.
- Failed actions, ReplayGain bakes, and waveform reviews offer an optional failure-only retry. Successful work is not replayed. Each retry gets fresh checks; no automatic retry loop.
- At the end of interactive runs, backup count and storage usage are shown. Optional cleanup requires a preview and separate confirmation, rechecks the listed backups, and uses the Recycle Bin only. Unresolved failures suppress cleanup to preserve recovery copies.
- New isolated tests cover hierarchical locking, stale proposals, resumed decisions, retries, cleanup confirmation, and multichannel FLAC plus malformed metadata under long Unicode paths. Existing interruption tests remain in the recovery suite.

Validation: the external suite passes. The legacy inline `--unit-tests` suite has 23 pre-existing failures also reproduced in the unchanged v164 snapshot; it is not a clean release gate. Run it with `py -3 -X utf8 -B audit_music_batch.py --unit-tests --no-pager` when output is redirected on Windows.

## v164 — single active Python file

The audit-specific runtime is now included in `audit_music_batch.py`; no separate runtime module is needed. The safety behavior below is unchanged.

## Safety checks

- Windows file locks block concurrent modifying audits of the same resolved root and overlapping parent/child roots. Windows releases locks when their owner exits or crashes.
- Before baking, check room for four source-sized copies plus 64 MiB and probe exclusive read/write access. Recheck before replacement. This is a best-effort preflight, not a guarantee against another program locking the file or consuming space afterward. Failure skips the file without starting its bake.
- Recovery tests verify family rename round trips for audio, lyric sidecars, backup suffixes, playlists, waveform approvals, and before/after caches. Injected mid-rename failure verifies rollback. No music-library files are used.
- SQLite contexts now close explicitly, preventing persistent database-file locks.
- Resume remains optional. Recovery journal inspection: `audit_music_batch ROOT --show-batch-journal --no-pager`. Recycle Bin restoration and recovery from interrupted operations remain manual; this is not automatic undo.

Run the focused suite from this directory with:

```
py -3 -B -m unittest discover -s tests -p "test_*.py"
```

Tests leave new safety-test scratch directories in TEMP for inspection.

## Layout

- Root: active `audit_music_batch.py`, `README.md`, and `AGENTS.md` only.
- `tests/`: regression and integration tests; run discovery from the project root.
- `releases/v163/`: named release snapshot and its matching runtime, runnable independently.
- `releases/v164/`: single-file release snapshot. The historical v163 runtime stays with v163 only.
- `releases/v165/`: safer batch/retry/backup-review snapshot.
- `backups/`: archived replacement backups. Create and verify required sibling backups before edits, then archive them here without overwriting existing files.
- `tools/`: compatibility-launcher source.

Keep future tests, snapshots, and support files in these subfolders rather than adding them to the root. The external BAT launcher remains in C:\BAT and does not change the caller's working directory.
