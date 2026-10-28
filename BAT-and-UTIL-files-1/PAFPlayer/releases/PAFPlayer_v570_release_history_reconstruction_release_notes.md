# PAFPlayer V570 — historical release index and root cleanup

October 17, 2026. This is a documentation and file-organization release. Playback code is unchanged apart from the version string.

- Rebuilt `PAFPlayer_changelog.md` as one descending entry per number from V1 through V570, retaining detailed historical text and merging two reused identifiers (V526 and V527) without discarding either record.
- Inspected numbered source, Markdown release documents, and replacement backups in `C:\BAT\PAFPlayer\releases`; new entries distinguish archived notes, source-filename clues, ambiguous internal version labels, and numbers with no trustworthy release artifact.
- Updated the main manual and documentation index; archived stray replacement backups from the workspace root and moved its generated playlist-analysis report to `tests/reports`.
- The historic `C:\BAT` release archive was read for evidence, not rewritten or copied wholesale. No client or playback behavior is changed.

## Verification

Validated one V570–V1 heading per number in descending order, the V570 source version, release-copy equality, compilation without bytecode output, and backup hashes. The historical descriptions have different confidence levels as labeled in the changelog; filename-derived entries are not independently verified feature claims.
