@Echo Off
@loadbtm on
@set whisper_alignment_happened=0



rem Install WhisperTimeSync with:  git clone https://github.com/EtienneAb3d/WhisperTimeSync.git
rem Set JAVA_WHISPERTIMESYNC=      to the path of the java.exe you wish to use. Or just set it to "java"

rem Synchonize example from that github: java -Xmx2G -jar distrib/WhisperTimeSync.jar song.srt lyrics.txt en
                               

rem CONFIG:
        if not defined WHISPERTIME_SYNC_WINAMP_INTEGRATION set WHISPERTIME_SYNC_WINAMP_INTEGRATION=1    %+ rem For auto-enqueing the song afterward to see a live test
        set WhisperTimeSync=%UTIL2%\WhisperTimeSync\distrib\WhisperTimeSync.jar                         %+ rem Location of WhisperTimeSync .jar file
        set our_language=en                                                                             %+ rem Our default language

rem VALIDATE ENVIRONMENT:
        set  validated_srt_and_txt_for_whispertimesync_already=0
        iff "2" != "%validated_whispertimesync2%" then
                call validate-in-path errorlevel success WhisperTimeSync-helper divider print-with-columns.bat print_with_columns.py review-file review-files AskYN lyric-postprocessor.pl set-tmp-file
                rem  validate-environment-variables JAVA_WHISPERTIMESYNC our_language color_advice ansi_color_advice ansi_color_removal ansi_color_normal ansi_color_run smart_apostrophe italics_on italics_off lq rq smart_apostrophe
                call validate-environment-variables ANSI_COLORS_HAVE_BEEN_SET EMOJIS_HAVE_BEEN_SET JAVA_WHISPERTIMESYNC our_language 
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
        rem echo %%1 is %lq%%1%rq% %+ pause
        rem @echo on
        set      SRT=%@UNQUOTE[%1]
        set  SRT_OLD=%@UNQUOTE[%1]
        set  LYR_RAW=%@UNQUOTE[%2]
        set  aud_MP3=%@NAME[%SRT%].mp3
        set  aud_WAV=%@NAME[%SRT%].wav
        set aud_FLAC=%@NAME[%SRT%].flac
        rem @echo off
        if not exist "%SRT%" .or. not exist "%LRC%" call validate-environment-variables SRT LYR_RAW
        call validate-is-extension        "%SRT%"     *.srt
        call validate-is-extension        "%LYR_RAW%" *.txt

rem Make sure we’re dealing with *processed* lyrics for WhisperTimeSync:
        call set-tmp-file "postprocessed_lyrics"
        set lyr_processed=%tmpfile%.txt
        lyric-postprocessor.pl -A -L -S  "%LYR_RAW%"    >:u8%lyr_processed%
        if not exist %lyr_processed% call validate-environment-variable target "lyric-postprocessor.pl output file does not exist: “%lyr_processed%”"

rem Run WhisperTimeSync:
        set  validated_srt_and_txt_for_whispertimesync_already=1
    rem echo WhisperTimeSync-helper "%srt%" "%lyr_processed%"       %+ pause
        call WhisperTimeSync-helper "%srt%" "%lyr_processed%"       %+ rem “Did it work?”-style validation is in WhisperTimeSync-helper.bat
        set  validated_srt_and_txt_for_whispertimesync_already=0    %+ rem This flag has now been used and can be disposedo f

rem Did it work?
        call validate-environment-variable SRT_NEW "seems like we didn’t set SRT_NEW correctly, it’s value is “%SRT_NEW%”"




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







