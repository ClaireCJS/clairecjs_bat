@LoadBTM on
@Echo OFF
@on break cancel


rem Validate environment (once):
        if "1" != "%VALIDATED_AHK%" (call validate-ahk %+ set VALIDATED_AHK=1)

rem Config and Get parameters:
        set OUR_LOGGING_LEVEL=None
        set PARAMS=%*
        set PARAM_1=%1

rem Save folder & go into AutoHotKey folder:
        pushd
        %AHK_DIR%\

rem Default action if no parameters are passed... 
    iff "%PARAM_1%" == "" then
            cls
            dir
            repeat 2 echo.
            call warning_soft "No AHK file specified, went to folder instead... “popd” to return"
            goto :END_No_Popd
    endiff

rem Special "autohotkey restart" / "ahk restart" command to re-start it in case something goes wrong or we want to force-restart AutoHotKey:
    iff "%PARAM_1%" == "restart" then
                rem Let user know:
                        echo %ANSI_COLOR_REMOVAL%Restarting %italics_on%AutoHotKey%italics_off%...%ANSI_RESET%

                rem “AutoHotKey-autoexec.bat” performs the following:
                rem     ❶ kills the Autohotkey process with “taskend /f autohotkey64*”
                rem     ❷  sets the “insert” mode to “on”
                rem     ❸  sets the “scroll lock" to “off”
                rem     ❹  sets the   “caps lock” to “off”
                rem     ❺  sets the    “num lock” to “off” 
                rem     ❻  runs the AutoHotKey startup script “autoexec.ahk” 
                        call AutoHotKey-autoexec 
                        set  PARAM_1=start                       
                        goto /i END
    endiff

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
