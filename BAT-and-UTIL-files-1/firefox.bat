@on break cancel
:@Echo OFF

if "%1"=="exitafter" (goto :noarg)
if "%1"==""          (goto :noarg)

:arg
	if "%OS"=="7" goto :arg7
        :argpre7
        start "%ProgramFiles\Mozilla Firefox\firefox.exe" %*
        goto :argdone
	:arg7
	:start "%ProgramFiles(x86)%\Mozilla Firefox\firefox.exe" -new-tab %*
    call pf2.bat
    cd "Mozille Firefox"
    start firefox.exe %*
:argdone

goto :END


:noarg
	:REM: start /min "%ProgramFiles\Mozilla Firefox\firefox.exe"
	set URL=http://www.krazydad.com/gustavog/FlickRandom.pl?user=ClioCJS
	if "%MACHINENAME%" eq "WORK" set URL=http://www.google.com
	start %URL%
	if "%1"=="exitafter" exit
goto :END


:END
