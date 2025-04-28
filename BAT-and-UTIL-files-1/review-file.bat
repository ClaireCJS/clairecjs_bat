@loadbtm on
@Echo off
rem on break cancel
set onbreak=goto:END
setdos /x0

rem Usage:
        iff "%1" == "" then
                echo USAGE: review_files -options_to_pass_to_print-with-columns `<`file`>` `<`file2`>` `<`file3`>` 
                echo.
                echo EXAMPLE: review-files a.txt
                echo EXAMPLE: review-files a.txt b.txt c.txt
                echo EXAMPLE: review-files *.txt
                echo EXAMPLE: review-files *
                echo EXAMPLE: review-files -wh    *.txt ——— passes “-wh”          on to print-with-columns
                echo EXAMPLE: review-files -wh -1 *.txt ——— passes “-wh” and “-1” on to print-with-columns
                echo EXAMPLE: review-files -wh -1 *.txt ——— passes “-wh” and “-1” on to print-with-columns
                echo.
                echo. SPECIAL: the “-st”  action can be stacked with “-wh”, even though print-with-columns doesn’t work like that
                echo. SPECIAL: the “-stU” action causes “-st” stripe to be an “upper stripe” before divider
                goto /i END
endiff

rem Config:
        set our_filemask=*.srt;*.lrc

rem First, process any arguments that start with “-”:
        unset /q PWC_OPTIONS
        set STRIPE=0
        set STRIPEU=0
        :check_next_arg_for_pwd_opts
        set  left1=%@UNQUOTE[%@LEFT[2,"%1"]]
        iff "%left1%" == "-" then
                iff "%1" == "-st" .or. "%1" == "--stripe" then
                        set STRIPE=1
                elseiff "%1" == "-stU" .or. "%1" == "--stripeU" then
                        set STRIPEU=1
                else
                        rem echo * Adding PWC_OPTION of “%1”
                        set PWC_OPTIONS=%PWC_OPTIONS% %1
                endiff
                shift
                goto /i check_next_arg_for_pwd_opts
        endiff           
        rem echo %%1 is %1 , 2=%2, 3=%3, 4=%4 %+ pause


rem Only review a single file, if [what is hopefully] a filename is provided:
        set replacement_text=
        *setdos /x-5
        iff "%@UNQUOTE[%1]" != "" .and. "%2" == "" then        
                set our_filemask=%1
                set replacement_text=
                rem echo Tracking 1>nul
                gosub check_for_filemask
        endiff              
        echo Checkpoint alpha ----------━━━━━━━━━━━━━━━━━━━━━━━━━━━>nul
        iff "%@UNQUOTE[%2]" != "" then
                iff not exist "%@unquote[%2]" then 
                        set our_filemask=%1
                        set replacement_text=%@UNQUOTE[%2]
                        rem echo Tracking 2>nul
                        gosub check_for_filemask 
                else
                        set our_filemask=%1$
                        set replacement_text=
                endiff
        endiff                
        setdos /x0

              goto :skip_check_for_filemask
                        :check_for_filemask 
                                *setdos /x-5
                                iff not exist %our_filemask% then
                                        echo %ANSI_COLOR_WARNING_soft%%EMOJI_WARNING% No %@upper[%@%@REReplace[;,/,%@REReplace[\*\.,,%our_filemask%]]] files present %EMOJI_WARNING%%ANSI_COLOR_NORMAL%
                                        goto /i END
                                else
                                        echo It exists...>nul
                                endiff
                                *setdos   /x0
                        return                
              :skip_check_for_filemask

rem Validate environment:
        iff "4" != "%validated_review_subtitles%" then
                call validate-in-path print-with-columns grep remove-blank-lines warning preview-audio-file preview-video-file preview-image-file print-with-columns print_with_columns.py
                call validate-environment-variables ansi_color_bright_red ansi_color_warning_soft emoji_warning ansi_color_normal italics_on italics_off left_quote right_quote 
                if not defined filemask_video call validate-environment-variables filemask_video skip_validation_existence
                if not defined filemask_audio call validate-environment-variables filemask_audio skip_alidation_existence
                if not defined filemask_audio call validate-environment-variables filemask_image skip_validation_existence
                set  validated_review_subtitles=4
        endiff
        
rem Check if SRT files are actually here:

