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
                call validate-in-path errorlevel success WhisperTimeSync-helper divider print-with-columns.bat print_with_columns.py review-file review-files AskYN lyric-postprocessor.pl set-tmp-file enqueue.bat visual-comparison.bat srt_comparator.py subtitle-integrity-checker
                rem  validate-environment-variables JAVA_WHISPERTIMESYNC our_language color_advice ansi_color_advice ansi_color_removal ansi_color_normal ansi_color_run smart_apostrophe italics_on italics_off lq rq smart_apostrophe
                call validate-environment-variables ANSI_COLORS_HAVE_BEEN_SET EMOJIS_HAVE_BEEN_SET JAVA_WHISPERTIMESYNC our_language lq rq FILEEXT_AUDIO 
                call validate-is-function cool_text
                set  validated_whispertimesync=1
        endiff

rem IMPLIED PARAMETERS —— If we only give a song file as a first parameter, then we imply the rest:
        rem If the first parameter is a song file, but the other 2 parametesrs don’t exist, flip to implied parameter mode:
                set PARAM1=%@UNQUOTE[%1]
                set PARAM1_IS_AUDIO=0
                for %%tmpExt in (%FILEEXT_AUDIO%) if "%@EXT[%PARAM1%]" == "%tmpExt" set PARAM1_IS_AUDIO=1
                if "%2" != "" .or. "%3" != "" set PARAM1_IS_AUDIO=0     
        rem If it is, then we will react to it below
                

rem USAGE:
        iff "%@unquote[%1]" == "" .or. ("%@unquote[%2]" == "" .and. "0" == "%PARAM1_IS_AUDIO%") then
                echo.
                gosub divider
                %color_advice%
                        echo.
                        echo USAGE #1: %0 {subtitle} {lyrics} [audio_file]
                        echo USAGE #1: %0 {subtitle file with bad words and good timing} {lyric file with good words and no/bad timing} [optional filename of audio_file]
                        echo USAGE #2: %0 {audiofile} --`>` this mode automatically finds sidecar lyric and subtitle files from the audio filename
                        echo    EX #1: %0  %@cool_text[bad.srt good.txt]%ansi_color_advice%
                        echo    EX #2: %0  %@cool_text[song.mp3]%ansi_color_advice%
                        rem     EX: %0  %@cool_text[subtitles.srt lyrics.txt]%ansi_color_advice%
                gosub divider
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

        rem If our first parameter is an audio file, the other 2 parameters are implied:
                iff "1" == "%PARAM1_IS_AUDIO%" then
                        set  AUD_FIL=%@UNQUOTE[%1]
echo                    set      SRT=%@NAME[%AUD_FIL%].srt
                        set      SRT=%@NAME[%AUD_FIL%].srt
                        set  SRT_OLD=%SRT%
                        set  LYR_RAW=%@NAME[%AUD_FIL%].txt
                        set  aud_MP3=%@NAME[%AUD_FIL%].mp3
                        set  aud_WAV=%@NAME[%AUD_FIL%].wav
                        set aud_FLAC=%@NAME[%AUD_FIL%].flac                
                endiff

        if not exist "%SRT%" .or. not exist "%LRC%" call validate-environment-variables SRT LYR_RAW
        call validate-is-extension          "%SRT%"      *.srt
        call validate-is-extension          "%LYR_RAW%"  *.txt

rem Make sure we’re dealing with *processed* lyrics for WhisperTimeSync:

        rem Set post-processed filename:
                call set-tmp-file "WhisperTimeSync"
                set lyr_processed=%tmpfile%-proposed-new-subtitles-via-WhisperTimeSync.txt
                set lyr_processed_rendered_plus_bot_stripe=%tmpfile2%-lyr-plus-str.txt

        rem Run current iteration of lyrics through post-processor and make sure it was successful:
                set LYRICS_TO_POSTPROCESS=%lyr_raw%
                lyric-postprocessor.pl -A -L -S  "%LYRICS_TO_POSTPROCESS%"    >:u8%lyr_processed%
                call errorlevel                  "wts69 in %0"
                if not exist %lyr_processed% call validate-environment-variable target "lyric-postprocessor.pl output file does not exist: %lq%%lyr_processed%%rq%"


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
                                                                        rem     gosub divider
                                                                                call review-file -ins   -wh -stB "%srt_old%" "old subs"        %+ rem 3 & 4

                                                                        rem Preview the NEW srt just past the old srt, with stripes next to each other:
                                                                        rem     call print-with-columns -wh -st  "%srt_old%"                   %+ rem 5
                                                                                call review-file -ins   -wh -stU "%srt_new%" "new subs"        %+ rem 6 & 7
                                                                                gosub divider

                                                                        rem Compare stripes of old srt and new srt:
                                                                                type "%lyr_processed_rendered_plus_bot_stripe%"               %+ rem call print-with-columns    -st  "%lyr_processed%"             %+ rem 9
                                                                                call print-with-columns -wh -st -ins "%srt_old%"              %+ rem 8
                                                                                call print-with-columns -wh -st -ins "%srt_new%"              %+ rem 10
                                                                                type "%lyr_processed_rendered_plus_bot_stripe%"               %+ rem call print-with-columns    -st  "%lyr_processed%"             %+ rem 9
                                                                                echo %faint_on%(lyrics, original subtitle, new subtitle, lyrics again)%faint_off%
                                                                                gosub divider


