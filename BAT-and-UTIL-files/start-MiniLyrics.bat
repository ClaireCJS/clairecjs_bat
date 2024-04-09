@echo off

set                                 MINILYRICS_EXE=c:\util2\MiniLyrics\MiniLyrics.exe
call  validate-environment-variable MINILYRICS_EXE
start                              %MINILYRICS_EXE%

