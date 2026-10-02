# PAFPlayer V471 — live screen-lock bass transition

This release follows V470’s persistent Discord and bass-control setup.

- When “Reduce bass when screen is locked” is enabled, PAFPlayer now checks the Windows lock state once per second and restarts FFplay at the current playback position when locking or unlocking. This applies or removes the configured low-shelf reduction immediately after the transition.
- The version identifiers now correctly distinguish this post-V470 behavior from the original V470 snapshot.
