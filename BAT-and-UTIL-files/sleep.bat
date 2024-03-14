@Echo OFF
goto :%OS


:Windows_NT
:10
:11
:7
    %color_debug%  %+ echo %EMOJI_STOPWATCH%%FAINT_ON% delay %* %FAINT_OFF%
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

