@loadbtm on
@Echo OFF
@set whisper_alignment_happened=0

if  "%1" == "jump" goto :jump_point
iff "%1" == "fast" .or. "%1" == "quick" .or. "%2" == "fast" .or. "%2" == "quick"  .or. "%3" == "fast" .or. "%3" == "quick"  .or. "%4" == "fast" .or. "%4" == "quick"  then
        set WHISPERTIMESYNC_QUICK=1
else
        set WHISPERTIMESYNC_QUICK=0
endiff

rem Install WhisperTimeSync with:  git clone https://github.com/EtienneAb3d/WhisperTimeSync.git
rem Set JAVA_WHISPERTIMESYNC=      to the path of the java.exe you wish to use. Or just set it to "java"

rem Synchonize example from that github: java -Xmx2G -jar distrib/WhisperTimeSync.jar song.srt lyrics.txt en
                               

rem CONFIG:
        if not defined WHISPERTIME_SYNC_WINAMP_INTEGRATION set WHISPERTIME_SYNC_WINAMP_INTEGRATION=1    %+ rem For auto-enqueing the song afterward to see a live test
        set WhisperTimeSync=%UTIL2%\WhisperTimeSync\distrib\WhisperTimeSync.jar                         %+ rem Location of WhisperTimeSync .jar file
        set our_language=en                                                                             %+ rem Our default language

rem VALIDATE ENVIRONMENT:
        set  validated_srt_and_txt_for_whispertimesync_already=0
        iff "1" != "%validated_whispertimesync%" then
                call validate-in-path errorlevel success WhisperTimeSync-helper divider print-with-columns.bat print_with_columns.py review-file review-files AskYN lyric-postprocessor.pl set-tmp-file enqueue.bat visual-comparison.bat
                rem  validate-environment-variables JAVA_WHISPERTIMESYNC our_language color_advice ansi_color_advice ansi_color_removal ansi_color_normal ansi_color_run smart_apostrophe italics_on italics_off lq rq smart_apostrophe
                call validate-environment-variables ANSI_COLORS_HAVE_BEEN_SET EMOJIS_HAVE_BEEN_SET JAVA_WHISPERTIMESYNC our_language lq rq 
                call validate-is-function cool_text
                set  validated_whispertimesync=1
        endiff

rem USAGE:
        iff "%1" == "" .or. "%2" == "" then
                echo.
                call divider
                %color_advice%
                        echo.
                        echo USAGE: %0 {subtitle file with bad words and good timing} {lyric file with good words and no/bad timing} [optional filename of audio_file]
                        echo USAGE: %0 {subtitle} {lyrics} [audio_file]
                        echo    EX: %0  %@cool_text[bad.srt good.txt]%ansi_color_advice%
                        rem     EX: %0  %@cool_text[subtitles.srt lyrics.txt]%ansi_color_advice%
                call divider
                echo.
                goto :END
        endiff

rem VALIDATE PARAMETERS:
        rem echo %%1 is %lq%%1%rq% %+ pause
        set      SRT=%@UNQUOTE[%1]
        set  SRT_OLD=%@UNQUOTE[%1]
        set  LYR_RAW=%@UNQUOTE[%2]
        set  AUD_FIL=%@UNQUOTE[%3]
        set  aud_MP3=%@NAME[%SRT%].mp3
        set  aud_WAV=%@NAME[%SRT%].wav
        set aud_FLAC=%@NAME[%SRT%].flac
        rem @Echo OFF
        if not exist "%SRT%" .or. not exist "%LRC%" call validate-environment-variables SRT LYR_RAW
        call validate-is-extension          "%SRT%"      *.srt
        call validate-is-extension          "%LYR_RAW%"  *.txt

rem Make sure we’re dealing with *processed* lyrics for WhisperTimeSync:

        rem Set post-processed filename:
                call set-tmp-file "WhisperTimeSync"
                set lyr_processed=%tmpfile%-postprocessed-lyrics.txt
                set lyr_processed_rendered_plus_bot_stripe=%tmpfile2%-lyr-plus-str.txt

        rem Run current iteration of lyrics through post-processor and make sure it was successful:
                set LYRICS_TO_POSTPROCESS=%lyr_raw%
                lyric-postprocessor.pl -A -L -S  "%LYRICS_TO_POSTPROCESS%"    >:u8%lyr_processed%
                call errorlevel                  "wts69 in %0"
                if not exist %lyr_processed% call validate-environment-variable target "lyric-postprocessor.pl output file does not exist: “%lyr_processed%”"


