@Echo off
call warning about to rename branch %1 to %2
pause
git branch -m %1 %2
call errorlevel
