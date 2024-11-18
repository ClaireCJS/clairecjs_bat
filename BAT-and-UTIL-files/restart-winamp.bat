@Echo OFF




::::: FOR GOOGLE HOME VOICE-ACTIVATED INVOCATION THAT SHOULD BE INVISIBLE:
    if "%WINDOW_MINIMIZE%" eq  "1" (window min )
    if  "WINDOW_MINIMIZE"  eq "%1" (window min )
    if "%WINDOW_HIDE%"     eq  "1" (window hide)
    if  "WINDOW_HIDE"      eq "%1" (window hide)

::::: CONFIGURATION:
    :was 2 for many years, setting to 1 for Thailog:
    SET SLEEP_TIME_AFTER_RESTARTING_WINAMP_BEFORE_CHECKING_THAT_IT_RESTARTED=1

    call set-winamp-constants
        :SET REGEX_TASKLIST_WINAMP=Winamp
        :SET REGEX_KILLPROC_WINAMP=winamp*
        :SET REGEX_TASKLIST_LASTFM=Last.fm
        :SET REGEX_KILLPROC_LASTFM=last.fm*
        :SET REGEX_TASKLIST_LYRICS=MiniLyrics
        :SET REGEX_KILLPROC_LYRICS=MiniLyrics


::::: CLOSE WINAMP:
    echo.
    echo.
        REM call save-window-positions 
            call save-window-positions WinampLast


    echo.
    echo.
    call important "Closing Winamp %italics_on%gracefully%italics_off%"
        call change-command-separator-character-to-normal
        call winamp-close-gracefully
        call wait 3







echo NOTE: 202102: Okay this is where things get weird and disruptive, might want to Ctrl-Break outta this...
echo               We might want to change this script to have multiple modes.
:pause


    
    
    
    
    call stop-minilyrics    


    echo.
    echo.
    set SLEEP=1
    rem  important "Waiting %SLEEP% seconds"
    call wait              %SLEEP% 

    echo.
    echo.
    call important "%ANSI_COLOR_REMOVAL%Killing %ANSI_COLOR_IMPORTANT%%italics_on%WinAmp%italics_off% & %italics_on%Last.fm%italics_off% again"
        call killIfRunning %REGEX_TASKLIST_WINAMP% %REGEX_KILLPROC_WINAMP%
        call killIfRunning %REGEX_TASKLIST_LASTFM% %REGEX_KILLPROC_LASTFM%
        call killIfRunning %REGEX_TASKLIST_LYRICS% %REGEX_KILLPROC_LYRICS%

    echo.
    echo.
    call important "Verifying they are killed"
            :Verify
                call isRunning winamp
                if "%ISRUNNING%" eq "1" (goto :Running_YES)
                            goto :Running_NO
                    :Running_YES
                        call warning "Winamp %italics_on%really%italics_off% should be dead now. Let's try again in a second."
                            beep 50 1
                            call sleep 1
                            goto :Verify
                    :Running_NO



::::: COPY OUR MATRIXMIXER CONFIG:
    pushd
        REM goat not sure if this will continue to work after changing winamp back to 5.666 but it was an install-over-5.92 install so maybe it will
        call appdata 
        cd winamp

        echo ry | cp /z out_mixer.ini.official out_mixer.ini    
    popd





::::: REOPEN WINAMP (et al):
    echo.
    echo.
    call important "Starting Winamp/etc"
        call nocar
        call WinAmp.bat
        call wait %SLEEP_TIME_AFTER_RESTARTING_WINAMP_BEFORE_CHECKING_THAT_IT_RESTARTED%
        call isRunning winamp

    echo.
    echo.
    call important "Starting Lastfm"
        call                 lastfm-start


    
    REM echo.
    REM echo.
    REM call important "Restoring/Fixing window positions"
    REM     :: a broad-sweep window position fix for ALL windows 
    REM         call warning "NOT restoring window positions for the time being"
    REM         :call restore-window-positions WinampLast
    REM         call fix-minilyrics-window-size-and-position
    REM    
    REM     :: a narrow sweep to fix window position AND sizes for MiniLyrics, EvilLyrics, Last.FM (as of 2020/06), etc:
    REM         call warning "%underline_on%%italics_on%NOT%italics_off%%underline_off% CURRENTLY DOING THIS: call fix-music-window-sizes-and-positions"





:END
    echo Not randomizing or next'ing
    REM call randomize
    REM call next
