@echo off


call  isRunning                     MiniLyrics
if  "%isRunning" eq 1              (call important_less "MiniLyrics not starting because it's already running" %+ goto :Nevermind)
set                                 MINILYRICS_EXE=%UTIL2%\MiniLyrics\MiniLyrics.exe
call  validate-environment-variable MINILYRICS_EXE  UTIL2
start                              %MINILYRICS_EXE%
call  wait                          3
call  isRunning                     MiniLyrics

:Nevermind

