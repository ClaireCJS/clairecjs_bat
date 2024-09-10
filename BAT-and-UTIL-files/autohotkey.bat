@echo off

set OUR_LOGGING_LEVEL=None

if %VALIDATED_AHK ne 1 (call validate-ahk)

pushd
%AHK_DIR%\

    if "%1" eq "" (
        cls
        dir
        repeat 2 echo.
        call warning_soft "No AHK file specified, went to folder instead... 'popd' to return"
        goto :END_No_Popd
    )

    if "%1" eq "c:\bat\autoexec.ahk" .or. "%1" eq "autoexec.ahk" (echos %SET_INSERT_ON%``)

    set COMMAND=*start "%@UNQUOTE[%1]" %AHK_DIR%\AutoHotkey64.exe %*
        call %OUR_LOGGING_LEVEL% "command is '%italics_on%%COMMAND%%italics_off%'"
        %COLOR_RUN%
        %COMMAND%

:END
        popd

:END_No_Popd
        %COLOR_NORMAL%
