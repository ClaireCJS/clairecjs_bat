from clairecjs_utils.claire_winamp import *

w = initialize_and_get_winamp_object()

while True:
    status = w.get_playing_status()
    if status == PlayingStatus.Paused or status == PlayingStatus.Stopped and not cleared:
        previous_track = ""
        cleared = True
    elif status == PlayingStatus.Playing:
        update_rpc()
    time.sleep(1)
    artist, title, trackinfo_raw = w.get_artist(), w.get_title(), w.get_trackinfo_raw()
    print(f"\ntrackinfo_raw = {trackinfo_raw}\n       artist = {artist}\n       title  = {title}")
