# PAFPlayer V478 — floating lyrics center over visualizer

Added a Floating Lyrics control named **Center Over Visualizer**. It positions
the floating lyrics over the native console window that hosts the visualizer,
using the current lyric-window size. If the console rectangle is unavailable,
the existing monitor-centered placement is used as a safe fallback.

The existing **Bring to Center** and **Bring to Top** actions remain separate;
Always On Top does not prevent either action from being invoked.

Validation: Python compilation and focused V478 placement/control regression
tests passed.
