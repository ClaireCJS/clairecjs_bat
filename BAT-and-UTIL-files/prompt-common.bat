@Echo OFF

rem         INVOCATION:   Just run prompt-common.bat!
rem
rem                       But you can set environment variables to override default behavior, then run prompt-common
rem
rem
rem   WAYS TO CHANGE THE DEFAULT BEHAVIOR:
rem                       set OS=95                                 (OS-specific behavior: set to 95,98,ME,2K,7,10,11 etc)        [default behavior as of 2023 is Windows 10]
rem                       set SUPPRESS_LESSTHAN_BEFORE_PATH=0       (difference between "c:\>" [1] and "<c:\>" [0])
rem                       set ADD_THE_CPU_USAGE=0                       (suppress adding CPU usage to prompt)
rem
rem   WAYS TO CHANGE THE DEFAULT COLORS:
rem                       set CPU_USAGE_PERCENTS=0;32;33\
rem                       set CPU_USAGE_BRACKETS=0;32;33 \
rem                       set PATH_COLOR_THE_PAT=0;32;33  \
rem                       set PATH_COLOR_BRACKET=0;32;33   >--- Look below for example ANSI color codes
rem                       set TIME_COLOR_THE_TIM=0;32;33  /
rem                       set TIME_COLOR_BRACKET=0;32;33 /
rem                       set USER__TYPING__COLO=0;32;33/
rem   WAYS TO CHANGE THE PROMPT CONTENT:
rem                       set TEXT_AT_START=Hi!
rem                       set TEXT_BEFORE_PATH=IceCream!   <——— changes "< 8:46a> <17%> C:\Users\ClioC>" to "< 8:46a> <17%> IceCream! C:\Users\ClioC>"


rem ///// Branched to new version of this script with Windows 10, older OSes get the older version
    REM DEBUG: echo [DEBUG] prompt-common: os is %OS
    if "%OS" eq "95" .or. "%OS" eq "98" .or. "%OS" eq "ME" .or. "%OS" eq "2K" .or. "%OS" eq "7" (call prompt-common-pre-win10-fork.bat %* %+ goto :END)

rem ///// ANSI CONSTANTS (probably malformed, but work, so I never fixed them):
    :: QUICK-REF: 1=BOLD;30=Black,31=Red,32=Green,33=Yellow,34=Blue,35=Purp,36=Cyan,37=White
    set           RED=1;31;31  %+ rem is this right?
    set    BRIGHT_RED=1;32;31  %+ rem is this right?
    set         GREEN=0;32;32
    set  BRIGHT_GREEN=1;32;32
    set        YELLOW=0;32;33
    set BRIGHT_YELLOW=1;32;33
    set          BLUE=0;32;34
    set   BRIGHT_BLUE=1;32;34
    set        PURPLE=0;32;35
    set BRIGHT_PURPLE=1;32;35
    set          CYAN=0;32;36
    set   BRIGHT_CYAN=0132;36
    set          GRAY=1;30;30 %+ set GREY=%GRAY%
    set         WHITE=0;00;00

rem ///// DEFAULT COLORS THAT CAN BE OVERRIDDEN:
    if not defined CPU_USAGE_PERCENTS  set  CPU_USAGE_PERCENTS=%YELLOW%
    if not defined CPU_USAGE_BRACKETS  set  CPU_USAGE_BRACKETS=%GREEN% %+ rem %BRIGHT_YELLOW%
    if not defined PATH_COLOR_THE_PATH set PATH_COLOR_THE_PATH=%BRIGHT_GREEN%
    if not defined PATH_COLOR_BRACKETS set PATH_COLOR_BRACKETS=%GREEN%
    if not defined TIME_COLOR_THE_TIME set TIME_COLOR_THE_TIME=%RED%
    if not defined TIME_COLOR_BRACKETS set TIME_COLOR_BRACKETS=%BRIGHT_RED%
    if not defined USER__TYPING__COLOR set USER__TYPING__COLOR=%WHITE%

rem ///// DEFAULT BEHAVIOR THAT CAN BE OVERRIDDEN:
    if not defined ADD_THE_CPU_USAGE   set ADD_THE_CPU_USAGE=1
    if "%SUPPRESS_LESSTHAN_BEFORE_PATH%" ne "1" if not defined PATH_BRACKET_BEFORE set PATH_BRACKET_BEFORE=$l

