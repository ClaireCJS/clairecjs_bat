"""Deterministic 6,000-slot transition diagnostic; does not play audio."""
from pathlib import Path
import json
import statistics
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import PAFPlayer as player


def run(track_count=6000, transitions=2000):
    order=[Path(f"track-{i:05}.flac") for i in range(track_count)]
    current=order[0]; selection=[]
    with __import__("unittest.mock").mock.patch.object(Path,"is_file",return_value=True):
        started=time.perf_counter()
        for _ in range(transitions):
            phase=time.perf_counter()
            successor=player.predict_playlist_successor_for_prefetch(
                order,current,shuffled=True,is_recent=lambda _:False)
            selection.append((time.perf_counter()-phase)*1000)
            order=player.rotate_playlist_queue_after_play(order,current)
            current=successor
        total=(time.perf_counter()-started)*1000
    return {
        "playlist_tracks":track_count,"transitions":transitions,
        "selection_ms_median":statistics.median(selection),
        "selection_ms_p95":sorted(selection)[int(len(selection)*.95)],
        "preparation_ms":"requires real media; emitted by transition.prepare-consumed",
        "decoder_open_ms":"requires live playback; emitted by transition.decoder-start",
        "end_to_end_ms":"requires live playback; emitted by transition.decoder-start",
        "silence_between_tracks_ms":"requires live playback; emitted by transition.decoder-start",
        "prepared_ready_before_previous_ended":"requires live playback trace",
        "synthetic_total_ms":total,
    }


if __name__ == "__main__": print(json.dumps(run(),indent=2))
