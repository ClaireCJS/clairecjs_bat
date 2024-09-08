@echo off


call validate-environment-variables LOCALAPPDATA TEMP TMPDIR 
call validate-in-path important.bat

set FREE_C_BEFORE=%@DISKFREE[c]

call less_important "Freeing up harddrive space..."


REM If you use a *.* filemask you need to also call CreateIfGone because IT WILL REMOVE THE FOLDER TOO if you use *.*

gosub DelIfExists "%LOCALAPPDATA%\Binary Fortress Software\DisplayFusion\CrashDumps\*.dmp"
gosub DelIfExists  %LOCALAPPDATA%\Temp\DiagOutputDir\RdClientAutoTrace\*.etl
gosub DelIfExists  %TEMP%\*.*
gosub CreateIfGone %TEMP%
gosub DelIfExists  %TMPDIR%\*.*
gosub CreateIfGone %TMPDIR%
gosub DelIfExists  c:\recycled\*.*
gosub CreateIfGone c:\recycled



set FREE_C_AFTER=%@DISKFREE[c]
set SPACE_SAVED_MEGS=%@FORMATN[01.0,%@EVAL[(%FREE_C_AFTER - %FREE_C_BEFORE)/1000000]]
set SPACE_SAVED_GIGS=%@FORMATN[01.0,%@EVAL[(%FREE_C_AFTER - %FREE_C_BEFORE)/1000000000]]
set SPACE_SAVED_MEGS_PRETTY=%@COMMA[%SPACE_SAVED_MEGS]
set SPACE_SAVED_GIGS_PRETTY=%@COMMA[%SPACE_SAVED_GIGS]
echos     `` %+ call less_important.bat "Saved %bold%%SPACE_SAVED_MEGS_PRETTY%%bold_off% megs"
echos     `` %+ call less_important.bat "Saved %bold%%SPACE_SAVED_GIGS_PRETTY%%bold_off% gigs"
set FREE_GIGABYTES=%@FORMATN[1.1,%@EVAL[%@DISKFREE[c]/1000000000]]
set FREE_TERABYTES=%@FORMATN[1.2,%@EVAL[%@DISKFREE[c]/1000000000000]]
echos     `` %+ call less_important "%ANSI_COLOR_IMPORTANT%Free space now: %FREE_TERABYTES%%blink_on%T%blink_off% (%FREE_GIGABYTES%%blink_on%G%blink_off%)"


goto :END
    :DelIfExists [files_param]
        %COLOR_REMOVAL%
        set files="%@UNQUOTE[%files_param]"
        if not exist %files% return
        if     exist %files% (*del /e /s /a: /f /k /L /X /Y /Z %files%) >nul
    return
    :CreateIfGone [dir_param]
        %COLOR_SUCCESS%
        set dir="%@UNQUOTE[%dir_param]"
        if not isdir %dir% (mkdir /s %dir%)
        if not isdir %dir% (call error.bat "There's still a problem when Creating %dir%!")
    return
:END
%COLOR_NORMAL%
