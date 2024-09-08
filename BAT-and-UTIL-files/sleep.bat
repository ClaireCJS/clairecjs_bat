@Echo OFF
goto :%OS


:Windows_NT
:10
:11
:7
    if "%2" eq "silent" (goto :silent_1)
    %color_debug%  %+ echo %EMOJI_STOPWATCH%%FAINT_ON% delay %* %FAINT_OFF%
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

