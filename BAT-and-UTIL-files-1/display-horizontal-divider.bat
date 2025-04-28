@rem @if %_columns eq %LAST_NUM_COLUMNS .and. defined last_divider .and. "%last_divider_cmd_tail%" == "%*" (echos %last_divider% %+ goto :The_Very_END) %+ rem Quick exit
@Echo OFF
@on break cancel


setdos /x-5
rem setdos /c^
setdos /c%default_command_separator_character%
setdos /x0
set last_divider_cmd_tail=%*

rem QUICK VERSION:        :divider []
rem QUICK VERSION:                *type %bat%\dividers\rainbow-%@EVAL[%_columns - 1].txt
rem QUICK VERSION:        return



rem :USAGE: "Divider"      to draw a horizontal divider using the default character repeated
rem :USAGE: "Divider newline"        ^^^^ same as above, but with a newline echo’ed afterward
rem :USAGE: "Divider 50 nonewline"   ^^^^ [DEPRECATED USAGE, MAY NOT WORK] same as above, but leave us dangling right at the last drawn character; no newline or moving back to column 0 [DEPRECATED USAGE, MAY NOT WORK]
rem :USAGE:
rem :USAGE:
rem :USAGE: .... Everything else below is likely broken....
rem :USAGE:
rem :USAGE:
rem :USAGE: "Divider 50"   ^^^^ same as above, but only 50 columns wide
rem :USAGE: "Divider HII!" to draw a horizontal divider using the string  "HII!"    repeated 
rem :USAGE: "Divider 😂"   to draw a horizontal divider using the laugh-emoji (😂)  repeated
rem :USAGE: "Divider -"    to draw a horizontal divider using the   '-'   character repeated
rem :USAGE: "Divider - 50"             to draw a horizontal divider with indication of 50% progress via decorating the divider —— cannot choose characters for this one so "-" option is ignored
rem :USAGE: "Divider - 50 rand_middle" to draw a horizontal divider with indication of 50% progress via decorating the divider where it's default color for the left, random color for the right
rem :USAGE: "Divider - 50 reverse" ^^^^ same as above, but for decorating our progress, using reverse  text
rem :USAGE: "Divider - 50 blink"   ^^^^ same as above, but for decorating our progress, using blinking text
rem :USAGE: "Divider - 50 randbg"  ^^^^ same as above, but for decorating our progress, applying a subtle random background color
rem :USAGE: "Divider - 50 faint"   ^^^^ same as above, but for decorating our progress, using faint    text —— looks good
rem :USAGE: "Divider - 50 bold"    ^^^^ same as above, but for decorating our progress, using bold     text —— NOT very visible 😡
rem :USAGE: OPTION:        Add "big" as a 2nd parameter to use double-height text

rem CONFIGURATION:
        echos %ANSI_INVISIBLE_CURSOR%
        setdos /x-6 %+ rem turn off file redirection so we can use < and >
        set DEFAULT_DIVIDER==
        rem                 ^ our default divider is '=', the equal symbol


rem quick: type %bat%\dividers\rainbow-%@EVAL[%_columns - 1].txt

rem Did we pass “newline” as an option?
        set DHD_NEWLINE=0
        if "%1" == "newline" (set DHD_NEWLINE=1 %+ shift)


rem After this script was developed, pre-rendered horizontal dividers were created [for use with top-message.bat]
rem As of 2024/10/18, we now try to use the pre-rendered dividers before drawing our own. It is ***MUCH*** faster.
        set WIDTH_TO_USE=%@EVAL[%_columns - 1]
        if "" != "%1" .and. %1 lt 999999 set WIDTH_TO_USE=%1
        set RAINBOW_DIVIDER_FILE=%bat%\dividers\rainbow-%WIDTH_TO_USE%.txt
        iff exist %RAINBOW_DIVIDER_FILE% then
                rem Validate the environment, but only once:
                        iff 1 ne %validated_divider_env then
                                if ""  eq "%@FUNCTION[ansi_move_to_col]" (function ANSI_MOVE_TO_COL=`%@CHAR[27][%1G`)
                                if not defined NEWLINE                   (set NEWLINE=%@char[12]%@char[13])
                                set validated_divider_env=1
                        endiff

                rem First, move to column 0... Yes, this means we will overwrite things. This is by design.
                rem TODO: We could look at where we are with the %_column variable, and if it’s more than 1, go to the next line... that might be better!
                        echos %@ANSI_MOVE_TO_COL[1]%ANSI_ERASE_TO_EOL%
                        iff "%2" == "lmc" .and. defined LOCKED_MESSAGE_COLOR then 
                                color cyan on blue
                                echos %LOCKED_MESSAGE_COLOR%%ANSI_ERASE_TO_EOL%
                        endiff

                rem Type the file out, but only if the # of columns is different from last time:
                rem old: 
                        rem type %RAINBOW_DIVIDER_FILE%
                rem new:
                        iff %_columns ne %LAST_NUM_COLUMNS then
                               set LAST_DIVIDER=%@execstr[type %RAINBOW_DIVIDER_FILE%]
                               echos %last_divider%
                               set LAST_NUM_COLUMNS=%_columns
                        else
                               echos %last_divider%
                        endiff

                rem   Okay this is weird. I keep getting "stuck" because the generated 
                rem   dividers don't have newlines at the end! So let's force one:
                        if "%1" ne "NoNewline" .and. "%2" ne "NoNewline" .and. "%3" ne "NoNewline" .and. "%4" ne "NoNewline" .and. "%5" ne "NoNewline"  .and. "%6" ne "NoNewline" (echos %NEWLINE%%@ANSI_MOVE_TO_COL[1])
                goto /i Done
        endiff