rem TODO: if aud_fil="" then check audmp3/wav/flac

rem Run WhisperTimeSync:
        set  validated_srt_and_txt_for_whispertimesync_already=1
        echo %ansi_color_debug%* About to: call WhisperTimeSync-helper "%srt%" "%lyr_processed%"  "%aud_fil%"%ansi_color_normal%
        call WhisperTimeSync-helper "%srt%" "%lyr_processed%"  "%aud_fil%"     %+ rem “Did it work?”-style validation is in WhisperTimeSync-helper.bat, so no need to do it here
        set  validated_srt_and_txt_for_whispertimesync_already=0               %+ rem This flag has now been used and can be disposedo f

rem Did it work?
        if not exist "%SRT_NEW%" call validate-environment-variable SRT_NEW "seems like we didn’t set SRT_NEW correctly, it’s value is %lq%%SRT_NEW%%rq%"





















rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ PREVIEW CHANGES: ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 


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


goto :new_way_212
        set SRT_OLD=%SRT%

rem Preview the lyrics vs OLD srt with stripes next to each other:
        call review-file        -wh -st  "%lyr_raw%" --output_file "%lyr_processed_rendered_plus_bot_stripe%" %+ type "%lyr_processed_rendered_plus_bot_stripe%"             %+ rem 1 & 2
rem     call review-file        -wh -stU "%srt_old%"                   %+ rem 3 & 4
rem     call divider
        call review-file -ins   -wh -stB "%srt_old%" "old subs"        %+ rem 3 & 4

rem Preview the NEW srt just past the old srt, with stripes next to each other:
rem     call print-with-columns -wh -st  "%srt_old%"                   %+ rem 5
        call review-file -ins   -wh -stU "%srt_new%" "new subs"        %+ rem 6 & 7
        call divider

rem Compare stripes of old srt and new srt:
        type "%lyr_processed_rendered_plus_bot_stripe%"               %+ rem call print-with-columns    -st  "%lyr_processed%"             %+ rem 9
        call print-with-columns -wh -st -ins "%srt_old%"              %+ rem 8
        call print-with-columns -wh -st -ins "%srt_new%"              %+ rem 10
        type "%lyr_processed_rendered_plus_bot_stripe%"               %+ rem call print-with-columns    -st  "%lyr_processed%"             %+ rem 9
        echo %faint_on%(lyrics, original subtitle, new subtitle, lyrics again)%faint_off%
        call divider







repeat 5 call divider %+ call important "let%smart_apostrophe%s try viewing our %italics_on%WhisperTimeSync%italics_off% results in a different way..." %+ repeat 5 call divider 
:new_way_212





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
        call review-file       -wh -st  -ins --output_file  "%lyr_processed_rendered_plus_bot_stripe%" "%lyr_processed%" %+ type "%lyr_processed_rendered_plus_bot_stripe%"            %+ rem 1 & 2
        call review-file       -wh -stU -ins "%srt_old%"                   %+ rem 3 & 4
        echo %faint_on%lyrics + stripe, old subtitle + stripe%faint_off%
        call divider

rem Preview the old subtitles vs the new subtitles, with stripes for both between them:
        call print-with-columns    -st  -ins "%srt_old%"                   %+ rem 5
        call review-file       -wh -stU -ins "%srt_new%"                   %+ rem 6 & 7
        echo %faint_on% old subtitle + stripe, new subtitle + stripe%faint_off%
        call divider

rem Compare stripes of old subtitle to lyrics:
        echo %STAR2% %double_underline_on%OLD%double_underline_off% lyrics vs subtitles:
        call print-with-columns    -st  -ins "%lyr_processed%"             %+ rem 9
        call print-with-columns    -st  -ins "%srt_old%"                   %+ rem 8
        echo %faint_on% lyrics + stripe, old subtitle + stripe%faint_off%
        call divider

rem Compare stripes of new subtitle to lyrics:
        echo %STAR2% %double_underline_on%NEW%double_underline_off% subtitles vs lyrics:
        type "%lyr_processed_rendered_plus_bot_stripe%"                    %+ rem  9 %+ rem call print-with-columns    -st  -ins "%lyr_processed%"             %+ rem 9
        call print-with-columns    -st  -ins "%srt_new%"                   %+ rem 10
        echo %faint_on% lyrics + stripe, new subtitle + stripe%faint_off%
        call divider 

