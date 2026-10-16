# PAFPlayer V559 — instant console break

- Ctrl+C and Ctrl+Break restore the terminal before doing any other shutdown work.
- The decoder receives an immediate, non-waiting kill.
- Console interruption exits directly instead of waiting for tray, web, GUI, or
  media-integration teardown.
- The normal quit path remains orderly and unchanged.

See [the performance note](../docs/performance-v559.md) for the exact fast-path
boundary.
