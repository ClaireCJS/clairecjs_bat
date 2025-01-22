@Echo Off
 on break cancel

:DESCRIPTION: "cd" but with file-number-tracking, a tiny bit of file maintenance, and autoruns
:DESCRIPTION:
:DESCRIPTION: NOTE: Uses a bunch of fancy environment variables for stylization —— see set-colors.bat for those.
:DESCRIPTION:                                                                      (Not required, but nice to have.)
:DESCRIPTION:
:DESCRIPTION: NOTE: Uses, but does *NOT* require the %@WIDTH[] function in set-ansi (which itself requires the StripANSI plugin)

rem Validate Environemnt: Check if we have the width function, which requires the stripansi plugin:
        iff 1 ne %validated_cd_haveWidth then
                iff "%@function[width]" ne "" .and. "%@plugin[stripansi]" ne "" then 
                        set HAVE_WIDTH_FUNCTION=1
                else
                        set HAVE_WIDTH_FUNCTION=0
                endiff
                set validated_cd_haveWidth=1
        endiff

rem Capture parameters & keep track of the last folder we're in —— this is done automatically in other ways but we want our own:
        set CD_PARAMS=%*
        set CD_PARAM1=%1
        set CD_PARAM2=%2
        set CD_PARAM3=%3
        set CD_PARAM4=%4
        set CD_PARAM5=%5
        
rem Handle if the folder doesn't exist: 
        rem call debug "CD COMMAND IS cd %*"
        iff "-" ne "%CD_PARAM1%" .and. not isdir "%CD_PARAMS%" .and. not isdir "%CD_PARAM1%" .and. not isdir "%CD_PARAM2%" .and. not isdir %CD_PARAM1% .and. not isdir %CD_PARAM2% .and. not isdir %CD_PARAM3% .and. not isdir %CD_PARAM4% .and. not isdir %CD_PARAM5% then
                rem Blank line:
                        echo.
                        
                rem big error / top line error / simple errorr:
                        set MSG=%ANSI_COLOR_ERROR% %SKULL_AND_CROSSBONES%  “%@ansi_rgb[192,255,192]%@UNQUOTE[%CD_PARAMS%]%ansi_color_alarm%” doesn’t exist! %SKULL_AND_CROSSBONES%  %ANSI_COLOR_NORMAL%
                        
                        iff 1 eq %HAVE_WIDTH_FUNCTION% then
                                set top_width=%@width[%msg]
                        else                                
                                set top_width=%@len[%msg]
                        endiff                                
                        
                        iff defined BIG_TOP then                        
                                echo %BIG_TOP%%MSG%
                                echo %BIG_BOT%%MSG%%ansi_eol%
                                set top_width=%@eval[%top_width * 2]
                        else                        
                                echo %MSG%%ansi_eol%
                        endiff
                        
                        echos.

                rem small error / bottom line error / explained error:
                                set SECOND_LINE=%ANSI_COLOR_ERROR%  %no%%no%  %ansi_color_bright_yellow%Folder does not exist: “%italics_on%%blink_on%%@unquote[%CD_PARAMS%]%blink_off%%italics_off%” %NO%%NO%  %ANSI_COLOR_NORMAL%%ansi_color_yellow%%italics_on%%faint_on%

                                iff 1 eq %HAVE_WIDTH_FUNCTION% then
                                        set bottom_width=%@width[%second_line]
                                else                                
                                        set bottom_width=%@len[%second_line]
                                endiff                       
                                
                                set spaces=%@FLOOR[%@EVAL[(top_width - bottom_width) / 2]]
                                echo %@repeat[ ,%spaces%]%second_line

                                echo.
                
                rem But try anyway in case we're wrong: And make sure this next line is line #69 (nice): 
                *cd %*
                
                echos %BLINK_OFF%%ANSI_COLOR_NORMAL%``
                cancel
                goto :END
        endiff


