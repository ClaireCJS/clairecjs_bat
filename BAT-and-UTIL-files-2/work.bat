@Echo Off
@loadbtm on
@on break cancel
@call bat-init
@.
@cls

:═══════════════════════════════════════════════════════════════════════
:║                                                                     ║
:║  This was developed to work on our karaoke/lyric workload,          ║
:║  but it’s actually a frame work to manage doing ANY kind of work!   ║
:║                                                                     ║
:═══════════════════════════════════════════════════════════════════════


rem Work configuration: lyrics & karaoke:
        set default_playlist_to_work=crtl.m3u
        set default_playlist_to_work=2010s party.m3u
        set default_number_of_lyrics_to_work=69
        set default_number_of_karaoke_to_work=1500












rem Validate environment (once):
        iff 1 ne %validated_work% then
                call validate-in-path askyn
                set  validated_work=1
        endiff

iff     "%1" == "/?" then
        goto :usage
elseiff "%1" == "" then
        echo.
        cls
        call AskYn "Work how? K=Karaoke, L=Lyrics" no 9999 big LK L:Lyrics!,K:Karaoke!
endiff


:start
echos %italics_on%%faint_on%
timer /4 on
echos %italics_off%%faint_off%



set CURRENTLY_WORKING_RIGHT_NOW=1
iff "L" == "%ANSWER%" .or. "K" == "%ANSWER%" .or. "%1" == "lyrics" .or. "%1" == "karaoke" then
        iff "1" !=  "%validated_work_lyricskaraoke%" then
                call validate-in-path get-lyrics get-karaoke mp3l error print-message
                set  validated_work_lyricskaraoke=1
        endiff
        call mp3l
        unset /q worker workload
        set default_playlist_to_work="%@UNQUOTE["%default_playlist_to_work%"]"
        iff "K" == "%ANSWER%" .or. "%1" == "karaoke" then
                call convert-playlist-to-only-songs-that-do-not-have-karaoke.bat %default_playlist_to_work%
                set worker=get-karaoke
                set workload=%default_number_of_karaoke_to_work%
                set PLAYLIST_TO_WORK="%@NAME["%default_playlist_to_work%"]-without lrc or srt.%@EXT["%default_playlist_to_work%"]"
        elseiff  "L" == "%ANSWER%" .or. "%1" == "lyrics"  then
                call convert-playlist-to-only-songs-that-do-not-have-lyrics.bat  %default_playlist_to_work%
                set worker=get-lyrics
                set workload=%default_number_of_lyrics_to_work%
                set PLAYLIST_TO_WORK="%@NAME["%default_playlist_to_work%"]-without txt.%@EXT["%default_playlist_to_work%"]"
        else
                rem (copypaste of the previous section)
                call convert-playlist-to-only-songs-that-do-not-have-lyrics.bat  %default_playlist_to_work%
                set worker=get-lyrics
                set workload=%default_number_of_lyrics_to_work%
                set PLAYLIST_TO_WORK="%@NAME["%default_playlist_to_work%"]-without txt.%@EXT["%default_playlist_to_work%"]"
        endiff
        if "%1" !=  "" set workload=%1
        if "%2" !=  "" set workload=%2
        if "%worker%" !=  "" call %worker% %PLAYLIST_TO_WORK% %@IF["%workload%" != "",%workload%,%@IF["%2" != "",%2,10]] %3$
endiff
set CURRENTLY_WORKING_RIGHT_NOW=0



goto :end_of_subroutines

        :usage
                echo.
                %color_advice%
                                echo USAGE:  work lyrics
                                echo USAGE:  work karaoke
                %color_normal%
        goto :END

:end_of_subroutines

:end
echo.
echos %italics_on%%faint_on%
timer /4 off
echos %italics_off%%faint_off%

