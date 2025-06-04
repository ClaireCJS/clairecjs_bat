@Echo Off
@loadBTM ON
@on break cancel



rem SETUP: 
rem
rem 1) Install WhisperTimeSync with:      git clone https://github.com/EtienneAb3d/WhisperTimeSync.git
rem 2) Set JAVA_WHISPERTIMESYNC=          to the path of the java.exe you wish to use. Or just set it to "java"
rem
rem Synchonize example from that github: java -Xmx2G -jar distrib/WhisperTimeSync.jar song.srt lyrics.txt en



rem TODO: Possble idea: Preview it if 3ʳᵈ “preview” option (TODO) is passed?


                               

rem CONFIG:
        set WhisperTimeSync=%UTIL2%\WhisperTimeSync\distrib\WhisperTimeSync.jar
        set our_language=en

rem VALIDATE ENVIRONMENT:
        iff "1" != "%validated_whispertimesynchelper%" then
                call validate-in-path               errorlevel askyn enqueue.bat warning.bat advice.bat print-message.bat winamp-next subtitle-postprocessor.pl perl preview-audio-file.bat tail 
                rem  validate-environment-variables JAVA_WHISPERTIMESYNC WhisperTimeSync our_language color_advice ansi_color_advice lq rq underline_on underline_off italics_on italics_off
                call validate-environment-variables ANSI_COLORS_HAVE_BEEN_SET EMOJIS_HAVE_BEEN_SET JAVA_WHISPERTIMESYNC our_language WhisperTimeSync 
                call validate-is-function           cool_text
                call checkeditor
                set  validated_whispertimesynchelper=1
        endiff



rem USAGE:
        iff "%1" eq "" .or. "%2" eq "" then
                echo.
                call divider
                %color_advice%
                        echo.
                        echo USAGE: %0 {subtitle file with bad words and good timing} {lyric file with good words and no/bad timing} [optional audio file]
                        echo USAGE: %0 {subtitles} {lyrics} [audio_file]
                        echo    EX: %0  %@cool_text[subtitl.srt lyrics.txt]%ansi_color_advice%
                        echo    EX: %0  %@cool_text[subtitl.srt crappy.srt]
                call divider
                echo.
                goto :END
        endiff

rem VALIDATE PARAMETERS:
        set SRT=%@UNQUOTE[%1]
        set LYR=%@UNQUOTE[%2]
        set AFL=%@UNQUOTE[%3]
        iff "1" != "%validated_srt_and_txt_for_whispertimesync_already%" then
                call validate-environment-variables   SRT     LYR
                call validate-is-extension          "%SRT%" *.srt
                call validate-is-extension          "%LYR%" *.txt
        endiff

rem Extra prep of lyrics:
        iff "1" != "%WHISPERTIMESYNC_QUICK%" then
                set held_answer_wtsh=%ANSWER%
                call warning "Get the lyrics %blink_on%perfect%blink_off%" big
                call AskYN   "Edit lyrics for required perfection"   yes 0
                iff "Y" == "%ANSWER%" then
                        rem Ask if we want to listen to the song while editing:
                                echo * Audio file==%AFL%
                                call AskYN   "Listen to the audio file while editing lyrics"   no  0
                                %EDITOR% "%LYR%"

                        rem If we answered “yes”, then play that song:
                                iff "Y" == "%ANSWER%" then
                                        set PAF_START=start
                                        call preview-audio-file.bat "%AFL%"
                                endiff

                        rem Pause this script while they go edit...
                                pause "Press any key after fixing up the lyrics"

                        rem Ask if we want to copy these lyrics back over our official file when we’re done
                                iff exist "%AFL%" .and. "1" != "%WHISPERTIMESYNC_QUICK%" then
                                        call warning_soft "Do you want these lyric edits to be saved over the original lyric file?" %+ rem  [[not!!]] at %faint_on%%italics_on%%lyr%%italics_off%%faint_off%
                                        call AskYN          "Copy lyric edits over original lyrics" no 0
                                                iff "Y" == "%ANSWER%" then
                                                        set      COMMAND=copy "%LYR%" "%@NAME["%AFL%"].txt"
                                                        rem echo COMMAND is %COMMAND% %+ pause
                                                        %color_removal%
                                                        %COMMAND%
                                                endiff
                                endiff
        endiff



rem Run WhisperTimeSync:
        %color_run%
        echo %STAR3% Running WhisperTimeSync...%ansi_move_up_1%
        "%JAVA_WHISPERTIMESYNC%" -Xmx2G -jar %WhisperTimeSync% "%srt%" "%lyr%" %our_language%
        call errorlevel

