@loadbtm on
@Echo Off
@on break cancel

:USAGE: get-karaoke {songfile}

rem Debug configuration:
        set CALL=echo call           %+ rem Use this for a dry run
        set CALL=call                %+ rem Use this for normal production

rem Validate usage:
        iff "%1" == "" then
                %color_advice%
                        echo.
                        echo USAGE: get-karaoke song.flac    —— attempts to get approved lyrics for one song
                        echo USAGE: get-karaoke here         —— attempts to get approved lyrics for all files in current folder
                        echo USAGE: get-karaoke playlist.m3u —— attempts to get approved lyrics for all files in a playlist
                        echo USAGE: get-karaoke now_playing  —— get lyrics for the song currently playing in WinAmp                        
                        echo                                   nowplaying, np, now, winamp, this —— are other alises for this mode
                        echo.
                        echo.
                        echo.
                %color_normal%
                goto :END
        endiff

rem Validate environment once:
        iff "1" != "%validated_getlyrics%" then
                %CALL% validate-in-path create-srt-file-for-currently-playing-song.bat check-for-missing-karaoke-here create-srt-from-playlist create-srt-from-file.bat
                set  validated_getlyrics=1
        endiff



rem Process currently-playing song:
        iff "%1" == "nowplaying" .or. "%1" == "now" .or. "%1" == "np" .or. "%1" == "winamp" .or. "%1" == "this" then
                setdos /x0
                %CALL% create-srt-file-for-currently-playing-song.bat get %2$
                goto :next_step
        endiff         

rem Process current folder:
        iff "%1" == "here"  then
                shift
                setdos /x0
                rem echo %%1=“%1” %%2=“%2” %%3=“%3” %%4=“%4” ...... %%9$=“%9$”
                unset /q get
                if "%1" == "get" (set get=get %+ shift)
                %CALL% check-for-missing-karaoke.bat %get% %2 %3 %4 %5 %6 %7 %8 %9$
                goto :next_step
        endiff


rem DEBUG: setdos /x-4 %+ echo param1 is %1 %+ pause

rem Error out if a parameter is given that doesn’t exist:
        setdos /x-4
        iff not exist %1 then
                %CALL% fatal_error "get-lyrics can’t do anything with “%1” because it doesn’t exist!"
                setdos /x0
                goto :END
        endiff
        setdos /x0

rem Process playlists / audio files:
        setdos /x-4
        iff exist %1 then
                setdos /x0
                set ext=%@ext[%1]
                rem echo ext is %ext


                rem Process either a playlist or an individual song:
                        iff "m3u" == "%ext%" then
                                rem echo 🍕🍕🍕
                                %CALL% create-srt-from-playlist  %1$       %+ rem Process individual playlist
                        else
                                %CALL% create-srt-from-file.bat  %1$       %+ rem Process individual audiofile
                        endiff       
        else 
                setdos /x0
                %CALL% alarm "%0 reached point of confusion"
                pause
        endiff
        setdos /x0



rem Clean up & finish:
        :next_step
                setdos /x0
        :END
                setdos /x0

