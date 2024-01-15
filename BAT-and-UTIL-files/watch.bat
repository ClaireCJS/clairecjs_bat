@Echo Off
:Edit self [good when testing]: %EDITOR% c:\bat\watch.bat


set ROLL_MADVR_LOGS=0      


                         ::: PRE-2014 STUFF (HAHA):
                         :::  @Echo OFF
                         :::  call vw nobackup
                         :::  call after show
                         :::  call after coincidence

::::: SHORT-CIRCUITING:
    if "%1" == ""      (goto :The_Very_End)
    if "%1" == "askyn" (goto :askyn       )

::::: CONFIGURATION:
	::::: The preferred videoplayer of the moment:
	         set VIDEOPLAYER=call vlc -f
             set EXE_TO_SEE_IF_RUNNING=vlc.exe

	::::: The 2nd-favorite videoplayer of the moment:
	         set ALT_VIDEOPLAYER=call mpc 
             set ALT_EXE_TO_SEE_IF_RUNNING=mpc-hc.exe


	::::: Whether to run a process that kills slui.exe every second:
             set SLAY_SLUI=0






::::: SETUP:
	call nocar
    if "%ROLL_MADVR_LOGS" eq "1" (call roll-log-madvr)
    set nopause=0









		if "%PROTECTCLIPBOARD%"=="1" goto :ProtectClipboard2
			echo %* >clip:
						  :ProtectClipboard2
	       :pause















::::: CHECK IF PARAMETERS ARE FILES THAT EXIST:
	set ERROR=0
		gosub checkiffileexists %1
		gosub checkiffileexists %2
		gosub checkiffileexists %3
		gosub checkiffileexists %4
		gosub checkiffileexists %5
		gosub checkiffileexists %6
		gosub checkiffileexists %7
		gosub checkiffileexists %8
		gosub checkiffileexists %9
	if "%ERROR%" eq "1" goto :END


::::: CHECK IF THIS IS EVEN A FILE WE CAN PLAY:
                                              set DONOTPLAY=0
        if "%@REGEX[.IDX,%@UPPER[%*]]" eq "1" set DONOTPLAY=1
	    if                         "1" eq       "%DONOTPLAY%" goto :Play_Cannot
	                                                          goto :Play_Can
				:Play_Cannot
					call fatal_error "Can't play this kind of file."
					goto :END
				:Play_Can



::::: ARGUMENTS CONVERTED TO SEMICOLON-DELIMITED BECAUSE THAT'S WHAT MANY COMMANDS USE:
       :echo set ARGSWITHSEMICOLONS=%1;%2;%3;%4;%5;%6;%7;%8;%9
             set ARGSWITHSEMICOLONS=%1;%2;%3;%4;%5;%6;%7;%8;%9
             set ARGSWITHSPACES=%@REPLACE[;, ,%ARGSWITHSEMICOLONS%]


::::: RUN A DAEMON THAT KEEPS KILLING PROCESSES (like slui.exe) THAT TEND TO INTERRUPT OUR VIEWING BY POPPING US OUT OF FULLSCREEN MODE:
	if %SLAY_SLUI eq 1 (start /min keep-killing-if-running slui slui 30 media.player.classic exitafter)


::::: START THE AMBILIGHT IF NOT ALREADY STARTED:
	REM uncomment if we ever get controllable ambilight again: if %AMBILIGHT_DOWN eq 0 (call ambilight)


::::: CALL OTHER AFTER-WATCHING-STUFF SCRIPT:
	                   set MINIMIZE_AFTER=1
    if %_MONITORS gt 1 set MINIMIZE_AFTER=0
        if "%ALREADY_RAN_AFTER_SHOW%" eq "1" goto :NoAfterShow
            call after show
            set ALREADY_RAN_AFTER_SHOW=1
            window restore
        :NoAfterShow
	set MINIMIZE_AFTER=0

::::: TURN OFF ANY X10 LIGHTS, IN ORDER OF ANNOYINGNESS, AND PUT BLACKLIGHTS ON:
    if "%X10_DOWN%" eq "1" goto :X10_DOWN_YES
            if "%TVLIGHTING%" eq "1" goto :TV_Lighting_Done_Already
                    :TV_Lighting_NOT_Done_Already
                            call x10 a1 on
                            call x10 a6 on
                            call x10 a4 off
                            call  sleep  2
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

::::: PAUSE MUSIC:
    call stop fast
    if "%GOOGLE_ASSIST_TV_MODE_ON%" eq "1" goto :AlreadyOKGoogled
        sleep 2
        call okgoogle i'm watching tv
        SET GOOGLE_ASSIST_TV_MODE_ON=1
    :AlreadyOKGoogled
	REM call paus


::::: SAVE WINDOW POSITIONS:
	call save-window-positions LastWatch







