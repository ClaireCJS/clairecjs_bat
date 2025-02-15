@Echo Off
 on break cancel

:DESCRIPTION: aliased intercept for the “window” command
:DESCRIPTION:       1) so that we can warn user that it is not appliable under Windows Terminal
:DESCRIPTION:       2) to implement a “window restore” workaround using Verfatica’s [unpublished] TCC+WT plugin


rem NOTES:
            REM      WINDOW won’t work in WT because (as previously mentioned elsewhere) there is no console window when you’re in WT. 
            REM      You might try something based on activate "%_wintitle". 
            REM      I’m pretty sure _WINTITLE will be the WT tab’s caption if current TCC is in WT’s active tab/pane.



rem Capture parameters:
        set WINDOW_PARAM_1=%1


rem First, we detect the command line container so we can use the native window command if possible:
        call detect-command-line-container



rem If it is a “window flash” command, we use a semi-workaround: color-cycling the background color using ANSI codes:
        if  "%@REGEX[/flash,%WINDOW_PARAM_1]" eq "1"  (
            call color-cycle-background-briefly
            goto :END
        )


rem If it is a “window restore” command, we use our workaround, courtsey of Verfatica’s plugin [which must be present!]:
        if "%WINDOW_PARAM_1" eq "restore" .and. %PLUGIN_4WT_LOADED% eq 1 (
             rem 1=minimize, 2=restore, 3=maximize, 4=unmaximize, 5=?, 6=minmimize ——— Verfatica’s way was to do 6, then 1
             rem echos %@winapi[user32.dll,ShowWindow,%@eval[%_hwndwt],6] >>&nul 
             rem *delay 1 
             echos %@winapi[user32.dll,ShowWindow,%@eval[%_hwndwt],3] >>&nul
             goto :END
        )


rem Otherwise, we [quietly] warn the user that the command isn’t going to work:
        if "%container" eq "WindowsTerminal" .and. %RUNNING_ENVIRONM ne 1 .and. %SUPPRESS_WINDOW_UNDER_WINDOWS_TERMINAL_WARNING ne 1 (
            set PRINTMESSAGE_OPT_SUPPRESS_AUDIO=1
            call advice "Window command mostly doesn%@CHAR[8217]t work under WindowsTerminal, but we will try this anyway: %@CHAR[8220]%0 %*%@CHAR[8221]"
        )


rem We still attempt the native command anyway, just to demonstrate that it doesn’t work:
        *window %*



::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


:END
    rem SUPPRESS_WINDOW_UNDER_WINDOWS_TERMINAL_WARNING is meant for one-time use, so if it’s set, we must clear it:
            if defined SUPPRESS_WINDOW_UNDER_WINDOWS_TERMINAL_WARNING (set SUPPRESS_WINDOW_UNDER_WINDOWS_TERMINAL_WARNING=)

