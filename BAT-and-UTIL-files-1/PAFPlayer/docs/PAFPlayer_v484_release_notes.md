# PAFPlayer V484 release notes

- Restored instant Ctrl+Break cleanup: reset DEC double-height text, restore
  terminal state, home, and erase through the end of the screen before any
  cleanup that could wait.
- Console aborts no longer perform normal workflow shutdown joins after the
  fast path, avoiding delayed exit on instance-server or HTTP cleanup.
