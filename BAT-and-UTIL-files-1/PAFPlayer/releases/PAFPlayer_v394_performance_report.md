# V394 console visualizer performance

Measured on 2026-09-07 using `C:\ProgramData\anaconda3\python.exe` (Python 3.10.9), the same interpreter used by the running player.

The live V393 player reported roughly 21–30 FPS with 32 rows, Twin DRCS, Signal Aurora processing, and mode 13 background artwork at 30% strength. Its generation time was approximately 26–29 ms in these samples, plus approximately 2 ms for terminal transport. These live samples and the synthetic benchmark below have different bar patterns and are not interchangeable.

## Change

V394 calculates each bar column's partial-fill boundary and row-independent color once per frame. Fully filled and empty cells then reuse their glyph/color data. Static artwork cells also cache their SGR sequences, Unicode/DRCS classification, and absolute cursor fences. These identity caches hold their source objects, are bounded to four artwork grids, and refresh with artwork, strength, dimensions, character mode, fence configuration, or DRCS-bank changes.

The same frame contents, artwork resolution, terminal protections, configured row count, and web payload are preserved. Row-dependent color processors and artwork blended into bars retain their existing rendering path. The greatest speedup applies to the measured background-artwork setup.

## Warm renderer benchmark

Sixty moving spectrum frames follow eight warm-up frames for each build and size. Each frame changes its bar heights. The fixture uses a deterministic, detailed RGB grid, a mode 13 artwork background, 30% strength, row-delta output, and the normal two bins per terminal column. Timing excludes initial artwork conversion and real terminal I/O.

| Console size | V393 median | V394 median | V394 p95 | Generation speedup |
| --- | ---: | ---: | ---: | ---: |
| 200 columns × 32 rows | 38.68 ms | 6.85 ms | 7.29 ms | 5.64× |
| 240 columns × 32 rows | 46.92 ms | 8.22 ms | 8.67 ms | 5.71× |
| 200 columns × 48 rows | 57.20 ms | 8.85 ms | 9.31 ms | 6.46× |

60 FPS allows 16.67 ms for the complete frame. The measured generation times leave room for terminal transport and other player work, but are not measurements of V394's actual playback FPS. The running V393 process must be restarted to load this code. The existing `--visualizer-target-fps=60` option can select a 60 FPS target; the default target and adaptive governor are unchanged.

## Verification

- Four differential test groups compare exact ANSI payloads, row strings, RGB captures, and cell captures against the preserved V393 snapshot.
- Cases cover eleven artwork modes, 1–96 rows, cropping, volume brightness, top-blank karaoke columns, all three granularities, bar-art fallback modes, changing strengths, Unicode fences, and DRCS-bank changes.
- Fill boundaries include half-step rounding ties and their immediately neighboring floating-point values.
- Seven existing geometry, microtile, charset, cursor-fence, and atomic-bank-transition regression tests pass.

Reproduce from the workspace with:

```powershell
& 'C:\ProgramData\anaconda3\python.exe' -B test_play_audio_file_v394_rendering.py
& 'C:\ProgramData\anaconda3\python.exe' -B test_play_audio_file_v394_rendering.py --benchmark --profile
```

The benchmark uses the user's preserved snapshot `play_audio_file_v393_console_visualizer_art_hot_path_VUSIZLIER_AT_30FPS.py` as its baseline.
