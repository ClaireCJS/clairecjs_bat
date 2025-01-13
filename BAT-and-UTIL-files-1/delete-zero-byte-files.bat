@echo off
 on break cancel

:USAGE: delete-zero-byte-files           - deletes all zero byte files
:USAGE: delete-zero-byte-files *.lrc     - deletes all zero byte files with the LRC extension


               set FILES=*.*
if "%1" != "" (set FILES=%1)

set DZBF_SILENT=0
if "%1" == "silent" .or. "%2" == "silent" .or. "%3" == "silent" (set DZBF_SILENT=1)

:: Loop through all files in the target directory
for %%qqq in (%FILES%) do (gosub :processfile "%qqq")

goto :Next1
                            :processfile [qqqparam]
                                    set qqq=%@UNQUOTE[%qqqparam]
                                    rem  checking %qqq filesize .. %@FILESIZE["%qqq"] eq 0
                                    iff %@FILESIZE["%qqq"] eq 0 then
                                            %COLOR_REMOVAL%
                                            *del /a: /f /q "%qqq%" >&>nul
                                            %COLOR_NORMAL%
                                            iff %DZBF_SILENT ne 1 then
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
:Cleanup

if %DZBF_SILENT eq 1 goto :silent

        call success "All zero-byte files have been deleted.")

:silent

:END
unset /q DZBF_SILENT

