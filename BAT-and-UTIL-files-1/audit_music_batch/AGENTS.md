# Active project location

Work directly in C:\BAT\audit_music_batch. C:\codex\clairevironment\bat is an older workspace copy, not the active source.

Disclose every created, modified, or deleted C:\BAT file in the final response. Before replacing existing content, create and verify a sibling `<filename>.bak.YYYYMMDDHHMM.replaced-by-chatgpt.bak`; preserve collisions with ` (1)` before the final extension. Recycle deletions, never permanently delete. Preserve named version snapshots for releases.

Use the shared clairecjs_utils.claire_progressbar for rainbow progress. Do not create a replacement utility library here. Audit-specific runtime helpers are included in audit_music_batch.py; keep one active Python file at the root.

Run tests with `py -3 -B` to avoid deployment-tree bytecode artifacts. Do not run destructive tests against the music library.

## Release handoff disclosure

Whenever creating or updating a versioned program or release, explicitly state
the exact version number, the active runnable filename with a clickable absolute
path, and every newly created versioned runnable/release filename with clickable
absolute paths in the final response. Include the release-notes path when one
was created. Do this for every release, including small fixes and deployments;
do not report only a feature summary, folder, or version without filenames.
If only instructions or documentation changed and no application release was
created, say so explicitly; do not imply a new program version was released.
