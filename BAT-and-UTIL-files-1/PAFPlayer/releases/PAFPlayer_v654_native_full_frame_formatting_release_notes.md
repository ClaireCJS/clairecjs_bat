# PAFPlayer V654 — native full-frame artwork formatting

Released November 11, 2026. SHA-256: `a26c04407993622f543c5786e2c611113f70baa6b768297914545582c0181776`.

The user confirmed that V653 removed about 95% of the visualizer hitching but
tiny hangs remained during ordinary playback. The new V653 trace caught a
243 ms diagnostic delay near a full garbage collection. Three minutes of live
sampling reported 45.8–55.4 FPS toward 60, no popup backlog, and zero audio
underruns. Private memory ranged from 1.470 to 1.510 GB, ending at 1.498 GB.
This is a short observation, not proof of long-term stability or frame latency.

## Change

The artwork compositor already produced packed cells in native code, but the
full-frame path still iterated over every cell in Python to format foreground
and background terminal color strings. V654 reuses the existing native artwork
encoder for that step, then restores the original row strings exactly. Temporary
native cursor prefixes are stripped in memory; the existing caller still owns
all row positioning, wrapping, line erasure and character-set resets.

Semantic-only rendering still bypasses string encoding. Missing NumPy/native
support, invalid dimensions, native errors or malformed output retain the old
Python formatter. No new native binary, dependency, setting, frame target, audio
change, GC policy, or reduced image precision was introduced. V653 features and
V652's memory-retention fixes remain intact.

## Evidence

The repeat benchmark formats 200 dynamic 140×48-cell frames with the same output
digest: **5.503 ms/frame before, 0.657 ms/frame after**, about 8.4× faster for this
step. The old path triggered 12 generation-0 and one generation-1 collections;
the new path triggered none during that measured interval. These are isolated
formatting timings, not end-to-end FPS or proof that every hitch is eliminated.
Alternative integer/string cache keys were rejected because they slowed this
workload by 22–24%, despite reducing collections.

- [Production benchmark](../tests/reports/full-frame-native-20261111-102649.json)
- [V653 live stack trace](../tests/reports/v648-thread-stacks-20261111-101441.json)
- [V653 three-minute sample](../tests/reports/v652-live-retention-V653-20261111-101837.json)

All **eight new tests pass**, including 128 flag combinations, default flags,
multiple dimensions, repeated colors, semantic-only output, missing dependencies,
errors, malformed native output and empty/uneven rows. Full payloads, row strings
and semantic cells match the immutable V653 oracle exactly. The 115-test group
has 113 passes and two pre-existing media-coordinator failures. The 188-test group
has 176 passes, 11 failures and one source-contract error, matching its baseline.
Python compilation, 27 embedded/source comparisons and eight generated JavaScript
syntax checks pass. The suite is not wholly green.

- [Focused/relevant checks](../tests/reports/v654-checks-V654-20261111-102553.json)
- [Broad checks](../tests/reports/pipeline-regressions-V654-20261111-102652.json)

## Manual verification

Restart the usual PAFPlayer.py with console karaoke, artwork popup and floating
lyrics enabled. Check ordinary animation, lyric-gap layout changes, the rightmost
artwork cells, frame position and glyph shapes. Verify that audio stays smooth.
Live V654 verification and a multi-hour memory observation remain pending.

The native ABI rejected a zero-length origin during the initial offline
experiment; the tested implementation supplies a temporary nonempty origin and
removes it before output. No experimental payload was sent to the live console.

Verified sibling backups are retained. Prior releases are preserved and no files
were permanently deleted. play_audio_file.py was not modified. No literal
C:\BAT path changed. [All affected paths](../tests/reports/v654-change-manifest.json).