rem Determine output filenames:
        set BASE=%@NAME[%SRT%]
        rem SRT_NEW=%BASE%.txt.srt
        rem SRT_NEW=%@NAME["%LYR%"].txt.srt
        set SRT_NEW=%@PATH[%@UNQUOTE["%LYR%"]]%@NAME[%@UNQUOTE["%LYR%"]].txt.srt                                          %+ rem Never as simple as you think....
        rem eset SRT_NEW

rem Did it work?
        iff exist "%SRT_NEW%" then
                call success "%italics_on%WhisperTimeSync%italics_off% successful"
        else
                if not exist "%SRT_NEW%" call validate-environment-variable SRT_NEW "WhisperTimeSync did not produce expected output file of %lq%%SRT_NEW%%rq%"
        endiff


rem WhisperTimeSync is horribly buggy so we fix some of that——particularly the blocks that are completely missing lyrics——with our subtitle postprocessor:
        echo %ansi_color_important%%star% Postprocessing subtitle file because %italics_on%WhisperTimeSync%italics_off% produces malformed SRT files...%ansi_color_normal%
        subtitle-postprocessor.pl "%SRT_NEW%"

rem WhisperTimeSync is horribly buggy so manual review/fix is needed:
        rem  warning "%underline_on%WhisperTimeSync%underline_off% is buggy af%italics_off%" big
        echo %ANSI_COLOR_WARNING_SOFT%%STAR2% Quick review of subtitles:%ansi_color_normal%
        echo %ANSI_COLOR_WARNING_SOFT%%STAR2% %italics_on%WhisperTimeSync%italics_off% often gets the very beginning wrong%ansi_color_normal%
        echo %ANSI_COLOR_WARNING_SOFT%%zzzzz% ❶  Take special care that the very beginning / first words fall within a subtitle"  silent
        echo %ANSI_COLOR_WARNING_SOFT%%zzzzz% ❷  There shouldn’t be duplicate timestamps in different blocks (TODO: write autochecker)
        echo %ANSI_COLOR_WARNING_SOFT%%zzzzz% ❸  If the last timestamp of the new subtitles, which is:

        @echo off
        call set-tmp-file subtitle-final-timestamp-grep-results 
        set last_timestamp_old_file=%tmpfile1%
        set last_timestamp_new_file=%tmpfile2%
        ((grep "[0-9][0-9]:[0-9][0-9]:[0-9][0-9],[0-9][0-9][0-9].....[0-9][0-9]:[0-9][0-9]:[0-9][0-9],[0-9][0-9][0-9]" "%@UNQUOTE["%srt_new%"]" |:u8 tail -1 |:u8 cut -c 18- | sed -e "s/^00://g" -e "s/^0//g" -e "s/,/./g" ) >:u8 %last_timestamp_new_file%)
        ((grep "[0-9][0-9]:[0-9][0-9]:[0-9][0-9],[0-9][0-9][0-9].....[0-9][0-9]:[0-9][0-9]:[0-9][0-9],[0-9][0-9][0-9]" "%@UNQUOTE["%srt_old%"]" |:u8 tail -1 |:u8 cut -c 18- | sed -e "s/^00://g" -e "s/^0//g" -e "s/,/./g" ) >:u8 %last_timestamp_old_file%)
        iff %@CRC32["%last_timestamp_new_file%"] ne %@CRC32["%last_timestamp_old_file%"] then
                call warning "Final timestamps differ!" big
                set our_display_color=%ansi_color_bright_red%
        else
                call success "Final timestamps are the same, so we’re probably fine!" big
                set our_display_color=%ansi_color_bright_green%
                
        endiff
        echos %ansi_color_important%              %star2% last timestamp %@cursive_plain[for] %ansi_color_bright_red%%zzzzzz%%italics_on%old%italics_off%%ansi_color_important% subtitles is: %our_display_color% %+ type %last_timestamp_new_file%
        echos %ansi_color_important%              %star2% last timestamp %@cursive_plain[for] %ansi_color_bright_green%%zzzz%%italics_on%new%italics_off%%ansi_color_important% subtitles is: %our_display_color% %+ type %last_timestamp_old_file%

        %EDITOR% "%SRT_NEW%" "%SRT_OLD%"
        pause "Press any key after BRIEFLY reviewing the subtitles for malformed blocks and making sure the first word(s) are inside a valid block and no blocks have same timestamps"



:END

