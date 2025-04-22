@loadbtm on
@Echo OFF
@on break cancel
cls



:USAGE: get-lyrics {songfile}

rem Validate environment once:
        iff "1" != "%validated_getlyrics2%" then
                rem call validate-in-path get-lyrics-for-currently-playing-song check-for-missing-lyrics get-lyrics-for-playlist get-lyrics-for-song fatal_error alarm
                call validate-in-path get-lyrics-for-currently-playing-song 
                call validate-in-path check-for-missing-lyrics 
                call validate-in-path get-lyrics-for-playlist 
                call validate-in-path get-lyrics-for-song 
                call validate-in-path fatal_error alarm
                call validate-environment-variables ansi_color_pink color_advice ansi_color_advice color_normal faint_on faint_off up_arrow italics_on italics_off star
                set  validated_getlyrics2=1
        endiff

rem Validate usage:
        iff "%1" == "" then
                %color_advice%
                        echo.
                        echo %STAR% USAGE: %ansi_color_pink%get-lyrics %italics_on%song.flac%italics_off%    %ansi_color_advice%—— attempts to align lyrics for one audio file
                        echo %STAR% USAGE: %ansi_color_pink%get-lyrics %italics_on%playlist.m3u%italics_off% %ansi_color_advice%—— attempts to align lyrics for all audio files in a playlist
                        echo %STAR% USAGE: %ansi_color_pink%get-lyrics here         %ansi_color_advice%—— attempts to align lyrics for all audio files in the current folder
                        echo %STAR% USAGE: %ansi_color_pink%get-lyrics this         %ansi_color_advice%—— attempts to align lyrics for the audio file currently playing in WinAmp                        
                        echo                                      %italics_on%nowplaying, np, now, %italics_off%and%italics_on% winamp%italics_off% —— should also work
                        echo.
                        echo. %STAR% ENVIRONMENT VARIABLE PARAMETERS:
                        echo       %ansi_color_pink%set OVERRIDE_FILE_ARTIST_TO_USE=Misfits      %ansi_color_advice%//override artist name
                        echo           %@repeat[%up_arrow%,27] %faint_on%especially useful if you are using %italics_on%predownload-all-lyrics-in-subfolders.bat%italics_off% to predownload lyrics for a bunch of tribute/cover albums of a particular band. For example, I have 10 tribute albums for The Misfits that I wanted to pre-download lyrics for. Although %italics_on%get-lyrics%italics_off% falls back on the %italics_on%original artist%italics_off% tag, some of my files were missing that tag.  So I set this value to override the artist to %italics_on%“Misfits”%italics_off% name from the start.%faint_off%
                        echo.
                        echo       %ansi_color_pink%set CONSIDER_ALL_LYRICS_APPROVED=1           %ansi_color_advice%//autom-approves lyrics when asked %faint_on%[reduces prompt wait from %LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME% to %LYRIC_ACCEPTABILITY_REVIEW_WAIT_TIME_AUTO% seconds]%faint_off%
                        echo.
                        echo       %ansi_color_pink%set LYRIC_KARAOKE_ALIGNMENT_THOROUGH_MODE=1  %ansi_color_advice%//no automatic timeouts; always waits for user input
                        echo.
                %color_normal%
                goto :END
        endiff

        setdos /x0





rem Process currently-playing song:
        iff "%1" == "nowplaying" .or. "%1" == "now" .or. "%1" == "np" .or. "%1" == "winamp" .or. "%1" == "this" then
                setdos /x0
                call get-lyrics-for-currently-playing-song %2$
                goto next_step
        endiff         

rem Process current folder:
        iff "%1" == "here"  then
                setdos /x0
                unset /q FILE_* 

                iff "%2" == "abc" then
                        call get-lyrics-here-in-alphabetical-order.bat %3$
                        goto end
                else
                        call check-for-missing-lyrics get %2$
                        goto /i next_step
                endiff
        endiff
        iff "%2" == "abc" goto end

rem DEBUG: *setdos /x-4 %+ echo param1 is %1 %+ pause

rem Error out if a parameter is given that doesn’t exist:
        *setdos /x-4
        iff not exist %1 then
                call fatal_error "get-lyrics can’t do anything with “%1” because it doesn’t exist!"
                setdos /x0
                goto /i :END
        endiff
        setdos /x0

rem Process playlists / audio files:
        *setdos /x-4
        iff exist %1 then
                setdos /x0
                set ext=%@ext[%1]
                rem echo ext is %ext


                rem Process either a playlist or an individual song:
                        if "m3u" == "%ext%" call get-lyrics-for-playlist %1$       %+ rem Process individual playlist
                        if "m3u" != "%ext%" call get-lyrics-for-file.btm %1$       %+ rem Process individual audiofile
        else 
                setdos /x0
                call alarm "get-lyrics reached point of confusion"
                pause
        endiff
        setdos /x0



rem Clean up & finish:
        :next_step
        :END
                setdos /x0

