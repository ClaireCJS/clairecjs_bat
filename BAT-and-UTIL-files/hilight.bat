@echo on

    set SEARCHFOR1=%*
    set SEARCHFOR2=%@UNQUOTE[%*]
    :call debug "Searchfor1/2 are '%SEARCHFOR1%' and '%SEARCHFOR1%'"

::::: DEBUGS:
    set DEBUG_HIGHLIGHT=0

::::: DOCUMENTATION ONLY: SUGGESTED EXAMPLE ENVIRONMENT VALUES:
    :set GREP_COLORS_NORMAL=fn=1;33:ln=1;36;44
    :set GREP_COLOR_NORMAL=1;33;42
    :set GREP_COLORS_HILITE=fn=1;34:ln=1;37;44
    :set GREP_COLOR_HILITE=1;41;37


::::: ENVIRONMENT VALIDATION:
    if "%ENVIRONMENT_VALIDATION_HIGHLIGHT_ALREADY%" eq "1" goto :AlreadyValidated
        call validate-environment-variables GREP_COLOR_NORMAL GREP_COLORS_NORMAL GREP_COLOR_HILITE GREP_COLORS_HILITE
        call validate-in-path sed
        set ENVIRONMENT_VALIDATION_HIGHLIGHT_ALREADY=1
    :AlreadyValidated

::::: STORE ORIGINAL GREP-COLOR AND ESCAPE KEY, SWAP OUT FOR HILIGHT-SPECIFIC GREP-COLOR:
    set GREP_COLORS=%GREP_COLORS_HILITE% 
    call car silent



::::: DO THE ACTUAL GREP:
        set DEBUG_HIGHLIGHT=1
        if %DEBUG_HIGHLIGHT ne 1 goto :No_Debug
            echo SEARCHFOR1=%SEARCHFOR1%
            echo SEARCHFOR2=%SEARCHFOR2%
            echo sed '/%SEARCHFOR1/,${s//\x1b[1;33;41m&\x1b[0m/g;b};$q5'  [with searchfor1]
            echo sed '/%SEARCHFOR2/,${s//\x1b[1;33;41m&\x1b[0m/g;b};$q5'  [with searchfor2]
        :No_Debug
                 sed '/%SEARCHFOR2/,${s//\x1b[1;33;41m&\x1b[0m/g;b};$q5' 

    

::::: RESTORE ORIGINAL GREP-COLORS AND ESCAPE CHARACTER:
    call nocar silent
    set  GREP_COLOR=%GREP_COLOR_NORMAL%
    set GREP_COLORS=%GREP_COLORS_NORMAL%

