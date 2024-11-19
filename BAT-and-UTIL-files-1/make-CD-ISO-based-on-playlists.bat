@on break cancel
@Echo OFF


rem FOR CAR STEROS THAT ACCEPT MP3-CDRs!!!!!

rem This create a CD-sized ramdrive andrandomly copies the files of playlists to it until the ramdrive is full. An ISO is then created.


::::: DOCUMENTATION: Behavior can be controlled by setting environment variables:
:::::       set HELPER_TOKEN_54=1                     %+ REM  Mandatory token to force you to read this documentation
:::::		set AUTOSYNCCRTL=1                        %+ REM  AutoSync[PLAYLISTNAME]=1 - to sync that playlist
:::::		set AUTOSYNCCHANGERRECENT=1               %+ REM  AutoSync the playlist named changerrecent.m3u
:::::		set AUTOSYNCCHANGER=1                     %+ REM  Autosync the playlist named changer.m3u
:::::       set COLLAPSE=1                            %+ REM set to 1 to collapse the songs into the root directory first
:::::
::::: Also, we can pass "unmount" as a command-line parameter to do an unmount only -- though we always unmount first [to be sure] in normal mode anyway:
:::::
:::::		make-CD-ISO-based-on-playlists unmount
:::::
:::::


:Pre-Setup:
    if not defined HELPER_TOKEN_54 (call alarm-beep * FATAL ERROR: This script cannot be run directly. %+ goto :END)
	pushd
	call validate-environment-variable BEST_FREE_DRIVE_LETTER
    gosub debugBlahBlah 2

:Special command-line-option-specific behavior 
    if "%1"=="RAMDrive_Fine" goto :RAMDrive_Fine
	if "%1"=="unmount" gosub unmount
	if "%1"=="unmount" goto  :END
    gosub debugBlahBlah 3

:Drive letter we will use as a temp:
	set DRIVE_TO_SYNC_TO=%BEST_FREE_DRIVE_LETTER%
    :^^^^^^^^^^^^^^^^^^^^ used X: forever, but in 2016 with drives eating up drive letters, had to change to A: in environm.bat...

:Delete and re-create ramdrive:
		:Unmount_Ramdrive
            gosub debugBlahBlah 4
			gosub unmount
            gosub debugBlahBlah 5

        :Config: [had to be moved here because gosub unmount whacks out all our temp environment variables]
            set SIZE=700M
            set DEBUG_REVIEW_ZERO_BYTE_FILES_AFTER_CREATION=0
            set NO_WIPE=1
            gosub debugBlahBlah 1
            call validate-environment-variables SIZE 
            :call validate-environment-variables DRIVE

        :RAMDrive_Create
                             set    RAMDISKCOMMAND=  call imdisk.bat -a -s %SIZE% -m %DRIVE_TO_SYNC_TO: -p "/fs:ntfs /q /y"
            %COLOR_DEBUG% %+ echo * RAMDISK Command: %RAMDISKCOMMAND%
            pause
			%COLOR_RUN%   %+                         %RAMDISKCOMMAND%

        :RAMDrive_Validate
            :RAMDrive_Check
            if "%@READY[%DRIVE_TO_SYNC_TO%]" eq "1" goto :RAMDrive_Fine
                %COLOR_ALARM%
                echo * WARNING: RAMDRIVE %DRIVE_TO_SYNC_TO% IS NOT READY!!!
                call white-noise 1
                delay 1
                goto :RAMDrive_Check
            :RAMDrive_Fine

		:RAMDrive_Label
			call now
            %COLOR_DEBUG% %+ echo label %DRIVE_TO_SYNC_TO%: %YYYYMMDD%
            %COLOR_RUN%   %+      label %DRIVE_TO_SYNC_TO%: %YYYYMMDD%
			window restore                            %+ REM (winamp grabs focus when the drive is created, so grab it back)

        :Setup file structure for sync
		md                                   %DRIVE_TO_SYNC_TO%:\mp3\
				                            >%DRIVE_TO_SYNC_TO%:\"__ mp3 holder __"                    
				                            >%DRIVE_TO_SYNC_TO%:\"__ mp3 sync option - no playlists __"
				                            >%DRIVE_TO_SYNC_TO%:\"__ mp3 sync option - do not ask for wipe __"
				                            >%DRIVE_TO_SYNC_TO%:\"__ mp3 sync option - do not check for free space __"
		if "%COLLAPSE%"              eq "1" >%DRIVE_TO_SYNC_TO%:\"__ mp3 sync option - collapse __"                    
        if "%AUTOSYNCCRTL%"          eq "0" >%DRIVE_TO_SYNC_TO%:\"__ mp3 sync option - do not auto-sync CRTL __" 
		if "%AUTOSYNCCRTL%"          eq "0" >%DRIVE_TO_SYNC_TO%:\"__ mp3 sync option - sync never - CRTL __"
		if "%AUTOSYNCOH%"            ne "0" >%DRIVE_TO_SYNC_TO%:\"__ mp3 sync option - sync automatically - oh __"
		if "%AUTOSYNCPARTY%"         eq "0" >%DRIVE_TO_SYNC_TO%:\"__ mp3 sync option - sync never - party __"
		if "%AUTOSYNCBEST%"          eq "0" >%DRIVE_TO_SYNC_TO%:\"__ mp3 sync option - sync never - best __"
		if "%AUTOSYNCCHANGERRECENT%" eq "0" >%DRIVE_TO_SYNC_TO%:\"__ mp3 sync option - sync never - changerrecent __"
		if "%AUTOSYNCCHANGER%"       eq "0" >%DRIVE_TO_SYNC_TO%:\"__ mp3 sync option - sync never - changer __"

        :Review_The_Drive_So_Far
        %COLOR_SUCCESS% %+ echo. %+ dir %DRIVE_TO_SYNC_TO%:\ 
        if "%DEBUG_REVIEW_ZERO_BYTE_FILES_AFTER_CREATION%" eq "1" (color red on black %+ echo * Pausing because DEBUG_REVIEW_ZERO_BYTE_FILES_AFTER_CREATION=1 %+ color white on black %+ pause)

        :Do_IT!!
		set  SYNCONLY=%DRIVE_TO_SYNC_TO%
		call sync-music %+ unset ALREADY_SYNCED_%BEST_FREE_DRIVE_LETTER%



