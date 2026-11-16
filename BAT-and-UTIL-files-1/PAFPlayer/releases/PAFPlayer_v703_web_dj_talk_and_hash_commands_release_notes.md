# PAFPlayer V703 release notes

## AI DJ web control

The AI DJ web configuration now has a **Talk Now!** button. It queues the same
forced `#djforce` action used by the console, through the authenticated local
DJ workflow endpoint. The button is disabled for non-local web viewers.

## Named console commands

The `#` prompt now resolves common named commands for playback transport,
volume entry and steps, speed, repeat, shuffle, randomization, looping,
playlist, warning history, URLs, visualizer and karaoke controls, artwork,
floating lyrics, SIXEL, FPS HUD, help, and quit. `#commands` gives a short
HUD reminder; the complete table is in `docs/PAFPlayer_hash_commands.md`.

## Verification

- Embedded `PlayWaveFileTests.test_v703_web_talk_now_and_hash_command_contract` passed.
- Active and release copies were syntax-compiled without writing bytecode.
- The editable `PAFPlayer_web_workflows.py` source was synchronized into the single-file bundle.
