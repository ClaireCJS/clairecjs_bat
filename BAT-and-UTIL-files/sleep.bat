@Echo OFF
goto :%OS


:Windows_NT
:10
:11
:7
    if "%2" eq "silent" (goto :silent_1)
rem %color_debug%  %+ echo %@CHAR[9201]%@CHAR[65039]%FAINT_ON% delay %* %FAINT_OFF%
    %color_debug%  %+ echo %EMOJI_STOPWATCH%%ZZZZZZ%%FAINT_ON% delay %* %FAINT_OFF%
    :silent_1
    %color_normal% %+                                  delay %*
goto :END


:XP
:2K
:ME
:98
:95
    %UTIL%\sleep %*
goto :END


:END

