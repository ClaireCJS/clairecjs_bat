@Echo off
@loadbtm on
rem on break cancel
set onbreak=goto:END
setdos /x0




rem Config:
        set our_filemask=*.srt;*.lrc

rem Only review a single file, if [what is hopefully] a filename is provided:
        set replacement_text=
        setdos /x-5
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
                        set our_filemask=%*
                        set replacement_text=
                endiff
        endiff                
        setdos /x0

              goto :skip_check_for_filemask
                        :check_for_filemask 
                                setdos /x-5
                                iff not exist %our_filemask% then
                                        echo %ANSI_COLOR_WARNING_soft%%EMOJI_WARNING% No %@upper[%@%@REReplace[;,/,%@REReplace[\*\.,,%our_filemask%]]] files present %EMOJI_WARNING%%ANSI_COLOR_NORMAL%
                                        goto :END
                                else
                                        echo It exists...>nul
                                endiff
                                setdos   /x0
                        return                
              :skip_check_for_filemask

rem Validate environment:
        iff 1 ne %validated_review_subtitles% then
                call validate-in-path print-with-columns grep remove-blank-lines
                set  validated_review_subtitles=1
        endiff
        
rem Check if SRT files are actually here:

rem Go through each one and review it:
        rem for less: set lc_all=en_US.UTF-8
        rem for less: set LANG=en_US.UTF-8
        rem for less: set LESSCHARSET=utf-8
        rem for less: set columns=%_columns
        
        call set-tmp-file
        set tmp_file_1=%tmpfile%

        call set-tmp-file
        set tmp_file_2=%tmpfile%

        for %%File_To_Check  in (%our_filemask%) do if not exist "%File_To_Check%" (call fatal_error "File to review of %left_quote%%italics_on%%File_To_Check%%italics_on%%right_quote% does not exist")               
        for %%File_To_Review in (%our_filemask%) do gosub do_it "%@unquote[%File_To_Review%]"
        goto :do_it_end
        :do_it [tmpfile] 
                call divider 
                rem echo %blink_on%reviewing file %tmpfile%%blink_off% %warning% our_filemask=%our_filemask%
                setdos /x0
                rem title %@CHAR[55357]%@CHAR[56403] %@name[%tmpfile]
                title %emoji_palm_tree%%@name[%tmpfile]
                set ext=%@ext[%tmpfile%]
                iff "%replacement_text%" != "" then 
                        set our_msg=%replacement_text%
                else
                        set our_msg=%@name[%tmpfile%].%ext%
                endiff
                call bigecho "%STAR% %@randfg_soft[]%underline_on%%our_msg%%underline_off%:"
                setdos /x0
                rem (type "%@UNQUOTE[%tmpfile%]" |:u8 grep -vE "^[[:space:]]*$|^[0-9]+[[:space:]]*$|^[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{2,3} -->.*" )  |:u8 print-with-columns 
                setdos /x-5
                type "%@unquote[%tmpfile%]" >:u8"%tmp_file_1%"
                setdos /x0
                rem echo %ansi_color_debug%- DEBUG: %left_quote%%%ext%%%right_quote% is %left_quote%%ext%%right_quote% %warning%CP2309234%warning%
                if "%ext%" == "srt" (
                         grep -vE "^[[:space:]]*$|^[0-9]+[[:space:]]*$|^[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{2,3} -->.*" "%tmp_file_1%" >:u8"%tmp_file_2%"
                ) else (
                         (echo raw|(*copy /q /r "%tmp_file_1%" "%tmp_file_2%" >&nul))
                )
                echos %ansi_reset%
                rem call print-with-columns <%tmp_file_2 
                type %tmp_file_2 |:u8 call print-with-columns 
        return
        :do_it_end
        
        rem was a nice idea but no: |:u8 less -R




:END

 setdos /x0
