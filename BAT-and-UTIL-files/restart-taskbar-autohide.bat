@Echo OFF
kill /f taskba*
call important "Taskbar-autohide killed, now restarting..."
start c:\util\taskbar-autohide.exe
pg taskba|gr -v grep
