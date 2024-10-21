@Echo Off
rem to edit self [good when testing]: %EDITOR% c:\bat\watch.bat


rem TODO: if in \MEDIA\FOR-REVIEW\DO_LATERRRRRRRRRRRRRRRRRRRRRRR\oh set to reviewing mode
rem TODO: if in reviewing mode, after watching, rn %it, then move %@NAME[%newfilename].* to ..\..\REVIEWED-NOT-PRENAMED\


rem ——————————————————————————————————————————————————————————————————————————–—————————————————————————————————————–——–——–—–——————————————————————
rem CONFIGURATION:
        set SLAY_SLUI=0                                      %+ rem Whether to run a process that kills slui.exe every second:
        set ROLL_MADVR_LOGS=0                                %+	rem For when the MadVR plugin is used, which we stopped using in 2015ish:

        set EXE_TO_SEE_IF_RUNNING=vlc.exe                    %+ rem this exe should be what's we check to see if we are stillw atching
        set VIDEOPLAYER_COMMAND=vlc                          %+ rem **JUST** the command, ****NO**** parameters
        set VIDEOPLAYER_COMMAND_FULL=call vlc -f             %+ rem the **FULL** command, ***WITH*** parameters

        set ALT_EXE_TO_SEE_IF_RUNNING=mpc-hc.exe             %+ rem \
        set ALT_VIDEOPLAYER_COMMAND=mpc                      %+ rem  >——— unused alternate values for our video player
        set ALT_VIDEOPLAYER_COMMAND_FULL=call mpc            %+ rem /
rem ——————————————————————————————————————————————————————————————————————————–—————————————————————————————————————–——–——–—–——————————————————————


rem VALIDATE ENVIRONMENT:
        if %VLC_VALIDATED ne 1 (
                call validate-environment-variable BAT SMART_HOME_COMMAND_AUDIO ANSI_COLOR_FATAL_ERROR USERPROFILE LOGS 
                call validate-in-path %VIDEOPLAYER_COMMAND% bigecho debug fix-window-title fix-winamp bring-back-focus advice fatal_error error fix-MiniLyrics  paus stop
                set VLC_VALIDATED=1
        )



rem INVOCATION FORKING:
        if "%1" == ""      (echo. %+ call bigecho "%ANSI_COLOR_FATAL_ERROR%Watch what?" %+ goto :The_Very_End) %+ rem Improper invocation —— do nothing
        if "%1" == "askyn" (         call debug   "Skipping to post-watch questions"    %+ goto :askyn       ) %+ rem jump directly to AFTER-watching questions [mostly for testing]







rem PRE-VIDEO-WATCHING SETUP:
        rem no longer necessary: call change-command-separator-character-to-normal.bat

        rem If configured, copy MadVR log to %LOGS% (which is probably c:\logs)
                if "%ROLL_MADVR_LOGS" eq "1" (
                        set        TARGET=%USERPROFILE%\Desktop\madVR - log.txt
                        if exist "%TARGET%" (%COLOR_SUBTLE% %+ echo ray|*copy "%TARGET" %LOGS% %+ %COLOR_NORMAL%)
                )
                set nopause=0

        rem Copy showname to clipboard, but allow override by setting %PROTECTCLIPBOARD% to 1
                if %PROTECTCLIPBOARD ne 1 (echo %* >clip:)


rem CHECK IF PARAMETERS ARE FILES THAT EXIST: 
	set ERROR=0
            gosub ValidateFileForWatching %1
            gosub ValidateFileForWatching %2
            gosub ValidateFileForWatching %3
            gosub ValidateFileForWatching %4
            gosub ValidateFileForWatching %5
            gosub ValidateFileForWatching %6
            gosub ValidateFileForWatching %7
            gosub ValidateFileForWatching %8
            gosub ValidateFileForWatching %9
	if "%ERROR%" eq "1" goto :END




rem ARGUMENTS CONVERTED TO SEMICOLON-DELIMITED BECAUSE THAT'S WHAT MANY COMMANDS USE:
       :echo set ARGSWITHSEMICOLONS=%1;%2;%3;%4;%5;%6;%7;%8;%9
             set ARGSWITHSEMICOLONS=%1;%2;%3;%4;%5;%6;%7;%8;%9
             set ARGSWITHSPACES=%@REPLACE[;, ,%ARGSWITHSEMICOLONS%]


