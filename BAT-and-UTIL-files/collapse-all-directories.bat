@Echo OFF

::::: WARN:
    call alarm   "THIS WILL COLLAPSE ALL DIRECTORIES"
    call warning "There is no going back"
    call advice  "Directory tree will be saved in \recycled\undo.txt"
    %COLOR_NORMAL%  %+ echo. %+ pause

pause
pause
pause
pause
pause
pause
pause
pause

::::: SAVE UNDO INFORMATION:
    dir /bs/a: >\recycled\undo.txt

::::: COLLAPSE ALL THE FOLDERS:
    for /a:d /h %d in (*) mv/ds %d .

