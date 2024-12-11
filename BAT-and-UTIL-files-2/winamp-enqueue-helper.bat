@echo off

::::: GENERATE OUR PLAYLIST:
	:Get guaranteed unique temp filename
	call validate-environment-variable TEMP
	SET TMP1=%@UNIQUE[%TEMP]
	REM echo temp playlist is %PLAYLIST%


	:Append m3u playlist extension to it
	SET PLAYLIST=%TMP1.m3u
	set BACKUP=c:\recycled\last-mplay-playlist.m3u


	:Use the mp3-check search script to generate our playlist
	(call c:\bat\mp3-check %* |:u8 uniq) >:u8%PLAYLIST%

::::: DISPLAY OUR PLAYLIST:

    color bright yellow on black
    type %PLAYLIST%
    color white on black

::::: PLAY OUR PLAYLIST:

	if "%MPLAYVLC%" eq "1" goto :Play_With_VLC
	if "%MPLAYMPC%" eq "1" goto :Play_With_MPC
	if "%ENQUEUE%"  eq "1" goto :Play_With_Winamp
	                       goto :Play_With_MPC
                           :: 20150630 - default changed to MPC because VLC is being a bitch with forward slashes all of a sudden

		:Play_With_VLC
			call vlc --loop %PLAYLIST% 
		goto :Play_DONE

		:Play_With_MPC
            call pause.btm
			call mpc        %PLAYLIST% 
            call launch-monitor-to-react-after-program-closes mpc-hc "call unpause"     %+ REM unpause music when done but give command line back
		goto :Play_DONE

		:Play_With_Winamp
        echo WE NOW HAVE ENQUEUEUE.EXE (SEE ENQUEUE.BAT) SO WE MAY NOT TO DO THIS THIS WAY NOW!! MAINTENANCE MAY BE NEEDED!!
        PAUSE
        PAUSE
        PAUSE
        PAUSE
        PAUSE
			:Clear the screen and show the playlist
			cls
			type %PLAYLIST
			echo. %+ %COLOR_WARNING%
			echo ****** Ready to enque above playlist into winamp.  Hit any key to continue. ******
            %COLOR_PROMPT%
			pause>nul
            %COLOR_NORMAL%

			:Call winamp with the playlist
			"%ProgramFiles\WINAMP\WINAMP.EXE" /ADD %PLAYLIST

			:Make a rolling backup of the last playlist for reference
			if exist %BACKUP~~ copy /q %BACKUP~~ %BACKUP~~~
			if exist %BACKUP~  copy /q %BACKUP~  %BACKUP~~
			if exist %BACKUP   copy /q %BACKUP   %BACKUP~
			copy /q %PLAYLIST %BACKUP
			REM would delete before winamp grabbed it: del  /q %PLAYLIST
		goto :Play_DONE

	:Play_DONE

::::: CLEAN UP:
	:Clean_Up
	:Free environment
	unset /q TMP1
	unset /q PLAYLIST