rem RUN A DAEMON THAT KEEPS KILLING PROCESSES (like slui.exe) THAT TEND TO INTERRUPT OUR VIEWING BY POPPING US OUT OF FULLSCREEN MODE:
	if %SLAY_SLUI eq 1 (start /min keep-killing-if-running slui slui 30 media.player.classic exitafter)


rem START THE AMBILIGHT IF NOT ALREADY STARTED:
	REM uncomment if we ever get controllable ambilight again: if %AMBILIGHT_DOWN eq 0 (call ambilight)


rem CALL OTHER AFTER-WATCHING-STUFF SCRIPT:
	                   set MINIMIZE_AFTER=1
    if %_MONITORS gt 1 set MINIMIZE_AFTER=0
        if "%ALREADY_RAN_AFTER_SHOW%" eq "1" goto :NoAfterShow
            call after show
            set ALREADY_RAN_AFTER_SHOW=1
            window restore
        :NoAfterShow
	set MINIMIZE_AFTER=0

rem TURN OFF ANY X10 LIGHTS, IN ORDER OF ANNOYINGNESS, AND PUT BLACKLIGHTS ON:
    if "%X10_DOWN%" eq "1" goto :X10_DOWN_YES
            if "%TVLIGHTING%" eq "1" goto :TV_Lighting_Done_Already
                    :TV_Lighting_NOT_Done_Already
                            call x10 a1 on
                            call x10 a6 on
                            call x10 a4 off
                            call wait 2
                            call x10 a4 off
                           :call x10 a6 on
                            call x10 a7 off
                            call x10 a3 off
                            call x10 a2 off
                           :call x10 a1 off
                            call x10 b1 off
                            set TVLIGHTING=1
                    :TV_Lighting_Done_Already
            :Global
                call x10 a7 off
                call x10 a3 off
    :X10_DOWN_YES


rem PAUSE MUSIC SPEEDILY:
    call paus fast

    
rem TELL GOOGLE TO RUN "ok google, I'm watching TV" SMART HOME ROUTINE:

    if "%GOOGLE_ASSIST_TV_MODE_ON%" eq "1" goto :AlreadyOKGoogled
            sleep 2
            rem we cannot 'call okgoogle.bat i'm watching tv' because the synthesized voice will only trigger house routines, and our routine is a personal routine made beforeh house routines existed"
            call play-WAV-file "%BAT%\OK Google - I'm watching TV.wav"
            SET GOOGLE_ASSIST_TV_MODE_ON=1
    :AlreadyOKGoogled
	REM call paus


rem SAVE WINDOW POSITIONS:
	call save-window-positions LastWatch







rem ACTUALLY PLAY THE FILE, WAIT (PAUSE), THEN DELETE IT IF WE ARE IN A FOLDER WHOSE NAME IMPLIES THAT WE SHOULD DELETE IT: ******************************************************
        %VIDEOPLAYER_COMMAND_FULL% %*


        REM winamp moves when vlc starts and this moves it back
        call advice "NOT doing: '%italics_on%call fml.bat%italics_off%' to fix minilyrics/winamp %faint_on%[commented out 20240101]%faint_off%"






		if "%PROTECTCLIPBOARD%"=="1" goto :ProtectClipboard1
            call  fixclip
			echo %* >clip:
            call locked-message %*
        :ProtectClipboard1
	    :pause






rem DOUBLE-CHECK LIGHTS [OF ALL KINDS]:
	rem Only do x10-related lighting if it's not already done:
        if "%X10_DOWN%" eq "1" goto :X10_DOWN_YES_2
            if "%TVLIGHTING%" eq "1" goto :TV_Lighting_Done_Already_NO2
                :TV_Lighting_Done_Already_YES2
                        call wait 10
                        call x10 a6 on
                        call wait 6
                        call x10 a4 off
                        call wait 10
                        call x10 a6 on
                        call x10 b1 on
                        call x10 a7 off
                        call x10 a2 off
                        call x10 a1 on
                        set TVLIGHTING=1
                    goto :TV_Lighting_double_check_done
                :TV_Lighting_Done_Already_NO2
                        rem Even if the environment variable is set, let's ensure the blacklights are on anyway, no matter what:
                            call wait 5
                            call x10 a6 on
                            call x10 a7 off
                            call wait 5
                            call x10 a7 off
                            call wait 5
                            call x10 a7 off
                    goto :TV_Lighting_double_check_done
                :TV_Lighting_double_check_done
        :X10_DOWN_YES_2
	rem Sometimes the ambilight pop-up remains when it shouldn't, so kill it one more time:
		:call AREPopDown
		:::: ^^^^^^^^^^^ but the problem with doing this here is it generates a mouse click which removes focus from our player, causing confusion










		if "%PROTECTCLIPBOARD%"=="1" goto :ProtectClipboard2
            call  fixclip
			echo %* >clip:
        :ProtectClipboard2
	    :pause













