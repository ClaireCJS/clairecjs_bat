@Echo Off
@loadbtm on
@set whisper_alignment_happened=0

rem Install WhisperTimeSync with:  git clone https://github.com/EtienneAb3d/WhisperTimeSync.git
rem Set JAVA_WHISPERTIMESYNC=      to the path of the java.exe you wish to use. Or just set it to "java"

rem Synchonize example from that github: java -Xmx2G -jar distrib/WhisperTimeSync.jar song.srt lyrics.txt en
                               

rem CONFIG:
        set WhisperTimeSync=%UTIL2%\WhisperTimeSync\distrib\WhisperTimeSync.jar
        set our_language=en

rem VALIDATE ENVIRONMENT:
        set  validated_srt_and_txt_for_whispertimesync_already=0
        iff "2" != "%validated_whispertimesync2%" then
                call validate-in-path errorlevel success WhisperTimeSync-helper divider print-with-columns.bat print_with_columns.py review-file review-files AskYN lyric-postprocessor.pl set-tmp-file
                call validate-environment-variables JAVA_WHISPERTIMESYNC our_language color_advice ansi_color_advice ansi_color_removal ansi_color_normal ansi_color_run
                call validate-is-function cool_text
                set  validated_whispertimesync2=2
        endiff

rem USAGE:
        iff "%1" == "" .or. "%2" == "" then
                echo.
                call divider
                %color_advice%
                        echo.
                        echo USAGE: %0 [subtitle file with bad words and good timing] [lyric file with good words and no/bad timing]
                        echo USAGE: %0 [subtitles] [lyrics]
                        echo    EX: %0  %@cool_text[bad.srt good.txt]%ansi_color_advice%
                        rem     EX: %0  %@cool_text[subtitles.srt lyrics.txt]%ansi_color_advice%
                call divider
                echo.
                goto :END
        endiff

rem VALIDATE PARAMETERS:
        set     SRT=%@UNQUOTE[%1]
        set LYR_RAW=%@UNQUOTE[%2]
        set     MP3=%NAME[%LYR%].mp3
        set     WAV=%NAME[%LYR%].wav
        set    FLAC=%NAME[%LYR%].flac
        if not exist "%SRT%" .or. not exist "%LRC%" call validate-environment-variables SRT LYR_RAW
        call validate-is-extension        "%SRT%"     *.srt
        call validate-is-extension        "%LYR_RAW%" *.txt

rem Make sure we’re dealing with *processed* lyrics for WhisperTimeSync:
        call set-tmp-file "postprocessed_lyrics"
        set lyr_processed=%tmpfile%.txt
        lyric-postprocessor.pl -A -L -S  "%FILE_TO_USE%"   >:u8 %lyr_processed%
        if not exist %lyr_processed% call validate-environment-variable target "lyric-postprocessor.pl output file does not exist: “%lyr_processed%”"

rem Run WhisperTimeSync:
        set  validated_srt_and_txt_for_whispertimesync_already=1
        call WhisperTimeSync-helper "%srt%" "%lyr_processed%"       %+ rem “Did it work?”-style validation is in WhisperTimeSync-helper.bat
        set  validated_srt_and_txt_for_whispertimesync_already=0    %+ rem This flag has now been used and can be disposedo f


rem Preview changes:
rem            1 lyrics                   \__ review lyrics with stripe
rem            2     lyrics stripe        /  
rem            3     Old Subtitles stripe \__ review subtitles with upper stripe  
rem            4 Old Subtitles            /
rem            5     Old Subtitles stripe
rem            6     New Subtitles stripe\___ review new subtitles with upper stripe
rem            7 New Subtitles           /
rem            8     Old Subtitles stripe
rem            9     lyrics stripe
rem            10    New Subtitles stripe

rem Preview the lyrics vs OLD srt with stripes next to each other:
        call review-file       -wh -st  "%lyr_processed%"             %+ rem 1 & 2
        call review-file       -wh -stU "%srt%"                       %+ rem 3 & 4
        call divider
        call print-with-columns    -st  "%srt%"                       %+ rem 5

rem Preview the NEW srt with stripes next to each other:
        call review-file       -wh -stU "%srt_new%"                   %+ rem 6 & 7

