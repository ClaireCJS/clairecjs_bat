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


rem Work configuration: lyrics & karaoke: playlists:
        set default_playlist_to_work=2010s party.m3u
        set default_playlist_to_work=changer.m3u
        set default_playlist_to_work=crtl.m3u
        set default_playlist_to_work=changerrecent.m3u
        set default_playlist_to_work=best.m3u

rem Work configuration: lyrics & karaoke: workloads:
        set default_number_of_lyrics_to_work=69
        set default_number_of_karaoke_to_work=30
        set default_number_of_karaoke_to_work=10
        set default_number_of_karaoke_to_work=20
        set default_number_of_karaoke_to_work=30

rem Work configuration: lyrics & karaoke: options:
        set LYRIC_KARAOKE_ALIGNMENT_THOROUGH_MODE=1





rem Usage:
        if "%1" == "/?"     goto :usage
        if "%1" == "/h"     goto :usage
        if "%1" == "-?"     goto :usage
        if "%1" == "-h"     goto :usage
        if "%1" == "--help" goto :usage


rem Validate environment (once):
        iff "1" != "%validated_work%" then
                call validate-in-path askyn
                set  validated_work=1
        endiff



rem Ask what kind of work we are doing, if it is not specified already:
        iff "%1" == "" then
                echo.
                cls
                call AskYn "Work how? %ansi_color_bright_green%K%ansi_color_prompt%=Karaoke, %ansi_color_bright_green%L%ansi_color_prompt%=Lyrics, %ansi_color_bright_green%P%ansi_color_prompt%=Prompts" no 9999 big LKP L:Lyrics!,K:Karaoke!,P:Prompts!
                        set work_type_answer=%answer%
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
        rem echo goaty - work.bat - 6600.0.1 - beginning_of_karaoke_or_lyric_work - answer=“%work_type_answer%”
        iff "L" == "%WORK_TYPE_ANSWER%" .or. "K" == "%WORK_TYPE_ANSWER%" .or. "P" == "%WORK_TYPE_ANSWER%" .or. "%1" == "lyrics" .or. "%1" == "karaoke" .or. "%1" == "prompts" then

                rem Run the script that takes us to our playlist location - TODO: may need to change this to match yours:
                        call mp3l

                rem Validate environment specific to this task:
                        iff "1" != "%validated_work_lyricskaraoke%" then
                                echos %ansi_color_less_important%%star2% Validating work-related variables...
                                        call validate-in-path get-lyrics get-karaoke mp3l error print-message AskYN convert-playlist-to-only-songs-that-do-not-have-karaoke.bat convert-playlist-to-only-songs-that-do-not-have-lyrics.bat
                                        call validate-environment-variables default_playlist_to_work default_number_of_karaoke_to_work default_number_of_lyrics_to_work
                                echo done!%ansi_color_normal%
                                set  validated_work_lyricskaraoke=1
                        endiff

                rem Make sure our playlist-to-work is properly quoted:
                        set default_playlist_to_work="%@UNQUOTE["%default_playlist_to_work%"]"


                rem 1) Set the      converter-to-use  — to set playlist converter     (lyrics vs karaoke)
                rem 2) Set the         script-to-run  — to run the proper work script (lyrics vs karaoke)
                rem 3) set the default-number-to-get  — to the default value to grab  (lyrics vs karaoke) from our config up top 
                rem 4) set the       playlist-to-work — to a name that makes sense    (lyrics vs karaoke)
                        iff "K" == "%WORK_TYPE_ANSWER%" .or. "%1" == "karaoke" .or. "L" == "%WORK_TYPE_ANSWER%" .or. "%1" == "lyrics" .or. "P" == "%WORK_TYPE_ANSWER%" .or. "%1" == "prompts"  then
                                call less_important "Searching playlist “%@NAME["%default_playlist_to_work%"]”..."
                        endiff
                        echos %ansi_color_normal%

                        iff "K" == "%WORK_TYPE_ANSWER%" .or. "%1" == "karaoke"  then
                                set  WORK_TYPE_ANSWER=K
                                call convert-playlist-to-only-songs-that-do-not-have-karaoke.bat %default_playlist_to_work%
                                call sleep 4
                                set worker=get-karaoke
                                set workload=%default_number_of_karaoke_to_work%
                                set PLAYLIST_TO_WORK="%@NAME["%default_playlist_to_work%"]-without lrc or srt.%@EXT["%default_playlist_to_work%"]"
                        endiff
                        iff  "L" == "%WORK_TYPE_ANSWER%" .or. "%1" == "lyrics"  then
                                set  WORK_TYPE_ANSWER=L
                                call convert-playlist-to-only-songs-that-do-not-have-lyrics.bat  %default_playlist_to_work%
                                call sleep 4
                                set worker=get-lyrics
                                set workload=%default_number_of_lyrics_to_work%
                                set PLAYLIST_TO_WORK="%@NAME["%default_playlist_to_work%"]-without txt.%@EXT["%default_playlist_to_work%"]"
                        endiff
                        iff  "P" == "%WORK_TYPE_ANSWER%" .or. "%1" == "prompts"  then
                                set  WORK_TYPE_ANSWER=P
                                call convert-playlist-to-only-songs-that-do-not-have-karaoke-but-do-have-lyrics.bat  %default_playlist_to_work%
                                call sleep 4
                                set worker=get-karaoke-prompts-only
                                set workload=%default_number_of_lyrics_to_work%
                                set PLAYLIST_TO_WORK="%@NAME["%default_playlist_to_work%"]-with txt but no lrc or srt.%@EXT["%default_playlist_to_work%"]"
                        endiff

                rem Process command line override of # of files to process:
                        rem echo [PRE]  workload=“%workload%”,workload2=“%workload2%”  ... %%1=%1,%%2=%2,%%3=%3,%%4=%4
                        if "%1" == "karaoke" shift
                        if "%1" == "prompts" shift
                        rem TODO add?: if "%1" == "lyrics" shift
                        if "%1" !=    ""     set workload=%1
                        if "%2" !=    ""     set workload2=%2
                        rem echo [POST] workload=“%workload%”,workload2=“%workload2%”

                rem DO THE ACTUAL WORK!! Call the pre-determined proper script + playlist + workload:
                        iff "%worker%" !=  "" then
                                set worker_call=call %worker% %PLAYLIST_TO_WORK% %@IF["%workload%" != "",%workload%,%@IF["%workload2" != "",%workload2%,10]] %3$
                                echo %ansi_color_important%%STAR2% Calling worker: %worker_call%%ansi_color_normal%
                                %worker_call%
                        endiff

                rem Ask if we want to keep on chompin’... 
                rem If we answer “Yes”, then we must simulate, that we answered “K” to the original 
                rem                             “What kind of work do you want to do?” question
                        set WAIT_TIME=30
                        if "1" == "%LYRIC_KARAOKE_ALIGNMENT_THOROUGH_MODE%" set WAIT_TIME=0
                        call AskYN "Keep on chompin’" yes 30
                                iff "%ANSWER%" == "Y" then
                                        set ANSWER=%work_type_answer% 
                                        goto /i beginning_of_karaoke_or_lyric_work 
                                endiff
        endiff
        rem think we can get rid of this: (TODO get rid of this comment): if "Y" == "%ANSWER%" .or. "K" == "%ANSWER%"  goto /i  beginning_of_karaoke_or_lyric_work


:━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
:━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
goto :end_of_subroutines

        :usage
                echo.
                %color_advice%
                                echo USAGE:  %star2% For AI transcription project:
                                echo USAGE:      work lyrics
                                echo USAGE:      work karaoke
                                echo USAGE:      work prompts
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

