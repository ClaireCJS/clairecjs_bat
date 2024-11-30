@on break cancel
@Echo Off

set ARGS=%*
set NO_GIT_ADD_PAUSE=0

iff "%2" eq "nopause"  then
    set NO_GIT_ADD_PAUSE=1
    ARGS=%1 %3$
endiff

REM Skip validation if we're told, but only this once
    if %SKIP_GIT_ADD_VALIDATION ne 1 (call validate-environment-variable ARGS)
    if %SKIP_GIT_ADD_VALIDATION eq 1 (set SKIP_GIT_ADD_VALIDATION=)


REM create our add command
    set ADDCOMMAND=call git add --verbose %ARGS%


REM Let the user know, and do it
    call important      "➕Adding files➕"
    call print-if-debug "command: '%italics%%ADDCOMMAND%%italics_off%'"
    %COLOR_RUN%
    %ADDCOMMAND%

REM do not pause if we're in automatic mode
    if %NO_GIT_ADD_PAUSE ne 1 (call errorlevel "git add failed?!")
    if %NO_GIT_ADD_PAUSE eq 1 (set  NO_GIT_ADD_PAUSE=0           )


