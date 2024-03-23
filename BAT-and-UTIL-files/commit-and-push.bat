@echo off

set NO_PAUSE_TEMP=%NO_PAUSE%
set NO_PAUSE=1
set CAP_PARAMS=%1

call commit %CAP_PARAMS%
call push   %CAP_PARAMS%

set NO_PAUSE=%NO_PAUSE_TEMP%

