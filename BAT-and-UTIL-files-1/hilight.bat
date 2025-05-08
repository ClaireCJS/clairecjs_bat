@on break cancel
@echo off


rem PARAMS:
    set SEARCHFOR1=%*
    set SEARCHFOR2=%@UNQUOTE[%*]
    rem call debug "Searchfor1/2 are '%SEARCHFOR1%' and '%SEARCHFOR1%'"

rem DEBUGS:
    set DEBUG_HIGHLIGHT=0

rem DOCUMENTATION ONLY: SUGGESTED EXAMPLE ENVIRONMENT VALUES:
    rem set GREP_COLORS_NORMAL=fn=1;33:ln=1;36;44
    rem set GREP_COLOR_NORMAL=1;33;42
    rem set GREP_COLORS_HILITE=fn=1;34:ln=1;37;44
    rem set GREP_COLOR_HILITE=1;41;37


rem ENVIRONMENT VALIDATION:
    if "%ENVIRONMENT_VALIDATION_HIGHLIGHT_ALREADY%" == "1" goto :AlreadyValidated
        if not defined GREP_COLOR_NORMAL  call validate-environment-variable GREP_COLOR_NORMAL 
        if not defined GREP_COLORS_NORMAL call validate-environment-variable GREP_COLORS_NORMAL 
        if not defined GREP_COLOR_HILITE  call validate-environment-variable GREP_COLOR_HILITE 
        if not defined GREP_COLORS_HILITE call validate-environment-variable GREP_COLORS_HILITE        
        rem this creates problems when in a piped situation like this script: call validate-in-path sed
        set ENVIRONMENT_VALIDATION_HIGHLIGHT_ALREADY=1
    :AlreadyValidated

rem STORE ORIGINAL GREP-COLOR AND ESCAPE KEY, SWAP OUT FOR HILIGHT-SPECIFIC GREP-COLOR:
    set GREP_COLORS=%GREP_COLORS_HILITE% 
    call car silent



rem DO THE ACTUAL GREP:
        if "%DEBUG_HIGHLIGHT%" != "1" goto :No_Debug
            echo SEARCHFOR1=%SEARCHFOR1%
            echo SEARCHFOR2=%SEARCHFOR2%
            echo sed '/%SEARCHFOR1/,${s//\x1b[1;33;41m&\x1b[0m/g;b};$q5'  [with searchfor1]
            echo sed '/%SEARCHFOR2/,${s//\x1b[1;33;41m&\x1b[0m/g;b};$q5'  [with searchfor2]
        :No_Debug
                 sed '/%SEARCHFOR2/,${s//\x1b[1;33;41m&\x1b[0m/g;b};$q5' 

    

rem RESTORE ORIGINAL GREP-COLORS AND ESCAPE CHARACTER:
    call nocar silent
    set  GREP_COLOR=%GREP_COLOR_NORMAL%
    set GREP_COLORS=%GREP_COLORS_NORMAL%

