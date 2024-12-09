@Echo off
 on break cancel

rem Config:
        set our_filemask=*.srt;*.lrc

rem Only review a single file, if [what is hopefully] a filename is provided:
        if "%1" ne "" set our_filemask=%1


rem Validate environment:
        iff 1 ne %validated_review_subtitles% then
                call validate-in-path print-with-columns grep remove-blank-lines
                set  validated_review_subtitles=1
        endiff
        
rem Check if SRT files are actually here:
        iff not exist %our_filemask% then
                call warning "No %@upper[%@%@REReplace[;,/,%@REReplace[\*\.,,%our_filemask%]]] files present" silent
                goto :END
        endiff

rem Go through each one and review it:
        rem for less: set lc_all=en_US.UTF-8
        rem for less: set LANG=en_US.UTF-8
        rem for less: set LESSCHARSET=utf-8
        rem for less: set columns=%_columns
        
        for %tmpfile in (%our_filemask%) do (
                rem call debug tmpfile=%tmpfile%
                call divider 
                rem  bigecho %STAR% %@randfg_soft[]%underline_on%%@name[%tmpfile%]%underline_off%:
                call bigecho %STAR% %@randfg_soft[]%underline_on%%tmpfile%%underline_off%:
                (type "%@UNQUOTE[%tmpfile%]" |:u8 grep -vE "^[[:space:]]*$|^[0-9]+[[:space:]]*$|^[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{2,3} -->.*" )  |:u8 print-with-columns 
        )
        
        rem was a nice idea but no: |:u8 less -R




:END