rem Do the animated visual comparison:
        :jump_point
        echo %STAR2% %double_underline_on%NEW%double_underline_off% subtitles vs lyrics: %faint_on%[hit %left_apostrophe%X%right_apostrophe% to stop animation]%faint_off%
        call visual-comparison "%srt_old%" "%srt_new%" "%italics_on%old%italics_off% subtitles" "%italics_on%new%italics_off% subtitles"












rem Ask if it’s better or not...
        :AskYnIfBetter
        call AskYN "%faint_on%[WhisperTimeSync]%faint_off% Is this realignment better than the original [P=Play,Q=enQueue in WinAmp]" yes 0 PQ P:play_it,Q:enQueue_it

rem Preview if it need be, prior to asking:
        iff "%ANSWER%" == "P" then
                rem DEBUG:
                        echo %ansi_color_subtle%🐐 %0: call vlc %@if[exist "%aud_mp3%","%aud_mp3%",] %@if[exist "%aud_flac%","%aud_flac%",] %@if[exist "%aud_wav%","%aud_wav%",]%ansi_color_normal%
                rem PLAY IT:
                        call                                vlc %@if[exist "%aud_mp3%","%aud_mp3%",] %@if[exist "%aud_flac%","%aud_flac%",] %@if[exist "%aud_wav%","%aud_wav%",]
                rem GO BACK TO OUR QUESTION AGAIN:
                        goto :AskYnIfBetter
        endiff

rem Enqueue in WinAmp, which requires copying our audio file into the temp folder next to our provisional/freshly-generated/not-yet-approved-so-not-yet-copied-to-real-locatin-yet subtitles:
        iff "%ANSWER%" == "Q" then
                rem DETERMINE AUDIO FILE THAT WE WILL NEED TO COPY INTO TEMP FOLDER:                                
                        if exist "%aud_wav%"      SET FILE_TO_COPY=%aud_wav%
                        if exist "%aud_mp3%"      SET FILE_TO_COPY=%aud_mp3%
                        if exist "%aud_flac%"     SET FILE_TO_COPY=%aud_flac%
                        if exist "%aud_fil%"      SET FILE_TO_COPY=%aud_fil%
                rem DETERMINE TARGET FILENAME THAT WE WILL NEED TO COPY THE FILE TO:
                        SET  COPIED_FILE=%@PATH[%SRT_NEW%]\%@NAME[%SRT_NEW%].%@EXT["%FILE_TO_COPY%"]
                rem DEBUG:
                        rem pause "FILE_TO_COPY==%lq%%FILE_TO_COPY%%rq%, COPIED_FILE==%lq%%COPIED_FILE%%rq% (@NAME[SRT_NEW]=%lq%%@NAME[%SRT_NEW%]%rq%)"
                rem COPY THE FILE:
                        *copy "%FILE_TO_COPY%" "%COPIED_FILE%"
                rem DEBUG:
                        echo %ansi_color_subtle%🐐 %0: call enqueue "%COPIED_FILE%" %ansi_color_normal%
                rem PLAY IT:
                        call                                enqueue "%COPIED_FILE%"
                rem GO BACK TO OUR QUESTION AGAIN:
                        goto :AskYnIfBetter
        endiff

rem If it is better, back up the old version and replace it with this one:
        set whisper_alignment_happened=0
        set original_srt_before_whispertimesync=%srt%.pre-wts.%_DATETIME.bak
        iff "Y" == "%ANSWER%" then
                rem Audit flag:
                        set whisper_alignment_happened=1
                rem back up the old/existing karaoke:
                        echos %ansi_color_removal%
                        rem echo *copy /Nst "%srt%"     "%original_srt_before_whispertimesync%"
                        echo ray|*copy /Nst "%srt%"     "%original_srt_before_whispertimesync%"
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
                call askyn "Enqueue the song into %italics_on%WinAmp%italics_off% to see how the subtitles play in %italics_on%Minilyrics%italics_off%" no 0
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
                        %color_run%                                                        
                        call enqueue "%our_audio%"
                        %color_run%                                                        
                        call winamp-next        
                        %color_normal%                                                        
                endiff
        endiff



:END


:Cleanup
        set validated_srt_and_txt_for_whispertimesync_already=0