rem Respond to parameters [if any]:
        if "%1" ne "NoNewLine" set DIVIDER_PARAM1=%1
        if defined USE_THIS_DIVIDER (
            set DIVIDER_PARAM1=%USE_THIS_DIVIDER%
            unset /q USE_THIS_DIVIDER
        )
        unset /q HZ_PCT
        unset /q HZ_DECO_TYPE
        if "%2" ne "" (
            set HZ_PCT=%2
            if "%3" ne "" (set HZ_DECO_TYPE=%3)
        )
                                                                       set DIVIDER=%DEFAULT_DIVIDER%
        if "%DIVIDER_PARAM1%" ne "" .and. "%DIVIDER_PARAM1%" ne "big" (set DIVIDER=%@UNQUOTE[%DIVIDER_PARAM1%])
                                                           set BIG=0
        if "%2" eq "big" .or. "%DIVIDER_PARAM1%" eq "big" (set BIG=1)





rem Our divider could be any length, and our screen could have any number of columns,
rem so we must determine how many times we must repeat our divider to fill the line,
rem all while considering that double-height lines use 2 columns per character:
                       set SCREEN_COLUMNS=%_COLUMNS
        if "%1" ne "" (set SCREEN_COLUMNS=%1)        
        if %BIG eq  1 (set SCREEN_COLUMNS=%@EVAL[%SCREEN_COLUMNS / 2])
        set DIVIDER_LENGTH=%@LEN[%DIVIDER]
        rem echo sc=%screen_columns% divid_len=%divider_length% divider=“%divider%”
        set NUM_REPEATS=%@EVAL[%SCREEN_COLUMNS / %DIVIDER_LENGTH]




