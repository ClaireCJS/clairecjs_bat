# PAFPlayer V750 — simple-mode global pause ownership

Simple previews now ignore Win+C, Pause/Break and Media Play/Pause when another player process is detected in the same Windows logon session. Native process inspection reads executable names and Python command lines, so it also recognizes older and explicitly launched instances. The probe excludes its own PID and the lock-screen companion. It does not acquire the official player mutex, forward controls or stop any process. An unreadable Python command line is treated conservatively as a possible competing player.

Both media-key polling paths and Win+C apply the rule at the press edge. Suppressed presses are latched until release, avoiding a delayed pause when another player exits while the key is held. Focused Space continues to control the preview. The normal player path skips process inspection entirely.

Validation includes competing-player and solitary-preview decisions, normal-player compatibility, focused Space and all three polling gates, source/bundle parity and a native process-inspection check.
