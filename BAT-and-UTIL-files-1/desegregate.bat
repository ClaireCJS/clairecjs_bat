
::::: CONFIGURATION: 
    call segregate-vars

::::: BRANCHING:
    set CURDIR=%@FILENAME[%_CWP]
    if "%@UPPER[%CURDIR%]" eq "%@UPPER[%SUBFOLDER%]" goto :WeAreInIt




goto :END

    :WeAreInIt
        cd ..
        if isdir "%SUBFOLDER%" mv/ds "%SUBFOLDER%" .
    goto :END

:END