rem ///// BUILD THE PROMPT:
    :Setup
        unset /q TMPPROMPT
    :Reset_Font_To_English
        rem just in case we used ansi to flip it into DEC drawing font, we want it back
        set TMPPROMPT=$e(B%TMPPROMPT%
    :Reset_Cursor_To_Our_Preferred_Color_And_Shape
        rem we return diff colored cursors from programs sometimes, and this resets them
        rem Actually... Decided not to do this because it would change it upon the first prompt. I'd really only want to do this a 2nd time. Not feasible.
    :Add_StarT_Text
            rem echo tmpprompt=%tmpprompt%
            iff "%TEXT_AT_START%" ne "" .and. 1 eq 1 then
                set TMPPROMPT=%TMPPROMPT%%TEXT_AT_START% ``
            endiff
    :Add_Time_Of_Day
        set TMPPROMPT=%TMPPROMPT%$e[%TIME_COLOR_BRACKETS%m$L
        set TMPPROMPT=%TMPPROMPT%$e[%TIME_COLOR_THE_TIME%m$M
        set TMPPROMPT=%TMPPROMPT%$e[%TIME_COLOR_BRACKETS%m$G ``
    :Add_CPU_Usage
        REM DEBUG: call warning "`%`ADD_THE_CPU_USAGE is %ADD_THE_CPU_USAGE"
        if %ADD_THE_CPU_USAGE ne 0 (
            set TMPPROMPT=%TMPPROMPT%$e[%CPU_USAGE_BRACKETS%m$L
            set TMPPROMPT=%TMPPROMPT%$e[%CPU_USAGE_PERCENTS%m CPUUSAGEHERE
            set TMPPROMPT=%TMPPROMPT%$e[%CPU_USAGE_BRACKETS%m$G ``
        )
    :Add_Any_Text_We_Want_Between
            rem echo tmpprompt=%tmpprompt%
            iff "%TEXT_BEFORE_PATH%" ne "" .and. 1 eq 1 then
                set TMPPROMPT=%TMPPROMPT%%TEXT_BEFORE_PATH% ``
            endiff
    :Add_Path
        set TMPPROMPT=%TMPPROMPT%$e[%PATH_COLOR_BRACKETS%m%PATH_BRACKET_BEFORE%
        set TMPPROMPT=%TMPPROMPT%$e[%PATH_COLOR_THE_PATH%m$P
        set TMPPROMPT=%TMPPROMPT%$e[%PATH_COLOR_BRACKETS%m$G
    :Add_Color_For_user_Typing
        set TMPPROMPT=%TMPPROMPT%$e[%USER__TYPING__COLOR%m


rem ///// FORMAT/SBUSTITUTE/SET THE PROMPT:
        if "%OS%" eq "2K" goto :CPU_Usage_Format_NO
        if "%OS%" eq "XP" goto :CPU_Usage_Format_NO
        if "%OS%" eq "10" goto :CPU_Usage_Format_YES_10
        if "%OS%" eq "11" goto :CPU_Usage_Format_YES_10
                          goto :CPU_Usage_Format_YES_10 %+ REM Default behavior if %OS isn't set

            :CPU_Usage_Format_YES
                rem This one worked for years, maybe 10+, up until Windows 10 came out
                prompt=%@REPLACE[ CPUUSAGEHERE,%%%%@FORMATN[02.0,%%%%[_CPUUsage]]%%%%%%%%,%[TMPPROMPT]]
            goto :CPU_Usage_Format_DONE

            :CPU_Usage_Format_YES_10
                prompt=%%@REPLACE[ CPUUSAGEHERE,%%_CPUUSAGE%%%%%%%%%%,%[TMPPROMPT]]
            goto :CPU_Usage_Format_DONE

            :CPU_Usage_Format_NO
                 prompt=%@REPLACE[ CPUUSAGEHERE,%%%%[_CPUUsage]%%%%%%%%,%[TMPPROMPT]]
            :CPU_Usage_Format_DONE


rem ///// CLEAN UP:
    unset /q CPU_USAGE_PERCENTS
    unset /q CPU_USAGE_BRACKETS
    unset /q PATH_BRACKET_BEFORE
    unset /q PATH_COLOR_THE_PATH
    unset /q PATH_COLOR_BRACKETS
    unset /q TIME_COLOR_THE_TIME
    unset /q TIME_COLOR_BRACKETS
    unset /q USER__TYPING__COLOR
    unset /q SUPPRESS_LESSTHAN_BEFORE_PATH
    unset /q TEXT_BEFORE_PATH
    unset /q TEXT_AT_START
:END