rem THIS IS WHAT HAPPENS WHILE WE ARE WATCHING AFTER THE 2ND-PASS LIGHTING DOUBLE-CHECK. BASICALLY, WE WAIT:
        REM winamp moves when vlc starts and this moves it back
        call sleep 3
        call fix-MiniLyrics.bat
        :: Check if we are still watching 
                :Still_Watching
                        call sleep 1
                        rem call isRunning mpc-hc quiet
                        rem call isRunning mpc-hc 
                        rem call isRunningfast %EXE_TO_SEE_IF_RUNNING%
                        rem winamp moves when vlc starts and this moves it back
                if %ISRUNNING eq 1 (goto :Still_Watching)

        
rem THIS IS WHAT HAPPENS WHEN WE'RE FINALLY DONE WATCHING:
        :: done watching - bring command-line window back to front:
            window restore
			REM call fix-minilyrics-window-size-and-position
        	:202007: NOPE SO SICK OF THIS NOW!!! call restore-window-positions
            REM call advice "Type 'rwp' to restore the window positions (if they got messed up by watching this video)."
            call sleep 1
            window restore
            call bring-back-focus
            window /flash=2
            echo.


rem DISPLAY THE TIME IN CASE WE WAKE UP THE NEXT DAY WONDERING WHEN WE WENT TO SLEEP:
    echo.
        %COLOR_SUCCESS%
        call qd
    echo.



rem COPY SHOWNAME TO CLIPBOARD, FOR PASTING INTO LOG WITH EASE:
        call  fixclip
	    echo %* >clip:
        call locked-message %*
        
rem DELETE IT IF WE ARE IN A FOLDER WHOSE NAME IMPLIES THAT WE SHOULD DELETE IT:
        %COLOR_REMOVAL%
                                                                           set RENAMEIT=0
                                                                           set SMALL_VID_WATCHING=0
        if %@REGEX[DO_LATERRRRRRRRRRRRRRRRRRRRRRR\OH,%@UPPER["%_CWP"]]==1 (set SMALL_VID_WATCHING=1 %+ set RENAMEIT=1)
                                                                           set             DELETE=0
        if             %@REGEX[DELETE.AFTER.WATCHING,%@UPPER["%_CWP"]]==1 (set             DELETE=1)
        if  isdir  %*                                                     (set             DELETE=0)
        if %DELETE eq 1 (
            echos %FAINT_OFF%%EMOJI_RED_QUESTION_MARK% ``
            rem *del /p  %* has bad emoji rendering?, try this:
                *del /p  %* 
            echos %FAINT_ON%
            for %f in (%ARGSWITHSPACES%) if exist "%@NAME[%f].*" (*del /p "%@NAME[%f].*")
        )
        echos %FAINT_OFF%

        REM winamp moves when vlc starts and this moves it back
        REM call fix-MiniLyrics.bat

