@echo off
 on break cancel

::::: PARAMETERS:
    if "%@UPPER[%2]"      eq "HIDDEN"    (set HIDDEN=1    %+ set MINIMIZE_FIRST=1)
    if "%@UPPER[%1]"      eq "EXITAFTER" (set EXITAFTER=1 %+ set MINIMIZE_FIRST=1)
    if "%MINIMIZE_FIRST%" eq "1"         (set SUPPRESS_WINDOW_UNDER_WINDOWS_TERMINAL_WARNING=1  %+ window minimize)
    if "%HIDDEN%"         eq "1"         (windowhide.exe /hide *drives.bat*hidden* %+ set SUPPRESS_WINDOW_UNDER_WINDOWS_TERMINAL_WARNING=1 %+ window /trans=0)


::::: MAIN:
    echo.
    :::: TODO nest A..Z loop around this so we can differentiate between "[NOT READY]" and not actually a drive and have diff colors for that. THIS WILL SOMETIMES HELP MORE THAN YOU IMAGINE.
    for %drive in (%_ready) gosub wakeDrive %drive%

goto :END

	:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
	:wakeDrive [drive]
		if "%@READY[%drive%]" eq "1" goto :Ready_YES
		                             goto :Ready_NO
			:Ready_NO
                color bright red on black
				goto :Ready_DONE
			:Ready_YES
                color bright green on black
				goto :Ready_DONE
			:Ready_DONE

        echos * ``

        dir %drive\ >nul

		%COLOR_SUCCESS% %+ echo Awakened: %drive% %+ %COLOR_NORMAL%
	return
	:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:END


    if "%@UPPER[%1]" eq "EXITAFTER" exit
