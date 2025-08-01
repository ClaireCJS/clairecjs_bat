@loadBTM on
@on break cancel
@Echo off
@set OLDTITLE=%_TITLE
  rem WARNING: Do NOT turn echo on if %DEBUG% is 1, because this won’t work if we do that. In general, this script can be problematic with echo on


rem REQUIRED CONFIGURATION:
        set SONGLIST_FILE_TO_USE=%ALL_SONGS_PLAYLIST%   %+ rem File that is a list of all the songs in your music collectoin. Used when we do regex-specific searches. c:\mp3\lists\everything.m3u or even c:\mp3\filelist.txt (run “makefilelist” to make one of those) will suffice

rem DEBUG CONFIGURATION:
	set VERBOSE=0                                   %+ rem Setting this to 1 will make the greps be put on the screen

rem ENVIRONMENT VALIDATION:
        iff %EC_VALIDATED ne 1 then
                call validate-environment-variables TMPMUSICSERVERCDRIVE MUSICSERVERCDRIVE AUDIOSCROBBLER_LOG MACHINENAME MUSICSERVERMACHINENAME EDITOR TEMP MACHINENAME MUSICSERVERMACHINENAME MUSICSERVERUSERNAME
                call validate-in-path               yyyymmdd lastfm-start alarm isrunning print-if-debug fixclip
                set EC_VALIDATED=1
        endiff

rem CLIPBOARD FIX + FIGURE OUT OUR FILENAME:
	unset /q  ECCHECKPASSED                                                  %+ rem This really needs to be done. A lot
        iff 1 ne %ECCHECKPASSED then
                rem Store that we have passed the check
                        rem DEBUG: :echo checking eccheckpassed
                        set  ECCHECKPASSED=1
                rem I forget why the clipboard had problems here or why we do this, but we do:
                        call fixclip
                rem CREATE FILENAME FOR SCRIPT TO RUN:
                        call  yyyymmdd
                        set   SCRIPT_TO_RUN=%temp\ec-tmp-%_PID%-%YYYYMMDDHHMMSS%.bat                  
                        rem DEGBUG: :echo SCRIPT_TO_RUN is %SCRIPT_TO_RUN% %+ pause
        endiff                        
        
rem Create the script to run:
        :2013way
        :2024way
        :2024_new_way_uses_this_also

        rem Set drive letter to use:
                set DRIVE_TO_USE=%MUSICSERVERCDRIVE%
                if "%MACHINENAME%" == "%MUSICSERVERMACHINENAME%" (set DRIVE_TO_USE=C)
        
        rem Set log file to use:
                rem //rem 2008–2024: last.fm logfile parsing method
                rem //        set LOG_TO_USE=%AUDIOSCROBBLER_LOG%       
                        
                rem 2024 update! Getting rid of last.fm dependency and using the WinampNowPlayingToFile plugin instead!
                rem Plugin is obtained at https://github.com/Aldaviva/WinampNowPlayingToFile
                rem Set the 2ⁿᵈ line in the output file to be the full filename of the currently plyaing song
                rem Set NOW_PLAYING_TXT=the filename that you save with the WinampNowPlayingToFile plugin
                        set LOG_TO_USE=%NOW_PLAYING_TXT%
        

        rem A bit of debug output:
                echos %ansi_color_debug%
                echo %faint_on%%ansi_color_bright_black%* edit-currently-playing-attrib-helper.pl "%LOG_TO_USE%" %ALL_SONGS_PLAYLIST% %*  `>`:u8%SCRIPT_TO_RUN% %ansi_color_normal%

        rem Generate our script using our helper program:                
                     edit-currently-playing-attrib-helper.pl "%LOG_TO_USE%" %ALL_SONGS_PLAYLIST% %*    >:u8%SCRIPT_TO_RUN%

goto :Run_Generated_Script

     :Run_Generated_Script
                rem Run our generated "SCRIPT_TO_RUN"
                rem Now that we have the filename of the attrib.lst, let’s edit it, assuming that’s what the generated SCRIPT_TO_RUN does
                rem originally that was all it did, but now it does some other things like going into the folder WITHOUT opening attrib.lst,
                rem and automarking attrib.lst without opening it.

                call %SCRIPT_TO_RUN%