:Review the drive
	echo.
	echo.
    %COLOR_IMPORTANT %+ echo Let's review the drive... (%DRIVE_TO_SYNC_TO%:\_* will be erased after this) 
                     %+ pause 
    %COLOR_SUCCESS%  %+ dir %DRIVE_TO_SYNC_TO%:\ /s %+ echo. %+ echo.
	%COLOR_PROMPT    %+ echo Describe this CD, if you'd like (date will already be inserted, this is description ONLY):
	%COLOR_INPUT%    %+ set  DESCRIPTION=. %+ eset DESCRIPTION

:Clean up the mess:
	%DRIVE_TO_SYNC_TO%:
	cd \
    %COLOR_REMOVAL%
	rd mp3
	(echo yryryr | *del %DRIVE_TO_SYNC_TO%:\__*)


:Make an ISO:
	set ISO=c:\mp3-700M-playlist_sync-%YYYYMMDD%-%DESCRIPTION%.iso
    %COLOR_RUN%
	mkisofs -r -o "%ISO%" %DRIVE_TO_SYNC_TO%:\

:Copy the ISO to the place where ISOs that need to be burned await their death sentence:
	set               TARGETDRIVE=%HD2000G5%
	if  not   exist  %TARGETDRIVE%:\ABOUT-TO-BE-BURNED\DATA       md %TARGETDRIVE%:\ABOUT-TO-BE-BURNED\DATA      
	if  not   exist  %TARGETDRIVE%:\ABOUT-TO-BE-BURNED\DATA\MUSIC md %TARGETDRIVE%:\ABOUT-TO-BE-BURNED\DATA\MUSIC
	set       TARGET=%TARGETDRIVE%:\ABOUT-TO-BE-BURNED\DATA\MUSIC 
    %COLOR_REMOVAL%
	mv "%ISO%" %TARGET%

:Unmount:
    %COLOR_WARNING% %+ 	echos Time to unmount. ``
    %COLOR_ADVICE%  %+  echo Ctrl-break if you don't want to do that.
    pause
	gosub        unmount
goto :END


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    :unmount
        :first we do the graceful, then we do the forceful:
        start unmount-ramdisk %DRIVE_TO_SYNC_TO% exitafter
        delay 3
    return
    ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    :debugBlahBlah [num]
        color bright yellow on cyan %+ echo [debug][%0][%num%] SIZE=%size%,NO_WIPE=%NO_WIPE% %+ color white on black
    return
    :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


:END
	popd
	%COLOR_WARNING% %+ echo Testing phase almost done: Is the drive label for %DRIVE_TO_SYNC_TO% correct and is the drive label for the drive we're on still correct? %+ %COLOR_NORMAL%
    unset /q HELPER_TOKEN_54	
    unset /q NO_WIPE
    unset /q SIZE
    unset /q DEBUG_REVIEW_ZERO_BYTE_FILES_AFTER_CREATION
    c: