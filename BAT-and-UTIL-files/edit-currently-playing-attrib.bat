 @Echo off
:     ^^^----- WARNING: turning Echo ON makes this script not work!! 2023: NO LONGER TRUE!! HAHA!

:et AUDIOSCROBBLER_LOG=%TMPMUSICSERVERCDRIVE%:\program files\winamp\plugins\AudioScrobbler.log.txt
set AUDIOSCROBBLER_LOG=%TMPMUSICSERVERCDRIVE%:\Users\ClioC\AppData\Local\Last.fm\Last.fm Scrobbler.log

call validate-environment-variables TMPMUSICSERVERCDRIVE AUDIOSCROBBLER_LOG MACHINENAME MUSICSERVERMACHINENAME


::::: SETUP:
	:Fix Twitter non-response side-effect:
	:call nocar



::::: INITIALIZE COMMENT PASSTHROUGH:
    ::DO NOT DO THIS:: set LEARNED_COMMENT=%* - DOESN'T WORK LIKE THAT



:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::::: DEBUG STUFF:
	:Do NOT turn echo on if %DEBUG% is 1, because this won't work if we do that.

	:Setting this to 1 will make the greps be put on the screen..
		set VERBOSE=1

	:::: You want this a lot, too:
		unset /q ECCHECKPASSED
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::





:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::::: Make sure we have %temp and %editor defined, but only do it once, for speedup purposes
	if %ECCHECKPASSED == 1 goto :eccheckpassed
		:Debug
			:echo checking eccheckpassed
		:Check_Initial_Conditions
			call  checktemp.bat
			call  fixclip
			call  yyyymmdd
            call validate-environment-variables TEMP EDITOR MACHINENAME MP3OFFICIAL MUSICSERVERMACHINENAME MUSICSERVERUSERNAME
		:Set_The_Script_To_Run
			SET   ECCHECKPASSED=1
			set   LEARNEDSCRIPT=%temp\ec-tmp-%_PID%-%YYYYMMDDHHMMSS%.bat
		:Debug
			:echo LEARNEDSCRIPT is %LEARNEDSCRIPT%
			:pause
	:eccheckpassed
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::




:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::::: Make sure LAST.FM scrobbler is running, or this won't work: (only doable on the same machine)
	if "%MACHINENAME%" ne "%MUSICSERVERMACHINENAME" goto :CheckIfLastFMIsRunning_Nevermind
		call isrunning Last.*fm
        call print-if-debug "ISRUNNING='%ISRUNNING%'"
        :pause
		if "%ISRUNNING%" eq "1"  goto :LastFMIsRunning_Yes
			:LastFMIsRunning_No
				beep 300 %+ beep 250 %+ beep 200 %+ beep 150
                call FATAL_ERROR "Last.fm scrobbler must be running! Running it now."
                %COLOR_RUN%    %+ call lastfm-start 
                %COLOR_NORMAL%
			goto :END
		:LastFMIsRunning_Yes
	:CheckIfLastFMIsRunning_Nevermind
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::





:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
: Multi-room patch is now deprecated with an annoying warning, no longer need to do this:	call setTmpMusicServer.bat %*
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::



goto :2013way




















:Don't think this happens anymore:
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
: echo *** Doing things the new way...
: Lessons learned: it truly is best to grep against everything.m3u and not preferred.m3u
if not exist "%AUDIOSCROBBLER_LOG%" (echo WARNING: "%AUDIOSCROBBLER_LOG%" does not exist!  )





:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
goto :skip_old_way

	echo *** Getting mp3 regex...
        :grep from audioscrobbler's logfile on the correct computer, cut out the pre-filename+album part, pipe it to our perl script to remove the last parenthetical clause (including albums that have "(live)" at the end of their title -- this was DAMN DAMN tricky with a regex from hell), then convert id3 to filename regex, for example a question mark in a id3 should be .* for a grep against playlist filenames because "?" is not a valid filename character, then save that to afile

        (@grep CScrobbler::OnTrackPlay "%AUDIOSCROBBLER_LOG%"|@tail -1|@cut -c75-|@remove-last-parenthetical-clause|@convert-id3-to-filenameregex) >%temp\scrobble-regex.txt
        type %temp\scrobble-regex.txt
	echo.
	echo.

	echo *** Getting mp3 filename...
        :Now search for that regex against the playlist everything.m3u, which holds every mp3, in the correct location, convert / to \, and that is the currently playing file 
        if %VERBOSE == 1 echo *** grep -i "%@LINE[%temp\scrobble-regex.txt,0]" %MP3CL\LISTS\everything.m3u 
        (@grep -i "%@LINE[%temp\scrobble-regex.txt,0]" %MP3OFFICIAL\LISTS\everything.m3u | head /N1 | @convert-slashes-to-backslashes) >%temp\scrobble-file.txt
        type %temp\scrobble-file.txt
	echo.
	echo.

	echo *** Getting mp3 folder...
        : Now strip the filename off of the currently playing file, to get the currently playing folder
        (@type %temp\scrobble-file.txt | @trimfile ) >%temp\scrobble-dir.txt
        type %temp\scrobble-dir.txt
        cd "%@LINE[%temp\scrobble-dir.txt,0]" 
	echo.
	echo.

	: The attribute file will be named attrib.lst in that currently playing folder
        set ATTRIB="%@LINE[%temp\scrobble-dir.txt,0]attrib.lst"
        echo %ATTRIB >%temp\scrobble-attrib_used_last.txt
        echo Attribute file is: 
        echo %ATTRIB
	echo.
	echo.
	echo.

	: Let user know if it exists
        if     exist %ATTRIB echo Attribute file exists.
        : Give them a chance to run away if it does not exist
        if not exist %ATTRIB (echo *** Attribute file does not exist!! %+ echo Hit ctrl-break to abort. %+ pause )
        :Give them folder contents...
        call mp3index

	: Edit attrib.lst in whatever folder our mp3 is playing in
        REM echo EC_OPT_NOEDITOR is %EC_OPT_NOEDITOR%
        if %EC_OPT_NOEDITOR eq 1 .or. "noedit" eq ec"%1" (unset /q EC_OPT_NOEDITOR %+ goto :NoEditor1)
            :%EDITOR %ATTRIB
            %EDITOR attrib.lst
        :NoEditor1

