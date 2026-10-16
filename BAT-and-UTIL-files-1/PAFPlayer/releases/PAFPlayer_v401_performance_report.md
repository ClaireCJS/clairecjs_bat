# V401 visualizer bar artwork performance

Measured on 2026-09-08 with `C:\ProgramData\anaconda3\python.exe` (Python 3.10.9, NumPy 2.2.6). The existing V400 player was left running during the measurements. Its read-only status endpoint confirmed Twin DRCS, Signal Aurora (62), 32 rows, detail mode 9 for both artwork layers, 100% bar strength, luma blending (1), and 30% background strength.

## Change

- Batch full-cell and partial/non-microtile artwork RGB arithmetic with the same optional NumPy dependency used for FFT analysis. Preserve the existing operation order, round-to-even behavior, strength precision, tall-layout quantization, and volume-flash brightness.
- Cache static artwork arrays and luminance coefficients, retaining the source objects and bounding the cache to four entries.
- Pack computed RGB into byte rows instead of thousands of temporary Python lists, avoiding allocation-driven frame spikes.
- Classify fully filled/empty terminal columns once per frame and skip unnecessary half-cell setup on those rows.
- Format filled artwork cells directly from packed RGB and retain exact color-sequence suppression across full, partial, and empty runs.

Artwork detail, color precision, cursor fences, charset transitions, row counts, target FPS, and transport settings are preserved. Row-dependent processors and installations without NumPy retain the scalar fallback. No new package installation is required on this machine.

## Moving-frame benchmark

Each case measures 72 frames after eight warm-up frames, changing both heights and energy/color inputs on every frame. Timing includes full-frame ANSI generation but excludes initial artwork conversion and terminal I/O. Unlike the older V397 benchmark, the color inputs also change on every measured frame, so static blend-cache hits cannot hide the color-processing cost. V400 is the preserved `play_audio_file_v400_help_output_endpoint_details.py` snapshot.

| Layout | Artwork detail | V400 median | V401 median | V401 p95 | Speedup |
| --- | --- | ---: | ---: | ---: | ---: |
| 200 columns × 32 rows | 9 | 49.79 ms | 13.52 ms | 15.35 ms | 3.68× |
| 240 columns × 32 rows | 9 | 61.84 ms | 17.88 ms | 23.51 ms | 3.46× |
| 200 columns × 48 rows | 9 | 77.99 ms | 19.05 ms | 22.68 ms | 4.09× |
| 200 columns × 32 rows | 13 | 47.90 ms | 12.75 ms | 14.24 ms | 3.76× |

60 FPS permits 16.67 ms for the entire frame. The 200×32 median generation times fit that budget, but larger stress cases still exceed it. These are renderer benchmarks, not measured V401 playback FPS. Real playback also holds color inputs to its existing 30 Hz analyzer cadence, while updating bar geometry more frequently. Restart PAFPlayer to load V401 and measure end-to-end FPS with the actual artwork, console dimensions, and terminal transport.

## Verification

- Seven new V401 test groups pass: direct scalar-versus-array RGB comparisons, exact ANSI/row/RGB/cell output, all three blend modes, ten artwork detail modes, optional-NumPy fallback, row-dependent and monochrome fallback, layer toggles, crop/resize, small/fractional strengths, brightness feedback, fill rounding ties and neighboring floats, and equal-color run boundaries.
- The V397 bar-art differential suite and all four V394 renderer differential groups pass.
- Seven focused existing rendering tests pass, including cursor fences, fixed-cell DRCS, wrap-safe row output, adaptive artwork banks, and atomic bank/frame changes.
- One selected legacy test, `test_v380_renderer_switches_charset_per_hybrid_cell_only`, fails because it searches the source for a call written on one line, while that call has used multiple lines since before this change. Confirmed the same failure in untouched V400. Exact-output tests cover the charset behavior.
- Source and version snapshot compile and have matching SHA-256 hashes.
- The user's intervening `die` emoji edit is preserved. No files under `C:\BAT` were changed.

Reproduce from the workspace:

```powershell
& 'C:\ProgramData\anaconda3\python.exe' -B -X utf8 test_play_audio_file_v401_bar_art.py
& 'C:\ProgramData\anaconda3\python.exe' -B -X utf8 test_play_audio_file_v401_bar_art.py --benchmark --profile
& 'C:\ProgramData\anaconda3\python.exe' -B -X utf8 test_play_audio_file_v397_bar_art_performance.py
& 'C:\ProgramData\anaconda3\python.exe' -B -X utf8 test_play_audio_file_v394_rendering.py
```

Replacement backups were created and SHA-256 verified before every source/test overwrite. The original source for this operation is `play_audio_file.py.bak.202609081030.replaced-by-chatgpt.bak`.
