@Echo OFF

set timestr=%@DATEFMT[*,%%r]

:: Use substring extraction to remove seconds, processing from the end of the string
    set TIME_VERY_NICE=%timestr:~0,-6% %timestr:~-2%

:: Replace the space with nothing
    set TIME_VERY_NICE=%TIME_VERY_NICE: =%



set TIME_NICE=%TIME_VERY_NICE%
set TIME_NICE_VERY=%TIME_VERY_NICE%
set TIME_VERYNICE=%TIME_VERY_NICE%
set NICE_TIME=%TIME_VERY_NICE%
set NICE_TIME_VERY=%TIME_VERY_NICE%
set VERY_NICE_TIME=%TIME_VERY_NICE%
set NICETIME=%TIME_VERY_NICE%

REM call debug "NICE_TIME IS %NICE_TIME%"

call validate-environment-variables VERY_NICE_TIME NICE_TIME_VERY NICE_TIME TIME_VERYNICE TIME_NICE_VERY TIME_NICE TIME_VERY_NICE NICETIME

