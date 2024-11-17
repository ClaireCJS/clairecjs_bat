@Echo OFF

:DESCRIPTION: To put the current date in yyyymmdd format into the environment as %YYYYMMDDDOW.
:DESCRIPTION: Much like yyyymmdd.bat except adding the day of week to the end.
:DESCRIPTION: EXAMPLE: run this, then echo %YYYYMMDD would output 20031231(Fri) (Dec 12th 2003) if that was today's date and it was a friday

set             YYYYMMDDDOW=%@STRIP[-,%@MAKEDATE[%@DATE[],4]](%_DOW)
set                YYYYMMDD=%@STRIP[-,%@MAKEDATE[%@DATE[],4]]
set YYYY=%@SUBSTR[%YYYYMMDD,0,4]
set   MM=%@SUBSTR[%YYYYMMDD,4,2]
set   DD=%@SUBSTR[%YYYYMMDD,6,2]