rem Compare stripes of old srt and new srt:
        call divider
        call print-with-columns    -st  "%lyr_processed%"             %+ rem 9
        call print-with-columns    -st  "%srt%"                       %+ rem 8
        call print-with-columns    -st  "%srt_new%"                   %+ rem 10
        call print-with-columns    -st  "%lyr_processed%"             %+ rem 9
        echo %faint_on%(lyrics, original subtitle, new subtitle, lyrics again)%faint_off%
        call divider




repeat 5 call divider %+ pause "let’s try a different way..." %+ repeat 5 call divider 


rem Preview changes:
rem            1 lyrics                   \__ review lyrics with stripe
rem            2     lyrics stripe        /  
rem            3     Old Subtitles stripe \__ review subtitles with upper stripe  
rem            4 Old Subtitles            /
rem            5     Old Subtitles stripe
rem            6     New Subtitles stripe\___ review new subtitles with upper stripe
rem            7 New Subtitles           /
rem            10    New Subtitles stripe
rem            9     lyrics stripe
rem            8     Old Subtitles stripe

rem Preview the lyrics vs OLD srt with stripes next to each other:
        call review-file       -wh -st  "%lyr_processed%"             %+ rem 1 & 2
        call review-file       -wh -stU "%srt%"                       %+ rem 3 & 4
        call divider

rem Preview the old subtitles vs the new subtitles, with stripes for both between them:
        call print-with-columns    -st  "%srt%"                       %+ rem 5
        call review-file       -wh -stU "%srt_new%"                   %+ rem 6 & 7
        call divider

rem Compare stripes of old subtitle to lyrics:
        echo %STAR2% %double_underline_on%OLD%double_underline_off% subtitles vs lyrics:
        call print-with-columns    -st  "%srt%"                       %+ rem 8
        call print-with-columns    -st  "%lyr_processed%"             %+ rem 9
        echo %faint_on%(lyrics + [lyric stripe, original subtitle stripe], original subtitle, DIVIDER, new subtitle + [new subtitle stripe, lyric stripe, old-subtitle stripe])%faint_off%
        call divider

rem Compare stripes of new subtitle to lyrics:
        echo %STAR2% %double_underline_on%NEW%double_underline_off% subtitles vs lyrics:
        call print-with-columns    -st  "%srt_new%"                   %+ rem 10
        call print-with-columns    -st  "%lyr_processed%"             %+ rem 9
        call divider 



rem Ask if it’s better or not...
        :AskYnIfBetter
        call AskYN "%faint_on%[WhisperTimeSync]%faint_off% Is this realignment better than the original" no 0 P P:play_it
        iff "%ANSWER%" == "P" then
                rem DEBUG:
                        echo %ansi_color_subtle%🐐 %0: call vlc %@if[exist "%mp3%","%mp3%",] %@if[exist "%flac%","%flac%",]%ansi_color_normal%
                rem PLAY IT:
                        call vlc %@if[exist "%mp3%","%mp3%",] %@if[exist "%flac%","%flac%",]
                        goto :AskYnIfBetter
        endiff

rem If it is better, back up the old version and replace it with this one:
        set whisper_alignment_happened=0
        iff "Y" == "%ANSWER%" then
                rem Audit flag:
                        set whisper_alignment_happened=1
                rem back up the old/existing karaoke:
                        echos %ansi_color_removal%
                        echo     *copy /Nst "%srt%"      "%srt%.pre-wts.%_DATETIME.bak" 
                        echo ray|*copy /Nst "%srt%"      "%srt%.pre-wts.%_DATETIME.bak" 
                rem move the new karaoke to overwrite the now-backed-up old karaoke:
                        echos %ansi_color_success%
                        echo     *copy /Nst "%SRT_NEW%"  "%srt%" 
                        echo ray|*copy /Nst "%SRT_NEW%"  "%srt%" %+ pause
        else
                        set whisper_alignment_happened=0
                        echos %ansi_color_removal%
                        echo ray|*del  /q   "%SRT_NEW%" 
        endiff
        echos %ansi_color_normal%


:END


:Cleanup
        set validated_srt_and_txt_for_whispertimesync_already=0


