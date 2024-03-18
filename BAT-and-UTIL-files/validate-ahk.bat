@if  AHK_VALIDATED eq 1 (goto :END)


@Echo OFF

set AHK_DIR=c:\util\AutoHotKey\v2\
set AHK_EXE=%AHK_DIR%\AutoHotkey64.exe

call validate-environment-variables AHK_DIR AHK_EXE
set AHK_VALIDATED=1

:END

