@Echo OFF
 on break cancel

:DESCRIPTION: Replacement for the 'cls' command, necessary due to bugs in the interaction between TCC & Windows Terminal




rem 2024/05: However, certain ansi codes such as the DEC double-height codes get "stuck" using this method, so it's best to
rem          also manually scroll away the old content first:

        repeat 250 echo.



rem vefatica says: There are easier ways these days. Below, EMIT is WriteConsoleW to a CONOUT$ handle. Nothing special about EMIT/CONOUT$. You can do these with ECHO, Printf, ... .
rem                 Scroll to empty window: EMIT(L"\x01b[2J\x01b[H");
rem                 Clear everything: EMIT(L"\x1b[2J\x1b[3J\x1b[H");
rem                 Clear just the window. EMIT(L"\x1b[H\x1b[0J");
        echos %ANSI_ESCAPE%H%ANSI_ESCAPE%0J


rem Clear the screen the legacy way, which has become insufficient in a post-Windows Terminal world —— but do 
rem this last so that if any of the previous stuff doesn't work, we're left with something resembling normalcy
        *cls

