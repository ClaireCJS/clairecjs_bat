@echo off

set                                 MINILYRICS_EXE=%UTIL2%\MiniLyrics\MiniLyrics.exe
call  validate-environment-variable MINILYRICS_EXE  UTIL2
start                              %MINILYRICS_EXE%