rem IF WE ARE IN A FOLDER THAT ALREADY HAS A WATCHED SUB-FOLDER, WE NEED TO FIND IT, AND (LATER) MOVE WHAT WE WATCHED THERE:
        :Reviewing_Small_Videos_Dir_Finding_Time
            if %SMALL_VID_WATCHING eq 1 (
                call rn %1
                set                                REVIEWED_NOT_PRENAMED=..\..\REVIEWED-NOT-PRENAMED\
                call validate-environment-variable REVIEWED_NOT_PRENAMED
                goto :Watched_Dir_Found
            )

        :Watched_Dir_Finding_Time
            unset /q WATCHEDTARGET
            if isdir        _watched                                                                       (set WATCHEDTARGET=       _watched                                                                       %+ goto :Watched_Dir_Found)
            if isdir         watched                                                                       (set WATCHEDTARGET=        watched                                                                       %+ goto :Watched_Dir_Found)
            if isdir       "_WATCHED BUT NEED TO CATALOG AS WATCHED BEFORE MOVING TO MAIN _WATCHED FOLDER" (set WATCHEDTARGET=      "_WATCHED BUT NEED TO CATALOG AS WATCHED BEFORE MOVING TO MAIN _WATCHED FOLDER" %+ goto :Watched_Dir_Found)

            if isdir     ..\_watched                                                                       (set WATCHEDTARGET=    ..\_watched                                                                       %+ goto :Watched_Dir_Found)
            if isdir      ..\watched                                                                       (set WATCHEDTARGET=     ..\watched                                                                       %+ goto :Watched_Dir_Found)
            if isdir    ..\"_WATCHED BUT NEED TO CATALOG AS WATCHED BEFORE MOVING TO MAIN _WATCHED FOLDER" (set WATCHEDTARGET=   ..\"_WATCHED BUT NEED TO CATALOG AS WATCHED BEFORE MOVING TO MAIN _WATCHED FOLDER" %+ goto :Watched_Dir_Found)
            
            if isdir  ..\..\_watched                                                                       (set WATCHEDTARGET= ..\..\_watched                                                                       %+ goto :Watched_Dir_Found)
            if isdir   ..\..\watched                                                                       (set WATCHEDTARGET=  ..\..\watched                                                                       %+ goto :Watched_Dir_Found)
            if isdir ..\..\"_WATCHED BUT NEED TO CATALOG AS WATCHED BEFORE MOVING TO MAIN _WATCHED FOLDER" (set WATCHEDTARGET=..\..\"_WATCHED BUT NEED TO CATALOG AS WATCHED BEFORE MOVING TO MAIN _WATCHED FOLDER" %+ goto :Watched_Dir_Found)
        :Watched_Dir_Found

        if "%WATCHEDTARGET%"=="" goto :DealWithWatchedDir_NO
                                 goto :DealWithWatchedDir_YES
            :DealWithWatchedDir_YES

rem PRIOR TO MOVING TO WATCHED FOLDER, IF IT'S IN A PRE-RENAMING PART OF THE WORKFLOW, GIVE AN OPPORTUNITY TO RENAME IT:
                if       %@REGEX[FOR.REVIEW,%@UPPER["%_CWP"]]==1  set RENAMEIT=1
                if %@REGEX[WATCH.BEFORE.FRA,%@UPPER["%_CWP"]]==1  set RENAMEIT=1
                if "%RENAMEIT%" eq "0" goto :RenameIt_NO
                        :RenameIt_YES
                            set AFTER_PRE=mv /p
                            set AFTER_POST=%WATCHEDTARGET%
                            %COLOR_DEBUG%  %+ for %1 in (%*) echo if exist "%@UNQUOTE[%1]" call rn "%@UNQUOTE[%1]"
                            %COLOR_NORMAL% %+ for %1 in (%*)      if exist "%@UNQUOTE[%1]" call rn "%@UNQUOTE[%1]"
                        :RenameIt_NO

