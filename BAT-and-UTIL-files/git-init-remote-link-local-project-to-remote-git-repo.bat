@Echo OFF

echo.
echo.
echo.
call advice If you don't have a repo, go to http://github.com and click the '+' at the top-right of the screen and create one

echo.
echo.
call important "Input your git repository name:"
         set GITHUB_REPO_NAME=%@NAME[%_CWP]
        eset GITHUB_REPO_NAME


echo.
echo.
call validate-environment-variables NETNAME GITHUB_REPO_NAME NETNAME_CLAIRE
 set REPO_URL=https://github.com/%NETNAME_CLAIRE%/%GITHUB_REPO_NAME%.git
call important "Edit your repo URL if you think this auto-generated one isn't correct:"
eset REPO_URL

echo.
echo.
echo.
call important "Press any key to confirm your repo URL -- this will open it in your web browser for you to verify it's correct"
pause
call validate-environment-variables REPO_URL
%REPO_URL%

echo.
echo.
echo.
call important "Proceed to link local repo %_CWP to remote repo at %REPO_URL%"
        pause
        :Redo_1
            call git.bat remote add origin %REPO_URL%
            call errorlevel
        if %REDO_BECAUSE_OF_ERRORLEVEL eq 1 (goto :Redo_1)

echo.
echo.
echo.
call advice (select manager-core for credentials)
echo.
call important "About to: call git.bat pull origin main"
pause

:Redo_2
    call git.bat pull origin main
    call errorlevel
if %REDO_BECAUSE_OF_ERRORLEVEL eq 1 (goto :Redo_2)







echo.
echo.
echo.
call advice (select manager-core for credentials)
echo.
call important "About to: call git.bat push -u origin main"
pause

:Redo_3
    call call git.bat push -u origin main
    call errorlevel
if %REDO_BECAUSE_OF_ERRORLEVEL eq 1 (goto :Redo_3)

