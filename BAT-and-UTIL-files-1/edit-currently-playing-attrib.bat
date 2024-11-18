 @Echo off
  rem WARNING: Do NOT turn echo on if %DEBUG% is 1, because this won't work if we do that. In general, this script can be problematic with echo on



rem CONFIGURATION:
		set VERBOSE=1          %+ rem Setting this to 1 will make the greps be put on the screen

rem ENVIRONMENT VALIDATION:
        if %EC_VALIDATED ne 1 (
            call validate-environment-variables TMPMUSICSERVERCDRIVE MUSICSERVERCDRIVE AUDIOSCROBBLER_LOG MACHINENAME MUSICSERVERMACHINENAME EDITOR TEMP MACHINENAME MP3OFFICIAL MUSICSERVERMACHINENAME MUSICSERVERUSERNAME
            set EC_VALIDATED=1
        )

rem CLIPBOARD FIX + FIGURE OUT OUR FILENAME:
		unset /q ECCHECKPASSED %+ rem This really needs to be done. A lot
        if %ECCHECKPASSED == 1 (goto :eccheckpassed)
            rem DEBUG: :echo checking eccheckpassed
            call fixclip
            set  ECCHECKPASSED=1
            rem CREATE FILENAME FOR SCRIPT TO RUN:
                call  yyyymmdd
                set   LEARNEDSCRIPT=%temp\ec-tmp-%_PID%-%YYYYMMDDHHMMSS%.bat                  
            rem DEGBUG: :echo LEARNEDSCRIPT is %LEARNEDSCRIPT% %+ pause
        :eccheckpassed



rem Make sure LAST.FM scrobbler is running, or this won't work: (only doable on the same machine):
	if "%MACHINENAME%" eq "%MUSICSERVERMACHINENAME" (
		call isrunning Last.*fm
        call print-if-debug "ISRUNNING='%ISRUNNING%'" %+ if %DEBUG eq 1 (pause)
		if "%ISRUNNING%" ne "1" (
                call alarm "Last.fm scrobbler must be running! Running it now."
                call lastfm-start                 
                call isrunning Last.*fm
                if "%ISRUNNING%" ne "1" (call fatal_error "could not restart Last.fm scrobbler, despite trying")
         )
	)



rem Multi-room patch for house addition construction (2003-2006) is now deprecated with an annoying warning, as no longer need to do this:	
        rem call setTmpMusicServer.bat %*


rem If for some reason we made it here, try the old method:
        goto :2013way


:END
    rem save values for auditing:
        set LAST_ATTRIB=%ATTRIB%             %+    unset /q ATTRIB
        set LAST_COMMENT=%LEARNED_COMMENT%   %+    unset /q LEARNED_COMMENT
        set LAST_VERBOSE=%VERBOSE%           %+    unset /q VERBOSE
        set LAST_AUTOMARK=%AUTOMARK%         %+    unset /q AUTOMARK
        set LAST_AUTOMARKAS=%AUTOMARKAS%     %+    unset /q AUTOMARKAS
goto :EOF





















:Don't think this happens anymore:
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
: echo *** Doing things the new way...
: Lessons learned: it truly is best to grep against everything.m3u and not preferred.m3u
if not exist "%AUDIOSCROBBLER_LOG%" (echo WARNING: "%AUDIOSCROBBLER_LOG%" does not exist!  )





:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
goto :skip_old_way

	echo *** Getting mp3 regex...
        :grep from audioscrobbler's logfile on the correct computer, cut out the pre-filename+album part, pipe it to our perl script to remove the last parenthetical clause (including albums that have "(live)" at the end of their title -- this was DAMN DAMN tricky with a regex from hell), then convert id3 to filename regex, for example a question mark in a id3 should be .* for a grep against playlist filenames because "?" is not a valid filename character, then save that to afile

        (@grep CScrobbler::OnTrackPlay "%AUDIOSCROBBLER_LOG%"|:u8@tail -1|:u8@cut -c75-|:u8@remove-last-parenthetical-clause|:u8@convert-id3-to-filenameregex) >:u8%temp\scrobble-regex.txt
        type %temp\scrobble-regex.txt
	echo.
	echo.

	echo *** Getting mp3 filename...
        :Now search for that regex against the playlist everything.m3u, which holds every mp3, in the correct location, convert / to \, and that is the currently playing file 
        if %VERBOSE == 1 echo *** grep -i "%@LINE[%temp\scrobble-regex.txt,0]" %MP3CL\LISTS\everything.m3u 
        (@grep -i "%@LINE[%temp\scrobble-regex.txt,0]" %MP3OFFICIAL\LISTS\everything.m3u |:u8 head /N1 |:u8 @convert-slashes-to-backslashes) >:u8%temp\scrobble-file.txt
        type %temp\scrobble-file.txt
	echo.
	echo.

	echo *** Getting mp3 folder...
        : Now strip the filename off of the currently playing file, to get the currently playing folder
        (@type %temp\scrobble-file.txt |:u8 @trimfile ) >:u8%temp\scrobble-dir.txt
        type %temp\scrobble-dir.txt
        cd "%@LINE[%temp\scrobble-dir.txt,0]" 
	echo.
	echo.

	: The attribute file will be named attrib.lst in that currently playing folder
        set ATTRIB="%@LINE[%temp\scrobble-dir.txt,0]attrib.lst"
        echo %ATTRIB >:u8%temp\scrobble-attrib_used_last.txt
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
	      edit-currently-playing-attrib-helper.pl "%AUDIOSCROBBLER_LOG%" %MP3OFFICIAL\lists\everything.m3u %*    >:u8%LEARNEDSCRIPT%
	goto :EditIt

