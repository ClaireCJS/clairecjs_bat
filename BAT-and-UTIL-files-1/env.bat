@echo off

if "%1" ne "" (set PARAM=%1 %+ goto :Params)


:No_Params
    REM there is an env.pl script, but it's redundant -- the internal command 'set' does the same thing...
        set|:u8strip-ansi
goto :END


:Params
    setdos /A0
    set|:u8findstr /i %PARAM%|:u8findstr /v CMDLINE=env |:u8findstr /v PARAM=%PARAM%
    setdos /A1
goto :END


:END