rem Go through each one and review it:
        rem for less: set lc_all=en_US.UTF-8
        rem for less: set LANG=en_US.UTF-8
        rem for less: set LESSCHARSET=utf-8
        rem for less: set columns=%_columns

        if defined tmp_file_1 goto :defined_1        
        call set-tmp-file
        set tmp_file_1=%tmpfile%
        rem gosub debug "tmp_file_1==“%tmp_file_1%”"
        :defined_1

        if defined tmp_file_2 goto :defined_2
        call set-tmp-file
        set tmp_file_2=%tmpfile%
        rem gosub debug "tmp_file_2==“%tmp_file_2%”"
        :defined_2

        for %%File_To_Check  in (%our_filemask%) do if not exist "%File_To_Check%" (call fatal_error "File to review of %left_quote%%italics_on%%File_To_Check%%italics_on%%right_quote% does not exist")               
        for %%File_To_Review in (%our_filemask%) do gosub do_it "%@unquote[%File_To_Review%]"
        goto :do_it_end
        :do_it [tmpfile] 
                if not exist "%@UNQUOTE["%tmpfile%"]" return

                rem echo %blink_on%reviewing file %tmpfile%%blink_off% %warning% our_filemask=%our_filemask%
                setdos /x0


                rem What if we call this with a file that isn’t text?
                        set display_text=1

                        iff defined filemask_video then
                                iff "%@RegEx[\.%@EXT["%tmpfile%"],%filemask_video%]" == "1" then
                                        call warning "File to review of %left_quote%%italics_on%%tmpfile%%italics_on%%right_quote% %ansi_color_bright_red%is a video file" 
                                        call askyn "Play it" no 30 
                                        if "%answer%" == "Y" call preview-video-file "%@UNQUOTE["%tmpfile%"]" 
                                        set display_text=0
                                endiff
                        endiff

                        iff defined filemask_audio then
                                iff "%@RegEx[\.%@EXT["%tmpfile%"],%filemask_audio%]" == "1" then
                                        call warning "File to review of %left_quote%%italics_on%%tmpfile%%italics_on%%right_quote% %ansi_color_bright_red%is an audio file" 
                                        call askyn "Play it" no 30 
                                        if "%answer%" == "Y" call preview-audio-file "%@UNQUOTE["%tmpfile%"]" 
                                        set display_text=0
                                endiff
                        endiff

                        iff defined filemask_image then
                                iff "%@RegEx[\.%@EXT["%tmpfile%"],%filemask_image%]" == "1" then
                                        call warning "File to review of %left_quote%%italics_on%%tmpfile%%italics_on%%right_quote% %ansi_color_bright_red%is an image file" 
                                        call askyn "View it" no 30 
                                        if "%answer%" == "Y" call preview-image-file "%@UNQUOTE["%tmpfile%"]" 
                                        set display_text=0
                                endiff
                        endiff


                        if "1" == "%display_text%" goto :continue_on_to_display_text
                                call divider
                                return
                        :continue_on_to_display_text
                
                             


                rem title %@CHAR[55357]%@CHAR[56403] %@name[%tmpfile]
                title %emoji_palm_tree%%@name[%tmpfile]
                set ext=%@ext[%tmpfile%]
                iff "%replacement_text%" != "" then 
                        set our_msg=%replacement_text%
                else
                        set our_msg=%@name[%tmpfile%].%ext%
                endiff
                setdos /x0
                rem (type "%@UNQUOTE[%tmpfile%]" |:u8 grep -vE "^[[:space:]]*$|^[0-9]+[[:space:]]*$|^[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{2,3} -->.*" )  |:u8 print-with-columns 
                *setdos /x-5
                type "%@unquote[%tmpfile%]" >:u8"%tmp_file_1%"
                setdos /x0
                rem echo %ansi_color_debug%- DEBUG: %left_quote%%%ext%%%right_quote% is %left_quote%%ext%%right_quote% %warning%CP2309234%warning%
                if "%ext%" == "srt" (
                         grep -vE "^[[:space:]]*$|^[0-9]+[[:space:]]*$|^[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{2,3} -->.*" "%tmp_file_1%" >:u8"%tmp_file_2%"
                         grep -vE "^#" "%tmp_file_2%" >:u8"%tmp_file_1%"
                        *copy /z /q "%tmp_file_1%" "%tmp_file_2%"
                ) else (
                         (echo raw|(*copy /q /r "%tmp_file_1%" "%tmp_file_2%" >&nul))
                )
                echos %ansi_reset%
                if "1" == "%STRIPEU%" (type %tmp_file_2 |:u8 call print-with-columns -st)
                gosub "%bat%\get-lyrics-for-file.btm" divider
                call bigecho "%STAR% %@randfg_soft[]%underline_on%%our_msg%%underline_off%:"
                rem call print-with-columns <%tmp_file_2 
                                      type %tmp_file_2 |:u8 call print-with-columns %PWC_OPTIONS%
                iff "1" == "%STRIPE%" then
                        gosub "%bat%\get-lyrics-for-file.btm" divider
                        type %tmp_file_2 |:u8 call print-with-columns -st
                endiff
        return
        :do_it_end
        
        rem was a nice idea but no: |:u8 less -R




:END

 setdos /x0