repeat 5 gosub divider %+ call important "let%smart_apostrophe%s try viewing our %italics_on%WhisperTimeSync%italics_off% results in a different way..." %+ repeat 5 gosub divider 
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
        repeat 5 echo.
        call bigecho "%star% Review #1: Lyrics vs old subtitles:"
        call review-file       -wh -st  -ins --output_file  "%lyr_processed_rendered_plus_bot_stripe%" "%lyr_processed%" %+ type "%lyr_processed_rendered_plus_bot_stripe%"            %+ rem 1 & 2
        call review-file       -wh -stU -ins "%srt_old%"                   %+ rem 3 & 4
        echo %faint_on%lyrics + stripe, old subtitle + stripe%faint_off%
        gosub divider
        repeat 10 echo.

rem rem Preview the old subtitles vs the new subtitles, with stripes for both between them:
rem         call bigecho "Review #2 buggy: old vs new subtitles"
rem         call print-with-columns    -st  -ins "%srt_old%"                   %+ rem 5
rem         call review-file       -wh -stU -ins "%srt_new%"                   %+ rem 6 & 7
rem         echo %faint_on% That was old subtitle + stripe, new subtitle + stripe%faint_off%
rem         gosub divider
rem         repeat 10 echo.

rem Preview the old subtitles vs the new subtitles, with stripes for both between them:
        call bigecho "%star% Review #2: old vs new subtitles:"
        rem  print-with-columns    -st  -ins "%srt_old%"                   %+ rem 5
        call review-file       -wh -stL -ins "%srt_old%"                   %+ rem 6 & 7
        call review-file       -wh -stU -ins "%srt_new%"                   %+ rem 6 & 7
        echo %faint_on% That was old subtitle + stripe, new subtitle + stripe%faint_off%
        gosub divider
        repeat 10 echo.





rem rem Compare stripes of old subtitle to lyrics:
rem         call bigecho "Review #3 DEPRECATED: lyrics vs old subtitle"
rem         echo %STAR2% %double_underline_on%OLD%double_underline_off% lyrics vs subtitles:
rem         call print-with-columns    -st  -ins "%lyr_processed%"             %+ rem 9
rem         call print-with-columns    -st  -ins "%srt_old%"                   %+ rem 8
rem         echo %faint_on% That was lyrics + stripe, old subtitle + stripe%faint_off%
rem         gosub divider
rem         repeat 10 echo.


rem Compare stripes of old subtitle to lyrics:
        call bigecho "%star% Review #3: lyrics vs old subtitle:"
        echo %STAR2% %double_underline_on%OLD%double_underline_off% lyrics vs subtitles:
        call review-file       -wh -stL -ins "%lyr_processed%"                   
        call review-file       -wh -stU -ins "%srt_old%"                   
        echo %faint_on% That was lyrics + stripe, old subtitle + stripe%faint_off%
        gosub divider
        repeat 10 echo.




rem rem Compare stripes of new subtitle to lyrics:
rem         call bigecho "Review #4 deprecated: lyrics vs new subtitle"
rem         echo %STAR2% %double_underline_on%NEW%double_underline_off% subtitles vs lyrics:
rem         type "%lyr_processed_rendered_plus_bot_stripe%"                    %+ rem  9 %+ rem call print-with-columns    -st  -ins "%lyr_processed%"             %+ rem 9
rem         call print-with-columns    -st  -ins "%srt_new%"                   %+ rem 10
rem         echo %faint_on% That was lyrics + stripe, new subtitle + stripe%faint_off%
rem         gosub divider 
rem         repeat 10 echo.

