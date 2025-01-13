@loadbtm on
@Echo OFF
 on break cancel

:DESCRIPTION: To put the current date in yyyymmdd format into the environment as %YYYYMMDD, %YYYY for year, %MM for month, %DD for day.
:DESCRIPTION: EXAMPLE: run this, then echo %YYYYMMDD would output 20031231 (Dec 12th 2003) if that was today's date

set                YYYYMMDD=%@STRIP[-,%@MAKEDATE[%@DATE[],4]]
set YYYY=%@SUBSTR[%YYYYMMDD,0,4]
set   MM=%@SUBSTR[%YYYYMMDD,4,2]
set   DD=%@SUBSTR[%YYYYMMDD,6,2]