::::: ACTUALLY PLAY THE FILE, WAIT (PAUSE), THEN DELETE IT IF WE ARE IN A FOLDER WHOSE NAME IMPLIES THAT WE SHOULD DELETE IT: ******************************************************
        :all wrapper %VIDEOPLAYER% %*
        call         %VIDEOPLAYER% %*


        REM winamp moves when vlc starts and this moves it back
        call advice "NOT doing: '%italics_on%call fml.bat%italics_off%' to fix minilyrics/winamp %faint_on%[commented out 20240101]%faint_off%"






		if "%PROTECTCLIPBOARD%"=="1" goto :ProtectClipboard1
            call  fixclip
			echo %* >clip:
        :ProtectClipboard1
	    :pause






::::: DOUBLE-CHECK LIGHTS [OF ALL KINDS]:
	::::: Only do x10-related lighting if it's not already done:
        if "%X10_DOWN%" eq "1" goto :X10_DOWN_YES_2
            if "%TVLIGHTING%" eq "1" goto :TV_Lighting_Done_Already_NO2
                :TV_Lighting_Done_Already_YES2
                        call sleep 10
                        call x10 a6 on
                        call sleep 6
                        call x10 a4 off
                        call sleep 10
                        call x10 a6 on
                        call x10 b1 on
                        call x10 a7 off
                        call x10 a2 off
                        call x10 a1 on
                        set TVLIGHTING=1
                    goto :TV_Lighting_double_check_done
                :TV_Lighting_Done_Already_NO2
                        ::::: Even if the environment variable is set, let's ensure the blacklights are on anyway, no matter what:
                            call sleep 5
                            call x10 a6 on
                            call x10 a7 off
                            call sleep 5
                            call x10 a7 off
                            call sleep 5
                            call x10 a7 off
                    goto :TV_Lighting_double_check_done
                :TV_Lighting_double_check_done
        :X10_DOWN_YES_2
	::::: Sometimes the ambilight pop-up remains when it shouldn't, so kill it one more time:
		:call AREPopDown
		:::: ^^^^^^^^^^^ but the problem with doing this here is it generates a mouse click which removes focus from our player, causing confusion










		if "%PROTECTCLIPBOARD%"=="1" goto :ProtectClipboard2
            call  fixclip
			echo %* >clip:
        :ProtectClipboard2
	    :pause













::::: THIS IS WHAT HAPPENS WHILE WE ARE WATCHING, AFTER THE 2ND-PASS LIGHTING DOUBLE-CHECK. BASICALLY, WE WAIT:
        REM winamp moves when vlc starts and this moves it back
        call sleep 3
        call fml.bat
        :: Check if we are still watching 
            :Still_Watching
                call sleep 1
                :all isRunning mpc-hc quiet
                :all isRunning mpc-hc 
                call isRunningfast %EXE_TO_SEE_IF_RUNNING%
                REM winamp moves when vlc starts and this moves it back

            if %ISRUNNING eq 1 (goto :Still_Watching)
        :: done watching - bring command-line window back to front:
            window restore
			REM call fix-minilyrics-window-size-and-position
        	:202007: NOPE SO SICK OF THIS NOW!!! call restore-window-positions
            REM call advice "Type 'rwp' to restore the window positions (if they got messed up by watching this video)."

            call sleep 1
            window restore
            window /flash=2
            echo.


::::: DISPLAY THE TIME IN CASE WE WAKE UP THE NEXT DAY WONDERING WHEN WE WENT TO SLEEP:
    echo.
        %COLOR_SUCCESS%
        call qd
    echo.



::::: COPY SHOWNAME TO CLIPBOARD, FOR PASTING INTO LOG WITH EASE:
        call  fixclip
	    echo %* >clip:
        
::::: DELETE IT IF WE ARE IN A FOLDER WHOSE NAME IMPLIES THAT WE SHOULD DELETE IT:
        %COLOR_REMOVAL%
                                                               set DELETE=0
        if %@REGEX[DELETE.AFTER.WATCHING,%@UPPER["%_CWP"]]==1  set DELETE=1
        if isdir %*                                            set DELETE=0
        if %DELETE eq 1 (
            echos %FAINT_OFF%
            *del /p  %*
            echos %FAINT_ON%
            for %f in (%ARGSWITHSPACES%) if exist "%@NAME[%f].*" *del /p "%@NAME[%f].*"
        )
        echos %FAINT_OFF%

        REM winamp moves when vlc starts and this moves it back
        REM call fml.bat

::::: IF WE ARE IN A FOLDER THAT ALREADY HAS A WATCHED SUB-FOLDER, WE NEED TO FIND IT, AND (LATER) MOVE WHAT WE WATCHED THERE:
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

