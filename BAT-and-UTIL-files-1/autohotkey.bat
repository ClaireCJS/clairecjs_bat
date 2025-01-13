@Echo OFF
 on break cancel

set OUR_LOGGING_LEVEL=None

if %VALIDATED_AHK ne 1 (call validate-ahk)

set PARAMS=%*
set PARAM_1=%1

pushd
%AHK_DIR%\

    rem Default action if no parameters are passed... 
            if "%PARAM_1%" == "" (
                    cls
                    dir
                    repeat 2 echo.
                    call warning_soft "No AHK file specified, went to folder instead... “popd” to return"
                    goto :END_No_Popd
            )

    rem allow "autohotkey restart" / "ahk restart" command:
            if "%PARAM_1%" == "restart" (
                    echo %ANSI_COLOR_REMOVAL%Restarting %italics_on%AutoHotKey%italics_off%...%ANSI_RESET%
                    rem Kills/restarts, run
                    call AutoHotKey-autoexec 
                    set PARAM_1=start
                    goto :END
            )

    rem our autoexec.ahk has a insert-status "tracker" that doesn’t really track, so best set insert to on coinciding with the loading of this:
            if "%PARAM_1%" == "start" .or. "%PARAM_1%" == "restart" .or. "%PARAM_1%" == "autoexec"     (set PARAM_1=%BAT%\autoexec.ahk %+ set PARAMS=%PARAM_1%)
            rem infinite loop oops if "%PARAM_1%" == "%bat%\autoexec.ahk"                  .or. "%PARAM_1%" == "autoexec.ahk" (call AutoHotKey-autoexec %bat%\autoexec.ahk %+ goto :END)


    rem Logging
            rem set OUR_LOGGING_LEVEL=debug
            rem commenting out for speedup only: call %OUR_LOGGING_LEVEL% "command is “%italics_on%%COMMAND%%italics_off%”"

    rem Run Autohotkey
            set COMMAND=*start "%@UNQUOTE[%PARAM_1%]" %AHK_DIR%\AutoHotkey64.exe %PARAMS%
            %COLOR_RUN% %+ %COMMAND%
            rem commenting out for speedup only: call errorlevel "something’s up with %italics_on%%0%italics_off%"

:END
        popd
:END_No_Popd
:END
