@Echo OFF
@loadbtm ON

:USAGE: delete-sidecar-lyric-and-subtitle-files-for-audiofiles-in-lyricless-approved-state ——— run it in default mode




rem Validate environment (once):
        iff "1" != "%validated_delsidclrsubfilfafinllappstttt%" then
                call validate-environment-variable  filemask_audio skip_validation_existence
                call validate-environment-variables faint_on faint_off ansi_color_normal ansi_color_important ansi_color_alarm ansi_color_green ansi_color_bright_green ansi_color_bright_red ansi_color_grey ansi_color_bright_yellow ansi_color_important_less underline_on underline_off no check ansi_save_position ansi_restore_position ansi_color_bright_green blink_off blink_on red_x emoji_warning axe tab newline logs
                call validate-is-functions          ansi_move_to_col ansi_move_to ansi_move_left ansi_move_up randfg_soft random_cursor_color
                set  validated_delsidclrsubfilfafinllappstttt=1
        endiff

rem Validate usage:
        :usage
        iff "%1" == "" .or. ("%1" != "ask" .and. "%1" != "force")  then
                echo.
                echo %no% %ansi_color_error%You must provide either “%blink_on%ask%blink_off%” or “%blink_on%force%blink_off%” as an argument%ansi_color_normal% %no%
                echo.
                echo %ansi_color_advice% Run “%0 ask”   ━━ to  %zzzzz%  %blink_on%ask%zzzzzzz%%blink_off%   for each deletion
                echo %ansi_color_advice% Run “%0 force” ━━ to  %zzzzzzz%%blink_on%force%zzzzz%%blink_off%       each deletion
                goto :END
        endiff

rem Set mode:
        unset /q mode
        if "%1" == "ask"   set mode=ask
        if "%1" == "force" set mode=force

rem CONSTANTS:
        set OUR_LOGFILE=%LOGS%\audiofile-transcription.log                                           %+ rem don’t change because this needs to be sync’ed with the value in report-lyric-approval-progress.bat
        set str_longest_possible_lyriclessness_status=NOT_APPROVED                                   %+ rem don’t change because this needs to be the longest-possible value of lyriclessness for a file. See get-lyrics for full list of valid values

rem How to represent our probing nature based on operational mode of this script:
        iff "1" != "%INSTRUMENTAL_PROCESSING_MODE%" then
                set str_probing_nature=lyric%underline_on%%italics_on%less%italics_off%%underline_off%ness   %+ rem how we want to write the word “lyriclessness”
        else
                set str_probing_nature=Instrumental ``                                                       %+ rem how we want to write the word “instrumental” —— the one space after is to match length with ‘lyriclessness’
        endiff
        set str_status_introd=%star% %str_probing_nature% is ``                                      %+ rem beginning of the line that displays lyriclessness status for each file

rem Debug logging:
        unset /q our_log*

rem Determine cosmetic values:
        rem Save screen width:
                set last_columns=%_columns
        rem Find longest filename, for cosmetic purposes:
                set longest_filename_length_here=-1                                                                                                                
                for %%tmpaudiofile_main in (%filemask_audio%) do (set len=%@LEN[%@UNQUOTE["%tmpaudiofile_main"]] %+ if %len% gt %longest_filename_length_here% set longest_filename_length_here=%len%)
        rem Determine 1ˢᵗ column stuffs:
                set column_for_blank_filled_in_with_approval_status=%@LEN[%@STRIPANSI[%str_status_introd%``]]                                                                                                                
        rem Determine 2ⁿᵈ column stuffs:
                set left_amount_for_filename_display=%@EVAL[%_columns - %col_3_max_width% - (%columns - %column_for_col_3%)]
        rem Determine 3ʳᵈ  column location and width:
                set col_3_max_width=20                                                                                                                                                            
                set column_for_col_3=%@MIN[%@EVAL[%_columns - %col_3_max_width%],%@EVAL[%column_for_blank_filled_in_with_approval_status% + %@LEN[%str_longest_possible_lyriclessness_status% for file: “] + %longest_filename_length_here% + 4]] 

