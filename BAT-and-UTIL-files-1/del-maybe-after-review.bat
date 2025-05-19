@loadbtm on
rem @call bat-init
@Echo OFF
set last_title=%_title

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
                call validate-in-path review-file.bat review-files.bat print_with_columns.py print-with-columns grep remove-blank-lines echos preview-audio-file.bat
                call validate-environment-variables lq rq  ansi_color_prompt ansi_color_bright_yellow star ansi_color_yellow  ansi_color_normal faint_on italics_on faint_off italics_off
                call validate-is-function randfg_soft
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
        goto :END


        :do_file [file]
                call review-file -st  "%@UNQUOTE["%file%"]"
                echo %star% %ansi_color_yellow%Full filename: %faint_on%%italics_on%%@UNQUOTE["%@FULL["%file%"]"]%italics_off%%faint_off%

                :reask
                call askyn "Delete %lq%%ansi_color_bright_yellow%%@UNQUOTE["%file%"]%ansi_color_prompt%%rq% [%ansi_color_bright_green%E%ansi_color_prompt%=edit%EVEN_MORE_PROMPT_TEXT%]" yes 0 E%EVEN_MORE_EXTRA_LETTERS% E:edit_it_instead%EVEN_MORE_EXTRA_EXPLANATIONS%
                iff not exist "%@UNQUOTE["%file%"]" then
                        call warning "File “%@UNQUOTE["%file%"]” doesn’t seem to exist... [anymore?]"
                else
                        if "Y" == "%ANSWER%" (*del /a: /f /Ns  "%@UNQUOTE["%file%"]"               )
                        if "E" == "%ANSWER%" (%EDITOR%         "%@UNQUOTE["%file%"]" %+ goto :reask)
                        iff "P" == "%ANSWER%" then
                                set file_to_play=%@UNQUOTE["%file%"]                                                                                
                                if not defined FILEEXT_AUDIO set FILEEXT_AUDIO=mp3   wav   rm   voc   au   mid   stm   s3m   mod   vqf   ogg   mpc   wma   mp4   flac   snd   aac   opus   ac3   ra   dtshd   m4a   aif   cmf   rol
                                set DMAR_IS_AUDIO=0
                                for %%tmpext in (%fileext_audio%) do (if exist "%@NAME[%file%].%tmpext%" set file_to_play=%@NAME[%file%].%tmpext% %+ set DMAR_IS_AUDIO=1)
                                pause "file is now %file%, file_to_play is now %file_to_play%, DMAR_IS_AUDIO=%DMAR_IS_AUDIO%"

                                iff "1" == "%DMAR_IS_AUDIO%" then
                                        call preview-audio-file "%@UNQUOTE["%file_to_play%"]" 
                                else
                                        call        review-file "%@UNQUOTE["%file%"]" 
                                endiff
                                goto /i reask
                        endiff
                endiff
                
        return

:END
setdos /x0
echos %ansi_color_normal%%@randfg_soft[]
title %_CWP

