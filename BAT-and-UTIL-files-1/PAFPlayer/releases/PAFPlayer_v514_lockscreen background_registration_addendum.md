# V514 release addendum — 2026-10-08

Final comparison against the pre-task V513 backup found the three release-label
changes made by this lock-screen task plus a separately added
`WEB_SERVER_HOST = "0.0.0.0" # No, listen to anybody!` setting. That setting was
already present when work resumed on 2026-10-08; it was preserved, not introduced
by the lock-screen changes. The release snapshot and bundle contain it.

The original release notes' “main player changes are three release constants
only” describes this task's edits; it must not be read as an exhaustive diff
against V513. The bundled guide's stronger statement was inaccurate. The current
guide is corrected. Existing release artifacts remain unchanged, with this
addendum recording the clarification. Native lock-screen display is still
unresolved. No literal C:\BAT paths changed.
