@echo off
unset /q TMP
if not isdir "%TEMP%" set TEMP=c:\recycled
if isdir %TMPDIR% set  TMP=%TMPDIR%
if isdir %TMPDIR% set TEMP=%TMPDIR%