::::: PRIOR TO MOVING TO WATCHED FOLDER, IF IT'S IN A PRE-RENAMING PART OF THE WORKFLOW, GIVE AN OPPORTUNITY TO RENAME IT:
                                                                  set RENAMEIT=0
                if       %@REGEX[FOR.REVIEW,%@UPPER["%_CWP"]]==1  set RENAMEIT=1
                if %@REGEX[WATCH.BEFORE.FRA,%@UPPER["%_CWP"]]==1  set RENAMEIT=1
                if "%RENAMEIT%" eq "0" goto :RenameIt_NO
                        :RenameIt_YES
                            set AFTER_PRE=mv /p
                            set AFTER_POST=%WATCHEDTARGET%
                            %COLOR_DEBUG%  %+ for %1 in (%*) echo if exist "%@UNQUOTE[%1]" call rn "%@UNQUOTE[%1]"
                            %COLOR_NORMAL% %+ for %1 in (%*)      if exist "%@UNQUOTE[%1]" call rn "%@UNQUOTE[%1]"
                        :RenameIt_NO

::::: NOW THAT WE'VE RENAMED IT AND KNOW WHERE TO MOVE IT, MOVE IT:

                :Move any files that match the names of any files that we played, but which have a different extension (subtitles, texts, etc):										
                :@ECHO ON
                    if exist %ARGSWITHSEMICOLONS% (mv /p %ARGSWITHSEMICOLONS% %WATCHEDTARGET%)
                    if exist "%@NAME[%1].*"       (mv /p "%@NAME[%1].*"       %WATCHEDTARGET%)
                    if exist "%@NAME[%2].*"       (mv /p "%@NAME[%2].*"       %WATCHEDTARGET%)
                    if exist "%@NAME[%3].*"       (mv /p "%@NAME[%3].*"       %WATCHEDTARGET%)
                    if exist "%@NAME[%4].*"       (mv /p "%@NAME[%4].*"       %WATCHEDTARGET%)
                    if exist "%@NAME[%5].*"       (mv /p "%@NAME[%5].*"       %WATCHEDTARGET%)
                    if exist "%@NAME[%6].*"       (mv /p "%@NAME[%6].*"       %WATCHEDTARGET%)
                    if exist "%@NAME[%7].*"       (mv /p "%@NAME[%7].*"       %WATCHEDTARGET%)
                    if exist "%@NAME[%8].*"       (mv /p "%@NAME[%8].*"       %WATCHEDTARGET%)
                    if exist "%@NAME[%9].*"       (mv /p "%@NAME[%9].*"       %WATCHEDTARGET%)
                :@ECHO OFF
            :DealWithWatchedDir_NO







::::: WARN BEFORE WRAP-UP:
	echo.
	:NOT UNTIL LATER: window restore
    call fix-window-title

    :askyn
    echo. %+ echo. %+ echo. %+ echo. %+ echo. 

    call askyn "Run 'after show'?" no
    	set MINIMIZE_AFTER=0
        if %DO_IT eq 1 (call after show)

    REM todo check if we are in a movie folder?

    call askyn "Run 'after movie'?" no
    	set MINIMIZE_AFTER=0
        if %DO_IT eq 1 (call after movie)


::::: UNPAUSE MUSIC:
     REM call important "Lower music volume..."
     call askyn "Unpause music?" no
        if %DO_IT eq 1 (call unpause)


::::: WAKE UP WITH SOME PARTY LIGHTS:
	REM if "%TVLIGHTING%" eq "0" goto :TV_Lighting_Done_Already_NO3
	:TV_Lighting_Done_Already_YES3
        call askyn "Fix lights ('ok google I'm done watching tv')?" no
    		if %DO_IT eq 1 (
                rem call exit-maybe
                call okgoogle I'm done watching TV
                set TVLIGHTING=0
                if %X10_DOWN ne 1 (for %x10_code in (a7 a3 a4 a2 a1 a6) do (call x10 %x10_code on))
            )
	:TV_Lighting_Done_Already_NO3
 
::::: FIX WINUAMP POSITION:
     REM call important "Lower music volume..."
     call askyn "Fix WinAmp position?" no
                        set FIX_WINAMP_POSITION=0
        if %DO_IT eq 1 (set FIX_WINAMP_POSITION=1)



::::: COPY SHOWNAME TO CLIPBOARD (AGAIN):
	call  fixclip
	echo %* >clip:
    :::::TODO: refocus to editplus maybe sleep 1s first
    goto :END



:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

	::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
	:CheckIfFileExists   [fileToCheck]
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
                %color_success %+ echo ...file exists! %PARTY_POPPER%
	:NeverMind
	return
	::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

                         

:END
    rem call print-message logging "Ending!"
    call fix-window-title

::::: FIX WINAMP POSITION IF WE WERE ASKED:
        if %FIX_WINAMP_POSITION eq 1 (call fw)


:The_Very_End
