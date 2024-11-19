@on break cancel
@Echo OFF

:: sweep thru subdirs first, before conquering main:
    call important * Adding files...
    set  ADDCOMMAND=call git add -A --all --verbose * */.*
        %COLOR_RUN%
        %ADDCOMMAND%
        %COLOR_NORMAL%
        REM DEBUG: if ERRORLEVEL gt 1 echo    errorrrrr
        REM DEBUG: if ERRORLEVEL eq 0 echo no errorrrrr
        call errorlevel "git add failed?!"

pause


:    set  ADDCOMMAND=call git add -A --all --verbose *
:        %ADDCOMMAND%
:
::: also pick up .files, which are ignored by default:
:    set  ADDCOMMAND=call git add -A --all --verbose */.*
:        %ADDCOMMAND%
