@Echo OFF
call git-initvars
git init
call errorlevel
call advice.bat now use git add to add the appropriate files