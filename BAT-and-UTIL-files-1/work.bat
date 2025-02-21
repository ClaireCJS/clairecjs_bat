@Echo Off
@loadbtm on
@on break cancel
@call bat-init
@.
@cls

:══════════════════════════════════════════════════════════════════════
:║                                                                    ║
:║  This was developed to work on our karaoke/lyric workload,         ║
:║  but it’s actually a framework to manage doing ANY kind of work!   ║
:║                                                                    ║
:══════════════════════════════════════════════════════════════════════


rem Work configuration: lyrics & karaoke:
        set default_playlist_to_work=2010s party.m3u
        set default_playlist_to_work=crtl.m3u
        set default_playlist_to_work=changer.m3u
        set default_number_of_lyrics_to_work=69
        set default_number_of_karaoke_to_work=1





rem Usage:
        if "%1" == "/?"     goto :usage
        if "%1" == "/h"     goto :usage
        if "%1" == "-?"     goto :usage
        if "%1" == "-h"     goto :usage
        if "%1" == "--help" goto :usage


rem Validate environment (once):
        iff 1 ne %validated_work% then
                call validate-in-path askyn
                set  validated_work=1
        endiff



rem Ask what kind of work we are doing, if it is not specified already:
        iff "%1" == "" then
                echo.
                cls
                call AskYn "Work how? K=Karaoke, L=Lyrics" no 9999 big LK L:Lyrics!,K:Karaoke!
        endiff


rem Start working by starting a timer:
        :start
        echos %italics_on%%faint_on%
        timer /4 on
        echos %italics_off%%faint_off%
        set CURRENTLY_WORKING_RIGHT_NOW=1


rem Clean up env vars that may be left over from previous runs:
        unset /q worker workload


rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 🪓🪓🪓 START WORKING! 🪓🪓🪓 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 🪓🪓🪓 START WORKING! 🪓🪓🪓 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 🪓🪓🪓 START WORKING! 🪓🪓🪓 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

rem Handle option “K” / “L” which are for karaoke / lyric work related to the music-collection-AI-transcription project:
        :beginning_of_karaoke_or_lyric_work
        echo goaty α 2500.0.1 - beginning_of_karaoke_or_lyric_work - answer=“%%answer%”
        iff "L" == "%ANSWER%" .or. "K" == "%ANSWER%" .or. "%1" == "lyrics" .or. "%1" == "karaoke" then
                rem Run the script that takes us to our playlist location:
                        call mp3l

                rem Validate environment specific to this task:
                        iff "1" !=  "%validated_work_lyricskaraoke%" then
                                call validate-in-path get-lyrics get-karaoke mp3l error print-message AskYN convert-playlist-to-only-songs-that-do-not-have-karaoke.bat convert-playlist-to-only-songs-that-do-not-have-lyrics.bat
                                call validate-environment-variables default_playlist_to_work default_number_of_karaoke_to_work default_number_of_lyrics_to_work
                                set  validated_work_lyricskaraoke=1
                        endiff

                rem Make sure our playlist-to-work is properly quoted:
                        set default_playlist_to_work="%@UNQUOTE["%default_playlist_to_work%"]"


                rem 1) Set the      converter-to-use  — to set playlist converter     (lyrics vs karaoke)
                rem 2) Set the         script-to-run  — to run the proper work script (lyrics vs karaoke)
                rem 3) set the default-number-to-get  — to the default value to grab  (lyrics vs karaoke) from our config up top 
                rem 4) set the       playlist-to-work — to a name that makes sense    (lyrics vs karaoke)
                        iff "K" == "%ANSWER%" .or. "%1" == "karaoke" then
                                call convert-playlist-to-only-songs-that-do-not-have-karaoke.bat %default_playlist_to_work%
                                set worker=get-karaoke
                                set workload=%default_number_of_karaoke_to_work%
                                set PLAYLIST_TO_WORK="%@NAME["%default_playlist_to_work%"]-without lrc or srt.%@EXT["%default_playlist_to_work%"]"
                        iff  "L" == "%ANSWER%" .or. "%1" == "lyrics"  then
                                rem (copypaste of the previous section)
                                call convert-playlist-to-only-songs-that-do-not-have-lyrics.bat  %default_playlist_to_work%
                                set worker=get-lyrics
                                set workload=%default_number_of_lyrics_to_work%
                                set PLAYLIST_TO_WORK="%@NAME["%default_playlist_to_work%"]-without txt.%@EXT["%default_playlist_to_work%"]"
                        endiff

                rem Process command line override of # of files to process:
                        rem echo [PRE]  workload=“%workload%”,workload2=“%workload2%”  ... %%1=%1,%%2=%2,%%3=%3,%%4=%4
                        if "%1" == "karaoke" shift
                        if "%1" !=    ""     set workload=%1
                        if "%2" !=    ""     set workload2=%2
                        rem echo [POST] workload=“%workload%”,workload2=“%workload2%”

                rem DO THE ACTUAL WORK!! Call the pre-determined proper script + playlist + workload:
                        if "%worker%" !=  "" call %worker% %PLAYLIST_TO_WORK% %@IF["%workload%" != "",%workload%,%@IF["%workload2" != "",%workload2%,10]] %3$

                rem Ask if we want to keep on chompin’... 
                rem If we answer “Yes”, then we must simulate, that we answered “K” to the original 
                rem                             “What kind of work do you want to do?” question
                        call AskYN "Keep on chompin’" yes 30
                           echo if "%ANSWER%" == "Y" ( set goto_beginning_of_karaoke_or_lyric_work=1 %+ set ANSWER=K )
                                if "%ANSWER%" == "Y" ( set goto_beginning_of_karaoke_or_lyric_work=1 %+ set ANSWER=K )
        endiff
    echo [A] one more goddamn time!!! if "%ANSWER%" == "Y"    goto :beginning_of_karaoke_or_lyric_work
        if "Y" == "%ANSWER%"                                  goto :beginning_of_karaoke_or_lyric_work
    echo [B] one more goddamn time!!! if "1" == "%goto_beginning_of_karaoke_or_lyric_work%" goto :beginning_of_karaoke_or_lyric_work
        if "1" == "%goto_beginning_of_karaoke_or_lyric_work%" goto :beginning_of_karaoke_or_lyric_work


:━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
:━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
goto :end_of_subroutines

        :usage
                echo.
                %color_advice%
                                echo USAGE:  work lyrics
                                echo USAGE:  work karaoke
                %color_normal%
        goto :END

:end_of_subroutines
:━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
:━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

:end
        set CURRENTLY_WORKING_RIGHT_NOW=0
        echo.
        echos %italics_on%%faint_on%
                timer /4 off
        echos %italics_off%%faint_off%

