@loadbtm on
@echo ━━━━━━━━DEL-MAYBE-AFTER-REVIEW: BEGIN━━━━━━━━
@rem call bat-init
@Echo OFF
@set dmar_title=%_title



rem CONFIG:
        set DEBUG_DEL_MAYBE_AFTER_REVIEW=0



rem Turn special chars off, even semicolons for multiple files, as we intend to use 
rem this one file at a time or with multiple files separated by a space not semicolon:
        *setdos /x-12456789

rem Get filename:
        set CMD_TAIL=%1$
        set OUR_TARGETS=%*
        setdos /x0

rem Validate filename:
        rem :validate_next_param
        rem if  ""  ==               "%1"  (goto :skip_val)
        rem if not exist "%@UNQUOTE["%1"]" (setdos /x0 %+ call error "file to maybe delete does not exist: “%1”")
        rem if  ""  !=               %2    (shift %+ goto :validate_next_param)
        rem :skip_val
        rem echo tail=%cmd_tail%,  our_targets=“%our_targets%”                                   
        rem pause
      
rem Validate environment once per session:
        iff "2" != "%validated_del_maybe_after_review%" then
                call validate-in-path               get-lyrics-for-file.btm preview-audio-file.bat review-file.bat review-files.bat print_with_columns.py print-with-columns grep remove-blank-lines echos preview-audio-file.bat enqueue-file-into-winamp-playlist.bat
                call validate-environment-variables emoji_have_been_set ansi_colors_have_been_set  
                call validate-is-function           randfg_soft
                call checkeditor
                set  validated_del_maybe_after_review=2
        endiff

rem Who is calling this bat file?
        set parent=%@NAME[%_PBATCHNAME]
        rem echo parent is %parent% %+ pause

rem Ask for each file, and delete:
        *setdos /x-168
        setdos /x0
        for %%tmp_target in (%OUR_TARGETS%) do gosub do_file "%@UNQUOTE["%tmp_target%"]"
        goto END_OF_DMAR


        :do_file [file]
                call review-file -st  "%@UNQUOTE["%file%"]"
                echo %star% %ansi_color_yellow%Full filename: %faint_on%%italics_on%%@UNQUOTE["%@FULL["%file%"]"]%italics_off%%faint_off%

                :reask
                rem title Delete? >nul
                set OVERRIDE_ASKYN_NOTITLE=1
                call askyn "₇Delete %lq%%ansi_color_bright_yellow%%@UNQUOTE["%file%"]%ansi_color_prompt%%rq% [%ansi_color_bright_green%E%ansi_color_prompt%=edit%EVEN_MORE_PROMPT_TEXT%]" no 0 E%EVEN_MORE_EXTRA_LETTERS% E:edit_it_instead%EVEN_MORE_EXTRA_EXPLANATIONS%
                iff not exist "%@UNQUOTE["%file%"]" then
                        call warning "₄File “%italics_on%%@UNQUOTE["%file%"]%italics_off%” doesn’t seem to exist... [anymore?]"
                        pause
                        unset /q answer
                        call askyn "Y=end del-maybe-after-review,N=proceed to next file" no 0
                        if "N" == "%ANSWER%" return
                        if "Y" == "%ANSWER%" goto /i END_OF_DMAR
                else

                        rem Multiple answers of ours rely on determing which file is the *audio file* associated witht he file we’re dealing with:
                                set THERE_IS_A_FILE_WE_CAN_PLAY_FOR_THIS_ONE=0
                                for %%tmpext in (%fileext_audio%) do (if exist "%@NAME[%file%].%tmpext%" set file_to_play=%@NAME[%file%].%tmpext% %+ set THERE_IS_A_FILE_WE_CAN_PLAY_FOR_THIS_ONE=1)
                                if "1" == "%DEBUG_DEL_MAYBE_AFTER_REVIEW%" pause "goat-DEL-MAYBE-AFTER-REVIEW-goat: file is now %file%, file_to_play is now %file_to_play%, THERE_IS_A_FILE_WE_CAN_PLAY_FOR_THIS_ONE=%THERE_IS_A_FILE_WE_CAN_PLAY_FOR_THIS_ONE%"


                        if  "E" == "%ANSWER%" (%EDITOR%                                                                "%@UNQUOTE["%file%"]" %+ goto /i reask)
                        if  "Y" == "%ANSWER%" (*del /a: /f /Ns                                                         "%@UNQUOTE["%file%"]"                 )
                        iff "I" == "%ANSWER%" then
                                set file_to_use=%file%
                                if "1" == "%THERE_IS_A_FILE_WE_CAN_PLAY_FOR_THIS_ONE%" SET file_to_use=%file_to_play%
                                gosub "%BAT%\get-lyrics-for-file.btm" rename_audio_file_as_instrumental "%@UNQUOTE["%file_to_use%"]"                 
                        endiff
                        iff "Q" == "%ANSWER%" then
                                call    enqueue-file-into-winamp-playlist.bat "%@UNQUOTE["%file_to_play%"]" 
                                goto /i reask
                        endiff
                        iff "P" == "%ANSWER%" then
                                iff "1" == "%THERE_IS_A_FILE_WE_CAN_PLAY_FOR_THIS_ONE%" then
                                        call preview-audio-file "%@UNQUOTE["%file_to_play%"]" 
                                else
                                        call        review-file "%@UNQUOTE["%file%"]" 
                                endiff
                                goto /i reask
                        endiff
                endiff
                
        return

:END_OF_DMAR
:END_OF_DEMAR
        setdos /x0
        echos %ansi_color_normal%%@randfg_soft[]
        title %dmar_title% >nul
        @echo ━━━━━━━━DEL-MAYBE-AFTER-REVIEW: END━━━━━━━━


