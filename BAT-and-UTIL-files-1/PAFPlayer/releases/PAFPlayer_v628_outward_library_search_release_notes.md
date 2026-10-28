# PAFPlayer V628 — outward search without a full-library filelist

Released October 27, 2026.

- The queueing guide now has separate `-qa` and `-qe` rows: `-qa` places tracks immediately after the current song, while `-qe` appends them at the playlist end. Both override the saved placement for one request.
- The table explains that an existing file or folder remains a path, while a nonexistent argument with a regex signal such as `.*`, or an explicit `re:PATTERN`, searches the player library.
- If the configured full-library filelist is absent and indexed tracks, the active queue, and configured roots cannot match a selector, PAFPlayer scans supported audio from the invoking folder and then outward through sibling branches of up to four parent folders. The scan examines at most 25,000 entries. A remote folder hint works only when that path is accessible on the player computer; otherwise its current folder is used.
- Direct, existing audio paths and matches already in the player library avoid the outward scan. The background full-library filelist builder is unchanged.
- The web configuration note describes this fallback.

Verification: focused outward-search tests, existing enqueue and IPC tests, Python compilation, source/bundle parity, and active/release copy hash parity. A bounded search can miss files beyond its limit; configuring a complete `everything.m3u` remains the reliable full-library route.