:2009way
	echo  edit-currently-playing-attrib-helper.pl "%TMPMUSICSERVERCDRIVE:\Documents and Settings\oh\Local Settings\Application Data\Last.fm\Client\WinampPlugin.log" %MP3OFFICIAL\lists\everything.m3u %* {GT}%LEARNEDSCRIPT%
	      edit-currently-playing-attrib-helper.pl "%TMPMUSICSERVERCDRIVE:\Documents and Settings\oh\Local Settings\Application Data\Last.fm\Client\WinampPlugin.log" %MP3OFFICIAL\lists\everything.m3u %*    >:u8%LEARNEDSCRIPT%
	:                                                                  T:\Documents and Settings\oh\Local Settings\Application Data\Last.fm\Client\WinampPlugin.log
	goto :EditIt


:2011way
	if "%HADES_DOWN"=="1" goto :HadesDown
	:HadesNotDown
	echo edit-currently-playing-attrib-helper.pl "%AUDIOSCROBBLER_LOG%" %MP3OFFICIAL\lists\everything.m3u %* {GT}%LEARNEDSCRIPT%
	     edit-currently-playing-attrib-helper.pl "%AUDIOSCROBBLER_LOG%" %MP3OFFICIAL\lists\everything.m3u %*    >:u8%LEARNEDSCRIPT%
	goto :CallECTmp
	:HadesDown
	set AUDIOSCROBBLER_LOG=%HD128G:\Users\carolyn\AppData\Local\Last.fm\Client\Last.fm.log
	call validate-environment-variable AUDIOSCROBBLER_LOG
	echo edit-currently-playing-attrib-helper.pl "%AUDIOSCROBBLER_LOG%" %MP3OFFICIAL\lists\everything.m3u %* {GT}%LEARNEDSCRIPT%
	     edit-currently-playing-attrib-helper.pl "%AUDIOSCROBBLER_LOG%" %MP3OFFICIAL\lists\everything.m3u %*    >:u8%LEARNEDSCRIPT%
	goto :CallECTmp
	:CallECTmp
	goto :EditIt






:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:2013way
	:if "%HADES_DOWN"=="1" goto :HadesDown
    :    :HadesNotDown
    :    :echo edit-currently-playing-attrib-helper.pl "%AUDIOSCROBBLER_LOG%" %MP3OFFICIAL\lists\everything.m3u %* {GT}%LEARNEDSCRIPT%
    :          edit-currently-playing-attrib-helper.pl "%AUDIOSCROBBLER_LOG%" %MP3OFFICIAL\lists\everything.m3u %*    >:u8%LEARNEDSCRIPT%
    :    goto :CallECTmp
	::HadesDown
	::et LOGFILENAME=Last.fm.log
	:et LOGFILENAME=WinampPlugin.log
	set LOGFILENAME=Last.fm Scrobbler.log
        %COLOR_DEBUG%
        set DRIVE_TO_USE=%MUSICSERVERCDRIVE%
        if "%MACHINENAME%"  eq "%MUSICSERVERMACHINENAME%" (set DRIVE_TO_USE=C)
        echo edit-currently-playing-attrib-helper.pl "%AUDIOSCROBBLER_LOG%" %MP3OFFICIAL\lists\everything.m3u %* {GT}%LEARNEDSCRIPT% %+ %COLOR_NORMAL%
             edit-currently-playing-attrib-helper.pl "%AUDIOSCROBBLER_LOG%" %MP3OFFICIAL\lists\everything.m3u %*    >:u8%LEARNEDSCRIPT%
	goto :CallECTmp
	:CallECTmp
	goto :EditIt

	:EditIt
	call %LEARNEDSCRIPT%
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::













:EOF
