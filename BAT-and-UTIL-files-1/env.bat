@on break cancel
@echo off

if "%1" ne "" (set PARAM=%1 %+ goto :Params)


:No_Params
    REM there is an env.pl script, but it's redundant -- the internal command 'set' does the same thing...
        set|:u8 strip-ansi
goto :END


:Params
    setdos /A0
    set|:u8 findstr /i %PARAM%|:u8 findstr /v CMDLINE=env |:u8 findstr /v PARAM=%PARAM%
    setdos /A1
goto :END


:END