rem Compare stripes of new subtitle to lyrics:
        call bigecho "%star% Review #4: lyrics vs new subtitle:"
        echo %STAR2% %double_underline_on%NEW%double_underline_off% subtitles vs lyrics:
        type "%lyr_processed_rendered_plus_bot_stripe%"                    %+ rem  9 %+ rem call print-with-columns    -st  -ins "%lyr_processed%"             %+ rem 9
        call review-file -stu  -ins "%srt_new%"                            %+ rem 10
        echo %faint_on% That was lyrics + stripe, new subtitle + stripe%faint_off%
        gosub divider 
        repeat 10 echo.





rem Do the animated visual comparison:
        :jump_point
        call bigecho "%star% Review #5: animated comparison: (hit %lq%X%rq% to end)"
        echo %STAR2% %double_underline_on%NEW%double_underline_off% old vs new subtitles:  %faint_on%[hit %left_apostrophe%X%right_apostrophe% to stop animation]%faint_off%
        call visual-comparison "%srt_old%" "%srt_new%" "%italics_on%old%italics_off% subtitles" "%italics_on%new%italics_off% subtitles"
        repeat 10 echo.

rem Use our comparator:
        rem Warn user:
                gosub divider
                call bigecho "%star% Review #6: old/new subtitle comparator:"
                rem pause "Presss any key to see SRT comparator output..."

        rem Run comparator:
                call set-tmp-file "comparator-output"                                %+ rem sets %tmpfile1%, %tmpfile2% automatically
                srt_comparator.py "%srt_old%" "%srt_new%" -hi -lr -key >"%tmpfile1%" %+ rem     using “--key” option
                srt_comparator.py "%srt_old%" "%srt_new%" -hi -lr      >"%tmpfile2%" %+ rem not using “--key” option
                goto :print_it_with_columns

                                                        rem Let’s try raw printing the results:
                                                                gosub divider
                                                                call debug "(type tmpfile1)"
                                                                type "%tmpfile1%"

        rem Let’s try generically printing the comparator output with however many columns it uses:
                :print_it_with_columns
                rem gosub divider
                rem call debug "(print tmpfile2 with columns)"
                call print-with-columns "%tmpfile2%"
                goto :done_with_comparator_output

                                                        rem Let’s try specifically printing the comparator output with 2 columns only:
                                                                gosub divider
                                                                rem call debug "(print tmpfile2 with 2 columns)"
                                                                call print-with-columns "%tmpfile2%" -c 2

                                                        rem Let’s try specifically printing the comparator output with 2/4/6/8 columns:
                                                                rem call debug "(print tmpfile2 with dynamic columns)"
                                                                gosub divider
                                                                if not defined SUBTITLE_OUTPUT_WIDTH set SUBTITLE_OUTPUT_WIDTH=30
                                                                SET COMPARATOR_PADDING=7
                                                                set COL_PADDING=5
                                                                set COL_SIZE=%@eval[%SUBTITLE_OUTPUT_WIDTH% + %COMPARATOR_PADDING%]
                                                                rem call debug "COL_SIZE initial value is %lq%%COL_SIZE%%rq%"
                                                                REM set    initial_column_pair_width=%@EVAL[2 * SUBTITLE_OUTPUT_WIDTH + 1 * PADDING + 7]
                                                                REM set subsequent_column_pair_width=%@EVAL[2 * SUBTITLE_OUTPUT_WIDTH + 2 * PADDING]
                                                                set INITIAL_COLS_TO_USE=10
                                                                set         COLS_TO_USE=%INITIAL_COLS_TO_USE%
                                                                :recol_calc
                                                                set TOTAL_WIDTH=%@EVAL[(%COLS_TO_USE% * %COL_SIZE%) + ((%COLS_TO_USE% - 1) * %COL_PADDING%)]
                                                                rem call debug "TOTAL_WIDTH for %COLS_TO_USE% columns is now being set to %lq%%TOTAL_WIDTH%%rq% [columns=%_COLUMNS]"
                                                                rem @EVAL[%initial_column_pair_width% + %subsequent_column_pair_width%] lt %@EVAL[%_COLUMNS-1] (set COLS_TO_USE=%@EVAL[%cols_to_use% + 2] %+ goto :recol_calc)
                                                                set MAX_WIDTH=%@EVAL[%_COLUMNS-3]
                                                                iff %TOTAL_WIDTH% gt %MAX_WIDTH% then
                                                                        set COLS_TO_USE=%@EVAL[%cols_to_use% - 1] 
                                                                        rem call debug "Because TOTAL_WIDTH[%TOTAL_WIDTH%] gt MAX_WIDTH[%MAX_WIDTH%] we need to use 1 fewer column, so wet have set COLS_TO_USE=%COLS_TO_USE%"
                                                                        if %COLS_TO_USE% gt 2 goto :recol_calc
                                                                endiff
                                                                rem call debug "determined # of even columns to use of %lq%%COLS_TO_USE%%rq%, COL_SIZE=%lq%%COL_SIZE%%rq%"                
                                                                rem call debug "call print-with-columns %tmpfile2% -c %COLS_TO_USE% [screen width=%_COLUMNS]"
                                                                call print-with-columns "%tmpfile2%" -c %COLS_TO_USE%

        rem Final divider:
                :done_with_comparator_output
                gosub divider






