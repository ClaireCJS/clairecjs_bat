@Echo Off
 on break cancel




:::::::::::::: POSSIBLE PLAN: ADD REVERT ACTION.
:::::::::::::: SIMPLY PIPE TO FILTERSCRIPT TWICE, BUT SECOND TIME PASS AN ARG OR ENVVAR FOR REVERSING IT
:::::::::::::: ALLFILE1.PL  OR WHATEVER would simply check this and invert itself.


:::::::::::::: **** set SWEEPING=1         --- suppresses pauses
:::::::::::::: **** SET NO_PRESCRUB=1      --- skip prescrub, great for successive renames
:::::::::::::: **** set ADDITIONAL_FILENAME_DESCRIPTOR=Chrysler to prefix "Chrysler - " during an allfiles exif time

:: NEW: 2023:
    :: USAGE: allfiles unicode       --- automatically rename away all unicode bullshit

:: USED COMMONLY:
    :: USAGE: allfiles mv            --- to rename all files via text editor
    :: USAGE: allfiles mv /s         --- to rename all files via text editor recursing folders
    :: USAGE: allfiles exif          --- to rename all files via exif date
    :: USAGE: allfiles exif time     --- to rename all files via exif date AND time
    :: USAGE: allfiles wav2mp3       --- to create script using ffmpeg
    :: USAGE: allfiles wav2mp3old    --- to create script using old internal ways (wav2mp3.bat - ripped wav mode (unlabelled=VBR))

:: USED OCCASIONALLY:
    :: USAGE: allfiles               --- to run script based on filenames
    :: USAGE: allfiles /ad           --- to run script based on dirnames (MAY NOT WORK RIGHT)

:: USED RARELY:
    :: USAGE: allfiles filedate      --- to rename all files via file date
    :: USAGE: allfiles filedate time --- to rename all files via file date AND time
    :: USAGE: allfiles mv hyphenswap --- to rename all "x - y" files as "y - x"
    :: USAGE: allfiles /ad mv        --- to rename all dirs via text editor (PROBABLY WONT WORK RIGHT)

:: USED NOT REALLY ANYMORE: PRACTICES NO LONGER PRACTICED:
    :: USAGE: allfiles wav2mp3 /D    --- to create script using wav2mp3.bat - downloaded wav mode (unlabelled=128 CBR)
    :: USAGE: allfiles master        --- to rename all files limiting characters per filename for media burning

:: USED NOT REALLY ANYMORE: SUPERCEDED:
    :: USAGE: allfiles avi2wav       --- to create script using avi2wav.exe - USE GENERALLY SUPERSECED BY EXTRACT-ALL-WAVS.BAT
    :: USAGE: allfiles flac2wav      --- to create script using avi2wav.exe - USE GENERALLY SUPERSECED BY EXTRACT-ALL-WAVS.BAT
    :: USAGE: allfiles mp32wav       --- to create script using mp32wav.bat - USE GENERALLY SUPERSECED BY EXTRACT-ALL-WAVS.BAT
    :: USAGE: allfiles mpc2wav       --- to create script using mpc2wav.bat - USE GENERALLY SUPERSECED BY EXTRACT-ALL-WAVS.BAT


rem Environment validation
         call environm %+ REM this one doesn't seem to hang on stale command lines for some reason
         setdos /X0

        ::::: These need to be defined if not already.  For me, perl.exe is
        ::::: already in my path so I don't need to specify it's directory,
        ::::: but some people may need to:
             if "%BAT"    == "" SET    BAT=c:\bat
             if "%PERL"   == "" SET   PERL=perl
            :if "%EDITOR" == "" SET EDITOR=notepad
            call validate-environment-variables  PERL  BAT EDITOR 
            call validate-in-path               %PERL%

