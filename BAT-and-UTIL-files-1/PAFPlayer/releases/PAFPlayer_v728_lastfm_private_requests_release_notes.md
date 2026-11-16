# PAFPlayer V728 — Last.fm in the private runtime

Pin Requests 2.34.2 and its resolved HTTP dependencies in `requirements-core.txt` and include them in the app-owned Python runtime. This fixes Last.fm Now Playing and scrobbling when PAFPlayer runs through `pafplayer.bat`.

The installed runtime was updated in place with the pinned packages and its runtime manifest. The private interpreter imports Requests and its full dependency set; the personal Anaconda Python was not changed by this update.
