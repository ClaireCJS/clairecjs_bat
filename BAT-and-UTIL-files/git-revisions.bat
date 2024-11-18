@Echo OFF
call git-initvars
set FILE=%1
git.exe --no-pager log --follow -p -- %FILE%
