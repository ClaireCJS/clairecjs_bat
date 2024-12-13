@Echo Off
@on break cancel

REM TODO if a srt exists without lyrics, consider converting that instead of downloading lyrics

:USAGE: get-lyrics

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

call validate-in-path get-lyrics-for-currently-playing-song check-for-missing-lyrics get-lyrics-for-playlist get-lyrics-for-song
set  validated_getlyrics=1

iff "%1" == "nowplaying" .or. "%1" == "now" .or. "%1" == "np" .or. "%1" == "winamp" .or. "%1" == "this" then
        call get-lyrics-for-currently-playing-song %*
elseiff "%1" == "here"  then
        rem  process current folder:
        call check-for-missing-lyrics get
elseiff not exist %1 then
        call fatal_error "get-lyrics can’t do anything with “%1” because it doesn’t exist!"
elseiff exist %1 then
        set ext=%@ext[%1]
        rem echo ext is %ext
        iff "m3u" eq "%ext%" then
                call get-lyrics-for-playlist %*
        else
                call get-lyrics-for-song %*        
        endiff
else 
        call alarm "%0 reached point of confusion"
        pause
endiff


:END

