@Echo OFF

echos %faint_on%Getting lyrics...%faint_off%%@ANSI_MOVE_TO_COL[0]

echos %ANSI_CURSOR_INVISIBLE%


@((eyed3 %* | sed -e "s/Lyrics:/%ansi_color_important%Lyrics:/g" -e "s/UserTextFrame/%ANSI_COLOR_RESET%UserTextFrame/g"     -e "/Lyrics/,/UserTextFrame/ { /^Lyrics:/b; /^UserTextFrame/b; s/^/%ansi_color_important%LYRICS: / }"  |:u8 *grep LYRICS: |:u8 *grep -v UserTextFrame |:u8 *grep -v Lyrics:) |:u8 fast_cat ) |:u8 fast_cat

echos %ANSI_CURSOR_VISIBLE%
