@set                                                            NUM_ROWS_TO_SCROLL=%@EVAL[%_rows+10] 
@if defined ANSI_COLORS_HAVE_BEEN_SET (@echos %@ANSI_MOVE_DOWN[%NUM_ROWS_TO_SCROLL%]) else (@repeat %NUM_ROWS_TO_SCROLL% echo.)
@echos %@char[27][1J%@CHAR[27][0H%@CHAR[27][0G
@quit

:DESCRIPTION: Replacement for the 'cls' command, necessary due to bugs in the interaction between TCC & Windows Terminal


rem 2024/05: Certain ansi codes such as the DEC double-height codes get "stuck" using this method, so it's best to also manually scroll away the old content first:
                rem 2024/12: Re-verified when I lowered from 100 rows scrolled to 10...and immediately had weird problems with double-height lines being stuck

        @set     NUM_ROWS_TO_SCROLL=%@EVAL[%_rows+10] 
        rem This was slow: @repeat %NUM_ROWS_TO_SCROLL% echo.        
        rem But this wasn’t:
        if defined ANSI_COLORS_HAVE_BEEN_SET (@echos %@ANSI_MOVE_DOWN[%NUM_ROWS_TO_SCROLL%]) else (@repeat %NUM_ROWS_TO_SCROLL% echo.)

rem or do it with ansi:

rem vefatica says: There are easier ways these days. Below, EMIT is WriteConsoleW to a CONOUT$ handle. Nothing special about EMIT/CONOUT$. You can do these with ECHO, Printf, ... .
rem                 Scroll to empty window: EMIT(L"\x01b[2J\x01b[H");
rem                 Clear everything: EMIT(L"\x1b[2J\x1b[3J\x1b[H");
rem                 Clear just the window. EMIT(L"\x1b[H\x1b[0J");
        rem echos %ANSI_ESCAPE%H%ANSI_ESCAPE%0J


rem Clear the screen the legacy way, which has become insufficient in a post-Windows Terminal world —— but do 
rem this last so that if any of the previous stuff doesn't work, we're left with something resembling normalcy
rem 2024/2025: We decided to suspend this method to test the other methods
        rem *cls

rem 20241209: Let’s try something different to accomodate our ANSI status bars —— but I really wish I’d explained in this comment exactly what it is I’m doing:
        echos %@char[27][1J%@CHAR[27][0H%@CHAR[27][0G


