:::: USAGE:  monitor-to-react-after-program-closes videolan.vlc "call unpause"
::::         ...would run the command "call unpause" once the process VLCPlayer is no longer running
:::: Do everything related to making this window invisible first:
                                     SET HIDDEN=0
    if "%@UPPER[%3]" eq "EXITAFTER" (SET HIDDEN=1)
    if "%HIDDEN%"                   (window /trans=0)

:::: Get parameters:
    SET WAIT_FOR=%1
    SET REACTION=%@UNQUOTE[%2]
	if "%WAIT_FOR%" eq "" (gosub :NoArg 1 "what to wait for" %+ goto :END)
	if "%REACTION%" eq "" (gosub :NoArg 2  "how to react"    %+ goto :END)

:::: See if the process is running:
    title * Waiting for: %WAIT_FOR% to close before running: %@UNQUOTE[%REACTION%]
    :TryAgain
	call IsRunning %WAIT_FOR%

:::: If it is, continue waiting:
	if "%ISRUNNING%" eq "0" goto :DoneWaiting
    delay 1
    goto :TryAgain


:::: Once we are done waiting, we can do our delayed-reaction:
    :DoneWaiting
	set REDOCOMMAND=%REACTION%
    %REACTION%



        goto :END
            ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
                :NoArg [arg explanation]
                    %COLOR_ALARM%  %+ echos * FATAL ERROR: Argument %arg% (%@UNQUOTE[%explanation%]) is missing.
                    %COLOR_NORMAL% %+ echo. %+ call white-noise 1
                return
            ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :END

::::: Exit if instructed:
    %COLOR_DEBUG% %+ echo - hidden is %HIDDEN% %+ %COLOR_NORMAL%
    if "%HIDDEN%" eq "1" (exit)
