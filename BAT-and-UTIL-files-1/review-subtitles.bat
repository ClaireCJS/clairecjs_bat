@Echo off
 on break cancel

rem Config:
        set our_filemask=*.srt;*.lrc

rem Validate environment:
        call validate-in-path print-with-columns grep remove-blank-lines

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
        
        for %tmpfile in (%our_filemask%) do (call divider %+ call bigecho %@randfg_soft[]%@name[%tmpfile%]%@randfg_soft[]  %+  (type "%tmpfile%" |:u8 grep -vE "^[[:space:]]*$|^[0-9]+[[:space:]]*$|^[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{2,3} -->.*" )  |:u8 print-with-columns )
        
        rem was a nice idea but no: |:u8 less -R




:END

