@Echo OFF
@on break cancel

rem VALIDATE ENVIRONMENT:
    call validate-in-path LaunchKey


rem CHECK IF MILKDROP IS RUNNING
    rem Can't do process ID check, must do Window Title check:
    if "%@WINPID[Milkdrop 2]" ne "-1" (goto :Milkdrop_Already_Running)
    goto :Milkdrop_Not_Running



rem STOPMILKDROP IF NOT ALREADY STARTED:
    :Milkdrop_Already_Running
        rem Send Ctrl-Shift-K keypress to Winamp:
        LaunchKey "+^K" "%ProgramFiles\Winamp\winamp.exe"
    :Milkdrop_Not_Running