rem NOW THAT WE'VE RENAMED IT AND KNOW WHERE TO MOVE IT, MOVE IT:

                :Move any files that match the names of any files that we played, but which have a different extension (subtitles, texts, etc):										
                :@ECHO ON
                    if exist %ARGSWITHSEMICOLONS%          (echos %@RANDFG[] %+ mv /p %ARGSWITHSEMICOLONS%          %WATCHEDTARGET%)
                    if exist "%@NAME[%1].*"                (echos %@RANDFG[] %+ mv /p "%@NAME[%1].*"                %WATCHEDTARGET%)
                    if exist "%@NAME[%2].*"                (echos %@RANDFG[] %+ mv /p "%@NAME[%2].*"                %WATCHEDTARGET%)
                    if exist "%@NAME[%3].*"                (echos %@RANDFG[] %+ mv /p "%@NAME[%3].*"                %WATCHEDTARGET%)
                    if exist "%@NAME[%4].*"                (echos %@RANDFG[] %+ mv /p "%@NAME[%4].*"                %WATCHEDTARGET%)
                    if exist "%@NAME[%5].*"                (echos %@RANDFG[] %+ mv /p "%@NAME[%5].*"                %WATCHEDTARGET%)
                    if exist "%@NAME[%6].*"                (echos %@RANDFG[] %+ mv /p "%@NAME[%6].*"                %WATCHEDTARGET%)
                    if exist "%@NAME[%7].*"                (echos %@RANDFG[] %+ mv /p "%@NAME[%7].*"                %WATCHEDTARGET%)
                    if exist "%@NAME[%8].*"                (echos %@RANDFG[] %+ mv /p "%@NAME[%8].*"                %WATCHEDTARGET%)
                    if exist "%@NAME[%9].*"                (echos %@RANDFG[] %+ mv /p "%@NAME[%9].*"                %WATCHEDTARGET%)
                    if exist "%@NAME[%LAST_RENAMED_TO].*"  (echos %@RANDFG[] %+ mv /p "%@NAME[%LAST_RENAMED_TO].*"  %WATCHEDTARGET%)
                :@ECHO OFF
            :DealWithWatchedDir_NO







rem WARN BEFORE WRAP-UP:
	echo.
	:NOT UNTIL LATER: window restore
    call fix-window-title

    :askyn
    echo. %+ echo. %+ echo. %+ echo. %+ echo. 

    call askyn "Run '%italics_on%after show%italics_off%'?" no
    	set MINIMIZE_AFTER=0
        if %DO_IT eq 1 (call after show)

    REM todo check if we are in a movie folder?

    call askyn "Run '%italics_on%after movie%italics_off%'?" no
    	set MINIMIZE_AFTER=0
        if %DO_IT eq 1 (call after movie)


rem UNPAUSE MUSIC:
     REM call important "Lower music volume..."
     call askyn "Unpause music?" no
        if %DO_IT eq 1 (call unpause)


rem WAKE UP WITH SOME PARTY LIGHTS:
	REM if "%TVLIGHTING%" eq "0" goto :TV_Lighting_Done_Already_NO3
	:TV_Lighting_Done_Already_YES3
        call askyn "Fix lights ('%italics_on%ok google I'm done watching tv%italics_off%')?" no
    		if %DO_IT eq 1 (
                rem call exit-maybe
                call okgoogle I'm done watching TV
                set TVLIGHTING=0
                if %X10_DOWN ne 1 (for %x10_code in (a7 a3 a4 a2 a1 a6) do (call x10 %x10_code on))
            )
	:TV_Lighting_Done_Already_NO3
 
rem FIX WINUAMP POSITION:
     REM call important "Lower music volume..."
     call askyn "Fix WinAmp position?" no
                        set FIX_WINAMP_POSITION=0
        if %DO_IT eq 1 (set FIX_WINAMP_POSITION=1)



rem COPY SHOWNAME TO CLIPBOARD (AGAIN):
	call  fixclip
	echo %* >clip:
    :::::TODO: refocus to editplus maybe sleep 1s first
    goto :END



:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
        :ValidateFileForWatching   [fileToCheck]
            if "%fileToCheck%" eq "" goto :NeverMind
            %COLOR_IMPORTANT% %+ echos %EMOJI_MAGNIFYING_GLASS_TILTED_RIGHT% Checking if file exists: '%faint%%italics%%FileToCheck%%italics_off%%faint_off%' %EMOJI_MAGNIFYING_GLASS_TILTED_LEFT%
            if ""  eq    "%fileToCheck%" goto :NeverMind
            if not exist  %fileToCheck%  goto :Exists_NO
                                         goto :Exists_YES
                    :Exists_NO
                            call FATALERROR "File %FileToCheck% does not exist!"
                            set ERROR=1
                            call print-if-debug "Goto End!"
                            goto :END
                    :Exists_YES
                            echos %ANSI_COLOR_SUCCESS%...file exists! %PARTY_POPPER%
                            call validate-file-extension %1 %filemask_video%
                            echo ...and is a valid extension! %PARTY_POPPER%
        :NeverMind
        return
        ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

                         

:END
        rem call print-message logging "Ending!"
        call fix-window-title 

rem FIX WINAMP POSITION IF WE WERE ASKED:
        if %FIX_WINAMP_POSITION eq 1 (call fix-winamp)

:The_Very_End