rem TODO GOATGOAT: This inform user about timestamp section moved from whispertimesync-helper to test if it works here:
rem Inform user if final timestamp on new subtitles is different from final timestamp on old subtitles:

        rem Inform user and run out external subtitle integrity checker utility that displays duplicate timestamps in a table:
                echo %ANSI_COLOR_LESS_IMPORTANT%%STAR2% Checking for duplicate timestamps...%ansi_color_normal%
                rem echo    subtitle-verifier.py --columns %_COLUMNS "%SRT_NEW%"
                call subtitle-integrity-checker "%SRT_NEW%"

        rem WhisperTimeSync is horribly buggy so manual review/fix is needed:
                rem  warning "%underline_on%WhisperTimeSync%underline_off% is buggy af%italics_off%" big
                echo %ANSI_COLOR_WARNING_SOFT%%STAR2% Potential manual review of subtitles:%ansi_color_normal%
                echo %ANSI_COLOR_WARNING_SOFT%  %STAR2% %italics_on%WhisperTimeSync%italics_off% on rare case gets the very beginning wrong%ansi_color_normal%
                echo %ANSI_COLOR_WARNING_SOFT%%zzzzz%      %inverse_circled_1%  Take special care that the very beginning / first words fall within a subtitle
                rem  We now have a program for this:       %inverse_circled_2%  There shouldn’t be duplicate timestamps in different blocks (TODO: write autochecker)
                echo %ANSI_COLOR_WARNING_SOFT%%zzzzz%      %inverse_circled_3%  If the last timestamp of the new subtitles, which is:


        rem Use grep+tail+cut+sed to extract the final timestamp from both the old and new subtitles into their own files:
                call set-tmp-file subtitle-final-timestamp-grep-results 
                set last_timestamp_old_file=%tmpfile1%
                set last_timestamp_new_file=%tmpfile2%
                rem ((grep -a "[0-9][0-9]:[0-9][0-9]:[0-9][0-9],[0-9][0-9][0-9].....[0-9][0-9]:[0-9][0-9]:[0-9][0-9],[0-9][0-9][0-9]" "%@UNQUOTE["%srt_old%"]" |:u8 tail -1 |:u8 cut -c 18- | sed -e "s/^00://g" -e "s/^0//g" -e "s/,/./g" ) >:u8 %last_timestamp_old_file%)
                ((type "%@UNQUOTE["%srt_old%"]" |:u8 grep -a "[0-9][0-9]:[0-9][0-9]:[0-9][0-9],[0-9][0-9][0-9].....[0-9][0-9]:[0-9][0-9]:[0-9][0-9],[0-9][0-9][0-9]" |:u8 tail -1 |:u8 cut -c 18- | sed -e "s/^00://g" -e "s/^0//g" -e "s/,/./g" ) >:u8 %last_timestamp_old_file%)       %+        if not exist %last_timestamp_old_file% call fatal_error "last_timestamp_new_file does not exist: %last_timestamp_old_file%"
                ((type "%@UNQUOTE["%srt_new%"]" |:u8 grep -a "[0-9][0-9]:[0-9][0-9]:[0-9][0-9],[0-9][0-9][0-9].....[0-9][0-9]:[0-9][0-9]:[0-9][0-9],[0-9][0-9][0-9]" |:u8 tail -1 |:u8 cut -c 18- | sed -e "s/^00://g" -e "s/^0//g" -e "s/,/./g" ) >:u8 %last_timestamp_new_file%)       %+        if not exist %last_timestamp_new_file% call fatal_error "last_timestamp_new_file does not exist: %last_timestamp_new_file%"

        rem Display final timestamp from each file:
                echos %ansi_color_important%              %star2% last timestamp %@cursive_plain[for] %ansi_color_bright_red%%zzzzzz%%italics_on%old%italics_off%%ansi_color_important% subtitles is: %our_display_color% %+ type %last_timestamp_new_file%
                echos %ansi_color_important%              %star2% last timestamp %@cursive_plain[for] %ansi_color_bright_green%%zzzz%%italics_on%new%italics_off%%ansi_color_important% subtitles is: %our_display_color% %+ type %last_timestamp_old_file%

        rem Warn user if the timestamps are different:
                iff %@CRC32["%last_timestamp_new_file%"] ne %@CRC32["%last_timestamp_old_file%"] then
                        call warning "Final timestamps differ!" big
                        call advice  "Make sure to manually review before/after subs in text editor"
                        *pause
                        set our_display_color=%ansi_color_bright_red%
                else
                        call success "Final timestamps are the same, so we%apostrophe%e probably fine!" big
                        set our_display_color=%ansi_color_bright_green%
                        
                endiff

        rem 2025/12/21 moved to WhisperTimeSync.bat:
        rem %EDITOR% "%SRT_NEW%" "%SRT_OLD%"
        rem pause "%ansi_color_prompt%Press any key after %italics_on%potentially%italics_off% reviewing the subtitles for malformed blocks & making sure the first word(s) are inside a valid block..."





