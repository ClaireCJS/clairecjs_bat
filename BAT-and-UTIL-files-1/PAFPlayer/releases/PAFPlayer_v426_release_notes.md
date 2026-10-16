# PAFPlayer V426 — audible VLC resume

- Fixed automatic resume after VLC closes: a Core Audio session without a Windows media-transport session must now be audibly producing audio before it pauses or continues to hold PAFPlayer.
- Preserved media-session-based pause behavior for applications that report `Playing` through Windows transport controls.
- The live trace showed VLC's inactive Core Audio session persisting after the process closed; this release prevents that silent residue from blocking the 1.5-second automatic-resume timer.
