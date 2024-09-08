@echo off

set NO_PAUSE_TEMP=%NO_PAUSE%
set NO_PAUSE=0 %+ rem decided i no longer want to default to not-pausing cause it doesn't give an opportunity to update the commit reason
set CAP_PARAMS=%1

call commit %CAP_PARAMS%
call push   %CAP_PARAMS%

set NO_PAUSE=%NO_PAUSE_TEMP%

