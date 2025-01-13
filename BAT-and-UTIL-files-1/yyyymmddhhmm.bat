@loadbtm on
@echo off
 on break cancel
:#PURPOSE: To put the current date in yyyymmddhh format into the environment as %YYYYMMDDHH.
:#EXAMPLE: run this, then echo %YYYYMMDDHH would output 200312312359 (Dec 12th 2003 11:59PM Happy New Year's!) if that was today's date

set YYYYMMDDHHMMSS=%@STRIP[-,%@MAKEDATE[%@DATE[],4]]%@STRIP[:,%@maketime[%@time[%_TIME]]]

set YYYY=%@SUBSTR[%YYYYMMDDHHMMSS,0,4]
set MM=%@SUBSTR[%YYYYMMDDHHMMSS,4,2]
set DD=%@SUBSTR[%YYYYMMDDHHMMSS,6,2]
set HH=%@SUBSTR[%YYYYMMDDHHMMSS,8,2]
set MI=%@SUBSTR[%YYYYMMDDHHMMSS,10,2]

set YYYYMMDDHHMM=%YYYY%%MM%%DD%%HH%%MI%
