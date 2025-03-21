@Echo OFF
@on break cancel
if "%1" == "cleanup" goto :cleanup
set USER=%1

call warning "The first paramater to %0 should be a reddit username, or 'cleanup' to run cleanup"
rem obsolete now that we have bdfr: call advice  "Consider running ripme.bat %0"


set USER_URL=https://www.reddit.com/user/%USER%
call clip %USER_URL%
call debug "Reddit user = '%USER%'%NEWLINE%%overstrike%Reddit url  = '%USER_URL%'%overstrike_off% [not currently used]"

if "%1" == "" goto :Usage

call validate-in-path bdfr.exe "bdfr.exe not found, do we need to run 'pip install bdfr'?"

set TARGET=c:\bdsmlr\%USER% (u_%USER%)
if not exist "%TARGET%" (md /s "%TARGET%")

call advice "removing --log has helped with failures before"
    
call warning "not sure if this --log parameter needs a filename or not..." %+ pause
     
rem %COLOR_UNIMPORTANT% %+ echo bdfr.exe download "%TARGET%" --user %USER% --submitted --no-dupes --log "%TARGET%"
rem %COLOR_RUN%         %+      bdfr.exe download "%TARGET%" --user %USER% --submitted --no-dupes --log "%TARGET%"

%COLOR_UNIMPORTANT% %+ echo About to: bdfr.exe download "%TARGET%" --user %USER% --submitted --no-dupes --log "%TARGET%\log.txt" %+ pause
%COLOR_RUN%         %+                bdfr.exe download "%TARGET%" --user %USER% --submitted --no-dupes --log "%TARGET%\log.txt"
            
call errorlevel
call validate-environment-variable TARGET

"%TARGET%\"
call important "about to run cleanup in %_CWP..."
:ause
:cleanup
set CLEANDIR=%_CWD
echo sweep mv * %CLEANDIR% %+ sweep rd *
sweep mv * "%CLEANDIR%" %+ sweep rd *
call delete-duplicate-files-including-subfolder-duplicates




goto :END
if "%1" eq "2022" goto :2022

                            REM :::::::::::::::::::::::::: LEGACY STUFF :::::::::::::::::::::::::: 
                            :2022
                            set TOOL=%UTIL2%\Download_Reddit_Images\
                            set REDDIT_USER_NAME=%1
                            call validate-environment-variables UTIL2 PRN_NEW TOOL REDDIT_USER_NAME REDDIT REDDIT_USER_NAME
                            DownloadRedditImages.exe  %REDDIT_USER_NAME%
                            ::::: CLEANUP
                                set                             REDDIT=%PRN_NEW%\Reddit
                                call print-if-debug                 REDDIT  %REDDIT%
                                if not isdir "%REDDIT%"         (md /s "%REDDIT%")
                                set                             REPO_TARGET="%REDDIT%\%REDDIT_USER_NAME%"
                                call print-if-debug REPO_TARGET is %REPO_TARGET%
                                call put %REDDIT_USER_NAME%   "%REDDIT%"
                                :all put %REDDIT_USER_NAME%   "%REPO_TARGET%"
                                                               %REPO_TARGET%
                            goto :END

    :Usage
        call advice "%0 %italics%{reddit_user_name}%italics_off%"
    goto :END

:END
