@Echo off
 on break cancel
call environm

:::::    PURPOSE: To list all environment variables representing color change commands.
:::::                Variables like %COLOR_ALARM%, %COLOR_DEBUG%, %COLOR_IMPORTANT%, etc
:::::                which have values like "color bright white on red", "color green on black", "color bright cyan on black", etc.
:::::
:::::   UPDATE 1: Skip "COLOR_xxxx_ANSI" environment variables, as these are actually ANSI strings  
:::::             instead of "color xxx on xxx" commands. Not the same thing.
:::::
:::::   UPDATE 2: Skip "GREP_COLOR".  
:::::             Yes, we could have used a regex with "^" in it, but there are reasons we avoid that.
:::::
:::::       TODO: draw "*_color_hex".  
:::::             Yes, we COULD print these out somehow


call validate-in-path   sed grep colortool display-message_type_environment-variables-and-corresponding-ansi-color-environment-variables
call validate-env-vars  DEFAULT_TAB_STOP_WIDTH ANSI_ESCAPE ESCAPE 
call validate-functions ANSI_MOVE_TO_COL

:cls
set SILENT=0
if "%1" eq "silent" set SILENT=1

if %SILENT ne 1  (
    call display-message_type_environment-variables-and-corresponding-ansi-color-environment-variables.bat
    echo.
    rem repeat 6 echos @ANSI_MOVE_TO_COL[%_repeat]%ESCAPE%[3g%%ESCAPE%H 🐐 this breaks it .. we really want to fix it
    echos %@ANSI_MOVE_TO_COL[1]%ANSI_ESCAPE%0g
    echos %@ANSI_MOVE_TO_COL[2]%ANSI_ESCAPE%0g
    echos %@ANSI_MOVE_TO_COL[3]%ANSI_ESCAPE%0g
    echos %@ANSI_MOVE_TO_COL[4]%ANSI_ESCAPE%0g
    echos %@ANSI_MOVE_TO_COL[5]%ANSI_ESCAPE%0g
    echos %@ANSI_MOVE_TO_COL[6]%ANSI_ESCAPE%0g
    echos %@ANSI_MOVE_TO_COL[7]%ESCAPE%H
    call colortool -c
    call reset-tab-stops %DEFAULT_TAB_STOP_WIDTH%

)


call settmpfile 
set ALL_COLORS=
set|:u8grep -i color|:u8sed "s/=.*$//ig" >:u8"%TMPFILE%"
:DEBUG: (set|:u8sed "s/=.*$//ig") %+ echo TMPFILE: %+ type "%TMPFILE%" %+ pause
for /f "tokens=1-999" %co in (%TMPFILE%) gosub ProcessEnvVar %co%


goto :END
    :ProcessEnvVar [var]
        set ADD_TO_ALL_COLORS=1
        if  "%VAR%" eq "LAST_RANDCOLOR"   (set ADD_TO_ALL_COLORS=0) %+ REM  don't add this one to our ALL_COLORS list because it's an audit color not one of our messaging colors .. any LAST_.*COLOR really would be, but this is the only one bothering us
        if "%@REGEX[ANSI_PREFERRED_CUR,%VAR%]" eq  "1"  (return)    %+ REM  stop for environment variables like "LAST_COLOR"
        if "%@REGEX[LAST_COLOR,%VAR%]"         eq  "1"  (return)    %+ REM  stop for environment variables like "LAST_COLOR"
        if "%@REGEX[ERASE_COLOR_,%VAR%]"       eq  "1"  (return)    %+ REM  stop for environment variables like "ERASE_COLOR_MODE_OFF"
        if "%@REGEX[COLOR_.*_HEX,%VAR%]"       eq  "1"  (return)    %+ REM  stop for environment variables like "COLOR_ALARM_HEX"
        if "%@REGEX[COLOR_,%VAR%]"             ne  "1"  (return)    %+ REM  stop for environment variables like "COLOR_ALARM"
        if "%@REGEX[COLOR_.*_ANSI,%VAR%]"      eq  "1"  (return)    %+ REM   but not environment variables like "COLOR_ALARM_ANSI", which are different
        if "%@REGEX[GREP_COLOR_,%VAR%]"        eq  "1"  (return)    %+ REM   and not environment variables like "GREP_COLOR"      , which are different
        REM DEBUG: echo.%+echo.%+echo.%+ 
        set TMP_CLR=%@REPLACE[COLOR_,,%var]
        REM DEBUG: echo * Processing colorvar %var (color=%TMP_CLR%)
        if %ADD_TO_ALL_COLORS eq 1 (set ALL_COLORS=%ALL_COLORS% %TMP_CLR%)
        if %SILENT eq 1 (goto :silent_1)
            echo. 
            rem Determine if this is a color command, or an ansi color value:
            setdos /x-5
            set IS_ANSI=%@REGEX[^ANSI_COLOR,%VAR%]
            set IS_MACHINE=%@REGEX[^MACHINE_COLOR,%VAR%]
            setdos /x0

            if %IS_MACHINE eq 1 (set  IS_ANSI=1)
            if %IS_ANSI    eq 1 (echos %[%VAR%]) 
            if %IS_ANSI    eq 0       (%[%VAR%])

            rem echos %IS_ANSI%/%IS_MACHINE% 
            echos  *** This is %VAR% *** `` 
            %COLOR_NORMAL%
        :silent_1
    return
:END
REM echo.
REM echo. %+ call debug "ALL_COLORS is now set to '%ALL_COLORS%'"