rem Section moved from WhisperTimeSync-helper.bat (happening before our comparisons) to here:
        repeat 7 echo.
        call bigecho "Opening new/old subs in txt editor"
        %EDITOR% "%SRT_NEW%" "%SRT_OLD%"
        pause "%ansi_color_prompt%Press any key after %italics_on%potentially%italics_off% reviewing the subtitles for malformed blocks & making sure the first word(s) are inside a valid block..."







rem Ask if it’s better or not...
        :AskYnIfBetter
        call AskYN "%faint_on%[WhisperTimeSync]%faint_off% Is this realignment better than the original [%ansi_color_bright_green%P%ansi_color_prompt%=%ansi_color_bright_green%P%ansi_color_prompt%lay,%ansi_color_bright_green%Q%ansi_color_prompt%=en%ansi_color_bright_green%Q%ansi_color_prompt%ueue in WinAmp]" yes 0 PQ P:play_it,Q:enQueue_it

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
                gosub divider
                echo %ansi_color_important%%STAR% Because %italics_on%WHISPERTIME_SYNC_WINAMP_INTEGRATION%italics_off% is set to %lq%1%rq% in WhisperTimeSync-helper.bat, we will ask:%ansi_color_normal%
                call askyn "Enqueue the song into %italics_on%WinAmp%italics_off% to see how the subtitles play in %italics_on%Minilyrics%italics_off%" no 60 %+ rem Thorough mode will still bypass this prompt on timeout because if we aren’t paying attention we truly do want to move to the next task
                iff "Y" == "%ANSWER%" then
                        if exist "%aud_wav%"  set our_audio=%aud_wav%
                        if exist "%aud_mp3%"  set our_audio=%aud_mp3%
                        if exist "%aud_flac%" set our_audio=%aud_flac%
                        iff not exist "%our_audio%" then
                                rem call debug   "[our_audio=%lq%%italics_on%%our_audio%%italics_off%%rq%]"
                                call warning "Oops! Can%smart_apostrophe%t find our audio file!"
                                call advice  "Try manually setting it?"
                                eset our_audio
                        endiff
                        iff not exist "%our_audio%" then
                                rem call debug   "[our_audio=%lq%%italics_on%%our_audio%%italics_off%%rq%]"
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



goto :END


        :divider [divider_param]
                iff "1" == "%suppress_next_divider%" then
                        set  suppress_next_divider=0
                        return
                endiff

                rem Determine divider file to use:
                        set wd=%@EVAL[%_columns - 1]
                        set nm=%bat%\dividers\rainbow-%wd%.txt

                rem Type divider file if it exists:
                        iff exist %nm% then
                                *type %nm%
                                set last_divider_method=type
                                set last_divider_param=%divider_param%
                rem Otherwise, manually draw the divider:
                        else
                                echo %@char[27][93m%@REPEAT[%@CHAR[9552],%wd%]%@char[27][0m
                                set last_divider_method=echo
                        endiff

                rem Our divider files do not include newlines. Do we add one ourself?
                        rem debug: *pause>nul
                        iff "%divider_param%" == "NoNewline"  then
                                set last_divider_newline=False
                        else 
                                set last_divider_newline=True

                                rem Go to the next line:           
                                        rem echos %NEWLINE%
                                        echo.

                                rem Then move to column 0/1 [which are the same column]:
                                        echos %@ANSI_MOVE_TO_COL[0] 

                        endiff

                rem Debug:
                        echo wtf last_divider_newline=%last_divider_newline% should we do one? >nul
        return





:END


:Cleanup
        set validated_srt_and_txt_for_whispertimesync_already=0


