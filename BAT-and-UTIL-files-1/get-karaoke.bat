@loadbtm on
@Echo Off
@on break cancel

:USAGE: get-karaoke {songfile}

rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

rem Debug configuration:
        set CALL=echo call           %+ rem Use this for a dry run
        set CALL=call                %+ rem Use this for normal production

rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

rem CONFIGURATION:
        set CREATE_MISSING_KRAOKES_SCRIPT_NAME=create-the-missing-karaokes-here-temp.bat %+ rem This must be synchronized with values elsewhere, so don’t change!

rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

rem Validate usage:
        iff "%1" == "" then
                %color_advice%
                        echo.
                        echo %STAR% USAGE: %ansi_color_pink%get-karaoke %italics_on%song.flac%italics_off%    %ansi_color_advice%—— attempts to align karaoke for one audio file
                        echo %STAR% USAGE: %ansi_color_pink%get-karaoke %italics_on%playlist.m3u%italics_off% %ansi_color_advice%—— attempts to align karaoke for all audio files in a playlist
                        echo %STAR% USAGE: %ansi_color_pink%get-karaoke here         %ansi_color_advice%—— attempts to align karaoke for all audio files in the current folder
                        echo %STAR% USAGE: %ansi_color_pink%get-karaoke this         %ansi_color_advice%—— attempts to align karaoke for the audio file currently playing in WinAmp                        
                        echo                                      %italics_on%nowplaying, np, now, %italics_off%and%italics_on% winamp%italics_off% —— should also work
                        echo.
                        echo. %STAR% ENVIRONMENT VARIABLE PARAMETERS:
                        echo       %ansi_color_pink%set OVERRIDE_FILE_ARTIST_TO_USE=Misfits      %ansi_color_advice%//override artist name
                        echo           %@repeat[%up_arrow%,27] %faint_on%especially useful if you are using %italics_on%predownload-all-lyrics-in-subfolders.bat%italics_off% to predownload lyrics for a bunch of tribute/cover albums of a particular band. For example, I have 10 tribute albums for The Misfits that I wanted to pre-download lyrics for. Although %italics_on%get-lyrics%italics_off% falls back on the %italics_on%original artist%italics_off% tag, some of my files were missing that tag.  So I set this value to override the artist to %italics_on%“Misfits”%italics_off% name from the start.%faint_off%
                        echo.
                        echo       %ansi_color_pink%set CONSIDER_ALL_LYRICS_APPROVED=1           %ansi_color_advice%//autom-approves lyrics when asked %faint_on%[reduces prompt wait from %LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME% to %LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME_AUTO% seconds]%faint_off%
                        echo.
                        echo       %ansi_color_pink%set LYRIC_KARAOKE_ALIGNMENT_THOROUGH_MODE=1  %ansi_color_advice%//no automatic timeouts; always waits for user input
                        echo.                %color_normal%
                goto /i END
        endiff
        echos %ANSI_COLOR_NORMAL%``

rem Validate environment once:
        iff "1" != "%validated_getlyrics%" then
                rem    validate-in-path create-srt-file-for-currently-playing-song.bat check-for-missing-karaoke-here create-srt-from-playlist create-srt-from-file.bat
                %CALL% validate-in-path create-srt-file-for-currently-playing-song.bat check-for-missing-karaoke      create-srt-from-playlist create-srt-from-file.bat
                set  validated_getlyrics=1
        endiff


rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

rem Process currently-playing song:
        iff "%1" == "nowplaying" .or. "%1" == "now" .or. "%1" == "np" .or. "%1" == "winamp" .or. "%1" == "this" then
                setdos /x0
                %CALL% create-srt-file-for-currently-playing-song.bat get %2$
                goto /i END
        endiff         

rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

rem Process current folder:
        iff "%1" == "here"  then
                rem Gobble up “here” option:
                        shift
                        setdos /x0
                        rem echo %%1=“%1” %%2=“%2” %%3=“%3” %%4=“%4” ...... %%9$=“%9$”

                rem Remove older generated script if it exists:
                        if exist %CREATE_MISSING_KRAOKES_SCRIPT_NAME% (echos %ansi_color_removal%%axe%%axe% `` %+ *del /z /a: /Ns %CREATE_MISSING_KRAOKES_SCRIPT_NAME%)

                rem Determine mode:
                        unset /q get
                        if "%1" == "get"            (set get=get            %+ shift)
                        if "%1" == "PromptAnalysis" (set get=PromptAnalysis %+ shift)
                        %CALL% check-for-missing-karaoke.bat %get% %2 %3 %4 %5 %6 %7 %8 %9$

                rem Run our script, if it now exists / was generated:
                        if exist %CREATE_MISSING_KRAOKES_SCRIPT_NAME% %CALL% %CREATE_MISSING_KRAOKES_SCRIPT_NAME%

                goto /i END
        endiff


rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

rem DEBUG: *setdos /x-4 %+ echo param1 is %1 %+ pause

rem At this point, we’re NOT operating on the currently-playing song or the current folder
rem                (because we already dealt with those situations above!)
rem So now, at this point:
rem Error out if the parameter is given that doesn’t exist:
        *setdos /x-4
        iff not exist %1 then
                %CALL% fatal_error "get-lyrics can’t do anything with “%1” because it doesn’t exist!"
                setdos /x0
                goto /i END
        endiff
        setdos /x0

rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

rem Process playlists / single audio files:
        *setdos /x-4
        iff exist %1 then
                setdos /x0
                set ext=%@ext[%1]
                                                                                                                        
                rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                rem Process either a playlist or an individual song:
                        iff "m3u" == "%ext%" then
                                rem echo 🍕🍕🍕
                                %CALL% create-srt-from-playlist  %1$       %+ rem Process individual playlist
                        else
                                %CALL% create-srt-from-file.bat  %1$       %+ rem Process individual audiofile
                        endiff       
                rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        else 
                setdos /x0
                %CALL% alarm "%0 reached point of confusion"
                pause
        endiff
        setdos /x0

rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

rem Clean up & finish:

:END
setdos /x0


