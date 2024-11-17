@Echo off
call validate-in-path isrunning winkill.exe
call isRunning WinKill 
if %IS_RUNNING eq 1 (goto         :END)
if %IS_RUNNING eq 0 (start winkill.exe)
call isRunning WinKill 
:END


