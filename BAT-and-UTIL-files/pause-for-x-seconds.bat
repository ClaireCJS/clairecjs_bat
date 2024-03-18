@echo off

rem Validate the parameters
        set              SECONDS=%1
        call val-env-var SECONDS "Must provide number of seconds to pause when invoking %0 ... And optional 2nd parameter of your pause message"

rem Set up the pause text
        set                PAUSE_MESSAGE=Press any key when ready...
        if "%2" ne "" (set PAUSE_MESSAGE=%@UNQUOTE[%2])

rem Set the colors (two redundant methods):
                   %COLOR_PAUSE%
        echos %ANSI_COLOR_PAUSE%

rem Do the actual pause:
        *pause /W%SECONDS% /T %PAUSE% %PAUSE_MESSAGE% 

