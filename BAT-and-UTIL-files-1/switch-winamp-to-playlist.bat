@Echo OFF
@on break cancel

:::::::::::::::::::::::: Due to problems with c:\mp3\ junction on hades, there are some u:\mp3\'s hard-coded in the code below, where things used to be c:\mp3\. And WAWI is configured for U:\mp3\

:Define_Stuff

        rem wget32quiet was good during the Win95/98/ME/XP/2K days but by Win7 wget32 was better
        rem so make wget32 (not wget32quiet) be the default from here on out:
                              COMMAND=wget32
	if "%OS%"=="95" (set  COMMAND=wget32quiet)
	if "%OS%"=="98" (set  COMMAND=wget32quiet)
	if "%OS%"=="ME" (set  COMMAND=wget32quiet)
	if "%OS%"=="XP" (set  COMMAND=wget32quiet)
	if "%OS%"=="2K" (set  COMMAND=wget32quiet)
	if "%OS%"=="7"  (set  COMMAND=wget32)
	if "%OS%"=="10" (set  COMMAND=wget32)
        call validate-in-path %COMMAND%

	rem Old code from the 2003–2005 addition-construction days when we 
        rem had multiple separate music areas in our house due to construction:
	        rem call setMUSICSERVER.bat %*

:	rem set DEBUG=0
	call advice "Does %1 exist?"
		iff exist %1 then
			call debug "Yes: Precise full filename given."
			set FULLLIST=%@STRIP[%=",%1]
			set FULLLIST2=%FULLLIST
			rem PLAYLIST=%@STRIP[%=",%@NAME[%1].m3u]
			set PLAYLIST=%@REPLACE[.m3u.m3u,.m3u,%@STRIP[%=",%@NAME[%1].m3u]]
		endiff

        call debug "No: Base filename given."
		echo.
		set  PLAYLIST=%@REPLACE[.m3u.m3u,.m3u,%@STRIP[%=",%1.m3u]]
		call important "echo PLAYLIST set to '%emphasis%%PLAYLIST%%deemphasis%'"

        call pause-for-x-seconds 100 "Everything look good?"

			              set  FULLLIST=%@STRIP[%=",%MP3\LISTS\%PLAYLIST]
		if "%BOTH"=="1" ( set FULLLIST2=%@STRIP[%=",%MP32\LISTS\%PLAYLIST])
				         call debug          "FULLLIST  set to '%FULLLIST%'"
		if "%BOTH"=="1" (call less_important "FULLLIST2 set to '%FULLLIST2'")

		set ORIGINALLIST=%FULLLIST
		set ORIGINALLIST2=%FULLLIST2
				 call debug "ORIGINALLIST  set to '%ORIGINALLIST%'"
		if "%BOTH"=="1" (call debug "ORIGINALLIST2 set to '%ORIGINALLIST2'")

        call debug "* 1) Checking if %FULLLIST exists"       
        if exist %FULLLIST% goto :done_defining

		                if not exist %FULLLIST  (set   FULLLIST=%MP3\LISTS\by-attribute\%PLAYLIST %+ set PLAYLIST=by-attribute\%PLAYLIST)
		if "%BOTH"=="1" if not exist %FULLLIST2 (set  FULLLIST2=%MP3\LISTS\by-attribute\%PLAYLIST %+ set PLAYLIST=by-attribute\%PLAYLIST)

        call debug "* 2) Checking if %FULLLIST exists"
                if not exist %FULLLIST% then
                if                 not exist %FULLLIST  (call FATAL_ERROR "Could not find '%FULLLIST%' in LISTS or LISTS\by-attribute!")
		if "%BOTH"=="1" if not exist %FULLLIST2 (call FATAL_ERROR "Could not find '%FULLLIST2' in LISTS or LISTS\by-attribute!")
		endiff


:done_defining
	set PLAYLIST=%@REPLACE[ ,%%%%%%%%%%%%%%%%20,%PLAYLIST]
	echo.
	echo.
	::A new approach - instead of trying to load the specified playlist, and deal with the %20 b.s.,
	::let's just COPY whatever playlist they select to now-playing-playlist -- then we can reload
	::that list blindly without knowing what it is (i.e. after index).
			          call  debug             "FULLLIST  is '%FULLLIST%'"
	if "%BOTH"=="1" ( call  debug             "FULLLIST2 is '%FULLLIST2'")
                         %COLOR_SUCCESS% %+ echo r|copy "%FULLLIST"   %MP3\LISTS\now-playing-playlist.m3u
	if "%BOTH"=="1" (%COLOR_SUCCESS% %+ echo r|copy "%FULLLIST2" %MP32\LISTS\now-playing-playlist.m3u)
	call debug "originallist = '%ORIGINALLIST%'"
	:DEBUG: PAUSE
			        echo %ORIGINALLIST%>%MP3\LISTS\now-playing.dat
	if "%BOTH"=="1" echo %ORIGINALLIST2>%MP3\LISTS\now-playing.dat
	call debug "originallist = '%ORIGINALLIST%'"
	:DEBUG: PAUSE

	call less_important "PLAYLIST is '%PLAYLIST%'"
	echo.
	echo.
	if not exist %FULLLIST (call FATAL_ERROR "FullList of %emphasis%%FULLLIST%%deemphasis% MUST EXIST!")

:DO_IT
	call debug "MUSICSERVER is '%MUSICSERVER%'"
    call debug "%COMMAND --http-user=%WAWI_USER% --http-passwd=%WAWI_PASS%  http://%MUSICSERVER/clear"
	if "%BOTH"=="1" (call debug "%COMMAND --http-user=%WAWI_USER% --http-passwd=%WAWI_PASS% http://%MUSICSERVER2/clear")
    %COLOR_RUN%   %+ call %COMMAND --http-user=%WAWI_USER% --http-passwd=%WAWI_PASS%  http://%MUSICSERVER/clear
	if "%BOTH"=="1"  call %COMMAND --http-user=%WAWI_USER% --http-passwd=%WAWI_PASS% http://%MUSICSERVER2/clear

	::OLD:
	:               echo %COMMAND --http-user=%WAWI_USER% --http-passwd=%WAWI_PASS%  http://%MUSICSERVER/ld?path=%%%%5cLISTS%%%%5c%PLAYLIST
	:f "%BOTH"=="1" echo %COMMAND --http-user=%WAWI_USER% --http-passwd=%WAWI_PASS% http://%MUSICSERVER2/ld?path=%%%%5cLISTS%%%%5c%PLAYLIST
	:               call %COMMAND --http-user=%WAWI_USER% --http-passwd=%WAWI_PASS%  http://%MUSICSERVER/ld?path=%%%%5cLISTS%%%%5c%PLAYLIST
	:f "%BOTH"=="1" call %COMMAND --http-user=%WAWI_USER% --http-passwd=%WAWI_PASS% http://%MUSICSERVER2/ld?path=%%%%5cLISTS%%%%5c%PLAYLIST
	::NEW:
			         call debug           "%COMMAND --http-user=%WAWI_USER% --http-passwd=%WAWI_PASS%  http://%MUSICSERVER/ld?path=%MP3DRIVE%:\mp3\LISTS\now-playing-playlist.m3u"
			         %COLOR_RUN%   %+ call %COMMAND --http-user=%WAWI_USER% --http-passwd=%WAWI_PASS%  http://%MUSICSERVER/ld?path=%MP3DRIVE%:\mp3\LISTS\now-playing-playlist.m3u
	if "%BOTH"=="1" (%COLOR_DEBUG% %+ echo %COMMAND --http-user=%WAWI_USER% --http-passwd=%WAWI_PASS% http://%MUSICSERVER2/ld?path=%MP3DRIVE%:\mp3\LISTS\now-playing-playlist.m3u)
	if "%BOTH"=="1" (%COLOR_RUN%   %+ call %COMMAND --http-user=%WAWI_USER% --http-passwd=%WAWI_PASS% http://%MUSICSERVER2/ld?path=%MP3DRIVE%:\mp3\LISTS\now-playing-playlist.m3u)



::Randomize it afterwards! We're shuffle-lovers! Create an override later if this becomes bothersome
call winamp-randomize-playlist

::Now that we have switched, let's store the playlist, which must be done before we call play.bat 
:(Because someimtes we don't pass %BOTH to play.bat, which makes BOTH=0 and breaks this)
	:DEBUG: echo MUSICSERVER=%MUSICSERVER,MUSICSERVER2=%MUSICSERVER2,musicserverup/downstairs=%MUSICSERVERUPSTAIRS/%MUSICSERVERDOWNSTAIRS
    %COLOR_DEBUG% 
			        if "%MUSICSERVER"  == "%MUSICSERVERUPSTAIRS"   echo %PLAYLIST  >%MP3OFFICIAL\lists\TRIGGER-PLAYLIST-USTAIRS.TRG
			        if "%MUSICSERVER"  == "%MUSICSERVERDOWNSTAIRS" echo %PLAYLIST  >%MP3OFFICIAL\lists\TRIGGER-PLAYLIST-DOWNSTAIRS.TRG
	if "%BOTH"=="1" if "%MUSICSERVER2" == "%MUSICSERVERUPSTAIRS"   echo %PLAYLIST  >%MP3OFFICIAL\lists\TRIGGER-PLAYLIST-USTAIRS.TRG
	if "%BOTH"=="1" if "%MUSICSERVER2" == "%MUSICSERVERDOWNSTAIRS" echo %PLAYLIST  >%MP3OFFICIAL\lists\TRIGGER-PLAYLIST-DOWNSTAIRS.TRG
        			if "%MUSICSERVER"  == "%MUSICSERVERUPSTAIRS"   echo %PLAYLIST >%MP3SECONDARY\lists\TRIGGER-PLAYLIST-USTAIRS.TRG
			        if "%MUSICSERVER"  == "%MUSICSERVERDOWNSTAIRS" echo %PLAYLIST >%MP3SECONDARY\lists\TRIGGER-PLAYLIST-DOWNSTAIRS.TRG
	if "%BOTH"=="1" if "%MUSICSERVER2" == "%MUSICSERVERUPSTAIRS"   echo %PLAYLIST >%MP3SECONDARY\lists\TRIGGER-PLAYLIST-USTAIRS.TRG
	if "%BOTH"=="1" if "%MUSICSERVER2" == "%MUSICSERVERDOWNSTAIRS" echo %PLAYLIST >%MP3SECONDARY\lists\TRIGGER-PLAYLIST-DOWNSTAIRS.TRG



::Now let's play: ********** 20140705 - DECIDED NOT TO DO THIS ANYMORE *****
	goto :donotplay
	if "%MACHINEMAME"=="work" goto :donotplay
        %COLOR_RUN%
		if "%BOTH"=="0" call winamp-play.bat %*
		if "%BOTH"=="1" call winamp-play.bat 
	:donotplay
	:^^^^ the only exception; we probably don't want to play music on both floors! set playlist on both floors; play on current floor. 
	:we can always "paus both" ("flip") if it's on the wrong floor





::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:END
	goto :noclean
		unset /q ORIGINALLIST
		unset /q ORIGINALLIST2
		unset /q     FULLLIST
		unset /q     PLAYLIST
		unset /q     FULLLIST2
		unset /q     PLAYLIST2
	:noclean
	if exist clear (echo R|*del /q clear >nul)
    call fix-window-title
