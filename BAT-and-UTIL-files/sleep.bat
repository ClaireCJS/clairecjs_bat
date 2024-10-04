@Echo OFF

rem Before Windows  7, we used a 32-bit sleep.exe in our %UTIL% folder, but
rem After  Windows XP, we redirect sleep commands to the internal *delay command:
        goto :%OS


:Windows_NT
:10
:11
:7
    
    rem Cute screen output, except when we don't want it:
            if "%2" eq "silent" (goto :silent_1)
                    rem  %ANSI_COLOR_DEBUG%%@CHAR[9201]%@CHAR[65039]%FAINT_ON% delay %* %FAINT_OFF%%ANSI_RESET%
                    echo %ANSI_COLOR_DEBUG%%EMOJI_STOPWATCH%%ZZZZZZ%%FAINT_ON% delay %* %FAINT_OFF%%ANSI_RESET%
            :silent_1

    rem Do the actual sleep using the TCC internal DELAY command:
             *delay %*
goto :END


:XP
:2K
:ME
:98
:95
    %UTIL%\sleep %*
goto :END


:END

