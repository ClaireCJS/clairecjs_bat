@echo off

if "%1" ne "" (set PARAM=%1 %+ goto :Params)


:No_Params
    REM there is an env.pl script, but it's redundant -- the internal command 'set' does the same thing...
        set|strip-ansi
goto :END


:Params
    setdos /A0
    set|findstr /i %PARAM%|findstr /v CMDLINE=env |findstr /v PARAM=%PARAM%
    setdos /A1
goto :END


:END