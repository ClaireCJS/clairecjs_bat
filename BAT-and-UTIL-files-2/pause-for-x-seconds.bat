@Echo Off
@on break cancel
setlocal

rem Quick short circuit if our time-wait is 0 (for whatever reason):
        if "%1" eq "0" goto :Abort

rem Validate the parameters
        unset /q       PAUSE_FOR_X_SECONDS_SECONDS
        set            PAUSE_FOR_X_SECONDS_SECONDS=%1
        if not defined PAUSE_FOR_X_SECONDS_SECONDS call validate-env-var     PAUSE_FOR_X_SECONDS_SECONDS     "Must provide number of seconds to pause when invoking %0 ... And optional 2nd parameter of your pause message"
        call validate-is-number  %PAUSE_FOR_X_SECONDS_SECONDS%

rem Set up the pause text
        set                PAUSE_MESSAGE=Press any key when ready...
        if "%2" ne "" (set PAUSE_MESSAGE=%@UNQUOTE[%2])

rem Set the colors (two redundant methods):
                   %COLOR_PAUSE%
        echos %ANSI_COLOR_PAUSE%
        echos %@CHAR[27][ q%@CHAR[27]]12;yellow%@CHAR[7]

rem Clear the character buffer so we don't end up hitting a key BEFORE the prompt and have it be counted as after:
        rem repeat 100 
        @input /c /w0 %%This_Line_Clears_The_Character_Buffer

        rem 🐐🐐GOATGOAT🐐🐐 i think this results in false pauses somehow!!! Scripts get caught up here! This isn’t reliable for workflows!

rem Do the actual pause:
        *pause /W%PAUSE_FOR_X_SECONDS_SECONDS% /T %PAUSE% %PAUSE_MESSAGE% 

:Abort
endlocal