repeat 5 call divider %+ pause "let%smart_apostrophe%s try viewing our %italics_on%WhisperTimeSync%italics_off% results in a different way..." %+ repeat 5 call divider 






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
        call review-file       -wh -stU "%srt_old%"                   %+ rem 3 & 4
        echo %faint_on%(lyrics + [lyric stripe, original subtitle stripe] + original subtitles ... srt_old=“%srt_old%”%faint_off%
        call divider

rem Preview the old subtitles vs the new subtitles, with stripes for both between them:
        call print-with-columns    -st  "%srt_old%"                   %+ rem 5
        call review-file       -wh -stU "%srt_new%"                   %+ rem 6 & 7
        call divider

rem Compare stripes of old subtitle to lyrics:
        echo %STAR2% %double_underline_on%OLD%double_underline_off% subtitles vs lyrics:
echo    call print-with-columns    -st  "%srt_old%"                   %+ rem 8
        call print-with-columns    -st  "%srt_old%"                   %+ rem 8
echo    call print-with-columns    -st  "%lyr_processed%"             %+ rem 9
        call print-with-columns    -st  "%lyr_processed%"             %+ rem 9
        echo %faint_on% original subtitle + stripe, lyrics + stripe%faint_off%
        call divider

rem Compare stripes of new subtitle to lyrics:
        echo %STAR2% %double_underline_on%NEW%double_underline_off% subtitles vs lyrics:
echo    call print-with-columns    -st  "%srt_new%"                   %+ rem 10
        call print-with-columns    -st  "%srt_new%"                   %+ rem 10
echo    call print-with-columns    -st  "%lyr_processed%"             %+ rem 9
        call print-with-columns    -st  "%lyr_processed%"             %+ rem 9
        echo %faint_on% new subtitle + stripe, lyrics + stripe%faint_off%
        call divider 



rem Ask if it’s better or not...
        :AskYnIfBetter
        call AskYN "%faint_on%[WhisperTimeSync]%faint_off% Is this realignment better than the original" no 0 P P:play_it

rem Preview if it need be, prior to asking
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
                        rem echo *copy /Nst "%srt%"     "%srt%.pre-wts.%_DATETIME.bak" 
                        echo ray|*copy /Nst "%srt%"     "%srt%.pre-wts.%_DATETIME.bak" 
                rem move the new karaoke to overwrite the now-backed-up old karaoke:
                        echos %ansi_color_success%
                        rem echo *copy /Nst "%SRT_NEW%" "%srt%" 
                        echo ray|*copy /Nst "%SRT_NEW%" "%srt%" %+ rem pause
        else
                        set whisper_alignment_happened=0
                        echos %ansi_color_removal%
                        echo ray|*del  /q   "%SRT_NEW%" 
        endiff
        echos %ansi_color_normal%




rem Load the new song into winamp to test?
        iff "1" == "%WHISPERTIME_SYNC_WINAMP_INTEGRATION%" then
                call divider
                echo %ansi_color_important%%STAR% Because %italics_on%WHISPERTIME_SYNC_WINAMP_INTEGRATION%italics_off% is set to %lq%1%rq% in WhisperTimeSync-helper.bat, we will ask:%ansi_color_normal%
                call askyn "Enqueue the song into WinAmp to see how the subtitles play in Minilyrics" no 0
                iff "Y" == "%ANSWER%" then
                        if exist "%aud_wav%"  set our_audio=%aud_wav%
                        if exist "%aud_mp3%"  set our_audio=%aud_mp3%
                        if exist "%aud_flac%" set our_audio=%aud_flac%
                        iff not exist "%our_audio%" then
                                call debug   "[our_audio=%lq%%italics_on%%our_audio%%italics_off%%rq%]"
                                call warning "Oops! Can%smart_apostrophe%t find our audio file!"
                                call advice  "Try manually setting it?"
                                eset our_audio
                        endiff
                        iff not exist "%our_audio%" then
                                call debug   "[our_audio=%lq%%italics_on%%our_audio%%italics_off%%rq%]"
                                call warning "Still can%smart_apostrophe%t find our audio file! Giving up!"
                                goto /i END
                        endiff
                        call enqueue "%our_audio%"
                        call winamp-next        
                endiff
        endiff



:END


:Cleanup
        set validated_srt_and_txt_for_whispertimesync_already=0


