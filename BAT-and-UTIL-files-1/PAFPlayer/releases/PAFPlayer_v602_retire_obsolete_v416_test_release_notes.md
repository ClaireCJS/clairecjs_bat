# PAFPlayer V602 release notes

The obsolete `tests/test_play_audio_file_v416.py` test was sent to the Windows
Recycle Bin. It imported the unavailable `play_audio_file` module and could
not run. PAFPlayer playback code is unchanged apart from the version number.

The current V601 global-seek and audio-worker tests remain in place.
