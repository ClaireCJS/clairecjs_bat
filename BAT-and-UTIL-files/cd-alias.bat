@Echo Off

:DESCRIPTION: "cd" but with file-number-tracking and a tiny bit of file maintenance
:DESCRIPTION:
:DESCRIPTION: NOTE: Uses a bunch of fancy environment variables for stylization —— see set-colors.bat for those.
:DESCRIPTION:                                                                      (Not required, but nice to have.)


rem Capture parameters & keep track of the last folder we're in —— this is done automatically in other ways but we want our own:
        set CD_PARAMS=%*
        set CD_PARAM1=%1
        set CD_PARAM2=%2
        set CD_PARAM3=%3
        set CD_PARAM4=%4
        set CD_PARAM5=%5

rem Does the folder exist?
        rem call debug "CD COMMAND IS cd %*"
        if "-" ne "%CD_PARAM1%" .and. not isdir "%CD_PARAMS%" .and. not isdir "%CD_PARAM1%" .and. not isdir "%CD_PARAM2%" .and. not isdir %CD_PARAM1% .and. not isdir %CD_PARAM2% .and. not isdir %CD_PARAM3% .and. not isdir %CD_PARAM4% .and. not isdir %CD_PARAM5% (
            call error "Folder does not exist: %italics_on%%CD_PARAMS%%italics_off%"
            rem But try anyway in case we're wrong:
            *cd %*
            goto :END
        )

