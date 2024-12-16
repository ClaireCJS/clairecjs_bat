@echo off
@on break cancel


call  isRunning                     MiniLyrics
if  "%isRunning" eq 1              (call important_less "MiniLyrics not starting because it's already running" %+ goto :Nevermind)
set                                 MINILYRICS_EXE=%UTIL2%\MiniLyrics\MiniLyrics.exe
call  validate-environment-variable MINILYRICS_EXE  UTIL2

rem echo DEBUG: About to start minilyrics %+ call pause-for-x-seconds 600


*start ""                          %MINILYRICS_EXE%
call  wait                          3
call  isRunning                     MiniLyrics

:Nevermind

