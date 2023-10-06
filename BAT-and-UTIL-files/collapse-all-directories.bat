@Echo OFF

::::: WARN:
    %COLOR_ALARM%   %+ echo. %+ echo **** THIS WILL COLLAPSE ALL DIRECTORIES!!! ****
    %COLOR_WARNING% %+ echo. %+ echo **** There is no going back!!! ****
    %COLOR_ADVICE%  %+ echo. %+ echo Directory tree will be saved in \recycled\undo.txt
    %COLOR_NORMAL%  %+ echo. %+ pause

::::: SAVE UNDO INFORMATION:
    dir /bs/a: >\recycled\undo.txt

::::: COLLAPSE ALL THE FOLDERS:
    for /a:d /h %d in (*) mv/ds %d .

