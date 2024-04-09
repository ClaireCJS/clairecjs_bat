:::: USAGE:  killIfRunning processIsRunningRegex processKillGlob
::::    ex:  killIfRunning winamp                winamp*

:::: Get parameters:
    title killIfRunning %*
	if "%1" eq "" goto :NoArg1
	SET  PROCS_REGEX=%1
	SET  PROCS_KILL=%2
	:no, this made failures letting me forget proper invocation: if "%PROCS_KILL%" eq "" set PROCES_KILL=%PROCS_REGEX%
    call validate-environment-variable PROCS_KILL

:::: See if the process is running:
	call IsRunning %PROCS_REGEX%

:::: And kill it if it is:
	if "%ISRUNNING%" eq "1" .and. "%DEBUG%" ne "" (%COLOR_DEBUG% %+ echo - kill /f %PROCS_KILL% %+ %COLOR_NORMAL%)
	if "%ISRUNNING%" eq "1"      kill /f %PROCS_KILL%

goto :END

	:NoArg1
		echo * FATAL ERROR: need at least one argument
		call white-noise 1
		pause
        gosub :USAGE
	goto :END

    :USAGE
        %COLOR_ADVICE%
            echo USAGE:  killIfRunning processIsRunningRegex processKillGlob
            echo    ex:  killIfRunning winamp                winamp*
        %COLOR_NORMAL%
    return

:END

set LAST_PROCES_KILL=%PROCS_KILL%
set LAST_PROCES_REGEX=%PROCS_REGEX%

unset /q PROCS_REGEX
unset /q PROCS_KILL

call fix-window-title
