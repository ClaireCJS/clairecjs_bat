@Echo off
call validate-in-path isrunning winkill.exe
call isRunning WinKill %+ if %IS_RUNNING eq 0 (winkill.exe)
