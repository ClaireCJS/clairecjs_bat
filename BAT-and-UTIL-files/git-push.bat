@Echo OFF
set PARAMS=%*
set BASENAME=%@NAME[%_CWD]
if %VALIDATED_GITPUSH ne 1 (
    call validate-in-path git.bat errorlevel advice important
    call validate-environment-variables GITHUB_USERNAME BAT BASENAME 
    set VALIDATED_GITPUSH=1
)

echo.
echo.
echo.
echo.
set spacer=
if "%params%" ne "" set spacer= ``
call important "About to: 'git push origin main%spacer%%params%' in %@NAME[%_CWP]"
if %NO_PAUSE ne 1 pause

set GIT_OUT=git.out
echo.
REM call unimportant "[Unfiltered GIT output followed by filtered GIT output]..."
set TEECOLOR=%COLOR_UNIMPORTANT%
call git push origin main %PARAMS% |& tee %GIT_OUT%
call errorlevel "Advice: for 'updates were rejected because the remote contains work that you do not have locally', you may need to 'git pull origin main' to merge and then try again" 

echo.
call validate-environment-variable GIT_OUT
if "%@EXECSTR[grep Updates.were.rejected.because.the.remote.contains.work.that.you.do git.out]" ne "" (call warning "You probably need to do 'git pull origin main'")

echo.
echo.
REM moved below: call success "Git Push was successful!"


set URL=https://github.com/%GITHUB_USERNAME%/%BASENAME%
call advice "- Your GitHub URL is: %URL%"
echo %URL>%BAT%\go-url.bat
call advice "                      (type 'go-url' to go there)"

echo.
call celebration "%BLINK_ON%Git Push completed successfully%BLINK_OFF%"
