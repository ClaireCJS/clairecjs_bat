# PAFPlayer V623 — enqueue search preview

Released October 26, 2026.

- Regex enqueue prints a live status immediately while the official player searches its library. The temporary status line clears when the result arrives in an interactive terminal.
- Matching filenames appear under each folder heading once, with alternating soft colors where the terminal supports ANSI color. Output without ANSI remains readable.
- Up to 20 matches queue after the preview. At 21 or more, the first 20 are shown and the user must explicitly choose **Y** to enqueue all; **L** lists every match, while **N** or Enter cancels. Noninteractive input cancels a large request without changing the queue.
- The official player resolves regexes only once. A one-use, ten-minute preview token carries the resolved paths to the commit, which verifies they still exist. Local IPC and the remote `--server` API both preserve official-instance ownership and the V622 `-qa`/`-qe` placement override.
- Direct file requests also announce that resolution and enqueue are in progress. Small direct requests retain one network or IPC round trip.

Verification: focused V623 preview tests, related enqueue/IPC/workflow regression suites, Python syntax checks, and bundled-source/release parity. The running player must be restarted to load V623. Extremely large previews are rejected with a request to narrow the search, and a failed or interrupted commit may already have been accepted; check the official queue before retrying.
