@Echo OFF

:DESCRIPTION: To put the current date in mmddhhmmss format into the environment as %MMDDHHMMSS.
:DESCRIPTION: EXAMPLE: run this, then echo %MMDDHHMMSS would output 12312359 if that was that moment in time [lat second of the year]


call              YYYYMMDD
set  YY=%@SUBSTR[%YYYYMMDD%,2,2]
set  MM=%@SUBSTR[%YYYYMMDD%,4,2]
set  DD=%@SUBSTR[%YYYYMMDD%,6,2]
set  HH=%@SUBSTR[%_TIME,0,2]
set MIN=%@SUBSTR[%_TIME,3,2]
set  SS=%@SUBSTR[%_TIME,6,2]

set MMDDHHMMSS=%MM%%DD%%HH%%MIN%%SS%




