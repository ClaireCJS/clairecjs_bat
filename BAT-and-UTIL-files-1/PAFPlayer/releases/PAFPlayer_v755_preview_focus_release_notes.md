# PAFPlayer V755 — preview audio focus and bottom-row spacing

The visualizer uses one bottom safety row instead of two, retaining explicit cursor movement without drawing the hazardous bottom-right cell.

Simple previews now request acknowledged pauses from the main player and other previews before starting their decoder. Authenticated loopback coordination works with the web server disabled and keeps the official single-instance ownership separate. Pause leases preserve previously paused state, support nested previews and expire after a crash. Graceful exit releases requests and archives peer descriptors. Restart running players once to enable participation.

Validation: focused HTTP coordination, real disabled-web transport queue acknowledgement, nested and out-of-order preview release, prior pause state, authentication, failure recovery, bundle parity, existing simple-mode and speed tests, and the embedded viewport geometry regression. Tests simulate transport state without interrupting the user's live music.
