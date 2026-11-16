# PAFPlayer V699 — HUD timing and warning history

## Behavior

- Ordinary HUD notices now remain visible for twice their requested duration.
- HUD warnings remain visible until the current song changes.
- Warning conditions that remain active are eligible to reappear every tenth
  song; conditions that stop being reported are removed from the schedule.
- Lowercase `w` keeps its existing SIXEL visualizer meaning. **Shift+W** opens
  a modal warning screen containing active track conditions, current persistent
  HUD warnings, and unresolved runtime warning summaries.

## Verification

- Embedded `PlayWaveFileTests.test_v699_hud_warning_schedule_and_shift_w_history`
  covers the ten-song cadence, condition removal, key mapping, and notice-duration
  contract.
- The active player compiles successfully.
