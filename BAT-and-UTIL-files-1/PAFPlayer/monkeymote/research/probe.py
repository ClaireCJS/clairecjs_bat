"""Explicit, 15-minute iPad interoperability probe; no real playback commands."""
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from PAFPlayer_monkeymote import Listener, validate_config


class Probe:
    def __init__(self):
        self.started = time.monotonic()
        self.paused = False
        self.volume = 50
    def owns(self):
        return True  # Test fixture; never imports/acquires PAFPlayer ownership.
    def snapshot(self):
        return dict(playing=True, paused=self.paused, volume=self.volume,
                    duration_seconds=180, position_seconds=(time.monotonic()-self.started) % 180,
                    metadata={'Artist': 'PAFPlayer protocol test', 'Song': 'MonkeyMote connection test',
                              'Album': 'Sample data - no playback'}, track={})
    def playlist(self):
        return ['MonkeyMote connection test', 'Second sample track'], 0
    def playlist_token(self):
        return ('sample-one', 'sample-two')
    def play_selected(self, token, index):
        return token == self.playlist_token() and 0 <= index < 2
    def media_revision(self):
        return (0, 0)
    def media(self, kind, index=0xffffffff):
        from PAFPlayer_monkeymote import packet, media_packet
        return packet(13) if kind == 'art' else media_packet(36, b'', bytes(16))
    def command(self, command, value=0):
        if command == 1: self.paused = False
        elif command == 2: self.paused = not self.paused
        elif command == 6:
            from PAFPlayer_monkeymote import volume_percent
            self.volume = volume_percent(value)
        return command in (1, 2, 6, 8, 9)


if __name__ == '__main__':
    host, subnet, report = sys.argv[1:]
    config = validate_config(dict(enabled=True, host=host, trusted_subnet=subnet))
    with Path(report).open('x', encoding='utf-8') as output:
        def observe(event, **values):
            line = json.dumps(dict(event=event, elapsed=round(time.monotonic()-start, 3), **values))
            output.write(line+'\n'); output.flush()
            print(line, flush=True)
        start = time.monotonic()
        listener = Listener(Probe(), config, observe).start()
        print('TEST FIXTURE listening on '+host+':19371; no playback access; expires after 15 minutes.', flush=True)
        try:
            while time.monotonic()-start < 900:
                time.sleep(.5)
        finally:
            listener.close()
