@Echo OFF

*cls

rem vefatica says: There are easier ways these days. Below, EMIT is WriteConsoleW to a CONOUT$ handle. Nothing special about EMIT/CONOUT$. You can do these with ECHO, Printf, ... .
rem                 Scroll to empty window: EMIT(L"\x01b[2J\x01b[H");
rem                 Clear everything: EMIT(L"\x1b[2J\x1b[3J\x1b[H");
rem                 Clear just the window. EMIT(L"\x1b[H\x1b[0J");


echos %ANSI_ESCAPE%H%ANSI_ESCAPE%0J

