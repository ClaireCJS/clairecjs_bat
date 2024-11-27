@Echo OFF

git.exe remote set-url origin git@github.com:ClaireCJS/clairecjs_bat.git
pause-for-x-seconds 3
git.exe remote -v