rem Go through each file and do the thing:
        echo.
        for %%tmpaudiofile_main in (%filemask_audio%) do gosub process_file "%@UNQUOTE["%tmpaudiofile_main"]"
        goto :END


rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

:process_file [filename_to_process]
        rem Debug info:
                rem echo gosub process_file [%filename_to_process%]                   

        rem React to window being resized:
                iff  %_columns ne %last_columns then
                        set last_columns=%_columns
                        rem line copied from initialization above:
                        set column_for_col_3=%@MIN[%@EVAL[%_columns - 20],%@EVAL[%column_for_blank_filled_in_with_approval_status% + %@LEN[%str_longest_possible_lyriclessness_status% for file: “] + %longest_filename_length_here% + 4]] %+ rem 20=how wide col 3 gets
                endiff

        rem If we are in instrumental mode then leave if it is not an instrumental:
                iff "1" == "%INSTRUMENTAL_PROCESSING_MODE%" then
                        set filename=%@unquote["%filename_to_process%"]
                        set regex="[\(\[]instrumental[\]\)]"
                        set found=%@Regex[%regex%,"%filename%"] 
                        iff "%found%" == "1" then
                                set INSTRUMENTAL_STATUS=INSTRUMENTAL
                                rem echo %check% this is an instrumental: %filename_to_process%
                        else
                                set INSTRUMENTAL_STATUS=VOCAL
                                rem echo %red_x%  is NOT an instrumental: %filename_to_process%
                                rem return
                        endiff
                        goto /i determine_sidecar_filenames
                endiff                

        rem Get lyriclessness status:
                unset /q   LYRICLESSNESS_STATUS
                set        LYRICLESSNESS_STATUS=%@EXECSTR[type <"%@unquote["%filename_to_process%"]:lyriclessness" >&>nul]``
                if "" == "%LYRICLESSNESS_STATUS%" set LYRICLESSNESS_STATUS=NOT SET
                rem echo.

        rem Determine all the individual sidecars we want to erase for lyrics-unfindable(“lyriclessness approved”) audiofiles:        
                :determine_sidecar_filenames
                set SIDECAR_TXT=%@NAME[%filename_to_process%].txt
                set SIDECAR_LRC=%@NAME[%filename_to_process%].lrc
                set SIDECAR_SRT=%@NAME[%filename_to_process%].srt
                set SIDECAR_JSN=%@NAME[%filename_to_process%].json

        rem Then, group them together in multilpe ways, for later use:
                set our_log2=%our_log2%SIDECARS_TO_DELETE_1="%SIDECAR_TXT%" "%SIDECAR_LRC%" "%SIDECAR_SRT%" "%SIDECAR_JSN%"%newline%
                set SIDECARS_TO_DELETE_1="%SIDECAR_TXT%" "%SIDECAR_LRC%" "%SIDECAR_SRT%" "%SIDECAR_JSN%"
                set SIDECARS_TO_DELETE_2="%SIDECAR_TXT%";"%SIDECAR_LRC%";"%SIDECAR_SRT%";"%SIDECAR_JSN%"

        rem Get lyrics-approved status:
                iff "1" == "%INSTRUMENTAL_PROCESSING_MODE%" goto :display_filename
                set LYRIC_STATUS=DOES_NOT_EXIST
                if not exist "%SIDECAR_TXT%" goto :endif_99
                        set  LYRIC_STATUS=%@EXECSTR[type <"%SIDECAR_TXT%:lyrics" >&>nul]``
                        if "%LYRIC_STATUS%" == "" set LYRIC_STATUS=NOT SET
                :endif_99
                rem echo.
                

        rem Display filename / header:
                :display_filename
                echos %ansi_color_important%%str_status_introd%____________ for file: “%faint_on%%@UNQUOTE["%@LEFT[%left_amount_for_filename_display,%filename_to_process%]"]%faint_off%”...

        rem Display lyriclessness status:
                rem echo %ansi_color_important_less%%tab%%star2% %str_probing_nature% == “%@IF["APPROVED" == "%LYRICLESSNESS_STATUS%",%ansi_color_bright_green%,%ansi_color_bright_red%]%LYRICLESSNESS_STATUS%%ansi_color_important_less%”
                rem echo %@IF["APPROVED" == "%LYRICLESSNESS_STATUS%",%ansi_color_bright_green%,%ansi_color_bright_red%]%LYRICLESSNESS_STATUS%%ansi_color_important_less%

                rem Determine color to display status in, and which status we are displaying:
                        iff "1" != "%INSTRUMENTAL_PROCESSING_MODE%" then
                                                                              set color=%ansi_color_bright_yellow%
                                if     "APPROVED" == "%LYRICLESSNESS_STATUS%" set color=%ansi_color_bright_green%
                                if "NOT APPROVED" == "%LYRICLESSNESS_STATUS%" set color=%ansi_color_bright_red%
                                if      "NOT SET" == "%LYRICLESSNESS_STATUS%" set color=%ansi_color_grey%
                                set STATUS_TO_DISPLAY=%LYRICLESSNESS_STATUS%        
                        else
                                                                             set color=%ansi_color_bright_red%
                                if "INSTRUMENTAL" == "%INSTRUMENTAL_STATUS%" set color=%ansi_color_bright_green%
                                if        "VOCAL" == "%INSTRUMENTAL_STATUS%" set color=%ansi_color_grey%
                                set STATUS_TO_DISPLAY=%INSTRUMENTAL_STATUS%        
                        endiff

                rem Go to the column that was the blank and display the status:
                        echos %@ANSI_MOVE_TO_COL[%column_for_blank_filled_in_with_approval_status%]%COLOR%%STATUS_TO_DISPLAY%

        
        rem Then, go to edge of what we consider to be the 3ʳᵈ  column in our output:                
                        echos %@ANSI_MOVE_TO_COL[%column_for_col_3%]

