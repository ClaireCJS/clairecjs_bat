@on break cancel
@echo off

::::: CONFIGURATION:
    set PARAMETERS=AUTOEXEC

::::: ENSURE CORRECT SETUP:
    call validate-environment-variables machinename appdata bat
    if not isdir %APPDATA% gosub :No %APPDATA%
    if not isdir %BAT%     gosub :No %BAT%


::::: SET TARGET:
    set TARGET="%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\autoexec-launcher.btm"

::::: ENSURE WE HAVEN'T DONE THIS ALREADY:
    if exist %TARGET% .and. "%@UPPER[%1]" ne "FORCE" goto :Already

::::: INSTALL AUTOEXEC LAUNCHER:
    rem worked 'til 20241016: echo %BAT%\%MACHINENAME%\autoexec.btm %PARAMETERS% >%TARGET%
    rem new:
    echo c:\TCMD\tcc.exe %BAT%\%MACHINENAME%\autoexec.btm %PARAMETERS% >%TARGET%


::::: REPORT:
    echo.
    echo.
    echo.
    %COLOR_SUCCESS%
    echo * Autoexec launcher installed! Go into your start menu and 
    echo   Right click the newly-created icon in order to manually 
    echo   change the launcher to our preferred command line.
    echo * Location: %TARGET%
    %COLOR_IMPORTANT%
    echo * Contents:
    %COLOR_DEBUG%
    type %TARGET%
    echo.
    echo.
    echo.
    %COLOR_WARNING%
    echo ** THIS WILL NOT WORK ** unless you right click on a BTM file and 
    echo    Choose Program and choose TCMD to open it. Otherwise, the above
    echo    contents will run things with CMD.EXE, which is very bad.



goto :END

    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    :No [dir]
        call alarm-beep
        echo * FATAL ERROR! %dir% does not exist as a folder!
    goto :END
    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    :Already
        beep
        echo.
        echo * We already did this! Add "force" as a parameter to force it.
        echo.
        echo * This already exists:
        echo   %TARGET% 
    goto :END
    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:END
