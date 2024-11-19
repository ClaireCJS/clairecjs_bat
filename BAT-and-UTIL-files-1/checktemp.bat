@echo off
 on break cancel
call validate-environment-variable TEMP

if "%temp"=="" goto Error
goto :done

:Error
    echo Uh oh!  No temp directory defined.
    echo We will set one for you.
    pause
    pause
    set TEMP=c:\recycled\
    if "%OS"=="2K" set TEMP=c:\recycler\
    if "%OS"=="ME" set TEMP=c:\recycler\
    if "%OS"=="98" set TEMP=c:\recycler\
    if "%OS"=="95" set TEMP=c:\recycler\
    echo %%TEMP is now %tmp ... 
    pause

:done