rem     rem If it’s not approved as lyricless/lyrics-unfindable, then this script is not applicable, so we are done:
rem             if "APPROVED" != "%LYRICLESSNESS_STATUS%" (echo %NO% %+ return)
rem             echos %CHECK% ``

        rem If it’s not approved as lyricless/lyrics-unfindable, then this script is not applicable, so we are done:
                echos %NO%
                iff "1" != "%INSTRUMENTAL_PROCESSING_MODE%" then
                        if     "APPROVED" != "%LYRICLESSNESS_STATUS%" (echo. %+ return)
                        if     "APPROVED" == "%LYRICLESSNESS_STATUS%" (echo  %ansi_color_green%Lyrics approved  %+ return)
                else
                        rem INSTRUMENTAL" != "%INSTRUMENTAL_STATUS%"  (echo. %ansi_color_green%Not instrumental %+ return)
                        if "INSTRUMENTAL" != "%INSTRUMENTAL_STATUS%"  (echo. %+ return)
                endiff                

        rem At this point, it’s a lyriclessness file. We should not have lyric/subtitle sidecar files —— The purpose of this script is to delete them!
        
        rem Then give each one “the treatment”:
                rem Reset variable to hold error messages for (only) this file:
                        unset /q errmsg
                rem Determine ansi sequence to restore our position to “the spot”:
                        echos %@ansi_move_left[2]%check%
                        set saved_row=%_ROW
                        set saved_col=%_COLUMN
                        set restore_position=%@ansi_move_to[%@EVAL[%saved_row% + 1],%@EVAL[%saved_col% + 1]]
                rem Ask about deleting each sidecar file:
                        set any_deleted=0
                        iff exist %SIDECARS_TO_DELETE_2% then
                                rem Log the event:
                                        set our_log=%our_log%iff exist %SIDECARS_TO_DELETE_2% then is true for “%filename_to_process%”%newline%
                                        echo. >>:u8"%OUR_LOGFILE%"
                                        echo. >>:u8"%OUR_LOGFILE%"
                                        echo. >>:u8"%OUR_LOGFILE%"
                                        echo. %EMOJI_WARNING%%EMOJI_WARNING%%EMOJI_WARNING% WARNING: %@IF["1" == "%INSTRUMENTAL_PROCESSING_MODE%",Instrumental,Lyricless] file has inapplicable sidecar files: “%@FULL["%@UNQUOTE["%filename_to_process%"]"]” >>:u8"%OUR_LOGFILE%"

                                rem Move to the right spot and leave the default visual representation:
                                        echos %@ansi_move_left[2]%NO% ``

                                rem Process each potentially-existing sidecar file:
                                        for %%tmp_sidecar_file in (%SIDECARS_TO_DELETE_1%) gosub process_potential_sidecar_files "%@UNQUOTE["%tmp_sidecar_file%"]"               
                        else
                                iff "1" == "%INSTRUMENTAL_PROCESSING_MODE%" then
                                        echos %@ANSI_MOVE_LEFT[2]
                                        echos %NO% %ansi_color_green%No bad sidecars
                                endiff
                                rem echos no sidecars
                                echo.
                                return
                        endiff

        rem Cosmetics:
                rem Go to next line, but it kind of doesn’t matter because after this:
                       echo.
                rem ...we Set our position to the “next place”——which isn’t the same as “the spot”:
                        echos %@ansi_move_to[%@EVAL[%saved_row% + 0],%@EVAL[%saved_col% - 1]]

        rem Display our success/failure(s):
                iff "" == "%errmsg%" then
                        if "1" == "%any_deleted%" echos %check%%ansi_color_bright_green%%ZZZZ%%faint_on% ...%faint_off% Done! %faint_on%...%faint_off% %check%
                        if "1" != "%any_deleted%" echos %red_x%%ansi_color_bright_yellow%%ZZZ%%faint_on% ...%faint_off% Done! %faint_on%...%faint_off% %red_x%
                else
                        echos %ansi_color_bright_red%%red_x%%blink_on% %errmsg%%blink_off% %red_x%
                endiff
                echo.        
