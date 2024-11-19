@Echo OFF
 on break cancel

:DESCRIPTION: To put the current date in yyyymmddhhss format into the environment as %YYYYMMDDHHSS.
:DESCRIPTION: EXAMPLE: run this, then echo %YYYYMMDDHHSS would output 20031231235959 (Dec 12th 2003 11:59:59AM Happy New Year's!) if thatwas today's date

set                YYYYMMDDHHMMSS=%@STRIP[-,%@MAKEDATE[%@DATE[],4]]%@STRIP[:,%@maketime[%@time[%_TIME]]]
set YYYY=%@SUBSTR[%YYYYMMDDHHMMSS,0,4]
set   MM=%@SUBSTR[%YYYYMMDDHHMMSS,4,2]
set   DD=%@SUBSTR[%YYYYMMDDHHMMSS,6,2]
set   HH=%@SUBSTR[%YYYYMMDDHHMMSS,8,2]
set   MM=%@SUBSTR[%YYYYMMDDHHMMSS,10,2]

