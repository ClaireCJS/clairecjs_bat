# PAFPlayer V467

- Fixed the web Progress Bar control crash.  `progress_color_mode` is now shared
  correctly by the live web-control handler, so both the Demo switch and turning
  the progress bar off can publish their updated state safely.
- Restored the familiar recycle control beside each Fav/Def pair: Fav and Def are
  stacked, the ♻️ button is immediately to their right, and it again has the
  persistent hover tooltip explaining favorite, sequential, and default cycling.
- Updated the focused regression contract so this shared-progress-state bug is
  caught by tests.