:skip_old_way
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


:2008way
	echo  edit-currently-playing-attrib-helper.pl "%AUDIOSCROBBLER_LOG%" %MP3OFFICIAL\lists\everything.m3u %* {GT}%LEARNEDSCRIPT%
	      edit-currently-playing-attrib-helper.pl "%AUDIOSCROBBLER_LOG%" %MP3OFFICIAL\lists\everything.m3u %*    >%LEARNEDSCRIPT%
	goto :EditIt

:2009way
	echo  edit-currently-playing-attrib-helper.pl "%TMPMUSICSERVERCDRIVE:\Documents and Settings\oh\Local Settings\Application Data\Last.fm\Client\WinampPlugin.log" %MP3OFFICIAL\lists\everything.m3u %* {GT}%LEARNEDSCRIPT%
	      edit-currently-playing-attrib-helper.pl "%TMPMUSICSERVERCDRIVE:\Documents and Settings\oh\Local Settings\Application Data\Last.fm\Client\WinampPlugin.log" %MP3OFFICIAL\lists\everything.m3u %*    >%LEARNEDSCRIPT%
	:                                                                  T:\Documents and Settings\oh\Local Settings\Application Data\Last.fm\Client\WinampPlugin.log
	goto :EditIt


:2011way
	if "%HADES_DOWN"=="1" goto :HadesDown
	:HadesNotDown
	echo edit-currently-playing-attrib-helper.pl "%AUDIOSCROBBLER_LOG%" %MP3OFFICIAL\lists\everything.m3u %* {GT}%LEARNEDSCRIPT%
	     edit-currently-playing-attrib-helper.pl "%AUDIOSCROBBLER_LOG%" %MP3OFFICIAL\lists\everything.m3u %*    >%LEARNEDSCRIPT%
	goto :CallECTmp
	:HadesDown
	set AUDIOSCROBBLER_LOG=%HD128G:\Users\carolyn\AppData\Local\Last.fm\Client\Last.fm.log
	call validate-environment-variable AUDIOSCROBBLER_LOG
	echo edit-currently-playing-attrib-helper.pl "%AUDIOSCROBBLER_LOG%" %MP3OFFICIAL\lists\everything.m3u %* {GT}%LEARNEDSCRIPT%
	     edit-currently-playing-attrib-helper.pl "%AUDIOSCROBBLER_LOG%" %MP3OFFICIAL\lists\everything.m3u %*    >%LEARNEDSCRIPT%
	goto :CallECTmp
	:CallECTmp
	goto :EditIt










:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:2013way
	:if "%HADES_DOWN"=="1" goto :HadesDown
    :    :HadesNotDown
    :    :echo edit-currently-playing-attrib-helper.pl "%AUDIOSCROBBLER_LOG%" %MP3OFFICIAL\lists\everything.m3u %* {GT}%LEARNEDSCRIPT%
    :          edit-currently-playing-attrib-helper.pl "%AUDIOSCROBBLER_LOG%" %MP3OFFICIAL\lists\everything.m3u %*    >%LEARNEDSCRIPT%
    :    goto :CallECTmp
	::HadesDown
	::et LOGFILENAME=Last.fm.log
	:et LOGFILENAME=WinampPlugin.log
	set LOGFILENAME=Last.fm Scrobbler.log
        %COLOR_DEBUG%
        set DRIVE_TO_USE=%MUSICSERVERCDRIVE%
        if "%MACHINENAME%"  eq "%MUSICSERVERMACHINENAME%" (set DRIVE_TO_USE=C)
        echo edit-currently-playing-attrib-helper.pl "%AUDIOSCROBBLER_LOG%" %MP3OFFICIAL\lists\everything.m3u %* {GT}%LEARNEDSCRIPT% %+ %COLOR_NORMAL%
             edit-currently-playing-attrib-helper.pl "%AUDIOSCROBBLER_LOG%" %MP3OFFICIAL\lists\everything.m3u %*    >%LEARNEDSCRIPT%
	goto :CallECTmp
	:CallECTmp
	goto :EditIt

	:EditIt
	call %LEARNEDSCRIPT%
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::









:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:END
    set LAST_ATTRIB=%ATTRIB%             %+    unset /q ATTRIB
    set LAST_COMMENT=%LEARNED_COMMENT%   %+    unset /q LEARNED_COMMENT
	set LAST_VERBOSE=%VERBOSE%           %+    unset /q VERBOSE
	set LAST_AUTOMARK=%AUTOMARK%         %+    unset /q AUTOMARK
	set LAST_AUTOMARKAS=%AUTOMARKAS%     %+    unset /q AUTOMARKAS
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
