# V744 lock-screen cadence verification

Date: 2026-11-20

- `python -B -m unittest discover -s lockscreen\testing -p test_managed_publisher.py -v`: 37 passed.
- `python -B -m unittest discover -s tests -p test_v724_remote_lockscreen.py -v`: 4 passed.
- `lockscreen\testing\test_desktop.ps1`: 89 passed; one existing obsolete-enum compiler warning.
- `python -B -m py_compile PAFPlayer.py lockscreen\src\PAFPlayer_lockscreen.py src\PAFPlayer_remote_lockscreen.py`: passed.
- Embedded `PAFPlayer_lockscreen` and `PAFPlayer_remote_lockscreen` source parity: passed through the focused tests.

Expected ordinary counter-driven notification rate:

- Before: up to 60 changed counter payloads per minute at one-second resolution.
- After: up to 12 changed counter payloads per minute at five-second resolution.
- Reduction: 80%.

Lyric selection remains based on the unrounded synchronized timestamp and the 250 ms lock-screen lead. Thailog was not reachable on port 666 from the development machine, so no claim is made about an observed end-to-end Windows rendering latency on that computer.
