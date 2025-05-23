@on break cancel
@Echo OFF


rem Collect parameters:
        unset /q GIT_PULL_PARAMETERS
        set      GIT_PULL_PARAMETERS=%*


rem Configuratoin:
        set GIT_OUT=git.out
        rem BASENAME=%@FILENAME[%_CWD]
        set BASENAME=%@UNQUOTE[%@FILENAME["%_CWD"]]
        set MY_GITHUB_URL=https://github.com/%GITHUB_USERNAME%/%BASENAME%


rem Validate environment:
        if %VALIDATED_GITPULL ne 1 (
            call validate-in-path               git.bat errorlevel advice important celebration
            call validate-environment-variables GITHUB_USERNAME BAT BASENAME MY_GITHUB_URL GITHUB_USERNAME
            set VALIDATED_GITPULL=1
        )




rem Cosmetics:
        echo.
        echo.
        echo.
        echo.
        set spacer=
        if "%GIT_PULL_PARAMETERS%" ne "" (set spacer= ``)


rem Inform regarding what we’re about to do:
        call important "About to: “git pull %spacer%%GIT_PULL_PARAMETERS%” in %emphasis%%BASENAME%%deemphasis%"
        rem I stopped wanting a pause *ALL* the time, ater awhile: if %NO_PAUSE ne 1 (pause)
        echo.

rem Run GIT, check for error status, and collect the output:
        rem old: call unimportant "[Unfiltered GIT output followed by filtered GIT output]..."
        REM old, but now git.bat has it’s own TEE to git.out internally: 
            REM set TEECOLOR=%COLOR_UNIMPORTANT%
            REM call git.bat push origin main %GIT_PUSH_PARAMETERS% |& tee %GIT_OUT%
                call git.bat pull %GIT_PUSH_PARAMETERS% 
                rem call errorlevel "Advice: for “updates were rejected because the remote contains work that you do not have locally”, you may need to “git pull origin main” to merge and then try again" 
        echo.
        if not exist %GIT_OUT% (goto :NoGitOut)
        if "%@EXECSTR[grep Updates.were.rejected.because.the.remote.contains.work.that.you.do git.out]" ne "" (call warning "You probably need to do “git pull origin main”" %+ pause)
        :NoGitOut

rem Provide easy way to check that it happened online:
        call advice "Your GitHub URL is: %MY_GITHUB_URL%"
        echo %MY_GITHUB_URL>%BAT%\go-url.bat
        call advice "                    (type “go-url” to go there)"

rem Be happy that we were successful!
        echo.
        call celebration "%BLINK_ON%%DOUBLE_UNDERLINE%Pull%DOUBLE_UNDERLINE_OFF% completed%BLINK_OFF%"


