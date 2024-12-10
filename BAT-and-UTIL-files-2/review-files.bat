@Echo off
rem on break cancel
set onbreak=goto:END



:DESCRIPTION: This is not intended as a general file reviewer:
:DESCRIPTION:           It does things. 
:DESCRIPTION:           It removes lines from SRT files so that you are reviewing ONLY the subtitles.
:DESCRIPTION:           This could cause unintended results when used for general file reviewing.



rem Config:
        set our_filemask=*.srt;*.lrc

rem Only review a single file, if [what is hopefully] a filename is provided:
        set replacement_text=
        setdos /x-5
        if "%1" ne "" set our_filemask=%1
        if "%2" ne "" set replacement_text=%2
        setdos /x0


rem Validate environment:
        iff 1 ne %validated_review_subtitles% then
                call validate-in-path print-with-columns grep remove-blank-lines
                set  validated_review_subtitles=1
        endiff
        
rem Check if SRT files are actually here:
        setdos /x-5
        iff not exist %our_filemask% then
                echo %ANSI_COLOR_WARNING_soft%%EMOJI_WARNING% No %@upper[%@%@REReplace[;,/,%@REReplace[\*\.,,%our_filemask%]]] files present %EMOJI_WARNING%%ANSI_COLOR_NORMAL%
                setdos /x0
                goto :END
        endiff
        setdos /x0

rem Go through each one and review it:
        rem for less: set lc_all=en_US.UTF-8
        rem for less: set LANG=en_US.UTF-8
        rem for less: set LESSCHARSET=utf-8
        rem for less: set columns=%_columns
        
        call set-tmp-file
        set tmp_file_1=%tmpfile%

        call set-tmp-file
        set tmp_file_2=%tmpfile%
               
        for %%tmpfileouter in (%our_filemask%) do gosub do_it "%@unquote[%tmpfileouter%]"
        goto :do_it_end
        :do_it [tmpfile] 
                call divider 
                setdos /x0
                rem title %@CHAR[55357]%@CHAR[56403] %@name[%tmpfile]
                title %emoji_palm_tree%%@name[%tmpfile]
                iff "%replacement_text%" ne "" then 
                        set our_msg=%replacement_text%
                else
                        set our_msg=%@name[%tmpfile%]
                endiff
                call bigecho "%STAR% %@randfg_soft[]%underline_on%%our_msg%%underline_off%:"
                setdos /x0
                rem (type "%@UNQUOTE[%tmpfile%]" |:u8 grep -vE "^[[:space:]]*$|^[0-9]+[[:space:]]*$|^[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{2,3} -->.*" )  |:u8 print-with-columns 
                setdos /x-5
                type "%@unquote[%tmpfile%]" >:u8"%tmp_file_1%"
                setdos /x0
                grep -vE "^[[:space:]]*$|^[0-9]+[[:space:]]*$|^[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{2,3} -->.*" "%tmp_file_1%" >:u8"%tmp_file_2%"
                echos %ansi_reset%
                call print-with-columns <%tmp_file_2 
        return
        :do_it_end
        
        rem was a nice idea but no: |:u8 less -R




:END

 setdos /x0
