@loadbtm on
@Echo OFF
@on break cancel

:USAGE: get-lyrics {songfile}

rem Validate usage:
        iff "%1" == "" then
                %color_advice%
                        echo.
                        echo USAGE: get-lyrics song.flac    —— attempts to get approved lyrics for one song
                        echo USAGE: get-lyrics here         —— attempts to get approved lyrics for all files in current folder
                        echo USAGE: get-lyrics playlist.m3u —— attempts to get approved lyrics for all files in a playlist
                        echo USAGE: get-lyrics now_playing  —— get lyrics for the song currently playing in WinAmp                        
                        echo                                   nowplaying, np, now, winamp, this —— are other alises for this mode
                        echo.
                        echo.
                        echo.
                %color_normal%
                goto :END
        endiff

rem Validate environment once:
        iff 1 ne %validated_getlyrics% then
                call validate-in-path get-lyrics-for-currently-playing-song check-for-missing-lyrics get-lyrics-for-playlist get-lyrics-for-song
                set  validated_getlyrics=1
        endiff


setdos /x0

rem Process currently-playing song:
        iff "%1" == "nowplaying" .or. "%1" == "now" .or. "%1" == "np" .or. "%1" == "winamp" .or. "%1" == "this" then
                setdos /x0
                call get-lyrics-for-currently-playing-song %2$
                goto :next_step
        endiff         

rem Process current folder:
        iff "%1" == "here"  then
                setdos /x0
                call check-for-missing-lyrics get %2$
                goto :next_step
        endiff


rem DEBUG: setdos /x-4 %+ echo param1 is %1 %+ pause

rem Error out if a parameter is given that doesn’t exist:
        setdos /x-4
        iff not exist %1 then
                call fatal_error "get-lyrics can’t do anything with “%1” because it doesn’t exist!"
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
                                call get-lyrics-for-playlist %1$       %+ rem Process individual playlist
                        else
                                call get-lyrics-for-song     %1$       %+ rem Process individual audiofile
                        endiff       
        else 
                setdos /x0
                call alarm "%0 reached point of confusion"
                pause
        endiff
        setdos /x0



rem Clean up & finish:
        :next_step
                setdos /x0
        :END
                setdos /x0
