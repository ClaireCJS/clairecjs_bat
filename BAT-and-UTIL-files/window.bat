@Echo OFF

REM alias passthrough/intercept for the window command so that we can warn user that it is not appliable under Windows Terminal


REM      WINDOW won't work in WT because (as previously mentioned elsewhere) there is no console window when you're in WT. 
REM      You might try something based on activate "%_wintitle". 
REM      I'm pretty sure _WINTITLE will be the WT tab's caption if current TCC is in WT's active tab/pane.



call detect-command-line-container
if "%container" eq "WindowsTerminal" .and. %RUNNING_ENVIRONM ne 1 .and. %SUPPRESS_WINDOW_UNDER_WINDOWS_TERMINAL_WARNING ne 1 (
    set PRINTMESSAGE_OPT_SUPPRESS_AUDIO=1
	call advice "Window command does not work under WindowsTerminal, but we will try this anyway: '%0 %*'"
)

*window %*

if defined SUPPRESS_WINDOW_UNDER_WINDOWS_TERMINAL_WARNING (set SUPPRESS_WINDOW_UNDER_WINDOWS_TERMINAL_WARNING=)