:ErrorCheck
    call set-drive-related-environment-variables
   if "%[%DRIVEHD%_SSD]" eq "1" goto :ssdwarn_yes
                                goto :ssdwarn_no
                :ssdwarn_yes
                    %COLOR_WARNING% %+ echo. %+ echo. %+ echo. %+ echo. %+ echo.
                    echo Do you really want to run this on an SSD? %+ echo.
                    %COLOR_ADVICE% %+ echo   It should actually be fine as long as the files you are renaming are ACTUALLY on the ssd and not some junction.
                    echo. %+ echo. %+ echo.
                    :2022 let's stop this pause madness pause
                    %COLOR_NORMAL%
                    goto :ssdwarn_done
                :ssdwarn_no
                    if "%DEBUG_SSDWARN%" eq "1" goto :SayWeAreFine        
                                                goto :ssdwarn_done
                        :SayWeAreFine
                        %COLOR_DEBUG%  %+ echo * Not an SSD. Should be fine.
                        %COLOR_NORMAL% %+ pause
                :ssdwarn_done
if "%DEBUG_SSDWARN%" eq "1" goto :END


:Initialize
    ::::: DETERMINE SOME TEMP FILES:
    rem have to erase windows\temp because fuckin @UNIQUE isn't always unique!
    %COLOR_UNIMPORTANT%
    echos %ANSI_OVERSTRIKE_ON%
    if exist c:\windows\temp\*.*          (echo yr |:u8 *del /q /e c:\windows\temp\*.*         )
    if exist c:\windows\temp\avginfo.id	  (echo yr |:u8 *del /q /e c:\windows\temp\avginfo.id  )
    if exist c:\windows\temp\MpCmdRun.log (echo yr |:u8 *del /q /e c:\windows\temp\MpCmdRun.log)
    if exist c:\recycled\MpCmdRun.log	  (echo yr |:u8 *del /q /e c:\recycled\MpCmdRun.log    )
    set tmp=c:\recycled\
    if "%DEBUG%" eq "1" (%COLOR_DEBUG% %+ echo * tmp directory is %tmp %+ %COLOR_NORMAL%)
    SET TMP1=%@UNIQUE[%tmp]
    SET TMP2=%@UNIQUE[%tmp]
    SET TMP3=%@UNIQUE[%tmp]
    SET TMP4=%@UNIQUE[%tmp]
    SET TMP5=%TMP4.bat
    SET FILTERSCRIPT=type
    SET CALLINGDIR=%_CWD
    set LATESTALLFILES1=c:\recycled\latest-allfiles-%_PID.bat
    set LATESTALLFILES2=c:\recycled\latest-allfiles.bat
    if "%DEBUG%" eq "1"  (%COLOR_DEBUG% %+ echo %%_CWD is "%_cwd" %+ %COLOR_NORMAL% %+ echo on)
    set VALIDATE_LINES=0

::::: SET DEFAULT DIRECTORY COMMAND:
    SET TMPDIRCMD=/ba-d-h
    set RECURSIVEMOVE=0
    set HYPHENSWAP=0
    if "%2" eq "/s"         (set RECURSIVEMOVE=1 %+ set TMPDIRCMD=%TMPDIRCMD% /s)
    if "%2" eq "hyphenswap" (set RECURSIVEMOVE=0 %+ set HYPHENSWAP=1)

    rem # Since "/ad" is the "dir" way to list just directories, I'm going to use
    rem # this as a way to *include* directories *also* with files, since sometimes
    rem # I like to use allfiles to mess with directories too, not just files.
    if "%1"=="/ad" SET TMPDIRCMD=/b


::::: SOME SCRIPTS DON'T RUN FROM THE SAME PATTERN, AND CALL OUTWARD TO OTHER UTILITIES:
        if "%1"=="mp32wav"  (set SWEEPING=1 %+ goto  :mp32wav_prescrub)


::::: GENERATE FILE LIST USING DETERMINED "dir" OPTIONS:
    :ir %TMPDIRCMD >    %TMP1 ------- 20221119, adding unicode support by changing to the ">:u8" UTF-8-exclusive redirector:
    dir %TMPDIRCMD >:u8 %TMP1
    %COLOR_LOGGING% %+ *copy %TMP1 c:\recycled\latest-allfiles-dircmd-output.txt
    %COLOR_NORMAL%


:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:Replicate
    : I keep the original names in the 2nd temp file for "allfiles mv" purposes
    %COLOR_UNIMPORTANT%
    *copy %TMP1 %TMP2
    %COLOR_NORMAL%

::::: Pre-Scrub, if necessary
    if "%1"=="oops"       (               %+ goto :recover                   )
    if "%1"=="retry"      (               %+ goto :recover                   )
    if "%1"=="recover"    (               %+ goto :recover                   )
    if "%1"=="mv"         (               %+ goto :allfiles_mv_prescrub      )
    if "%1"=="exif"       (               %+ goto :allfiles_exif_prescrub    )
    if "%1"=="filedate"   (               %+ goto :allfiles_filedate_prescrub)
    if "%1"=="master"     (               %+ goto :allfiles_master_prescrub  )
    if "%1"=="unicode"    (               %+ goto :allfiles_unicode          )
    if "%1"=="flac2wav"   (set SWEEPING=1 %+ goto :flac2wav_prescrub         )
    if "%1"=="mp32wav"    (set SWEEPING=1 %+ goto :mp32wav_prescrub          )
    if "%1"=="mpc2wav"    (set SWEEPING=1 %+ goto :mpc2wav_prescrub          )
    if "%1"=="wav2mp3"    (set SWEEPING=1 %+ goto :wav2mp3_ffmpeg            )
    if "%1"=="wav2mp3old" (set SWEEPING=1 %+ goto :wav2mp3_prescrub          )
    if "%1"=="avi2wav"    (set SWEEPING=1 %+ goto :avi2wav_prescrub          )
    if "%1"=="wav2avi"    (set SWEEPING=1 %+ goto :wav2avi_prescrub          )
    if "%1"=="flac2mp3"   (set SWEEPING=1 %+ goto :flac2mp3_ffmpeg           )
goto :Edit
::::::::::::::::::::::::::::::::::::::::::::::::::::::::


:::::::::::::::::::::::::::::::
:wav2mp3_ffmpeg
    call allwav2mp3.bat %*
goto :END
:::::::::::::::::::::::::::::::
:::::::::::::::::::::::::::::::
:flac2mp3_ffmpeg
    call allflac2mp3.bat %*
goto :END
:::::::::::::::::::::::::::::::


:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:recover
    ::::: sometimes start.exe fails to actually *start* the process (That's windows for ya.)  
    ::::  So we must use our recovered-copy:
        :call c:\recycled\latest-allfiles.bat noexit
         %EDITOR%        %LATESTALLFILES1%    
         call            %LATESTALLFILES1%    noexit
goto :END
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:allfiles_mv_prescrub
    set VALIDATE_LINES=1



    rem This prescrub does things like removes underscores, capitalizes each word 
    rem THIS IS THE MEAT! 99% OF THE TIME WE CAL THIS SCRIPT, THIS IS WHAT WE'RE DOING:
    set FILTERSCRIPT=%BAT%\allfilesmv.pl

  
    rem If our task is simply swapping what's before/after hyphens in filenames, change the filterscript accordingly:
    if "%HYPHENSWAP%" eq "1" (set FILTERSCRIPT=%BAT%\allfilesHyphenswap.pl)

    rem This encourages development:
    if "%@UPPER[%USERNAME%]" ne "CAROLYN" .and. "%SWEEPING%" ne "1" .and. "%ALLFILESNOSCRIPTEDIT%" ne "1" call editplus %FILTERSCRIPT%
goto :do_prescrub
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


:::::::::::::::::::::::::::::::::::::::::::
:allfiles_exif_prescrub
    set VALIDATE_LINES=1
    : This prescrub does things like removes underscores, capitalizes each word
    set ADDTIME=0
    if "%2"=="time" set ADDTIME=1
    REM: trigger used for workflows
    >"__ done - allfiles exif time __"
    set FILTERSCRIPT=%BAT%\allfileexif.pl
    : This encourages development:
goto :do_prescrub
:::::::::::::::::::::::::::::::::::::::::::
:allfiles_filedate_prescrub
    set VALIDATE_LINES=1
    : This prescrub just deals with putting the date of the file ahead of there
    set ADDTIME=0
    if "%2"=="time" set ADDTIME=1
    set FILTERSCRIPT=%BAT%\allfilefiledate.pl
    : This encourages development:
goto :do_prescrub

:::::::::::::::::::::::::::::::::::::::::::
:allfiles_master_prescrub
    set VALIDATE_LINES=1
    : This prescrub does things to make files suitable for burning
    set FILTERSCRIPT=%BAT%\allfilem.pl
    : This encourages development:
    %EDITOR% %FILTERSCRIPT%
goto :do_prescrub
:::::::::::::::::::::::::::::::::::::::::::
:::::::::::::::::::::::::::::::::::::::::::
:avi2wav_prescrub
    set FILTERSCRIPT=%BAT%\allfilea2w.pl
goto :do_prescrub
:::::::::::::::::::::::::::::::::::::::::::
:::::::::::::::::::::::::::::::::::::::::::
:wav2avi_prescrub
    set FILTERSCRIPT=%BAT%\allfilew2a.pl
goto :do_prescrub
:::::::::::::::::::::::::::::::::::::::::::
:::::::::::::::::::::::::::::::::::::::::::
:wav2mp3_prescrub
    set FILTERSCRIPT=%BAT%\allfilew2m.pl
goto :do_prescrub
:::::::::::::::::::::::::::::::::::::::::::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:mp32wav_prescrub
echo asefasdfads ^ pause
    set FILTERSCRIPT=%BAT%\allfilem2w.pl
    ::^^^^^^^^^^^^^^ WE ARE NOT USING THIS! JUST HERE FOR HISTORICAL PURPOSES. DOESN'T ACTUALLY WORK.
    call extract-all-WAVs-from-audio-files.bat %*
    goto :CleanUp
goto :do_prescrub
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:::::::::::::::::::::::::::::::::::::::::::
:mpc2wav_prescrub
    set FILTERSCRIPT=%BAT%\allfilemp2w.pl
goto :do_prescrub
:::::::::::::::::::::::::::::::::::::::::::
:::::::::::::::::::::::::::::::::::::::::::
:flac2wav_prescrub
    set FILTERSCRIPT=%BAT%\allfilef2w.pl
goto :do_prescrub
:::::::::::::::::::::::::::::::::::::::::::
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:allfiles_unicode_prescrub_OLD
    :: not sure if this really applies for this situation:
    set VALIDATE_LINES=1 
    set SKIPEDIT_OLD=%SKIPEDIT%
    set SKIPEDIT=1
    set SKIPWARN=1
    set STARTWITHCALL=1
    set NOEXITINTERNAL=1
    set NOCLS=1
    : This prescrub does things to make files suitable for burning
    set FILTERSCRIPT=%BAT%\allfileunicode.pl
    : This encourages development:
    : %EDITOR% %FILTERSCRIPT%
goto :do_prescrub
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::


::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
REM This example breaks off from previous examples in not relying on any of the other
REM infrascructure/variables that the rest of this script uses. Too many bad practices
REM added up and it's just easier to manage it all here:
:allfiles_unicode
    set BAT=fixfixfix.bat
    if exist %BAT (%COLOR_ERROR% %+ echo Uhoh! %BAT% already exists! %+ goto :END)
    dir /b |:u8 allfileunicode.pl >:u8 %BAT%
    call %BAT%
    echo yr  |:u8 mv %BAT% \recycled
    : This encourages development:
    : %EDITOR% %FILTERSCRIPT%
goto :Cleanup
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::




::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:do_prescrub
	::::: 20221119 
    %COLOR_UNIMPORTANT% %+      *copy                       %TMP1% c:\recycled\latest-allfiles-filelist-just-before-filterscript.txt
    %COLOR_UNIMPORTANT% %+      *copy                       %TMP1%                                %TMP3%   %+ REM copy file before filtering it, so if filter hangs and is aborted, this can continue with unfiltered version of output
    %COLOR_DEBUG%       %+ echo %PERL% -CSDA %FILTERSCRIPT% %TMP1% %2 %3 %4 %5 %6 %7 %8 %9 %=>:u8 %TMP3% [is the filter command]
echo %emoji_goat%      %PERL% -CSDA %FILTERSCRIPT% %TMP1% %2 %3 %4 %5 %6 %7 %8 %9   >:u8 %TMP3%
    %COLOR_UNIMPORTANT% %+      %PERL% -CSDA %FILTERSCRIPT% %TMP1% %2 %3 %4 %5 %6 %7 %8 %9   >:u8 %TMP3%
    call errorlevel
    if "%NO_PRESCRUB%" eq "1"   *copy                       %TMP1%                                %TMP3%
    %COLOR_UMIMPORTANT% %+      *copy                       %TMP3%                                %TMP1%
goto :Edit
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::







:::: EDIT THE UNIQUE FILENAMES IF WE ARE SUPPOSED TO:
:Edit
    if "%DEBUG"  ==  "1" goto :Debug1_YES
                         goto :Debug1_NO
        :Debug1_YES
            if "%DEBUG%"    eq "1" (%COLOR_DEBUG% %+ echo * about to %EDITOR %TMP1 %+ %COLOR_NORMAL%)
            if "%SWEEPING%" eq "1" goto :SkipDebug1Pause
                pause
            :SkipDebug1Pause
        :Debug1_NO

    pushd
    if "%SKIPEDIT%" eq "1" goto :SkipEdit
    if "%SWEEPING%" eq "1" goto :SkipEdit
        call wrapper %EDITOR "%TMP1"
        if "%VALIDATE_LINES%" ne "1" goto :SkipValidationOfLines
                :::: TODO PUT VALIDATION OF LINES CODE HERE
        :SkipValidationOfLines
    :SkipEdit
    popd

    ::::: in case you're wondering about that pushd popd shit, I found out the
    ::::: hard way that in the event of the user somehow changing the current
    ::::: working dir WHILE in the call of %EDITOR (for example, a text editor
    ::::: with a shell function where the user changes the directory while
    ::::: shelled out), that this thing fails.  So let's use 4DOS's pushd and
    ::::: popd to preserve the directory so that we make goddamn sure we are in
    ::::: the right motherfucking directory!!





::::: PROVIDE WARNING, IF WE ARE SUPPOSED TO:
:Warn
    if "%1"=="mv"     goto :allfiles_mv_msg
    if "%1"=="master" goto :allfiles_master_msg
    if %SKIPWARN%==1  goto :afterMessage
            :allfiles_default_msg
                %COLOR_WARNING%
                echo *** WARNING ***        About to send the contents of the file
                echo *** WARNING ***        (which you just edited) to the command line!
                echo *** WARNING ***        Hit Ctrl-Break to NOT do this.
                echo *** WARNING ***        CWP=%_CWP
                %COLOR_NORMAL%
            goto :afterMessage

                :allfiles_master_msg
                    %COLOR_WARNING%
                    echo *** WARNING ***        About to RENAME THE WHOLE DIRECTORY according to
                    echo *** WARNING ***        length limitations in the number of characters in
                    echo *** WARNING ***        a filename.  This should help with burning.
                    %COLOR_NORMAL%
                goto :afterMessage

                :allfiles_mv_msg
                    %COLOR_WARNING%
                    echo *** WARNING ***        About to RENAME THE WHOLE DIRECTORY according to
                    echo *** WARNING ***        the file you just edited.  If you deleted or
                    echo *** WARNING ***        swapped any lines, HIT CTRL-BREAK NOW.  If you
                    echo *** WARNING ***        continue and this hoses your dir, you must look in 
                    echo *** WARNING ***        c:\recycled (do not run allfiles again until you do)
                    echo *** WARNING ***        for 'latest-allfiles-(somenumber).bat', and reverse
                    echo *** WARNING ***        engineer the bat file using text editor macros
                    echo *** WARNING ***        to get your old filenames back.  BE CAREFUL!!!
                    echo.
                    %COLOR_IMPORTANT%
                    echo Current folder is:
                    echo    %_CWP
                    %COLOR_NORMAL%
                goto :afterMessage
    :afterMessage

::::: EXTRA WARNING IF WE ARE SWEEPING:
    echo.
    if "%SKIPWARN%" eq "1" goto :skipthispausetoo234234
    if "%SWEEPING%" eq "1" goto :skipthispausetoo234234
        pause
        if "%DEBUG%" eq "1" (%COLOR_DEBUG% %+ echo * SWEEPING IS %SWEEPING %+ %COLOR_NORMAL%)
            %COLOR_ALARM%   %+ echo. %+ echos Are you SURE??     (3) %+ %COLOR_NORMAL% %+ echo. %+ echo. %+ pause
            %COLOR_PROMPT%  %+ echo. %+ echos Are you SURE??     (2) %+ %COLOR_NORMAL% %+ echo. %+ echo. %+ pause
            %COLOR_WARNING% %+ echo. %+ echos Are you SURE??     (1) %+ %COLOR_NORMAL% %+ echo. %+ echo. %+ pause
    :skipthispausetoo234234









::::: CREATE THE BAT FILE TO DO OUR WILL:
:CreateBatFile

    ::::: COPY UNIQUE FILENAME TO OUR GENERIC .\BAT NAME
        %COLOR_LOGGING%
        if exist %TMP5% del /q %TMP5%
        echo @Echo OFF                                                                             >:u8 %TMP5%
        echo :: generated on %_DATETIME by %0.bat to create file %TMP5%                           >>:u8 %TMP5%

	::::: GET IN THE RIGHT DIR (yes, 3 different ways to make sure)
	::::: for example, "h:\test" would not work but h:\test would,
	::::: but "h:\two words" would work and h:\two words woudn't.
        echo *cd "%_cwd"                                                                          >>:u8 %TMP5%
        rem      "%_cwd"\                                                                         >>:u8 %TMP5%
        rem       %_cwd\                                                                          >>:u8 %TMP5%

        if "%NOCLS%"    eq "1" (goto :nocls1)
        if "%DEBUG%"    eq "1" (goto :nocls1)
        if "%SWEEPING%" eq "1" (goto :nocls1)
    	    echo cls                                                                              >>:u8 %TMP5%
        :nocls1
        if "%DEBUG%" eq "1" echo call print-if-debug Current directory is %%_cwd                  >>:u8 %TMP5%
	    if "%DEBUG%" eq "1" echo pause                                                            >>:u8 %TMP5%


    if "%1"=="mv" goto :allfiles_mv_creation_meat
        :NormalCreationMeat
            call less_important "Using normal creation meat..."
            type %TMP1                                                                            >>:u8 %TMP5
            goto :FinishCreatingBatfile

        :allfiles_mv_creation_meat
            call less_important "Using allfiles_mv creation meat..."
            :allfile2.pl is simply one that checks %TMP1 vs %TMP2 and creates rename commands to rename the names in %TMP1% to %TMP2%. That is all.
            set DIFFERENCE_SCRIPT=%BAT%\allfile2.pl
            if "%DEBUG" == "1" echo * About to: %PERL% %DIFFERENCE_SCRIPT% %TMP1% %TMP2%          >>:u8 %TMP5%
            ::20220207  MOVED A CPL LINES BELOW %PERL% %DIFFERENCE_SCRIPT% %TMP1% %TMP2%          >>:u8 %TMP5%
			::20221109  NO LET'S MOVE IT BACK!
			%PERL% %DIFFERENCE_SCRIPT% %TMP1% %TMP2%                                              >>:u8 %TMP5%
    goto :FinishCreatingBatfile


    :FinishCreatingBatfile
        echo :   /* Begin User Input */                                                           >>:u8 %TMP5%
        :: 20220207 MOVED HERE FROM CPL LINES ABOVE BE CAREFUL THIS COULD BREAK LESS-USED ONES:
		:: 20221109 THIS SEEMS TO BE CAUSING DOUBLE-ENCODING FOR ALLFILES-WAV2MP3 ACTIONS LET'S MOVE IT BACK AND HOPE
        ::          (but it's commented out? wtf? -20221216)
        :%PERL %FILTERSCRIPT %TMP1 %TMP2                                                          >>:u8 %TMP5%

        :: allfiles postprocessing scripts go here
        echo.                                                                                     >>:u8 %TMP5%
        echo.                                                                                     >>:u8 %TMP5%
        :TODO this next part should really only be added if we are doing allfiles mv type stuff:
        echo :::: POST-PROCESSING                                                                 >>:u8 %TMP5%
        echo if exist %%FILEMASK_AUDIO%% (call remove-leading-0s-from-music-filenames)            >>:u8 %TMP5%
        echo.                                                                                     >>:u8 %TMP5%
        echo.                                                                                     >>:u8 %TMP5%
        echo.                                                                                     >>:u8 %TMP5%
        echo.                                                                                     >>:u8 %TMP5%
        if "%DEBUG%"    eq "1"                                 echo pause                         >>:u8 %TMP5%
       :if "%SWEEPING%" ne "1" .and. "%NOCLS%"          ne "1" echo cls %%+ set FOO=1             >>:u8 %TMP5%
                                                               echo if isfile \*.tmp (*del \*.tmp)>>:u8 %TMP5%        %+ REM        :: new 2015 temp file superior naming structure leaves trash that needs to be cleaned up:
        if "%SWEEPING%" ne "1" .and. "%NOEXITINTERNAL%" ne "1" echo if "%%1" != "noexit" exit     >>:u8 %TMP5%
        if "%SWEEPING%" ne "1" .and. "%NOCLS%"          ne "1" echo cls %%+ set FOO=2             >>:u8 %TMP5%



::::: EXECUTE THE BAT FILE WE HAVE CREATED:
:Execute
    %COLOR_SUCCESS% %+ echos ===================================== RUNNING: ====================================== 
    %COLOR_NORMAL%  %+ echo.


    :NEWWAY
        set MINIMIZE=1
        if "%STARTWITHCALL%" eq "1" (set NOEXIT=1)
        if "%STARTWITHCALL%" eq "1" goto :Start_With_Call
        if "%SWEEPING%"      eq "1" goto :Start_With_Call
                                    goto :Start_With_Start
            :Start_With_Call
                set REDOCOMMAND=call              c:\bat\allfiles-helper.bat "%_cwd" "%TMP5"
                   %REDOCOMMAND%
            goto :Sweeping_RunIt_DONE

            :Start_With_Start
                set REDOCOMMAND=call helper-start c:\bat\allfiles-helper.bat "%_cwd" "%TMP5"
                   %REDOCOMMAND%
            :Sweeping_RunIt_DONE
    :DONESTARTING


    ::::: save temp files for debugging/auditing
        color cyan on black 
        %COLOR_LESS_IMPORTANT%
                            *copy %TMP5 %LATESTALLFILES1%
        %COLOR_UNIMPORTANT%
                            *copy %TMP5 %LATESTALLFILES2%
        echo %@RANDFG[]
                            *copy %TMP1% c:\recycled\latest-tmp1
        echo %@RANDFG[]
                            *copy %TMP2% c:\recycled\latest-tmp2
        echo %@RANDFG[]
                            *copy %TMP3% c:\recycled\latest-tmp3

    :done
        REM MOVED TO ALLFILES-HELPER--TIMING ISSUES: *del /q %TMP5 %TMP1 >nul
        %COLOR_SUCCESS%
        echo ===================================== **DONE** ======================================


::::: CLEAN-UP:
:CleanUp
        unset /q ADDTIME
        unset /q DEBUG
        unset /q SKIPEDIT
        unset /q SKIPWARN
        unset /q STARTWITHCALL
        unset /q NOEXITINTERNAL
        unset /q NOCLS
    rem unset /q FILTERSCRIPT
    rem unset /q TMPDIRCMD
    rem	unset /q TMP1
    rem	unset /q TMP2
    rem	unset /q TMP3
    rem	unset /q TMP4
    rem	unset /q TMP5
        if "%SWEEPING%" eq "1" dir
        :unset /q LATESTALLFILES1
        :unset /q LATESTALLFILES2
        window restore

:END
%COLOR_NORMAL%