return

        :process_potential_sidecar_files [ tmp_sidecar_file ]
                rem De-quotify parameter:
                        set sidecar=%@UNQUOTE["%tmp_sidecar_file"]

                rem Extract the extension of the sidecar file:
                        set ext=%@EXT[%sidecar%]

                rem Return if the sidecar file doesn’t exist:
                        if exist "%sidecar%" goto :sidecar_exists
                                rem echo %sidecar% doesn’t exist
                                return
                        :sidecar_exists

                rem Return to “the spot”:
                        echos %restore_position% %ansi_color_bright_red%%blink_on%Delete%blink_off% %italics_on%%@randfg_soft[]%ext%%ansi_color_bright_red%%italics_off%%blink_on%?%blink_off% ``

                rem Ask to delete the sidecar files, unless we are in force mode:
                        unset /q ANSWER
                        iff "%mode%" == "ask" then
                                echos %@RANDOM_CURSOR_COLOR[]
                                call AskYn "Delete %italics_on%%ext%%italics_off% file %italics_on%“%sidecar%”%italics_off%" yes 0 invisible
                                echos %@ansi_move_left[1] ``
                        endiff
                        iff "%mode%" == "force" then
                                set ANSWER=Y
                        endiff

                rem Return if they did not say yes:
                        if "Y" != "%ANSWER%" goto :subroutine_cleanup 

                rem Delete the file silently:
                        (echo yra|*del /z /a: /Ns "%sidecar%" >>&nul)
                        set any_deleted=1

                rem Log the event:
                        echo. >>:u8"%OUR_LOGFILE%"
                        rem echo. >>:u8"%OUR_LOGFILE%"
                        echo. %tab%%AXE%%AXE%%AXE% Deleted sidecar file: “%sidecar%”>>:u8"%OUR_LOGFILE%"

                rem If it still exists, add an error to our %ERRMSG% variable:
                        if exist "%sidecar%" (set ERRMSG=%ERRMSG%“%sidecar%” still exists! `` %+ echo %ansi_color_alarm%?%ansi_color_normal%)

                rem Great ready to return:        
                        :subroutine_cleanup 
                        title %check%DONE: %@NAME["%tmp_sidecar_file%"]
        return

rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

:END


unset instrumental_status*

