@echo off

set NO_PAUSE_TEMP=%NO_PAUSE%
set NO_PAUSE=1
set PARAMS=%1

call commit %PARAMS%
call push   %PARAMS%

set NO_PAUSE=%NO_PAUSE_TEMP%

