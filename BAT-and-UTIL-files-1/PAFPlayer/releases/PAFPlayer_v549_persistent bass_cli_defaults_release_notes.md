# PAFPlayer V549 — persistent bass CLI defaults

- `--bass-reduction-while-locked=on|off` now persists the checkbox setting and
  applies it during the current run.
- Bare enable/disable switches remain deliberately session-only.
- `--default-bass-reduction-percent-while-locked=0..100` saves the percentage
  restored by default actions. The factory-reset value remains 50%.
