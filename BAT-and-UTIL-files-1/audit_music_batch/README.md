# audit_music_batch — active installation

The active source is now `C:\BAT\audit_music_batch`. The older sandbox copy is not the development target.

Run `C:\BAT\audit_music_batch.bat` from your music directory, with the same arguments as before. The launcher preserves the working directory and propagates the exit code. The old `C:\BAT\audit_music_batch.py` command forwards here for compatibility.

## v164 — single active Python file

The audit-specific runtime is now included in `audit_music_batch.py`; no separate runtime module is needed. The safety behavior below is unchanged.

## Safety checks

- A Windows mutex blocks concurrent modifying audits of the same resolved root. Windows releases it when its owner exits or crashes. Different roots are independent; overlapping parent/child audits are not covered.
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
- `backups/`: archived replacement backups. Create and verify required sibling backups before edits, then archive them here without overwriting existing files.
- `tools/`: compatibility-launcher source.

Keep future tests, snapshots, and support files in these subfolders rather than adding them to the root. The external BAT launcher and legacy Python entry point remain in C:\BAT and do not change the caller's working directory.
