@Echo Off

rem Capture parameters & keep track of the last folder we're in —— this is done automatically in other ways but we want our own:
        set CD_PARAMS=%*
        set CD_PARAM1=%1
        set CD_PARAM2=%2
        set CD_PARAM3=%3
        set CD_PARAM4=%4
        set CD_PARAM5=%5


rem Does the folder exist?
        if "-" ne "%CD_PARAM1%" .and. not isdir %CD_PARAM1% .and. not isdir %CD_PARAM2% .and. not isdir %CD_PARAM3% .and. not isdir %CD_PARAM4% .and. not isdir %CD_PARAM5% (
            call error "Folder does not exist: %italics_on%%CD_PARAMS%%italics_off%"
            goto :END
        )

rem Change into the folder —— the actual thing we mean to do 😂 —— and count the files:
        set NUMFILES_NOW_2=%@FILES[.,-d]
                                      set FILE_COUNT_LAST=%[FILE_COUNT_%[_CWD]_EXITED]
        if "%FILE_COUNT_LAST%" eq "" (set FILE_COUNT_LAST=%[FILE_COUNT_%[_CWD]_ENTERED]) %+ rem if no exit  value, get entered value
        if "%FILE_COUNT_LAST%" eq "" (set FILE_COUNT_LAST=%[FILE_COUNT_%[_CWD]]        ) %+ rem if no enter value, get generic value [this shouldn't happen and is just added as a foolproof mechanism]
        set                   FILE_COUNT_%[_CWD]_EXITED=%NUMFILES_NOW_2%
        set LAST_FOLDER=%_CWD
        *cd %CD_PARAMS%
        set NUMFILES_NOW=%@FILES[.,-d]

        rem How do we set the files that were in the folder prior? By looking at *both* FILE_COUNT_%_CWD_ENTERED & FILE_COUNT_%_CWD_EXITED
        rem NUMFILES_THEN=%[FILE_COUNT_%[_CWD]_ENTERED] %+ rem the old value of this variable was the number of files in this folder LAST time we entered it
                                    set NUMFILES_THEN=%[FILE_COUNT_%[_CWD]_EXITED]  %+ rem the old value of this variable was the number of files in this folder LAST time we entered it
        if "%NUMFILES_THEN%" eq "" (set NUMFILES_THEN=%[FILE_COUNT_%[_CWD]_ENTERED])
        set FILE_COUNT_%[_CWD]_ENTERED=%NUMFILES_NOW%   %+ rem the new value of this variable  is the number of files there now
        set FILE_COUNT_%[_CWD]=%NUMFILES_NOW%           %+ rem We also maintain a "current count of files" var which is the last value regardless of entering or existing


rem Change the window title to the folder, while keeping track of the last couple titles:
        if "%CD_PARAMS%" ne "" (
            if defined LAST_TITLE (set LAST_TITLE_2=%LAST_TITLE%)
            set        LAST_TITLE=%_wintitle
            title %CD_PARAMS%
        )

rem If there were a different number of files now, than when we entered or existed this folder last time, let us know:
        set NUMFILES_THEN_2=%FILE_COUNT_LAST%
        rem 🔴Folder %LAST_FOLDER% had %NUMFILES_NOW_2% file. Last time we checked, it had %NUMFILES_THEN_2%
        rem  not defined       NUMFILES_NOW_2  (goto  :skip_saying)
        if   not defined       NUMFILES_THEN_2 (goto  :skip_saying)
        if %NUMFILES_NOW_2 eq %NUMFILES_THEN_2 (goto  :skip_saying)
        if %NUMFILES_NOW_2 gt %NUMFILES_THEN_2 (set VERB=%ansi_color_bright_green%increased)
        if %NUMFILES_NOW_2 lt %NUMFILES_THEN_2 (set VERB=%ansi_color_red%decreased)
        call less_important "%faint_on%# of files %faint_on%%italics_on%%VERB%%italics_off% %ansi_color_important_less%from%faint_off% %bold_on%%numfiles_then_2%%bold_off% %faint_on%to%faint_off% %double_underline_on%%blink_on%%bold_on%%NUMFILES_NOW_2%%bold_off%%blink_off%%double_underline_off% %faint_on%since last check of %faint_off%%italics_on%%LAST_FOLDER%%italics_off%%faint_off%"
        :skip_saying

rem If there were a different number of files when we entered our new folder than when we last exited our new folder, let us know:
        rem 💚Folder %_CWD has %NUMFILES_NOW% file. Last time it had %NUMFILES_THEN%
        rem not defined      NUMFILES_NOW  (goto  :skip_saying_2)
        if  not defined      NUMFILES_THEN (goto  :skip_saying_2)
        if %NUMFILES_NOW eq %NUMFILES_THEN (goto  :skip_saying_2)
        if %NUMFILES_NOW gt %NUMFILES_THEN (set VERB=%ansi_color_bright_green%increased)
        if %NUMFILES_NOW lt %NUMFILES_THEN (set VERB=%ansi_color_red%decreased)
        call less_important "%faint_on%# of files %faint_on%%italics_on%%VERB%%italics_off% %ansi_color_important_less%from%faint_off% %bold_on%%numfiles_then%%bold_off% %faint_on%to%faint_off% %double_underline_on%%blink_on%%bold_on%%NUMFILES_NOW%%bold_off%%blink_off%%double_underline_off% %faint_on%since last check in %faint_off%%italics_on%%[_cwd]%italics_off%%faint_off%"
        :skip_saying_2

rem Stuff we don't normally do is coming up —— so color it a warning color to some extent
        %COLOR_WARNING%

rem Rename extensions we don't ever want to exist:
            if exist *.jpg_large (ren /E *.jpg_large *.jpg >&nul)
            if exist *.jpg!d     (ren /E *.jpg!d     *.jpg >&nul)

rem Delete files we don't ever want to exist:
            if exist  thumbs.db  (                     *del /z  thumbs.db ) %+ rem ::::: cruft: Windows 
            if exist desktop.ini (                     *del /z desktop.ini) %+ rem ::::: cruft: Windows 
            if exist       a.out (                     *del /z       a.out) %+ rem ::::: cruft: Unix
            if exist       *.pkf (                     *del /z       *.pkf) %+ rem ::::: cruft: CoolEdit/Audition 
            if exist       *.mta (sweep if exist *.mta *del /z       *.mta) %+ rem ::::: cruft: Samsung Allshare 
            if exist   clear     (                                          %+ rem ::::: cruft: wget calls to WinAmp's wawi plugin
                    call warning "'clear' file found!%ANSI_COLOR_RED%" 
                    call divider 
                    type clear 
                    call divider 
                    *del /p clear
            )                                                


:END
%COLOR_NORMAL%
