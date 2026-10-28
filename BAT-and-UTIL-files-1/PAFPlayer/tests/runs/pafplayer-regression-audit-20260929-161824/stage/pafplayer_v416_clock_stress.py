"""Muted native EOF/read race reproduction and regression check."""
import concurrent.futures
import json
from pathlib import Path
import time

import play_audio_file as p
from pafplayer_v416_edit import unique

root = Path(__file__).resolve().parent
fixture = root / 'pafplayer_v416_timing_fixture.wav'
counts = []
for _ in range(12):
    command = [str(p.direct_ffmpeg_executable()), '-v', 'error', '-i', str(fixture),
               '-t', '0.12', '-af', 'volume=0', '-ar', '48000', '-ac', '2', '-f', 's16le', '-']
    process = p.MatrixMixerInspiredWaveOutProcess(command, 2, 48000, -1, 16, target_buffer_ms=100)
    def read_clock():
        count = 0
        deadline = time.monotonic() + 5
        while process.poll() is None and time.monotonic() < deadline:
            if process.playback_clock is not None:
                count += 1
            time.sleep(.001)
        # Reading after native Close must retain the final timestamp safely.
        final = process.playback_clock
        assert final is not None and .10 <= final['seconds'] <= .13, final
        assert final['queued_seconds'] == 0, final
        return count
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as readers:
            counts.extend(readers.map(lambda _: read_clock(), range(4)))
        assert process.poll() == 0, process._last_error
    finally:
        p.stop_process(process)

report = {'muted_tracks': 12, 'concurrent_clock_readers': 4, 'samples': sum(counts),
          'eof_clock_retained': True, 'access_violations': 0}
path = unique(root / 'pafplayer_v416_clock_stress.json')
path.write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report))
