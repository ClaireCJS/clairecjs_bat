# PAFPlayer V558 — global responsiveness optimizations

- Debounces superseded whole-library filesystem searches while typing.
- Coalesces repeated tray registry reads and invalidates them on saved changes.
- Limits tray hover snapshots to ten per second without changing hover delay.
- Reuses the Web Config tray-icon gallery instead of rebuilding 200 canvases on
  every status poll.
- Reuses the server's immutable 200-entry tray-icon catalog between requests.

See [the performance note](../docs/performance-v558.md) for scope and limits.
