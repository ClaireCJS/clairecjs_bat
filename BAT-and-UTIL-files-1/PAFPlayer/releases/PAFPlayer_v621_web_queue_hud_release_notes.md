# PAFPlayer V621 — web queue activity on the console HUD

The third HUD detail line now briefly reports queue and clear requests accepted
through the web playlist and remote-control queue callback. V620 already
reported single-instance enqueue requests and owner transport controls. These
short messages omit media paths and leave the underlying playback queue logic
unchanged.

V620's direct-file enqueue, library filelist setting, missing-filelist search,
startup handoff wait, and clearer two-track enqueue receipt remain available.
