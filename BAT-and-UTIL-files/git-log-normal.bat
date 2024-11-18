@Echo OFF
call git-initvars
set FILE=%1
git --no-pager log -p  %FILE%