rem Actually write out the divider, which is easy for normal height text:
        if %BIG eq 1 (goto :BIG)
        rem old: repeat %NUM_REPEATS% echos %DIVIDER% 
        if defined HZ_PCT goto :HZ_PCT_defined

        :HZ_PCT_defined
            repeat %NUM_REPEATS% echos %DIVIDER% 
            rem TODO speed this up^^^^^^^^
            goto :HZ_PCT_stuff_done

        :HZ_PCT_NOT_defined
            rem Default decorator:
                    set DECORATOR_BAR_END=%FAINT_ON%
                    set DECORATOR_BAR_BEG=%FAINT_OFF   
                            rem Command-line override decorator:
                                    if "%HZ_DECO_TYPE%" eq "bold" (
                                        set DECORATOR_BAR_BEG=%BOLD_ON%   
                                        set DECORATOR_BAR_END=%BOLD_OFF   
                                    )
                                    if "%HZ_DECO_TYPE%" eq "faint" (
                                        set DECORATOR_BAR_BEG=%FAINT_ON%   
                                        set DECORATOR_BAR_END=%FAINT_OFF   
                                    )
                                    if "%HZ_DECO_TYPE%" eq "blink" (
                                        set DECORATOR_BAR_BEG=%BLINK_ON%   
                                        set DECORATOR_BAR_END=%BLINK_OFF   
                                    )
                                    if "%HZ_DECO_TYPE%" eq "reverse" (
                                        set DECORATOR_BAR_BEG=%REVERSE_ON%   
                                        set DECORATOR_BAR_END=%REVERSE_OFF   
                                    )
                                    if "%HZ_DECO_TYPE%" eq "randbg" (
                                        set DECORATOR_BAR_BEG=%@ANSI_RANDBG_SOFT[]
                                        set DECORATOR_BAR_END=%@ANSI_BG[0,0,0]
                                    )
            set DIVIDER_LEFT==
            set DIVIDER_RIGHT=-      
            set  NUM_REPEATS=%@EVAL[%NUM_REPEATS - 1]
            set  REPEAT_LEFT=%@FLOOR[%@EVAL[                %HZ_PCT/100 * %NUM_REPEATS - 1]]
            set REPEAT_RIGHT=%@FLOOR[%@EVAL[%NUM_REPEATS - (%HZ_PCT/100 * %NUM_REPEATS)   ]]
            unset /q LEFT  %+ 
            unset /q RIGHT %+ 
            if %HZ_PCT eq 100 (set LEFT=%ANSI_COLOR_SUCCESS%)          %+ rem If we are at 100%, let's use our predefined ANSI_COLOR_SUCCESS to color it
             if %REPEAT_LEFT%  gt 0 (repeat %REPEAT_LEFT%  set  LEFT=%LEFT%%ZZZZZ%%DIVIDER_LEFT%) 
             if %REPEAT_RIGHT% gt 0 (repeat %REPEAT_RIGHT% set RIGHT=%RIGHT%%ZZZZ%%DIVIDER_RIGHT%)
            if "%3" eq "rand_middle" .or. "%3" eq "rand" (set RIGHT=%@ANSI_RANDFG[]%RIGHT%) %+ rem If we've been told to insert a random color in the middle, do that by inserting our ansi-randfg code at the beginning of the right half
            set LAST_GENERATED_DIVIDER_LEFT=%ANSI_INVISIBLE_CURSOR%%DECORATOR_BAR_BEG%%LEFT%
            set LAST_GENERATED_DIVIDER_RIGHT=%RIGHT%%DECORATOR_BAR_END%%ANSI_VISIBLE_CURSOR%
            set LAST_GENERATED_DIVIDER_BOTH_BUT_PROBLEMATIC=%LAST_GENERATED_DIVIDER_LEFT%%ESCAPE_CHARACTER>%LAST_GENERATED_DIVIDER_RIGHT%
            echos %LAST_GENERATED_DIVIDER_LEFT%
            if %HZ_PCT gt 0 (echos %ESCAPE_CHARACTER%>)
            echos %LAST_GENERATED_DIVIDER_RIGHT%

        :HZ_PCT_stuff_done
        echos %ANSI_EOL% 
        echo.
        goto :END


rem But a bit more complicated for double-height text, particulary when dealing with a 
rem TCC/Windows Terminal rendering bug that required a lot of ANSI fuddling to deal with...
        :BIG
        set DIVIDER_FULL=%DIVIDER%
        set NUM_REPEATS=%@EVAL[%NUM_REPEATS - 1]
        repeat %NUM_REPEATS set DIVIDER_FULL=%DIVIDER%%DIVIDER_FULL%
        rem works but blank line necessary after because that one line is stuck in big:
        echos %ANSI_SAVE_POSITION%%BIG_TOP%%DIVIDER_FULL%%ANSI_RESTORE_POSITION%%BIG_OFF%%NEWLINE%%@ANSI_MOVE_UP[1]%BIG_BOT%%DIVIDER_FULL%%ANSI_EOL%

        rem echos %ANSI_SAVE_POSITION%
        rem echos %BIG_TOP%%DIVIDER_FULL%%BIG_OFF%
        rem echos %ANSI_RESTORE_POSITION%
        rem echos %NEWLINE%%@ANSI_MOVE_UP[1]%@ANSI_MOVE_TO_COL[1]
        rem rem echos %ANSI_SAVE_POSITION%
        rem echos %BIG_BOT%%DIVIDER_FULL%
        rem echos %BIG_OFF%
        rem echos %ANSI_RESTORE_POSITION%%NEWLINE%%BIG_OFF%%@ANSI_MOVE_UP[1]
        rem echos %BIG_OFF%%ANSI_ERASE_CURRENT_LINE%%BIG_OFF%
        rem echos %ANSI_RESTORE_POSITION%
        rem echos %BIG_OFF%%@ANSI_MOVE_UP[1]%BIG_OFF%%ANSI_ERASE_CURRENT_LINE%%BIG_OFF%%@ANSI_MOVE_TO_COL[1]%BIG_OFF%
        rem echos %NEWLINE%%BIG_OFF%%ANSI_RESET%%NEWLINE%helloooooooooooooo%@ANSI_MOVE_UP[1]Y%@ANSI_MOVE_UP[1]Z
        rem echos %newline%
        rem echo.


:END
:Done

rem Echo a newline if told:
        if "1" == "%DHD_NEWLINE%" echo.

rem turn-back-on-file-redirection:
        setdos /x0
        echos %CURSOR_RESET%



rem experimenting with not resetting this for less cursor-y progress bars: echo %ANSI_INVISIBLE_CURSOR%
:The_Very_END

