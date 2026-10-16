# PAFPlayer V427 — attribute-rule alternation repair

- Fixed the global attribute-list parser for rules written with a terminal `|:` separator.
- Before this fix, the retained terminal `|` created an empty regex alternative that matched every song. That incorrectly applied `instrumental(s)`, `chiptune(s)`, and `sound effect(s)` to unrelated tracks.
- The parser now removes only that delimiter-adjacent terminal pipe, preserving normal regex alternatives and the existing shared `mp3-base-attributes.lst` file unchanged.
- Added a focused regression test; a direct evaluation of the previously affected Freezepop file now yields only its ordinary playlist tags.
