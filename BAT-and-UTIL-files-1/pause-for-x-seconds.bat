@echo off

rem Quick short circuit if our time-wait is 0 (for whatever reason):
        if "%1" eq "0" goto :Abort

rem Validate the parameters
        set                       SECONDS=%1
        call validate-env-var     SECONDS     "Must provide number of seconds to pause when invoking %0 ... And optional 2nd parameter of your pause message"
        call validate-is-number  %SECONDS%

rem Set up the pause text
        set                PAUSE_MESSAGE=Press any key when ready...
        if "%2" ne "" (set PAUSE_MESSAGE=%@UNQUOTE[%2])

rem Set the colors (two redundant methods):
                   %COLOR_PAUSE%
        echos %ANSI_COLOR_PAUSE%

rem Clear the character buffer so we don't end up hitting a key BEFORE the prompt and have it be counted as after:
        repeat 100 @input /c /w0 %%This_Line_Clears_The_Character_Buffer

rem Do the actual pause:
        *pause /W%SECONDS% /T %PAUSE% %PAUSE_MESSAGE% 

:Abort