rem Change into the folder —— the actual thing we mean to do 😂 —— and count the files:
        set NUM_FILES_NOW_2=%@FILES[.,-d]

                                      set FILE_COUNT_LAST=%[FILE_COUNT_%[_CWD]_EXITED]
        if "%FILE_COUNT_LAST%" eq "" (set FILE_COUNT_LAST=%[FILE_COUNT_%[_CWD]_ENTERED]) %+ rem if no exit  value, get entered value
        if "%FILE_COUNT_LAST%" eq "" (set FILE_COUNT_LAST=%[FILE_COUNT_%[_CWD]]        ) %+ rem if no enter value, get generic value [this shouldn't happen and is just added as a foolproof mechanism]

        set FILE_COUNT_%[_CWD]_EXITED=%NUM_FILES_NOW_2%
        set LAST_FOLDER=%_CWD

        *cd %CD_PARAMS%

        set NUM_FILES_NOW=%@FILES[.,-d]
        set FILE_COUNT_%[_CWD]_ENTERED=%NUM_FILES_NOW%   %+ rem the new value of this variable  is the number of files there now

        rem How do we set the files that were in the folder prior? By looking at *both* FILE_COUNT_%_CWD_ENTERED & FILE_COUNT_%_CWD_EXITED
        rem NUM_FILES_THEN=%[FILE_COUNT_%[_CWD]_ENTERED] %+ rem the old value of this variable was the number of files in this folder LAST time we entered it
                                    set NUM_FILES_THEN=%[FILE_COUNT_%[_CWD]_EXITED]  %+ rem the old value of this variable was the number of files in this folder LAST time we entered it
        if "%NUM_FILES_THEN%" eq "" (set NUM_FILES_THEN=%[FILE_COUNT_%[_CWD]_ENTERED])
        set FILE_COUNT_%[_CWD]_ENTERED=%NUM_FILES_NOW%   %+ rem the new value of this variable  is the number of files there now
        set FILE_COUNT_%[_CWD]=%NUM_FILES_NOW%           %+ rem We also maintain a "current count of files" var which is the last value regardless of entering or existing


rem Change the window title to the folder, while keeping track of the last couple titles:
        if "%CD_PARAMS%" ne "" (
            if defined LAST_TITLE (set LAST_TITLE_2=%LAST_TITLE%)
            set        LAST_TITLE=%_wintitle
            title %CD_PARAMS%
        )

rem If there were a different number of files now than when we last entered this folder, let us know either/both:
        set NUM_FILES_THEN_2=%FILE_COUNT_LAST%
        rem 🔴Folder %LAST_FOLDER% had %NUM_FILES_NOW_2% file. Last time we checked, it had %NUM_FILES_THEN_2%
        rem  not defined        NUM_FILES_NOW_2  (goto  :skip_saying)
        if   not defined        NUM_FILES_THEN_2 (goto  :skip_saying)
        if %NUM_FILES_NOW_2 eq %NUM_FILES_THEN_2 (goto  :skip_saying)
        if %NUM_FILES_NOW_2 gt %NUM_FILES_THEN_2 (set CHANGE=increased %+ set VERB=%ansi_color_bright_green%increased)
        if %NUM_FILES_NOW_2 lt %NUM_FILES_THEN_2 (set CHANGE=decreased %+ set VERB=%ansi_color_red%decreased)
        if         0        eq %NUM_FILES_THEN_2 (set CD_PERCENT=0 %+ goto :NoPercent)
        if         0        ne %NUM_FILES_THEN_2 (set CD_PERCENT=1)
        set PERCENT=%@FLOOR[100-%@EVAL[100*(%NUM_FILES_NOW_2 / %NUM_FILES_THEN_2)]]
        set PERCENT=%@EVAL[-1 * %PERCENT]
        :NoPercent
        if %CD_PERCENT eq 1 (call less_important "%faint_on%# of files %faint_on%%italics_on%%VERB%%italics_off% %ansi_color_important_less%from%faint_off% %bold_on%%NUM_FILES_then_2%%bold_off% %faint_on%to%faint_off% %double_underline_on%%blink_on%%bold_on%%NUM_FILES_NOW_2%%bold_off%%blink_off%%double_underline_off% %faint_on%(%faint_off%%[PERCENT]{PERCENT}%faint_on%) %faint_on%since last check of %faint_off%%italics_on%%LAST_FOLDER%%italics_off%%faint_off%")
        if %CD_PERCENT eq 0 (call less_important "%faint_on%# of files %faint_on%%italics_on%%VERB%%italics_off% %ansi_color_important_less%from%faint_off% %bold_on%%NUM_FILES_then_2%%bold_off% %faint_on%to%faint_off% %double_underline_on%%blink_on%%bold_on%%NUM_FILES_NOW_2%%bold_off%%blink_off%%double_underline_off% %faint_on%since last check of %faint_off%%italics_on%%LAST_FOLDER%%italics_off%%faint_off%") %+ REM previous line copied over but with percent section removed to avoid divide by zero errors
        :skip_saying

rem If there were a different number of files when we entered our new folder than when we last exited our new folder, let us know:
        rem 💚Folder %_CWD has %NUM_FILES_NOW% file. Last time it had %NUM_FILES_THEN%
        rem not defined      NUM_FILES_NOW   (goto  :skip_saying_2)
        if  not defined      NUM_FILES_THEN  (goto  :skip_saying_2)
        if %NUM_FILES_NOW eq %NUM_FILES_THEN (goto  :skip_saying_2)
        if %NUM_FILES_NOW gt %NUM_FILES_THEN (set CHANGE=increased %+ set VERB=%ansi_color_bright_green%increased)
        if %NUM_FILES_NOW lt %NUM_FILES_THEN (set CHANGE=decreased %+ set VERB=%ansi_color_red%decreased)
        set PERCENT=%@FLOOR[100-%@EVAL[100*(%NUM_FILES_NOW / %NUM_FILES_THEN)]]
        set PERCENT=%@EVAL[-1 * %PERCENT]
        echo %STAR% %ANSI_COLOR_LESS_IMPORTANT%%faint_on%# of files %faint_on%%italics_on%%VERB%%italics_off% %ansi_color_important_less%from%faint_off% %bold_on%%NUM_FILES_then%%bold_off% %faint_on%to%faint_off% %double_underline_on%%blink_on%%bold_on%%NUM_FILES_NOW%%bold_off%%blink_off%%double_underline_off% %faint_on%(%faint_off%%[PERCENT]%%%faint_on%) %faint_on%since last check in %faint_off%%italics_on%%[_cwd]%italics_off%%faint_off%%ANSI_RESET%%ANSI_EOL%
        :skip_saying_2

rem Stuff we don't normally do is coming up —— so color it a warning color to some extent
        %COLOR_WARNING%

rem Rename extensions we don't ever want to exist:
            if exist *.jpg_large (ren /E *.jpg_large *.jpg >&nul)
            if exist *.jpg!d     (ren /E *.jpg!d     *.jpg >&nul)

rem Delete files we don't ever want to exist:
            if exist  thumbs.db  (                     *del /z  thumbs.db ) %+ rem cruft: Windows 
            if exist desktop.ini (                     *del /z desktop.ini) %+ rem cruft: Windows 
            if exist       a.out (                     *del /z       a.out) %+ rem cruft: Unix
            if exist       *.pkf (                     *del /z       *.pkf) %+ rem cruft: CoolEdit/Audition 
            if exist       *.mta (sweep if exist *.mta *del /z       *.mta) %+ rem cruft: Samsung Allshare 
            rem cruft: wget calls to WinAmp's wawi plugin leaves file named 'clear' that we've found repeatedly:
            if exist   clear     (                                          
                    echos %ANSI_COLOR_WARNING% 'clear' file found %DASH% this should probably be deleted! %ANSI_COLOR_NORMAL%
                    echo  %ANSI_COLOR_MAGENTA%             %+   call divider 
                    echos %[ANSI_COLOR_YELLOW]%BLINK_ON%   %+   type  clear 
                    echos %ANSI_COLOR_MAGENTA%%BLINK_OFF   %+   call divider 
                    echos %ANSI_COLOR_BRIGHT_RED%%ANSI_BLINK_ON%%EMOJI_RED_QUESTION_MARK%
                    *del /p clear
            )                                                


:END
%COLOR_NORMAL%
