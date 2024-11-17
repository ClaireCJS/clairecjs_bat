@echo off

:PUBLISH:
:DESCRIPTION: A way to highlight text.  Basically a grep-like functionality. Great for doing secondary greps on already grepped blocks of text that you *do* want to see. can be done with grep, but we prefer using sed.

    REM call debug "parameters are %*"
    call change-command-separator-character-to-tilde silent
    set SEARCHFOR1=%*
    set SEARCHFOR2=%@UNQUOTE[%*]
    REM call debug "Searchfor1/2 are '%SEARCHFOR1%' and '%SEARCHFOR1%'"

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



::::: DEBUG INFO:
        REM echo DEBUG_HIGHLIGHT is "%DEBUG_HIGHLIGHT"
        if %DEBUG_HIGHLIGHT eq 1 (
            echo SEARCHFOR2=%SEARCHFOR2%
            echo sed "/%%SEARCHFOR2/,${s//\x1b[1;33;41m&\x1b[0m/g;b};$q5"  %faint_on%[with searchfor2='%italics_on%%searchfor2%%italics_off%']%faint_off%
        )

::::: DO THE ACTUAL HIGHLIGHTING:
           REM sed -E "/%SEARCHFOR2%/,${s/%SEARCHFOR2%/\x1b[1;33;41m&\x1b[0m/gI;b};$q5" 
REM              sed -E "/%SEARCHFOR2%/,${s/%SEARCHFOR2%/\x1b[1;33;41m&\x1b[0m/gi;b};$q1" 
REM    awk -v srch="%SEARCHFOR2%" 'BEGIN{IGNORECASE=1} {gsub(srch,"\033[1;33;41m" srch "\033[0m"); print}' | cat
REM    awk -v srch="%SEARCHFOR2%" 'BEGIN{IGNORECASE=1} {gsub(srch,"\033[1;33;41m" srch "\033[0m"); print}'
REM    awk -v srch="%SEARCHFOR2%" "BEGIN{IGNORECASE=1} gsub(srch,'\033[1;33;41m' srch '\033[0m'){print}"
REM    awk -v srch="%SEARCHFOR2%" 'BEGIN{IGNORECASE=1}{gsub(srch, "\033[1;33;41m" srch "\033[0m"); print}' 
REM close but \033 instead of [ESC] gawk -v srch="%SEARCHFOR2%" "BEGIN{IGNORECASE=1}{gsub(srch, \"\\033[1;33;41m\" srch \"\\033[0m\"); print}" 
REM doesn't dsplay the damn ansi when typed almost seems like gawk kills ansi emulation until cmd line is back (c:\cygwin\bin\gawk -v srch="%SEARCHFOR2%" "BEGIN{IGNORECASE=1}{gsub(srch, \"%ESCAPE%[1;33;41m\" srch \"%ESCAPE%[0m\"); print}")>a %+ type a %+ *del /q a

             sed "/%SEARCHFOR2%/,${s//\x1b[1;33;41m&\x1b[0m/g;b};$q5"  


    call change-command-separator-character-back silent


rem RESTORE ORIGINAL GREP-COLORS AND ESCAPE CHARACTER:
    set  GREP_COLOR=%GREP_COLOR_NORMAL%
    set GREP_COLORS=%GREP_COLORS_NORMAL%