:END
        rem Save values for auditing:
                set LAST_ATTRIB=%ATTRIB%                %+    unset /q ATTRIB
                set LAST_COMMENT=%LEARNED_COMMENT%      %+    unset /q LEARNED_COMMENT
                set LAST_VERBOSE=%VERBOSE%              %+    unset /q VERBOSE
                set LAST_AUTOMARK=%AUTOMARK%            %+    unset /q AUTOMARK
                set LAST_AUTOMARKAS=%AUTOMARKAS%        %+    unset /q AUTOMARKAS


goto :EOF











rem ———————————————————————————————————————— DEPRECATED CODE BELOW ————————————————————————————————————————
rem ———————————————————————————————————————— DEPRECATED CODE BELOW ————————————————————————————————————————
rem ———————————————————————————————————————— DEPRECATED CODE BELOW ————————————————————————————————————————
rem ———————————————————————————————————————— DEPRECATED CODE BELOW ————————————————————————————————————————
rem ———————————————————————————————————————— DEPRECATED CODE BELOW ————————————————————————————————————————

rem 2008–2024: Make sure LAST.FM scrobbler is running, or this won’t work: (only doable on the same machine):
rem 2024–Present: skip this!
                                                goto :skip_old_lastfm_code_1
                                                        iff "%MACHINENAME%" == "%MUSICSERVERMACHINENAME" then
                                                                call isrunning Last.*fm
                                                                call print-if-debug "ISRUNNING=“%ISRUNNING%”" %+ if %DEBUG eq 1 (pause)
                                                                iff "%ISRUNNING%" != "1" then
                                                                        call alarm "Last.fm scrobbler must be running! Running it now."
                                                                        call lastfm-start                 
                                                                        call isrunning Last.*fm
                                                                        if "%ISRUNNING%" != "1" (call fatal_error "could not restart Last.fm scrobbler, despite trying")
                                                                endiff
                                                        endiff
                                                :skip_old_lastfm_code_1
                                                rem Multi-room patch for house addition construction (2003-2006) is now deprecated with an annoying warning, as no longer need to do this:	
                                                        rem call setTmpMusicServer.bat %*
                                                rem If for some reason we made it here, try the old method:
                                                        goto :2013way


                                        :Don’t think this happens anymore:
                                        :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
                                        : echo *** Doing things the new way...
                                        : Lessons learned: it truly is best to grep against everything.m3u and not preferred.m3u
                                        if not exist "%AUDIOSCROBBLER_LOG%" (echo WARNING: "%AUDIOSCROBBLER_LOG%" does not exist!  )


                                        :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
                                        goto :skip_old_way

                                        echo *** Getting mp3 regex...
                                        :grep from audioscrobbler’s logfile on the correct computer, cut out the pre-filename+album part, pipe it to our perl script to remove the last parenthetical clause (including albums that have "(live)" at the end of their title -- this was DAMN DAMN tricky with a regex from hell), then convert id3 to filename regex, for example a question mark in a id3 should be .* for a grep against playlist filenames because "?" is not a valid filename character, then save that to afile

                                        (@grep CScrobbler::OnTrackPlay "%AUDIOSCROBBLER_LOG%"|:u8@tail -1|:u8@cut -c75-|:u8@remove-last-parenthetical-clause|:u8@convert-id3-to-filenameregex) >:u8%temp\scrobble-regex.txt
                                        type %temp\scrobble-regex.txt
                                        repeat 2 echo.

                                        echo *** Getting mp3 filename...
                                        :Now search for that regex against the playlist everything.m3u, which holds every mp3, in the correct location, convert / to \, and that is the currently playing file 
                                        if %VERBOSE == 1 echo *** grep -i "%@LINE[%temp\scrobble-regex.txt,0]" %MP3CL\LISTS\everything.m3u 
                                        (@grep -i "%@LINE[%temp\scrobble-regex.txt,0]" %MP3OFFICIAL\LISTS\everything.m3u |:u8 head /N1 |:u8 @convert-slashes-to-backslashes) >:u8%temp\scrobble-file.txt
                                        type %temp\scrobble-file.txt
                                        repeat 2 echo.

                                        echo *** Getting mp3 folder...
                                        : Now strip the filename off of the currently playing file, to get the currently playing folder
                                        (@type %temp\scrobble-file.txt |:u8 @trimfile ) >:u8%temp\scrobble-dir.txt
                                        type %temp\scrobble-dir.txt
                                        cd "%@LINE[%temp\scrobble-dir.txt,0]" 
                                        repeat 2 echo.

                                        : The attribute file will be named attrib.lst in that currently playing folder
                                        set ATTRIB="%@LINE[%temp\scrobble-dir.txt,0]attrib.lst"
                                        echo %ATTRIB >:u8%temp\scrobble-attrib_used_last.txt
                                        echo Attribute file is: 
                                        echo %ATTRIB
                                        repeat 3 echo.

                                        : Let user know if it exists
                                        if     exist %ATTRIB echo Attribute file exists.
                                        : Give them a chance to run away if it does not exist
                                        if not exist %ATTRIB (echo *** Attribute file does not exist!! %+ echo Hit ctrl-break to abort. %+ pause )
                                        :Give them folder contents...
                                        call mp3index

                                        : Edit attrib.lst in whatever folder our mp3 is playing in
                                        REM echo EC_OPT_NOEDITOR is %EC_OPT_NOEDITOR%
                                        if %EC_OPT_NOEDITOR == 1 .or. "noedit" == "%1" (unset /q EC_OPT_NOEDITOR %+ goto :NoEditor1)
                                                :%EDITOR %ATTRIB
                                                %EDITOR attrib.lst
                                        :NoEditor1

                                :skip_old_way
                                :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
                                :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
                                :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
                                :2008way
                                        echo  edit-currently-playing-attrib-helper.pl "%AUDIOSCROBBLER_LOG%" %MP3OFFICIAL\lists\everything.m3u %* {GT}%SCRIPT_TO_RUN%
                                              edit-currently-playing-attrib-helper.pl "%AUDIOSCROBBLER_LOG%" %MP3OFFICIAL\lists\everything.m3u %*    >:u8%SCRIPT_TO_RUN%
                                        goto :Run_Generated_Script
                                :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
                                :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
                                :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
                                :2009way
                                        echo  edit-currently-playing-attrib-helper.pl "%TMPMUSICSERVERCDRIVE:\Documents and Settings\oh\Local Settings\Application Data\Last.fm\Client\WinampPlugin.log" %MP3OFFICIAL\lists\everything.m3u %* {GT}%SCRIPT_TO_RUN%
                                              edit-currently-playing-attrib-helper.pl "%TMPMUSICSERVERCDRIVE:\Documents and Settings\oh\Local Settings\Application Data\Last.fm\Client\WinampPlugin.log" %MP3OFFICIAL\lists\everything.m3u %*    >:u8%SCRIPT_TO_RUN%
                                        :                                                                  T:\Documents and Settings\oh\Local Settings\Application Data\Last.fm\Client\WinampPlugin.log
                                        goto :Run_Generated_Script
                                :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
                                :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
                                :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
                                :2011way
                                        if "%HADES_DOWN"=="1" goto :HadesDown
                                        :HadesNotDown
                                        echo edit-currently-playing-attrib-helper.pl "%AUDIOSCROBBLER_LOG%" %MP3OFFICIAL\lists\everything.m3u %* {GT}%SCRIPT_TO_RUN%
                                             edit-currently-playing-attrib-helper.pl "%AUDIOSCROBBLER_LOG%" %MP3OFFICIAL\lists\everything.m3u %*    >:u8%SCRIPT_TO_RUN%
                                        goto :CallECTmp
                                        :HadesDown
                                        set AUDIOSCROBBLER_LOG=%HD128G:\Users\carolyn\AppData\Local\Last.fm\Client\Last.fm.log
                                        call validate-environment-variable AUDIOSCROBBLER_LOG
                                        echo edit-currently-playing-attrib-helper.pl "%AUDIOSCROBBLER_LOG%" %MP3OFFICIAL\lists\everything.m3u %* {GT}%SCRIPT_TO_RUN%
                                             edit-currently-playing-attrib-helper.pl "%AUDIOSCROBBLER_LOG%" %MP3OFFICIAL\lists\everything.m3u %*    >:u8%SCRIPT_TO_RUN%
                                        goto :CallECTmp
                                        :CallECTmp
                                        goto :Run_Generated_Script

rem ———————————————————————————————————————— DEPRECATED CODE ABOVE ————————————————————————————————————————
rem ———————————————————————————————————————— DEPRECATED CODE ABOVE ————————————————————————————————————————
rem ———————————————————————————————————————— DEPRECATED CODE ABOVE ————————————————————————————————————————
rem ———————————————————————————————————————— DEPRECATED CODE ABOVE ————————————————————————————————————————
rem ———————————————————————————————————————— DEPRECATED CODE ABOVE ————————————————————————————————————————





















:EOF
title %OLDTITLE%