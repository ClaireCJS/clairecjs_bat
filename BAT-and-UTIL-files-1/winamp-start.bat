@Echo OFF
 on break cancel


rem BRANCH VIA PARAMETERS:
	if "%1"=="plugins" (goto :Plugins  )
	if "%1"=="appdata" (goto :Appdata  )
	                    goto :RunWinAmp


:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:RunWinAmp
    call nocar
	:a bad idea when queueing mp3s: kill /f winamp*
	:et WINAMP="%ProgramFiles%\Winamp\winamp.exe"
	set WINAMP="%UTIL2%\Winamp repo\WinAmp\winamp.exe"
	if isdir %UTIL2%\WinAmp (set WINAMP="%UTIL2%\Winamp\winamp.exe")
    set PARAM=%1
    REM Force-start always-using-new -winamp by igoring user input, for example: set PARAM=new
    if "%PARAM" eq "default"   (set WINAMP="%UTIL2%\WinAmp\winamp.exe")
    if "%PARAM" eq "community" (set WINAMP="%UTIL2%\WinAmp repo\Winamp WACUP\winamp.exe")
    if "%PARAM" eq "new"       (set WINAMP="%UTIL2%\WinAmp repo\Winamp v5.9.2\winamp.exe")
    if "%PARAM" eq "old"       (set WINAMP="%UTIL2%\WinAmp repo\Winamp v5.666\winamp.exe")
    if "%PARAM" eq "5.666"     (set WINAMP="%UTIL2%\WinAmp repo\Winamp v5.666\winamp.exe")
    if "%PARAM" eq  "5666"     (set WINAMP="%UTIL2%\WinAmp repo\Winamp v5.666\winamp.exe")
    if "%PARAM" eq   "666"     (set WINAMP="%UTIL2%\WinAmp repo\Winamp v5.666\winamp.exe")
    if not defined WINAMP call validate-environment-variable WINAMP
	if exist %WINAMP% goto :Winamp_Exists_YES
	                       :Winamp_Exists_NO
		:Winamp_Exists_YES
                        call MiniLyrics
                        iff "%1" != "noposfix" then
                                call AskYN "Fix Minilyrics size & position" no 10
                                if "Y" == "%ANSWER%" call fix-MiniLyrics-window-size-and-position
                        endiff
			goto :Winamp_Exists_DONE

		:Winamp_Exists_NO
			call alarmbeep
			pause
			goto :Winamp_Exists_DONE
	:Winamp_Exists_DONE
goto :End
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:Appdata
        call appdata
        cd   winamp
        cls
        dir
        echo.
        call advice "WinampMatrixMixer settings are in out_mixer.ini" silent
        rem  advice "There is also another winamp folder - type 'nd' to go there" 
goto :END
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::::::::::::::::::::
:Plugins
	call winamp-plugins %*
goto :End
::::::::::::::::::::::::::::::::::::::::::::::::::::::


:End

repeat 5 echo.