rem Count the number of files the current folder as we leave it:
        set NUM_FILES_NOW_2=%@FILES[.,-d]
                                      set FILE_COUNT_LAST=%[FILE_COUNT_%[_CWD]_EXITED]
        if "%FILE_COUNT_LAST%" eq "" (set FILE_COUNT_LAST=%[FILE_COUNT_%[_CWD]_ENTERED]) %+ rem if no exit  value, get entered value
        if "%FILE_COUNT_LAST%" eq "" (set FILE_COUNT_LAST=%[FILE_COUNT_%[_CWD]]        ) %+ rem if no enter value, get generic value [this shouldn't happen and is just added as a foolproof mechanism]

rem Store what the last folder was:
        set FILE_COUNT_%[_CWD]_EXITED=%NUM_FILES_NOW_2%
        set LAST_FOLDER=%_CWD

rem Actually do our cd command —— Change into the folder:
        *cd %CD_PARAMS%


rem Count the files in the new folder as we enter it:
        set NUM_FILES_NOW=%@FILES[.,-d]
        set FILE_COUNT_%[_CWD]_ENTERED=%NUM_FILES_NOW%   %+ rem the new value of this variable  is the number of files there now
        rem How do we set the files that were in the folder prior? By looking at *both* FILE_COUNT_%_CWD_ENTERED & FILE_COUNT_%_CWD_EXITED
        rem NUM_FILES_THEN=%[FILE_COUNT_%[_CWD]_ENTERED] %+ rem the old value of this variable was the number of files in this folder LAST time we entered it
                                     set NUM_FILES_THEN=%[FILE_COUNT_%[_CWD]_EXITED]      %+ rem the old value of this variable was the number of files in this folder LAST time we entered it
        if "%NUM_FILES_THEN%" eq "" (set NUM_FILES_THEN=%[FILE_COUNT_%[_CWD]_ENTERED])
        set FILE_COUNT_%[_CWD]_ENTERED=%NUM_FILES_NOW%                                    %+ rem the new value of this variable  is the number of files there now
        set FILE_COUNT_%[_CWD]=%NUM_FILES_NOW%                                            %+ rem We also maintain a "current count of files" var which is the last value regardless of entering or existing


rem Set the window title to the folder name, while keeping track of the last couple titles:
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
        if %CD_PERCENT eq 1 (echo %ANSI_COLOR_LESS_IMPORTANT%%STAR2% %faint_on%# of files %faint_on%%italics_on%%VERB%%italics_off% %ansi_color_important_less%from%faint_off% %bold_on%%NUM_FILES_then_2%%bold_off% %faint_on%to%faint_off% %double_underline_on%%blink_on%%bold_on%%NUM_FILES_NOW_2%%bold_off%%blink_off%%double_underline_off% %faint_on%(%faint_off%%[PERCENT]`%`%faint_on%) %faint_on%since last check of %faint_off%%italics_on%%LAST_FOLDER%%italics_off%%faint_off%)
        if %CD_PERCENT eq 0 (echo %ANSI_COLOR_LESS_IMPORTANT%%STAR2% %faint_on%# of files %faint_on%%italics_on%%VERB%%italics_off% %ansi_color_important_less%from%faint_off% %bold_on%%NUM_FILES_then_2%%bold_off% %faint_on%to%faint_off% %double_underline_on%%blink_on%%bold_on%%NUM_FILES_NOW_2%%bold_off%%blink_off%%double_underline_off% %faint_on%since last check of %faint_off%%italics_on%%LAST_FOLDER%%italics_off%%faint_off%) %+ REM previous line copied over but with percent section removed to avoid divide by zero errors
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
        echo %ANSI_COLOR_LESS_IMPORTANT%%STAR2% %faint_on%# of files %faint_on%%italics_on%%VERB%%italics_off% %ansi_color_important_less%from%faint_off% %bold_on%%NUM_FILES_then%%bold_off% %faint_on%to%faint_off% %double_underline_on%%blink_on%%bold_on%%NUM_FILES_NOW%%bold_off%%blink_off%%double_underline_off% %faint_on%(%faint_off%%[PERCENT]%%%faint_on%) %faint_on%since last check in %faint_off%%italics_on%%[_cwd]%italics_off%%faint_off%%ANSI_RESET%%ANSI_EOL%
        :skip_saying_2



rem Stuff we don't normally do is coming up —— so color it a warning color 
        %COLOR_WARNING%

rem Rename extensions we don't ever want to ever exist:
            if exist *.jpg_large (ren /E *.jpg_large *.jpg >&nul)
            if exist *.jpg!d     (ren /E *.jpg!d     *.jpg >&nul)

rem Delete files we don't ever want to exist:
            if  exist  thumbs.db  (                     *del /z  thumbs.db ) %+ rem cruft: Windows 
            if  exist desktop.ini (                     *del /z desktop.ini) %+ rem cruft: Windows 
            if  exist       a.out (                     *del /z       a.out) %+ rem cruft: Unix
            if  exist       *.pkf (                     *del /z       *.pkf) %+ rem cruft: CoolEdit/Audition 
            if  exist       *.mta (sweep if exist *.mta *del /z       *.mta) %+ rem cruft: Samsung Allshare 
            iff exist clear then                                             %+ rem cruft: wget calls to WinAmp's wawi plugin leaves file named 'clear' that we've found repeatedly:
                    echos %ANSI_COLOR_WARNING% 'clear' file found %DASH% this should probably be deleted! %ANSI_COLOR_NORMAL%
                    echo %[ANSI_COLOR_MAGENTA]             %+   call divider 
                    echos %[ANSI_COLOR_YELLOW]%BLINK_ON%   %+   type  clear 
                    echos %ANSI_COLOR_MAGENTA%%BLINK_OFF   %+   call divider 
                    echos %ANSI_COLOR_BRIGHT_RED%%ANSI_BLINK_ON%%EMOJI_RED_QUESTION_MARK%
                    *del /p clear
            endiff                                 




rem Automatically run autorun.bat, or if one doesn't exist, one from the parent folder, and so forth:
        %COLOR_NORMAL%
        set AUTO_RUN_BAT=
        if exist ..\..\..\..\..\..\..\..\autorun.bat set AUTO_RUN_BAT=..\..\..\..\..\..\..\..\autorun.bat
        if exist    ..\..\..\..\..\..\..\autorun.bat set AUTO_RUN_BAT=   ..\..\..\..\..\..\..\autorun.bat
        if exist       ..\..\..\..\..\..\autorun.bat set AUTO_RUN_BAT=      ..\..\..\..\..\..\autorun.bat
        if exist          ..\..\..\..\..\autorun.bat set AUTO_RUN_BAT=         ..\..\..\..\..\autorun.bat
        if exist             ..\..\..\..\autorun.bat set AUTO_RUN_BAT=            ..\..\..\..\autorun.bat
        if exist                ..\..\..\autorun.bat set AUTO_RUN_BAT=               ..\..\..\autorun.bat
        if exist                   ..\..\autorun.bat set AUTO_RUN_BAT=                  ..\..\autorun.bat
        if exist                      ..\autorun.bat set AUTO_RUN_BAT=                     ..\autorun.bat
        if exist                         autorun.bat set AUTO_RUN_BAT=                        autorun.bat
        if "" ne "%AUTO_RUN_BAT" (call %AUTO_RUN_BAT%)
        


:END
%COLOR_NORMAL%

