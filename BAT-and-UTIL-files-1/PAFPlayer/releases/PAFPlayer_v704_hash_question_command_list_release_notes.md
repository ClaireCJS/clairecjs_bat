# PAFPlayer V704 release notes

`#?` now lists the named hash commands just like `#commands`. The existing
hash-command input buffer accepts the question mark, and the command table and
manual both document the shortcut.

## Verification

- Embedded `PlayWaveFileTests.test_v704_hash_question_opens_command_list` passed.
- Active `PAFPlayer.py` was syntax-compiled without writing bytecode.
