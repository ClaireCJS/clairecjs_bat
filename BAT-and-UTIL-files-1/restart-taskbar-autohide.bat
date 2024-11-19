@Echo OFF
@on break cancel
kill /f taskba*
call important "Taskbar-autohide killed, now restarting..."
start c:\util\taskbar-autohide.exe
pg taskba|:u8gr -v grep
