@loadbtm on
@echo off
 on break cancel

:echo DEBUG: CALLED: %0 1=%1 2=%2 3=%3 4=%4 5=%5

if "%2"=="" goto :badusage
if "%CHUNK" ne "" goto :chunk_set
echo * setting chunk size to %1
set CHUNK=%1
:chunk_set
echo * chunk size is %CHUNK
if "%3" ne "" (echo setting compression to %3 %+ set COMPRESSION=%3 %+ goto :compression_set)

inkey /C /K"YN12345[ENTER]" /w600 Use compression?  (takes much longer)  [Y/n/0-5] (N=none/fastest):  %%key  
set COMPRESSION=%key
if /I "%key"=="n" set COMPRESSION=0
if /I "%key"=="y" set COMPRESSION=3
if /I "%@ascii[%key]"=="64 50 56" set COMPRESSION=3
:compression_set
:echo COMPRESSION IS %COMPRESSION
:OLD:"%ProgramFiles\winrar\rar.exe" a -m%COMPRESSION -ep1 -rr8p -r -v%%1b %3      "%@STRIP[%=",%2].rar" "%@STRIP[%=",%2]"
:OLD:"%ProgramFiles\winrar\rar.exe" a -m%COMPRESSION -ep1 -rr8p -r -v%[CHUNK]b    "%@STRIP[%=",%2].rar" "%@STRIP[%=",%2]"
echo "%ProgramFiles\winrar\rar.exe" a -m%COMPRESSION -ep1       -r -v%[CHUNK]b    "%@STRIP[%=",%2].rar" "%@STRIP[%=",%2]"
title RARing...
     "%ProgramFiles\winrar\rar.exe" a -m%COMPRESSION -ep1       -r -v%[CHUNK]b    "%@STRIP[\,%@STRIP[%=",%2]].rar" "%@STRIP[%=",%@UNQUOTE[%2]]"
call fix-window-title
goto :end


:badusage
echo Doing nothing. Try one of these:
echo.
echo USAGE: backup-to-CDs   %*
echo USAGE: backup-to-DVDs  %*
echo.
echo NOTE:  backup to CDs  is currently set for 650M cds
echo NOTE:  backup to DVDs is currently set for quarter-DVD sized files (due to 2G file limit)
echo.
echo NOTE: backup.bat is really intended to only be called by scripts that know the options.
:works now! echo IMPORTANT NOTE!!: Script WILL NOT WORK for folders with SPACES in the title. Rename first.
goto :end

:end
unset /q CHUNK
unset /q COMPRESSION
