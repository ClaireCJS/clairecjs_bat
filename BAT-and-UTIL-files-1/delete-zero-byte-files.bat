@loadbtm on
@echo DZBF BEGIN━━━━━━-━—-━━-–🐐🐐🐐
@echo off
@on break cancel

:USAGE: delete-zero-byte-files           - deletes all zero byte files
:USAGE: delete-zero-byte-files *.lrc     - deletes all zero byte files with the LRC extension




rem Get files to work on:
                       set FILES=*.*
        if "%1" != "" (set FILES=%1)

rem Get silence mode:
        set DZBF_SILENT=0
        if "%1" == "silent" .or. "%2" == "silent" .or. "%3" == "silent" (set DZBF_SILENT=1)

rem Loop through all files in the target directory
        for %%qqq in (%FILES%) do (gosub :processfile "%qqq")

rem All done!
        goto :Cleanup


rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                                goto :Next1
                                    :processfile [qqqparam]
                                            set qqq=%@UNQUOTE[%qqqparam]
                                            rem  checking %qqq filesize .. %@FILESIZE["%qqq"] eq 0
                                            iff %@FILESIZE["%qqq"] eq 0 .and. 1 ne %@Regex[__ [0-9]+kbps __,"%qqq%"] .and. 1 ne %@Regex[__ .*instrumental.* __,"%qqq%"] then
                                                    %COLOR_REMOVAL%
                                                    *del /a: /f /q "%qqq%" >&>nul
                                                    %COLOR_NORMAL%
                                                    iff "%DZBF_SILENT%" != "1" then
                                                        iff not exist "%qqq%" then
                                                                echo %ANSI_COLOR_IMPORTANT_LESS%* %ansi_COLOR_REMOVAL%Deleted zero-byte file: %faint_on%%qqq%%ansi_reset%
                                                        else    
                                                                call warning "Could not delete zero-byte file: '%italics_on%%qqq%%italics_off%'%ansi_reset%
                                                        endiff
                                                    endiff
                                            else
                                                     rem it's fine
                                            endiff 
                                            rem done with %qqq%
                                    return
                                :Next1
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
rem ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

:Cleanup
        if "1" != "%DZBF_SILENT%" call success "All zero-byte files have been deleted."

:END
        unset /q DZBF_SILENT
        @echo DZBF END━━━━━━-━—-━━-–🐐🐐🐐
