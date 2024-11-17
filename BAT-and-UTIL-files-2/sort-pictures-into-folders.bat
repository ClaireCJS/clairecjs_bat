@echo off

SET RECYCLEDBAT=c:\recycled\latest-sort-pictures-into-folders.bat

call fixtmp.bat
call setpath.bat
call settmpfile 
set TMPFILE1=%tmpfile%
call settmpfile 
set TMPFILE2=%tmpfile%

set runme=runme.bat

set filelist=filelist.txt
dir /a:-d /b>%filelist%

(sort-pictures-into-folders-helper.pl <%filelist)  >%runme%

if exist %filelist *del /q %filelist

call validate-environment-variable runme

    echo.
    echo.
    echo.

    %COLOR_PROMPT% 
    echos Batfile completed.  Please review: 
    %COLOR_NORMAL% 
    echo.
    pause

    %COLOR_SUBTLE%
    type %runme%
    if "%1" ne "nopause" (pause)


    echo.
    echo.
    echo.
:%COLOR_PROMPT%
:    echo If that seems okay, press any key to run it.
:    pause>nul

    echo.
    echo.
    echo.

%COLOR_RUN%
    call %runme%
    cp   %runme% c:\recycled\sort-pictures-into-folders-%_datetime.bat
    *del %runme%

